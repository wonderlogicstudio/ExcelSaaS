from fastapi.testclient import TestClient

from app.main import app


def test_scan_exposes_non_purchasable_product_deliverables(risky_workbook_bytes: bytes) -> None:
    response = TestClient(app).post(
        "/v1/scans", files={"file": ("synthetic-d01.xlsx", risky_workbook_bytes)}
    )
    assert response.status_code == 200
    result = response.json()
    products = {item["product_id"]: item for item in result["products"]}
    repair = products["APPROVED_REPAIR"]
    assert repair["capability_status"] == "PLANNED"
    assert repair["purchase_enabled"] is False
    assert repair["includes_repaired_workbook"] is True
    assert [item["kind"] for item in repair["deliverables"]] == [
        "REPAIRED_WORKBOOK_XLSX",
        "CHANGE_LOG_XLSX",
        "REVALIDATION_HTML",
    ]
    comparison = products["TWO_FILE_COMPARISON"]
    assert comparison["includes_repaired_workbook"] is False
    assert comparison["purchase_enabled"] is False
    assert comparison["capability_status"] == "PLANNED"
    assert result["finding_counts"]["returned_details"] == len(result["findings"])


def test_catalog_matches_frontend_fixture_and_preserves_legacy_scan(risky_workbook_bytes):
    import json
    from pathlib import Path

    from app.config import Settings
    from app.recommendation_engine import enrich_scan_result
    from app.scanner import scan_workbook
    from app.service_catalog import get_product_offerings

    root = Path(__file__).resolve().parents[3]
    fixture = json.loads(
        (root / "apps/web/src/data/product-catalog.fixture.json").read_text(encoding="utf-8")
    )
    assert fixture == [item.model_dump(mode="json") for item in get_product_offerings()]
    base = scan_workbook("synthetic-d01.xlsx", risky_workbook_bytes, Settings())
    enriched = enrich_scan_result(base)
    assert enriched.summary == base.summary
    assert enriched.workbook == base.workbook
    assert enriched.quote == base.quote
    assert [f.model_dump(exclude={"guidance"}) for f in enriched.findings] == [
        f.model_dump(exclude={"guidance"}) for f in base.findings
    ]
    assert all(item.purchase_enabled is False for item in enriched.products)
    assert not {"approval", "payment", "change_plan"}.intersection(enriched.model_dump())


def test_counts_retain_all_detections_when_details_are_capped(monkeypatch, risky_workbook_bytes):
    from app import main
    from app.config import Settings
    from app.scanner import scan_workbook

    full = scan_workbook("synthetic-d01.xlsx", risky_workbook_bytes, Settings())
    monkeypatch.setattr(main, "settings", Settings(finding_limit=1))
    response = TestClient(app).post(
        "/v1/scans", files={"file": ("synthetic-d01.xlsx", risky_workbook_bytes)}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == full.summary.model_dump()
    assert payload["finding_counts"] == {
        "total_detected": full.summary.issue_count,
        "returned_details": 1,
        "omitted_details": full.summary.issue_count - 1,
        "scan_complete": True,
    }
