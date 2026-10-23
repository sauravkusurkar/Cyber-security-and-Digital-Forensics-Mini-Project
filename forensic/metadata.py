from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import cv2


def _run_ffprobe(path: Path) -> dict[str, Any] | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None

    cmd = [
        ffprobe, "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        completed = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, check=False
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            return None
        return json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


def _opencv_metadata(path: Path) -> dict[str, Any]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"error": "OpenCV could not open the evidence file.", "_source": "opencv"}

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration = frames / fps if fps > 0 else 0.0
    cap.release()

    return {
        "filename": path.name,
        "container": path.suffix.lower().lstrip("."),
        "width": width,
        "height": height,
        "resolution": f"{width}x{height}" if width and height else "unknown",
        "frame_rate_fps": round(fps, 6),
        "frame_count": frames,
        "duration_seconds": round(duration, 6),
        "_source": "opencv",
    }


def extract_metadata(path: str | Path) -> dict[str, Any]:
    """
    Primary metadata path: FFprobe.
    Fallback: OpenCV, so the application remains runnable without a manual FFmpeg install.
    """
    path = Path(path)
    probed = _run_ffprobe(path)
    if probed:
        streams = probed.get("streams", [])
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        fmt = probed.get("format", {})

        fps = video_stream.get("r_frame_rate") or video_stream.get("avg_frame_rate")
        if isinstance(fps, str) and "/" in fps:
            try:
                n, d = fps.split("/", 1)
                fps_value = float(n) / float(d) if float(d) else 0.0
            except ValueError:
                fps_value = 0.0
        else:
            try:
                fps_value = float(fps or 0)
            except (TypeError, ValueError):
                fps_value = 0.0

        return {
            "filename": path.name,
            "container": fmt.get("format_name", path.suffix.lower().lstrip(".")),
            "format_long_name": fmt.get("format_long_name", ""),
            "duration_seconds": float(fmt.get("duration") or 0),
            "bit_rate": int(float(fmt.get("bit_rate") or 0)),
            "codec": video_stream.get("codec_name", ""),
            "codec_long_name": video_stream.get("codec_long_name", ""),
            "width": video_stream.get("width", 0),
            "height": video_stream.get("height", 0),
            "resolution": f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
            "frame_rate_fps": fps_value,
            "frame_count": video_stream.get("nb_frames", ""),
            "pixel_format": video_stream.get("pix_fmt", ""),
            "profile": video_stream.get("profile", ""),
            "_source": "ffprobe",
        }

    return _opencv_metadata(path)
