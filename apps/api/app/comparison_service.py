"""Owner/spec-bound comparison jobs and independent private report entitlement."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import time
import uuid
from pathlib import Path

from .comparison_artifacts import REQUIRED
from .comparison_engine import engine_fingerprint
from .comparison_process import run_comparison
from .delivery_artifact_process import make_comparison_artifacts, validate_package
from .delivery_execution import ACTIVE, CONTROLS, CONTROLS_LOCK
from .delivery_execution_control import ExecutionControl, execution_scope
from .delivery_inputs import MAX_BYTES, digest, reject
from .delivery_operations import claim_attempt
from .errors import WorkbookCareError

PRODUCT = "TWO_FILE_COMPARISON"


def comparison_entitled(job, settings):
    if job["product"] != PRODUCT:
        return False
    if job["state"].get("order_id"):
        from .delivery_rights import payment_grant

        return bool(payment_grant(job, settings.app_env))
    grant = job["state"].get("comparison_grant") or {}
    registry = json.loads(
        Path(__file__).with_name("comparison_synthetic_sources.json").read_text(encoding="utf-8")
    )
    known = {digest([p["A"], p["B"]]) for p in registry["pairs"]}
    if job["snapshot"].get("source_pair_hash") not in known:
        return False
    return (
        (
            (
                settings.app_env == "internal_beta"
                and grant.get("kind") == "INTERNAL_SYNTHETIC_COMPARISON"
            )
            or (
                settings.app_env == "hosted_beta"
                and settings.hosted_synthetic_delivery_enabled
                and grant.get("kind") == "HOSTED_SYNTHETIC_COMPARISON"
                and grant.get("owner") == job["owner"]
            )
        )
        and job["product"] == PRODUCT
        and grant.get("job_id") == job["id"]
        and grant.get("source_pair_hash") == job["snapshot"].get("source_pair_hash")
        and grant.get("spec_hash") == job["state"].get("spec_hash")
        and grant.get("expires_at", 0) > time.time()
    )


def require_right(job, settings):
    if not comparison_entitled(job, settings):
        reject(
            "COMPARISON_ENTITLEMENT_REQUIRED",
            "비교 보고서 전용 사용권이 필요합니다. 수정 사용권과 공유하지 않습니다.",
            403,
        )


def project_comparison(job, settings):
    from .delivery_hosted_rehearsal import available

    state = job["state"]
    authorized = comparison_entitled(job, settings)
    return {
        "job_id": job["id"],
        "synthetic_rehearsal_available": available(job, settings),
        "product_id": PRODUCT,
        "revision": job["revision"],
        "expires_at": job["expires"],
        "status": state["status"],
        "sources": job["snapshot"]["previews"],
        "source_pair_hash": job["snapshot"]["source_pair_hash"],
        "source_unchanged": True,
        "purchase_enabled": False,
        "payment_status": state["payment"],
        "preflight": state.get("comparison_preflight"),
        "spec_hash": state.get("spec_hash"),
        "comparison_spec": state.get("comparison_spec"),
        "internal_rehearsal": authorized and not state.get("order_id"),
        "entitlement_active": authorized,
        "order_id": state.get("order_id"),
        "result": state.get("comparison_result") if authorized else None,
        "delivery": state.get("delivery") if authorized else None,
        "includes_repaired_workbook": False,
        "failure_code": state.get("failure_code"),
        "storage_mode": "BETA_EPHEMERAL_LOCAL_ADAPTER",
    }


def create_comparison(store, owner, body, settings):
    if body.get("consent") is not True:
        reject("INPUT_CONSENT_REQUIRED", "두 합성 파일의 업로드 권한과 임시 보관에 동의하세요.")
    key = body.get("request_key", "")
    if not isinstance(key, str) or not re.fullmatch("[a-zA-Z0-9-]{16,80}", key):
        reject("INVALID_REQUEST_KEY", "새 비교 요청으로 시작하세요.")
    inputs = body.get("sources")
    if not isinstance(inputs, dict) or set(inputs) != {"A", "B"}:
        reject("COMPARISON_TWO_SOURCES_REQUIRED", "A와 B 파일을 각각 선택하세요.")
    raw = {}
    message = {}
    for side, item in inputs.items():
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("filename"), str)
            or not isinstance(item.get("file_base64"), str)
        ):
            reject("INVALID_FILE", "두 자료의 형식을 확인하세요.")
        try:
            raw[side] = base64.b64decode(item["file_base64"], validate=True)
        except (ValueError, TypeError):
            reject("INVALID_FILE", "파일 전송 내용을 확인할 수 없습니다.")
        if not raw[side] or len(raw[side]) > MAX_BYTES:
            reject("COMPARISON_INPUT_LIMIT", "비교 베타는 파일당 2MiB 이하입니다.", 413)
        suffix = Path(item["filename"]).suffix.lower()
        if suffix not in {".csv", ".xlsx"}:
            reject("COMPARISON_FORMAT_UNSUPPORTED", "XLSX 또는 UTF-8 CSV만 지원합니다.", 415)
        message[side] = {"filename": "source" + suffix, "file_base64": item["file_base64"]}
    previews = run_comparison({"action": "preview", "sources": message})["sources"]
    snapshot = {
        "source_hash": previews["A"]["source_hash"],
        "source_pair_hash": digest([previews[s]["source_hash"] for s in ["A", "B"]]),
        "previews": previews,
        "formats": {s: message[s]["filename"] for s in ["A", "B"]},
    }
    store.cleanup()
    return store.create(
        owner,
        raw["A"],
        snapshot,
        key,
        product=PRODUCT,
        secondary=(raw["B"], {"source_hash": previews["B"]["source_hash"]}),
    )


def process_message(store, job, spec):
    secondary = store.load_secondary(job)
    return {
        "action": "compare",
        "sources": {
            side: {
                "filename": job["snapshot"]["formats"][side],
                "file_base64": base64.b64encode(data).decode(),
            }
            for side, data in [("A", job["source"]), ("B", secondary)]
        },
        "spec": spec,
    }


def prepare_comparison(store, job, body, settings):
    if job["product"] != PRODUCT:
        reject("COMPARISON_JOB_REQUIRED", "두 파일 비교 작업이 아닙니다.", 409)
    if job["state"]["status"] in ACTIVE | {"READY"} or comparison_entitled(job, settings):
        reject(
            "COMPARISON_SPEC_FIXED",
            "실행 또는 사용권이 연결된 비교 기준입니다. 새 기준은 새 작업으로 시작하세요.",
            409,
        )
    if (
        body.get("source_pair_hash") != job["snapshot"]["source_pair_hash"]
        or type(body.get("revision")) is not int
        or body["revision"] != job["revision"]
    ):
        reject("STALE_JOB", "두 원본과 최신 작업 상태를 다시 확인하세요.", 409)
    spec = body.get("spec")
    if not isinstance(spec, dict) or len(json.dumps(spec)) > 100_000:
        reject("COMPARISON_SPEC_INVALID", "비교 기준과 제외 범위를 확인하세요.")
    claim_attempt(store, job, "COMPARISON_PLAN")
    result = run_comparison(process_message(store, job, spec))
    raw_issues = []
    duplicates = []
    for side, data in result["sources"].items():
        for row in data["rows"]:
            if row["errors"]:
                raw_issues.append(
                    {
                        "source": side,
                        "sheet": row["sheet"],
                        "row": row["physical_row"],
                        "reason_codes": row["errors"],
                    }
                )
        groups = {}
        for row in data["rows"]:
            if row["canonical_key"] is not None:
                groups.setdefault(tuple(row["canonical_key"]), []).append(row)
        for rows in groups.values():
            if len(rows) > 1:
                duplicates.append(
                    {
                        "source": side,
                        "sheet": rows[0]["sheet"],
                        "rows": [r["physical_row"] for r in rows],
                    }
                )
    preflight = {
        "eligibility": result["eligibility"],
        "input_rows": result["summary"]["input_rows"],
        "assigned_rows": result["summary"]["assigned_rows"],
        "excluded_rows": result["summary"]["excluded_rows"],
        "input_issues": raw_issues,
        "duplicate_locations": duplicates,
        "comparable_pair_count": result["summary"]["counts"]["MATCHED"]
        + result["summary"]["counts"]["AMOUNT_DIFF"],
        "purchase_enabled": False,
        "limits_confirmed_required": result["eligibility"] == "ELIGIBLE_WITH_LIMITATIONS",
    }
    return store.update(
        job,
        job["revision"],
        {
            **job["state"],
            "status": "COMPARISON_PREFLIGHT",
            "comparison_spec": spec,
            "spec_hash": result["spec_hash"],
            "comparison_result": result,
            "comparison_result_hash": digest(result),
            "comparison_preflight": preflight,
            "comparison_grant": None,
            "delivery": None,
        },
    )


def validate_spec(job):
    state = job["state"]
    model = state.get("comparison_result")
    if (
        not model
        or model["engine_fingerprint"] != engine_fingerprint()
        or digest(model) != state.get("comparison_result_hash")
        or model["spec_hash"] != state.get("spec_hash")
    ):
        reject("COMPARISON_STALE_SPEC", "원본·기준·엔진이 변경되어 새 비교 확인이 필요합니다.", 409)
    if model["eligibility"] == "NOT_ELIGIBLE":
        reject(
            "COMPARISON_NOT_ELIGIBLE",
            "비교 가능한 공통 1:1 키가 없거나 지원 조건을 충족하지 않습니다.",
            409,
        )
    return model


def execute_comparison(store, job, body, settings):
    require_right(job, settings)
    model = validate_spec(job)
    if job["state"]["status"] == "READY":
        return store.load(job["owner"], job["id"])
    if job["state"]["status"] in ACTIVE:
        return job
    if job["state"]["status"] not in {"COMPARISON_PREFLIGHT", "QUARANTINED"}:
        reject(
            "COMPARISON_EXECUTION_UNAVAILABLE",
            "현재 상태에서는 비교 보고서를 실행할 수 없습니다.",
            409,
        )
    if (
        model["eligibility"] == "ELIGIBLE_WITH_LIMITATIONS"
        and body.get("acknowledge_limitations") is not True
    ):
        reject("COMPARISON_LIMITATIONS_REQUIRED", "중복·자료오류는 보류된다는 제한을 확인하세요.")
    claim_attempt(store, job, "EXECUTION")
    control = ExecutionControl()
    key = (str(store.path), job["id"])
    with CONTROLS_LOCK:
        if key in CONTROLS:
            return store.load(job["owner"], job["id"])
        CONTROLS[key] = control
    attempt = str(uuid.uuid4())
    fence = str(uuid.uuid4())
    try:
        job = store.update(
            job,
            job["revision"],
            {
                **job["state"],
                "status": "RUNNING",
                "attempt": attempt,
                "publication_fence": fence,
                "lease_expires_at": time.time() + 90,
                "delivery": None,
            },
        )
        with execution_scope(control):
            actual = run_comparison(process_message(store, job, job["state"]["comparison_spec"]))
            if digest(actual) != job["state"]["comparison_result_hash"]:
                reject("COMPARISON_RECHECK_FAILED", "실행 결과가 고정된 비교 기준과 다릅니다.", 422)
            control.check()
            package = make_comparison_artifacts(actual, job)
            validate_package(package, REQUIRED)
            control.check()
            current = store.load(job["owner"], job["id"])
            require_right(current, settings)
            validate_spec(current)
            if (
                current["state"]["status"] != "RUNNING"
                or current["state"].get("publication_fence") != fence
            ):
                reject("PUBLICATION_REVOKED", "취소된 비교 결과는 게시하지 않습니다.", 409)
            receipt = {
                "delivery_id": str(uuid.uuid4()),
                "product_id": PRODUCT,
                "files": package["manifest"]["files"],
                "expires_at": job["expires"],
                "spec_hash": actual["spec_hash"],
                "includes_repaired_workbook": False,
            }
            state = {
                **current["state"],
                "status": "READY",
                "delivery": receipt,
                "failure_code": None,
            }
            with store.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                if (current["state"].get("payment_grant") or current["state"]["comparison_grant"])[
                    "expires_at"
                ] <= time.time():
                    reject("PUBLICATION_REVOKED", "보고서 권리가 만료되어 게시하지 않습니다.", 409)
                changed = db.execute(
                    "UPDATE jobs SET state=?,revision=revision+1 WHERE id=? AND owner=? "
                    "AND revision=? AND expires>?",
                    (json.dumps(state), job["id"], job["owner"], current["revision"], time.time()),
                ).rowcount
                if changed != 1:
                    reject(
                        "PUBLICATION_REVOKED",
                        "작업 상태가 변경되어 보고서를 게시하지 않았습니다.",
                        409,
                    )
                db.execute("DELETE FROM delivery_artifacts WHERE job_id=?", (job["id"],))
                for kind, artifact in package["artifacts"].items():
                    db.execute(
                        "INSERT INTO delivery_artifacts VALUES (?,?,?,?,?)",
                        (
                            job["id"],
                            kind,
                            receipt["delivery_id"],
                            artifact["data"],
                            json.dumps(package["manifest"]),
                        ),
                    )
        return store.load(job["owner"], job["id"])
    except Exception as error:
        code = error.code if isinstance(error, WorkbookCareError) else "COMPARISON_REPORT_FAILED"
        try:
            current = store.load(job["owner"], job["id"])
            if current["state"].get("attempt") == attempt and current["state"]["status"] != "READY":
                store.update(
                    current,
                    current["revision"],
                    {
                        **current["state"],
                        "status": "CANCELLED"
                        if current["state"]["status"] == "CANCEL_REQUESTED"
                        or control.cancelled.is_set()
                        else "QUARANTINED",
                        "delivery": None,
                        "failure_code": code,
                    },
                )
        except WorkbookCareError:
            pass
        reject(
            code,
            "전체 보고서를 준비하지 못해 다운로드를 차단했습니다. 최신 상태를 확인하세요.",
            422,
        )
    finally:
        control.finished.set()
        with CONTROLS_LOCK:
            CONTROLS.pop(key, None)


def download_comparison(store, job, kind, settings):
    require_right(job, settings)
    if job["state"]["status"] != "READY" or kind not in REQUIRED:
        reject("COMPARISON_REPORT_NOT_READY", "완성된 비교 보고서만 받을 수 있습니다.", 409)
    delivery = job["state"]["delivery"]
    with store.connection() as db:
        rows = db.execute(
            "SELECT * FROM delivery_artifacts WHERE job_id=? AND delivery_id=?",
            (job["id"], delivery["delivery_id"]),
        ).fetchall()
    if {r["kind"] for r in rows} != REQUIRED:
        reject("COMPARISON_REPORT_INCOMPLETE", "필수 보고서가 없어 다운로드를 차단했습니다.", 409)
    row = next(r for r in rows if r["kind"] == kind)
    manifest = json.loads(row["manifest"])
    info = manifest["files"][kind]
    if (
        manifest["product_id"] != PRODUCT
        or manifest["spec_hash"] != job["state"]["spec_hash"]
        or hashlib.sha256(row["data"]).hexdigest() != info["sha256"]
    ):
        reject("COMPARISON_REPORT_INVALID", "보고서의 무결성·비교 기준이 다릅니다.", 409)
    latest = store.load(job["owner"], job["id"])
    require_right(latest, settings)
    if latest["revision"] != job["revision"]:
        reject("STALE_JOB", "작업 상태가 변경되었습니다.", 409)
    return {
        "filename": info["name"],
        "mime": info["mime"],
        "sha256": info["sha256"],
        "file_base64": base64.b64encode(row["data"]).decode(),
    }


def grant_comparison(store, job, settings):
    if settings.app_env != "internal_beta" or job["product"] != PRODUCT:
        reject("LOCAL_REHEARSAL_ONLY", "내부 합성 비교만 허용합니다.")
    if job["state"].get("order_id"):
        reject("ORDER_ALREADY_LINKED", "주문과 내부 검증권을 공유하지 않습니다.", 409)
    validate_spec(job)
    grant = {
        "kind": "INTERNAL_SYNTHETIC_COMPARISON",
        "job_id": job["id"],
        "source_pair_hash": job["snapshot"]["source_pair_hash"],
        "spec_hash": job["state"]["spec_hash"],
        "expires_at": job["expires"],
    }
    candidate = {**job, "state": {**job["state"], "comparison_grant": grant}}
    if not comparison_entitled(candidate, settings):
        reject("SYNTHETIC_FIXTURE_REQUIRED", "고정된 두 합성 원본과 비교 기준만 허용합니다.")
    return store.update(job, job["revision"], candidate["state"])
