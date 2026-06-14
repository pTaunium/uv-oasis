"""Download Python tarballs with SHA256 verification."""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from .models import MetadataIndex
from .utils import calculate_sha256, url_to_filename

logger = logging.getLogger(__name__)

# Chunk size for streaming downloads (1 MB).
_CHUNK_SIZE = 1024 * 1024


class ChecksumMismatchError(Exception):
    """Raised when a downloaded file's SHA256 doesn't match the expected value."""


def download_tarball(
    client: httpx.Client,
    url: str,
    dest: Path,
    *,
    expected_sha256: str | None = None,
) -> Path:
    """Download a single file from *url* to *dest*.

    If *expected_sha256* is provided, the file's SHA256 is verified after
    download. On mismatch, the file is removed and
    :class:`ChecksumMismatchError` is raised.

    Returns the path to the downloaded file.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Skip if already downloaded and checksum matches
    if dest.exists() and expected_sha256:
        actual = calculate_sha256(dest)
        if actual == expected_sha256:
            logger.info("Skipping %s (already downloaded, checksum OK)", dest.name)
            return dest

    logger.info("Downloading %s", url)
    with client.stream("GET", url) as response:
        response.raise_for_status()
        total_bytes = int(response.headers.get("content-length", 0))
        downloaded_bytes = 0
        with dest.open("wb") as f:
            for chunk in response.iter_bytes(chunk_size=_CHUNK_SIZE):
                f.write(chunk)
                downloaded_bytes += len(chunk)
                if total_bytes:
                    percent_complete = downloaded_bytes / total_bytes * 100
                    logger.debug("  %s: %.1f%%", dest.name, percent_complete)

    # Verify checksum
    if expected_sha256:
        actual = calculate_sha256(dest)
        if actual != expected_sha256:
            dest.unlink()
            raise ChecksumMismatchError(
                f"SHA256 mismatch for {dest.name}: "
                f"expected {expected_sha256}, got {actual}"
            )
        logger.info("  ✓ SHA256 verified: %s", dest.name)

    return dest


def download_tarballs(
    entries: MetadataIndex,
    output_dir: Path,
    *,
    timeout: float = 300.0,
) -> dict[str, Path]:
    """Download all tarballs for the given entries.

    Returns a mapping from entry key to the local file path.
    """
    results: dict[str, Path] = {}
    total_entries = len(entries)

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        for i, (key, entry) in enumerate(entries.items(), 1):
            url = entry["url"]
            filename = url_to_filename(url)
            dest = output_dir / filename

            logger.info("[%d/%d] %s", i, total_entries, key)
            download_tarball(
                client,
                url,
                dest,
                expected_sha256=entry.get("sha256"),
            )
            results[key] = dest

    return results
