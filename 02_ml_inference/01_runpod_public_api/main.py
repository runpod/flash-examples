"""Main FastAPI application for Runpod public API example."""

import logging
import os

from cpu_worker import cpu_router
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Runpod Public API Example",
    description="Generate images using Runpod public text-to-image endpoint",
    version="0.1.0",
)

# Include router
app.include_router(cpu_router, prefix="/api", tags=["Image Generation"])


@app.get("/", response_class=HTMLResponse)
def home():
    """Serve interactive HTML form for image generation."""
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Runpod Text-to-Image Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            color: #333;
            font-weight: 500;
            margin-bottom: 8px;
            font-size: 14px;
        }

        input[type="text"],
        input[type="number"],
        select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.3s;
        }

        input[type="text"]:focus,
        input[type="number"]:focus,
        select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }

        .checkbox-group label {
            margin-bottom: 0;
            display: flex;
            align-items: center;
            cursor: pointer;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        @media (max-width: 600px) {
            .form-row {
                grid-template-columns: 1fr;
            }
        }

        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-top: 10px;
        }

        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            margin-top: 20px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .loading-text {
            color: #666;
            font-size: 14px;
        }

        .result {
            display: none;
            margin-top: 30px;
            text-align: center;
        }

        .result.show {
            display: block;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .result-image {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            margin-bottom: 15px;
        }

        .result-info {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
        }

        .result-info-item {
            text-align: left;
            font-size: 13px;
            color: #666;
            margin: 8px 0;
            word-break: break-all;
        }

        .result-label {
            font-weight: 600;
            color: #333;
        }

        .error {
            display: none;
            background: #fee;
            border: 1px solid #fcc;
            color: #c33;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
            font-size: 14px;
        }

        .error.show {
            display: block;
            animation: slideIn 0.3s ease-out;
        }

        .help-text {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }

        .info-box {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-size: 13px;
            color: #445;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Text-to-Image Generator</h1>
        <p class="subtitle">Generate images using AI powered by Runpod public endpoint</p>

        <div class="info-box">
            Generated images are stored for 7 days. Links may expire after that time.
        </div>

        <form id="imageForm">
            <div class="form-group">
                <label for="prompt">Image Description *</label>
                <input
                    type="text"
                    id="prompt"
                    name="prompt"
                    required
                    placeholder="A serene mountain landscape at sunrise..."
                    maxlength="1000"
                >
                <p class="help-text">Describe the image you want to generate</p>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="aspectRatio">Aspect Ratio</label>
                    <select id="aspectRatio" name="aspect_ratio">
                        <option value="16:9">16:9 (Wide)</option>
                        <option value="1:1">1:1 (Square)</option>
                        <option value="9:16">9:16 (Tall)</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="seed">Seed (for reproducibility)</label>
                    <input
                        type="number"
                        id="seed"
                        name="seed"
                        min="0"
                        max="2147483647"
                        value="0"
                    >
                    <p class="help-text">Same seed produces same image</p>
                </div>
            </div>

            <div class="form-group">
                <div class="checkbox-group">
                    <input
                        type="checkbox"
                        id="safetyChecker"
                        name="enable_safety_checker"
                        checked
                    >
                    <label for="safetyChecker">Enable safety checker</label>
                </div>
            </div>

            <button type="submit" id="submitBtn">Generate Image</button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p class="loading-text">Generating image...</p>
        </div>

        <div class="error" id="error"></div>

        <div class="result" id="result">
            <img id="resultImage" class="result-image" alt="Generated image">
            <div class="result-info">
                <div class="result-info-item">
                    <span class="result-label">Image URL:</span>
                    <a id="imageUrl" href="#" target="_blank">View full resolution</a>
                </div>
                <div class="result-info-item">
                    <span class="result-label">Job ID:</span>
                    <span id="jobId"></span>
                </div>
                <div class="result-info-item">
                    <span class="result-label">Prompt:</span>
                    <span id="promptResult"></span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const form = document.getElementById('imageForm');
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');
        const error = document.getElementById('error');
        const submitBtn = document.getElementById('submitBtn');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = {
                prompt: document.getElementById('prompt').value,
                aspect_ratio: document.getElementById('aspectRatio').value,
                enable_safety_checker: document.getElementById('safetyChecker').checked,
                seed: parseInt(document.getElementById('seed').value) || 0,
            };

            // Show loading, hide result/error
            loading.style.display = 'block';
            result.classList.remove('show');
            error.style.display = 'none';
            error.textContent = '';
            submitBtn.disabled = true;

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to generate image');
                }

                const data = await response.json();

                // Display image
                document.getElementById('resultImage').src = data.image_url;
                document.getElementById('imageUrl').href = data.image_url;
                document.getElementById('jobId').textContent = data.job_id;
                document.getElementById('promptResult').textContent = data.prompt;

                result.classList.add('show');

            } catch (err) {
                error.textContent = err.message || 'An error occurred';
                error.classList.add('show');
            } finally {
                loading.style.display = 'none';
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>"""


@app.get("/ping")
def ping():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("FLASH_HOST", "localhost")
    port = int(os.getenv("FLASH_PORT", 8888))
    logger.info(f"Starting Flash server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
    )
