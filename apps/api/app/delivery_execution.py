"""Exact approval, fenced execution and an atomic, private three-artifact delivery."""

from __future__ import annotations

import base64
import hashlib
import json
import tempfile
import threading
import time
import uuid
from pathlib import Path

from .delivery_artifact_process import make_repair_artifacts as make_artifacts
from .delivery_artifact_process import validate_package
from .delivery_execution_control import ExecutionControl, execution_scope
from .delivery_inputs import digest, reject
from .delivery_patch import patch_workbook, verify_output
from .delivery_plan import REQUIRED_ARTIFACTS, reference_status, validate_plan
from .delivery_rehearsal import entitled
from .delivery_rights import effective_repair_grant
from .errors import WorkbookCareError

CONTROLS: dict[tuple[str, str], ExecutionControl] = {}
CONTROLS_LOCK = threading.Lock()
ACTIVE = {"RUNNING", "CANCEL_REQUESTED"}


def patch_fingerprint():
    root = Path(__file__).parent
    return digest(
        {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in [
                "delivery_patch.py",
                "delivery_artifacts.py",
                "delivery_inputs.py",
                "delivery_plan.py",
                "delivery_package.py",
                "delivery_verification_template.html",
                "repair_rules/__init__.py",
                "repair_rules/formula_restore.py",
                "repair_rules/numeric_text.py",
            ]
        }
    )


def compatibility_status():
    path = Path(__file__).with_name("delivery_patch_reference.json")
    if not path.is_file():
        return {"status": "NOT_RUN"}
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if evidence.get("patch_fingerprint") != patch_fingerprint():
        return {"status": "STALE"}
    return {
        "status": evidence["status"],
        "excel_version": evidence["excel_version"],
        "profiles": evidence["profiles"],
        "evidence_digest": digest(evidence),
    }


def require_right(job, settings):
    if job["product"] != "APPROVED_REPAIR" or not entitled(
        job, settings.app_env, settings.hosted_synthetic_delivery_enabled
    ):
        reject("ENTITLEMENT_REQUIRED", "유효한 수정 패키지 권리가 필요합니다.", 403)


def approve(store, job, body, settings):
    require_right(job, settings)
    plan = validate_plan(job)
    if job["state"]["status"] in ACTIVE | {"READY", "CANCELLED"}:
        reject("APPROVAL_NOT_AVAILABLE", "현재 작업 상태에서는 새 승인을 받을 수 없습니다.", 409)
    ids = body.get("candidate_ids")
    if (
        body.get("acknowledge_exact_changes") is not True
        or body.get("plan_digest") != plan["digest"]
        or not isinstance(ids, list)
        or any(not isinstance(value, str) for value in ids)
        or sorted(ids) != sorted(p["candidate_id"] for p in plan["patches"])
    ):
        reject(
            "EXACT_APPROVAL_REQUIRED",
            "현재 계획의 정확한 셀 변경과 계산 영향을 별도로 승인하세요.",
            409,
        )
    if reference_status()["status"] != "PASS" or compatibility_status()["status"] != "PASS":
        reject("REFERENCE_NOT_VERIFIED", "계산 또는 파일 호환성 검증이 완료되지 않았습니다.", 409)
    approval = {
        "owner": job["owner"],
        "job_id": job["id"],
        "product_id": job["product"],
        "sku": plan["sku"],
        "source_hash": plan["source_hash"],
        "plan_digest": plan["digest"],
        "candidate_ids": sorted(ids),
        "entitlement_digest": digest(effective_repair_grant(job, settings.app_env)),
        "created_at": time.time(),
        "expires_at": min(
            plan["expires_at"], effective_repair_grant(job, settings.app_env)["expires_at"]
        ),
    }
    from .delivery_receipts import sign

    approval["receipt"] = sign(store, approval)
    return store.update(
        job, body.get("revision"), {**job["state"], "approval": approval, "status": "APPROVED"}
    )


