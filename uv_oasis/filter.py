"""Filter download-metadata entries by platform, version, and variant."""

from __future__ import annotations

from typing import NamedTuple

from .models import FilterConfig, MetadataEntry, MetadataIndex, PlatformSpec

# Defaults if no config is provided
DEFAULT_PLATFORMS: list[PlatformSpec] = [
    PlatformSpec(os="linux", arch_family="x86_64", libc="gnu"),
    PlatformSpec(os="linux", arch_family="x86_64", libc="musl"),
    PlatformSpec(os="windows", arch_family="x86_64"),
]
DEFAULT_PYTHON_VARIANTS: set[str | None] = {None, "freethreaded"}
DEFAULT_CPU_VARIANTS: set[str | None] = {None}


class ReleaseGroup(NamedTuple):
    """Identifies a unique grouping of Python releases for filtering."""

    minor: int
    variant: str | None
    os: str
    arch_family: str
    arch_variant: str | None
    libc: str | None


def _is_stable(entry: MetadataEntry) -> bool:
    """Return True if the entry is a stable release (no prerelease tag)."""
    return entry.get("prerelease", "") == ""


def _extract_version_tuple(entry: MetadataEntry) -> tuple[int, int, int]:
    """Extract (major, minor, patch) from an entry."""
    return (entry["major"], entry["minor"], entry["patch"])


def _get_candidate_entries(
    metadata: MetadataIndex,
    platforms: list[PlatformSpec],
    python_variants: set[str | None],
    cpu_variants: set[str | None],
) -> list[tuple[str, MetadataEntry]]:
    """Filter out entries that don't match the requested platforms and variants."""
    candidate_entries: list[tuple[str, MetadataEntry]] = []
    for key, entry in metadata.items():
        if entry.get("name") != "cpython":
            continue
        if not _is_stable(entry):
            continue
        if entry.get("variant") not in python_variants:
            continue
        if not any(p.matches(entry, cpu_variants) for p in platforms):
            continue
        candidate_entries.append((key, entry))
    return candidate_entries


def _keep_latest_patch(
    candidate_entries: list[tuple[str, MetadataEntry]],
) -> dict[ReleaseGroup, tuple[str, MetadataEntry]]:
    """For each release group, keep only the one with the highest patch version."""
    latest_patch_entries_by_group: dict[ReleaseGroup, tuple[str, MetadataEntry]] = {}
    for key, entry in candidate_entries:
        group_key = ReleaseGroup(
            minor=entry["minor"],
            variant=entry.get("variant"),
            os=entry["os"],
            arch_family=entry["arch"]["family"],
            arch_variant=entry["arch"].get("variant"),
            libc=entry.get("libc"),
        )
        existing_entry = latest_patch_entries_by_group.get(group_key)
        if existing_entry is None or _extract_version_tuple(
            entry
        ) > _extract_version_tuple(existing_entry[1]):
            latest_patch_entries_by_group[group_key] = (key, entry)
    return latest_patch_entries_by_group


def _sort_key(item: tuple[ReleaseGroup, tuple[str, MetadataEntry]]) -> tuple:
    key, entry = item[1]
    v = _extract_version_tuple(entry)
    return (-v[0], -v[1], -v[2], key)


def filter_entries(
    metadata: MetadataIndex,
    *,
    config: FilterConfig | None = None,
) -> MetadataIndex:
    """Filter the full metadata down to the entries we want to ship.

    Uses the provided FilterConfig (or defaults) to:
    - Keep only cpython and stable releases
    - Filter by specified platforms, CPU variants, and Python variants
    - Keep only the highest patch version for each ReleaseGroup
    - Return the entries sorted by version descending
    """
    platforms = DEFAULT_PLATFORMS
    python_variants = DEFAULT_PYTHON_VARIANTS
    cpu_variants = DEFAULT_CPU_VARIANTS

    if config is not None:
        if config.platforms is not None:
            platforms = config.platforms
        python_variants = config.python_variants
        cpu_variants = config.cpu_variants
    # Step 1: Basic filtering
    candidate_entries = _get_candidate_entries(
        metadata, platforms, python_variants, cpu_variants
    )

    # Step 2: For each group, keep only the latest patch
    latest_patch_entries_by_group = _keep_latest_patch(candidate_entries)

    # Step 3: Sort results by version (descending) then key (ascending)
    sorted_group_items = sorted(latest_patch_entries_by_group.items(), key=_sort_key)
    return {k: v for _, (k, v) in sorted_group_items}
