#!/usr/bin/env python3
"""
Animate an input image into a short GIF video.

Usage:
    python demo.py [input.png] [output.gif]
"""

import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "http://localhost:8888/gpu/animate"
DEFAULT_IMAGE = Path(__file__).resolve().parent / "poddy.jpg"
DEFAULT_OUTPUT = "image_to_video.gif"


def main() -> None:
    input_path = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else DEFAULT_IMAGE
    output_path = Path(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT).resolve()

    if not input_path.exists():
        print(f"Input image not found: {input_path}")
        sys.exit(1)

    image_base64 = base64.b64encode(input_path.read_bytes()).decode("utf-8")
    payload = {
        "image_base64": image_base64,
        "motion_bucket_id": 127,
        "noise_aug_strength": 0.02,
        "num_frames": 12,
        "num_steps": 18,
        "fps": 7,
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Request failed: HTTP {exc.code}")
        if body:
            print(f"Server detail: {body}")
        print("Make sure the server is running from this folder with: flash run")
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc}")
        print("Make sure the server is running from this folder with: flash run")
        sys.exit(1)

    if result.get("status") != "success":
        print(f"Worker error: {result}")
        sys.exit(1)

    output_bytes = base64.b64decode(result["video_base64"])
    output_path.write_bytes(output_bytes)
    print(f"Saved animated video GIF to {output_path}")


if __name__ == "__main__":
    main()
