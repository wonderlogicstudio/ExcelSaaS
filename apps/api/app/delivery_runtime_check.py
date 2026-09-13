"""Container startup checks using only fixed synthetic inputs; logs contain no input data."""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path


def verify(directory: Path):
    from .config import Settings
    from .delivery_calculation import calculate
    from .delivery_execution import approve, compatibility_status, execute
    from .delivery_inputs import PROFILE_1, PROFILE_2, inspect_input
    from .delivery_plan import build_plan, reference_status
    from .delivery_store import DeliveryStore

    assert reference_status()["status"] == "PASS"
    assert compatibility_status()["status"] == "PASS"
    oracle = json.loads((directory / "reference-cases.json").read_text(encoding="utf-8"))
    for case in oracle["cases"]:
        cells = {
            a: {
                "type": "text"
                if isinstance(v, str)
                else "boolean"
                if isinstance(v, bool)
                else "number",
                "value": v,
                "style": "0",
            }
            for a, v in case["values"].items()
        }
        cells.update(
            {a: {"type": "formula", "value": v, "style": "0"} for a, v in case["formulas"].items()}
        )
        actual = calculate({"검증": cells})["values"]["검증"]
        for cell, expected in case["expected"].items():
            assert actual[cell]["type"] == expected["type"]
            if expected["type"] == "number":
                assert math.isclose(
                    actual[cell]["value"], expected["value"], rel_tol=1e-12, abs_tol=1e-12
                )
            else:
                assert actual[cell]["value"] == expected["value"]
    source = (directory / "delivery-rp01-rp02.xlsx").read_bytes()
    settings = Settings(app_env="internal_beta")
    with tempfile.TemporaryDirectory(prefix="workbookcare-runtime-proof-") as folder:
        store = DeliveryStore(Path(folder))
        for profile, targets in [(PROFILE_1, ["B2", "B3"]), (PROFILE_2, ["F3"])]:
            job = store.create(
                "synthetic-runtime",
                source,
                inspect_input("synthetic.xlsx", source, settings),
                profile,
            )
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
                    "plan_digest": plan["digest"],
                    "candidate_ids": [p["candidate_id"] for p in plan["patches"]],
                    "acknowledge_exact_changes": True,
                },
                settings,
            )
            assert execute(store, job, settings)["state"]["status"] == "READY"
    return {
        "event": "delivery_runtime_verified",
        "reference_cases": len(oracle["cases"]),
        "repair_profiles": 2,
        "artifacts": 6,
        "payment_tested": False,
    }
