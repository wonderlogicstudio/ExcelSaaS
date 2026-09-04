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
from typing import Final

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
        "processing_duration_ms",
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
