FROM runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

# System deps for OpenCV / image processing (SSH already in base image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libxcb1 libx11-6 libxext6 libsm6 \
    && rm -rf /var/lib/apt/lists/*

# Install ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui
WORKDIR /comfyui
RUN pip install -r requirements.txt

# Clone custom nodes + install their deps
RUN cd custom_nodes && \
    git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack && \
    git clone https://github.com/ltdrdata/comfyui-impact-subpack && \
    git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus && \
    git clone https://github.com/cubiq/ComfyUI_InstantID
RUN cd custom_nodes/ComfyUI-Impact-Pack && pip install -r requirements.txt && python install.py
RUN cd custom_nodes/comfyui-impact-subpack && [ -f requirements.txt ] && pip install -r requirements.txt || true
RUN cd custom_nodes/ComfyUI_IPAdapter_plus && [ -f requirements.txt ] && pip install -r requirements.txt || true
RUN cd custom_nodes/ComfyUI_InstantID && [ -f requirements.txt ] && pip install -r requirements.txt || true

# Pin insightface + onnxruntime-gpu LAST
# Must uninstall CPU onnxruntime first — it shadows the GPU version's CUDAExecutionProvider
RUN pip uninstall -y onnxruntime onnxruntime-gpu 2>/dev/null; \
    pip install insightface==0.7.3 onnxruntime-gpu runpod nest_asyncio

# Validate critical deps at build time
RUN python -c "\
import insightface; assert insightface.__version__ == '0.7.3', f'insightface={insightface.__version__}'; \
import onnxruntime; provs = onnxruntime.get_available_providers(); \
print(f'insightface OK, onnxruntime providers: {provs}')"

# Install huggingface_hub for model downloads at build time
RUN pip install huggingface_hub

# ---------------------------------------------------------------------------
# Bake all models into the image for fast cold start (NVMe instead of network volume)
# ---------------------------------------------------------------------------
ENV MODELS_DIR=/baked-models
ENV HF_HOME=/tmp/hf_cache

# Checkpoints
RUN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
os.makedirs('${MODELS_DIR}/models/checkpoints', exist_ok=True); \
p = hf_hub_download('cyberdelia/CyberRealisticXL', 'CyberRealisticXLPlay_V7.0_FP16.safetensors'); \
shutil.copy(p, '${MODELS_DIR}/models/checkpoints/cyberrealistic_xl_v7.safetensors')"

RUN --mount=type=secret,id=HF_TOKEN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
os.makedirs('${MODELS_DIR}/models/checkpoints', exist_ok=True); \
token = open('/run/secrets/HF_TOKEN').read().strip() if os.path.exists('/run/secrets/HF_TOKEN') else os.environ.get('HF_TOKEN',''); \
p = hf_hub_download('RunDiffusion/Juggernaut-XI-v11', 'Juggernaut-XI-byRunDiffusion.safetensors', token=token); \
shutil.copy(p, '${MODELS_DIR}/models/checkpoints/Juggernaut-XI-byRunDiffusion.safetensors')"

# CLIP Vision
RUN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
os.makedirs('${MODELS_DIR}/models/clip_vision', exist_ok=True); \
p = hf_hub_download('laion/CLIP-ViT-H-14-laion2B-s32B-b79K', 'open_clip_model.safetensors'); \
shutil.copy(p, '${MODELS_DIR}/models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors')"

# IPAdapter models
RUN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
os.makedirs('${MODELS_DIR}/models/ipadapter', exist_ok=True); \
p = hf_hub_download('h94/IP-Adapter-FaceID', 'ip-adapter-faceid-plusv2_sdxl.bin'); \
shutil.copy(p, '${MODELS_DIR}/models/ipadapter/ip-adapter-faceid-plusv2_sdxl.bin')"

RUN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
os.makedirs('${MODELS_DIR}/models/loras', exist_ok=True); \
p = hf_hub_download('h94/IP-Adapter-FaceID', 'ip-adapter-faceid-plusv2_sdxl_lora.safetensors'); \
shutil.copy(p, '${MODELS_DIR}/models/loras/ip-adapter-faceid-plusv2_sdxl_lora.safetensors')"

RUN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
os.makedirs('${MODELS_DIR}/models/ipadapter', exist_ok=True); \
p = hf_hub_download('h94/IP-Adapter', 'sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors'); \
shutil.copy(p, '${MODELS_DIR}/models/ipadapter/ip-adapter-plus-face_sdxl_vit-h.safetensors')"

# InstantID (ControlNet + ip-adapter)
RUN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
os.makedirs('${MODELS_DIR}/models/controlnet', exist_ok=True); \
p = hf_hub_download('InstantX/InstantID', 'ControlNetModel/diffusion_pytorch_model.safetensors'); \
shutil.copy(p, '${MODELS_DIR}/models/controlnet/diffusion_pytorch_model_instantid.safetensors')"

RUN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
os.makedirs('${MODELS_DIR}/models/instantid', exist_ok=True); \
p = hf_hub_download('InstantX/InstantID', 'ip-adapter.bin'); \
shutil.copy(p, '${MODELS_DIR}/models/instantid/ip-adapter.bin')"

# SAM
RUN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
os.makedirs('${MODELS_DIR}/models/sams', exist_ok=True); \
p = hf_hub_download('ybelkada/segment-anything', 'checkpoints/sam_vit_b_01ec64.pth'); \
shutil.copy(p, '${MODELS_DIR}/models/sams/sam_vit_b_01ec64.pth')"

# InsightFace antelopev2 (5 ONNX files)
RUN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
d = '${MODELS_DIR}/models/insightface/models/antelopev2'; os.makedirs(d, exist_ok=True); \
for f in ['1k3d68.onnx','2d106det.onnx','genderage.onnx','glintr100.onnx','scrfd_10g_bnkps.onnx']: \
    p = hf_hub_download('lithiumice/insightface', f'models/antelopev2/{f}'); shutil.copy(p, os.path.join(d, f))"

# InsightFace buffalo_l (5 ONNX files)
RUN python -c "\
from huggingface_hub import hf_hub_download; import shutil, os; \
d = '${MODELS_DIR}/models/insightface/models/buffalo_l'; os.makedirs(d, exist_ok=True); \
for f in ['1k3d68.onnx','2d106det.onnx','det_10g.onnx','genderage.onnx','w600k_r50.onnx']: \
    p = hf_hub_download('lithiumice/insightface', f'models/buffalo_l/{f}'); shutil.copy(p, os.path.join(d, f))"

# YOLOv8m face detector (direct URL download)
RUN python -c "\
import urllib.request, os; \
d = '${MODELS_DIR}/models/ultralytics/bbox'; os.makedirs(d, exist_ok=True); \
urllib.request.urlretrieve('https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8m.pt', os.path.join(d, 'face_yolov8m.pt'))"

# Write sentinel so _download_models() is skipped at runtime
RUN mkdir -p /baked-models/comfyui && echo "v5" > /baked-models/comfyui/.install_complete

# Clean HF cache to reduce image size
RUN rm -rf /tmp/hf_cache /root/.cache/huggingface

# Redirect HuggingFace cache to network volume for any runtime downloads
ENV HF_HOME=/runpod-volume/hf_cache

# Copy application code
COPY handler.py /handler.py
COPY comfyui_character.py /comfyui_character.py

CMD ["python", "-u", "/handler.py"]
