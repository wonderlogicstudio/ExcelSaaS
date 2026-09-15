from __future__ import annotations

import copy
from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from openpyxl import Workbook
from test_delivery_inputs import policy
from test_delivery_plan import make_job

from app.config import Settings
from app.delivery_artifacts import verification_html
from app.delivery_inputs import PROFILE_2, inspect_input
from app.delivery_patch import patch_workbook, verify_output
from app.delivery_plan import build_plan
from app.delivery_store import DeliveryStore
from app.errors import WorkbookCareError


def scan_stub(findings=(), *, truncated=False, issue_count=None):
    findings = list(findings)
    return SimpleNamespace(
        workbook=SimpleNamespace(scan_truncated=truncated),
        summary=SimpleNamespace(issue_count=len(findings) if issue_count is None else issue_count),
        findings=findings,
    )


def audit_stub(candidates=(), *, status="COMPLETED", limitations=()):
    return SimpleNamespace(
        status=status,
        candidates=list(candidates),
        limitations=list(limitations),
        rule_set_version="test-m4",
    )


def finding(rule_code, sheet, cell, *, subtype=None):
    return SimpleNamespace(
        finding_key=f"{rule_code}:{sheet}:{cell}",
        rule_code=rule_code,
        sheet=sheet,
        cell=cell,
        formula_pattern=SimpleNamespace(pattern_subtype=subtype) if subtype else None,
    )


def rewrite(payload, part, operation):
    out = BytesIO()
    with ZipFile(BytesIO(payload)) as source, ZipFile(out, "w") as dest:
        for item in source.infolist():
            raw = source.read(item.filename)
            dest.writestr(item, operation(raw) if item.filename == part else raw)
    return out.getvalue()


@pytest.mark.parametrize(
    "profile,targets,value",
    [("RP01_NUMERIC_TEXT_FIELD_V1", ["B2", "B3"], 15500), (PROFILE_2, ["F3"], 18200)],
)
def test_actual_minimal_patch_and_whole_calculation(tmp_path, profile, targets, value):
    store, job = make_job(tmp_path)
    plan = build_plan(job, policy(profile, targets))
    output = patch_workbook(job["source"], job["snapshot"], plan)
    checks = verify_output(job["source"], output, plan, Settings())
    assert all(c["status"] == "PASS" for c in checks["checks"])
    assert checks["patch_count"] == len(targets)
    assert checks["output_hash"] != checks["source_hash"]
    assert store.load("owner", job["id"])["source"] == job["source"]
    assert (
        plan["expected_calculated_values"]["검증"]["F12" if profile == PROFILE_2 else "H2"]["value"]
        == value
    )
    assert inspect_input("out.xlsx", output, Settings())["cells"]["검증"]["A2"]["value"] == "00123"


@pytest.mark.parametrize(
    "part,old,new",
    [
        ("xl/worksheets/sheet1.xml", b"<v>1500</v>", b"<v>1501</v>"),
        ("xl/worksheets/sheet1.xml", b'r="B2"', b'r="B2" s="7"'),
        ("xl/worksheets/sheet1.xml", b'r="B2"', b'r="B2" cm="1"'),
        ("xl/worksheets/sheet1.xml", b'r="C2"', b'r="C2" s="1"'),
        ("xl/worksheets/sheet1.xml", b"<v>15500.0</v>", b"<v>1</v>"),
        ("xl/workbook.xml", b'name="', b'name="changed'),
        ("_rels/.rels", b"rId1", b"rId2"),
    ],
)
def test_unauthorized_change_never_passes(tmp_path, part, old, new):
    _, job = make_job(tmp_path)
    plan = build_plan(job, policy())
    output = patch_workbook(job["source"], job["snapshot"], plan)

    def corrupt(raw):
        assert old in raw
        return raw.replace(old, new, 1)

    altered = rewrite(output, part, corrupt)
    with pytest.raises((WorkbookCareError, KeyError)):
        verify_output(job["source"], altered, plan, Settings())


