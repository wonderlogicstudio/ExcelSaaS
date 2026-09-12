from __future__ import annotations

import copy
from io import BytesIO
from zipfile import ZipFile

import pytest
from test_delivery_inputs import policy
from test_delivery_plan import make_job

from app.config import Settings
from app.delivery_inputs import PROFILE_2, inspect_input
from app.delivery_patch import patch_workbook, verify_output
from app.delivery_plan import build_plan
from app.errors import WorkbookCareError


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
