"""Content-free observability helpers for a future hosted beta.

This module deliberately accepts a small, typed allowlist. It is not a
workbook-event logger and must never receive upload names, workbook data,
formula text, locations, URLs, identities, credentials, or free-form notes.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from .models import ScanResult

LOGGER = logging.getLogger("workbookcare.safe_events")

SAFE_EVENT_FIELDS: Final = frozenset(
    {
        "opaque_scan_id",
        "scanner_version",
        "base_rule_set_version",
        "formula_audit_rule_set_version",
        "release_candidate_version",
        "file_size_bucket",
        "sheet_count_bucket",
        "formula_count_bucket",
        "processing_duration_bucket",
        "rule_code",
        "subtype",
        "execution_status",
        "safe_error_code",
    }
)
SAFE_EVENT_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
SAFE_TEXT_VALUE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


def build_safe_event(event: str, fields: Mapping[str, object]) -> dict[str, object]:
    """Return a JSON-safe event or reject fields that can carry workbook data."""

    if not SAFE_EVENT_NAME.fullmatch(event):
        raise ValueError("event must be a fixed lowercase identifier")
    unknown = set(fields).difference(SAFE_EVENT_FIELDS)
    if unknown:
        raise ValueError(f"unsafe observability fields: {', '.join(sorted(unknown))}")

    payload: dict[str, object] = {"event": event}
    for key, value in fields.items():
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise ValueError(f"unsupported observability value for {key}")
        if isinstance(value, str) and not SAFE_TEXT_VALUE.fullmatch(value):
            raise ValueError(f"unsafe observability text value for {key}")
        payload[key] = value
    return payload


def log_safe_event(event: str, **fields: object) -> None:
    """Emit only an allowlisted JSON record without exception context."""

    LOGGER.info("%s", json.dumps(build_safe_event(event, fields), separators=(",", ":")))


def file_size_bucket(size_bytes: int) -> str:
    """Return a fixed, content-free file-size bucket."""

    if size_bytes <= 1 * 1024 * 1024:
        return "up_to_1mb"
    if size_bytes <= 5 * 1024 * 1024:
        return "1_to_5mb"
    return "5_to_10mb"


def count_bucket(count: int) -> str:
    """Return a compact count bucket without recording exact workbook shape."""

    if count == 0:
        return "zero"
    if count <= 5:
        return "1_to_5"
    if count <= 25:
        return "6_to_25"
    if count <= 100:
        return "26_to_100"
    return "over_100"


def processing_duration_bucket(duration_ms: int) -> str:
    """Avoid per-request timing precision while retaining operational utility."""

    if duration_ms < 1_000:
        return "under_1s"
    if duration_ms < 5_000:
        return "1_to_5s"
    if duration_ms < 15_000:
        return "5_to_15s"
    if duration_ms < 45_000:
        return "15_to_45s"
    return "45_to_60s"


def log_scan_completed(
    result: ScanResult,
    duration_ms: int,
    release_candidate_version: str,
) -> None:
    """Record scan outcomes with only versioned, value-free aggregates."""

    shared = {
        "opaque_scan_id": result.analysis_id,
        "scanner_version": result.scanner_version,
        "base_rule_set_version": result.rule_set_version,
        "release_candidate_version": release_candidate_version,
        "file_size_bucket": file_size_bucket(result.file_size_bytes),
        "sheet_count_bucket": count_bucket(result.workbook.sheet_count),
        "formula_count_bucket": count_bucket(result.workbook.formula_count),
        "processing_duration_bucket": processing_duration_bucket(duration_ms),
        "execution_status": "completed",
    }
    log_safe_event("scan_completed", **shared)
    for finding in result.findings:
        event_fields = {
            "opaque_scan_id": result.analysis_id,
            "scanner_version": result.scanner_version,
            "base_rule_set_version": result.rule_set_version,
            "release_candidate_version": release_candidate_version,
            "rule_code": finding.rule_code,
            "execution_status": "completed",
        }
        subtype = finding.formula_pattern.pattern_subtype if finding.formula_pattern else None
        if subtype:
            event_fields["subtype"] = subtype
        log_safe_event("scan_rule_observed", **event_fields)
