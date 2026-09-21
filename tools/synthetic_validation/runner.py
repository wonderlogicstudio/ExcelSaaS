from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .engine_worker import _status_from_parts
from .schema import (
    DatasetManifest,
    dataclass_to_dict,
    read_json,
    sha256_file,
    sha256_json,
    write_json,
)

ENGINE_DESCRIPTOR = {
    "entrypoints": ["scan_workbook", "run_formula_audit"],
    "base_settings": {"_env_file": None, "finding_limit": 120},
    "audit_settings": {"_env_file": None, "app_env": "internal_beta", "formula_pattern_audit_enabled": True, "finding_limit": 120},
    "compare_policy": {"expected_actual_match": "one_to_one", "duplicates": "counted_not_fp", "malformed_locations": "unjudged"},
    "rule_map": {"m4": ["FORMULA_PATTERN_OUTLIER", "FORMULA_PATTERN_GAP"], "base": ["FORMULA_REF_ERROR", "FORMULA_VISIBLE_ERROR_TOKEN"]},
    "excel_recalculation": "NOT_RUN",
}
SAFE_CHILD_ENV = {"PATH", "PYTHONPATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE"}


@dataclass(frozen=True, slots=True)
class EngineRunConfig:
    timeout_seconds: int = 20
    resume: bool = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _worker_script() -> Path:
    return Path(__file__).with_name("engine_worker.py")


def _raw_path(run_root: Path, workbook_id: str) -> Path:
    return run_root / "raw_engine" / f"{workbook_id}.json"


def _status_path(run_root: Path) -> Path:
    return run_root / "engine_status.json"


def _tool_hash() -> str:
    root = Path(__file__).resolve().parent
    payload = {str(path.relative_to(root)).replace("\\", "/"): sha256_file(path) for path in sorted(root.rglob("*")) if path.is_file() and path.suffix in {".py", ".md"}}
    return sha256_json(payload)


def _engine_source_hash() -> str:
    root = _repo_root()
    payload: dict[str, str] = {}
    app_root = root / "apps" / "api" / "app"
    if app_root.exists():
        for path in sorted(app_root.rglob("*.py")):
            payload[str(path.relative_to(root)).replace("\\", "/")] = sha256_file(path)
    for rel in ("requirements.txt", "apps/api/requirements.txt", "dependencies.lock.json", "apps/api/dependencies.lock.json", "apps/api/engine/dependencies.lock.json"):
        path = root / rel
        if path.exists():
            payload[rel] = sha256_file(path)
    return sha256_json(payload)


def _current_file_hashes(manifest: DatasetManifest, dataset_root: Path) -> dict[str, str]:
    hashes = {}
    for truth in manifest.workbooks:
        path = dataset_root / truth.relative_path
        actual = sha256_file(path)
        if actual != truth.sha256:
            raise RuntimeError(f"Generated workbook hash mismatch for {truth.workbook_id}: manifest={truth.sha256} actual={actual}")
        hashes[truth.workbook_id] = actual
    return hashes


def _settings_hash(python_exe: Path, config: EngineRunConfig) -> str:
    return sha256_json({"python_exe": str(python_exe), "config": asdict(config), "engine_descriptor": ENGINE_DESCRIPTOR})


def _verify_truth_hash(manifest: DatasetManifest, dataset_root: Path) -> str:
    truth_payload = [dataclass_to_dict(workbook) for workbook in manifest.workbooks]
    recomputed = sha256_json(truth_payload)
    if recomputed != manifest.truth_hash:
        raise RuntimeError("Manifest truth_hash does not match manifest workbook truth payload.")
    truth_path = dataset_root / "truth.json"
    if not truth_path.exists():
        raise RuntimeError("truth.json is required for canonical truth hash verification.")
    truth_json_hash = sha256_json(read_json(truth_path))
    if truth_json_hash != manifest.truth_hash:
        raise RuntimeError("truth.json hash does not match manifest truth_hash.")
    return recomputed


