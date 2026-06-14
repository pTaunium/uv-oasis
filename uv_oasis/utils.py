"""Common utility functions for uv-oasis."""

import hashlib
from pathlib import Path


def url_to_filename(url: str) -> str:
    """Derive the local filename from the original download URL.

    Handles URL decoding (e.g., %2B to +) and path splitting.
    """
    filename = url.rsplit("/", 1)[-1]
    return filename.replace("%2B", "+")


def calculate_sha256(path: Path) -> str:
    """Calculate the SHA256 checksum of a file using Python 3.11+ file_digest."""
    with path.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256")
    return digest.hexdigest()
