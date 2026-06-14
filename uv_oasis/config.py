"""Configuration loader for uv-oasis."""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path

from .models import FilterConfig, PlatformSpec

logger = logging.getLogger(__name__)

DEFAULT_PLATFORMS: list[PlatformSpec] = [
    PlatformSpec(os="linux", arch_family="x86_64", libc="gnu"),
    PlatformSpec(os="linux", arch_family="x86_64", libc="musl"),
    PlatformSpec(os="windows", arch_family="x86_64"),
]
DEFAULT_PYTHON_VARIANTS: set[str | None] = {None, "freethreaded"}
DEFAULT_CPU_VARIANTS: set[str | None] = {None}


def get_default_config() -> FilterConfig:
    """Return the default filtering configuration."""
    return FilterConfig(
        python_variants=DEFAULT_PYTHON_VARIANTS,
        cpu_variants=DEFAULT_CPU_VARIANTS,
        platforms=DEFAULT_PLATFORMS,
    )


def load_filter_config(config_path: Path) -> FilterConfig:
    """Load and parse the TOML configuration file if it exists.

    Returns the default configuration if the file does not exist.
    """
    if not config_path.exists():
        return get_default_config()

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

    platforms: list[PlatformSpec] = DEFAULT_PLATFORMS
    if "platforms" in config:
        platforms = [
            PlatformSpec(
                os=p["os"],
                arch_family=p.get("arch") or p.get("arch_family"),
                libc=p.get("libc"),
            )
            for p in config["platforms"]
        ]

    return FilterConfig(
        python_variants=python_variants,
        cpu_variants=cpu_variants,
        platforms=platforms,
    )
