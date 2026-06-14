from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest
import respx

from uv_oasis.downloader import (
    ChecksumMismatchError,
    download_tarball,
    download_tarballs,
)
from uv_oasis.models import MetadataIndex


@patch("uv_oasis.downloader.calculate_sha256")
def test_download_tarball_skip_existing(mock_calc: MagicMock, tmp_path: Path):
    dest = tmp_path / "test.tar.gz"
    dest.write_text("dummy")
    mock_calc.return_value = "fake_sha"

    client = Mock()
    result = download_tarball(client, "http://url", dest, expected_sha256="fake_sha")

    assert result == dest
    client.stream.assert_not_called()


@respx.mock
@patch("uv_oasis.downloader.calculate_sha256")
def test_download_tarball_success(mock_calc: MagicMock, tmp_path: Path):
    dest = tmp_path / "test.tar.gz"
    mock_calc.return_value = "fake_sha"

    route = respx.get("http://url").mock(
        return_value=httpx.Response(
            200, content=b"helloworld", headers={"content-length": "10"}
        )
    )

    with httpx.Client() as client:
        result = download_tarball(
            client, "http://url", dest, expected_sha256="fake_sha"
        )

    assert result == dest
    assert dest.read_text() == "helloworld"
    assert route.called
    mock_calc.assert_called_once_with(dest)


@respx.mock
@patch("uv_oasis.downloader.calculate_sha256")
def test_download_tarball_checksum_mismatch(mock_calc: MagicMock, tmp_path: Path):
    dest = tmp_path / "test.tar.gz"
    mock_calc.return_value = "wrong_sha"

    respx.get("http://url").mock(return_value=httpx.Response(200, content=b"hello"))

    with httpx.Client() as client, pytest.raises(ChecksumMismatchError):
        download_tarball(client, "http://url", dest, expected_sha256="fake_sha")

    assert not dest.exists()  # Ensure file is deleted on mismatch


@patch("uv_oasis.downloader.download_tarball")
def test_download_tarballs(mock_download: MagicMock, tmp_path: Path):

    entries = cast(
        MetadataIndex,
        {
            "cpython-1": {
                "url": "http://example.com/cpython-1.tar.gz",
                "sha256": "sha1",
            },
            "cpython-2": {
                "url": "http://example.com/cpython-2%2Bbuild.tar.gz",
                "sha256": "sha2",
            },
        },
    )

    results = download_tarballs(entries, tmp_path)

    assert len(results) == 2
    assert "cpython-1" in results
    assert "cpython-2" in results

    assert results["cpython-1"].name == "cpython-1.tar.gz"
    assert results["cpython-2"].name == "cpython-2+build.tar.gz"

    assert mock_download.call_count == 2
