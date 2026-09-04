from __future__ import annotations

import asyncio
import json

from fastapi.testclient import TestClient

from app.main import app, unexpected_error_handler

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "workbookcare-api"}


def test_liveness_and_readiness_are_content_free_and_versioned() -> None:
    live = client.get("/health/live")
    ready = client.get("/health/ready")

    assert live.status_code == ready.status_code == 200
    assert live.json() == {"status": "live", "service": "workbookcare-api"}
    assert ready.json() == {
        "status": "ready",
        "service": "workbookcare-api",
        "scanner_version": "0.1.3",
        "base_rule_set_version": "2026.09.4",
        "formula_audit_rule_set_version": "2026.09.5",
        "release_candidate_version": "m4-formula-audit-rc1",
    }
    assert "path" not in ready.text
    assert "secret" not in ready.text.lower()


def test_unexpected_error_handler_returns_only_a_safe_error() -> None:
    response = asyncio.run(unexpected_error_handler(None, RuntimeError("private workbook detail")))

    assert response.status_code == 500
    assert json.loads(response.body) == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        }
    }
    assert b"private workbook detail" not in response.body


def test_scan_endpoint_returns_structured_result(risky_workbook_bytes: bytes) -> None:
    response = client.post(
        "/v1/scans",
        files={
            "file": (
                "monthly-report.xlsx",
                risky_workbook_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "monthly-report.xlsx"
    assert payload["summary"]["issue_count"] >= 1
    assert payload["quote"]["currency"] == "KRW"
    assert payload["limitations"]


def test_scan_endpoint_returns_safe_error_shape() -> None:
    response = client.post(
        "/v1/scans",
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
