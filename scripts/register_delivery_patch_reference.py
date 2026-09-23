"""Register measured Excel compatibility; never invent or upgrade missing evidence."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "apps/api"))
from app.delivery_execution import patch_fingerprint
from app.delivery_plan import reference_status


def resolve_evidence_dir(value: str | None, *, stage: str) -> Path:
    artifact_root = (R / "artifacts").resolve()
    path = R / f"artifacts/verification/{stage}/compatibility" if value is None else Path(value)
    path = (R / path).resolve() if not path.is_absolute() else path.resolve()
    if path != artifact_root and artifact_root not in path.parents:
        raise SystemExit("Evidence directory must stay under the repository artifacts directory")
    return path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--stage", choices=["d04", "d08"], default="d04")
parser.add_argument("--evidence-dir")
args = parser.parse_args()
root = resolve_evidence_dir(args.evidence_dir, stage=args.stage)
data = json.loads((root / "excel-reopen.json").read_text(encoding="utf-8-sig"))
inputs = json.loads((root / "inputs.json").read_text(encoding="utf-8"))
assert reference_status()["status"] == "PASS"
assert data["status"] == "PASS"
assert data["patch_fingerprint"] == inputs["patch_fingerprint"] == patch_fingerprint()
assert set(data["profiles"]) == {"RP01", "RP02", "RP03"}
assert len(data["profiles"]) == len(set(data["profiles"])) == 3
assert len(inputs["rows"]) == len({row["profile"] for row in inputs["rows"]}) == 3
assert len(data["results"]) == len({row["profile"] for row in data["results"]}) == 3
input_rows = {row["profile"]: row for row in inputs["rows"]}
result_rows = {row["profile"]: row for row in data["results"]}
assert set(input_rows) == set(result_rows) == {"RP01", "RP02", "RP03"}
for profile, result in result_rows.items():
    assert all(
        result[k] is True
        for k in [
            "repaired_opened",
            "changes_opened",
            "actual_values_match",
            "literal_report_formulas",
            "read_only_hash_unchanged",
        ]
    )
    manifest = json.loads((root / f"{profile}-manifest.json").read_text(encoding="utf-8"))
    files = manifest["files"]
    artifacts = {
        "REPAIRED_XLSX": root / f"{profile}-REPAIRED_XLSX.xlsx",
        "CHANGES_XLSX": root / f"{profile}-CHANGES_XLSX.xlsx",
        "VERIFICATION_HTML": root / f"{profile}-VERIFICATION_HTML.html",
    }
    for kind, path in artifacts.items():
        actual = sha(path)
        assert actual == files[kind]["sha256"]
        assert actual == input_rows[profile]["files"][kind]["sha256"]
    assert result["output_hash"] == sha(artifacts["REPAIRED_XLSX"])
    assert result["changes_hash"] == sha(artifacts["CHANGES_XLSX"])
    assert result["verification_html_hash"] == sha(artifacts["VERIFICATION_HTML"])
    assert manifest["plan_digest"] == input_rows[profile]["plan_digest"]
    assert manifest["output_hash"] == result["output_hash"]
    assert input_rows[profile]["ready_published"] is False
(R / "apps/api/app/delivery_patch_reference.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print("Measured Excel output evidence registered; current engine and patch fingerprints PASS.")
