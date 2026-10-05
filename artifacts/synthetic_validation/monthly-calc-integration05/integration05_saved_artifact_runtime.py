from __future__ import annotations

import hashlib
import json
import tempfile
import base64
from pathlib import Path

from app.config import Settings
from app.delivery_execution import approve, compatibility_status, download, execute
from app.delivery_inputs import PROFILE_1, PROFILE_2, inspect_input
from app.delivery_plan import build_plan, plan_digest, reference_status
from app.delivery_store import DeliveryStore

repo = Path(__file__).resolve().parents[3]
out_dir = Path(__file__).with_name("saved-artifacts")
out_dir.mkdir(parents=True, exist_ok=True)
source = (repo / "samples" / "delivery-v3_2" / "delivery-rp01-rp02.xlsx").read_bytes()
source_sha256 = hashlib.sha256(source).hexdigest()
settings = Settings(app_env="internal_beta")
status = {"reference_status": reference_status(), "compatibility_status": compatibility_status()}
assert status["reference_status"].get("status") == "PASS", status
assert status["compatibility_status"].get("status") == "PASS", status

profiles = [
    ("rp01", PROFILE_1, ["B2", "B3"], "H2", 15500),
    ("rp02", PROFILE_2, ["F3"], "F12", 18200),
]
rows = []
with tempfile.TemporaryDirectory(prefix="monthly-calc-integration05-") as folder:
    store = DeliveryStore(Path(folder))
    for label, profile, targets, expected_cell, expected_value in profiles:
        snapshot = inspect_input("delivery-rp01-rp02.xlsx", source, settings)
        job = store.create("synthetic-runtime", source, snapshot, f"integration05-{label}")
        policy = {
            "profile": profile,
            "sheet": "검증",
            "targets": targets,
            "role": "AMOUNT",
            "confirmed": True,
            "anchor": "F2",
            "anchor_formula": "=ROUND(C2*D2*(1-E2),0)",
        }
        plan = build_plan(job, policy)
        typed_expected = plan["expected_calculated_values"]["검증"][expected_cell]
        assert typed_expected["type"] == "number", typed_expected
        assert typed_expected["value"] == expected_value, typed_expected
        job = store.update(
            job,
            job["revision"],
            {
                **job["state"],
                "policy": policy,
                "plan": plan,
                "status": "PREVIEW_VALIDATED",
                "internal_grant": {
                    "kind": "INTERNAL_SYNTHETIC",
                    "job_id": job["id"],
                    "source_hash": job["snapshot"]["source_hash"],
                    "expires_at": job["expires"],
                },
            },
        )
        job = approve(
            store,
            job,
            {
                "revision": job["revision"],
                "plan_digest": plan_digest(plan),
                "candidate_ids": [patch["candidate_id"] for patch in plan["patches"]],
                "acknowledge_exact_changes": True,
            },
            settings,
        )
        result = execute(store, job, settings)
        assert result["state"]["status"] == "READY"
        assert store.load("synthetic-runtime", job["id"])["source"] == source
        artifacts = {}
        for kind, suffix in [
            ("REPAIRED_XLSX", "repaired.xlsx"),
            ("CHANGES_XLSX", "changes.xlsx"),
            ("VERIFICATION_HTML", "verification.html"),
        ]:
            artifact = download(store, result, kind, settings)
            data = base64.b64decode(artifact["file_base64"], validate=True)
            path = out_dir / f"{label}-{suffix}"
            path.write_bytes(data)
            assert hashlib.sha256(data).hexdigest() == artifact["sha256"]
            artifacts[kind] = {
                "path": str(path.relative_to(repo)),
                "filename": artifact["filename"],
                "mime": artifact["mime"],
                "sha256": artifact["sha256"],
                "bytes": len(data),
            }
        rows.append(
            {
                "label": label,
                "profile": profile,
                "targets": targets,
                "expected_cell": expected_cell,
                "typed_expected": typed_expected,
                "patch_count": len(plan["patches"]),
                "delivery_status": result["state"]["status"],
                "source_sha256_preserved": source_sha256,
                "artifacts": artifacts,
            }
        )

evidence = {
    "status": "PASS",
    "kind": "UNMOCKED_RP01_RP02_SAVED_ARTIFACT_RUNTIME_NO_REFERENCE_LOOP",
    "reference_and_compatibility": status,
    "source_sha256": source_sha256,
    "profiles": rows,
    "artifact_count": sum(len(row["artifacts"]) for row in rows),
    "mocked": False,
    "note": "Skips the 20-case reference recalculation loop; uses current unmocked PASS statuses and saves downloaded artifacts before the temporary store is removed.",
}
out_path = Path(__file__).with_name("saved-artifact-runtime-result.json")
out_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))

