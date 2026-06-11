document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const imagePreview = document.getElementById('image-preview');
    const removeBtn = document.getElementById('remove-btn');
    const extractBtn = document.getElementById('extract-btn');
    const modeSelect = document.getElementById('mode-select');
    const loadingState = document.getElementById('loading-state');
    const resultSection = document.getElementById('result-section');
    const resultText = document.getElementById('result-text');
    const timeMetric = document.getElementById('time-metric');
    
    // vLLM OpenAI-compatible API endpoint on AWS EC2
    const VLLM_URL = 'http://13.62.96.5:8000/v1/chat/completions';
    const MODEL_NAME = 'ocr-engine';

    const OCR_PROMPTS = {
        'ocr': 'Please extract ALL text from this image exactly as written. Preserve line breaks and formatting. Do not summarize or paraphrase. Output only the extracted text, nothing else.',
        'json': 'Extract all text from this image and return it as a structured JSON object. Use appropriate keys based on the content. Output only valid JSON, no markdown fences.',
        'markdown': 'Extract all text from this image and format it as clean Markdown. Use headings, bullet points, and emphasis where appropriate. Output only the Markdown text, nothing else.',
    };
    
    let currentFile = null;

    // Handle Drag & Drop
    dropZone.addEventListener('click', () => {
        if (!currentFile) fileInput.click();
    });

    ['dragover', 'dragenter'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'dragend', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const file = e.dataTransfer.files[0];
        handleFile(file);
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFile(file);
    });

    function handleFile(file) {
        if (!file || !file.type.startsWith('image/')) {
            alert('Please select a valid image file.');
            return;
        }
        
        currentFile = file;
        const reader = new FileReader();
        
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.classList.remove('hidden');
            removeBtn.classList.remove('hidden');
            extractBtn.disabled = false;
        };
        
        reader.readAsDataURL(file);
    }

    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        currentFile = null;
        fileInput.value = '';
        imagePreview.src = '';
        imagePreview.classList.add('hidden');
        removeBtn.classList.add('hidden');
        extractBtn.disabled = true;
        resultSection.classList.add('hidden');
    });

    extractBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        // UI transitions
        extractBtn.disabled = true;
        resultSection.classList.add('hidden');
        loadingState.classList.remove('hidden');

        try {
            // Convert image file to base64
            const b64 = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => {
                    // Strip the data:image/...;base64, prefix
                    resolve(reader.result.split(',')[1]);
                };
                reader.onerror = reject;
                reader.readAsDataURL(currentFile);
            });

            const mediaType = currentFile.type || 'image/jpeg';
            const prompt = OCR_PROMPTS[modeSelect.value] || OCR_PROMPTS['ocr'];

            // Build vLLM OpenAI-compatible payload
            const payload = {
                model: MODEL_NAME,
                messages: [
                    {
                        role: 'user',
                        content: [
                            {
                                type: 'image_url',
                                image_url: {
                                    url: `data:${mediaType};base64,${b64}`
                                }
                            },
                            {
                                type: 'text',
                                text: prompt
                            }
                        ]
                    }
                ],
                max_tokens: 2048,
                temperature: 0.0
            };

            const t0 = performance.now();

            const response = await fetch(VLLM_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const elapsed_ms = performance.now() - t0;

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`vLLM Error: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            const resultContent = data.choices[0].message.content;

            // Display results
            resultText.textContent = resultContent;
            const seconds = (elapsed_ms / 1000).toFixed(2);
            timeMetric.textContent = `${seconds}s inference`;
            
            resultSection.classList.remove('hidden');
        } catch (error) {
            console.error('Extraction Error:', error);
            alert(`Failed to extract text: ${error.message}\n\nMake sure the vLLM server is running!\nOn EC2: bash ~/start_server.sh`);
        } finally {
            loadingState.classList.add('hidden');
            extractBtn.disabled = false;
        }
    });
});
