from tetra_rp import CpuLiveLoadBalancer, remote

cpu_config = CpuLiveLoadBalancer(
    name="03_05_load_balancer_cpu",
)


@remote(cpu_config, method="GET", path="/health")
async def cpu_health() -> dict:
    """Health check endpoint for CPU service."""
    return {"status": "healthy", "service": "cpu"}


@remote(cpu_config, method="POST", path="/validate")
async def validate_data(text: str) -> dict:
    """Validate and analyze text data.

    Args:
        text: Text to validate

    Returns:
        Validation results
    """
    import time
    from datetime import datetime, timezone

    if not text or not text.strip():
        raise ValueError("text cannot be empty")

    start_time = time.time()

    # Simple text analysis
    words = text.split()
    char_count = len(text)
    word_count = len(words)
    avg_word_length = char_count / word_count if word_count > 0 else 0

    process_time = (time.time() - start_time) * 1000

    return {
        "status": "success",
        "is_valid": True,
        "character_count": char_count,
        "word_count": word_count,
        "average_word_length": round(avg_word_length, 2),
        "process_time_ms": round(process_time, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@remote(cpu_config, method="POST", path="/transform")
async def transform_data(text: str, operation: str = "uppercase") -> dict:
    """Transform text data.

    Args:
        text: Text to transform
        operation: Transform operation (uppercase, lowercase, reverse, title)

    Returns:
        Transformed text
    """
    import time
    from datetime import datetime, timezone

    if not text or not text.strip():
        raise ValueError("text cannot be empty")

    valid_operations = ["uppercase", "lowercase", "reverse", "title"]

    if operation not in valid_operations:
        raise ValueError(f"operation must be one of: {', '.join(valid_operations)}")

    start_time = time.time()
    result = ""

    # Perform transformation
    if operation == "uppercase":
        result = text.upper()
    elif operation == "lowercase":
        result = text.lower()
    elif operation == "reverse":
        result = text[::-1]
    elif operation == "title":
        result = text.title()

    process_time = (time.time() - start_time) * 1000

    return {
        "status": "success",
        "original": text,
        "transformed": result,
        "operation": operation,
        "process_time_ms": round(process_time, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Test locally with: python -m workers.cpu.endpoint
if __name__ == "__main__":
    import asyncio

    async def test():
        print("Testing CPU worker endpoints...\n")

        print("1. Health check:")
        result = await cpu_health()
        print(f"   {result}\n")

        print("2. Validate text:")
        result = await validate_data("Hello world from load balancer")
        print(f"   Characters: {result['character_count']}")
        print(f"   Words: {result['word_count']}\n")

        print("3. Transform text:")
        result = await transform_data("Hello World", "uppercase")
        print(f"   Original: {result['original']}")
        print(f"   Transformed: {result['transformed']}")

    asyncio.run(test())
