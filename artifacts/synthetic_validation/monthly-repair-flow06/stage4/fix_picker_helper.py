from pathlib import Path
p=Path('apps/web/src/components/RepairProposalPicker.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("const isMonthly=(item:BasketItem|RepairDraft)=>item.draft ? item.draft.profile===RP03 : item.profile===RP03;", "const isMonthlyItem=(item:BasketItem)=>item.draft.profile===RP03;\nconst isMonthlyDraft=(draft:RepairDraft)=>draft.profile===RP03;")
s=s.replace('if (isMonthly(item) && old.some(existing=>existing.id!==item.id))', 'if (isMonthlyItem(item) && old.some(existing=>existing.id!==item.id))')
s=s.replace('if (!isMonthly(item) && old.some(isMonthly))', 'if (!isMonthlyItem(item) && old.some(isMonthlyItem))')
s=s.replace('basket.length>1&&basket.some(isMonthly)', 'basket.length>1&&basket.some(isMonthlyItem)')
p.write_text(s,encoding='utf-8')
