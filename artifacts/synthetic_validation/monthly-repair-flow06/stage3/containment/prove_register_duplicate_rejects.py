from __future__ import annotations

import json
import runpy
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

repo = Path.cwd()
source = repo / "artifacts/verification/d08/compatibility"
work = repo / "artifacts/synthetic_validation/monthly-repair-flow06/stage3/containment/duplicate-register-proof"
if work.exists():
    shutil.rmtree(work)
work.mkdir(parents=True)
for path in source.iterdir():
    if path.is_file() and path.suffix.lower() in {".json", ".xlsx", ".html"}:
        shutil.copy2(path, work / path.name)
inputs_path = work / "inputs.json"
inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
inputs["rows"] = [inputs["rows"][0], inputs["rows"][0], inputs["rows"][1]]
inputs_path.write_text(json.dumps(inputs, ensure_ascii=False, indent=2), encoding="utf-8")

sys.argv = [
    "scripts/register_delivery_patch_reference.py",
    "--stage",
    "d08",
    "--evidence-dir",
    str(work),
]
reference = repo / "apps/api/app/delivery_patch_reference.json"
with patch("app.delivery_plan.reference_status", lambda: {"status": "PASS"}), patch.object(
    Path,
    "write_text",
    side_effect=lambda self, *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("unexpected reference write")
    )
    if self.resolve() == reference.resolve()
    else Path.write_text(self, *args, **kwargs),
):
    try:
        runpy.run_path("scripts/register_delivery_patch_reference.py", run_name="__main__")
    except AssertionError:
        print("duplicate input rows rejected before registration")
    else:
        raise SystemExit("duplicate input rows were not rejected")