def build_frozen_contract(*, manifest: DatasetManifest, dataset_root: Path, run_root: Path, python_exe: Path, config: EngineRunConfig) -> dict[str, Any]:
    verified_truth_hash = _verify_truth_hash(manifest, dataset_root)
    return {
        "run_id": manifest.run_id,
        "generated_run_path": str(run_root),
        "created_before_engine_execution": True,
        "dataset_version": manifest.dataset_version,
        "generator_version": manifest.generator_version,
        "config_hash": manifest.config_hash,
        "source_hash": manifest.source_hash,
        "truth_hash": verified_truth_hash,
        "split_by_family": manifest.split_by_family,
        "family_order": manifest.family_order,
        "engine_descriptor": ENGINE_DESCRIPTOR,
        "engine_source_hash": _engine_source_hash(),
        "tool_hash": _tool_hash(),
        "settings_hash": _settings_hash(python_exe, config),
        "python_exe": str(python_exe),
        "engine_config": asdict(config),
        "entrypoint_scope": "local product internals; not HTTP/UI",
        "excel_recalculation": "NOT_RUN",
        "cache_dependent_claims": "EXCLUDED",
        "file_hashes": _current_file_hashes(manifest, dataset_root),
    }


def write_frozen_contract(*, manifest: DatasetManifest, dataset_root: Path, run_root: Path, python_exe: Path, config: EngineRunConfig) -> dict[str, Any]:
    contract = build_frozen_contract(manifest=manifest, dataset_root=dataset_root, run_root=run_root, python_exe=python_exe, config=config)
    path = run_root / "frozen_contract.json"
    if path.exists() and read_json(path) != contract:
        raise RuntimeError("Existing frozen_contract.json differs; use a new run_id instead of overwriting.")
    write_json(path, contract)
    return contract


def validate_frozen_contract(*, manifest: DatasetManifest, dataset_root: Path, run_root: Path, python_exe: Path, config: EngineRunConfig) -> dict[str, Any]:
    path = run_root / "frozen_contract.json"
    if not path.exists():
        raise RuntimeError("frozen_contract.json is required before engine run or score.")
    expected = build_frozen_contract(manifest=manifest, dataset_root=dataset_root, run_root=run_root, python_exe=python_exe, config=config)
    actual = read_json(path)
    if actual != expected:
        raise RuntimeError("Frozen contract validation failed; source, truth, files, tool, or settings changed.")
    return actual


def _resume_ok(status: dict[str, Any], manifest: DatasetManifest, dataset_root: Path, python_exe: Path | None = None, config: EngineRunConfig | None = None) -> bool:
    if status.get("config_hash") != manifest.config_hash or status.get("source_hash") != manifest.source_hash or status.get("truth_hash") != _verify_truth_hash(manifest, dataset_root):
        return False
    if status.get("tool_hash") != _tool_hash() or status.get("engine_source_hash") != _engine_source_hash():
        return False
    if python_exe is not None and config is not None and status.get("settings_hash") != _settings_hash(python_exe, config):
        return False
    if status.get("engine_descriptor") != ENGINE_DESCRIPTOR:
        return False
    if status.get("file_hashes", {}) != _current_file_hashes(manifest, dataset_root):
        return False
    for record in status.get("records", []):
        raw_sha = record.get("raw_sha256")
        if raw_sha is None:
            continue
        raw_path_value = record.get("raw_output")
        if not raw_path_value:
            return False
        raw_path = Path(raw_path_value)
        if not raw_path.exists() or raw_sha != sha256_file(raw_path):
            return False
    return True


