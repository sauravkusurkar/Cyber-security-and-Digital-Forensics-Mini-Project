from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO


CHUNK_SIZE = 8192


def compute_file_hash(path: str | Path) -> str:
    """Compute a streaming SHA-256 digest without loading the whole file into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_uploaded_file(uploaded_file, destination: str | Path) -> Path:
    """Save a Streamlit UploadedFile or file-like object."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        handle.write(uploaded_file.getbuffer())
    return destination
