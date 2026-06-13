#!/usr/bin/env python3
"""Build script for uv-oasis.

Downloads selected Python standalone builds and generates a JSON index
for use with ``UV_PYTHON_DOWNLOADS_JSON_URL``.

Usage::

    uv run python build.py --output ./dist
"""

from __future__ import annotations

import argparse
import logging
import sys
import tomllib
from pathlib import Path

from uv_oasis.downloader import download_tarballs
from uv_oasis.filter import PlatformSpec, filter_entries
from uv_oasis.index_generator import write_json_index
from uv_oasis.metadata import fetch_metadata

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download Python standalone builds and generate index."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist"),
        help="Output directory (default: ./dist)",
    )
    parser.add_argument(
        "--metadata-url",
        default=None,
        help="Override the download-metadata.json URL",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.toml"),
        help="Path to the TOML configuration file (default: config.toml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without downloading",
    )
    args = parser.parse_args(argv)

    output_dir: Path = args.output
    assets_dir = output_dir / "assets"
    index_path = output_dir / "download-metadata.json.template"

    # Step 1: Fetch metadata
    logger.info("Fetching download-metadata.json...")
    kwargs = {}
    if args.metadata_url:
        kwargs["url"] = args.metadata_url
    metadata = fetch_metadata(**kwargs)
    logger.info("Fetched %d total entries from metadata", len(metadata))

    # Load optional config
    config_path: Path = args.config
    if config_path.exists():
        logger.info("Loading configuration from %s", config_path)
        with config_path.open("rb") as f:
            config = tomllib.load(f)

        python_variants: set[str | None] = set()
        for v in config.get("python_variants", ["default", "freethreaded"]):
            python_variants.add(None if v == "default" else v)

        cpu_variants: set[str | None] = set()
        # if cpu_variants is omitted, we default to [None] via the loop or explicitly
        for v in config.get("cpu_variants", []):
            cpu_variants.add(None if v == "default" or v == "" else v)
        if not cpu_variants:
            cpu_variants.add(None)

        platforms: list[PlatformSpec] | None = None
        if "platforms" in config:
            platforms = [
                PlatformSpec(
                    os=p["os"],
                    arch_family=p.get("arch") or p.get("arch_family"),
                    libc=p.get("libc"),
                )
                for p in config["platforms"]
            ]

        # Step 2: Filter with config
        if platforms is not None:
            entries = filter_entries(
                metadata,
                platforms=platforms,
                python_variants=python_variants,
                cpu_variants=cpu_variants,
            )
        else:
            entries = filter_entries(
                metadata,
                python_variants=python_variants,
                cpu_variants=cpu_variants,
            )
    else:
        # Step 2: Filter without config (defaults)
        entries = filter_entries(metadata)
    logger.info("Filtered to %d entries:", len(entries))
    for key in entries:
        entry = entries[key]
        size_info = ""
        variant = entry.get("variant") or "normal"
        logger.info("  %s (variant=%s)%s", key, variant, size_info)

    if args.dry_run:
        logger.info("Dry run — skipping downloads")
        return 0

    # Step 3: Download
    logger.info("Downloading tarballs to %s...", assets_dir)
    download_tarballs(entries, assets_dir)

    # Step 4: Generate index
    logger.info("Generating JSON index...")
    write_json_index(entries, index_path)

    logger.info("Done! Output directory: %s", output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
