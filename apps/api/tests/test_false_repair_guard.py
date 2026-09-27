"""Frozen mixed synthetic RP01/RP02 oracle exercised through real OOXML paths."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from app.config import Settings
from app.delivery_inputs import PROFILE_1, PROFILE_2, PROFILE_COMBINED, inspect_input, preflight
from app.delivery_patch import patch_workbook, verify_output
from app.delivery_plan import build_plan
from app.delivery_store import DeliveryStore
from app.errors import WorkbookCareError

ROOT = Path(__file__).resolve().parents[3]
ORACLE = json.loads(
    (ROOT / "artifacts/synthetic_validation/false-repair-guard01/expected-v2.json").read_text(
        encoding="utf-8"
    )
)
CONTROL = json.loads(
    (ROOT / "artifacts/synthetic_validation/false-repair-guard01/expected-supported-control.json")
    .read_text(encoding="utf-8")
)
SPEC = importlib.util.spec_from_file_location(
    "synthetic_delivery_guard", ROOT / "scripts/generate_delivery_fixtures.py"
)
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
PKG = "http://schemas.openxmlformats.org/package/2006/content-types"
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
SHEET = ORACLE["sheet"]


def mixed_workbook(oracle: dict = ORACLE) -> bytes:
    """Reuse the legacy raw OOXML generator and substitute the frozen case's cells."""
    cells = oracle["inputs"]
    rows: dict[int, list[tuple[str, object]]] = {}
    for address, value in cells.items():
        row = int("".join(c for c in address if c.isdigit()))
        rows.setdefault(row, []).append((address, value))
    worksheet = ET.Element(f"{{{MAIN}}}worksheet")
    sheet_data = ET.SubElement(worksheet, f"{{{MAIN}}}sheetData")
    for number, entries in sorted(rows.items()):
        row = ET.SubElement(sheet_data, f"{{{MAIN}}}row", r=str(number))
        for address, value in sorted(entries):
            if value is None:
                continue
            attrs = {"r": address}
            if address == "E3":
                attrs["s"] = "1"
            elif address == "B2":
                attrs["s"] = "2"
            elif address == "B3":
                attrs["s"] = "3"
            if isinstance(value, str) and not value.startswith("="):
                attrs["t"] = "inlineStr"
            cell = ET.SubElement(row, f"{{{MAIN}}}c", attrs)
            if isinstance(value, str) and value.startswith("="):
                ET.SubElement(cell, f"{{{MAIN}}}f").text = value[1:]
            elif isinstance(value, str):
                ET.SubElement(ET.SubElement(cell, f"{{{MAIN}}}is"), f"{{{MAIN}}}t").text = value
            else:
                ET.SubElement(cell, f"{{{MAIN}}}v").text = str(value)
    styles = ET.Element(f"{{{MAIN}}}styleSheet")
    fmts = ET.SubElement(styles, f"{{{MAIN}}}numFmts", count="1")
    ET.SubElement(fmts, f"{{{MAIN}}}numFmt", numFmtId="164", formatCode="00000")
    xfs = ET.SubElement(styles, f"{{{MAIN}}}cellXfs", count="4")
    ET.SubElement(xfs, f"{{{MAIN}}}xf", numFmtId="0")
    ET.SubElement(xfs, f"{{{MAIN}}}xf", numFmtId="164", applyNumberFormat="1")
    ET.SubElement(xfs, f"{{{MAIN}}}xf", numFmtId="1", applyNumberFormat="1")
    ET.SubElement(xfs, f"{{{MAIN}}}xf", numFmtId="3", applyNumberFormat="1")
    source = BytesIO(FIXTURE.workbook_bytes())
    output = BytesIO()
    with ZipFile(source) as archive, ZipFile(output, "w") as target:
        for entry in archive.infolist():
            raw = archive.read(entry.filename)
            if entry.filename == "xl/worksheets/sheet1.xml":
                raw = ET.tostring(worksheet, encoding="utf-8", xml_declaration=True)
            elif entry.filename == "xl/workbook.xml":
                root = ET.fromstring(raw)
                root.find(f"{{{MAIN}}}sheets/{{{MAIN}}}sheet").set("name", SHEET)
                raw = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            elif entry.filename == "[Content_Types].xml":
                root = ET.fromstring(raw)
                ET.SubElement(
                    root, f"{{{PKG}}}Override", PartName="/xl/styles.xml",
                    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml",
                )
                raw = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            elif entry.filename == "xl/_rels/workbook.xml.rels":
                root = ET.fromstring(raw)
                ET.SubElement(
                    root, f"{{{RELS}}}Relationship", Id="rId2",
                    Type=OFFICE + "styles", Target="styles.xml",
                )
                raw = ET.tostring(root, encoding="utf-8", xml_declaration=True)
            target.writestr(entry, raw)
        target.writestr(
            "xl/styles.xml", ET.tostring(styles, encoding="utf-8", xml_declaration=True)
        )
    return output.getvalue()


