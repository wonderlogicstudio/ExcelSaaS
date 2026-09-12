"""Generate/check the local fallback from the actual API service catalog."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))
from app.service_catalog import get_product_offerings  # noqa: E402

path = ROOT / "apps/web/src/data/product-catalog.fixture.json"
content = json.dumps(
    [item.model_dump(mode="json") for item in get_product_offerings()],
    ensure_ascii=False, indent=2,
) + "\n"
if "--check" in sys.argv:
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        raise SystemExit("Product catalog fixture is stale")
    print("Product catalog fixture matches the API catalog")
else:
    path.write_text(content, encoding="utf-8")
    print("Generated apps/web/src/data/product-catalog.fixture.json")