def _classified_record(record: dict[str, Any]) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    raw_status = None
    raw_output = record.get("raw_output")
    if raw_output:
        try:
            raw = read_json(Path(raw_output))
            raw_status = raw.get("status")
        except Exception:
            raw = {}
    status = str(record.get("status") or "FAILED")
    if status == "NOT_RUN":
        classified = "NOT_RUN"
    elif status == "TIMEOUT" or record.get("timed_out") is True:
        classified = "TIMEOUT"
    elif raw:
        classified = _status_from_parts(raw.get("base"), raw.get("audit"))
    else:
        classified = status if status in {"COMPLETED", "PARTIAL", "FAILED"} else "FAILED"
    audit_status = str((raw.get("audit") or {}).get("status") or "")
    base = raw.get("base") or {}
    workbook = base.get("workbook") if isinstance(base.get("workbook"), dict) else {}
    counts = base.get("finding_counts") if isinstance(base.get("finding_counts"), dict) else {}
    return {
        "status": classified,
        "raw_status": raw_status,
        "audit_status": audit_status,
        "raw_errors": len(raw.get("errors") or []),
        "truncated": workbook.get("scan_truncated") is True or counts.get("scan_complete") is False,
        "omitted_details": int(counts.get("omitted_details") or 0),
        "has_raw_output": bool(raw_output),
    }


def _completion(records: list[dict[str, Any]], manifest_workbooks: int | list[str]) -> dict[str, int]:
    if isinstance(manifest_workbooks, int):
        terminal = {record["workbook_id"]: _classified_record(record) for record in records}
        return {
            "workbooks_total": manifest_workbooks,
            "completed": sum(1 for record in terminal.values() if record["status"] == "COMPLETED"),
            "partial": sum(1 for record in terminal.values() if record["status"] == "PARTIAL"),
            "failed": sum(1 for record in terminal.values() if record["status"] == "FAILED"),
            "timeouts": sum(1 for record in terminal.values() if record["status"] == "TIMEOUT"),
            "not_run": max(0, manifest_workbooks - len(terminal)),
        }
    terminal = {record["workbook_id"]: _classified_record(record) for record in records}
    scoped = {workbook_id: terminal.get(workbook_id, {"status": "NOT_RUN"}) for workbook_id in manifest_workbooks}
    completed = sum(1 for record in scoped.values() if record["status"] == "COMPLETED")
    partial = sum(1 for record in scoped.values() if record["status"] == "PARTIAL")
    failed = sum(1 for record in scoped.values() if record["status"] == "FAILED")
    timeouts = sum(1 for record in scoped.values() if record["status"] == "TIMEOUT")
    not_run = sum(1 for record in scoped.values() if record["status"] == "NOT_RUN")
    skipped = sum(1 for record in scoped.values() if str(record.get("audit_status") or "").startswith("SKIPPED_"))
    abstained = sum(1 for record in scoped.values() if str(record.get("audit_status") or "").startswith("ABSTAINED"))
    audit_failed = sum(1 for record in scoped.values() if str(record.get("audit_status") or "") == "FAILED")
    truncated = sum(1 for record in scoped.values() if record.get("truncated") or int(record.get("omitted_details") or 0) > 0)
    raw_errors = sum(int(record.get("raw_errors") or 0) for record in scoped.values())
    return {
        "workbooks_total": len(manifest_workbooks),
        "process_outputs": sum(1 for record in scoped.values() if record.get("has_raw_output")),
        "completed": completed,
        "partial": partial,
        "failed": failed,
        "timeouts": timeouts,
        "not_run": not_run,
        "skipped": skipped,
        "abstained": abstained,
        "audit_failed": audit_failed,
        "truncated": truncated,
        "raw_errors": raw_errors,
    }


def _raw_status(raw_output: Path, fallback: str) -> str:
    if not raw_output.exists():
        return fallback
    try:
        return str(read_json(raw_output).get("status") or fallback)
    except Exception:
        return fallback


def _child_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key.upper() in SAFE_CHILD_ENV}


