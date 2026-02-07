const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const port = 3001;

app.use(cors());
app.use(express.json({ limit: '50mb' }));

app.post('/api/analyze', async (req, res) => {
    try {
        const { imageBase64 } = req.body;
        const apiKey = process.env.GOOGLE_API_KEY;

        if (!apiKey) {
            return res.status(500).json({
                error: 'API Key not found',
                details: 'Please add GOOGLE_API_KEY to your backend/.env file'
            });
        }

        if (!imageBase64) {
            return res.status(400).json({ error: 'No image data provided' });
        }

        // Remove header if present
        const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, "");

        // Prepare request body for Google Cloud Vision REST API
        const requestBody = {
            requests: [
                {
                    image: {
                        content: base64Data
                    },
                    features: [
                        { type: 'OBJECT_LOCALIZATION' },
                        { type: 'LABEL_DETECTION' }
                    ]
                }
            ]
        };

        // Make direct fetch call
        const response = await fetch(
            `https://vision.googleapis.com/v1/images:annotate?key=${apiKey}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            }
        );

        const data = await response.json();

        if (!response.ok) {
            console.error('Vision API Error Response:', JSON.stringify(data, null, 2));
            throw new Error(data.error?.message || 'API request failed');
        }

        const result = data.responses[0];

        res.json({
            objects: result.localizedObjectAnnotations || [],
            labels: result.labelAnnotations || [],
        });

    } catch (error) {
        console.error('Vision API Error:', error);
        res.status(500).json({ error: 'Failed to analyze image', details: error.message });
    }
});

app.listen(port, () => {
    console.log(`Backend server running at http://localhost:${port}`);
    console.log('Ensure GOOGLE_API_KEY is defined in backend/.env');
});
