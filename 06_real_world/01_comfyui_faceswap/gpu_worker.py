# ComfyUI SDXL character generation with face swapping.
# Mirrors the customer's Modal v3_character_realistic workflow:
# - Two checkpoints: CyberRealistic XL v7 (generation) + Juggernaut XI (InstantID)
# - LoRA pre-applied to CyberRealistic model at load time
# - Face swap: IPAdapter FaceID + Advanced -> KSampler -> InstantID -> DetailerForEach
# Run with: flash run
import logging
import os

from runpod_flash import GpuGroup, LiveServerless, NetworkVolume, remote

logger = logging.getLogger(__name__)

volume = NetworkVolume(name="comfyui-faceswap-example", size=100)

_env = {
    "COMFYUI_PATH": "/runpod-volume/comfyui",
    "HF_TOKEN": os.environ.get("HF_TOKEN", ""),
}

gpu_config = LiveServerless(
    name="comfyui-faceswap-example",
    gpus=[GpuGroup.AMPERE_80],
    workersMin=0,
    workersMax=3,
    idleTimeout=300,
    networkVolume=volume,
    env=_env,
)


@remote(
    resource_config=gpu_config,
    dependencies=[
        "torch",
        "torchvision",
        "torchaudio",
        "insightface",
        "onnxruntime-gpu",
        "safetensors",
        "Pillow",
        "huggingface_hub",
        "requests",
    ],
    system_dependencies=[
        "git",
        "libgl1",
        "libglib2.0-0",
        "cmake",
        "build-essential",
        "pkg-config",
    ],
)
class ComfyUICharacter:
    """SDXL character generation with optional face swapping via ComfyUI nodes.

    Mirrors the Modal v3_character_realistic workflow:
    - CyberRealistic XL v7 for initial generation (with LoRA pre-applied)
    - Juggernaut XI for InstantID face refinement
    - Face swap: IPAdapter FaceID + Advanced -> KSampler -> InstantID -> DetailerForEach
    """

    COMFYUI_PATH = "/runpod-volume/comfyui"
    # Bump when models/repos change to force re-download
    INSTALL_VERSION = "v5"
    SENTINEL_FILE = "/runpod-volume/comfyui/.install_complete"
    HF_TOKEN_FILE = "/runpod-volume/comfyui/.hf_token"

    CUSTOM_NODES = [
        "https://github.com/ltdrdata/ComfyUI-Impact-Pack",
        "https://github.com/ltdrdata/comfyui-impact-subpack",
        "https://github.com/cubiq/ComfyUI_IPAdapter_plus",
        "https://github.com/cubiq/ComfyUI_InstantID",
    ]

    # (hf_repo, hf_filename, dest_subdir, dest_filename)
    HF_MODELS = [
        # CyberRealistic XL v7 (primary generation checkpoint)
        (
            "cyberdelia/CyberRealisticXL",
            "CyberRealisticXLPlay_V7.0_FP16.safetensors",
            "models/checkpoints",
            "cyberrealistic_xl_v7.safetensors",
        ),
        # Juggernaut XI (used for InstantID face refinement only)
        (
            "RunDiffusion/Juggernaut-XI-v11",
            "Juggernaut-XI-byRunDiffusion.safetensors",
            "models/checkpoints",
            "Juggernaut-XI-byRunDiffusion.safetensors",
        ),
        # CLIP Vision (renamed to match Modal's expected filename)
        (
            "laion/CLIP-ViT-H-14-laion2B-s32B-b79K",
            "open_clip_model.safetensors",
            "models/clip_vision",
            "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
        ),
        (
            "h94/IP-Adapter-FaceID",
            "ip-adapter-faceid-plusv2_sdxl.bin",
            "models/ipadapter",
            "ip-adapter-faceid-plusv2_sdxl.bin",
        ),
        (
            "h94/IP-Adapter-FaceID",
            "ip-adapter-faceid-plusv2_sdxl_lora.safetensors",
            "models/loras",
            "ip-adapter-faceid-plusv2_sdxl_lora.safetensors",
        ),
        (
            "h94/IP-Adapter",
            "sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors",
            "models/ipadapter",
            "ip-adapter-plus-face_sdxl_vit-h.safetensors",
        ),
        (
            "InstantX/InstantID",
            "ControlNetModel/diffusion_pytorch_model.safetensors",
            "models/controlnet",
            "diffusion_pytorch_model_instantid.safetensors",
        ),
        (
            "InstantX/InstantID",
            "ip-adapter.bin",
            "models/instantid",
            "ip-adapter.bin",
        ),
        (
            "ybelkada/segment-anything",
            "checkpoints/sam_vit_b_01ec64.pth",
            "models/sams",
            "sam_vit_b_01ec64.pth",
        ),
        # InsightFace antelopev2 (for InstantID)
        (
            "lithiumice/insightface",
            "models/antelopev2/1k3d68.onnx",
            "models/insightface/models/antelopev2",
            "1k3d68.onnx",
        ),
        (
            "lithiumice/insightface",
            "models/antelopev2/2d106det.onnx",
            "models/insightface/models/antelopev2",
            "2d106det.onnx",
        ),
        (
            "lithiumice/insightface",
            "models/antelopev2/genderage.onnx",
            "models/insightface/models/antelopev2",
            "genderage.onnx",
        ),
        (
            "lithiumice/insightface",
            "models/antelopev2/glintr100.onnx",
            "models/insightface/models/antelopev2",
            "glintr100.onnx",
        ),
        (
            "lithiumice/insightface",
            "models/antelopev2/scrfd_10g_bnkps.onnx",
            "models/insightface/models/antelopev2",
            "scrfd_10g_bnkps.onnx",
        ),
        # InsightFace buffalo_l (for IPAdapter)
        (
            "lithiumice/insightface",
            "models/buffalo_l/1k3d68.onnx",
            "models/insightface/models/buffalo_l",
            "1k3d68.onnx",
        ),
        (
            "lithiumice/insightface",
            "models/buffalo_l/2d106det.onnx",
            "models/insightface/models/buffalo_l",
            "2d106det.onnx",
        ),
        (
            "lithiumice/insightface",
            "models/buffalo_l/det_10g.onnx",
            "models/insightface/models/buffalo_l",
            "det_10g.onnx",
        ),
        (
            "lithiumice/insightface",
            "models/buffalo_l/genderage.onnx",
            "models/insightface/models/buffalo_l",
            "genderage.onnx",
        ),
        (
            "lithiumice/insightface",
            "models/buffalo_l/w600k_r50.onnx",
            "models/insightface/models/buffalo_l",
            "w600k_r50.onnx",
        ),
    ]

    # (url, dest_subdir, dest_filename)
    URL_MODELS = [
        (
            "https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8m.pt",
            "models/ultralytics/bbox",
            "face_yolov8m.pt",
        ),
    ]

    def __init__(self):
        import logging
        import os

        self.logger = logging.getLogger(__name__)
        comfyui_path = os.environ.get("COMFYUI_PATH", self.COMFYUI_PATH)

        # Phase 0: Install system libraries needed by custom nodes.
        # Flash deploy doesn't process system_dependencies, so we install
        # them here. These are pre-built .deb packages (fast, ~5s).
        self._install_system_deps()

        # Phase 1: Clone repos + download models (cached on volume, skip if sentinel)
        sentinel_current = False
        if os.path.exists(self.SENTINEL_FILE):
            with open(self.SENTINEL_FILE) as f:
                sentinel_current = f.read().strip() == self.INSTALL_VERSION
        if not sentinel_current:
            self._clone_repos(comfyui_path)
            self._download_models(comfyui_path)
            with open(self.SENTINEL_FILE, "w") as f:
                f.write(self.INSTALL_VERSION)
            self.logger.info("Installation complete, sentinel written")
        else:
            self.logger.info("Sentinel current, skipping clone + download")

        # Phase 2: Initialize ComfyUI node system
        # (All pip packages are pre-baked in the Flash artifact — no pip
        # install needed on cold start.)
        self._init_comfyui_nodes(comfyui_path)

        # Phase 3: Load all models to GPU (mirrors Modal's post_restore)
        self._load_models()

        self.logger.info("ComfyUICharacter initialized successfully")

    async def generate(self, payload: dict) -> dict:
        """Generate a character image, optionally with face swapping.

        Mirrors Modal's generate endpoint. Wraps _generate with error handling.

        Args:
            payload: Dict with keys:
                - prompt (str): Character description
                - negative_prompt (str, optional): What to avoid
                - image_url (str, optional): Face reference URL for face swap
                - face_description (str, optional): Description of face to pick
                - width (int, optional): Image width (default 832)
                - height (int, optional): Image height (default 1216)
                - steps (int, optional): Sampling steps (default 35)
                - cfg (float, optional): CFG scale (default 2.0)
                - seed (int, optional): Random seed
        """
        try:
            return self._generate(
                prompt=payload.get("prompt", ""),
                negative_prompt=payload.get("negative_prompt", ""),
                image_url=payload.get("image_url"),
                face_description=payload.get("face_description", ""),
                seed=payload.get("seed"),
                width=payload.get("width", 832),
                height=payload.get("height", 1216),
                steps=payload.get("steps", 35),
                cfg=payload.get("cfg", 2.0),
            )
        except Exception as e:
            import traceback

            traceback.print_exc()
            return {"status": "error", "detail": str(e)}

    def _generate(
        self,
        prompt,
        negative_prompt="",
        image_url=None,
        face_description="",
        seed=None,
        width=832,
        height=1216,
        steps=35,
        cfg=2.0,
    ):
        """Run the full workflow. Mirrors Modal's _generate exactly."""
        import random
        import time

        import torch
        from nodes import CLIPTextEncode, EmptyLatentImage, KSampler, VAEDecode

        start_time = time.perf_counter()

        if seed is None:
            seed = random.randint(1, 2**63)

        self.logger.info(f"Generating with seed: {seed}")

        with torch.inference_mode():
            # Encode prompts using CyberRealistic's CLIP
            cliptextencode = CLIPTextEncode()
            pos = cliptextencode.encode(
                text=f"RAW photo, masterpiece, {prompt}",
                clip=self.clip,
            )[0]
            neg = cliptextencode.encode(
                text=f"(worst quality, low quality:1.4), {negative_prompt}",
                clip=self.clip,
            )[0]

            # Empty latent
            latent = EmptyLatentImage().generate(
                width=width, height=height, batch_size=1
            )[0]

            # Determine model to use
            if image_url:
                # Load reference image and apply IPAdapter pipeline
                ref_image = self._load_image_from_url(image_url)
                sampling_model = self._apply_ipadapter(ref_image)
            else:
                # No face swap: use LoRA'd CyberRealistic model directly
                sampling_model = self.lora_model

            # KSampler
            sampled = KSampler().sample(
                seed=seed,
                steps=steps,
                cfg=cfg,
                sampler_name="dpmpp_2m_sde",
                scheduler="karras",
                denoise=1.0,
                model=sampling_model,
                positive=pos,
                negative=neg,
                latent_image=latent,
            )[0]

            # VAE Decode using CyberRealistic's VAE
            decoded = VAEDecode().decode(samples=sampled, vae=self.vae)[0]

            # Face detailing if reference image provided
            if image_url:
                decoded = self._apply_face_pipeline(decoded, ref_image, pos, neg)

            image_b64 = self._image_to_base64(decoded)
            duration = round(time.perf_counter() - start_time, 2)

            return {
                "status": "success",
                "seed": seed,
                "image_base64": image_b64,
                "duration_seconds": duration,
            }

    # -------------------------------------------------------------------------
    # Private: Installation & setup
    # -------------------------------------------------------------------------

    def _install_system_deps(self):
        """Install system libraries needed by custom nodes.

        Flash deploy doesn't handle system_dependencies, so we install
        the required .deb packages here. These are pre-built .deb
        packages (~5s install).
        """
        import subprocess

        packages = [
            "libgl1",
            "libglib2.0-0",
            "libxcb1",
            "libx11-6",
            "libxext6",
            "libsm6",
            "git",
        ]
        self.logger.info(f"Installing system packages: {packages}")
        subprocess.run(
            ["apt-get", "update", "-qq"],
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            ["apt-get", "install", "-y", "-qq", "--no-install-recommends"] + packages,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.logger.warning(f"apt-get install had issues: {result.stderr[-300:]}")
        else:
            self.logger.info("System packages installed")

    def _run_cmd(self, cmd, description="command"):
        """Run a subprocess command with output logging."""
        import subprocess

        self.logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            self.logger.info(f"[{description}] stdout: {result.stdout[-2000:]}")
        if result.returncode != 0:
            self.logger.error(
                f"[{description}] failed (exit {result.returncode}): "
                f"{result.stderr[-2000:]}"
            )
            raise RuntimeError(
                f"{description} failed (exit {result.returncode}): "
                f"{result.stderr[-500:]}"
            )

    def _clone_repos(self, path):
        """Clone ComfyUI and custom node repos to the volume (one-time)."""
        import os

        comfyui_dir = os.path.join(path, "ComfyUI")
        os.makedirs(path, exist_ok=True)

        if not os.path.exists(comfyui_dir):
            self.logger.info(f"Cloning ComfyUI to {comfyui_dir}...")
            self._run_cmd(
                [
                    "git",
                    "clone",
                    "https://github.com/comfyanonymous/ComfyUI.git",
                    comfyui_dir,
                ],
                "git clone ComfyUI",
            )

        custom_nodes_dir = os.path.join(comfyui_dir, "custom_nodes")
        os.makedirs(custom_nodes_dir, exist_ok=True)

        for node_url in self.CUSTOM_NODES:
            node_name = node_url.rstrip("/").split("/")[-1]
            node_path = os.path.join(custom_nodes_dir, node_name)

            if os.path.exists(node_path):
                self.logger.info(f"Custom node exists, skipping: {node_name}")
                continue

            self.logger.info(f"Cloning custom node: {node_name}")
            self._run_cmd(
                ["git", "clone", node_url, node_path],
                f"git clone {node_name}",
            )

        self.logger.info("Repos cloned")

    def _download_models(self, path):
        """Download all required models to the network volume."""
        import os
        import shutil

        import requests
        from huggingface_hub import hf_hub_download

        comfyui_dir = os.path.join(path, "ComfyUI")

        # HF_TOKEN needed for gated models (e.g. Juggernaut-XI).
        # Read from volume file (written by setup_hf_token), then fallback to env.
        hf_token = ""
        if os.path.exists(self.HF_TOKEN_FILE):
            with open(self.HF_TOKEN_FILE) as f:
                hf_token = f.read().strip()
        if not hf_token:
            hf_token = os.environ.get("HF_TOKEN", "")
        if hf_token:
            self.logger.info("HF_TOKEN found, gated model access enabled")
        else:
            self.logger.warning("HF_TOKEN not set — gated models will fail to download")

        for hf_repo, hf_file, dest_subdir, dest_name in self.HF_MODELS:
            dest_dir = os.path.join(comfyui_dir, dest_subdir)
            dest_path = os.path.join(dest_dir, dest_name)

            if os.path.exists(dest_path):
                self.logger.info(f"Model exists, skipping: {dest_name}")
                continue

            os.makedirs(dest_dir, exist_ok=True)
            self.logger.info(f"Downloading {hf_repo}/{hf_file}...")
            downloaded = hf_hub_download(
                repo_id=hf_repo, filename=hf_file, token=hf_token
            )
            shutil.copy2(downloaded, dest_path)
            self.logger.info(f"Saved to {dest_path}")

        for url, dest_subdir, dest_name in self.URL_MODELS:
            dest_dir = os.path.join(comfyui_dir, dest_subdir)
            dest_path = os.path.join(dest_dir, dest_name)

            if os.path.exists(dest_path):
                self.logger.info(f"Model exists, skipping: {dest_name}")
                continue

            os.makedirs(dest_dir, exist_ok=True)
            self.logger.info(f"Downloading {url}...")
            resp = requests.get(url, timeout=600)
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                f.write(resp.content)
            self.logger.info(f"Saved to {dest_path}")

        self.logger.info("All models downloaded")

    def _init_comfyui_nodes(self, path):
        """Initialize ComfyUI's node system for programmatic access."""
        import os
        import sys

        # Monkey-patch insightface FaceAnalysis to accept 'providers' kwarg.
        # Newer insightface versions removed this parameter from __init__,
        # but ComfyUI custom nodes still pass it.
        try:
            from insightface.app import FaceAnalysis

            _orig_init = FaceAnalysis.__init__

            def _patched_init(self_fa, *args, providers=None, **kwargs):
                return _orig_init(self_fa, *args, **kwargs)

            FaceAnalysis.__init__ = _patched_init
            self.logger.info("Patched insightface FaceAnalysis for providers kwarg")
        except Exception as e:
            self.logger.warning(f"Could not patch insightface: {e}")

        comfyui_dir = os.path.join(path, "ComfyUI")

        # Add ComfyUI to Python path AND change working directory.
        # ComfyUI expects to be run from its own directory (its `utils/`
        # package conflicts with other `utils` modules in site-packages).
        if comfyui_dir not in sys.path:
            sys.path.insert(0, comfyui_dir)
        os.chdir(comfyui_dir)

        # Clear any cached `utils` module so ComfyUI's own `utils/` package
        # is found instead of a conflicting site-package module.
        for mod_name in list(sys.modules.keys()):
            if mod_name == "utils" or mod_name.startswith("utils."):
                del sys.modules[mod_name]

        # Force-load ComfyUI's utils package before anything else tries
        # to import it, preventing site-package `utils` from shadowing.
        import importlib.util

        utils_init = os.path.join(comfyui_dir, "utils", "__init__.py")
        if os.path.exists(utils_init):
            spec = importlib.util.spec_from_file_location("utils", utils_init)
            utils_mod = importlib.util.module_from_spec(spec)
            sys.modules["utils"] = utils_mod
            spec.loader.exec_module(utils_mod)

        # Initialize ComfyUI's internals
        import folder_paths  # noqa: F401 -- side effect: registers model paths
        import server

        # Set up model paths
        folder_paths.set_output_directory(os.path.join(comfyui_dir, "output"))

        # Create a minimal PromptServer (required for some custom nodes)
        loop = None
        try:
            import asyncio

            loop = asyncio.get_event_loop()
        except RuntimeError:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        server.PromptServer(loop)

        # Initialize built-in nodes
        import nodes

        nodes.init_extra_nodes()

        # Manually load custom nodes with proper package registration.
        # ComfyUI's init_extra_nodes() silently swallows import errors,
        # and some custom nodes need sys.modules registration before
        # relative imports work.
        custom_nodes_dir = os.path.join(comfyui_dir, "custom_nodes")
        node_load_errors = []

        for node_url in self.CUSTOM_NODES:
            node_name = node_url.rstrip("/").split("/")[-1]
            node_path = os.path.join(custom_nodes_dir, node_name)
            init_py = os.path.join(node_path, "__init__.py")

            if node_name in sys.modules:
                continue
            if not os.path.exists(init_py):
                node_load_errors.append(f"{node_name}: no __init__.py")
                continue

            # Register as a proper package so relative imports work
            spec = importlib.util.spec_from_file_location(
                node_name,
                init_py,
                submodule_search_locations=[node_path],
            )
            mod = importlib.util.module_from_spec(spec)
            mod.__package__ = node_name
            sys.modules[node_name] = mod

            try:
                spec.loader.exec_module(mod)
                # Register any discovered nodes
                if hasattr(mod, "NODE_CLASS_MAPPINGS"):
                    nodes.NODE_CLASS_MAPPINGS.update(mod.NODE_CLASS_MAPPINGS)
            except Exception as e:
                node_load_errors.append(f"{node_name}: {e}")
                del sys.modules[node_name]

        self.logger.info("ComfyUI node system initialized")

        from nodes import NODE_CLASS_MAPPINGS

        required_nodes = [
            "IPAdapterModelLoader",
            "IPAdapterInsightFaceLoader",
            "IPAdapterFaceID",
            "IPAdapterAdvanced",
            "InstantIDModelLoader",
            "InstantIDFaceAnalysis",
            "ApplyInstantIDAdvanced",
            "ImpactSimpleDetectorSEGS",
            "SEGSToImageList",
            "DetailerForEach",
            "SAMLoader",
            "UltralyticsDetectorProvider",
        ]
        missing = [n for n in required_nodes if n not in NODE_CLASS_MAPPINGS]
        if missing:
            diag = (
                f"Missing nodes: {missing}\n"
                f"Total loaded: {len(NODE_CLASS_MAPPINGS)}\n"
                f"Load errors: {node_load_errors}"
            )
            raise RuntimeError(diag)

        self.logger.info("All required custom nodes verified")

    def _load_models(self):
        """Load all models to GPU memory. Mirrors Modal's post_restore exactly."""
        from nodes import (
            NODE_CLASS_MAPPINGS,
            CheckpointLoaderSimple,
            CLIPVisionLoader,
            ControlNetLoader,
            LoraLoaderModelOnly,
        )

        self.logger.info("Loading models to GPU...")

        # Load CyberRealistic XL v7 checkpoint (primary generation model)
        self.logger.info("Loading checkpoint (CyberRealistic)...")
        self.model, self.clip, self.vae = CheckpointLoaderSimple().load_checkpoint(
            ckpt_name="cyberrealistic_xl_v7.safetensors"
        )

        # Load Juggernaut XI checkpoint (used for InstantID only)
        self.logger.info("Loading checkpoint (Juggernaut)...")
        (
            self.model_jugg,
            self.clip_jugg,
            self.vae_jugg,
        ) = CheckpointLoaderSimple().load_checkpoint(
            ckpt_name="Juggernaut-XI-byRunDiffusion.safetensors"
        )

        # Load CLIP Vision
        self.logger.info("Loading CLIP Vision...")
        self.clip_vision = CLIPVisionLoader().load_clip(
            clip_name="CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
        )[0]

        # Pre-apply LoRA to CyberRealistic model (strength 0.4)
        self.logger.info("Loading LoRA...")
        self.lora_model = LoraLoaderModelOnly().load_lora_model_only(
            lora_name="ip-adapter-faceid-plusv2_sdxl_lora.safetensors",
            strength_model=0.4,
            model=self.model,
        )[0]

        # Load ControlNet for InstantID
        self.logger.info("Loading ControlNet...")
        self.controlnet = ControlNetLoader().load_controlnet(
            control_net_name="diffusion_pytorch_model_instantid.safetensors"
        )[0]

        # Load IPAdapter models
        self.logger.info("Loading IPAdapter models...")
        IPAdapterModelLoader = NODE_CLASS_MAPPINGS["IPAdapterModelLoader"]
        ipadapter_loader = IPAdapterModelLoader()
        self.ipadapter_faceid = ipadapter_loader.load_ipadapter_model(
            ipadapter_file="ip-adapter-faceid-plusv2_sdxl.bin"
        )[0]
        self.ipadapter_plus = ipadapter_loader.load_ipadapter_model(
            ipadapter_file="ip-adapter-plus-face_sdxl_vit-h.safetensors"
        )[0]

        # Load InsightFace for IPAdapter
        self.logger.info("Loading InsightFace...")
        IPAdapterInsightFaceLoader = NODE_CLASS_MAPPINGS["IPAdapterInsightFaceLoader"]
        self.insightface = IPAdapterInsightFaceLoader().load_insightface(
            provider="CUDA", model_name="buffalo_l"
        )[0]

        # Load InstantID
        self.logger.info("Loading InstantID...")
        InstantIDModelLoader = NODE_CLASS_MAPPINGS["InstantIDModelLoader"]
        self.instantid_model = InstantIDModelLoader().load_model(
            instantid_file="ip-adapter.bin"
        )[0]

        InstantIDFaceAnalysis = NODE_CLASS_MAPPINGS["InstantIDFaceAnalysis"]
        self.instantid_face = InstantIDFaceAnalysis().load_insight_face(
            provider="CUDA"
        )[0]

        # Load SAM
        self.logger.info("Loading SAM...")
        SAMLoader = NODE_CLASS_MAPPINGS["SAMLoader"]
        self.sam_model = SAMLoader().load_model(
            model_name="sam_vit_b_01ec64.pth", device_mode="AUTO"
        )[0]

        # Load Ultralytics detector
        self.logger.info("Loading Ultralytics detector...")
        UltralyticsDetectorProvider = NODE_CLASS_MAPPINGS["UltralyticsDetectorProvider"]
        self.detector = UltralyticsDetectorProvider().doit(
            model_name="bbox/face_yolov8m.pt"
        )[0]

        self.logger.info("All models loaded to GPU")

    # -------------------------------------------------------------------------
    # Private: Image utilities
    # -------------------------------------------------------------------------

    def _load_image_from_url(self, url):
        """Download image from URL and convert to ComfyUI tensor (B,H,W,C).

        Replaces Modal's proprietary LoadImageAdvanced node.
        """
        import io

        import numpy as np
        import requests
        import torch
        from PIL import Image

        headers = {"User-Agent": "ComfyUI-Character/1.0"}
        resp = requests.get(url, timeout=60, headers=headers)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")

        # Convert to ComfyUI format: float32 tensor (1, H, W, 3) in [0, 1]
        img_array = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array).unsqueeze(0)

        return img_tensor

    def _image_to_base64(self, tensor):
        """Convert ComfyUI image tensor (B,H,W,C) to base64 PNG.

        Replaces Modal's proprietary WatermarkAndUpload node.
        """
        import base64
        import io

        import numpy as np
        from PIL import Image

        img_array = tensor[0].detach().cpu().numpy()
        img_array = (img_array * 255).clip(0, 255).astype(np.uint8)
        img = Image.fromarray(img_array)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _pick_largest_face(self, segs):
        """Pick the largest detected face by bounding box area.

        Replaces Modal's proprietary FacePickerNode + ImpactSEGSPicker.
        Takes SEGS data (header, seg_list) and returns filtered SEGS with
        only the largest face.
        """
        seg_header, seg_list = segs

        if not seg_list:
            self.logger.warning("No faces detected")
            return segs

        largest_idx = 0
        largest_area = 0
        for i, seg in enumerate(seg_list):
            x1, y1, x2, y2 = seg.crop_region
            area = (x2 - x1) * (y2 - y1)
            if area > largest_area:
                largest_area = area
                largest_idx = i

        self.logger.info(
            f"Picked face {largest_idx + 1}/{len(seg_list)} (area={largest_area}px)"
        )
        return (seg_header, [seg_list[largest_idx]])

    # -------------------------------------------------------------------------
    # Private: Face swap pipeline
    # -------------------------------------------------------------------------

    def _apply_ipadapter(self, ref_image):
        """Apply IPAdapter FaceID + IPAdapter Advanced to LoRA'd model.

        Mirrors Modal's face-swap model conditioning. Uses the pre-applied
        LoRA model (CyberRealistic + LoRA) as the base.
        """
        from nodes import NODE_CLASS_MAPPINGS

        # IPAdapterFaceID on LoRA'd CyberRealistic model
        IPAdapterFaceID = NODE_CLASS_MAPPINGS["IPAdapterFaceID"]
        model_after_faceid = IPAdapterFaceID().apply_ipadapter(
            weight=0.3,
            weight_faceidv2=0.3,
            weight_type="linear",
            combine_embeds="concat",
            start_at=0.0,
            end_at=1.0,
            embeds_scaling="V only",
            model=self.lora_model,
            ipadapter=self.ipadapter_faceid,
            image=ref_image,
            clip_vision=self.clip_vision,
            insightface=self.insightface,
        )

        # IPAdapterAdvanced (plus-face model)
        IPAdapterAdvanced = NODE_CLASS_MAPPINGS["IPAdapterAdvanced"]
        model_after_advanced = IPAdapterAdvanced().apply_ipadapter(
            weight=0.3,
            weight_type="linear",
            combine_embeds="concat",
            start_at=0.0,
            end_at=1.0,
            embeds_scaling="V only",
            model=model_after_faceid[0],
            ipadapter=self.ipadapter_plus,
            image=ref_image,
            clip_vision=self.clip_vision,
        )

        return model_after_advanced[0]

    def _apply_face_pipeline(self, decoded, ref_image, pos, neg):
        """Detect faces, apply InstantID + DetailerForEach.

        Mirrors Modal's face refinement pipeline:
        1. Detect faces with YOLO + SAM
        2. Pick largest face (replaces FacePickerNode + ImpactSEGSPicker)
        3. Extract face keypoint image
        4. Apply InstantID using Juggernaut model
        5. Inpaint face region with DetailerForEach
        """
        import random

        from nodes import NODE_CLASS_MAPPINGS

        ImpactSimpleDetectorSEGS = NODE_CLASS_MAPPINGS["ImpactSimpleDetectorSEGS"]
        SEGSToImageList = NODE_CLASS_MAPPINGS["SEGSToImageList"]
        ApplyInstantIDAdvanced = NODE_CLASS_MAPPINGS["ApplyInstantIDAdvanced"]
        DetailerForEach = NODE_CLASS_MAPPINGS["DetailerForEach"]

        # Step 1: Detect faces
        segs = ImpactSimpleDetectorSEGS().doit(
            bbox_threshold=0.5,
            bbox_dilation=0,
            crop_factor=2.5,
            drop_size=10,
            sub_threshold=0.5,
            sub_dilation=0,
            sub_bbox_expansion=0,
            sam_mask_hint_threshold=0.7,
            post_dilation=0,
            bbox_detector=self.detector,
            image=decoded,
            sam_model_opt=self.sam_model,
        )[0]

        # Step 2: Pick largest face (replaces FacePickerNode + ImpactSEGSPicker)
        picked_segs = self._pick_largest_face(segs)
        _, seg_list = picked_segs
        if not seg_list:
            self.logger.warning("No faces detected, skipping face pipeline")
            return decoded

        # Step 3: Get face keypoint image for InstantID
        face_images = SEGSToImageList().doit(segs=picked_segs)
        face_image = face_images[0][0]

        # Step 4: Apply InstantID using Juggernaut model
        instantid_result = ApplyInstantIDAdvanced().apply_instantid(
            ip_weight=0.85,
            cn_strength=0.7,
            start_at=0.0,
            end_at=1.0,
            noise=1.0,
            combine_embeds="concat",
            instantid=self.instantid_model,
            insightface=self.instantid_face,
            control_net=self.controlnet,
            image=ref_image,
            model=self.model_jugg,
            positive=pos,
            negative=neg,
            image_kps=face_image,
        )

        # Step 5: DetailerForEach face inpainting
        detailed = DetailerForEach().doit(
            guide_size=1024.0,
            guide_size_for=True,
            max_size=1024.0,
            seed=random.randint(1, 2**63),
            steps=20,
            cfg=2.0,
            sampler_name="dpmpp_2m_sde",
            scheduler="karras",
            denoise=0.6,
            feather=5,
            noise_mask=True,
            force_inpaint=True,
            wildcard="",
            cycle=1,
            inpaint_model=False,
            noise_mask_feather=20,
            tiled_encode=False,
            tiled_decode=False,
            image=decoded,
            segs=picked_segs,
            model=instantid_result[0],
            clip=self.clip,
            vae=self.vae,
            positive=instantid_result[1],
            negative=instantid_result[2],
        )[0]

        return detailed


