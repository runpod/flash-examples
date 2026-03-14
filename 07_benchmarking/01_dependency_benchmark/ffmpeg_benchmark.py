# ffmpeg version benchmark -- measures encoding performance.
# run with: flash run
# test directly: python ffmpeg_benchmark.py
from runpod_flash import Endpoint


@Endpoint(
    name="07_ffmpeg_baseline",
    cpu="cpu3c-1-2",
    system_dependencies=["ffmpeg"],
)
async def ffmpeg_benchmark(payload: dict) -> dict:
    """Benchmark ffmpeg operations and report version + timing + output sizes."""
    import os
    import re
    import shutil
    import subprocess
    import tempfile
    import time

    total_start = time.perf_counter()

    # parse installed version
    try:
        version_output = subprocess.check_output(
            ["ffmpeg", "-version"], stderr=subprocess.STDOUT
        ).decode()
        version_match = re.search(r"ffmpeg version (\S+)", version_output)
        installed_version = version_match.group(1) if version_match else "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        installed_version = f"error: {e}"

    benchmarks = {}
    tmp_dir = tempfile.mkdtemp(prefix="ffmpeg_bench_")

    try:
        # audio encode: 5-second 440Hz sine wave -> AAC
        audio_out = os.path.join(tmp_dir, "audio.aac")
        start = time.perf_counter()
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=5",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                audio_out,
            ],
            capture_output=True,
            check=True,
        )
        elapsed = (time.perf_counter() - start) * 1000
        audio_size = os.path.getsize(audio_out)
        benchmarks["audio_encode"] = {
            "time_ms": round(elapsed, 2),
            "output_size_bytes": audio_size,
        }

        # video encode: 5s of testsrc2 at 720p 30fps -> H264 MKV
        video_mkv = os.path.join(tmp_dir, "video.mkv")
        start = time.perf_counter()
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=1280x720:rate=30:duration=5",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                video_mkv,
            ],
            capture_output=True,
            check=True,
        )
        elapsed = (time.perf_counter() - start) * 1000
        video_size = os.path.getsize(video_mkv)
        benchmarks["video_encode"] = {
            "time_ms": round(elapsed, 2),
            "output_size_bytes": video_size,
        }

        # format conversion: remux MKV -> MP4
        video_mp4 = os.path.join(tmp_dir, "video.mp4")
        start = time.perf_counter()
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                video_mkv,
                "-c",
                "copy",
                video_mp4,
            ],
            capture_output=True,
            check=True,
        )
        elapsed = (time.perf_counter() - start) * 1000
        mp4_size = os.path.getsize(video_mp4)
        benchmarks["format_convert"] = {
            "time_ms": round(elapsed, 2),
            "output_size_bytes": mp4_size,
        }

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    total_ms = round((time.perf_counter() - total_start) * 1000, 2)

    return {
        "version": {"installed": installed_version},
        "benchmarks": benchmarks,
        "total_time_ms": total_ms,
    }


if __name__ == "__main__":
    import asyncio
    import json

    async def test():
        print("\n=== FFmpeg Benchmark ===")
        result = await ffmpeg_benchmark({})
        print(json.dumps(result, indent=2))

    asyncio.run(test())
