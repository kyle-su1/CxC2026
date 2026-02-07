const express = require('express');
const cors = require('cors');
require('dotenv').config();
const OpenAI = require('openai');
const sharp = require('sharp');

const app = express();
const port = 3001;

const openai = new OpenAI({
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: process.env.OPENROUTER_OPENAI_API_KEY,
    defaultHeaders: {
        "HTTP-Referer": "http://localhost:3000", // Optional, for OpenRouter rankings
        "X-Title": "VisionBackend", // Optional
    },
});

app.use(cors());
app.use(express.json({ limit: '50mb' }));

app.post('/api/analyze', async (req, res) => {
    try {
        const { imageBase64 } = req.body;
        console.log(`\n--- New Request Received (OpenAI-Only Mode) ---`);

        const apiKey = process.env.OPENROUTER_OPENAI_API_KEY; // Use OpenRouter Key

        if (!apiKey) {
            return res.status(500).json({
                error: 'API Key not found',
                details: 'Please add OPENROUTER_OPENAI_API_KEY to your backend/.env file'
            });
        }

        if (!imageBase64) {
            return res.status(400).json({ error: 'No image data provided' });
        }

        // 1. Process Image with Sharp
        // Detect if there's a header and strip it
        let base64Data = imageBase64;
        if (imageBase64.includes('base64,')) {
            base64Data = imageBase64.split('base64,')[1];
        }

        const imageBuffer = Buffer.from(base64Data, 'base64');

        // Resize and convert to JPEG using sharp
        console.log("Optimizing image with Sharp...");
        const optimizedBuffer = await sharp(imageBuffer)
            .resize({
                width: 2048,
                height: 2048,
                fit: 'inside', // Maintain aspect ratio, do not exceed dimensions
                withoutEnlargement: true // Do not upscale small images
            })
            .jpeg({ quality: 80 }) // standardized to JPEG, 80% quality
            .toBuffer();

        const optimizedBase64 = optimizedBuffer.toString('base64');
        console.log(`Image optimized. Original size: ${Math.round(base64Data.length / 1024)}KB, Optimized: ${Math.round(optimizedBase64.length / 1024)}KB`);

        console.log(`Sending Optimized Image to OpenRouter (gpt-4o) for Detection & Labeling...`);

        const systemPrompt = `
            You are an expert object detection and identification system.
            
            TASK: Detect ALL objects in the image and identify them with maximum specificity.
            
            For EACH object:
            1. "name": Look for visible text, logos, or distinctive features to identify:
               - BEST: Exact brand + model (e.g., "Boston Dynamics Spot", "DeWalt DCD771C2 Drill")
               - GOOD: Brand + type (e.g., "DeWalt Cordless Drill", "WEN Band Saw")
               - FALLBACK: Descriptive name only if no branding visible (e.g., "Yellow Robotic Dog", "Red Fire Extinguisher")
            
            2. "confidence": Your confidence in the detection (0.0 to 1.0):
               - 0.95-1.0 = Very clear, unobstructed, well-lit object
               - 0.85-0.94 = Clear but partially occluded or at angle
               - 0.70-0.84 = Visible but small, distant, or unclear
               - Below 0.70 = Uncertain identification
            
            3. "box": Bounding box in STANDARD CV FORMAT [y_min, x_min, y_max, x_max] where:
               - ALL values are decimals from 0.0 to 1.0 (normalized coordinates)
               - y_min = distance from TOP edge to TOP of box (0.0 = top of image)
               - x_min = distance from LEFT edge to LEFT of box (0.0 = left of image)
               - y_max = distance from TOP edge to BOTTOM of box (1.0 = bottom of image)
               - x_max = distance from LEFT edge to RIGHT of box (1.0 = right of image)
               
               EXAMPLES:
               - Object in top-left corner: [0.0, 0.0, 0.3, 0.3]
               - Object in center: [0.4, 0.4, 0.6, 0.6]
               - Object in bottom-right: [0.7, 0.7, 1.0, 1.0]
               - Object spanning full width at top: [0.0, 0.0, 0.2, 1.0]
            
            Return ONLY valid JSON: {"objects": [{"name": "...", "confidence": 0.95, "box": [y_min, x_min, y_max, x_max]}]}
        `;

        const aiResponse = await openai.chat.completions.create({
            model: "openai/gpt-4o",
            messages: [
                { role: "system", content: systemPrompt },
                {
                    role: "user",
                    content: [
                        { type: "text", text: "Detect and identify all objects." },
                        {
                            type: "image_url",
                            image_url: {
                                "url": `data:image/jpeg;base64,${optimizedBase64}`, // Always JPEG now
                                "detail": "high"
                            },
                        },
                    ],
                },
            ],
            max_tokens: 1500,
        });

        const content = aiResponse.choices[0].message.content;
        console.log("OpenAI Raw Response:", content.substring(0, 200) + "...");

        try {
            const cleanContent = content.replace(/```json\n?|```/g, '').trim();
            const result = JSON.parse(cleanContent);

            // Map OpenAI format to Google Cloud Vision format for Frontend Compatibility
            // GCV Format: localizedObjectAnnotations: [{ name, score, boundingPoly: { normalizedVertices: [{x,y}, {x,y}, {x,y}, {x,y}] } }]

            const mappedObjects = result.objects.map(obj => {
                // Handle both new format (box) and old format (box_2d)
                let [ymin, xmin, ymax, xmax] = obj.box || obj.box_2d;

                // Auto-detect scale: If any value is > 1, assume it's 0-1000 scale
                if (ymin > 1 || xmin > 1 || ymax > 1 || xmax > 1) {
                    ymin /= 1000;
                    xmin /= 1000;
                    ymax /= 1000;
                    xmax /= 1000;
                }

                // Clamp to 0-1 to be safe
                const nYmin = Math.max(0, Math.min(1, ymin));
                const nXmin = Math.max(0, Math.min(1, xmin));
                const nYmax = Math.max(0, Math.min(1, ymax));
                const nXmax = Math.max(0, Math.min(1, xmax));

                console.log(`Mapped Object: ${obj.name} [${nYmin.toFixed(2)}, ${nXmin.toFixed(2)}, ${nYmax.toFixed(2)}, ${nXmax.toFixed(2)}]`);

                return {
                    name: obj.name,
                    score: obj.confidence || 0.95, // Use GPT-4o's confidence, fallback to 0.95
                    openAiLabel: obj.name, // Use same name for the "robot" label
                    boundingPoly: {
                        normalizedVertices: [
                            { x: nXmin, y: nYmin }, // Top-Left
                            { x: nXmax, y: nYmin }, // Top-Right
                            { x: nXmax, y: nYmax }, // Bottom-Right
                            { x: nXmin, y: nYmax }  // Bottom-Left
                        ]
                    }
                };
            });

            console.log(`Successfully mapped ${mappedObjects.length} objects.`);

            res.json({
                objects: mappedObjects,
                labels: [] // Labels are less useful now that we have specific object names
            });

        } catch (e) {
            console.error("Failed to parse OpenAI JSON:", e);
            console.error("Raw Content:", content);
            res.status(500).json({ error: "Failed to parse AI response", details: content });
        }

    } catch (error) {
        console.error('API Error:', error);

        // Enhanced Error Logging for OpenRouter/OpenAI
        if (error.response) {
            console.error("Upstream Error Data:", error.response.data);
            console.error("Upstream Error Status:", error.response.status);
        }

        res.status(500).json({
            error: 'Failed to analyze image',
            details: error.message,
            upstreamError: error.response ? error.response.data : null
        });
    }
});

app.listen(port, () => {
    console.log(`Backend server running at http://localhost:${port}`);
    const key = process.env.OPENROUTER_OPENAI_API_KEY;
    console.log(`OpenRouter API Key Status: ${key ? 'Loaded (' + key.substring(0, 5) + '...)' : 'MISSING'}`);
});
