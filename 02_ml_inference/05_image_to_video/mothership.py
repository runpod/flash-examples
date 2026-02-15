"""Mothership endpoint configuration."""

from runpod_flash import CpuLiveLoadBalancer

mothership = CpuLiveLoadBalancer(
    name="02_05_image_to_video-mothership",
)
