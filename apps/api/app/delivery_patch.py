"""Minimal OOXML member edits with independent non-target semantic preservation checks."""

from __future__ import annotations

import copy
import hashlib
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

from lxml import etree
from openpyxl.utils.cell import column_index_from_string, coordinate_from_string

from .config import Settings
from .delivery_calculation import calculate
from .delivery_inputs import NS, inspect_input, reject
from .delivery_plan import typed_source
from .scanner import SCANNER_VERSION, run_formula_audit, scan_workbook

PATCH_VERSION = "minimal-ooxml-patch-v1"


def xml_root(raw: bytes):
    parser = etree.XMLParser(
        resolve_entities=False,
        load_dtd=False,
        no_network=True,
        recover=False,
        huge_tree=False,
        remove_comments=False,
        remove_pis=False,
    )
    root = etree.fromstring(raw, parser)
    if root.getroottree().docinfo.doctype:
        reject("UNSUPPORTED_FILE", "DTD가 있는 XML은 수정하지 않습니다.")
    return root


def _cell_key(address: str) -> tuple[int, int]:
    column, row = coordinate_from_string(address)
    return row, column_index_from_string(column)


def _find_or_create(root, address: str):
    data = root.find(NS + "sheetData")
    if data is None:
        reject("UNSUPPORTED_FILE", "시트 데이터가 없습니다.")
    row_number, column_number = _cell_key(address)
    rows = list(data.findall(NS + "row"))
    row = next((r for r in rows if r.get("r") == str(row_number)), None)
    if row is None:
        row = etree.Element(NS + "row", r=str(row_number))
        following = next((r for r in rows if int(r.get("r")) > row_number), None)
        if following is None:
            data.append(row)
        else:
            following.addprevious(row)
    cells = list(row.findall(NS + "c"))
    cell = next((c for c in cells if c.get("r") == address), None)
    if cell is None:
        cell = etree.Element(NS + "c", r=address)
        following = next((c for c in cells if _cell_key(c.get("r"))[1] > column_number), None)
        if following is None:
            row.append(cell)
        else:
            following.addprevious(cell)
    return cell


def _set_cache(cell, value: dict):
    for child in list(cell):
        if child.tag == NS + "v":
            cell.remove(child)
    kind = value["type"]
    cell.attrib.pop("t", None)
    if kind == "text":
        cell.set("t", "str")
        text = value["value"]
    elif kind == "boolean":
        cell.set("t", "b")
        text = "1" if value["value"] else "0"
    elif kind == "number":
        text = str(value["value"])
    elif kind == "error":
        cell.set("t", "e")
        text = value["value"]
    else:
        reject("UNSUPPORTED_CACHE", "지원하지 않는 계산 결과 타입입니다.")
    etree.SubElement(cell, NS + "v").text = text


