"""Langchain integration with Flash GPU workers for local LLM inference.

This module demonstrates how to use Langchain with Flash @remote decorator
for cost-effective local LLM inference using vLLM on GPU workers.
"""

import time

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from tetra_rp import GpuGroup, LiveServerless, remote

logger = structlog.get_logger(__name__)

# Model configuration (used by remote workers)
_model_name: str = "mistralai/Mistral-7B-Instruct-v0.3"

# GPU worker configuration for local LLM inference with vLLM
# Scale to zero when idle, allowing only a few parallel workers
gpu_config = LiveServerless(
    name="02_01_langchain_gpu",
    gpus=[GpuGroup.ADA_24],  # RTX 4090 with 24GB VRAM
    workersMin=0,  # Scale to zero when idle for cost savings
    workersMax=3,  # Allow up to 3 parallel requests
    idleTimeout=3,  # Minutes before scaling down
)


# ============================================================================
# REMOTE WORKER FUNCTIONS
# ============================================================================


@remote(
    resource_config=gpu_config,
    dependencies=[
        "vllm>=0.2.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "transformers>=4.38.0",
        "torch>=2.1.0",
    ],
)
async def summarize_text(input_data: dict) -> dict:
    """Summarize text using Langchain and local vLLM inference.

    Args:
        input_data: Dictionary containing 'text' and optional 'max_length'

    Returns:
        Dictionary with summary, metadata, and processing time
    """
    from langchain_core.prompts import PromptTemplate
    from vllm import LLM, SamplingParams

    # Initialize vLLM model for this worker
    llm = LLM(
        model="mistralai/Mistral-7B-Instruct-v0.3",
        trust_remote_code=True,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.8,
        max_model_len=4096,
    )

    # Create prompt template for summarization
    template = """Summarize the following text in {max_length} words or less.
Focus on key points and main ideas.

Text: {text}

Summary:"""

    prompt = PromptTemplate(template=template, input_variables=["text", "max_length"])

    # Format the prompt
    formatted_prompt = prompt.format(
        text=input_data["text"], max_length=input_data.get("max_length", 150)
    )

    # Execute LLM inference with vLLM and measure time
    start_time = time.time()
    sampling_params = SamplingParams(temperature=0.3, top_p=0.95, max_tokens=500)
    result = llm.generate(formatted_prompt, sampling_params)
    processing_time_ms = (time.time() - start_time) * 1000

    # Extract generated text from vLLM response
    summary = result[0].outputs[0].text.strip()

    return {
        "status": "success",
        "summary": summary,
        "word_count": len(summary.split()),
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "processing_time_ms": int(processing_time_ms),
    }


@remote(
    resource_config=gpu_config,
    dependencies=[
        "vllm>=0.2.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "transformers>=4.38.0",
        "torch>=2.1.0",
    ],
)
async def analyze_sentiment(input_data: dict) -> dict:
    """Analyze text sentiment using Langchain and local vLLM inference.

    Args:
        input_data: Dictionary containing 'text'

    Returns:
        Dictionary with sentiment analysis and structured output
    """
    import json

    from langchain_core.prompts import PromptTemplate
    from vllm import LLM, SamplingParams

    # Initialize vLLM model for this worker
    llm = LLM(
        model="mistralai/Mistral-7B-Instruct-v0.3",
        trust_remote_code=True,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.8,
        max_model_len=4096,
    )

    # Create structured analysis prompt
    template = """Analyze the sentiment of the following text.

Respond with a JSON object containing:
- label: 'positive', 'negative', or 'neutral'
- confidence: float between 0 and 1
- reasoning: brief explanation
- topics: list of 1-3 main topics detected
- action_required: boolean indicating if follow-up is needed

Text: {text}

JSON Response:"""

    prompt = PromptTemplate(template=template, input_variables=["text"])

    # Format the prompt
    formatted_prompt = prompt.format(text=input_data["text"])

    # Execute analysis with vLLM
    start_time = time.time()
    sampling_params = SamplingParams(temperature=0.2, top_p=0.95, max_tokens=500)
    result = llm.generate(formatted_prompt, sampling_params)
    processing_time_ms = (time.time() - start_time) * 1000

    # Extract generated text and parse as JSON
    response_text = result[0].outputs[0].text.strip()

    try:
        # Extract JSON if wrapped in markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        sentiment_data = json.loads(response_text.strip())
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        sentiment_data = {
            "label": "neutral",
            "confidence": 0.5,
            "reasoning": "Could not parse sentiment",
            "topics": [],
            "action_required": False,
        }

    return {
        "status": "success",
        "sentiment": sentiment_data,
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "processing_time_ms": int(processing_time_ms),
    }


