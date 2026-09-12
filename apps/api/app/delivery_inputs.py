"""D02 immutable, bounded OOXML inspection; no formula execution or workbook save."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from io import BytesIO
from zipfile import ZipFile

from defusedxml import ElementTree as ET

from .config import Settings
from .errors import WorkbookCareError
from .security import validate_ooxml

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
MAX_CELLS = 10_000
MAX_FORMULAS = 1_000
MAX_PATCHES = 100
MAX_BYTES = 2 * 1024 * 1024
PROFILE_1 = "RP01_NUMERIC_TEXT_FIELD_V1"
PROFILE_2 = "RP02_APPROVED_FORMULA_RESTORE_V1"
POLICY_VERSION = "ko-KR-integer15-v1"
CELL = re.compile(r"^[A-Z]{1,3}[1-9][0-9]{0,6}$")
PART = re.compile(
    r"^(?:\[Content_Types\]\.xml|_rels/\.rels|docProps/(?:core|app)\.xml|xl/(?:workbook\.xml|_rels/workbook\.xml\.rels|styles\.xml|sharedStrings\.xml|theme/theme[0-9]+\.xml|worksheets/sheet[0-9]+\.xml))$"
)
FORBIDDEN_FUNCTION = re.compile(
    r"\b(?:INDIRECT|OFFSET|NOW|TODAY|RAND|RANDBETWEEN|WEBSERVICE|FILTER|SORT|UNIQUE|XLOOKUP|_xlfn\.[A-Z]+)\s*\(",
    re.I,
)


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def reject(code: str, message: str, status: int = 400) -> None:
    raise WorkbookCareError(code, message, status)


def valid_cell(value: object) -> str:
    if not isinstance(value, str) or not CELL.fullmatch(value):
        reject("INVALID_LOCATION", "셀은 A1 형식의 정확한 단일 위치로 지정하세요.")
    letters = re.match("[A-Z]+", value).group()
    column = 0
    for letter in letters:
        column = column * 26 + ord(letter) - 64
    if column > 16384 or int(value[len(letters) :]) > 1048576:
        reject("INVALID_LOCATION", "Excel 셀 범위를 벗어난 위치입니다.")
    return value


def inspect_input(filename: str, payload: bytes, settings: Settings) -> dict:
    try:
        return _inspect_input(filename, payload, settings)
    except WorkbookCareError:
        raise
    except (ValueError, KeyError, TypeError, ET.ParseError):
        reject("UNSUPPORTED_FILE", "파일 내부 구조를 일관되게 읽을 수 없습니다.")


def _inspect_input(filename: str, payload: bytes, settings: Settings) -> dict:
    if not filename.lower().endswith(".xlsx"):
        reject("UNSUPPORTED_FILE", "사전 수정 검사는 매크로 없는 .xlsx만 지원합니다.")
    if len(payload) > MAX_BYTES:
        reject("LIMIT_EXCEEDED", "사전 수정 검사는 2MiB 이하 파일만 지원합니다.", 413)
    envelope = validate_ooxml(
        filename,
        payload,
        settings.model_copy(
            update={"max_uncompressed_mb": 20, "max_zip_entries": 256, "max_compression_ratio": 100}
        ),
    )
    issues: set[str] = set()
    if any(not PART.fullmatch(name) for name in envelope.names):
        issues.add("UNSUPPORTED_PACKAGE_PART")
    cells: dict[str, dict[str, dict]] = {}
    parts: dict[str, str] = {}
    sheet_parts: dict[str, str] = {}
    formula_count = 0
    with ZipFile(BytesIO(payload)) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            reject("UNSUPPORTED_FILE", "중복 내부 항목이 있는 파일은 수정하지 않습니다.")
        for name in archive.namelist():
            raw = archive.read(name)
            parts[name] = hashlib.sha256(raw).hexdigest()
            if name.endswith(".rels"):
                rels = ET.fromstring(raw)
                if any(r.get("TargetMode") == "External" for r in rels):
                    issues.add("EXTERNAL_RELATIONSHIP")
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        if workbook.find(NS + "workbookProtection") is not None:
            issues.add("PROTECTED_WORKBOOK")
        calc = workbook.find(NS + "calcPr")
        if calc is not None and calc.get("iterate") in {"1", "true"}:
            issues.add("ITERATIVE_CALCULATION")
        if len(workbook.findall(NS + "definedNames/" + NS + "definedName")) > 0:
            issues.add("DEFINED_NAMES_UNSUPPORTED")
        rel_path = "xl/_rels/workbook.xml.rels"
        if rel_path not in envelope.names:
            reject("UNSUPPORTED_FILE", "시트 연결 정보를 확인할 수 없습니다.")
        relationships = {
            r.get("Id"): r.get("Target", "") for r in ET.fromstring(archive.read(rel_path))
        }
        strings = []
        if "xl/sharedStrings.xml" in envelope.names:
            strings = [
                "".join(t.text or "" for t in si.iter(NS + "t"))
                for si in ET.fromstring(archive.read("xl/sharedStrings.xml"))
            ]
        date_styles: set[int] = set()
        if "xl/styles.xml" in envelope.names:
            styles = ET.fromstring(archive.read("xl/styles.xml"))
            custom = {
                int(n.get("numFmtId")): n.get("formatCode", "")
                for n in styles.findall(NS + "numFmts/" + NS + "numFmt")
            }
            for i, xf in enumerate(styles.findall(NS + "cellXfs/" + NS + "xf")):
                fmt = int(xf.get("numFmtId", "0"))
                if fmt in {*range(14, 23), 9, 10, 45, 46, 47} or re.search(
                    r"[ymdhHsS%]", custom.get(fmt, "")
                ):
                    date_styles.add(i)
        for sheet in workbook.findall(NS + "sheets/" + NS + "sheet"):
            name = sheet.get("name", "")
            target = relationships.get(sheet.get(REL + "id"), "")
            path = posixpath.normpath(
                target.lstrip("/") if target.startswith("/") else "xl/" + target
            )
            if (
                not name
                or name in cells
                or path not in envelope.names
                or not path.startswith("xl/worksheets/")
            ):
                reject("UNSUPPORTED_FILE", "시트 구성이 일관되지 않습니다.")
            if sheet.get("state", "visible") != "visible":
                issues.add("HIDDEN_SHEET")
            tree = ET.fromstring(archive.read(path))
            if any(
                tree.find(NS + tag) is not None
                for tag in [
                    "sheetProtection",
                    "mergeCells",
                    "tableParts",
                    "extLst",
                    "drawing",
                    "legacyDrawing",
                ]
            ):
                issues.add("UNSUPPORTED_SHEET_STRUCTURE")
            if any(n.get("hidden") in {"1", "true"} for n in tree.iter()):
                issues.add("HIDDEN_STRUCTURE")
            current: dict[str, dict] = {}
            for c in tree.findall(NS + "sheetData/" + NS + "row/" + NS + "c"):
                address = valid_cell(c.get("r"))
                if address in current:
                    reject("UNSUPPORTED_FILE", "중복 셀 위치가 있습니다.")
                t = c.get("t", "n")
                v = c.find(NS + "v")
                f = c.find(NS + "f")
                record = {"type": "blank", "value": None, "style": c.get("s", "0")}
                if f is not None:
                    formula_count += 1
                    if f.attrib or not f.text:
                        issues.add("SPECIAL_FORMULA")
                    value = "=" + str(f.text or "")
                    if (
                        FORBIDDEN_FUNCTION.search(value)
                        or "[" in value
                        or "!" in value
                        or any(
                            fn.upper()
                            not in {"SUM", "ROUND", "IF", "IFERROR", "AND", "OR", "ISNUMBER"}
                            for fn in re.findall(r"([A-Za-z_][A-Za-z0-9_.]*)\s*\(", value)
                        )
                    ):
                        issues.add("UNSUPPORTED_FORMULA")
                    record.update(
                        type="formula", value=value, cached=v.text if v is not None else None
                    )
                elif t in {"s", "inlineStr", "str"}:
                    if t == "s":
                        try:
                            value = strings[int(v.text)]
                        except (IndexError, ValueError, AttributeError, TypeError):
                            reject("UNSUPPORTED_FILE", "문자열 참조가 일관되지 않습니다.")
                    elif t == "inlineStr":
                        value = "".join(n.text or "" for n in c.iter(NS + "t"))
                    else:
                        value = v.text or "" if v is not None else ""
                    record.update(type="text", value=value)
                elif v is not None and v.text is not None:
                    if t == "b":
                        record.update(type="boolean", value=v.text == "1")
                    elif t in {"e", "d"}:
                        record.update(type="error" if t == "e" else "date", value=v.text)
                    elif t == "n":
                        record.update(type="number", value=v.text)
                    else:
                        issues.add("UNSUPPORTED_CELL_TYPE")
                if int(record["style"]) in date_styles:
                    record["special_format"] = True
                current[address] = record
                if len(current) + sum(len(c) for c in cells.values()) > MAX_CELLS:
                    reject("LIMIT_EXCEEDED", "사전 수정 검사 셀 한도를 초과했습니다.", 413)
            cells[name] = current
            sheet_parts[name] = path
            if sum(len(c) for c in cells.values()) > MAX_CELLS or formula_count > MAX_FORMULAS:
                reject("LIMIT_EXCEEDED", "사전 수정 검사 셀·수식 한도를 초과했습니다.", 413)
    if not cells or len(cells) > 10:
        issues.add("UNSUPPORTED_SHEET_COUNT")
    return {
        "source_hash": hashlib.sha256(payload).hexdigest(),
        "inventory_hash": digest(parts),
        "parts": parts,
        "sheet_parts": sheet_parts,
        "cells": cells,
        "formula_count": formula_count,
        "issues": sorted(issues),
    }


def numeric_text(value: object) -> int | None:
    if not isinstance(value, str) or not re.fullmatch(
        r"[+-]?(?:0|[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+)", value
    ):
        return None
    result = int(value.replace(",", ""))
    if len(str(abs(result))) > 15 or result == 0 and value != "0":
        return None
    return result


def preflight(snapshot: dict, policy: dict, *, calculation_verified: bool = False) -> dict:
    profile = policy.get("profile")
    if profile not in {PROFILE_1, PROFILE_2}:
        reject("INVALID_PROFILE", "지원하는 수정 종류를 선택하세요.")
    sheet = policy.get("sheet")
    selected = policy.get("targets", [])
    if (
        sheet not in snapshot["cells"]
        or not isinstance(selected, list)
        or len(selected) > MAX_PATCHES
    ):
        reject("INVALID_SELECTION", "시트와 100개 이하의 정확한 대상 셀을 선택하세요.")
    targets = sorted({valid_cell(c) for c in selected})
    if len(targets) != len(selected):
        reject("INVALID_SELECTION", "동일 셀을 중복 선택할 수 없습니다.")
    confirmed = policy.get("confirmed") is True
    reasons = list(snapshot["issues"])
    rows = []
    if not confirmed or profile == PROFILE_1 and policy.get("role") not in {"AMOUNT", "QUANTITY"}:
        reasons.append("UNCONFIRMED_BUSINESS_INTENT")
    anchor = policy.get("anchor")
    if profile == PROFILE_2:
        anchor_cell = snapshot["cells"][sheet].get(valid_cell(anchor), {})
        if anchor_cell.get("type") != "formula" or policy.get("anchor_formula") != anchor_cell.get(
            "value"
        ):
            reasons.append("UNCONFIRMED_ANCHOR")
    for cell in targets:
        current = snapshot["cells"][sheet].get(cell, {"type": "blank", "value": None, "style": "0"})
        eligible = not reasons
        why = []
        if profile == PROFILE_1:
            if (
                current["type"] != "text"
                or numeric_text(current["value"]) is None
                or current.get("special_format")
            ):
                eligible = False
                why.append("NOT_UNAMBIGUOUS_INTEGER_TEXT")
        elif current["type"] != "blank":
            eligible = False
            why.append("TARGET_NOT_TRUE_BLANK")
        rows.append(
            {
                "sheet": sheet,
                "cell": cell,
                "eligible": eligible,
                "current_type": current["type"],
                "reason_codes": why or reasons,
                "change_kind": "TYPE_NORMALIZATION" if profile == PROFILE_1 else "FORMULA_RESTORE",
            }
        )
    eligible_count = sum(row["eligible"] for row in rows)
    if any(not row["eligible"] for row in rows):
        reasons.append("INELIGIBLE_TARGETS")
    if not eligible_count:
        reasons.append("NO_ELIGIBLE_CHANGES")
    state = (
        "UNSUPPORTED"
        if reasons
        else "PRELIMINARY_ONLY"
        if not calculation_verified
        else "FEASIBILITY_VERIFIED"
    )
    return {
        "status": state,
        "profile": profile,
        "policy_version": POLICY_VERSION,
        "targets": rows,
        "eligible_count": eligible_count,
        "reason_codes": sorted(set(reasons)),
        "calculation_status": "NOT_RUN",
        "quote_enabled": False,
        "purchase_enabled": False,
        "source_hash": snapshot["source_hash"],
        "inventory_hash": snapshot["inventory_hash"],
        "policy_digest": digest(policy),
        "input_unchanged": True,
    }
