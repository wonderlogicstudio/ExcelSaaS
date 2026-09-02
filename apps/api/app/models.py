from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["critical", "warning", "info"]
EvidenceGrade = Literal["DIRECT_CONFIRMATION", "PATTERN_INFERENCE", "REFERENCE_SIGNAL"]
ActionCategory = Literal[
    "FIX_RECOMMENDED",
    "USER_CONFIRMATION",
    "DEEP_VALIDATION_REQUIRED",
    "INFO_ONLY",
]
RepairEligibility = Literal[
    "MANUAL_GUIDANCE_AVAILABLE",
    "USER_CONFIRMATION_REQUIRED",
    "EXPERT_REVIEW_REQUIRED",
    "CURRENTLY_NOT_SUPPORTED",
    "NOT_APPLICABLE",
]
RepairReadinessStatus = Literal[
    "REPAIR_CANDIDATE_AFTER_APPROVAL",
    "USER_DECISION_REQUIRED",
    "PRECISION_VERIFICATION_REQUIRED",
    "INFORMATION_ONLY",
]
RepairClass = Literal[
    "SAFE_CANDIDATE",
    "CONFIRMATION_REQUIRED",
    "EXPERT_REVIEW",
    "INFORMATION_ONLY",
]
FormulaPatternType = Literal[
    "DOMINANT_NORMALIZED_PATTERN_OUTLIER",
    "FORMULA_GAP_OR_CONSTANT",
]
FormulaPatternSubtype = Literal[
    "FUNCTION_PATTERN_DRIFT",
    "REFERENCE_SHEET_DRIFT",
    "REFERENCE_CELL_DRIFT",
    "RELATIVE_REFERENCE_DRIFT",
    "ABSOLUTE_REFERENCE_DRIFT",
    "RANGE_BOUNDARY_DRIFT",
    "CONSTANT_OVERRIDE_CANDIDATE",
    "BLANK_GAP_CANDIDATE",
    "GENERIC_PATTERN_DRIFT",
]
FormulaAuditStatus = Literal[
    "COMPLETED",
    "ABSTAINED_INSUFFICIENT_EVIDENCE",
    "SKIPPED_TRUNCATED",
    "SKIPPED_FORMULA_LIMIT",
    "SKIPPED_WORKBOOK_LIMIT",
    "SKIPPED_CANDIDATE_LIMIT",
    "SKIPPED_UNSUPPORTED_STRUCTURE",
    "FAILED",
]


class RepairReadiness(BaseModel):
    """Future repair path derived from an existing repair classification.

    This is not an instruction to change a workbook and never means a repair is
    currently available.
    """

    status: RepairReadinessStatus
    label: str
    explanation: str
    required_steps: list[str]
    planned_service_codes: list[str] = Field(default_factory=list)


class FindingGuidance(BaseModel):
    evidence_grade: EvidenceGrade
    action_category: ActionCategory
    repair_eligibility: RepairEligibility
    user_confirmation_required: bool
    detected_fact: str
    possible_impact: str
    how_to_check_in_excel: list[str]
    when_it_may_be_normal: list[str]
    when_action_is_recommended: list[str]
    recommended_next_action: str
    unchecked_scope: list[str]
    recommended_next_checks: list[str]
    recommended_service_code: str | None = None
    repair_readiness: RepairReadiness | None = None


class FormulaPatternEvidence(BaseModel):
    """Value-free evidence for an internal M4-A formula-pattern candidate.

    It deliberately contains no formula text, cell values, sheet name, or
    proposed replacement. Locations are relative to the Finding's sheet.
    """

    pattern_type: FormulaPatternType
    formula_region: str
    dominant_pattern_id: str
    current_pattern_id: str | None = None
    neighbor_count: int
    evidence_locations: list[str]
    detection_basis: str
    current_limitations: list[str]
    # These optional, value-free summaries are populated only by M4-A.5.
    # Keeping them optional preserves compatibility with existing M4-A payloads.
    pattern_subtype: FormulaPatternSubtype | None = None
    evidence_summary: str | None = None
    dominant_pattern_summary: str | None = None
    current_pattern_summary: str | None = None
    comparison_locations: list[str] = Field(default_factory=list)
    normal_case_possibility: str | None = None


class Finding(BaseModel):
    id: str
    finding_key: str | None = None
    rule_code: str
    severity: Severity
    title: str
    description: str
    sheet: str | None = None
    cell: str | None = None
    confidence: float = Field(ge=0, le=1)
    repair_class: RepairClass
    formula_pattern: FormulaPatternEvidence | None = None
    guidance: FindingGuidance | None = None


class WorkbookSummary(BaseModel):
    sheet_count: int
    hidden_sheet_count: int
    very_hidden_sheet_count: int
    formula_count: int
    merged_range_count: int
    external_link_count: int
    defined_name_count: int
    drawing_part_count: int
    has_macros: bool
    scanned_cell_count: int
    scan_truncated: bool


class DiagnosisSummary(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_band: Literal["low", "moderate", "high", "critical"]
    complexity_score: int = Field(ge=0)
    complexity_band: Literal["basic", "standard", "advanced", "expert"]
    issue_count: int
    critical_count: int
    warning_count: int
    info_count: int
    safe_candidate_count: int
    confirmation_required_count: int
    expert_review_count: int
    information_only_count: int = 0
    repair_review_candidate_count: int = 0


class QuotePreview(BaseModel):
    status: Literal["AVAILABLE", "EXPERT_REVIEW"]
    tier: Literal["AUDIT", "BASIC", "STANDARD", "ADVANCED", "EXPERT"]
    currency: Literal["KRW"] = "KRW"
    amount: int | None
    headline: str
    included: list[str]
    excluded: list[str]
    factors: list[str]
    amount_min: int | None = None
    amount_max: int | None = None
    pricing_note: str | None = None
    service_code: str | None = None
    service_status: str | None = None
    planned_deliverables: list[str] = Field(default_factory=list)


class ScanResult(BaseModel):
    analysis_id: str
    filename: str
    file_size_bytes: int
    scanned_at: datetime
    scanner_version: str
    rule_set_version: str
    workbook: WorkbookSummary
    summary: DiagnosisSummary
    findings: list[Finding]
    quote: QuotePreview
    limitations: list[str]


class FormulaAuditResult(BaseModel):
    """Isolated, opt-in M4 internal-beta result.

    It is deliberately not attached to ``ScanResult``: the free diagnosis has
    no server-side file retention or audit-session state, and must remain
    unchanged by an optional formula-pattern audit request.
    """

    status: FormulaAuditStatus
    formula_cell_count: int = Field(ge=0)
    audited_sheet_count: int = Field(ge=0)
    audited_formula_region_count: int = Field(ge=0)
    candidates: list[Finding] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    elapsed_ms: int | None = Field(default=None, ge=0)
    scanner_version: str
    rule_set_version: str


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
