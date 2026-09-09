from __future__ import annotations

import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import yaml
from fastapi.testclient import TestClient

from app.config import Settings
from app.control_plane import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    ControlPlaneHmacMiddleware,
    build_control_plane_signature,
)
from app.main import app

TEMPLATE = (
    Path(__file__).resolve().parents[3]
    / "infra/gateway/workbookcare-beta-openapi.yaml.template"
)
SECRET = "synthetic-gateway-route-test-secret-at-least-32-characters"
SCAN_PATH = "/v1/scans"
BACKEND_ORIGIN = "https://synthetic-backend.example.test"


def gateway_spec() -> dict:
    return yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))


def test_gateway_keeps_exact_access_and_backend_identity_contract() -> None:
    spec = gateway_spec()
    assert set(spec["paths"]) == {SCAN_PATH}
    operation = spec["paths"][SCAN_PATH]["post"]
    assert operation["security"] == [{"cloudflare_access": []}]
    backend = operation["x-google-backend"]
    assert backend["address"] == backend["jwt_audience"] == "${CLOUD_RUN_URL}"
    assert not backend.get("disable_auth", False)
    access = spec["securityDefinitions"]["cloudflare_access"]
    assert access["x-google-issuer"] == "${CLOUDFLARE_ACCESS_ISSUER}"
    assert access["x-google-jwks_uri"] == "${CLOUDFLARE_ACCESS_JWKS_URI}"
    assert access["x-google-audiences"] == "${CLOUDFLARE_ACCESS_AUD}"


def test_gateway_translated_route_reaches_signed_scan_and_rejects_unsigned_bypass(
    risky_workbook_bytes: bytes,
) -> None:
    backend = gateway_spec()["paths"][SCAN_PATH]["post"]["x-google-backend"]
    address = backend["address"].replace("${CLOUD_RUN_URL}", BACKEND_ORIGIN)
    # Match Google's operation-level default, which otherwise drops /v1/scans.
    translation = backend.get("path_translation", "CONSTANT_ADDRESS")
    assert translation in {"APPEND_PATH_TO_ADDRESS", "CONSTANT_ADDRESS"}
    target = address + SCAN_PATH if translation == "APPEND_PATH_TO_ADDRESS" else address
    backend_path = urlsplit(target).path or "/"

    settings = Settings(
        app_env="hosted_beta",
        cors_origins="https://synthetic-worker.example.test",
        control_plane_hmac_secret=SECRET,
    )
    # Exercise the real scan route behind the hosted HMAC guard, without
    # changing the global application's development settings or using secrets.
    client = TestClient(ControlPlaneHmacMiddleware(app, settings=settings))
    request = httpx.Request(
        "POST", target, files={"file": ("workbook.xlsx", risky_workbook_bytes)}
    )
    body = request.read()
    timestamp = int(time.time())
    headers = {
        "Content-Type": request.headers["content-type"],
        TIMESTAMP_HEADER: str(timestamp),
        SIGNATURE_HEADER: build_control_plane_signature(
            SECRET, timestamp, "POST", SCAN_PATH, body
        ),
    }

    response = client.post(backend_path, content=body, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["summary"]["issue_count"] >= 1
    assert response.json()["filename"] == "workbook.xlsx"
    unsigned = client.post(backend_path, content=body)
    assert unsigned.status_code == 401
    assert unsigned.json()["error"]["code"] == "CONTROL_PLANE_SIGNATURE_REQUIRED"