def run_engine(*, manifest: DatasetManifest, dataset_root: Path, run_root: Path, python_exe: Path | None = None, config: EngineRunConfig | None = None) -> dict[str, Any]:
    config = config or EngineRunConfig()
    python_exe = python_exe or Path(sys.executable)
    validate_frozen_contract(manifest=manifest, dataset_root=dataset_root, run_root=run_root, python_exe=python_exe, config=config)
    status_file = _status_path(run_root)
    file_hashes = _current_file_hashes(manifest, dataset_root)
    tool_hash = _tool_hash()
    engine_source_hash = _engine_source_hash()
    settings_hash = _settings_hash(python_exe, config)
    verified_truth_hash = _verify_truth_hash(manifest, dataset_root)

    previous = read_json(status_file) if status_file.exists() else {}
    if previous and not config.resume:
        raise RuntimeError("Existing engine_status.json is immutable; use a new run_id instead of overwriting.")
    can_resume = bool(previous) and _resume_ok(previous, manifest, dataset_root, python_exe, config)
    if previous and not can_resume:
        raise RuntimeError("Existing run cannot be resumed because frozen hashes or settings changed; use a new run_id.")
    records: list[dict[str, Any]] = list(previous.get("records", [])) if can_resume else []
    terminal_ids = {record["workbook_id"] for record in records if record.get("status") in {"COMPLETED", "PARTIAL", "FAILED", "TIMEOUT"}}

    for truth in manifest.workbooks:
        raw_output = _raw_path(run_root, truth.workbook_id)
        if truth.workbook_id in terminal_ids:
            continue
        started = time.perf_counter()
        command = [str(python_exe), str(_worker_script()), "--workbook", str(dataset_root / truth.relative_path), "--filename", truth.filename, "--output", str(raw_output)]
        status = "FAILED"
        exit_code: int | None = None
        timed_out = False
        stdout = ""
        stderr = ""
        try:
            proc = subprocess.run(command, cwd=str(_repo_root()), env=_child_env(), text=True, capture_output=True, timeout=config.timeout_seconds, check=False)
            exit_code = proc.returncode
            stdout = proc.stdout[-4000:]
            stderr = proc.stderr[-4000:]
            status = _raw_status(raw_output, "COMPLETED" if proc.returncode == 0 else "FAILED")
            if raw_output.exists():
                raw_payload = read_json(raw_output)
                status = _status_from_parts(raw_payload.get("base"), raw_payload.get("audit"))
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            status = "TIMEOUT"
            stdout = (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else ""
        except OSError as exc:
            status = "FAILED"
            stderr = f"{type(exc).__name__}: {exc}"
        raw_sha = sha256_file(raw_output) if raw_output.exists() else None
        records.append({"workbook_id": truth.workbook_id, "filename": truth.filename, "status": status, "exit_code": exit_code, "timed_out": timed_out, "elapsed_ms": round((time.perf_counter() - started) * 1000), "raw_output": str(raw_output) if raw_output.exists() else None, "raw_sha256": raw_sha, "stdout_tail": stdout, "stderr_tail": stderr})
        write_json(status_file, {"config_hash": manifest.config_hash, "source_hash": manifest.source_hash, "truth_hash": verified_truth_hash, "tool_hash": tool_hash, "engine_source_hash": engine_source_hash, "settings_hash": settings_hash, "engine_descriptor": ENGINE_DESCRIPTOR, "python_exe": str(python_exe), "engine_config": asdict(config), "file_hashes": file_hashes, "records": records, "completion": _completion(records, [item.workbook_id for item in manifest.workbooks])})
    status_payload = read_json(status_file) if status_file.exists() else {"config_hash": manifest.config_hash, "source_hash": manifest.source_hash, "truth_hash": verified_truth_hash, "tool_hash": tool_hash, "engine_source_hash": engine_source_hash, "settings_hash": settings_hash, "engine_descriptor": ENGINE_DESCRIPTOR, "python_exe": str(python_exe), "engine_config": asdict(config), "file_hashes": file_hashes, "records": records}
    status_payload["completion"] = _completion(status_payload.get("records", []), [item.workbook_id for item in manifest.workbooks])
    write_json(status_file, status_payload)
    return status_payload



