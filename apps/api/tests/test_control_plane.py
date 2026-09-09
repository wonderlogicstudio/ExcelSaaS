from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.config import Settings
from app.control_plane import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    ControlPlaneHmacMiddleware,
    build_control_plane_signature,
    verify_control_plane_signature,
)

SECRET = "synthetic-control-plane-secret-at-least-32-characters"
TIMESTAMP = 1_700_000_000
PATH = "/v1/scans"


def test_signature_binds_version_timestamp_method_path_and_exact_body() -> None:
    body = b"synthetic multipart bytes only"
    signature = build_control_plane_signature(SECRET, TIMESTAMP, "POST", PATH, body)

    assert signature.startswith("v1=")
    assert (
        verify_control_plane_signature(
            secret=SECRET,
            max_age_seconds=60,
            method="POST",
            path=PATH,
            body=body,
            timestamp_value=str(TIMESTAMP),
            signature_value=signature,
            now=TIMESTAMP,
        )
        is None
    )
    assert (
        verify_control_plane_signature(
            secret=SECRET,
            max_age_seconds=60,
            method="POST",
            path=PATH,
            body=body + b" substituted",
            timestamp_value=str(TIMESTAMP),
            signature_value=signature,
            now=TIMESTAMP,
        )
        == "CONTROL_PLANE_SIGNATURE_INVALID"
    )
    assert (
        verify_control_plane_signature(
            secret=SECRET,
            max_age_seconds=60,
            method="POST",
            path=PATH,
            body=body,
            timestamp_value=str(TIMESTAMP),
            signature_value=signature,
            now=TIMESTAMP + 61,
        )
        == "CONTROL_PLANE_SIGNATURE_EXPIRED"
    )


def test_hosted_middleware_rejects_unsigned_gateway_bypass_and_replays_signed_body() -> None:
    app = FastAPI()
    settings = Settings(
        app_env="hosted_beta",
        cors_origins="https://beta.example.test",
        control_plane_hmac_secret=SECRET,
    )
    app.add_middleware(ControlPlaneHmacMiddleware, settings=settings)

    @app.get("/health/live")
    async def health() -> dict[str, str]:
        return {"status": "live"}

    @app.post(PATH)
    async def scan(request: Request) -> dict[str, int]:
        return {"received_bytes": len(await request.body())}

    client = TestClient(app)
    body = b"--synthetic\r\ncontent\r\n--synthetic--\r\n"

    unsigned = client.post(PATH, content=body)
    assert unsigned.status_code == 401
    assert unsigned.json()["error"]["code"] == "CONTROL_PLANE_SIGNATURE_REQUIRED"

    timestamp = int(__import__("time").time())
    signature = build_control_plane_signature(SECRET, timestamp, "POST", PATH, body)
    signed = client.post(
        PATH,
        content=body,
        headers={TIMESTAMP_HEADER: str(timestamp), SIGNATURE_HEADER: signature},
    )
    assert signed.status_code == 200
    assert signed.json() == {"received_bytes": len(body)}

    wrong_body = client.post(
        PATH,
        content=body + b"tampered",
        headers={TIMESTAMP_HEADER: str(timestamp), SIGNATURE_HEADER: signature},
    )
    assert wrong_body.status_code == 403
    assert wrong_body.json()["error"]["code"] == "CONTROL_PLANE_SIGNATURE_INVALID"

    assert client.get("/health/live").json() == {"status": "live"}
