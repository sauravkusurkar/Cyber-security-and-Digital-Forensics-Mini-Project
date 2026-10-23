from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib

import cv2


def frame_to_jpeg_bytes(frame, quality: int = 85) -> bytes:
    params = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    ok, encoded = cv2.imencode(".jpg", frame, params)
    if not ok:
        raise ValueError("OpenCV could not encode the sampled frame as JPEG.")
    return encoded.tobytes()


def hash_frame(frame, quality: int = 85) -> str:
    return hashlib.sha256(frame_to_jpeg_bytes(frame, quality)).hexdigest()


def sample_frames(
    video_path: str | Path,
    interval_seconds: float = 1.0,
    max_frames: int = 300,
) -> list[dict[str, Any]]:
    """
    Sample representative frames from a video.

    The report describes 1 frame/second as the default practical sampling rate.
    """
    interval_seconds = max(float(interval_seconds), 0.01)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps > 0 else 0.0

    results = []
    next_time = 0.0
    index = 0

    while len(results) < max_frames:
        if fps > 0:
            cap.set(cv2.CAP_PROP_POS_MSEC, next_time * 1000.0)

        ok, frame = cap.read()
        if not ok:
            break

        actual_index = int(cap.get(cv2.CAP_PROP_POS_FRAMES) or 0) - 1
        actual_time = (actual_index / fps) if fps > 0 else next_time

        results.append({
            "index": actual_index if actual_index >= 0 else index,
            "timestamp": float(actual_time),
            "frame": frame,
        })
        index += 1
        next_time += interval_seconds

        if duration > 0 and next_time > duration + interval_seconds:
            break

        # For codecs that ignore random seeking, prevent an accidental infinite loop.
        if fps <= 0 and index > max_frames:
            break

    cap.release()
    return results


def build_frame_hash_manifest(frames: list[dict[str, Any]], jpeg_quality: int = 85) -> list[dict[str, Any]]:
    manifest = []
    for item in frames:
        manifest.append({
            "frame_index": int(item["index"]),
            "timestamp_seconds": round(float(item["timestamp"]), 6),
            "sha256": hash_frame(item["frame"], jpeg_quality),
        })
    return manifest
