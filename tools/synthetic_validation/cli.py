from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .generator import generate_dataset
from .report import write_html_report
from .runner import EngineRunConfig, validate_frozen_contract, write_frozen_contract
from .runner import run_engine
from .schema import DatasetManifest, ExpectedFinding, FormulaCellSpec, MutationSnapshot, NormalRegion, WorkbookTruth, read_json, sha256_file, write_json
from .scorer import score_results
from .verify_generated import validate_generated_workbook


def default_output_root() -> Path:
    return Path.cwd() / "artifacts" / "synthetic_validation"


def new_run_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"


def _manifest_from_dict(data: dict[str, Any]) -> DatasetManifest:
    workbooks = []
    for item in data["workbooks"]:
        mutation_snapshot = item.get("mutation_snapshot")
        workbooks.append(WorkbookTruth(**{**item, "normal_regions": [NormalRegion(**region) for region in item["normal_regions"]], "formula_cells": [FormulaCellSpec(**spec) for spec in item["formula_cells"]], "expected_findings": [ExpectedFinding(**expected) for expected in item["expected_findings"]], "mutation_snapshot": MutationSnapshot(**mutation_snapshot) if mutation_snapshot else None}))
    return DatasetManifest(**{key: value for key, value in data.items() if key != "workbooks"}, workbooks=workbooks)


def _load_manifest(dataset_root: Path) -> DatasetManifest:
    return _manifest_from_dict(read_json(dataset_root / "manifest.json"))


def _write_generation_validation(manifest: DatasetManifest, dataset_root: Path, run_root: Path) -> None:
    validation = {truth.workbook_id: validate_generated_workbook(dataset_root, truth) for truth in manifest.workbooks}
    write_json(run_root / "generation_validation.json", validation)


def generate_command(args: argparse.Namespace) -> int:
    run_id = args.run_id or new_run_id(args.mode)
    run_root = args.output_root / run_id
    if run_root.exists() and any(run_root.iterdir()):
        raise RuntimeError(f"Run already exists and will not be overwritten: {run_root}")
    dataset_root = run_root / "dataset"
    pair_count = 5 if args.mode == "smoke" else args.pairs
    manifest = generate_dataset(run_id=run_id, pair_count=pair_count, seed=args.seed, dataset_root=dataset_root)
    _write_generation_validation(manifest, dataset_root, run_root)
    write_frozen_contract(manifest=manifest, dataset_root=dataset_root, run_root=run_root, python_exe=args.python_exe, config=EngineRunConfig(timeout_seconds=args.timeout_seconds, resume=not args.no_resume))
    args.generated_run_root = run_root
    print(json.dumps({"run_id": run_id, "run_root": str(run_root), "dataset_root": str(dataset_root), "workbooks": len(manifest.workbooks)}))
    return 0


def prepare_eval_command(args: argparse.Namespace) -> int:
    source = args.source_run_root
    source_dataset = source / "dataset"
    source_manifest = _load_manifest(source_dataset)
    run_id = args.run_id or new_run_id("eval")
    run_root = args.output_root / run_id
    if run_root.exists() and any(run_root.iterdir()):
        raise RuntimeError(f"Run already exists and will not be overwritten: {run_root}")
    shutil.copytree(source_dataset, run_root / "dataset")
    manifest = _load_manifest(run_root / "dataset")
    if manifest.truth_hash != source_manifest.truth_hash:
        raise RuntimeError("Copied dataset truth hash does not match source dataset.")
    _write_generation_validation(manifest, run_root / "dataset", run_root)
    write_frozen_contract(manifest=manifest, dataset_root=run_root / "dataset", run_root=run_root, python_exe=args.python_exe, config=EngineRunConfig(timeout_seconds=args.timeout_seconds, resume=not args.no_resume))
    print(json.dumps({"run_id": run_id, "run_root": str(run_root), "source_run_root": str(source)}))
    return 0


def run_command(args: argparse.Namespace) -> int:
    run_root = args.run_root
    dataset_root = run_root / "dataset"
    manifest = _load_manifest(dataset_root)
    config = EngineRunConfig(timeout_seconds=args.timeout_seconds, resume=not args.no_resume)
    validate_frozen_contract(manifest=manifest, dataset_root=dataset_root, run_root=run_root, python_exe=args.python_exe, config=config)
    status = run_engine(manifest=manifest, dataset_root=dataset_root, run_root=run_root, python_exe=args.python_exe, config=config)
    print(json.dumps(status.get("completion", {})))
    return 0


def score_command(args: argparse.Namespace) -> int:
    run_root = args.run_root
    dataset_root = run_root / "dataset"
    manifest = _load_manifest(dataset_root)
    validate_frozen_contract(manifest=manifest, dataset_root=dataset_root, run_root=run_root, python_exe=args.python_exe, config=EngineRunConfig(timeout_seconds=args.timeout_seconds, resume=not args.no_resume))
    summary = score_results(manifest=manifest, dataset_root=dataset_root, run_root=run_root)
    html_path = write_html_report(manifest=manifest, summary=summary, run_root=run_root)
    print(json.dumps({"summary": str(run_root / "reports" / "summary.json"), "html": str(html_path)}))
    return 0


def all_command(args: argparse.Namespace) -> int:
    code = generate_command(args)
    if code:
        return code
    args.run_root = args.generated_run_root
    code = run_command(args)
    if code:
        return code
    return score_command(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synthetic WorkbookCare diagnostic validation.")
    parser.add_argument("--output-root", type=Path, default=default_output_root())
    parser.add_argument("--run-id")
    parser.add_argument("--seed", type=int, default=170917)
    parser.add_argument("--pairs", type=int, default=150)
    parser.add_argument("--python-exe", type=Path, default=Path(sys.executable))
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--no-resume", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "all"):
        child = sub.add_parser(name)
        child.add_argument("--mode", choices=["smoke", "full"], default="smoke")
        child.set_defaults(func=generate_command if name == "generate" else all_command)
    prepare = sub.add_parser("prepare-eval")
    prepare.add_argument("source_run_root", type=Path)
    prepare.set_defaults(func=prepare_eval_command)
    run = sub.add_parser("run-engine")
    run.add_argument("run_root", type=Path)
    run.set_defaults(func=run_command)
    score = sub.add_parser("score")
    score.add_argument("run_root", type=Path)
    score.set_defaults(func=score_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
