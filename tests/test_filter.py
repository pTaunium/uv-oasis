from typing import cast

from uv_oasis.filter import (
    ReleaseGroup,
    _extract_version_tuple,
    _get_candidate_entries,
    _is_stable,
    _keep_latest_patch,
    filter_entries,
)
from uv_oasis.models import FilterConfig, MetadataEntry, MetadataIndex, PlatformSpec


def test_is_stable():
    assert _is_stable(cast(MetadataEntry, {"prerelease": ""})) is True
    assert _is_stable(cast(MetadataEntry, {"prerelease": "b1"})) is False
    assert (
        _is_stable(cast(MetadataEntry, {})) is True
    )  # missing prerelease defaults to ""


def test_extract_version_tuple():
    assert _extract_version_tuple(
        cast(MetadataEntry, {"major": 3, "minor": 12, "patch": 1})
    ) == (
        3,
        12,
        1,
    )


def test_get_candidate_entries():
    metadata = cast(
        MetadataIndex,
        {
            "cpython-3.12.1-linux-gnu": {
                "name": "cpython",
                "major": 3,
                "minor": 12,
                "patch": 1,
                "prerelease": "",
                "variant": None,
                "os": "linux",
                "arch": {"family": "x86_64", "variant": None},
                "libc": "gnu",
            },
            "pypy-3.12": {
                "name": "pypy",  # Should be ignored (not cpython)
            },
            "cpython-3.13.0b1": {
                "name": "cpython",
                "prerelease": "b1",  # Should be ignored (not stable)
            },
            "cpython-3.12.1-freethreaded": {
                "name": "cpython",
                "prerelease": "",
                "variant": "freethreaded",  # Should be ignored (not in python_variants config below)
            },
            "cpython-3.12.1-mac": {
                "name": "cpython",
                "prerelease": "",
                "variant": None,
                "os": "darwin",  # Should be ignored (not in platforms)
                "arch": {"family": "aarch64", "variant": None},
                "libc": "none",
            },
        },
    )

    platforms = [PlatformSpec("linux", "x86_64", "gnu")]
    candidates = _get_candidate_entries(
        metadata, platforms, python_variants={None}, cpu_variants={None}
    )

    assert len(candidates) == 1
    assert candidates[0][0] == "cpython-3.12.1-linux-gnu"


def test_keep_latest_patch():
    candidates = cast(
        list[tuple[str, MetadataEntry]],
        [
            (
                "cpython-3.12.0-linux-gnu",
                {
                    "minor": 12,
                    "patch": 0,
                    "variant": None,
                    "os": "linux",
                    "arch": {"family": "x86_64", "variant": None},
                    "libc": "gnu",
                    "major": 3,
                },
            ),
            (
                "cpython-3.12.1-linux-gnu",
                {
                    "minor": 12,
                    "patch": 1,
                    "variant": None,
                    "os": "linux",
                    "arch": {"family": "x86_64", "variant": None},
                    "libc": "gnu",
                    "major": 3,
                },
            ),
            (
                "cpython-3.11.5-linux-gnu",
                {
                    "minor": 11,
                    "patch": 5,
                    "variant": None,
                    "os": "linux",
                    "arch": {"family": "x86_64", "variant": None},
                    "libc": "gnu",
                    "major": 3,
                },
            ),
        ],
    )

    result = _keep_latest_patch(candidates)

    assert len(result) == 2

    group_12 = ReleaseGroup(12, None, "linux", "x86_64", None, "gnu")
    assert group_12 in result
    assert result[group_12][0] == "cpython-3.12.1-linux-gnu"

    group_11 = ReleaseGroup(11, None, "linux", "x86_64", None, "gnu")
    assert group_11 in result
    assert result[group_11][0] == "cpython-3.11.5-linux-gnu"


def test_filter_entries_sorting():
    metadata = cast(
        MetadataIndex,
        {
            "cpython-3.10.0": {
                "name": "cpython",
                "major": 3,
                "minor": 10,
                "patch": 0,
                "prerelease": "",
                "variant": None,
                "os": "linux",
                "arch": {"family": "x86_64", "variant": None},
                "libc": "gnu",
            },
            "cpython-3.12.0": {
                "name": "cpython",
                "major": 3,
                "minor": 12,
                "patch": 0,
                "prerelease": "",
                "variant": None,
                "os": "linux",
                "arch": {"family": "x86_64", "variant": None},
                "libc": "gnu",
            },
        },
    )

    config = FilterConfig(
        python_variants={None},
        cpu_variants={None},
        platforms=[PlatformSpec("linux", "x86_64", "gnu")],
    )

    result = filter_entries(metadata, config=config)
    keys = list(result.keys())
    assert keys == ["cpython-3.12.0", "cpython-3.10.0"]  # Descending