@remote(
    resource_config=gpu_config,
    dependencies=[
        "vllm>=0.2.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "transformers>=4.38.0",
        "torch>=2.1.0",
    ],
)
async def transform_text(input_data: dict) -> dict:
    """Transform text using custom instructions with Langchain and local vLLM.

    This demonstrates dynamic prompting - users can provide any instruction.

    Args:
        input_data: Dictionary with 'text', 'instruction', and optional 'temperature'

    Returns:
        Dictionary with original, transformed text, and metadata
    """
    from langchain_core.prompts import PromptTemplate
    from vllm import LLM, SamplingParams

    # Initialize vLLM model for this worker
    llm = LLM(
        model="mistralai/Mistral-7B-Instruct-v0.3",
        trust_remote_code=True,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.8,
        max_model_len=4096,
    )

    # Get temperature from input or use default
    temperature = input_data.get("temperature", 0.7)

    # Create prompt template
    template = """Follow this instruction: {instruction}

Text to transform: {text}

Result:"""

    prompt = PromptTemplate(template=template, input_variables=["text", "instruction"])

    # Format the prompt
    formatted_prompt = prompt.format(
        text=input_data["text"], instruction=input_data["instruction"]
    )

    # Execute transformation with vLLM
    start_time = time.time()
    sampling_params = SamplingParams(
        temperature=temperature, top_p=0.95, max_tokens=500
    )
    result = llm.generate(formatted_prompt, sampling_params)
    processing_time_ms = (time.time() - start_time) * 1000

    # Extract generated text
    transformed = result[0].outputs[0].text.strip()

    return {
        "status": "success",
        "original_text": input_data["text"],
        "transformed_text": transformed,
        "instruction_used": input_data["instruction"],
        "temperature": temperature,
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "processing_time_ms": int(processing_time_ms),
    }


# ============================================================================
# PYDANTIC MODELS FOR REQUEST/RESPONSE VALIDATION
# ============================================================================


class SummarizeRequest(BaseModel):
    """Request model for text summarization."""

    text: str = Field(..., min_length=10, max_length=10000, description="Text to summarize")
    max_length: int = Field(
        default=150, ge=50, le=500, description="Maximum summary length in words"
    )

    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("Text cannot be empty or just whitespace")
        return v


class SummarizeResponse(BaseModel):
    """Response model for text summarization."""

    status: str = Field(description="Operation status")
    summary: str = Field(description="Generated summary")
    word_count: int = Field(description="Word count of summary")
    model: str = Field(description="LLM model used")
    processing_time_ms: int = Field(description="Processing time in milliseconds")


class SentimentRequest(BaseModel):
    """Request model for sentiment analysis."""

    text: str = Field(..., min_length=5, max_length=5000, description="Text to analyze")

    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("Text cannot be empty or just whitespace")
        return v


class SentimentData(BaseModel):
    """Structured sentiment analysis result."""

    label: str = Field(description="Sentiment label: positive, negative, or neutral")
    confidence: float = Field(description="Confidence score between 0 and 1", ge=0.0, le=1.0)
    reasoning: str = Field(description="Brief explanation of sentiment")
    topics: list[str] = Field(description="Main topics detected in text")
    action_required: bool = Field(description="Whether follow-up action is needed")


class SentimentResponse(BaseModel):
    """Response model for sentiment analysis."""

    status: str = Field(description="Operation status")
    sentiment: SentimentData = Field(description="Structured sentiment analysis")
    model: str = Field(description="LLM model used")
    processing_time_ms: int = Field(description="Processing time in milliseconds")


class TransformRequest(BaseModel):
    """Request model for text transformation."""

    text: str = Field(..., min_length=5, max_length=5000, description="Text to transform")
    instruction: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Transformation instruction (e.g., 'Translate to Spanish')",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM creativity (0=deterministic, 2=creative)",
    )

    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("Text cannot be empty or just whitespace")
        return v


