from __future__ import annotations

import hashlib
import json
from pathlib import Path

from release_config import LIVE_BASELINE, REPO, RP03_PRECEDENT, SOURCE_FREEZE, frontend_source_paths, overlay_paths, image_path_for


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

live = json.loads(LIVE_BASELINE.read_text(encoding="utf-8"))
precedent = json.loads(RP03_PRECEDENT.read_text(encoding="utf-8"))
paths = overlay_paths()
missing = [p for p in paths if not (REPO / p).is_file()]
if missing:
    raise SystemExit(f"Missing overlay inputs: {missing}")
fixture = "artifacts/synthetic_validation/monthly-repair-flow06/stage3/monthly-rp03-supported-6sheet.xlsx"
assert sha256(REPO / fixture) == precedent["source_sha256"], "RP03 fixture hash must match stage3 precedent"
freeze = {
    "status": "FROZEN",
    "unit": "MONTHLY-UX07-RELEASE",
    "live_base": live,
    "rp03_precedent": {
        "path": str(RP03_PRECEDENT.relative_to(REPO)),
        "source_sha256": precedent["source_sha256"],
        "expected_value": precedent["expected_value"],
        "raw_formula": precedent["raw_formula"],
        "monthly_detector_target_candidates": precedent["monthly_detector_target_candidates"],
    },
    "overlay": [
        {"repo_path": p, "image_path": image_path_for(p), "sha256": sha256(REPO / p), "bytes": (REPO / p).stat().st_size}
        for p in paths
    ],
    "frontend_source": [
        {"repo_path": p, "sha256": sha256(REPO / p), "bytes": (REPO / p).stat().st_size}
        for p in frontend_source_paths()
    ],
}
SOURCE_FREEZE.write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "FROZEN", "path": str(SOURCE_FREEZE), "count": len(paths)}, ensure_ascii=False))
