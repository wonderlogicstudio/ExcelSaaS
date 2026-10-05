from pathlib import Path
p=Path('apps/web/src/components/DeliveryWorkspace.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace('type DeliveryPolicyItem = {profile:string;sheet:string;targets:string[];role?:string;anchor?:string;anchor_formula?:string;confirmed?:boolean};','type DeliveryPolicyItem = {profile:string;sheet:string;targets:string[];role?:string;anchor?:string;anchor_formula?:string;before_formula?:string;confirmed?:boolean};')
s=s.replace('anchor_formula:draft.anchor_formula,confirmed:draft.confirmed===true','anchor_formula:draft.anchor_formula,before_formula:draft.before_formula,confirmed:draft.confirmed===true')
p.write_text(s,encoding='utf-8')

p=Path('apps/web/src/components/RepairPlanPreview.tsx')
s=p.read_text(encoding='utf-8')
old="""function patchKindLabel(p:{profile_version?:string;change_kind?:string;after:{type:string}}) {
  return (p.profile_version??p.change_kind)==='RP01_NUMERIC_TEXT_FIELD_V1'||p.change_kind==='TYPE_NORMALIZATION' ? '숫자 텍스트 정리' : '빈 셀 수식 복원';
}
"""
new="""function patchKindLabel(p:{profile_version?:string;change_kind?:string;after:{type:string}}) {
  const kind = p.profile_version ?? p.change_kind;
  if (kind === 'RP01_NUMERIC_TEXT_FIELD_V1' || p.change_kind === 'TYPE_NORMALIZATION') return '숫자 텍스트 정리';
  if (kind === 'RP03_MONTHLY_SHEET_FORMULA_REPLACEMENT_V1' || p.change_kind === 'MONTHLY_FORMULA_REPLACEMENT') return '월별 수식 검증';
  return '빈 셀 수식 복원';
}
"""
if old not in s:
    raise SystemExit('RepairPlanPreview pattern not found')
p.write_text(s.replace(old,new),encoding='utf-8')

p=Path('apps/web/src/components/ProposalExample.tsx')
s=p.read_text(encoding='utf-8')
old="""function patchType(p: PlanDetail['patches'][number]) {
  return (p.profile_version ?? p.change_kind) === 'RP01_NUMERIC_TEXT_FIELD_V1' || p.change_kind === 'TYPE_NORMALIZATION' ? '숫자 텍스트 정리' : '빈 셀 수식 복원';
}
"""
new="""function patchType(p: PlanDetail['patches'][number]) {
  const kind = p.profile_version ?? p.change_kind;
  if (kind === 'RP01_NUMERIC_TEXT_FIELD_V1' || p.change_kind === 'TYPE_NORMALIZATION') return '숫자 텍스트 정리';
  if (kind === 'RP03_MONTHLY_SHEET_FORMULA_REPLACEMENT_V1' || p.change_kind === 'MONTHLY_FORMULA_REPLACEMENT') return '월별 수식 검증';
  return '빈 셀 수식 복원';
}
"""
if old not in s:
    raise SystemExit('ProposalExample pattern not found')
p.write_text(s.replace(old,new),encoding='utf-8')
