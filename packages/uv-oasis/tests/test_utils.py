from pathlib import Path

from uv_oasis.utils import calculate_sha256, url_to_filename


def test_url_to_filename():
    url = "https://github.com/astral-sh/python-build-standalone/releases/download/20240107/cpython-3.12.1%2B20240107-x86_64-unknown-linux-gnu-install_only.tar.gz"
    assert (
        url_to_filename(url)
        == "cpython-3.12.1+20240107-x86_64-unknown-linux-gnu-install_only.tar.gz"
    )


def test_calculate_sha256(tmp_path: Path):
    p = tmp_path / "test.txt"
    p.write_text("hello world", encoding="utf-8")
    # echo -n "hello world" | sha256sum -> b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9
    assert (
        calculate_sha256(p)
        == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    )
