from tetra_rp import NetworkVolume

# Shared volume used by both GPU and CPU workers.
volume = NetworkVolume(
    name="flash-05-volume",
    size=50,  # in GB
)
