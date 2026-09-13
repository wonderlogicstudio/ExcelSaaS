from __future__ import annotations

import copy

import pytest
from test_comparison_service import prepared as compare_prepared
from test_delivery_execution import authorized, prepared
from test_delivery_execution import blueprint as blueprint

from app.comparison_service import comparison_entitled, execute_comparison
from app.config import Settings
from app.delivery_execution import execute
from app.delivery_hosted_rehearsal import available, grant
from app.delivery_rehearsal import entitled
from app.errors import WorkbookCareError


def hosted():
    return Settings(
        app_env="hosted_beta", cors_origins=["https://beta.example"],
        delivery_beta_enabled=True,
        hosted_synthetic_delivery_enabled=True,
        control_plane_hmac_secret="synthetic-only-proof-secret-00000000000000",
    )


def body(job):
    return {
        "revision": job["revision"],
        "acknowledge_no_payment": True,
        "acknowledge_limitations": True,
    }


def test_hosted_grant_is_not_payment_or_approval(tmp_path, blueprint):
    store, job, _ = prepared(tmp_path, blueprint)
    settings = hosted()
    assert not entitled(job, settings.app_env, True)  # Local grant cannot escape local beta.
    job = grant(store, job, body(job), settings)
    assert job["state"]["payment"] == "NOT_PURCHASED" and not job["state"].get("order_id")
    assert not job["state"].get("approval")
    with pytest.raises(WorkbookCareError) as error:
        execute(store, job, settings)
    assert error.value.code == "CURRENT_APPROVAL_REQUIRED"
    ready = execute(store, authorized(store, job, settings), settings)
    assert ready["state"]["status"] == "READY"
    assert not entitled(ready, "hosted_beta", False)
    assert not entitled(ready, "production", True)
    for field in ["owner", "plan_digest", "source_hash", "expires_at"]:
        changed = copy.deepcopy(ready)
        changed["state"]["internal_grant"][field] = 0 if field == "expires_at" else "changed"
        assert not entitled(changed, "hosted_beta", True)


def test_hosted_rehearsal_rejects_unregistered_order_notice_and_gate(tmp_path, blueprint):
    store, job, _ = prepared(tmp_path, blueprint)
    settings = hosted()
    for changes in [
        {"hosted_synthetic_delivery_enabled": False},
        {"app_env": "production"},
        {"app_env": "internal_beta"},
        {"payment_mode": "TOSS_TEST"},
    ]:
        assert not available(job, settings.model_copy(update=changes))
    for mutate in ["source", "order"]:
        changed = copy.deepcopy(job)
        if mutate == "source":
            changed["snapshot"]["source_hash"] = "0" * 64
        else:
            changed["state"]["order_id"] = "existing-order"
        with pytest.raises(WorkbookCareError):
            grant(store, changed, body(changed), settings)
    with pytest.raises(WorkbookCareError):
        grant(store, job, {**body(job), "acknowledge_no_payment": False}, settings)
    with pytest.raises(WorkbookCareError):
        grant(store, job, {**body(job), "revision": -1}, settings)


def test_hosted_comparison_has_separate_right_and_all_rows(tmp_path):
    store, job, _ = compare_prepared(tmp_path)
    settings = hosted()
    with pytest.raises(WorkbookCareError):
        grant(store, job, {**body(job), "acknowledge_limitations": False}, settings)
    job = grant(store, job, body(job), settings)
    assert comparison_entitled(job, settings) and not entitled(job, "hosted_beta", True)
    ready = execute_comparison(store, job, {"acknowledge_limitations": True}, settings)
    assert ready["state"]["status"] == "READY"
    assert ready["state"]["payment"] == "NOT_PURCHASED"
    assert not comparison_entitled(
        job, settings.model_copy(update={"hosted_synthetic_delivery_enabled": False})
    )
    changed = copy.deepcopy(job)
    changed["state"]["comparison_grant"]["owner"] = "other"
    assert not comparison_entitled(changed, settings)