class TransformResponse(BaseModel):
    """Response model for text transformation."""

    status: str = Field(description="Operation status")
    original_text: str = Field(description="Original input text")
    transformed_text: str = Field(description="Transformed output text")
    instruction_used: str = Field(description="Instruction that was applied")
    temperature: float = Field(description="Temperature used for generation")
    model: str = Field(description="LLM model used")
    processing_time_ms: int = Field(description="Processing time in milliseconds")


# ============================================================================
# FASTAPI ROUTER WITH ENDPOINTS
# ============================================================================


gpu_router = APIRouter()


@gpu_router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarize text",
    tags=["Text Processing"],
)
async def summarize_endpoint(request: SummarizeRequest) -> SummarizeResponse:
    """Summarize long text into key points.

    This endpoint uses Langchain with local vLLM inference (Mistral-7B)
    to generate concise summaries while preserving the main ideas.

    Args:
        request: SummarizeRequest with text and optional max_length

    Returns:
        SummarizeResponse with summary and metadata

    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(
            "Summarization request",
            text_length=len(request.text),
            max_length=request.max_length,
        )

        result = await summarize_text({"text": request.text, "max_length": request.max_length})

        logger.info("Summarization completed", word_count=result["word_count"])
        return SummarizeResponse(**result)

    except ValueError as e:
        logger.error("Validation error in summarize", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Summarization failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Text summarization failed. Check server logs.",
        ) from e


@gpu_router.post(
    "/analyze-sentiment",
    response_model=SentimentResponse,
    summary="Analyze text sentiment",
    tags=["Text Analysis"],
)
async def analyze_sentiment_endpoint(request: SentimentRequest) -> SentimentResponse:
    """Analyze sentiment of text with structured output.

    This endpoint uses Langchain with local vLLM inference to analyze
    sentiment and extract relevant topics and action items.

    Args:
        request: SentimentRequest with text to analyze

    Returns:
        SentimentResponse with structured sentiment data

    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info("Sentiment analysis request", text_length=len(request.text))

        result = await analyze_sentiment({"text": request.text})

        logger.info(
            "Sentiment analysis completed",
            sentiment_label=result["sentiment"]["label"],
        )
        return SentimentResponse(**result)

    except ValueError as e:
        logger.error("Validation error in sentiment analysis", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Sentiment analysis failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sentiment analysis failed. Check server logs.",
        ) from e


@gpu_router.post(
    "/transform",
    response_model=TransformResponse,
    summary="Transform text with custom instruction",
    tags=["Text Processing"],
)
async def transform_endpoint(request: TransformRequest) -> TransformResponse:
    """Transform text using custom instructions.

    This endpoint demonstrates dynamic prompting where users can provide
    any transformation instruction (translate, rephrase, formal, etc.).

    Args:
        request: TransformRequest with text, instruction, and optional temperature

    Returns:
        TransformResponse with original and transformed text

    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(
            "Text transformation request",
            text_length=len(request.text),
            instruction=request.instruction,
            temperature=request.temperature,
        )

        result = await transform_text(
            {
                "text": request.text,
                "instruction": request.instruction,
                "temperature": request.temperature,
            }
        )

        logger.info("Text transformation completed")
        return TransformResponse(**result)

    except ValueError as e:
        logger.error("Validation error in transform", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Text transformation failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Text transformation failed. Check server logs.",
        ) from e


# ============================================================================
# TESTING SUPPORT
# ============================================================================


if __name__ == "__main__":
    import asyncio

    async def test_worker():
        """Test workers locally without FastAPI."""
        print("Testing summarize_text worker...")
        try:
            result = await summarize_text(
                {
                    "text": "Artificial intelligence is rapidly transforming industries worldwide. "
                    "Machine learning algorithms can now recognize images, process natural language, and make decisions. "
                    "Deep learning networks have revolutionized computer vision and speech recognition. "
                    "AI applications range from healthcare diagnostics to autonomous vehicles.",
                    "max_length": 50,
                }
            )
            print("✓ Summarize result:", result)
        except Exception as e:
            print("✗ Summarize error:", str(e))

    asyncio.run(test_worker())
