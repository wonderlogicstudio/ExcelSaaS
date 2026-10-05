from __future__ import annotations

from pathlib import Path

REPO = next(parent for parent in Path(__file__).resolve().parents if (parent / "package.json").is_file() and (parent / "apps/api").is_dir())
TOOLS = Path(__file__).resolve().parent
OUT = TOOLS / "output"
IMAGE_OUT = OUT / "image"
API_RELEASE = OUT / "api-release"
WEB_RELEASE = OUT / "web-release"
SOURCE_FREEZE = TOOLS / "source-freeze.json"
LIVE_BASELINE = REPO / "artifacts/synthetic_validation/false-repair-guard01-release/live-baseline.json"
RP03_PRECEDENT = REPO / "artifacts/synthetic_validation/monthly-repair-flow06/stage3/rp03-saved-artifact-runtime-result.json"
RP03_SOURCE = REPO / "artifacts/synthetic_validation/monthly-repair-flow06/stage3/monthly-rp03-supported-6sheet.xlsx"
BASE_IMAGE_DIR = Path(r"C:\Users\JinwonLee\project\ExcelSaaS\artifacts\synthetic_validation\monthly-ux07-release\resume02\release-tools\output\image")
PROJECT = "workbookcare-beta"
SERVICE = "workbookcare-api-beta"
REGION = "asia-northeast3"
API_GATEWAY = "workbookcare-beta-gateway"
API_GATEWAY_API = "workbookcare-beta-api"
API_GATEWAY_LOCATION = "asia-northeast1"
WORKER_HOST = "https://workbookcare-beta.wonderlogic-studio.workers.dev"
EXPECTED_BASE_REVISION = "workbookcare-api-beta-00033-dum"
EXPECTED_BASE_IMAGE_DIGEST = "d2265d9e56756fd240e1ddf93509d9fa096bd6d77acd499caff9d41ab1caa5c9"
EXPECTED_WORKER_VERSION = "44ed2196-cca5-4fa9-963c-16497a3ff77a"
CONFIRM_MUTATION = "FALSE_REPAIR_GUARD01_APPROVED_MUTATION"
CONFIRM_PUSH = "MONTHLY_UX07_APPROVED_PUSH"

API_SOURCE_PATHS = [
    "apps/api/app/delivery_api.py",
    "apps/api/app/delivery_calculation.py",
    "apps/api/app/delivery_execution.py",
    "apps/api/app/delivery_inputs.py",
    "apps/api/app/repair_rules/numeric_text.py",
    "apps/api/app/delivery_patch.py",
    "apps/api/app/delivery_patch_reference.json",
    "apps/api/app/delivery_plan.py",
    "apps/api/app/delivery_reference.json",
    "apps/api/app/delivery_rehearsal.py",
    "apps/api/app/formula_patterns.py",
    "apps/api/app/repair_rules/monthly_formula.py",
]
ENGINE_SOURCE_PATHS = [
    "apps/api/engine/DeliveryCalc.java",
    "apps/api/engine/classes/DeliveryCalc.class",
    "apps/api/engine/classes/DeliveryCalc$1.class",
]
FIXTURE_PATHS = ["artifacts/synthetic_validation/monthly-repair-flow06/stage3/monthly-rp03-supported-6sheet.xlsx"]

def engine_jar_paths() -> list[str]:
    return sorted(p.relative_to(REPO).as_posix() for p in (REPO / "apps/api/engine/lib").glob("*.jar"))

def overlay_paths() -> list[str]:
    return API_SOURCE_PATHS + ENGINE_SOURCE_PATHS + engine_jar_paths() + FIXTURE_PATHS + [
        "artifacts/synthetic_validation/false-repair-guard01-release/release-tools/rp03_startup_wrapper.py"
    ]

def image_path_for(repo_path: str) -> str:
    if repo_path.startswith("apps/api/app/"):
        return "app/app/" + repo_path.removeprefix("apps/api/app/")
    if repo_path.startswith("apps/api/engine/"):
        return "app/engine/" + repo_path.removeprefix("apps/api/engine/")
    if repo_path.endswith("rp03_startup_wrapper.py"):
        return "app/release_tools/rp03_startup_wrapper.py"
    if repo_path.endswith("monthly-rp03-supported-6sheet.xlsx"):
        return "app/verification/monthly-rp03-supported-6sheet.xlsx"
    raise ValueError(f"No image path mapping for {repo_path}")


def frontend_source_paths() -> list[str]:
    roots = [REPO / "apps/web/src"]
    files = [
        REPO / "apps/web/package.json",
        REPO / "apps/web/tsconfig.json",
        REPO / "apps/web/tsconfig.app.json",
        REPO / "apps/web/tsconfig.node.json",
        REPO / "apps/web/vite.config.ts",
        REPO / "apps/web/index.html",
        REPO / "package.json",
        REPO / "package-lock.json",
    ]
    for root in roots:
        files.extend(p for p in root.rglob("*") if p.is_file())
    return sorted(p.relative_to(REPO).as_posix() for p in files if p.is_file())
