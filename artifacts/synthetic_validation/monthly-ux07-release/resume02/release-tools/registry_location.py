from __future__ import annotations

from urllib.parse import urljoin, urlparse

def normalize_registry_upload_location(registry: str, location: str) -> str:
    normalized = urljoin(registry.rstrip("/") + "/", location)
    parsed = urlparse(normalized)
    expected = urlparse(registry)
    if parsed.scheme != "https" or parsed.hostname != expected.hostname:
        raise ValueError("registry upload location must stay on the expected https host")
    if parsed.username or parsed.password:
        raise ValueError("registry upload location must not contain credentials")
    return normalized
