"""Fetch and parse uv's download-metadata.json."""

from __future__ import annotations

import httpx

# The canonical source for uv's Python download metadata.
DOWNLOAD_METADATA_URL = (
    "https://raw.githubusercontent.com/astral-sh/uv/main/"
    "crates/uv-python/download-metadata.json"
)


def fetch_metadata(
    *, url: str = DOWNLOAD_METADATA_URL, timeout: float = 30.0
) -> dict[str, dict]:
    """Download and return the full download-metadata.json as a dict.

    Keys are distribution identifiers like
    ``"cpython-3.13.3-linux-x86_64-gnu"`` and values are dicts with
    fields: name, arch, os, libc, major, minor, patch, prerelease,
    url, sha256, variant, build.
    """
    response = httpx.get(url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    return response.json()
