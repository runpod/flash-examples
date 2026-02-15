"""Mothership endpoint configuration."""

from runpod_flash import CpuLiveLoadBalancer

mothership = CpuLiveLoadBalancer(
    name="02_03_image_to_image-mothership",
)
