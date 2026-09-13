"""Private beta delivery API with separate owner, payment and exact approval gates."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import secrets
import tempfile
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from . import payment_service as payments
from .comparison_service import (
    create_comparison,
    download_comparison,
    execute_comparison,
    prepare_comparison,
    project_comparison,
)
from .config import get_settings
from .delivery_execution import ACTIVE, approve, cancel, compatibility_status, download, execute
from .delivery_inputs import (
    MAX_BYTES,
    MAX_CELLS,
    MAX_FORMULAS,
    MAX_PATCHES,
    PROFILE_1,
    PROFILE_2,
    inspect_input,
    preflight,
    reject,
)
from .delivery_operations import bounded_body, claim_attempt
from .delivery_plan import build_plan, customer_plan, plan_summary
from .delivery_rehearsal import entitled
from .delivery_store import INPUT_TTL_SECONDS, DeliveryStore
from .payment_plan_actions import reselect, restore_order, retry_delivery, validate_paid_scope

router = APIRouter()
_stores: dict[str, DeliveryStore] = {}
OWNER_HEADER = "x-workbookcare-owner"


def get_store() -> DeliveryStore:
    settings = get_settings()
    directory = settings.delivery_data_dir or str(
        Path(tempfile.gettempdir()) / "workbookcare-delivery"
    )
    if directory not in _stores:
        _stores[directory] = DeliveryStore(Path(directory))
    return _stores[directory]


def projection(job: dict) -> dict:
    if job["product"] == "TWO_FILE_COMPARISON":
        return project_comparison(job, get_settings())
    from .delivery_hosted_rehearsal import available

    state = job["state"]
    snapshot = job["snapshot"]
    return {
        "job_id": job["id"],
        "product_id": job["product"],
        "revision": job["revision"],
        "expires_at": job["expires"],
        "source_hash": snapshot["source_hash"],
        "inventory_hash": snapshot["inventory_hash"],
        "sheets": [
            {"name": name, "cell_count": len(cells)} for name, cells in snapshot["cells"].items()
        ],
        "formula_count": snapshot["formula_count"],
        "status": state["status"],
        "preflight": state["preflight"],
        "payment_status": state["payment"],
        "purchase_enabled": False,
        "synthetic_rehearsal_available": available(job, get_settings()),
        "repair_execution_available": entitled(
            job, get_settings().app_env, get_settings().hosted_synthetic_delivery_enabled
        )
        and compatibility_status()["status"] == "PASS",
        "approval_status": "APPROVED" if state.get("approval") else "NOT_APPROVED",
        "approval_receipt": (state.get("approval") or {}).get("receipt"),
        "delivery": state.get("delivery"),
        "failure_code": state.get("failure_code"),
        "storage_mode": "BETA_EPHEMERAL_LOCAL_ADAPTER",
        "source_unchanged": True,
        "plan_summary": plan_summary(state["plan"]) if state.get("plan") else None,
        "internal_rehearsal": entitled(
            job, get_settings().app_env, get_settings().hosted_synthetic_delivery_enabled
        )
        and not state.get("order_id"),
        "entitlement_active": entitled(
            job, get_settings().app_env, get_settings().hosted_synthetic_delivery_enabled
        ),
        "order_id": state.get("order_id"),
        "policy": state.get("policy"),
    }


@router.post("/v1/delivery")
async def delivery(request: Request):
    settings = get_settings()
    if not settings.delivery_beta_enabled or settings.app_env == "production":
        reject("DELIVERY_NOT_AVAILABLE", "이 환경에서는 수정 사전 검사를 제공하지 않습니다.", 404)
    origin = request.headers.get("origin")
    if origin not in settings.cors_origins or request.headers.get("x-workbookcare-csrf") != "1":
        reject("DELIVERY_ORIGIN_REJECTED", "같은 서비스 화면에서 다시 요청하세요.", 403)
    cookie = None
    if settings.control_plane_hmac_is_required:
        owner = request.headers.get(OWNER_HEADER, "")
        if not re.fullmatch("[0-9a-f]{64}", owner) or not request.scope.get(
            "delivery_owner_verified"
        ):
            reject("DELIVERY_OWNER_REQUIRED", "작업 소유권을 확인하지 못했습니다.", 401)
    else:
        token = request.cookies.get("workbookcare_local_session", "")
        if not re.fullmatch("[0-9a-f]{64}", token):
            token = secrets.token_hex(32)
            cookie = token
        owner = hashlib.sha256(token.encode()).hexdigest()
    raw = await bounded_body(request)
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeError):
        reject("INVALID_REQUEST", "요청 형식을 확인하세요.")
    if not isinstance(body, dict) or any(
        k in body
        for k in [
            "owner",
            "owner_id",
            "state",
            "payment",
            "approval",
            "artifacts",
            "internal_grant",
            "comparison_grant",
            "payment_grant",
            "comparison_result",
            "plan",
            "entitlement",
        ]
    ):
        reject("INVALID_REQUEST", "서버가 관리하는 작업 정보를 지정할 수 없습니다.")
    store = get_store()
    store.rate_limit(owner)
    store.cleanup()
    action = body.get("action")
    if action == "capabilities":
        from . import comparison_engine as comparison

        output = {
            "comparison_limits": {
                "max_bytes": comparison.MAX_BYTES,
                "max_rows": comparison.MAX_ROWS,
                "max_columns": comparison.MAX_COLUMNS,
                "max_cells": comparison.MAX_SELECTED_CELLS,
            },
            "profiles": [PROFILE_1, PROFILE_2],
            "max_bytes": MAX_BYTES,
            "max_cells": MAX_CELLS,
            "max_formulas": MAX_FORMULAS,
            "max_targets": MAX_PATCHES,
            "input_ttl_seconds": INPUT_TTL_SECONDS,
            "calculation_status": "NOT_RUN",
            "purchase_enabled": False,
            "durable_commerce_storage": False,
            "order_ttl_seconds": 86400,
            "cleanup_interval_seconds": 30,
            "cleanup_requires_active_instance": settings.app_env == "hosted_beta",
            "max_execution_attempts": 3,
            "support_intake_enabled": False,
            "automation_mode": "MANUAL_NEW_INPUT_ONLY",
            "payment_mode": settings.payment_mode,
            "official_pg_test_configured": bool(
                settings.toss_test_secret and settings.payment_mode == "TOSS_TEST"
            ),
        }
    elif action == "create_input":
        if body.get("consent") is not True:
            reject("INPUT_CONSENT_REQUIRED", "업로드 권한과 합성 파일 사전 검사 동의를 확인하세요.")
        key = body.get("request_key", "")
        if not isinstance(key, str) or not re.fullmatch("[a-zA-Z0-9-]{16,80}", key):
            reject("INVALID_REQUEST_KEY", "새 업로드 요청으로 다시 시작하세요.")
        try:
            payload = base64.b64decode(body.get("file_base64", ""), validate=True)
        except (ValueError, TypeError, binascii.Error):
            reject("INVALID_FILE", "파일 전송 내용을 확인할 수 없습니다.")
        name = body.get("filename", "")
        if not isinstance(name, str):
            reject("INVALID_FILE", "파일 확장자를 확인하세요.")
        snapshot = inspect_input(name, payload, settings)
        store.cleanup()
        output = projection(store.create(owner, payload, snapshot, key))
    elif action == "create_comparison":
        output = projection(
            await run_in_threadpool(create_comparison, store, owner, body, settings)
        )
    elif action == "orders":
        output = {"orders": payments.list_orders(store, owner)}
    elif action in {
        "order_get",
        "payment_confirm",
        "payment_reconcile",
        "order_cancel",
        "payment_event",
    }:
        order_id = body.get("order_id")
        if action == "order_get":
            order = payments.get_order(store, owner, order_id)
        elif action == "order_cancel":
            order = await run_in_threadpool(
                payments.request_cancel, store, owner, order_id, settings
            )
        elif action == "payment_event":
            order = await run_in_threadpool(
                payments.event_hint, store, owner, order_id, body.get("event_id"), settings
            )
        else:
            order = await run_in_threadpool(
                payments.perform,
                store,
                owner,
                order_id,
                "confirm" if action == "payment_confirm" else "query",
                settings,
                payment_key=body.get("payment_key"),
            )
        output = payments.project_order(store, order)
    elif action == "list":
        output = {"jobs": [projection(job) for job in store.list_jobs(owner)]}
    else:
        job_id = body.get("job_id")
        if not isinstance(job_id, str) or len(job_id) > 64:
            reject("INVALID_JOB", "작업을 다시 선택하세요.")
        job = store.load(owner, job_id)
        if job["product"] == "TWO_FILE_COMPARISON" and action in {
            "approve_plan",
            "execute",
            "download",
            "plan_details",
            "prepare_plan",
            "preflight",
        }:
            reject(
                "PRODUCT_ACTION_MISMATCH",
                "비교 보고서 권리로 수정 작업을 실행하거나 받을 수 없습니다.",
                403,
            )
        if action == "synthetic_rehearsal":
            from .delivery_hosted_rehearsal import grant

            output = projection(await run_in_threadpool(grant, store, job, body, settings))
        elif action == "order_create":
            output = payments.project_order(
                store, payments.create_order(store, job, body, settings)
            )
        elif action == "order_restore":
            output = payments.project_order(
                store, restore_order(store, owner, body.get("order_id"), job)
            )
        elif action == "retry_delivery":
            output = projection(await run_in_threadpool(retry_delivery, store, job, settings))
        elif action == "reselect_plan":
            output = projection(await run_in_threadpool(reselect, store, job, body, settings))
        elif action == "prepare_comparison":
            output = projection(
                await run_in_threadpool(prepare_comparison, store, job, body, settings)
            )
        elif action == "execute_comparison":
            output = projection(
                await run_in_threadpool(execute_comparison, store, job, body, settings)
            )
        elif action == "comparison_download":
            output = download_comparison(store, job, body.get("kind"), settings)
        elif action == "get":
            output = projection(job)
        elif action == "delete":
            if job["state"].get("order_id"):
                await run_in_threadpool(
                    payments.request_cancel, store, owner, job["state"]["order_id"], settings
                )
                job = store.load(owner, job_id)
            if job["state"]["status"] in ACTIVE:
                output = projection(cancel(store, job))
                return JSONResponse(output, headers={"Cache-Control": "no-store"})
            store.delete(owner, job_id)
            output = {"status": "DELETED"}
        elif action == "verify_approval_receipt":
            from .delivery_receipts import verify_current

            output = verify_current(store, job)
        elif action == "approve_plan":
            output = projection(approve(store, job, body, settings))
        elif action == "execute":
            output = projection(await run_in_threadpool(execute, store, job, settings))
        elif action == "cancel":
            if job["state"].get("order_id"):
                await run_in_threadpool(
                    payments.request_cancel, store, owner, job["state"]["order_id"], settings
                )
                output = projection(store.load(owner, job_id))
            else:
                output = projection(cancel(store, job))
        elif action == "download":
            output = download(store, job, body.get("kind"), settings)
        elif action == "plan_details":
            output = customer_plan(
                job,
                entitled=entitled(
                    job, settings.app_env, settings.hosted_synthetic_delivery_enabled
                ),
            )
        elif action == "prepare_plan":
            if job["state"]["status"] in ACTIVE | {"READY"}:
                reject("EXECUTION_IN_PROGRESS", "현재 실행을 마치거나 새 작업으로 시작하세요.", 409)
            if body.get("source_hash") != job["snapshot"]["source_hash"]:
                reject("STALE_INPUT", "고정된 원본이 일치하지 않습니다.", 409)
            if type(body.get("revision")) is not int or body["revision"] != job["revision"]:
                reject("STALE_JOB", "최신 작업 상태를 확인하세요.", 409)
            if not job["state"].get("policy"):
                reject("PREFLIGHT_REQUIRED", "업무 기준과 대상의 사전 검사를 먼저 완료하세요.")
            claim_attempt(store, job, "PLAN")
            plan = await run_in_threadpool(build_plan, job, job["state"]["policy"])
            validate_paid_scope(store, job, plan)
            state = {
                **job["state"],
                "status": plan_summary(plan)["status"],
                "plan": plan,
                "approval": None,
                "artifacts": None,
            }
            output = projection(store.update(job, job["revision"], state))
        elif action == "preflight":
            if job["state"]["status"] in ACTIVE | {"READY"}:
                reject("EXECUTION_IN_PROGRESS", "현재 실행을 마치거나 새 작업으로 시작하세요.", 409)
            if body.get("source_hash") != job["snapshot"]["source_hash"]:
                reject("STALE_INPUT", "고정된 원본과 요청한 원본이 다릅니다.", 409)
            if type(body.get("revision")) is not int:
                reject("INVALID_REVISION", "작업 버전을 확인하세요.")
            policy = body.get("policy")
            if not isinstance(policy, dict):
                reject("INVALID_POLICY", "수정 종류와 업무 기준을 입력하세요.")
            if len(json.dumps(policy)) > 20_000:
                reject("LIMIT_EXCEEDED", "선택한 기준이 너무 큽니다.", 413)
            result = preflight(job["snapshot"], policy)
            state = {
                **job["state"],
                "status": result["status"],
                "policy": policy,
                "preflight": result,
                "approval": None,
                "artifacts": None,
                "plan": None,
            }
            output = projection(store.update(job, body["revision"], state))
        else:
            reject("ACTION_NOT_AVAILABLE", "아직 제공하지 않는 작업입니다.", 404)
    response = JSONResponse(output, headers={"Cache-Control": "no-store"})
    if cookie:
        response.set_cookie(
            "workbookcare_local_session", cookie, httponly=True, samesite="strict", max_age=86400
        )
    return response
