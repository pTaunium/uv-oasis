from pathlib import Path

from uv_oasis.config import load_filter_config
from uv_oasis.models import PlatformSpec


def test_load_filter_config_missing_file():
    # File doesn't exist
    assert load_filter_config(Path("nonexistent.toml")) is None


def test_load_filter_config_empty(tmp_path: Path):
    p = tmp_path / "config.toml"
    p.write_text("")
    config = load_filter_config(p)
    assert config is not None
    assert config.python_variants == {None, "freethreaded"}
    assert config.cpu_variants == {None}
    assert config.platforms is None


def test_load_filter_config_full(tmp_path: Path):
    p = tmp_path / "config.toml"
    p.write_text(
        """
        python_variants = ["default", "freethreaded"]
        cpu_variants = ["default", "x86_64-v3"]

        [[platforms]]
        os = "linux"
        arch = "x86_64"
        libc = "gnu"

        [[platforms]]
        os = "windows"
        arch = "aarch64"
        """
    )

    config = load_filter_config(p)

    assert config is not None
    assert config.python_variants == {None, "freethreaded"}
    assert config.cpu_variants == {None, "x86_64-v3"}
    assert config.platforms is not None
    assert len(config.platforms) == 2

    assert config.platforms[0] == PlatformSpec(
        os="linux", arch_family="x86_64", libc="gnu"
    )
    assert config.platforms[1] == PlatformSpec(
        os="windows", arch_family="aarch64", libc=None
    )


def test_load_filter_config_no_platforms(tmp_path: Path):
    p = tmp_path / "config.toml"
    p.write_text(
        """
        python_variants = ["default"]
        """
    )

    config = load_filter_config(p)
    assert config is not None
    assert config.python_variants == {None}
    assert config.cpu_variants == {None}
    assert config.platforms is None
