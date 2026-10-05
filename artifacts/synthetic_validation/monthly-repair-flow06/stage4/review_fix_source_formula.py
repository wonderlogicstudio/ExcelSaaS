from pathlib import Path
p=Path('apps/web/src/lib/repairReview.ts')
s=p.read_text(encoding='utf-8')
s=s.replace("const match = formula.toUpperCase().match(/^=([A-Z]{1,3})([1-9][0-9]{0,6})-\x01([1-9][0-9]{0,6})$/);", "const match = formula.toUpperCase().match(/^=([A-Z]{1,3})([1-9][0-9]{0,6})-\\1([1-9][0-9]{0,6})$/);")
p.write_text(s,encoding='utf-8',newline='\n')

p=Path('apps/web/src/components/RepairProposalPicker.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("import { monthlyBeforeFormula, type RepairDraft, type ReviewSelection } from '../lib/repairReview';", "import { monthlyFormulaFromText, type RepairDraft, type ReviewSelection } from '../lib/repairReview';")
s=s.replace("  const first = proposal.findings.find(f => f.cell === targets[0]) ?? proposal.findings[0];\n  const beforeFormula = proposal.profile === RP03 ? monthlyBeforeFormula(first) : undefined;", "  const first = proposal.findings.find(f => f.cell === targets[0]) ?? proposal.findings[0];")
s=s.replace("  const source = cells.find(c => c.cell === first.cell), formula = cells.find(c => c.cell === anchor && c.type === 'formula');", "  const source = cells.find(c => c.cell === first.cell), formula = cells.find(c => c.cell === anchor && c.type === 'formula');\n  const beforeFormula = proposal.profile === RP03 && source?.type === 'formula' ? monthlyFormulaFromText(source.text) : undefined;")
needle="""    <p className=\"sr-only\" aria-live=\"polite\" aria-atomic=\"true\">{notice}</p>
"""
replacement="""    <p className=\"sr-only\" aria-live=\"polite\" aria-atomic=\"true\">{notice}</p>
    {notice.includes('월별') && <p className=\"proposal-basket-warning\" role=\"status\">{notice}</p>}
"""
if needle not in s:
    raise SystemExit('notice needle not found')
s=s.replace(needle,replacement)
p.write_text(s,encoding='utf-8',newline='\n')
