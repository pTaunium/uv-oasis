from uv_oasis.models import MetadataEntry, PlatformSpec


def test_platform_spec_matches():
    spec = PlatformSpec(os="linux", arch_family="x86_64", libc="gnu")

    # Match exact
    entry_match: MetadataEntry = {
        "os": "linux",
        "arch": {"family": "x86_64", "variant": None},
        "libc": "gnu",
    }
    assert spec.matches(entry_match, {None}) is True

    # OS Mismatch
    entry_mismatch_os: MetadataEntry = {
        "os": "windows",
        "arch": {"family": "x86_64", "variant": None},
        "libc": "gnu",
    }
    assert spec.matches(entry_mismatch_os, {None}) is False

    # Arch Mismatch
    entry_mismatch_arch: MetadataEntry = {
        "os": "linux",
        "arch": {"family": "aarch64", "variant": None},
        "libc": "gnu",
    }
    assert spec.matches(entry_mismatch_arch, {None}) is False

    # Variant mismatch / match
    entry_v2: MetadataEntry = {
        "os": "linux",
        "arch": {"family": "x86_64", "variant": "x86_64-v2"},
        "libc": "gnu",
    }
    assert spec.matches(entry_v2, {None}) is False
    assert spec.matches(entry_v2, {None, "x86_64-v2"}) is True

    # Libc match/mismatch
    entry_mismatch_libc: MetadataEntry = {
        "os": "linux",
        "arch": {"family": "x86_64", "variant": None},
        "libc": "musl",
    }
    assert spec.matches(entry_mismatch_libc, {None}) is False

    # Windows libc (none) vs spec libc (None)
    win_spec = PlatformSpec(os="windows", arch_family="x86_64")
    entry_win: MetadataEntry = {
        "os": "windows",
        "arch": {"family": "x86_64", "variant": None},
        "libc": "none",
    }
    assert win_spec.matches(entry_win, {None}) is True
