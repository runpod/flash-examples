# CPU serverless worker that factors its logic across local (non-pip) modules.
# run locally with: flash dev   |   deploy with: flash deploy
from runpod_flash import CpuInstanceType, Endpoint


@Endpoint(
    name="01_05_local_modules",
    cpu=CpuInstanceType.CPU3C_1_2,
)
async def greet(name: str = "world", lang: str = "en") -> dict:
    """Greeting endpoint whose logic lives in local sibling + package modules.

    The imports are inside the function body on purpose. On the live path
    (`flash dev` / `.run()`) only the function source plus its local-module
    closure are shipped to the worker, so imports must resolve at call time.
    The same code works unchanged for `flash deploy` (the whole tree is bundled).
    """
    from datetime import datetime

    import text_utils
    from greetings import render

    return {
        "status": "success",
        "greeting": text_utils.shout(render(name, lang)),
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(greet(name="Flash", lang="es"))
    print(result)
