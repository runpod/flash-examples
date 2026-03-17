# gpu workers pinned to specific datacenters.
# run with: flash run
from runpod_flash import Endpoint, GpuGroup, DataCenter


# pin to a single datacenter
@Endpoint(
    name="04_02_gpu_us",
    gpu=GpuGroup.ANY,
    workers=(0, 3),
    datacenter=DataCenter.US_GA_2,
)
async def us_inference(payload: dict) -> dict:
    """GPU inference pinned to US-GA-2."""
    return {"datacenter": "US-GA-2", "result": payload}


# deploy across multiple datacenters for broader availability
@Endpoint(
    name="04_02_gpu_multi",
    gpu=GpuGroup.ANY,
    workers=(0, 3),
    datacenter=[DataCenter.US_GA_2, DataCenter.EU_RO_1],
)
async def multi_dc_inference(payload: dict) -> dict:
    """GPU inference available in US-GA-2 and EU-RO-1."""
    return {"result": payload}


if __name__ == "__main__":
    import asyncio

    async def test():
        print("=== US datacenter ===")
        print(await us_inference({"prompt": "hello"}))
        print("\n=== Multi-DC ===")
        print(await multi_dc_inference({"prompt": "hello"}))

    asyncio.run(test())
