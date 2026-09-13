"""Explicit non-payment rehearsal for registered synthetic files behind hosted HMAC."""

from __future__ import annotations

import json
from pathlib import Path

from .delivery_inputs import digest, reject
from .delivery_rehearsal import SYNTHETIC_SOURCE_HASHES


def available(job, settings):
    if (
        settings.app_env != "hosted_beta"
        or not settings.delivery_beta_enabled
        or not settings.hosted_synthetic_delivery_enabled
        or not settings.control_plane_hmac_is_required
        or settings.payment_mode != "OFF"
        or job["state"].get("order_id")
        or job["state"]["status"] in {"RUNNING", "READY", "CANCELLED", "CANCEL_REQUESTED"}
    ):
        return False
    if job["product"] == "APPROVED_REPAIR":
        return job["snapshot"]["source_hash"] in SYNTHETIC_SOURCE_HASHES and bool(
            job["state"].get("plan")
        )
    if job["product"] == "TWO_FILE_COMPARISON":
        registry = json.loads(
            Path(__file__)
            .with_name("comparison_synthetic_sources.json")
            .read_text(encoding="utf-8")
        )
        return job["snapshot"].get("source_pair_hash") in {
            digest([p["A"], p["B"]]) for p in registry["pairs"]
        } and bool(job["state"].get("spec_hash"))
    return False


def grant(store, job, body, settings):
    if not available(job, settings):
        reject(
            "SYNTHETIC_REHEARSAL_UNAVAILABLE",
            "등록된 합성 파일의 베타 납품 시험만 허용합니다.",
            403,
        )
    if body.get("acknowledge_no_payment") is not True:
        reject("REHEARSAL_NOTICE_REQUIRED", "결제가 아닌 합성 파일 시험임을 확인하세요.")
    if body.get("revision") != job["revision"]:
        reject("STALE_JOB", "현재 작업 상태를 다시 확인하세요.", 409)
    state = job["state"]
    if state.get("approval"):
        reject("ALREADY_APPROVED", "현재 변경 승인을 새 시험권으로 대체하지 않습니다.", 409)
    common = {"owner": job["owner"], "job_id": job["id"], "expires_at": job["expires"]}
    if job["product"] == "APPROVED_REPAIR":
        from .delivery_execution import compatibility_status
        from .delivery_plan import reference_status, validate_plan

        plan = validate_plan(job)
        if reference_status()["status"] != "PASS" or compatibility_status()["status"] != "PASS":
            reject("REFERENCE_NOT_VERIFIED", "계산과 Excel 파일 검증이 필요합니다.", 409)
        common.update(
            kind="HOSTED_SYNTHETIC",
            source_hash=job["snapshot"]["source_hash"],
            plan_digest=plan["digest"],
            expires_at=min(job["expires"], plan["expires_at"]),
        )
        key = "internal_grant"
    else:
        from .comparison_service import validate_spec

        validate_spec(job)
        preflight = state["comparison_preflight"]
        if preflight["eligibility"] == "NOT_ELIGIBLE":
            reject("COMPARISON_NOT_ELIGIBLE", "지원되는 비교 범위를 먼저 확인하세요.", 409)
        if (
            preflight["limits_confirmed_required"]
            and body.get("acknowledge_limitations") is not True
        ):
            reject("COMPARISON_LIMITATIONS_REQUIRED", "중복·자료오류 보류 범위를 확인하세요.", 409)
        common.update(
            kind="HOSTED_SYNTHETIC_COMPARISON",
            source_pair_hash=job["snapshot"]["source_pair_hash"],
            spec_hash=state["spec_hash"],
        )
        key = "comparison_grant"
    # No order, payment state, customer approval or artifact is created here.
    return store.update(job, job["revision"], {**state, key: common})
