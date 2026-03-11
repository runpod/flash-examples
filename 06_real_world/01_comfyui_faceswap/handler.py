# RunPod serverless handler for ComfyUI character generation.
# Initializes ComfyUICharacter at startup (not on first request) to avoid
# execution timeout — model loading happens during container startup phase.
import logging
import os
import sys
import traceback

import runpod

# Ensure handler's directory is on the Python path so comfyui_character is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from comfyui_character import ComfyUICharacter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)


def handle_debug_env(job_input):
    """Return environment/dependency info without initializing ComfyUI."""
    import glob
    import inspect

    import insightface
    import onnxruntime

    result = {
        "insightface_version": insightface.__version__,
        "onnxruntime_version": onnxruntime.__version__,
        "onnxruntime_providers": onnxruntime.get_available_providers(),
        "python_version": sys.version,
        "insightface_init_sig": str(
            inspect.signature(insightface.app.FaceAnalysis.__init__)
        ),
    }
    vol = "/runpod-volume/comfyui/ComfyUI/models/insightface"
    model_dir = os.path.join(vol, "models", "buffalo_l")
    result["model_dir_exists"] = os.path.exists(model_dir)
    result["onnx_files"] = glob.glob(os.path.join(model_dir, "*.onnx"))
    try:
        from insightface.app import FaceAnalysis

        model = FaceAnalysis(name="buffalo_l", root=vol)
        model.prepare(ctx_id=0, det_size=(640, 640))
        result["load_success"] = True
        result["models_loaded"] = list(model.models.keys())
    except Exception as e:
        result["load_success"] = False
        result["load_error"] = str(e)
        result["load_traceback"] = traceback.format_exc()
    return result


def handle_debug_fs(job_input):
    """Return filesystem state for diagnostics."""
    result = {}
    paths_to_check = [
        "/runpod-volume",
        "/runpod-volume/comfyui",
        "/runpod-volume/comfyui/ComfyUI",
        "/runpod-volume/comfyui/ComfyUI/models",
        "/runpod-volume/comfyui/ComfyUI/models/insightface",
        "/runpod-volume/comfyui/ComfyUI/models/insightface/models",
        "/runpod-volume/comfyui/ComfyUI/models/insightface/models/buffalo_l",
        "/runpod-volume/comfyui/ComfyUI/models/insightface/models/antelopev2",
        "/comfyui/models",
        "/comfyui/models/insightface",
    ]
    for p in paths_to_check:
        if os.path.exists(p):
            if os.path.isdir(p):
                try:
                    result[p] = os.listdir(p)
                except Exception as e:
                    result[p] = f"error: {e}"
            elif os.path.islink(p):
                result[p] = f"symlink -> {os.readlink(p)}"
            else:
                result[p] = f"file, size={os.path.getsize(p)}"
        else:
            result[p] = "NOT FOUND"
    return result


# Lazy init on first request — startup init was hitting the serverless
# startup timeout because loading 2 SDXL checkpoints takes ~7 min.
worker = None


def handler(job):
    global worker
    job_input = job["input"]

    # Debug modes bypass normal generation
    if job_input.get("debug_env"):
        return handle_debug_env(job_input)
    if job_input.get("debug_fs"):
        return handle_debug_fs(job_input)

    if worker is None:
        logger.info("Lazy-initializing ComfyUICharacter (startup init failed)...")
        worker = ComfyUICharacter()
        logger.info("ComfyUICharacter ready (lazy init)")

    return worker.generate(job_input)


runpod.serverless.start({"handler": handler})
