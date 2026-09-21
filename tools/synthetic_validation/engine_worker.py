from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

SAFE_ENV_NAMES = {
    "PATH",
    "PYTHONPATH",
    "SYSTEMROOT",
    "WINDIR",
    "TEMP",
    "TMP",
    "NUMBER_OF_PROCESSORS",
    "PROCESSOR_ARCHITECTURE",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _model_dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def _safe_settings(settings: Any) -> dict[str, Any]:
    payload = _model_dump(settings)
    safe_keys = {
        "app_env",
        "formula_pattern_audit_enabled",
        "finding_limit",
        "scan_cell_limit",
    }
    return {key: payload.get(key) for key in sorted(safe_keys) if key in payload}


def _has_usable_base(base: dict[str, Any] | None) -> bool:
    if not isinstance(base, dict):
        return False
    return any(key in base for key in ("workbook", "summary", "findings", "finding_counts"))


def _has_usable_audit(audit: dict[str, Any] | None) -> bool:
    if not isinstance(audit, dict):
        return False
    candidates = audit.get("candidates")
    return audit.get("status") == "COMPLETED" or bool(candidates)


def _base_is_complete(base: dict[str, Any]) -> bool:
    workbook = base.get("workbook") if isinstance(base.get("workbook"), dict) else {}
    if workbook.get("scan_truncated") is True:
        return False
    counts = base.get("finding_counts") if isinstance(base.get("finding_counts"), dict) else {}
    if counts.get("scan_complete") is False:
        return False
    if int(counts.get("omitted_details") or 0) > 0:
        return False
    summary = base.get("summary") if isinstance(base.get("summary"), dict) else {}
    findings = base.get("findings") if isinstance(base.get("findings"), list) else []
    if "issue_count" in summary and int(summary.get("issue_count") or 0) > len(findings) and not isinstance(base.get("finding_counts"), dict):
        return False
    return True


def _status_from_parts(base: dict[str, Any] | None, audit: dict[str, Any] | None) -> str:
    base_usable = _has_usable_base(base)
    audit_usable = _has_usable_audit(audit)
    if not base_usable and not audit_usable:
        return "FAILED"
    if (
        base_usable
        and audit_usable
        and _base_is_complete(base or {})
        and str((audit or {}).get("status") or "") == "COMPLETED"
    ):
        return "COMPLETED"
    return "PARTIAL"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real WorkbookCare scanner entry points.")
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    api_root = _repo_root() / "apps" / "api"
    sys.path.insert(0, str(api_root))

    started = time.perf_counter()
    base_payload: dict[str, Any] | None = None
    audit_payload: dict[str, Any] | None = None
    errors: list[dict[str, str]] = []
    try:
        from app.config import Settings
        from app.scanner import run_formula_audit, scan_workbook

        payload = args.workbook.read_bytes()
        base_settings = Settings(_env_file=None, finding_limit=120)
        audit_settings = Settings(_env_file=None, app_env="internal_beta", formula_pattern_audit_enabled=True, finding_limit=120)
        try:
            base_payload = _model_dump(scan_workbook(args.filename, payload, base_settings))
        except Exception as exc:  # pragma: no cover - exercised by runner-level failures
            errors.append({"entrypoint": "scan_workbook", "error_type": type(exc).__name__, "error": str(exc)})
        try:
            audit_payload = _model_dump(run_formula_audit(args.filename, payload, audit_settings))
        except Exception as exc:  # pragma: no cover - exercised by runner-level failures
            errors.append({"entrypoint": "run_formula_audit", "error_type": type(exc).__name__, "error": str(exc)})
        result = {
            "status": _status_from_parts(base_payload, audit_payload),
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
            "entrypoints": ["scan_workbook", "run_formula_audit"],
            "base": base_payload or {"findings": []},
            "audit": audit_payload or {"status": "FAILED", "candidates": []},
            "errors": errors,
            "actual_safe_settings": {"base": _safe_settings(base_settings), "audit": _safe_settings(audit_settings)},
            "versions": {"python": sys.version.split()[0], "openpyxl": _package_version("openpyxl"), "pydantic": _package_version("pydantic")},
            "safe_env_names_present": sorted(name for name in SAFE_ENV_NAMES if name in os.environ),
            "engine_notes": ["Local diagnostic entry points only; not HTTP/UI validation.", "Excel formulas are not recalculated by this worker.", "M4 candidates are uncertainty signals, not confirmed formula errors."],
        }
    except Exception as exc:
        result = {"status": "FAILED", "elapsed_ms": round((time.perf_counter() - started) * 1000), "error_type": type(exc).__name__, "error": str(exc), "base": {"findings": []}, "audit": {"status": "FAILED", "candidates": []}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "elapsed_ms": result["elapsed_ms"]}))
    return 0 if result["status"] in {"COMPLETED", "PARTIAL"} else 2


if __name__ == "__main__":
    raise SystemExit(main())


