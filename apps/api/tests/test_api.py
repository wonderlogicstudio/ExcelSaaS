from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "workbookcare-api"}


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
