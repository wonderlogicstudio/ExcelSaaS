export type Severity = 'critical' | 'warning' | 'info';
export type EvidenceGrade = 'DIRECT_CONFIRMATION' | 'PATTERN_INFERENCE' | 'REFERENCE_SIGNAL';
export type ActionCategory =
  | 'FIX_RECOMMENDED'
  | 'USER_CONFIRMATION'
  | 'DEEP_VALIDATION_REQUIRED'
  | 'INFO_ONLY';
export type RepairEligibility =
  | 'MANUAL_GUIDANCE_AVAILABLE'
  | 'USER_CONFIRMATION_REQUIRED'
  | 'EXPERT_REVIEW_REQUIRED'
  | 'CURRENTLY_NOT_SUPPORTED'
  | 'NOT_APPLICABLE';
export type FindingUserStatus =
  | 'UNREVIEWED'
  | 'REVIEWED'
  | 'PLANNED_REPAIR'
  | 'IGNORED'
  | 'MARKED_NORMAL';
export type RepairReadinessStatus =
  | 'REPAIR_CANDIDATE_AFTER_APPROVAL'
  | 'USER_DECISION_REQUIRED'
  | 'PRECISION_VERIFICATION_REQUIRED'
  | 'INFORMATION_ONLY';
export type RepairClass =
  | 'SAFE_CANDIDATE'
  | 'CONFIRMATION_REQUIRED'
  | 'EXPERT_REVIEW'
  | 'INFORMATION_ONLY';
export type FormulaPatternType =
  | 'DOMINANT_NORMALIZED_PATTERN_OUTLIER'
  | 'FORMULA_GAP_OR_CONSTANT';
export type FormulaPatternSubtype =
  | 'FUNCTION_PATTERN_DRIFT'
  | 'REFERENCE_SHEET_DRIFT'
  | 'REFERENCE_CELL_DRIFT'
  | 'RELATIVE_REFERENCE_DRIFT'
  | 'ABSOLUTE_REFERENCE_DRIFT'
  | 'RANGE_BOUNDARY_DRIFT'
  | 'CONSTANT_OVERRIDE_CANDIDATE'
  | 'BLANK_GAP_CANDIDATE'
  | 'GENERIC_PATTERN_DRIFT';
export type FormulaAuditStatus =
  | 'COMPLETED'
  | 'ABSTAINED_INSUFFICIENT_EVIDENCE'
  | 'SKIPPED_TRUNCATED'
  | 'SKIPPED_FORMULA_LIMIT'
  | 'SKIPPED_WORKBOOK_LIMIT'
  | 'SKIPPED_CANDIDATE_LIMIT'
  | 'SKIPPED_UNSUPPORTED_STRUCTURE'
  | 'FAILED';

export interface FindingGuidance {
  evidence_grade: EvidenceGrade;
  action_category: ActionCategory;
  repair_eligibility: RepairEligibility;
  user_confirmation_required: boolean;
  detected_fact: string;
  possible_impact: string;
  how_to_check_in_excel: string[];
  when_it_may_be_normal: string[];
  when_action_is_recommended: string[];
  recommended_next_action: string;
  unchecked_scope: string[];
  recommended_next_checks: string[];
  recommended_service_code?: string | null;
  repair_readiness?: RepairReadiness | null;
}

export interface RepairReadiness {
  status: RepairReadinessStatus;
  label: string;
  explanation: string;
  required_steps: string[];
  planned_service_codes: string[];
}

export interface Finding {
  id: string;
  finding_key?: string | null;
  rule_code: string;
  severity: Severity;
  title: string;
  description: string;
  sheet?: string | null;
  cell?: string | null;
  confidence: number;
  repair_class: RepairClass;
  formula_pattern?: FormulaPatternEvidence | null;
  guidance?: FindingGuidance | null;
}

export interface FormulaPatternEvidence {
  pattern_type: FormulaPatternType;
  formula_region: string;
  dominant_pattern_id: string;
  current_pattern_id?: string | null;
  neighbor_count: number;
  evidence_locations: string[];
  detection_basis: string;
  current_limitations: string[];
  pattern_subtype?: FormulaPatternSubtype | null;
  evidence_summary?: string | null;
  dominant_pattern_summary?: string | null;
  current_pattern_summary?: string | null;
  comparison_locations?: string[];
  normal_case_possibility?: string | null;
}

export interface WorkbookSummary {
  sheet_count: number;
  hidden_sheet_count: number;
  very_hidden_sheet_count: number;
  formula_count: number;
  merged_range_count: number;
  external_link_count: number;
  defined_name_count: number;
  drawing_part_count: number;
  has_macros: boolean;
  scanned_cell_count: number;
  scan_truncated: boolean;
}

export interface DiagnosisSummary {
  risk_score: number;
  risk_band: 'low' | 'moderate' | 'high' | 'critical';
  complexity_score: number;
  complexity_band: 'basic' | 'standard' | 'advanced' | 'expert';
  issue_count: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  safe_candidate_count: number;
  confirmation_required_count: number;
  expert_review_count: number;
  information_only_count?: number;
  repair_review_candidate_count?: number;
}

export interface QuotePreview {
  status: 'AVAILABLE' | 'EXPERT_REVIEW';
  tier: 'AUDIT' | 'BASIC' | 'STANDARD' | 'ADVANCED' | 'EXPERT';
  currency: 'KRW';
  amount: number | null;
  headline: string;
  included: string[];
  excluded: string[];
  factors: string[];
  amount_min?: number | null;
  amount_max?: number | null;
  pricing_note?: string | null;
  service_code?: string | null;
  service_status?: string | null;
  planned_deliverables?: string[];
}

export interface ScanResult {
  analysis_id: string;
  filename: string;
  file_size_bytes: number;
  scanned_at: string;
  scanner_version: string;
  rule_set_version: string;
  workbook: WorkbookSummary;
  summary: DiagnosisSummary;
  findings: Finding[];
  quote: QuotePreview;
  limitations: string[];
}

export interface FormulaAuditResult {
  status: FormulaAuditStatus;
  formula_cell_count: number;
  audited_sheet_count: number;
  audited_formula_region_count: number;
  candidates: Finding[];
  limitations: string[];
  elapsed_ms?: number | null;
  scanner_version: string;
  rule_set_version: string;
}

export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
  };
  detail?: string;
}
