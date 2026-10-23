from pathlib import Path
import hashlib
import tempfile

from forensic.file_utils import compute_file_hash
from forensic.frames import frame_to_jpeg_bytes, hash_frame

import numpy as np


def test_sha256_matches_python_hashlib():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sample.bin"
        p.write_bytes(b"Digital Image Forensics")
        expected = hashlib.sha256(p.read_bytes()).hexdigest()
        assert compute_file_hash(p) == expected


def test_frame_jpeg_and_hash_are_stable():
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    first = hash_frame(frame, 85)
    second = hash_frame(frame, 85)
    assert first == second
    assert len(frame_to_jpeg_bytes(frame, 85)) > 0
