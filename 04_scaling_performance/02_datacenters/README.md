# 02_datacenters

Pin endpoints to specific RunPod data centers for latency, compliance, or availability reasons.

## Overview

By default, endpoints deploy across all available data centers. The `datacenter` parameter restricts placement to one or more specific DCs. CPU endpoints are limited to a subset of DCs that support CPU serverless (see `CPU_DATACENTERS`).

## Quick Start

```bash
pip install -r requirements.txt
flash run
```

## What You'll Learn

- How to pin a GPU endpoint to a single datacenter
- How to deploy across multiple datacenters
- How CPU datacenter restrictions work

## Available Data Centers

| ID | Location |
|----|----------|
| `US-GA-1` | US - Georgia |
| `US-KS-1` | US - Kansas |
| `US-TX-1` | US - Texas |
| `US-OR-1` | US - Oregon |
| `CA-MTL-1` | Canada - Montreal |
| `EU-NL-1` | Europe - Netherlands |
| `EU-CZ-1` | Europe - Czech Republic |
| `EU-RO-1` | Europe - Romania |
| `EU-NO-1` | Europe - Norway |
| `EU-SE-1` | Europe - Sweden |

CPU endpoints support: `EU-RO-1`, `US-TX-1`, `EU-SE-1`.

## Examples

**Single datacenter:**

```python
@Endpoint(name="us-worker", gpu=GpuGroup.ANY, datacenter=DataCenter.US_GA_1)
async def inference(data: dict) -> dict:
    ...
```

**Multiple datacenters:**

```python
@Endpoint(
    name="global-worker",
    gpu=GpuGroup.ANY,
    datacenter=[DataCenter.US_GA_1, DataCenter.EU_RO_1],
)
async def inference(data: dict) -> dict:
    ...
```

**No datacenter (default, all DCs):**

```python
@Endpoint(name="anywhere", gpu=GpuGroup.ANY)
async def inference(data: dict) -> dict:
    ...
```

## Project Structure

```
02_datacenters/
├── gpu_worker.py    # single-DC and multi-DC GPU endpoints
├── cpu_worker.py    # CPU endpoint in a supported DC
└── README.md
```
