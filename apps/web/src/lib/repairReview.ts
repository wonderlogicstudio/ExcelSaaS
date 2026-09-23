import type { Finding } from '../types';

export const RP03 = 'RP03_MONTHLY_SHEET_FORMULA_REPLACEMENT_V1';

export type RepairDraft = {
  profile: string;
  sheet: string;
  targets: string[];
  role?: string;
  anchor?: string;
  anchor_formula?: string;
  before_formula?: string;
  confirmed?: boolean;
  proposal?: boolean;
  items?: RepairDraft[];
};

export const reviewKey = (finding: Finding) => JSON.stringify([finding.rule_code, finding.sheet, finding.cell]);

export function monthlyFormulaFromText(raw: string | undefined | null): string | undefined {
  if (typeof raw !== 'string') return undefined;
  const formula = raw.trim();
  if (!formula || /[!'[\]]/.test(formula)) return undefined;
  const match = formula.toUpperCase().match(/^=([A-Z]{1,3})([1-9][0-9]{0,6})-\1([1-9][0-9]{0,6})$/);
  return match ? formula : undefined;
}


export function reviewDisposition(finding: Finding): { label: string; profile?: string } {
  const cell = Boolean(finding.sheet && finding.cell && /^[A-Z]+[1-9][0-9]*$/.test(finding.cell));
  if (cell && finding.rule_code === 'NUMBER_STORED_AS_TEXT') return { label: '수정 제안 후보 · 계산에 쓸 금액·개수인지 확인', profile: 'RP01_NUMERIC_TEXT_FIELD_V1' };
  if (cell && finding.rule_code === 'FORMULA_PATTERN_GAP' && finding.formula_pattern?.pattern_subtype === 'BLANK_GAP_CANDIDATE') return { label: '수정 후보 · 기준 수식 확인 필요', profile: 'RP02_APPROVED_FORMULA_RESTORE_V1' };
  if (cell && finding.rule_code === 'FORMULA_PATTERN_OUTLIER' && finding.formula_pattern?.pattern_subtype === 'REFERENCE_SHEET_DRIFT') return { label: '월별 수식 검증 필요 · 서버에서 재계산 확인', profile: RP03 };
  if (finding.rule_code === 'FORMULA_PATTERN_OUTLIER') return { label: '수식 비교 제공 · 현재 자동 수정 미지원' };
  if (finding.repair_class === 'INFORMATION_ONLY') return { label: '정보 제공 · 직접 확인 가능' };
  if (finding.guidance?.action_category === 'USER_CONFIRMATION') return { label: '사용자 판단 필요 · 현재 자동 수정 미지원' };
  return { label: '업무 기준 확인 필요 · 현재 자동 수정 미지원' };
}

export type ReviewSelection = { findings: Finding[]; locked: boolean; toggle: (finding: Finding) => void };
