"""Main FastAPI application for Langchain Basics example.

This application serves as a local development server for testing the
Langchain integration with Flash workers.
"""

from contextlib import asynccontextmanager

import structlog
from gpu_worker import gpu_router
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events.

    Handles startup and shutdown logging for the application.
    """
    logger.info("Starting Langchain Basics with vLLM example")
    yield
    logger.info("Shutting down Langchain Basics with vLLM example")


app = FastAPI(
    title="Langchain Basics - Flash GPU Example",
    description="Learn local LLM inference with Langchain + vLLM + Flash GPU workers",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse, tags=["Info"])
async def root():
    """Educational home page with comprehensive example documentation."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Langchain Basics - Flash LLM Orchestration</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                font-weight: 600;
            }
            .header p {
                font-size: 1.2em;
                opacity: 0.95;
            }
            .content {
                padding: 40px;
            }
            .section {
                margin-bottom: 40px;
            }
            .section h2 {
                color: #667eea;
                font-size: 1.8em;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid #667eea;
            }
            .card {
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 6px;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .card:hover {
                transform: translateX(5px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
            }
            .card h3 {
                color: #667eea;
                margin-bottom: 10px;
                font-size: 1.3em;
            }
            .card p {
                color: #666;
                margin-bottom: 8px;
            }
            .code-block {
                background: #2d2d2d;
                color: #f8f8f2;
                padding: 20px;
                border-radius: 6px;
                overflow-x: auto;
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 0.9em;
                line-height: 1.5;
                margin: 15px 0;
                position: relative;
            }
            .code-block:hover .copy-btn {
                opacity: 1;
            }
            .copy-btn {
                position: absolute;
                top: 10px;
                right: 10px;
                background: #667eea;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.85em;
                opacity: 0;
                transition: opacity 0.2s;
            }
            .copy-btn:hover {
                background: #5568d3;
            }
            .badge {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.85em;
                margin-right: 8px;
                margin-bottom: 8px;
            }
            .list-item {
                padding: 12px;
                margin: 8px 0;
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
            .list-item strong {
                color: #667eea;
            }
            .btn {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                margin: 10px 10px 10px 0;
                transition: background 0.2s;
                font-weight: 500;
            }
            .btn:hover {
                background: #5568d3;
            }
            .btn-secondary {
                background: #764ba2;
            }
            .btn-secondary:hover {
                background: #653a8d;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .cost-box {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            .cost-box h3 {
                color: white;
                margin-bottom: 10px;
            }
            .cost-box .amount {
                font-size: 2em;
                font-weight: bold;
                margin: 10px 0;
            }
            .endpoint-method {
                display: inline-block;
                background: #28a745;
                color: white;
                padding: 4px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 0.85em;
                margin-right: 10px;
            }
            ul {
                list-style: none;
                padding-left: 0;
            }
            ul li:before {
                content: "• ";
                color: #667eea;
                font-weight: bold;
                margin-right: 8px;
            }
            .warning-box {
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 6px;
            }
            .warning-box strong {
                color: #856404;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Langchain Basics</h1>
                <p>Local LLM Inference with vLLM + Flash GPU Workers</p>
                <div style="margin-top: 20px;">
                    <span class="badge">v0.2.0</span>
                    <span class="badge">Running</span>
                    <span class="badge">GPU Workers</span>
                </div>
            </div>

            <div class="content">
                <!-- Quick Actions -->
                <div style="text-align: center; margin-bottom: 40px;">
                    <a href="/docs" class="btn">Interactive API Docs</a>
                    <a href="/health" class="btn btn-secondary">Health Check</a>
                </div>

                <!-- What You'll Learn -->
                <div class="section">
                    <h2>What You'll Learn</h2>
                    <ul>
                        <li>Integrating Langchain with Flash @remote decorator</li>
                        <li>GPU workers for local LLM inference with vLLM</li>
                        <li>Running open-source models (Mistral-7B) locally</li>
                        <li>Prompt templating with Langchain</li>
                        <li>Structured output parsing with Pydantic</li>
                        <li>Production error handling patterns</li>
                        <li>Cost-effective self-hosted LLM architecture</li>
                    </ul>
                </div>

                <!-- Quick Start -->
                <div class="section">
                    <h2>Quick Start</h2>

                    <div class="warning-box">
                        <strong>Note:</strong> GPU workers will automatically download Mistral-7B model (~5GB) on first inference request. Allow 5-10 minutes for model loading on first startup.
                    </div>

                    <div class="list-item">
                        <strong>Step 1:</strong> Copy environment template (optional)
                        <div class="code-block">
                            <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                            <code>cp .env.example .env</code>
                        </div>
                    </div>

                    <div class="list-item">
                        <strong>Step 2:</strong> Start the server (models will be downloaded automatically)
                        <div class="code-block">
                            <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                            <code>flash run</code>
                        </div>
                    </div>

                    <div class="list-item">
                        <strong>Step 3:</strong> Try your first API call
                        <div class="code-block">
                            <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                            <code>curl -X POST http://localhost:8888/gpu/summarize \\
  -H 'Content-Type: application/json' \\
  -d '{"text": "Artificial intelligence is transforming how we work and live. Machine learning algorithms enable computers to learn from data without explicit programming. Deep learning networks can now recognize images, process natural language, and make decisions with remarkable accuracy.", "max_length": 50}'</code>
                        </div>
                    </div>
                </div>

                <!-- API Endpoints -->
                <div class="section">
                    <h2>API Endpoints</h2>

                    <div class="card">
                        <h3><span class="endpoint-method">POST</span> /gpu/summarize</h3>
                        <p><strong>Description:</strong> Summarize long text into key points using Mistral-7B local inference</p>
                        <p><strong>Use Cases:</strong> Document summarization, article highlights, meeting notes</p>
                        <div class="code-block">
                            <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                            <code>curl -X POST http://localhost:8888/gpu/summarize \\
  -H 'Content-Type: application/json' \\
  -d '{"text": "Your long text here...", "max_length": 100}'</code>
                        </div>
                    </div>

                    <div class="card">
                        <h3><span class="endpoint-method">POST</span> /gpu/analyze-sentiment</h3>
                        <p><strong>Description:</strong> Analyze sentiment with structured output (label, confidence, topics)</p>
                        <p><strong>Use Cases:</strong> Product reviews, customer feedback, social media monitoring</p>
                        <div class="code-block">
                            <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                            <code>curl -X POST http://localhost:8888/gpu/analyze-sentiment \\
  -H 'Content-Type: application/json' \\
  -d '{"text": "This product exceeded my expectations! Highly recommend."}'</code>
                        </div>
                    </div>

                    <div class="card">
                        <h3><span class="endpoint-method">POST</span> /gpu/transform</h3>
                        <p><strong>Description:</strong> Transform text with custom instructions (translate, rephrase, format)</p>
                        <p><strong>Use Cases:</strong> Translation, text formatting, style changes</p>
                        <div class="code-block">
                            <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                            <code>curl -X POST http://localhost:8888/gpu/transform \\
  -H 'Content-Type: application/json' \\
  -d '{"text": "Hello, how are you?", "instruction": "Translate to Spanish", "temperature": 0.7}'</code>
                        </div>
                    </div>
                </div>

                <!-- Architecture -->
                <div class="section">
                    <h2>Architecture</h2>
                    <div class="card">
                        <p><strong>Flow:</strong> User → FastAPI → GPU Worker (@remote) → Langchain + vLLM → Mistral-7B Local Inference</p>
                        <p><strong>Worker Type:</strong> GPU (RTX 4090, 24GB VRAM - scales to zero)</p>
                        <p><strong>LLM Model:</strong> Mistral-7B-Instruct-v0.3 (self-hosted)</p>
                        <p><strong>Inference Engine:</strong> vLLM (optimized for throughput)</p>
                        <p><strong>Cost Optimization:</strong> Workers scale to zero when idle, no external API fees</p>
                    </div>
                </div>

                <!-- Cost Estimates -->
                <div class="section">
                    <h2>Cost Estimates</h2>
                    <div class="grid">
                        <div class="cost-box">
                            <h3>Development</h3>
                            <div class="amount">~$0</div>
                            <p>Scale to zero between requests</p>
                        </div>
                        <div class="cost-box">
                            <h3>Per Request</h3>
                            <div class="amount">~$0.0002</div>
                            <p>GPU compute only (2 sec at RTX 4090 rate)</p>
                        </div>
                        <div class="cost-box">
                            <h3>10K Requests/Month</h3>
                            <div class="amount">~$2</div>
                            <p>GPU workers only (no external API fees)</p>
                        </div>
                    </div>
                </div>

                <!-- Key Concepts -->
                <div class="section">
                    <h2>Key Concepts</h2>
                    <div class="grid">
                        <div class="card">
                            <h3>vLLM Inference</h3>
                            <p>High-throughput local LLM inference engine</p>
                        </div>
                        <div class="card">
                            <h3>Mistral-7B Model</h3>
                            <p>Open-source, permissive license, excellent performance</p>
                        </div>
                        <div class="card">
                            <h3>GPU Workers</h3>
                            <p>RTX 4090 for fast local inference</p>
                        </div>
                        <div class="card">
                            <h3>Langchain Templates</h3>
                            <p>Structured prompt engineering</p>
                        </div>
                        <div class="card">
                            <h3>Scale-to-Zero</h3>
                            <p>No idle charges, pay only for computation</p>
                        </div>
                        <div class="card">
                            <h3>No API Dependencies</h3>
                            <p>Self-hosted, no external API costs</p>
                        </div>
                    </div>
                </div>

                <!-- Resources -->
                <div class="section">
                    <h2>Resources & Links</h2>
                    <div class="list-item">
                        <strong>Swagger UI:</strong> <a href="/docs">/docs</a> - Interactive API testing
                    </div>
                    <div class="list-item">
                        <strong>Health Check:</strong> <a href="/health">/health</a> - Service status
                    </div>
                    <div class="list-item">
                        <strong>vLLM Documentation:</strong> <a href="https://docs.vllm.ai" target="_blank">docs.vllm.ai</a> - Inference engine
                    </div>
                    <div class="list-item">
                        <strong>Mistral Model:</strong> <a href="https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3" target="_blank">HuggingFace Hub</a> - Model weights
                    </div>
                    <div class="list-item">
                        <strong>Langchain Docs:</strong> <a href="https://python.langchain.com/docs/get_started/introduction" target="_blank">python.langchain.com</a> - Prompt management
                    </div>
                    <div class="list-item">
                        <strong>Flash Documentation:</strong> <a href="https://docs.runpod.io" target="_blank">docs.runpod.io</a> - Deployment and scaling
                    </div>
                </div>

                <!-- Next Steps -->
                <div class="section">
                    <h2>Next Steps</h2>
                    <ol style="list-style: decimal; padding-left: 20px;">
                        <li style="margin: 10px 0;">Visit <a href="/docs">/docs</a> for interactive Swagger UI</li>
                        <li style="margin: 10px 0;">Try the example curl commands above</li>
                        <li style="margin: 10px 0;">Check README.md for detailed documentation</li>
                        <li style="margin: 10px 0;">Explore code in gpu_worker.py to see @remote decorator with vLLM usage</li>
                        <li style="margin: 10px 0;">Monitor GPU utilization in Runpod dashboard</li>
                        <li style="margin: 10px 0;">Experiment with different models on HuggingFace Hub</li>
                    </ol>
                </div>
            </div>
        </div>

        <script>
            function copyCode(button) {
                const codeBlock = button.parentElement;
                const code = codeBlock.querySelector('code').textContent;
                navigator.clipboard.writeText(code).then(() => {
                    button.textContent = 'Copied!';
                    setTimeout(() => {
                        button.textContent = 'Copy';
                    }, 2000);
                });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "langchain_basics_gpu",
        "version": "0.2.0",
    }


# Mount GPU worker router with /gpu prefix
app.include_router(gpu_router, prefix="/gpu", tags=["GPU Workers"])


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    logger.error("Validation error", error=str(exc))
    return JSONResponse(status_code=400, content={"detail": str(exc), "type": "ValidationError"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8888,
        log_level="info",
    )
