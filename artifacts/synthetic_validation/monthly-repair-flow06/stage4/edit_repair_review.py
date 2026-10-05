from pathlib import Path
p=Path('apps/web/src/components/RepairReview.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("import { reviewDisposition, reviewKey, type RepairDraft, type ReviewSelection } from '../lib/repairReview';", "import { monthlyBeforeFormula, reviewDisposition, reviewKey, RP03, type RepairDraft, type ReviewSelection } from '../lib/repairReview';")
s=s.replace("const key = JSON.stringify([disposition.profile, f.sheet]), group = groups.get(key) ?? { profile: disposition.profile, sheet: f.sheet, targets: [] };\n    if (!group.targets.includes(f.cell)) group.targets.push(f.cell); groups.set(key, group);", "const key = JSON.stringify([disposition.profile, f.sheet, disposition.profile === RP03 ? f.cell : '']);\n    const group = groups.get(key) ?? { profile: disposition.profile, sheet: f.sheet, targets: [], before_formula: disposition.profile === RP03 ? monthlyBeforeFormula(f) : undefined };\n    if (!group.targets.includes(f.cell)) group.targets.push(f.cell); groups.set(key, group);")
s=s.replace("{draft.sheet} 쨌 {draft.targets.length}媛?{draft.profile.startsWith('RP01') ? '?レ옄 ?' : '鍮??'} ?섏젙 諛⑸쾿 ?뺤씤", "{draft.sheet} · {draft.targets.length}개 {draft.profile === RP03 ? '월별 수식' : draft.profile.startsWith('RP01') ? '숫자 셀' : '빈 셀'} 수정 방법 확인")
p.write_text(s,encoding='utf-8')
