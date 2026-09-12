"""Create and validate reports in the same bounded, cancellable IPC boundary."""

from __future__ import annotations

import base64
import hashlib

from .comparison_process import run_comparison
from .delivery_inputs import reject


def validate_package(package, required):
    artifacts = package.get("artifacts", {})
    files = package.get("manifest", {}).get("files", {})
    if set(artifacts) != set(required) or set(files) != set(required):
        reject("INCOMPLETE_PACKAGE", "필수 산출물이 모두 준비되지 않았습니다.", 422)
    for kind, item in artifacts.items():
        if hashlib.sha256(item["data"]).hexdigest() != files[kind]["sha256"]:
            reject("ARTIFACT_INTEGRITY_FAILED", "산출물 검증 정보가 다릅니다.", 422)


def decode_package(result):
    for artifact in result["artifacts"].values():
        artifact["data"] = base64.b64decode(artifact.pop("data_base64"), validate=True)
    return result


def make_comparison_artifacts(model, job):
    return decode_package(
        run_comparison(
            {
                "action": "comparison_artifacts",
                "model": model,
                "job": {"id": job["id"], "expires": job["expires"]},
            },
            timeout=30,
        )
    )


def make_repair_artifacts(job, plan, repaired, verification):
    return decode_package(
        run_comparison(
            {
                "action": "repair_artifacts",
                "plan": plan,
                "repaired_base64": base64.b64encode(repaired).decode(),
                "verification": verification,
                "job": {"id": job["id"], "product": job["product"], "expires": job["expires"]},
            },
            timeout=30,
        )
    )
