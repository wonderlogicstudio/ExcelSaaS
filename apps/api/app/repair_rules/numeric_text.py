"""RP01: unambiguous integer text normalization."""

from __future__ import annotations

import re


def numeric_text(value: object) -> int | None:
    if not isinstance(value, str) or not re.fullmatch(
        r"[+-]?(?:0|[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+)", value
    ):
        return None
    result = int(value.replace(",", ""))
    if len(str(abs(result))) > 15 or result == 0 and value != "0":
        return None
    return result


def numeric_text_eligible(record: dict) -> bool:
    return (
        record.get("type") == "text"
        and numeric_text(record.get("value")) is not None
        and not record.get("special_format")
    )


def numeric_text_replacement(record: dict) -> dict:
    if not numeric_text_eligible(record):
        raise ValueError("record is not eligible for numeric text normalization")
    return {**record, "type": "number", "value": numeric_text(record.get("value"))}