def validate_approval(job, settings, store):
    require_right(job, settings)
    plan = validate_plan(job)
    approval = job["state"].get("approval") or {}
    from .delivery_receipts import valid

    if approval and not valid(store, approval):
        reject("APPROVAL_RECEIPT_INVALID", "현재 승인 기록의 서명을 확인하지 못했습니다.", 409)
    expected = {
        "owner": job["owner"],
        "job_id": job["id"],
        "product_id": job["product"],
        "sku": plan["sku"],
        "source_hash": plan["source_hash"],
        "plan_digest": plan["digest"],
        "candidate_ids": sorted(p["candidate_id"] for p in plan["patches"]),
        "entitlement_digest": digest(effective_repair_grant(job, settings.app_env)),
    }
    if approval.get("expires_at", 0) <= time.time() or any(
        approval.get(k) != v for k, v in expected.items()
    ):
        reject(
            "CURRENT_APPROVAL_REQUIRED",
            "결제나 기준 확인만으로 실행하지 않습니다. 현재 변경계획을 승인하세요.",
            409,
        )
    if reference_status()["status"] != "PASS" or compatibility_status()["status"] != "PASS":
        reject("REFERENCE_NOT_VERIFIED", "필수 엔진·파일 호환성 검증이 유효하지 않습니다.", 409)
    return plan


def receipt(job):
    return job["state"].get("delivery")


def execute(store, job, settings):
    require_right(job, settings)
    if job["state"]["status"] == "READY":
        return store.load(job["owner"], job["id"])
    if job["state"]["status"] in ACTIVE:
        return job
    plan = validate_approval(job, settings, store)
    if job["state"]["status"] not in {"APPROVED", "QUARANTINED"}:
        reject("EXECUTION_NOT_AVAILABLE", "새 변경계획 승인이 필요합니다.", 409)
    from .delivery_operations import claim_attempt

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
                "lease_expires_at": time.time() + 120,
                "delivery": None,
                "failure_code": None,
            },
        )
        with (
            execution_scope(control),
            tempfile.TemporaryDirectory(prefix="workbookcare-patch-") as folder,
        ):
            scratch = Path(folder)
            scratch.chmod(0o700)
            control.check()
            repaired = patch_workbook(job["source"], job["snapshot"], plan)
            control.check()
            verification = verify_output(job["source"], repaired, plan, settings)
            verification["checks"].append(
                {
                    "code": "EXCEL_FIXTURE_COMPATIBILITY",
                    "status": "PASS",
                    "evidence": compatibility_status(),
                }
            )
            control.check()
            package = make_artifacts(job, plan, repaired, verification)
            for k, v in package["artifacts"].items():
                (scratch / k).write_bytes(v["data"])
            control.check()
            validate_package(package, REQUIRED_ARTIFACTS)
            current = store.load(job["owner"], job["id"])
            validate_approval(current, settings, store)
            if (
                current["state"].get("publication_fence") != fence
                or current["state"]["status"] != "RUNNING"
            ):
                reject("PUBLICATION_REVOKED", "취소된 실행 결과는 게시하지 않습니다.", 409)
            publication = {
                "delivery_id": str(uuid.uuid4()),
                "plan_digest": plan["digest"],
                "patch_count": len(plan["patches"]),
                "expires_at": job["expires"],
                "files": package["manifest"]["files"],
            }
            state = {
                **current["state"],
                "status": "READY",
                "delivery": publication,
                "approval": current["state"]["approval"],
            }
            # SQLite commit is the publication boundary: all required blobs and READY together.
            with store.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                if (
                    min(
                        current["state"]["approval"]["expires_at"],
                        effective_repair_grant(current, settings.app_env)["expires_at"],
                    )
                    <= time.time()
                ):
                    reject("PUBLICATION_REVOKED", "게시 직전 권리가 만료되었습니다.", 409)
                changed = db.execute(
                    "UPDATE jobs SET state=?,revision=revision+1 WHERE id=? AND owner=? "
                    "AND revision=? AND expires>?",
                    (json.dumps(state), job["id"], job["owner"], current["revision"], time.time()),
                ).rowcount
                if changed != 1:
                    reject(
                        "PUBLICATION_REVOKED",
                        "실행 중 권리나 상태가 변경되어 게시하지 않았습니다.",
                        409,
                    )
                db.execute("DELETE FROM delivery_artifacts WHERE job_id=?", (job["id"],))
                for kind, artifact in package["artifacts"].items():
                    db.execute(
                        "INSERT INTO delivery_artifacts VALUES (?,?,?,?,?)",
                        (
                            job["id"],
                            kind,
                            publication["delivery_id"],
                            artifact["data"],
                            json.dumps(package["manifest"]),
                        ),
                    )
        return store.load(job["owner"], job["id"])
    except Exception as error:
        code = error.code if isinstance(error, WorkbookCareError) else "DELIVERY_VALIDATION_FAILED"
        try:
            current = store.load(job["owner"], job["id"])
            if current["state"].get("attempt") == attempt and current["state"]["status"] != "READY":
                cancelled = (
                    current["state"]["status"] == "CANCEL_REQUESTED" or control.cancelled.is_set()
                )
                store.update(
                    current,
                    current["revision"],
                    {
                        **current["state"],
                        "status": "CANCELLED" if cancelled else "QUARANTINED",
                        "delivery": None,
                        "failure_code": code,
                    },
                )
        except WorkbookCareError:
            pass
        # Raw library errors can contain workbook contents. Return only a stable code/message.
        reject(
            code,
            "실행 결과를 제공하지 않았습니다. 최신 상태에서 재시도 또는 취소를 확인하세요.",
            422,
        )
    finally:
        control.finished.set()
        with CONTROLS_LOCK:
            CONTROLS.pop(key, None)


