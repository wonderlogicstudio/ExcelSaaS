from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
SAMPLE_PATH = ROOT / "samples" / "demo-risky-workbook.xlsx"
OUTPUT_PATH = ROOT / "apps" / "web" / "src" / "data" / "demo-result.fixture.json"

sys.path.insert(0, str(API_ROOT))

from app.config import Settings  # noqa: E402
from app.recommendation_engine import enrich_scan_result  # noqa: E402
from app.scanner import scan_workbook  # noqa: E402


def build_fixture() -> dict[str, object]:
    result = enrich_scan_result(
        scan_workbook(SAMPLE_PATH.name, SAMPLE_PATH.read_bytes(), Settings())
    )
    return {
        "fixture_metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "generated_from": SAMPLE_PATH.relative_to(ROOT).as_posix(),
            "generator": "scripts/generate_demo_fixture.py",
            "scanner_version": result.scanner_version,
            "rule_set_version": result.rule_set_version,
        },
        "scan_result": result.model_dump(mode="json"),
    }


def main() -> None:
    OUTPUT_PATH.write_text(
        json.dumps(build_fixture(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
