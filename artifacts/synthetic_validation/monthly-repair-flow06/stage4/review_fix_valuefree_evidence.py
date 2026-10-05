from pathlib import Path
p=Path('apps/web/src/types.ts')
s=p.read_text(encoding='utf-8')
for line in ["  before_formula?: string | null;\n", "  current_formula?: string | null;\n", "  formula_text?: string | null;\n"]:
    s=s.replace(line,'')
p.write_text(s,encoding='utf-8',newline='\n')

p=Path('apps/web/src/lib/repairReview.ts')
s=p.read_text(encoding='utf-8')
start=s.index('export function monthlyBeforeFormula')
end=s.index('\n\nexport function reviewDisposition', start)
helper="""export function monthlyFormulaFromText(raw: string | undefined | null): string | undefined {
  if (typeof raw !== 'string') return undefined;
  const formula = raw.trim();
  if (!formula || /[!'[\]]/.test(formula)) return undefined;
  const match = formula.toUpperCase().match(/^=([A-Z]{1,3})([1-9][0-9]{0,6})-\1([1-9][0-9]{0,6})$/);
  return match ? formula : undefined;
}
"""
s=s[:start]+helper+s[end:]
s=s.replace("if (cell && finding.rule_code === 'FORMULA_PATTERN_OUTLIER' && finding.formula_pattern?.pattern_subtype === 'REFERENCE_SHEET_DRIFT' && monthlyBeforeFormula(finding)) return { label: '월별 수식 검증 필요 · 서버에서 재계산 확인', profile: RP03 };", "if (cell && finding.rule_code === 'FORMULA_PATTERN_OUTLIER' && finding.formula_pattern?.pattern_subtype === 'REFERENCE_SHEET_DRIFT') return { label: '월별 수식 검증 필요 · 서버에서 재계산 확인', profile: RP03 };")
p.write_text(s,encoding='utf-8',newline='\n')

p=Path('apps/web/src/components/RepairReview.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("import { monthlyBeforeFormula, reviewDisposition, reviewKey, RP03, type RepairDraft, type ReviewSelection } from '../lib/repairReview';", "import { reviewDisposition, reviewKey, RP03, type RepairDraft, type ReviewSelection } from '../lib/repairReview';")
s=s.replace("    const group = groups.get(key) ?? { profile: disposition.profile, sheet: f.sheet, targets: [], before_formula: disposition.profile === RP03 ? monthlyBeforeFormula(f) : undefined };", "    const group = groups.get(key) ?? { profile: disposition.profile, sheet: f.sheet, targets: [] };")
p.write_text(s,encoding='utf-8',newline='\n')
