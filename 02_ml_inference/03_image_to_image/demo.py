#!/usr/bin/env python3
"""
Send an input image to the local Flash img2img endpoint and save the output.

Usage:
    python demo.py "turn this into a watercolor painting" [output.png]
    python demo.py input.png "turn this into a watercolor painting" [output.png]
"""

import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "http://localhost:8888/gpu/transform"
DEFAULT_IMAGE = Path(__file__).resolve().parent / "poddy.jpg"
DEFAULT_PROMPT = "turn this into a cinematic watercolor painting"
DEFAULT_OUTPUT = "transformed.png"


def main() -> None:
    args = sys.argv[1:]

    if not args:
        input_path = DEFAULT_IMAGE
        prompt = DEFAULT_PROMPT
        output_path = Path(DEFAULT_OUTPUT).resolve()
    else:
        first_arg_path = Path(args[0]).expanduser()
        if first_arg_path.exists():
            input_path = first_arg_path.resolve()
            prompt = args[1] if len(args) > 1 else DEFAULT_PROMPT
            output_path = Path(args[2] if len(args) > 2 else DEFAULT_OUTPUT).resolve()
        else:
            input_path = DEFAULT_IMAGE
            prompt = args[0]
            output_path = Path(args[1] if len(args) > 1 else DEFAULT_OUTPUT).resolve()

    if not input_path.exists():
        print(f"Input image not found: {input_path}")
        sys.exit(1)

    image_base64 = base64.b64encode(input_path.read_bytes()).decode("utf-8")
    payload = {
        "image_base64": image_base64,
        "prompt": prompt,
        "strength": 0.65,
        "guidance_scale": 7.5,
        "num_steps": 25,
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc}")
        print("Make sure the server is running from this folder with: flash run")
        sys.exit(1)

    if result.get("status") != "success":
        print(f"Worker error: {result}")
        sys.exit(1)

    output_bytes = base64.b64decode(result["image_base64"])
    output_path.write_bytes(output_bytes)
    print(f"Saved transformed image to {output_path}")


if __name__ == "__main__":
    main()
