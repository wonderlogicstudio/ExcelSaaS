import argparse
import json
import sys
import uuid
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "apps/api"))

from app.config import Settings
from app.delivery_artifacts import make_artifacts
from app.delivery_execution import patch_fingerprint
from app.delivery_inputs import PROFILE_1, PROFILE_2, PROFILE_3, inspect_input
from app.delivery_patch import patch_workbook, verify_output
from app.delivery_plan import build_plan
from app.delivery_store import DeliveryStore


def resolve_artifact_dir(value: str | None, *, stage: str, default_leaf: str) -> Path:
    root = (R / "artifacts").resolve()
    path = (
        R / f"artifacts/verification/{stage}/{default_leaf}"
        if value is None
        else Path(value)
    )
    path = (R / path).resolve() if not path.is_absolute() else path.resolve()
    if path != root and root not in path.parents:
        raise SystemExit("Output directory must stay under the repository artifacts directory")
    return path


def require_empty_output(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise SystemExit(
            "Output directory is not empty; choose a fresh --output-dir. "
            "No files were written."
        )


parser = argparse.ArgumentParser()
parser.add_argument("--stage", choices=["d04", "d08"], default="d04")
parser.add_argument("--output-dir")
args = parser.parse_args()
out = resolve_artifact_dir(args.output_dir, stage=args.stage, default_leaf="compatibility")
require_empty_output(out)
out.mkdir(parents=True, exist_ok=False)
store = DeliveryStore(out / "private-state")
rows = []

legacy_source = (R / "samples/delivery-v3_2/delivery-rp01-rp02.xlsx").read_bytes()
monthly_source = (
    R
    / "artifacts/synthetic_validation/monthly-repair-flow06/stage3/monthly-rp03-supported-6sheet.xlsx"
).read_bytes()
cases = [
    (
        "RP01",
        legacy_source,
        {
            "profile": PROFILE_1,
            "sheet": "검증",
            "targets": ["B2", "B3"],
            "role": "AMOUNT",
            "confirmed": True,
            "anchor": "F2",
            "anchor_formula": "=ROUND(C2*D2*(1-E2),0)",
        },
    ),
    (
        "RP02",
        legacy_source,
        {
            "profile": PROFILE_2,
            "sheet": "검증",
            "targets": ["F3"],
            "role": "AMOUNT",
            "confirmed": True,
            "anchor": "F2",
            "anchor_formula": "=ROUND(C2*D2*(1-E2),0)",
        },
    ),
    (
        "RP03",
        monthly_source,
        {
            "profile": PROFILE_3,
            "sheet": "Budget",
            "targets": ["N18"],
            "before_formula": "=N15-N14",
            "confirmed": True,
        },
    ),
]
for tag, source, policy in cases:
    job = store.create(
        "synthetic-owner",
        source,
        inspect_input("synthetic.xlsx", source, Settings()),
        "compatibility-" + tag + "-" + uuid.uuid4().hex,
    )
    plan = build_plan(job, policy)
    repaired = patch_workbook(source, job["snapshot"], plan)
    verification = verify_output(source, repaired, plan, Settings())
    package = make_artifacts(job, plan, repaired, verification, compatibility_bootstrap=True)
    for kind, artifact in package["artifacts"].items():
        suffix = ".html" if kind == "VERIFICATION_HTML" else ".xlsx"
        (out / f"{tag}-{kind}{suffix}").write_bytes(artifact["data"])
    (out / f"{tag}-manifest.json").write_text(
        json.dumps(package["manifest"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    rows.append(
        {
            "profile": tag,
            "source_hash": plan["source_hash"],
            "plan_digest": plan["digest"],
            "output_hash": verification["output_hash"],
            "files": package["manifest"]["files"],
            "ready_published": False,
        }
    )
(out / "inputs.json").write_text(
    json.dumps({"patch_fingerprint": patch_fingerprint(), "rows": rows}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(
    "Actual patch, post-calculation and three artifacts created for Excel compatibility verification; not published READY."
)
