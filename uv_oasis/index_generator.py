"""Generate the final JSON index for uv's UV_PYTHON_DOWNLOADS_JSON_URL."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Placeholder that entrypoint.sh will replace at container startup.
BASE_URL_PLACEHOLDER = "{{BASE_URL}}"


def _extract_local_filename(entry: dict) -> str:
    """Derive the local filename from the original download URL."""
    url: str = entry["url"]
    filename = url.rsplit("/", 1)[-1]
    # URL-decode %2B -> +
    return filename.replace("%2B", "+")


def generate_json_index(
    entries: dict[str, dict],
    *,
    base_url_placeholder: str = BASE_URL_PLACEHOLDER,
) -> dict[str, dict]:
    """Build the JSON index dict with rewritten URLs.

    Each entry's ``url`` is rewritten from the upstream GitHub URL to
    ``{base_url_placeholder}/pythons/{filename}``.

    The rest of the fields (name, arch, os, libc, major, minor, patch,
    prerelease, sha256, variant, build) are preserved as-is.
    """
    index: dict[str, dict] = {}
    for key, entry in entries.items():
        filename = _extract_local_filename(entry)
        new_entry = {
            "name": entry["name"],
            "arch": entry["arch"],
            "os": entry["os"],
            "libc": entry.get("libc"),
            "major": entry["major"],
            "minor": entry["minor"],
            "patch": entry["patch"],
            "prerelease": entry.get("prerelease", ""),
            "url": f"{base_url_placeholder}/assets/{filename}",
            "sha256": entry.get("sha256"),
            "variant": entry.get("variant"),
            "build": entry.get("build"),
        }
        index[key] = new_entry
    return index


def write_json_index(
    entries: dict[str, dict],
    output_path: Path,
    *,
    base_url_placeholder: str = BASE_URL_PLACEHOLDER,
) -> Path:
    """Generate and write the JSON index template to *output_path*.

    The file is named ``download-metadata.json.template`` and contains
    ``{{BASE_URL}}`` placeholders that are replaced at container startup.
    """
    index = generate_json_index(entries, base_url_placeholder=base_url_placeholder)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(index, f, indent=2)
        f.write("\n")

    logger.info("Wrote index with %d entries to %s", len(index), output_path)
    return output_path
