from __future__ import annotations

import pytest

from app.observability import build_safe_event


def test_safe_event_allows_only_documented_metadata() -> None:
    event = build_safe_event(
        "scan_completed",
        {
            "opaque_scan_id": "a1b2c3d4",
            "scanner_version": "0.1.3",
            "processing_duration_ms": 2810,
            "execution_status": "completed",
        },
    )

    assert event == {
        "event": "scan_completed",
        "opaque_scan_id": "a1b2c3d4",
        "scanner_version": "0.1.3",
        "processing_duration_ms": 2810,
        "execution_status": "completed",
    }


@pytest.mark.parametrize(
    "field", ["filename", "sheet_name", "cell", "formula", "object_url", "email"]
)
def test_safe_event_rejects_workbook_and_identity_fields(field: str) -> None:
    with pytest.raises(ValueError, match="unsafe observability fields"):
        build_safe_event("scan_completed", {field: "not-allowed"})


def test_safe_event_rejects_free_text_values() -> None:
    with pytest.raises(ValueError, match="unsafe observability text value"):
        build_safe_event("scan_completed", {"execution_status": "customer workbook failed"})