@remote(resource_config=gpu_config)
async def setup_hf_token(payload: dict) -> dict:
    """Write HF_TOKEN to network volume so the worker can access gated models.

    Must be called before ComfyUICharacter is instantiated.
    The token persists on the volume across cold starts.
    """
    import os

    token = payload.get("token", "")
    token_file = "/runpod-volume/comfyui/.hf_token"

    os.makedirs(os.path.dirname(token_file), exist_ok=True)
    with open(token_file, "w") as f:
        f.write(token)

    return {"status": "ok", "token_length": len(token)}


if __name__ == "__main__":
    import asyncio

    async def test():
        print("=== Testing ComfyUI Character Generation ===")
        worker = ComfyUICharacter()

        # Test generation without face swap (uses LoRA'd CyberRealistic)
        print("\n--- Generation without face swap ---")
        result = await worker.generate(
            {
                "prompt": "a young woman with red hair in a medieval setting",
                "width": 832,
                "height": 1216,
                "steps": 35,
                "cfg": 2.0,
            }
        )
        print(f"Status: {result['status']}")
        if "duration_seconds" in result:
            print(f"Duration: {result['duration_seconds']}s")
        if "image_base64" in result:
            print(f"Image base64 length: {len(result['image_base64'])} chars")

    asyncio.run(test())
