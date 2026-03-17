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
| `US-CA-2` | US - California |
| `US-GA-2` | US - Georgia |
| `US-IL-1` | US - Illinois |
| `US-KS-2` | US - Kansas |
| `US-MD-1` | US - Maryland |
| `US-MO-1` | US - Missouri |
| `US-MO-2` | US - Missouri |
| `US-NC-1` | US - North Carolina |
| `US-NC-2` | US - North Carolina |
| `US-NE-1` | US - Nebraska |
| `US-WA-1` | US - Washington |
| `EU-CZ-1` | Europe - Czech Republic |
| `EU-RO-1` | Europe - Romania |
| `EUR-IS-1` | Europe - Iceland |
| `EUR-NO-1` | Europe - Norway |

CPU endpoints support: `EU-RO-1`.

## Examples

**Single datacenter:**

```python
@Endpoint(name="us-worker", gpu=GpuGroup.ANY, datacenter=DataCenter.US_GA_2)
async def inference(data: dict) -> dict:
    ...
```

**Multiple datacenters:**

```python
@Endpoint(
    name="global-worker",
    gpu=GpuGroup.ANY,
    datacenter=[DataCenter.US_GA_2, DataCenter.EU_RO_1],
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
