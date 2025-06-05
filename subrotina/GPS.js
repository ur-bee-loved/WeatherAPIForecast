require('dotenv').config(); 
const express = require('express');
const axios = require('axios');
const app = express();
const PORT = process.env.PORT || 4444;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ping test
app.get('/ping', (req, res) => {
res.send('pong');
});

app.post('/GPS', async (req, res) => {
    console.log('endpoint hit')
    const startTime = Date.now
    if (!req.body) {
        console.log('no request body found')
    }
    try {
        const gpsData = extractGPSData(req);

        if (!gpsData.latitude || !gpsData.longitude) {
            console.log('Missing required GPS coordinates');
            return res.status(400).json({ 
                error: 'Missing parameters',
                received: req.method === 'GET' ? req.query : req.body
            });
        }
        console.log('GPS Data received:', gpsData);

        await ProcessData(gpsData);
                const processingTime = Date.now() - startTime;
        console.log(`GPS data processed in ${processingTime}ms`);
        
        // Send success response
        res.json({ 
            status: 'success', 
            timestamp: new Date().toISOString(),
            processingTime: `${processingTime}ms`
        });

    } catch (error) {
        console.error('Error processing GPS data:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: error.message 
        });
    }
})

function extractGPSData(req) {
    const data = req.method === 'GET' ? req.query : req.body;
    
    return {
        latitude: parseFloat(data.lat || data.latitude),
        longitude: parseFloat(data.lon || data.lng || data.longitude),
        timestamp: data.time || data.timestamp || new Date().toISOString(),
        accuracy: parseFloat(data.acc || data.accuracy) || null,
        altitude: parseFloat(data.alt || data.altitude) || null,
        speed: parseFloat(data.spd || data.speed) || null,
        bearing: parseFloat(data.dir || data.bearing) || null,
        satellites: parseInt(data.sat || data.satellites) || null,
        battery: parseFloat(data.batt || data.battery) || null,
        provider: data.prov || data.provider || 'unknown',
        deviceId: data.device || data.deviceId || 'unknown',
        raw: data // Keep original data for debugging
    };
}

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
});