def test_partial_patch_blocked_and_shared_string_member_preserved(tmp_path):
    _, job = make_job(tmp_path)
    # Reuse a shared string in two cells: changing B2 must leave B3 and the table alone.
    source = rewrite(
        job["source"],
        "xl/worksheets/sheet1.xml",
        lambda raw: raw.replace(
            b'<c r="B2" t="inlineStr"><is><t xml:space="preserve">12000</t></is></c>',
            b'<c r="B2" t="s"><v>0</v></c>',
        ).replace(
            b'<c r="B3" t="inlineStr"><is><t xml:space="preserve">3,500</t></is></c>',
            b'<c r="B3" t="s"><v>0</v></c>',
        ),
    )
    out = BytesIO(source)
    with ZipFile(out, "a") as z:
        z.writestr(
            "xl/sharedStrings.xml",
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>12000</t></si></sst>',
        )
    source = out.getvalue()
    source = rewrite(
        source,
        "[Content_Types].xml",
        lambda raw: raw.replace(
            b"</Types>",
            b'<Override PartName="/xl/sharedStrings.xml" '
            b'ContentType="application/vnd.openxmlformats-officedocument.spreadsheet'
            b'ml.sharedStrings+xml"/></Types>',
        ),
    )
    source = rewrite(
        source,
        "xl/_rels/workbook.xml.rels",
        lambda raw: raw.replace(
            b"</Relationships>",
            b'<Relationship Id="rId2" '
            b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationsh'
            b'ips/sharedStrings" Target="sharedStrings.xml"/></Relationships>',
        ),
    )
    job["source"] = source
    job["snapshot"] = inspect_input("s.xlsx", source, Settings())
    plan = build_plan(job, policy(targets=["B2"]))
    repaired = patch_workbook(source, job["snapshot"], plan)
    assert verify_output(source, repaired, plan, Settings())["patch_count"] == 1
    assert inspect_input("out.xlsx", repaired, Settings())["cells"]["검증"]["B3"]["type"] == "text"
    with ZipFile(BytesIO(source)) as a, ZipFile(BytesIO(repaired)) as b:
        assert a.read("xl/sharedStrings.xml") == b.read("xl/sharedStrings.xml")
    incomplete = copy.deepcopy(plan)
    incomplete["patches"] = []
    with pytest.raises(WorkbookCareError):
        verify_output(source, patch_workbook(source, job["snapshot"], incomplete), plan, Settings())


def test_retained_static_target_finding_is_blocked(tmp_path, monkeypatch):
    _, job = make_job(tmp_path)
    plan = build_plan(job, policy(targets=["B2"]))
    output = patch_workbook(job["source"], job["snapshot"], plan)
    target = plan["patches"][0]
    retained = finding("NUMBER_STORED_AS_TEXT", target["sheet"], target["cell"])
    monkeypatch.setattr("app.delivery_patch.scan_workbook", lambda *a, **k: scan_stub([retained]))
    monkeypatch.setattr("app.delivery_patch.run_formula_audit", lambda *a, **k: audit_stub())
    with pytest.raises(WorkbookCareError) as error:
        verify_output(job["source"], output, plan, Settings())
    assert error.value.code == "TARGET_STATIC_FINDING_REMAINING"


def test_retained_formula_target_candidate_is_blocked(tmp_path, monkeypatch):
    _, job = make_job(tmp_path)
    plan = build_plan(job, policy(PROFILE_2, ["F3"]))
    output = patch_workbook(job["source"], job["snapshot"], plan)
    target = plan["patches"][0]
    retained = finding(
        "FORMULA_PATTERN_GAP",
        target["sheet"],
        target["cell"],
        subtype="BLANK_GAP_CANDIDATE",
    )
    monkeypatch.setattr("app.delivery_patch.scan_workbook", lambda *a, **k: scan_stub())
    monkeypatch.setattr(
        "app.delivery_patch.run_formula_audit", lambda *a, **k: audit_stub([retained])
    )
    with pytest.raises(WorkbookCareError) as error:
        verify_output(job["source"], output, plan, Settings())
    assert error.value.code == "TARGET_FORMULA_CANDIDATE_REMAINING"


def test_new_formula_candidate_is_blocked(tmp_path, monkeypatch):
    _, job = make_job(tmp_path)
    plan = build_plan(job, policy(PROFILE_2, ["F3"]))
    output = patch_workbook(job["source"], job["snapshot"], plan)
    new_candidate = finding(
        "FORMULA_PATTERN_GAP",
        plan["patches"][0]["sheet"],
        "F4",
        subtype="BLANK_GAP_CANDIDATE",
    )
    calls = iter([audit_stub(), audit_stub([new_candidate])])
    monkeypatch.setattr("app.delivery_patch.scan_workbook", lambda *a, **k: scan_stub())
    monkeypatch.setattr("app.delivery_patch.run_formula_audit", lambda *a, **k: next(calls))
    with pytest.raises(WorkbookCareError) as error:
        verify_output(job["source"], output, plan, Settings())
    assert error.value.code == "NEW_FORMULA_AUDIT_CANDIDATES"


def test_incomplete_formula_audit_is_blocked(tmp_path, monkeypatch):
    _, job = make_job(tmp_path)
    plan = build_plan(job, policy())
    output = patch_workbook(job["source"], job["snapshot"], plan)
    monkeypatch.setattr("app.delivery_patch.scan_workbook", lambda *a, **k: scan_stub())
    monkeypatch.setattr(
        "app.delivery_patch.run_formula_audit",
        lambda *a, **k: audit_stub(status="SKIPPED_TRUNCATED"),
    )
    with pytest.raises(WorkbookCareError) as error:
        verify_output(job["source"], output, plan, Settings())
    assert error.value.code == "INCOMPLETE_FORMULA_AUDIT_VALIDATION"


