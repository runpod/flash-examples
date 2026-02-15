"""Mothership Endpoint Configuration"""

from runpod_flash import CpuLiveLoadBalancer

mothership = CpuLiveLoadBalancer(
    name="02_02_text_to_image-mothership",
)
