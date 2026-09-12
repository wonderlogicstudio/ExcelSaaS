from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from test_delivery_execution import authorized, prepared
from test_delivery_execution import blueprint as blueprint

from app.delivery_execution import execute
from app.delivery_receipts import valid, verify_current
from app.errors import WorkbookCareError


@pytest.mark.parametrize(
    "change", ["signature", "source_hash", "plan_digest", "owner_binding", "key_id"]
)
def test_authenticated_receipt_tampering_is_rejected_before_patch(tmp_path, blueprint, change):
    store, job, settings = prepared(tmp_path, blueprint)
    approved = authorized(store, job, settings)
    assert verify_current(store, approved)["signature_valid"]
    changed = copy.deepcopy(approved)
    receipt = changed["state"]["approval"]["receipt"]
    if change in {"signature", "key_id"}:
        receipt[change] = "0" * 64
    else:
        receipt["payload"][change] = "0" * 64
    assert not valid(store, changed["state"]["approval"])
    with pytest.raises(WorkbookCareError) as error:
        execute(store, changed, settings)
    assert error.value.code == "APPROVAL_RECEIPT_INVALID"
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM delivery_artifacts").fetchone()[0] == 0


def test_receipt_integrity_is_not_execution_entitlement(tmp_path, blueprint):
    store, job, settings = prepared(tmp_path, blueprint)
    approved = authorized(store, job, settings)
    receipt = verify_current(store, approved)
    assert receipt["source_hash"] == job["snapshot"]["source_hash"]
    assert (
        receipt["plan_digest"] == job["state"]["plan"]["digest"]
        and receipt["historical_receipt_only"]
    )
    revoked = {**approved, "state": {**approved["state"], "internal_grant": None}}
    assert valid(store, revoked["state"]["approval"])
    with pytest.raises(WorkbookCareError) as error:
        execute(store, revoked, settings)
    assert error.value.code == "ENTITLEMENT_REQUIRED"
    public = json.dumps(receipt)
    with store.connection() as db:
        key = db.execute("SELECT secret FROM approval_receipt_key").fetchone()[0]
    assert key.hex() not in public and "secret" not in public


def test_holdout_oracle_remains_frozen_and_styles_are_supported():
    import hashlib

    from app.config import Settings
    from app.delivery_inputs import PROFILE_1, PROFILE_2, inspect_input, preflight

    root = Path(__file__).resolve().parents[3] / "samples/delivery-v3_2"
    expected = json.loads((root / "holdout-v2-expected.json").read_text(encoding="utf-8"))
    for name, sha in expected["source_hashes"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == sha
    source = inspect_input(
        "holdout.xlsx", (root / "delivery-holdout-v2.xlsx").read_bytes(), Settings()
    )
    assert source["issues"] == []
    base = {
        "sheet": "검증",
        "confirmed": True,
        "role": "AMOUNT",
        "anchor": "F2",
        "anchor_formula": "=ROUND(C2*D2*(1-E2),0)",
    }
    assert (
        preflight(source, {**base, "profile": PROFILE_1, "targets": ["B2", "B3"]})["eligible_count"]
        == 2
    )
    assert (
        preflight(source, {**base, "profile": PROFILE_2, "targets": ["F3"]})["eligible_count"] == 1
    )
    assert source["cells"]["검증"]["A2"]["style"] == "2"
    assert source["cells"]["검증"]["F3"]["style"] == "1"
    assert (
        preflight(source, {**base, "profile": PROFILE_1, "targets": ["A2"]})["eligible_count"] == 0
    )


def test_excel_rejected_unsorted_cells_cannot_enter_plan_or_order():
    from app.config import Settings
    from app.delivery_inputs import PROFILE_1, inspect_input, preflight

    root = Path(__file__).resolve().parents[3] / "samples/delivery-v3_2"
    source = inspect_input(
        "invalid-order.xlsx", (root / "delivery-holdout.xlsx").read_bytes(), Settings()
    )
    assert "UNSUPPORTED_CELL_ORDER" in source["issues"]
    result = preflight(
        source,
        {
            "profile": PROFILE_1,
            "sheet": "검증",
            "targets": ["B2", "B3"],
            "role": "AMOUNT",
            "confirmed": True,
        },
    )
    assert result["eligible_count"] == 0 and result["status"] == "UNSUPPORTED"
    assert not result["quote_enabled"] and not result["purchase_enabled"]
