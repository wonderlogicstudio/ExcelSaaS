from __future__ import annotations

import pytest

from app.observability import (
    build_safe_event,
    count_bucket,
    file_size_bucket,
    processing_duration_bucket,
)


def test_safe_event_allows_only_documented_metadata() -> None:
    event = build_safe_event(
        "scan_completed",
        {
            "opaque_scan_id": "a1b2c3d4",
            "scanner_version": "0.1.3",
            "processing_duration_bucket": "1_to_5s",
            "execution_status": "completed",
        },
    )

    assert event == {
        "event": "scan_completed",
        "opaque_scan_id": "a1b2c3d4",
        "scanner_version": "0.1.3",
        "processing_duration_bucket": "1_to_5s",
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


def test_operational_buckets_do_not_record_exact_workbook_measurements() -> None:
    assert file_size_bucket(1) == "up_to_1mb"
    assert file_size_bucket(5 * 1024 * 1024) == "1_to_5mb"
    assert count_bucket(0) == "zero"
    assert count_bucket(26) == "26_to_100"
    assert processing_duration_bucket(999) == "under_1s"
    assert processing_duration_bucket(5_000) == "5_to_15s"
