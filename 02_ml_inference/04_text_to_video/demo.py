#!/usr/bin/env python3
"""
Generate a short GIF video from a text prompt.

Usage:
    python demo.py "a cinematic drone shot of snowy mountains" [output.gif]
"""

import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "http://localhost:8888/gpu/generate"


def main() -> None:
    prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "a cinematic drone shot of snowy mountains at sunrise"
    )
    output_path = Path(sys.argv[2] if len(sys.argv) > 2 else "text_to_video.gif").resolve()

    payload = {
        "prompt": prompt,
        "num_frames": 12,
        "num_steps": 18,
        "guidance_scale": 7.0,
        "fps": 8,
        "width": 512,
        "height": 288,
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
    print(f"Saved generated video GIF to {output_path}")


if __name__ == "__main__":
    main()
