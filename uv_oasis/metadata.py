"""Fetch and parse uv's download-metadata.json."""

from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import MetadataIndex

# The canonical source for uv's Python download metadata.
DOWNLOAD_METADATA_URL = (
    "https://raw.githubusercontent.com/astral-sh/uv/main/"
    "crates/uv-python/download-metadata.json"
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def fetch_metadata(
    *, url: str = DOWNLOAD_METADATA_URL, timeout: float = 30.0
) -> MetadataIndex:
    """Download and return the full download-metadata.json as a dict.

    Keys are distribution identifiers like
    ``"cpython-3.13.3-linux-x86_64-gnu"`` and values are dicts with
    fields: name, arch, os, libc, major, minor, patch, prerelease,
    url, sha256, variant.
    """
    response = httpx.get(url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    return response.json()
