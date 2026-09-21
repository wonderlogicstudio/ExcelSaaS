from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


DATASET_VERSION = "synthetic-01.1"
GENERATOR_VERSION = "2026.09.20"
SUPPORTED_M4_RULES = {"FORMULA_PATTERN_OUTLIER", "FORMULA_PATTERN_GAP"}
IN_SCOPE_BASE_RULES = {"FORMULA_REF_ERROR", "FORMULA_VISIBLE_ERROR_TOKEN"}

ExpectedKind = Literal[
    "confirmed_error",
    "m4_candidate",
    "normal_exception",
    "user_confirmation",
    "out_of_scope",
]
WorkbookKind = Literal["normal", "mutated"]
SplitName = Literal["train", "dev", "holdout"]
CellValue = str | float | int | bool | None


@dataclass(frozen=True, slots=True)
class ExpectedFinding:
    expected_id: str
    kind: ExpectedKind
    sheet: str
    cell: str
    rule_code: str | None
    pattern_subtype: str | None = None
    severity: str | None = None
    family_id: str = ""
    mutation_type: str | None = None
    notes: str = ""

    @property
    def is_scored_error(self) -> bool:
        return self.kind in {"confirmed_error", "m4_candidate"}


@dataclass(frozen=True, slots=True)
class NormalRegion:
    sheet: str
    range_ref: str
    notes: str


@dataclass(frozen=True, slots=True)
class FormulaCellSpec:
    sheet: str
    cell: str
    formula: CellValue
    semantic_value: float | int | str | None
    role: Literal["detail", "subtotal", "normal_exception", "exploratory"]
    supported_by_current_m4: bool


@dataclass(frozen=True, slots=True)
class MutationSnapshot:
    sheet: str
    cell: str
    before_value: CellValue
    before_data_type: str
    after_value: CellValue
    after_data_type: str
    before_formula: CellValue = None
    after_formula: CellValue = None


@dataclass(frozen=True, slots=True)
class WorkbookTruth:
    workbook_id: str
    parent_id: str | None
    family_id: str
    scenario_id: str
    business_domain: str
    structural_family: str
    split: SplitName
    kind: WorkbookKind
    seed: int
    filename: str
    relative_path: str
    sha256: str
    mutation_type: str | None
    mutation_target: str | None
    supported_scope: list[str]
    exploratory_scope: list[str]
    normal_regions: list[NormalRegion]
    formula_cells: list[FormulaCellSpec]
    expected_findings: list[ExpectedFinding]
    generation_checks: dict[str, Any] = field(default_factory=dict)
    mutation_snapshot: MutationSnapshot | None = None


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    dataset_version: str
    generator_version: str
    run_id: str
    seed: int
    pair_count: int
    family_order: list[str]
    split_by_family: dict[str, SplitName]
    workbooks: list[WorkbookTruth]
    config_hash: str
    source_hash: str
    truth_hash: str


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(data: Any) -> str:
    return sha256_bytes(canonical_json(data).encode("utf-8"))


def dataclass_to_dict(value: Any) -> Any:
    return asdict(value)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
