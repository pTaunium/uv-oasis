"""Common utility functions for uv-oasis."""

import hashlib
from pathlib import Path

# Chunk size for streaming file hashing (1 MB).
_CHUNK_SIZE = 1024 * 1024


def url_to_filename(url: str) -> str:
    """Derive the local filename from the original download URL.

    Handles URL decoding (e.g., %2B to +) and path splitting.
    """
    filename = url.rsplit("/", 1)[-1]
    return filename.replace("%2B", "+")


def calculate_sha256(path: Path) -> str:
    """Compute the SHA256 hex digest of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()
