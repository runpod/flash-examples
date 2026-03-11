# ComfyUI SDXL character generation with face swapping.
# Extracted from gpu_worker.py for Docker-based deployment.
#
# Key differences from gpu_worker.py (Flash version):
# - No @remote decorator — runs directly in a Docker container
# - No _install_system_deps() — system deps baked into Docker image
# - No _clone_repos() — ComfyUI + custom nodes baked into Docker image
# - ComfyUI lives at /comfyui (in Docker image), models at /runpod-volume/
# - generate() is synchronous (RunPod handler doesn't need async)
import logging
import os

logger = logging.getLogger(__name__)


class ComfyUICharacter:
    """SDXL character generation with optional face swapping via ComfyUI nodes.

    Mirrors the Modal v3_character_realistic workflow:
    - CyberRealistic XL v7 for initial generation (with LoRA pre-applied)
    - Juggernaut XI for InstantID face refinement
    - Face swap: IPAdapter FaceID + Advanced -> KSampler -> InstantID -> DetailerForEach
    """

    # ComfyUI is baked into the Docker image at /comfyui
    COMFYUI_PATH = "/comfyui"
    # Models: use baked-in path if available (NVMe), else network volume
    BAKED_MODELS_PATH = "/baked-models"
    MODELS_PATH = (
        BAKED_MODELS_PATH
        if os.path.exists(os.path.join(BAKED_MODELS_PATH, "models", "checkpoints"))
        else "/runpod-volume/comfyui/ComfyUI"
    )
    # Bump when models change to force re-download
    INSTALL_VERSION = "v5"
    SENTINEL_FILE = (
        os.path.join(BAKED_MODELS_PATH, "comfyui", ".install_complete")
        if os.path.exists(os.path.join(BAKED_MODELS_PATH, "comfyui"))
        else "/runpod-volume/comfyui/.install_complete"
    )
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
        self.logger = logging.getLogger(__name__)
        comfyui_path = self.COMFYUI_PATH
        models_path = self.MODELS_PATH

        if models_path == self.BAKED_MODELS_PATH:
            self.logger.info(f"Using baked-in models from {models_path} (NVMe)")
        else:
            self.logger.info(f"Using network volume models from {models_path}")

        # Phase 1: Download models to network volume (cached, skip if sentinel)
        sentinel_current = False
        if os.path.exists(self.SENTINEL_FILE):
            with open(self.SENTINEL_FILE) as f:
                sentinel_current = f.read().strip() == self.INSTALL_VERSION
        if not sentinel_current:
            self._download_models(models_path)
            os.makedirs(os.path.dirname(self.SENTINEL_FILE), exist_ok=True)
            with open(self.SENTINEL_FILE, "w") as f:
                f.write(self.INSTALL_VERSION)
            self.logger.info("Installation complete, sentinel written")
        else:
            self.logger.info("Sentinel current, skipping model download")

        # Phase 2: Initialize ComfyUI node system
        self._init_comfyui_nodes(comfyui_path, models_path)

        # Phase 3: Load all models to GPU
        self._load_models()

        self.logger.info("ComfyUICharacter initialized successfully")

    def generate(self, payload: dict) -> dict:
        """Generate a character image, optionally with face swapping.

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
                - output (dict, optional): Output configuration
                    - include_base64 (bool, default true): Include base64 image in response
                    - save_to_volume (bool, default false): Save image to network volume
                    - volume_path (str, default "outputs"): Folder relative to /runpod-volume/
        """
        try:
            output_config = payload.get("output", {})
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
                include_base64=output_config.get("include_base64", True),
                save_to_volume=output_config.get("save_to_volume", False),
                volume_path=output_config.get("volume_path", "outputs"),
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
        include_base64=True,
        save_to_volume=False,
        volume_path="outputs",
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

            duration = round(time.perf_counter() - start_time, 2)

            result = {
                "status": "success",
                "seed": seed,
                "duration_seconds": duration,
            }

            if include_base64:
                result["image_base64"] = self._image_to_base64(decoded)

            if save_to_volume:
                result["image_path"] = self._save_to_volume(decoded, seed, volume_path)

            return result

    # -------------------------------------------------------------------------
    # Private: Installation & setup
    # -------------------------------------------------------------------------

    def _download_models(self, models_path):
        """Download all required models to the network volume."""
        import shutil

        import requests
        from huggingface_hub import hf_hub_download

        # HF_TOKEN needed for gated models (e.g. Juggernaut-XI).
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
            dest_dir = os.path.join(models_path, dest_subdir)
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
            dest_dir = os.path.join(models_path, dest_subdir)
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

    def _init_comfyui_nodes(self, comfyui_path, models_path):
        """Initialize ComfyUI's node system for programmatic access.

        Args:
            comfyui_path: Path to ComfyUI installation (in Docker image)
            models_path: Path to models directory (on network volume)
        """
        import importlib.util
        import sys

        # Add ComfyUI to Python path AND change working directory.
        # ComfyUI expects to be run from its own directory.
        if comfyui_path not in sys.path:
            sys.path.insert(0, comfyui_path)
        os.chdir(comfyui_path)

        # Force ComfyUI to keep all models in GPU memory (equivalent to
        # --highvram --gpu-only CLI flags). Without this, ComfyUI offloads
        # models to CPU after each use and reloads them on the next request,
        # causing ~70-90s overhead per request on serverless.
        from comfy import cli_args

        cli_args.args.highvram = True
        cli_args.args.gpu_only = True

        # Clear any cached `utils` module so ComfyUI's own `utils/` package
        # is found instead of a conflicting site-package module.
        for mod_name in list(sys.modules.keys()):
            if mod_name == "utils" or mod_name.startswith("utils."):
                del sys.modules[mod_name]

        # Force-load ComfyUI's utils package before anything else tries
        # to import it, preventing site-package `utils` from shadowing.
        utils_init = os.path.join(comfyui_path, "utils", "__init__.py")
        if os.path.exists(utils_init):
            spec = importlib.util.spec_from_file_location("utils", utils_init)
            utils_mod = importlib.util.module_from_spec(spec)
            sys.modules["utils"] = utils_mod
            spec.loader.exec_module(utils_mod)

        # Initialize ComfyUI's internals
        import folder_paths
        import server

        # Point ComfyUI at the network volume's model directories
        model_dirs = [
            "checkpoints",
            "clip_vision",
            "controlnet",
            "ipadapter",
            "instantid",
            "loras",
            "sams",
            "insightface",
            "ultralytics",
        ]
        for model_dir in model_dirs:
            volume_model_path = os.path.join(models_path, "models", model_dir)
            if os.path.exists(volume_model_path):
                folder_paths.add_model_folder_path(model_dir, volume_model_path)

        # Symlink volume model dirs into ComfyUI's models_dir so plugins
        # that construct paths directly from folder_paths.models_dir can
        # find them (e.g. ComfyUI_IPAdapter_plus for insightface/ultralytics).
        comfyui_models_dir = os.path.join(comfyui_path, "models")
        for model_dir in model_dirs:
            volume_model_path = os.path.join(models_path, "models", model_dir)
            comfyui_model_path = os.path.join(comfyui_models_dir, model_dir)
            if not os.path.exists(volume_model_path):
                continue
            if os.path.islink(comfyui_model_path):
                continue  # Already a symlink
            if os.path.isdir(comfyui_model_path) and not os.listdir(comfyui_model_path):
                # Empty dir from base image — remove it so we can symlink
                os.rmdir(comfyui_model_path)
            if not os.path.exists(comfyui_model_path):
                self.logger.info(
                    f"Symlinking {comfyui_model_path} -> {volume_model_path}"
                )
                os.symlink(volume_model_path, comfyui_model_path)

        folder_paths.set_output_directory(os.path.join(comfyui_path, "output"))

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

        # Initialize built-in nodes (init_extra_nodes is async in latest ComfyUI).
        # Use nest_asyncio to allow run_until_complete inside RunPod's event loop.
        import nest_asyncio
        import nodes

        nest_asyncio.apply()
        result = nodes.init_extra_nodes()
        if asyncio.iscoroutine(result):
            loop.run_until_complete(result)

        # Manually load custom nodes with proper package registration.
        custom_nodes_dir = os.path.join(comfyui_path, "custom_nodes")
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
        self.logger.info("Loading InsightFace (buffalo_l)...")
        # insightface 0.7.3 expects root/models/{name}/*.onnx
        vol_insightface = os.path.join(self.MODELS_PATH, "models", "insightface")

        from insightface.app import FaceAnalysis

        model = FaceAnalysis(
            name="buffalo_l",
            root=vol_insightface,
        )
        model.prepare(ctx_id=0, det_size=(640, 640))
        self.insightface = model

        # Load InstantID
        self.logger.info("Loading InstantID...")
        InstantIDModelLoader = NODE_CLASS_MAPPINGS["InstantIDModelLoader"]
        self.instantid_model = InstantIDModelLoader().load_model(
            instantid_file="ip-adapter.bin"
        )[0]

        # Load InsightFace antelopev2 for InstantID
        self.logger.info("Loading InsightFace (antelopev2) for InstantID...")
        model_antelope = FaceAnalysis(
            name="antelopev2",
            root=vol_insightface,
        )
        model_antelope.prepare(ctx_id=0, det_size=(640, 640))
        self.instantid_face = model_antelope

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
        """Download image from URL and convert to ComfyUI tensor (B,H,W,C)."""
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
        """Convert ComfyUI image tensor (B,H,W,C) to base64 PNG."""
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

    def _save_to_volume(self, tensor, seed, output_path):
        """Save ComfyUI image tensor to network volume as PNG. Returns the file path."""
        import time

        import numpy as np
        from PIL import Image

        folder = f"/runpod-volume/{output_path.strip('/')}"
        os.makedirs(folder, exist_ok=True)

        timestamp = int(time.time())
        filename = f"{seed}_{timestamp}.png"
        filepath = os.path.join(folder, filename)

        img_array = tensor[0].detach().cpu().numpy()
        img_array = (img_array * 255).clip(0, 255).astype(np.uint8)
        img = Image.fromarray(img_array)
        img.save(filepath, format="PNG")

        self.logger.info(f"Saved image to {filepath}")
        return filepath

    def _pick_largest_face(self, segs):
        """Pick the largest detected face by bounding box area."""
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
        """Apply IPAdapter FaceID + IPAdapter Advanced to LoRA'd model."""
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
        """Detect faces, apply InstantID + DetailerForEach."""
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

        # Step 2: Pick largest face
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
