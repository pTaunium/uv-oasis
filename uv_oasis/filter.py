"""Filter download-metadata entries by platform, version, and variant."""

from __future__ import annotations

from collections.abc import Sequence

from .models import PlatformSpec

# Defaults if no config is provided
DEFAULT_PLATFORMS: list[PlatformSpec] = [
    PlatformSpec(os="linux", arch_family="x86_64", libc="gnu"),
    PlatformSpec(os="linux", arch_family="x86_64", libc="musl"),
    PlatformSpec(os="windows", arch_family="x86_64"),
]
DEFAULT_PYTHON_VARIANTS: set[str | None] = {None, "freethreaded"}
DEFAULT_CPU_VARIANTS: set[str | None] = {None}


def _is_stable(entry: dict) -> bool:
    """Return True if the entry is a stable release (no prerelease tag)."""
    return entry.get("prerelease", "") == ""


def _extract_version_tuple(entry: dict) -> tuple[int, int, int]:
    """Extract (major, minor, patch) from an entry."""
    return (entry["major"], entry["minor"], entry["patch"])


def filter_entries(
    metadata: dict[str, dict],
    *,
    platforms: Sequence[PlatformSpec] = DEFAULT_PLATFORMS,
    python_variants: set[str | None] = DEFAULT_PYTHON_VARIANTS,
    cpu_variants: set[str | None] = DEFAULT_CPU_VARIANTS,
) -> dict[str, dict]:
    """Filter the full metadata down to the entries we want to ship.

    Rules:
    - Only cpython
    - Only stable releases (prerelease == "")
    - Only specified platforms and cpu_variants
    - Only allowed python_variants (normal + freethreaded)
    - For each (minor, variant, os, arch_family, arch_variant, libc) group,
      keep only the highest patch version
    """
    # Step 1: Basic filtering
    candidate_entries: list[tuple[str, dict]] = []
    for key, entry in metadata.items():
        # Only cpython
        if entry.get("name") != "cpython":
            continue
        # Only stable
        if not _is_stable(entry):
            continue
        # Only allowed variants
        if entry.get("variant") not in python_variants:
            continue
        # Only matching platforms
        if not any(p.matches(entry, cpu_variants) for p in platforms):
            continue
        candidate_entries.append((key, entry))

    # Step 2: For each group, keep only the latest patch
    # Group key: (minor, variant, os, arch_family, arch_variant, libc)
    latest_patch_entries_by_group: dict[tuple, tuple[str, dict]] = {}
    for key, entry in candidate_entries:
        group_key = (
            entry["minor"],
            entry.get("variant"),
            entry["os"],
            entry["arch"]["family"],
            entry["arch"].get("variant"),
            entry.get("libc"),
        )
        existing_entry = latest_patch_entries_by_group.get(group_key)
        if existing_entry is None or _extract_version_tuple(
            entry
        ) > _extract_version_tuple(existing_entry[1]):
            latest_patch_entries_by_group[group_key] = (key, entry)

    # Step 3: Sort results by version (descending) then key (ascending)
    def _sort_key(item: tuple[tuple, tuple[str, dict]]) -> tuple:
        key, entry = item[1]
        v = _extract_version_tuple(entry)
        return (-v[0], -v[1], -v[2], key)

    sorted_group_items = sorted(latest_patch_entries_by_group.items(), key=_sort_key)
    return {k: v for _, (k, v) in sorted_group_items}