def patch_workbook(source: bytes, snapshot: dict, plan: dict) -> bytes:
    if hashlib.sha256(source).hexdigest() != plan["source_hash"]:
        reject("INPUT_INTEGRITY_FAILED", "원본이 계획과 다릅니다.", 409)
    with ZipFile(BytesIO(source)) as archive:
        trees = {}
        for patch in plan["patches"]:
            part = snapshot["sheet_parts"][patch["sheet"]]
            if part not in trees:
                trees[part] = xml_root(archive.read(part))
            cell = _find_or_create(trees[part], patch["cell"])
            # Only the approved business cell loses its old value/formula children.
            for child in list(cell):
                if child.tag not in {NS + "v", NS + "f", NS + "is"}:
                    reject("UNSUPPORTED_CELL_STRUCTURE", "지원하지 않는 셀 내부 구조입니다.")
                cell.remove(child)
            cell.attrib.pop("t", None)
            updated = patch["after"]
            if updated["type"] == "number":
                etree.SubElement(cell, NS + "v").text = str(updated["value"])
            elif updated["type"] == "formula":
                etree.SubElement(cell, NS + "f").text = updated["value"][1:]
            else:
                reject("UNSUPPORTED_PATCH", "지원하지 않는 변경입니다.")
        for change in plan["technical_changes"]:
            part = change["part"]
            if part not in trees:
                trees[part] = xml_root(archive.read(part))
            if change["kind"] == "FORMULA_CACHE":
                _set_cache(_find_or_create(trees[part], change["cell"]), change["after"])
            elif change["kind"] == "RECALCULATION_FLAGS":
                node = trees[part].find(NS + "calcPr")
                if node is None:
                    node = etree.SubElement(trees[part], NS + "calcPr")
                for key, value in change["attributes"].items():
                    node.set(key, value)
            elif change["kind"] == "SHEET_DIMENSION":
                node = trees[part].find(NS + "dimension")
                if node is not None:
                    node.set("ref", change["after"])
            else:
                reject("UNSUPPORTED_TECHNICAL_CHANGE", "계획의 보조 변경을 지원하지 않습니다.")
        output = BytesIO()
        with ZipFile(output, "w") as modified:
            for entry in archive.infolist():
                raw = (
                    etree.tostring(
                        trees[entry.filename],
                        encoding="UTF-8",
                        xml_declaration=True,
                        standalone=True,
                    )
                    if entry.filename in trees
                    else archive.read(entry.filename)
                )
                modified.writestr(entry, raw)
        return output.getvalue()


def normalized_cell(record: dict) -> dict:
    result = typed_source(record)
    if result["type"] == "number":
        result["value"] = str(Decimal(str(result["value"])).normalize())
    return result


def _shape(node):
    tag = (
        node.tag if isinstance(node.tag, str) else "COMMENT" if node.tag is etree.Comment else "PI"
    )
    return (
        tag,
        tuple(sorted(node.attrib.items())),
        node.text if node.text and node.text.strip() else None,
        node.tail if node.tail and node.tail.strip() else None,
        getattr(node, "target", None),
        tuple(_shape(child) for child in node),
    )


def _masked_tree(
    root,
    *,
    targets: set[str],
    caches: set[str],
    original_rows: set[str],
    dimension: bool = False,
    calculation: bool = False,
):
    root = copy.deepcopy(root)
    for cell in root.findall(NS + "sheetData/" + NS + "row/" + NS + "c"):
        if cell.get("r") in targets:
            cell.attrib.pop("t", None)
            for child in list(cell):
                if child.tag in {NS + "f", NS + "v", NS + "is"}:
                    cell.remove(child)
            if len(cell) == 0 and set(cell.attrib) == {"r"}:
                cell.getparent().remove(cell)
        elif cell.get("r") in caches:
            cell.attrib.pop("t", None)
            for v in list(cell.findall(NS + "v")):
                cell.remove(v)
    for row in root.findall(NS + "sheetData/" + NS + "row"):
        if row.get("r") not in original_rows and len(row) == 0 and set(row.attrib) == {"r"}:
            row.getparent().remove(row)
    if dimension:
        node = root.find(NS + "dimension")
        if node is not None:
            node.attrib.pop("ref", None)
    if calculation:
        node = root.find(NS + "calcPr")
        if node is not None:
            for name in ["calcMode", "fullCalcOnLoad", "forceFullCalc"]:
                node.attrib.pop(name, None)
            if not node.attrib and not len(node):
                node.getparent().remove(node)
    return _shape(root)


def _finding_identity(finding) -> dict:
    pattern = getattr(finding, "formula_pattern", None)
    return {
        "rule_code": finding.rule_code,
        "sheet": finding.sheet or "",
        "cell": finding.cell or "",
        "pattern_subtype": getattr(pattern, "pattern_subtype", None) if pattern else None,
    }


def _identity_key(item: dict) -> tuple[str, str, str]:
    return (item["rule_code"], item["sheet"], item["cell"])


def _sorted_identities(values):
    return sorted(values, key=lambda x: (x["sheet"], x["cell"], x["rule_code"]))


