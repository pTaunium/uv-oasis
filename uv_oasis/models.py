"""Shared data models for uv-oasis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Type aliases for uv-oasis metadata
MetadataEntry = dict[str, Any]
MetadataIndex = dict[str, MetadataEntry]


@dataclass(frozen=True)
class PlatformSpec:
    """A target platform specification for filtering."""

    os: str
    arch_family: str
    libc: str | None = None  # None for Windows

    def matches(self, entry: dict, allowed_cpu_variants: set[str | None]) -> bool:
        if entry.get("os") != self.os:
            return False
        arch = entry.get("arch", {})
        if arch.get("family") != self.arch_family:
            return False
        if arch.get("variant") not in allowed_cpu_variants:
            return False
        return not (self.libc is not None and entry.get("libc") != self.libc)


@dataclass(frozen=True)
class FilterConfig:
    """Holds configuration for filtering metadata entries."""

    python_variants: set[str | None]
    cpu_variants: set[str | None]
    platforms: list[PlatformSpec] | None