def policy(profile: str, targets: list[str]) -> dict:
    return {
        "profile": profile,
        "sheet": SHEET,
        "targets": targets,
        "role": "AMOUNT",
        "confirmed": True,
        "anchor": "F2",
        "anchor_formula": "=C2*D2",
    }


def test_padded_format_is_ambiguous_even_with_amount_intent() -> None:
    source = mixed_workbook()
    snapshot = inspect_input("guard.xlsx", source, Settings())
    assert snapshot["cells"][SHEET]["E3"]["value"] == ORACLE["inputs"]["E3"]
    assert snapshot["cells"][SHEET]["E3"]["style"] == "1"
    assert preflight(snapshot, policy(PROFILE_1, ["B2", "B3"]))["eligible_count"] == 2
    for address in ORACLE["explicit_numeric_request_reject"]:
        result = preflight(snapshot, policy(PROFILE_1, [address]))
        assert result["status"] == "UNSUPPORTED", address
        assert result["eligible_count"] == 0, address
    for address in ORACLE["explicit_blank_restore_request_reject"]:
        result = preflight(snapshot, policy(PROFILE_2, [address]))
        assert result["status"] == "UNSUPPORTED", address


def test_mixed_approved_plan_patches_real_separate_xlsx(tmp_path: Path) -> None:
    source = mixed_workbook(CONTROL)
    before_hash = hashlib.sha256(source).hexdigest()
    snapshot = inspect_input("guard.xlsx", source, Settings())
    store = DeliveryStore(tmp_path)
    job = store.create("owner", source, snapshot, "false-repair-guard-request")
    combined = {
        "profile": PROFILE_COMBINED,
        "items": [policy(PROFILE_1, ["B2", "B3"]), policy(PROFILE_2, ["F3"])],
    }
    plan = build_plan(job, combined)
    assert {(p["sheet"], p["cell"]) for p in plan["patches"]} == {
        (SHEET, cell) for cell in ORACLE["approved_changes"]
    }
    assert plan["source_cache_used"] is False
    assert plan["expected_calculated_values"][SHEET]["F3"]["value"] == 20
    assert plan["expected_calculated_values"][SHEET]["G2"]["value"] == 5
    repaired = patch_workbook(source, snapshot, plan)
    verified = verify_output(source, repaired, plan, Settings())
    output = inspect_input("repaired.xlsx", repaired, Settings())
    for address, expected in CONTROL["approved_changes"].items():
        assert output["cells"][SHEET][address]["type"] == expected["type"]
        assert output["cells"][SHEET][address]["value"] == (
            str(expected["value"]) if expected["type"] == "number" else expected["value"]
        )
    for address in CONTROL["keep_unselected"]:
        actual = output["cells"][SHEET].get(address, {"type": "blank", "value": None})
        original = snapshot["cells"][SHEET].get(address, {"type": "blank", "value": None})
        assert {k: v for k, v in actual.items() if k != "cached"} == {
            k: v for k, v in original.items() if k != "cached"
        }, address
    assert float(output["cells"][SHEET]["G2"]["cached"]) == 5
    assert output["cells"][SHEET].get("F4", {}).get("value") is None
    assert hashlib.sha256(source).hexdigest() == before_hash
    assert repaired != source
    assert verified["source_hash"] == before_hash


def test_original_v2_refuses_unsupported_whole_file_formula(tmp_path: Path) -> None:
    source = mixed_workbook()
    snapshot = inspect_input("guard.xlsx", source, Settings())
    store = DeliveryStore(tmp_path)
    job = store.create("owner", source, snapshot, "false-repair-guard-v2-request")
    combined = {
        "profile": PROFILE_COMBINED,
        "items": [policy(PROFILE_1, ["B2", "B3"]), policy(PROFILE_2, ["F3"])],
    }
    with pytest.raises(WorkbookCareError) as error:
        build_plan(job, combined)
    assert error.value.code == "ENGINE_UNSUPPORTED"
