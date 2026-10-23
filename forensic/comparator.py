from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .file_utils import compute_file_hash
from .frames import sample_frames
from .metadata import extract_metadata


def _metadata_diff(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    keys = sorted(set(a) | set(b))
    diff = {}
    for key in keys:
        if key.startswith("_"):
            continue
        va, vb = a.get(key), b.get(key)
        if va != vb:
            diff[key] = {"A": va, "B": vb}
    return diff


def _frame_difference(a, b) -> float:
    h = min(a.shape[0], b.shape[0])
    w = min(a.shape[1], b.shape[1])
    a = cv2.resize(a, (w, h))
    b = cv2.resize(b, (w, h))
    diff = cv2.absdiff(a, b)
    return float(np.mean(diff))


def compare_media(
    path_a: str | Path,
    path_b: str | Path,
    interval_seconds: float = 1.0,
    max_frames: int = 300,
    jpeg_quality: int = 85,
) -> dict[str, Any]:
    del jpeg_quality  # reserved for future frame-hash comparison mode

    hash_a = compute_file_hash(path_a)
    hash_b = compute_file_hash(path_b)
    meta_a = extract_metadata(path_a)
    meta_b = extract_metadata(path_b)

    frames_a = sample_frames(path_a, interval_seconds, max_frames)
    frames_b = sample_frames(path_b, interval_seconds, max_frames)
    count = min(len(frames_a), len(frames_b))

    rows = []
    differences = []
    for i in range(count):
        d = _frame_difference(frames_a[i]["frame"], frames_b[i]["frame"])
        differences.append(d)
        rows.append({
            "Pair": i + 1,
            "Timestamp A (s)": round(frames_a[i]["timestamp"], 2),
            "Timestamp B (s)": round(frames_b[i]["timestamp"], 2),
            "Mean pixel difference": round(d, 4),
        })

    return {
        "file_hash_a": hash_a,
        "file_hash_b": hash_b,
        "metadata_diff": _metadata_diff(meta_a, meta_b),
        "frames_compared": count,
        "average_frame_difference": float(np.mean(differences)) if differences else 0.0,
        "frame_rows": rows,
    }
