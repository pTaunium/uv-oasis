import json
from pathlib import Path

from uv_oasis.index_generator import generate_json_index, write_json_index
from uv_oasis.models import MetadataIndex


def test_generate_json_index():
    entries: MetadataIndex = {
        "cpython-3.12": {
            "name": "cpython",
            "arch": {"family": "x86_64", "variant": None},
            "os": "linux",
            "libc": "gnu",
            "major": 3,
            "minor": 12,
            "patch": 1,
            "prerelease": "",
            "url": "http://example.com/cpython-3.12.1%2Bbuild-linux.tar.gz",
            "sha256": "fake_sha",
            "variant": None,
        }
    }

    index = generate_json_index(entries, base_url_placeholder="{{MY_URL}}")

    assert len(index) == 1
    assert "cpython-3.12" in index

    entry = index["cpython-3.12"]
    # Check that URL is rewritten and unquoted
    assert entry["url"] == "{{MY_URL}}/assets/cpython-3.12.1+build-linux.tar.gz"
    assert entry["name"] == "cpython"
    assert entry["sha256"] == "fake_sha"


def test_write_json_index(tmp_path: Path):
    output_path = tmp_path / "metadata" / "download-metadata.json.template"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    entries: MetadataIndex = {
        "cpython-1": {
            "name": "cpython",
            "arch": {"family": "x86_64", "variant": None},
            "os": "linux",
            "libc": "gnu",
            "major": 3,
            "minor": 12,
            "patch": 1,
            "prerelease": "",
            "url": "http://example.com/cpython.tar.gz",
            "sha256": "sha",
            "variant": None,
        }
    }

    result_path = write_json_index(entries, output_path)

    assert result_path == output_path
    assert output_path.exists()

    with output_path.open("r") as f:
        data = json.load(f)

    assert "cpython-1" in data
    assert data["cpython-1"]["url"] == "{{BASE_URL}}/assets/cpython.tar.gz"