def cancel(store, job):
    if job["state"]["status"] == "CANCELLED":
        return job
    if job["state"]["status"] == "READY":
        reject("DELIVERY_ALREADY_READY", "납품된 파일 삭제는 작업 삭제를 이용하세요.", 409)
    running = job["state"]["status"] in ACTIVE
    updated = store.update(
        job,
        job["revision"],
        {
            **job["state"],
            "status": "CANCEL_REQUESTED" if running else "CANCELLED",
            "publication_fence": str(uuid.uuid4()),
            "approval": None,
            "delivery": None,
        },
    )
    with CONTROLS_LOCK:
        control = CONTROLS.get((str(store.path), job["id"]))
    if control:
        control.cancel()
    return updated


def download(store, job, kind, settings):
    require_right(job, settings)
    if job["state"]["status"] != "READY" or not receipt(job) or kind not in REQUIRED_ARTIFACTS:
        reject("DELIVERY_NOT_READY", "완료된 검증 파일만 받을 수 있습니다.", 409)
    with store.connection() as db:
        available = {
            r["kind"]
            for r in db.execute(
                "SELECT kind FROM delivery_artifacts WHERE job_id=? AND delivery_id=?",
                (job["id"], receipt(job)["delivery_id"]),
            )
        }
        if available != set(REQUIRED_ARTIFACTS):
            reject("INCOMPLETE_PACKAGE", "세 파일 중 일부가 없어 다운로드를 차단했습니다.", 409)
        row = db.execute(
            "SELECT * FROM delivery_artifacts WHERE job_id=? AND kind=? AND delivery_id=?",
            (job["id"], kind, receipt(job)["delivery_id"]),
        ).fetchone()
    if not row:
        reject("INCOMPLETE_PACKAGE", "필수 파일을 찾지 못해 다운로드를 차단했습니다.", 409)
    manifest = json.loads(row["manifest"])
    info = manifest["files"][kind]
    if (
        manifest["source_hash"] != job["snapshot"]["source_hash"]
        or manifest["plan_digest"] != job["state"]["plan"]["digest"]
        or hashlib.sha256(row["data"]).hexdigest() != info["sha256"]
    ):
        reject("ARTIFACT_INTEGRITY_FAILED", "파일 무결성이 달라 다운로드를 차단했습니다.", 409)
    # Recheck ownership, rights, TTL and state after reading the private blob.
    current = store.load(job["owner"], job["id"])
    require_right(current, settings)
    if current["revision"] != job["revision"] or current["state"]["status"] != "READY":
        reject("STALE_JOB", "작업 상태가 변경되었습니다.", 409)
    return {
        "filename": info["name"],
        "mime": info["mime"],
        "sha256": info["sha256"],
        "file_base64": base64.b64encode(row["data"]).decode(),
    }