def test_unrelated_remaining_candidate_and_no_original_target_candidate_can_pass(
    tmp_path, monkeypatch
):
    _, job = make_job(tmp_path)
    plan = build_plan(job, policy(targets=["B2"]))
    output = patch_workbook(job["source"], job["snapshot"], plan)
    unrelated = finding(
        "FORMULA_PATTERN_GAP",
        plan["patches"][0]["sheet"],
        "F9",
        subtype="BLANK_GAP_CANDIDATE",
    )
    monkeypatch.setattr("app.delivery_patch.scan_workbook", lambda *a, **k: scan_stub())
    monkeypatch.setattr(
        "app.delivery_patch.run_formula_audit",
        lambda *a, **k: audit_stub([unrelated]),
    )
    result = verify_output(job["source"], output, plan, Settings())
    codes = {check["code"] for check in result["checks"]}
    assert result["formula_candidates_remaining"] == 1
    assert result["detectors"]["formula"]["target_before"] == []
    assert "TARGET_FORMULA_CANDIDATES_RESOLVED" not in codes
    assert all(check["status"] == "PASS" for check in result["checks"])



def test_incomplete_static_detail_count_is_blocked(tmp_path, monkeypatch):
    _, job = make_job(tmp_path)
    plan = build_plan(job, policy())
    output = patch_workbook(job["source"], job["snapshot"], plan)
    monkeypatch.setattr(
        "app.delivery_patch.scan_workbook", lambda *a, **k: scan_stub(issue_count=1)
    )
    monkeypatch.setattr("app.delivery_patch.run_formula_audit", lambda *a, **k: audit_stub())
    with pytest.raises(WorkbookCareError) as error:
        verify_output(job["source"], output, plan, Settings())
    assert error.value.code == "INCOMPLETE_STATIC_VALIDATION"


def test_formula_abstained_numeric_only_repair_stays_supported(tmp_path, monkeypatch):
    book = Workbook()
    sheet = book.active
    sheet.title = policy()["sheet"]
    sheet["B2"] = "12,000"
    source_io = BytesIO()
    book.save(source_io)
    book.close()
    source = rewrite(
        source_io.getvalue(),
        "xl/workbook.xml",
        lambda raw: raw.replace(b"<workbookProtection/>", b""),
    )
    snapshot = inspect_input("numeric-only.xlsx", source, Settings())
    store = DeliveryStore(tmp_path)
    job = store.create("owner", source, snapshot, "numeric-only")
    plan = build_plan(job, policy(targets=["B2"]))
    output = patch_workbook(source, snapshot, plan)
    result = verify_output(source, output, plan, Settings())
    codes = {check["code"] for check in result["checks"]}
    assert result["detectors"]["formula_comparison_status"] == "NOT_ESTABLISHED"
    assert "FORMULA_AUDIT_COMPLETED" not in codes
    assert "NO_NEW_FORMULA_CANDIDATES" not in codes
    assert "TARGET_FORMULA_CANDIDATES_RESOLVED" not in codes


def test_formula_abstained_then_completed_with_candidate_is_blocked(tmp_path, monkeypatch):
    _, job = make_job(tmp_path)
    plan = build_plan(job, policy(targets=["B2"]))
    output = patch_workbook(job["source"], job["snapshot"], plan)
    new_candidate = finding(
        "FORMULA_PATTERN_GAP",
        plan["patches"][0]["sheet"],
        "F9",
        subtype="BLANK_GAP_CANDIDATE",
    )
    calls = iter(
        [
            audit_stub(status="ABSTAINED_INSUFFICIENT_EVIDENCE"),
            audit_stub([new_candidate], status="COMPLETED"),
        ]
    )
    monkeypatch.setattr("app.delivery_patch.scan_workbook", lambda *a, **k: scan_stub())
    monkeypatch.setattr("app.delivery_patch.run_formula_audit", lambda *a, **k: next(calls))
    with pytest.raises(WorkbookCareError) as error:
        verify_output(job["source"], output, plan, Settings())
    assert error.value.code == "NEW_FORMULA_AUDIT_CANDIDATES"



def test_verification_html_summarizes_static_and_formula_detectors_without_raw_abstain(
    tmp_path, monkeypatch
):
    _, job = make_job(tmp_path)
    plan = build_plan(job, policy(targets=["B2"]))
    output = patch_workbook(job["source"], job["snapshot"], plan)
    monkeypatch.setattr("app.delivery_patch.scan_workbook", lambda *a, **k: scan_stub())
    monkeypatch.setattr(
        "app.delivery_patch.run_formula_audit",
        lambda *a, **k: audit_stub(
            status="ABSTAINED_INSUFFICIENT_EVIDENCE", limitations=["too_few_formulas"]
        ),
    )
    result = verify_output(job["source"], output, plan, Settings())
    result = {
        **result,
        "static_before": 8,
        "static_remaining": 8,
        "formula_candidates_before": 3,
        "formula_candidates_remaining": 0,
    }
    rendered = verification_html(plan, result).decode("utf-8")
    assert "정적 구조 발견: 원본 8건 → 수정본 8건" in rendered
    assert "수식 후보: 비교 미확정(증거 부족)" in rendered
    assert "수식 후보: 원본 3건 → 수정본 0건" not in rendered
    assert "수식 후보 비교에 필요한 증거가 부족" in rendered
    assert "too_few_formulas" in rendered
    assert "ABSTAINED_INSUFFICIENT_EVIDENCE" not in rendered
