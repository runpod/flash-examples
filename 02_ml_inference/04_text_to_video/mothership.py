"""Mothership endpoint configuration."""

from runpod_flash import CpuLiveLoadBalancer

mothership = CpuLiveLoadBalancer(
    name="02_04_text_to_video-mothership",
)
