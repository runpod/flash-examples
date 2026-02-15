#!/usr/bin/env python3
"""
Flash Demo — Generate an image with Flux and display it in your terminal.

Usage:
    1. Start the server:   cd 02_ml_inference/02_text_to_image && flash run
    2. Run this script:    python demo.py
    3. Or with a prompt:   python demo.py "a cat astronaut on mars"
"""

import base64
import io
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

API_URL = "http://localhost:8888/gpu/generate"
DEFAULT_PROMPT = "a tiny astronaut floating above earth, watercolor style"
OUTPUT_FILE = "generated.png"

# ── Terminal image rendering ─────────────────────────────────────────


def render_in_terminal(image_bytes: bytes, max_width: int | None = None):
    """Render an image in the terminal using ANSI true-color half-blocks.

    Works in any terminal that supports 24-bit color (iTerm2, Kitty,
    WezTerm, Windows Terminal, most modern terminals).
    """
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Fit to terminal width
    term_width = max_width or min(shutil.get_terminal_size().columns, 80)
    aspect = img.height / img.width
    w = term_width
    h = int(w * aspect)
    if h % 2 != 0:
        h += 1

    img = img.resize((w, h), Image.LANCZOS)
    px = img.load()

    lines = []
    for y in range(0, h, 2):
        row = []
        for x in range(w):
            r1, g1, b1 = px[x, y]
            r2, g2, b2 = px[x, y + 1] if y + 1 < h else (0, 0, 0)
            row.append(f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀")
        lines.append("".join(row) + "\033[0m")

    print("\n".join(lines))


def try_imgcat(image_bytes: bytes) -> bool:
    """Try to display via imgcat (iTerm2) or chafa."""
    for cmd in ("imgcat", "chafa", "viu"):
        if shutil.which(cmd):
            try:
                proc = subprocess.run(
                    [cmd, "-"],
                    input=image_bytes,
                    timeout=5,
                )
                return proc.returncode == 0
            except Exception:
                continue
    return False


def display_image(image_bytes: bytes):
    """Display an image in the terminal with the best available method."""
    # Try native image tools first (high-res)
    if try_imgcat(image_bytes):
        return

    # Fall back to ANSI half-block rendering (works everywhere)
    render_in_terminal(image_bytes)


# ── Main ─────────────────────────────────────────────────────────────


def main():
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_PROMPT

    print()
    print("  ⚡ Flash Demo — Flux Text-to-Image")
    print("  ─────────────────────────────────────")
    print(f'  Prompt:  "{prompt}"')
    print(f"  Server:  {API_URL}")
    print()

    # Build request
    hf_token = os.environ.get("HF_TOKEN", "")
    payload = json.dumps({"prompt": prompt, "hf_token": hf_token}).encode()
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    # Send request with timing
    print("  Sending to RunPod GPU worker...", end="", flush=True)
    t0 = time.time()

    try:
        resp = urllib.request.urlopen(req, timeout=300)
    except urllib.error.URLError as e:
        print(f"\n\n  Error: Could not connect to {API_URL}")
        print("  Make sure the Flash server is running:  flash run")
        print(f"  ({e})")
        sys.exit(1)

    result = json.loads(resp.read())
    elapsed = time.time() - t0

    if result.get("status") != "success":
        print(f"\n\n  Error from worker: {result}")
        sys.exit(1)

    # Decode image
    image_bytes = base64.b64decode(result["image_base64"])
    size_kb = len(image_bytes) / 1024

    print(f" done! ({elapsed:.1f}s)")
    print(f"  Image:   {result.get('width')}x{result.get('height')}px, {size_kb:.0f}KB")
    print()

    # Save to disk
    with open(OUTPUT_FILE, "wb") as f:
        f.write(image_bytes)
    print(f"  Saved to {OUTPUT_FILE}")
    print()

    # Display in terminal
    display_image(image_bytes)
    print()


if __name__ == "__main__":
    main()