def _classify_detector(
    before: list[dict], after: list[dict], targets: set[tuple[str, str]]
) -> dict:
    before_by_key = {_identity_key(item): item for item in before}
    after_by_key = {_identity_key(item): item for item in after}
    target_before = {
        key: item for key, item in before_by_key.items() if (item["sheet"], item["cell"]) in targets
    }
    return {
        "before": _sorted_identities(before_by_key.values()),
        "remaining": _sorted_identities(after_by_key.values()),
        "resolved": _sorted_identities(
            before_by_key[k] for k in before_by_key.keys() - after_by_key.keys()
        ),
        "new": _sorted_identities(
            after_by_key[k] for k in after_by_key.keys() - before_by_key.keys()
        ),
        "target_before": _sorted_identities(target_before.values()),
        "target_remaining": _sorted_identities(
            target_before[k] for k in target_before if k in after_by_key
        ),
    }


def _detector_summary(source: bytes, output: bytes, plan: dict, settings: Settings) -> dict:
    targets = {(p["sheet"], p["cell"]) for p in plan["patches"]}
    scans = [scan_workbook("workbook.xlsx", data, settings) for data in [source, output]]
    if any(
        scan.workbook.scan_truncated
        or getattr(getattr(scan, "summary", None), "issue_count", len(scan.findings))
        != len(scan.findings)
        for scan in scans
    ):
        reject("INCOMPLETE_STATIC_VALIDATION", "정적 재검증을 완료하지 못했습니다.", 422)
    static = _classify_detector(
        [_finding_identity(f) for f in scans[0].findings],
        [_finding_identity(f) for f in scans[1].findings],
        targets,
    )
    if static["new"]:
        reject("NEW_STATIC_FINDINGS", "수정본에서 새 정적 발견이 나왔습니다.", 422)
    if static["target_remaining"]:
        reject(
            "TARGET_STATIC_FINDING_REMAINING",
            "승인한 대상 정적 발견이 수정본에 남아 있습니다.",
            422,
        )

    audits = [run_formula_audit("workbook.xlsx", data, settings) for data in [source, output]]
    before_status = audits[0].status
    after_status = audits[1].status

    def incomplete(status: str) -> bool:
        return status == "FAILED" or status.startswith("SKIPPED_")

    if incomplete(before_status) or incomplete(after_status):
        reject(
            "INCOMPLETE_FORMULA_AUDIT_VALIDATION",
            "수식 후보 재검증을 완료하지 못했습니다.",
            422,
        )

    formula_comparison_status = "NOT_ESTABLISHED"
    if before_status == "COMPLETED":
        if after_status != "COMPLETED":
            reject(
                "INCOMPLETE_FORMULA_AUDIT_VALIDATION",
                "수식 후보 재검증을 완료하지 못했습니다.",
                422,
            )
        formula_comparison_status = "COMPLETED"
        formula = _classify_detector(
            [_finding_identity(f) for f in audits[0].candidates],
            [_finding_identity(f) for f in audits[1].candidates],
            targets,
        )
        if formula["new"]:
            reject(
                "NEW_FORMULA_AUDIT_CANDIDATES",
                "수정본에서 새 수식 후보가 나왔습니다.",
                422,
            )
        if formula["target_remaining"]:
            reject(
                "TARGET_FORMULA_CANDIDATE_REMAINING",
                "승인한 대상 수식 후보가 수정본에 남아 있습니다.",
                422,
            )
    elif before_status == "ABSTAINED_INSUFFICIENT_EVIDENCE":
        if after_status == "ABSTAINED_INSUFFICIENT_EVIDENCE":
            formula = _classify_detector([], [], targets)
        elif after_status == "COMPLETED":
            after_candidates = [_finding_identity(f) for f in audits[1].candidates]
            formula = _classify_detector([], after_candidates, targets)
            if formula["remaining"]:
                reject(
                    "NEW_FORMULA_AUDIT_CANDIDATES",
                    "수정본에서 새 수식 후보가 나왔습니다.",
                    422,
                )
        else:
            reject(
                "INCOMPLETE_FORMULA_AUDIT_VALIDATION",
                "수식 후보 재검증을 완료하지 못했습니다.",
                422,
            )
    else:
        reject(
            "INCOMPLETE_FORMULA_AUDIT_VALIDATION",
            "수식 후보 재검증을 완료하지 못했습니다.",
            422,
        )

    return {
        "static": static,
        "formula": formula,
        "static_scanner_version": SCANNER_VERSION,
        "formula_audit_rule_set_version": audits[0].rule_set_version,
        "formula_audit_before_status": before_status,
        "formula_audit_after_status": after_status,
        "formula_audit_before_limitations": list(getattr(audits[0], "limitations", [])),
        "formula_audit_after_limitations": list(getattr(audits[1], "limitations", [])),
        "formula_comparison_status": formula_comparison_status,
    }

