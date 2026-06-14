import httpx
import respx

from uv_oasis.metadata import DOWNLOAD_METADATA_URL, fetch_metadata


@respx.mock
def test_fetch_metadata():
    route = respx.get(DOWNLOAD_METADATA_URL).mock(
        return_value=httpx.Response(200, json={"cpython-3.12": {}})
    )

    result = fetch_metadata()

    assert result == {"cpython-3.12": {}}
    assert route.called


@respx.mock
def test_fetch_metadata_custom_url():
    custom_url = "http://example.com/metadata.json"
    route = respx.get(custom_url).mock(return_value=httpx.Response(200, json={}))

    result = fetch_metadata(url=custom_url, timeout=10.0)

    assert result == {}
    assert route.called
