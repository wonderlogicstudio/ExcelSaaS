"""RP02: approved formula restoration into true blank cells."""

from __future__ import annotations


def blank_formula_eligible(record: dict) -> bool:
    return record.get("type") == "blank"


def formula_restore_replacement(record: dict, formula: str) -> dict:
    if not blank_formula_eligible(record):
        raise ValueError("record is not eligible for formula restoration")
    return {**record, "type": "formula", "value": formula}
