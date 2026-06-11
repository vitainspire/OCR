/**
 * advanced_education_api.js
 * 
 * The Frontend Wrapper for the Enterprise Two-Door Architecture.
 * This runs on your Web Server (Node.js) and acts as the "Traffic Cop".
 */

const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Connect to the same hard-drive database the queue_worker is using
const dbPath = path.join(__dirname, 'requests_queue.db');
const db = new sqlite3.Database(dbPath);

/**
 * Ensures the database table exists.
 */
db.serialize(() => {
    db.run(`
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            door INTEGER,
            payload TEXT,
            status TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    `);
});

/**
 * THE TRAFFIC COP
 * Receives an API request from the college application.
 * Identifies if it requires Door 1 (OCR) or Door 2 (Text).
 * Saves it securely to the Hard Drive Queue.
 */
async function addRequestToQueue(userPrompt, imageBase64 = null) {
    return new Promise((resolve, reject) => {
        let door = 0;
        let payload = {};

        // TRAFFIC COP LOGIC
        if (imageBase64) {
            // It has an image -> Send to Door 1 (OCR Fortress)
            door = 1;
            payload = {
                model: "Qwen/Qwen2.5-VL-7B-Instruct-AWQ",
                messages: [{
                    role: "user",
                    content: [
                        { type: "image_url", image_url: { url: `data:image/jpeg;base64,${imageBase64}` } },
                        { type: "text", text: userPrompt }
                    ]
                }],
                max_tokens: 1024,
                temperature: 0.0 // OCR must be perfectly deterministic
            };
        } else {
            // No image -> Send to Door 2 (Lightning Text)
            door = 2;
            
            // RAG INJECTION & PERSONA
            const systemPersona = "You are an expert College Professor. Create highly detailed lesson plans.";
            
            payload = {
                model: "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4",
                messages: [
                    { role: "system", content: systemPersona },
                    { role: "user", content: userPrompt }
                ],
                max_tokens: 4000,
                temperature: 0.7, // Creative lesson planning
                top_p: 0.9
            };
        }

        const payloadStr = JSON.stringify(payload);

        // SAVE TO ZERO DATA LOSS QUEUE
        const query = `INSERT INTO requests (door, payload, status) VALUES (?, ?, "PENDING")`;
        db.run(query, [door, payloadStr], function(err) {
            if (err) return reject(err);
            resolve(this.lastID); // Return the Request ID to the user
        });
    });
}

/**
 * Checks the status of a specific job on the hard drive.
 */
async function checkJobStatus(jobId) {
    return new Promise((resolve, reject) => {
        db.get(`SELECT status, result FROM requests WHERE id = ?`, [jobId], (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

// ==========================================
// TEST EXECUTION
// ==========================================
async function runTest() {
    console.log("=== Testing Zero Data Loss Architecture ===");
    
    // 1. Simulate Teacher 1 asking for a pure text lesson plan (Door 2)
    const jobId = await addRequestToQueue("Write a detailed 3-page lesson plan on Quantum Mechanics.");
    console.log(`[Frontend] Successfully saved Job #${jobId} to the Hard Drive Queue (Door 2).`);
    
    console.log(`[Frontend] Safely returning to user. The queue_worker.py will now process it in the background!`);
    console.log(`[Frontend] You can check status anytime using checkJobStatus(${jobId}).`);
}

if (require.main === module) {
    runTest();
}
