"""Fail-closed proof for the private hosted-beta control plane.

Cloud Run IAM proves that API Gateway may invoke the service.  This module
proves that the request body passed through the Cloudflare Worker rather than
being submitted directly to the gateway by an otherwise authenticated user.
It deliberately handles only opaque bytes and never logs request content.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from collections.abc import Awaitable, Callable
from typing import Final

from .config import Settings
from .observability import log_safe_event

ASGIApp = Callable[
    [dict, Callable[[], Awaitable[dict]], Callable[[dict], Awaitable[None]]], Awaitable[None]
]
Receive = Callable[[], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]

PROTECTED_PATHS: Final = frozenset({"/v1/scans", "/v1/formula-audits", "/v1/delivery"})
SIGNATURE_HEADER: Final = "x-workbookcare-signature"
TIMESTAMP_HEADER: Final = "x-workbookcare-timestamp"
SIGNATURE_PREFIX: Final = "v1="
SIGNATURE_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")
# The API itself enforces the 10 MiB workbook limit.  The small allowance is
# solely multipart framing and prevents an unsigned direct-gateway request
# from forcing unlimited buffering before FastAPI can reject it.
MULTIPART_OVERHEAD_ALLOWANCE_BYTES: Final = 256 * 1024


def build_control_plane_signature(
    secret: str,
    timestamp: int,
    method: str,
    path: str,
    body: bytes,
    owner: str | None = None,
) -> str:
    """Return the versioned HMAC shared with the Cloudflare Worker.

    The content hash binds the exact multipart representation; callers cannot
    substitute a different workbook or endpoint after signing.
    """

    body_sha256 = hashlib.sha256(body).hexdigest()
    version = "v2" if owner is not None else "v1"
    owner_line = f"{owner}\n" if owner is not None else ""
    canonical = (
        f"{version}\n{timestamp}\n{method.upper()}\n{path}\n{owner_line}{body_sha256}".encode(
            "ascii"
        )
    )
    digest = hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    return f"{version}={digest}"


def verify_control_plane_signature(
    *,
    secret: str,
    max_age_seconds: int,
    method: str,
    path: str,
    body: bytes,
    timestamp_value: str | None,
    signature_value: str | None,
    now: int | None = None,
    owner: str | None = None,
) -> str | None:
    """Return a stable, content-free rejection code or ``None`` when valid."""

    if not timestamp_value or not signature_value:
        return "CONTROL_PLANE_SIGNATURE_REQUIRED"
    try:
        timestamp = int(timestamp_value)
    except ValueError:
        return "CONTROL_PLANE_SIGNATURE_INVALID"

    current_time = int(time.time()) if now is None else now
    if abs(current_time - timestamp) > max_age_seconds:
        return "CONTROL_PLANE_SIGNATURE_EXPIRED"

    prefix = "v2=" if owner is not None else SIGNATURE_PREFIX
    if not signature_value.startswith(prefix):
        return "CONTROL_PLANE_SIGNATURE_INVALID"
    received = signature_value.removeprefix(prefix)
    if not SIGNATURE_PATTERN.fullmatch(received):
        return "CONTROL_PLANE_SIGNATURE_INVALID"

    expected = build_control_plane_signature(secret, timestamp, method, path, body, owner)
    if not hmac.compare_digest(expected, signature_value):
        return "CONTROL_PLANE_SIGNATURE_INVALID"
    return None


class ControlPlaneHmacMiddleware:
    """Validate a Worker HMAC before multipart parsing in hosted environments."""

    def __init__(self, app: ASGIApp, *, settings: Settings) -> None:
        self.app = app
        self.required = settings.control_plane_hmac_is_required
        self.secret = (
            settings.control_plane_hmac_secret.get_secret_value()
            if settings.control_plane_hmac_secret is not None
            else None
        )
        self.max_age_seconds = settings.control_plane_hmac_max_age_seconds
        self.max_body_bytes = settings.max_upload_bytes + MULTIPART_OVERHEAD_ALLOWANCE_BYTES

    async def __call__(self, scope: dict, receive: Receive, send: Send) -> None:
        if (
            not self.required
            or scope.get("type") != "http"
            or scope.get("method") != "POST"
            or scope.get("path") not in PROTECTED_PATHS
        ):
            await self.app(scope, receive, send)
            return

        body = await self._read_body(receive)
        if body is None:
            await self._reject(send, 413, "CONTROL_PLANE_BODY_TOO_LARGE")
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        assert self.secret is not None  # Settings rejects a missing hosted secret.
        owner = None
        if scope.get("path") == "/v1/delivery":
            owner = headers.get("x-workbookcare-owner", "")
            if not SIGNATURE_PATTERN.fullmatch(owner):
                await self._reject(send, 401, "DELIVERY_OWNER_REQUIRED")
                return
        rejection_code = verify_control_plane_signature(
            secret=self.secret,
            max_age_seconds=self.max_age_seconds,
            method=scope["method"],
            path=scope["path"],
            body=body,
            timestamp_value=headers.get(TIMESTAMP_HEADER),
            signature_value=headers.get(SIGNATURE_HEADER),
            owner=owner,
        )
        if rejection_code is not None:
            status_code = 401 if rejection_code != "CONTROL_PLANE_SIGNATURE_INVALID" else 403
            await self._reject(send, status_code, rejection_code)
            return
        if owner is not None:
            scope["delivery_owner_verified"] = True

        delivered = False

        async def replay_receive() -> dict:
            nonlocal delivered
            if delivered:
                return {"type": "http.disconnect"}
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay_receive, send)

    async def _read_body(self, receive: Receive) -> bytes | None:
        chunks: list[bytes] = []
        received_bytes = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return None
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            received_bytes += len(chunk)
            if received_bytes > self.max_body_bytes:
                return None
            chunks.append(chunk)
            if not message.get("more_body", False):
                return b"".join(chunks)

    async def _reject(self, send: Send, status_code: int, code: str) -> None:
        log_safe_event(
            "control_plane_request_rejected",
            execution_status="rejected",
            safe_error_code=code,
        )
        payload = json.dumps(
            {"error": {"code": code, "message": "Unauthorized control-plane request."}},
            separators=(",", ":"),
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": payload})
