from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .endpoint import get_image_from_volume, list_images_in_volume

cpu_router = APIRouter()


@cpu_router.get("/", response_class=HTMLResponse)
async def browse_images() -> HTMLResponse:
    result = await list_images_in_volume()
    images = result.get("images", [])

    items = "\n".join(f'<li><a href="/cpu/image/{image}">{image}</a></li>' for image in images)
    body = items or "<li>No images found yet.</li>"

    html = f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Network Volume Images</title>
    <style>
      body {{ font-family: system-ui, sans-serif; padding: 24px; }}
      h1 {{ font-size: 20px; margin-bottom: 12px; }}
      ul {{ padding-left: 18px; }}
      li {{ margin: 6px 0; }}
    </style>
  </head>
  <body>
    <h1>Generated Images</h1>
    <ul>
      {body}
    </ul>
  </body>
</html>"""

    return HTMLResponse(content=html)


@cpu_router.get("/image")
async def list_images():
    # Simple index of files produced by the GPU worker.
    result = await list_images_in_volume()
    return result


@cpu_router.get("/image/{file_id}")
async def get_image(file_id: str):
    # Serve a single image file from the shared volume.
    result = await get_image_from_volume(file_id)
    return result