def verify_output(source: bytes, output: bytes, plan: dict, settings: Settings) -> dict:
    original = inspect_input("workbook.xlsx", source, settings)
    result = inspect_input("workbook.xlsx", output, settings)
    if (
        original["source_hash"] != plan["source_hash"]
        or original["inventory_hash"] != plan["inventory_hash"]
    ):
        reject("INPUT_INTEGRITY_FAILED", "계획의 원본이 일치하지 않습니다.", 409)
    if result["issues"]:
        reject("OUTPUT_VALIDATION_FAILED", "수정본에 지원하지 않는 구조가 있습니다.", 422)
    patches = {(p["sheet"], p["cell"]): p for p in plan["patches"]}
    actual = set()
    for sheet, rows in result["cells"].items():
        for address in set(rows) | set(original["cells"][sheet]):
            blank = {"type": "blank", "value": None, "style": "0"}
            old = normalized_cell(original["cells"][sheet].get(address, blank))
            new = normalized_cell(rows.get(address, blank))
            if old != new:
                key = (sheet, address)
                actual.add(key)
                if (
                    key not in patches
                    or old != normalized_cell(patches[key]["before"])
                    or new != normalized_cell(patches[key]["after"])
                ):
                    reject("UNAUTHORIZED_CHANGE", "승인 계획 외의 셀 변경을 발견했습니다.", 422)
    if actual != set(patches):
        reject("PARTIAL_PATCH", "승인한 변경 일부가 적용되지 않았습니다.", 422)
    changed_parts = {original["sheet_parts"][s] for s, _ in patches} | {
        c["part"] for c in plan["technical_changes"]
    }
    if set(original["parts"]) != set(result["parts"]):
        reject("PACKAGE_INVENTORY_CHANGED", "내부 파일 목록이 달라졌습니다.", 422)
    if any(
        original["parts"][p] != result["parts"][p]
        for p in original["parts"]
        if p not in changed_parts
    ):
        reject("UNAUTHORIZED_PART_CHANGE", "계획 밖의 내부 파일이 변경되었습니다.", 422)
    with ZipFile(BytesIO(source)) as before, ZipFile(BytesIO(output)) as after:
        for part in changed_parts:
            a = xml_root(before.read(part))
            b = xml_root(after.read(part))
            rows = {row.get("r") for row in a.findall(NS + "sheetData/" + NS + "row")}
            targets = {
                p["cell"] for p in plan["patches"] if original["sheet_parts"][p["sheet"]] == part
            }
            caches = {
                c["cell"]
                for c in plan["technical_changes"]
                if c["part"] == part and c["kind"] == "FORMULA_CACHE"
            }
            dimensions = any(
                c["part"] == part and c["kind"] == "SHEET_DIMENSION"
                for c in plan["technical_changes"]
            )
            flags = dict(
                targets=targets,
                caches=caches,
                original_rows=rows,
                dimension=dimensions,
                calculation=part == "xl/workbook.xml",
            )
            if _masked_tree(a, **flags) != _masked_tree(b, **flags):
                reject("UNAUTHORIZED_XML_CHANGE", "비대상 셀·서식·XML 구조가 달라졌습니다.", 422)
            for c in plan["technical_changes"]:
                if c["part"] != part:
                    continue
                if c["kind"] == "FORMULA_CACHE":
                    cell = next(
                        n
                        for n in b.findall(NS + "sheetData/" + NS + "row/" + NS + "c")
                        if n.get("r") == c["cell"]
                    )
                    v = cell.find(NS + "v")
                    raw = v.text or "" if v is not None else None
                    expected = c["after"]
                    if expected["type"] == "number":
                        same = (
                            raw is not None
                            and cell.get("t", "n") == "n"
                            and Decimal(raw) == Decimal(str(expected["value"]))
                        )
                    elif expected["type"] == "text":
                        same = cell.get("t") == "str" and raw == expected["value"]
                    elif expected["type"] == "boolean":
                        same = cell.get("t") == "b" and raw == ("1" if expected["value"] else "0")
                    else:
                        same = cell.get("t") == "e" and raw == expected["value"]
                    if not same:
                        reject(
                            "CACHE_VALIDATION_FAILED",
                            "계산 캐시가 검증 값과 일치하지 않습니다.",
                            422,
                        )
                elif c["kind"] == "RECALCULATION_FLAGS":
                    node = b.find(NS + "calcPr")
                    if node is None or any(node.get(k) != v for k, v in c["attributes"].items()):
                        reject("CALCULATION_FLAGS_MISMATCH", "계산 설정이 계획과 다릅니다.", 422)
                elif (
                    c["kind"] == "SHEET_DIMENSION"
                    and b.find(NS + "dimension").get("ref") != c["after"]
                ):
                    reject("DIMENSION_MISMATCH", "시트 범위가 계획과 다릅니다.", 422)
    calculated = calculate(result["cells"])
    if calculated["values"] != plan["expected_calculated_values"]:
        reject("POST_CALCULATION_MISMATCH", "후계산 값이 승인한 예상 영향과 다릅니다.", 422)
    detectors = _detector_summary(source, output, plan, settings)
    check_codes = [
        "SOURCE_IMMUTABLE",
        "EXACT_APPROVED_PATCH",
        "UNTOUCHED_MEMBERS",
        "NON_TARGET_XML_AND_STYLES",
        "TYPED_FORMULA_CACHES",
        "WHOLE_WORKBOOK_POST_CALCULATION",
        "NO_NEW_CALCULATION_ERRORS",
        "NO_NEW_STATIC_FINDINGS",
    ]
    if detectors["static"]["target_before"]:
        check_codes.append("TARGET_STATIC_FINDINGS_RESOLVED")
    if detectors["formula_comparison_status"] == "COMPLETED":
        check_codes.extend(["FORMULA_AUDIT_COMPLETED", "NO_NEW_FORMULA_CANDIDATES"])
        if detectors["formula"]["target_before"]:
            check_codes.append("TARGET_FORMULA_CANDIDATES_RESOLVED")
    checks = [{"code": code, "status": "PASS"} for code in check_codes]
    return {
        "checks": checks,
        "source_hash": original["source_hash"],
        "output_hash": result["source_hash"],
        "plan_digest": plan["digest"],
        "patch_count": len(patches),
        "untouched_member_count": len(original["parts"]) - len(changed_parts),
        "engine_version": calculated["engine_version"],
        "static_scanner_version": detectors["static_scanner_version"],
        "formula_audit_rule_set_version": detectors["formula_audit_rule_set_version"],
        "static_before": len(detectors["static"]["before"]),
        "static_remaining": len(detectors["static"]["remaining"]),
        "static_resolved": len(detectors["static"]["resolved"]),
        "formula_candidates_before": len(detectors["formula"]["before"]),
        "formula_candidates_remaining": len(detectors["formula"]["remaining"]),
        "formula_candidates_resolved": len(detectors["formula"]["resolved"]),
        "detectors": detectors,
        "coverage": calculated["coverage"],
        "business_truth_guaranteed": False,
    }
