const http = require('http');

// Simple 1x1 red pixel PNG base64
const sampleImageBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKwAEAAAAABJRU5ErkJggg==";

const data = JSON.stringify({
    imageBase64: sampleImageBase64
});

const options = {
    hostname: 'localhost',
    port: 3001,
    path: '/api/analyze',
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
    }
};

console.log("Sending test request to http://localhost:3001/api/analyze...");

const req = http.request(options, (res) => {
    console.log(`STATUS: ${res.statusCode}`);
    console.log(`HEADERS: ${JSON.stringify(res.headers)}`);

    let responseData = '';

    res.setEncoding('utf8');
    res.on('data', (chunk) => {
        responseData += chunk;
    });

    res.on('end', () => {
        console.log('Response Body:');
        console.log(responseData);

        if (res.statusCode === 200) {
            console.log("SUCCESS: Image analysis endpoint is working correctly.");
            try {
                const json = JSON.parse(responseData);
                console.log("Detected Objects:", json.objects ? json.objects.length : 0);
            } catch (e) {
                console.error("Failed to parse JSON response");
            }
        } else {
            console.error("FAILURE: Image analysis endpoint returned an error.");
        }
    });
});

req.on('error', (e) => {
    console.error(`problem with request: ${e.message}`);
});

// Write data to request body
req.write(data);
req.end();
