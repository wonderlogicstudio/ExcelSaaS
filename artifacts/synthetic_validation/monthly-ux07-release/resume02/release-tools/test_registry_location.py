from __future__ import annotations

import pytest

from registry_location import normalize_registry_upload_location

REG = "https://asia-northeast3-docker.pkg.dev"

def test_relative_location_is_normalized_to_registry_host():
    assert normalize_registry_upload_location(REG, "/v2/repo/blobs/uploads/session") == f"{REG}/v2/repo/blobs/uploads/session"

def test_absolute_same_origin_location_is_accepted():
    url = f"{REG}/v2/repo/blobs/uploads/session?upload_id=1"
    assert normalize_registry_upload_location(REG, url) == url

@pytest.mark.parametrize("location", [
    "https://evil.example/v2/repo/blobs/uploads/session",
    "http://asia-northeast3-docker.pkg.dev/v2/repo/blobs/uploads/session",
    "https://user:pass@asia-northeast3-docker.pkg.dev/v2/repo/blobs/uploads/session",
])
def test_foreign_http_or_credential_location_is_rejected(location: str):
    with pytest.raises(ValueError):
        normalize_registry_upload_location(REG, location)
