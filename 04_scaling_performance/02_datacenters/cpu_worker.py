# cpu worker pinned to a cpu-supported datacenter.
# cpu endpoints are only available in a subset of datacenters
# (see CPU_DATACENTERS). selecting an unsupported DC raises an error.
# run with: flash run
from runpod_flash import Endpoint, DataCenter

api = Endpoint(
    name="04_02_cpu_eu",
    cpu="cpu3c-2-4",
    workers=(0, 2),
    datacenter=DataCenter.EU_RO_1,
)


@api.post("/process")
async def process(data: dict) -> dict:
    """CPU processing pinned to EU-RO-1."""
    return {"datacenter": "EU-RO-1", "result": data}


@api.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(process({"text": "hello"})))
