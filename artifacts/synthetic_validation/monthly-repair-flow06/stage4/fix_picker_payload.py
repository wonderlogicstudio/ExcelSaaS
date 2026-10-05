from pathlib import Path
p=Path('apps/web/src/components/RepairProposalPicker.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("const basketRemoveLabel=(item:BasketItem)=>`${item.draft.sheet} ${item.draft.targets[0]?.replace(/[0-9].*$/,'') || ''}의 ${item.kindLabel} ${item.cellCount}곳 제외`;", "const basketRemoveLabel=(item:BasketItem)=>`${item.draft.sheet} ${item.draft.targets[0]?.replace(/[0-9].*$/,'') || ''}열 ${item.kindLabel} ${item.cellCount}곳 제외`;")
old="""  const draft:RepairDraft={ profile: proposal.profile!, sheet: proposal.sheet, targets, role: proposal.profile === RP01 ? role : undefined, anchor: proposal.profile === RP02 ? anchor : undefined, anchor_formula: proposal.profile === RP02 ? formula?.text ?? '' : undefined, before_formula: proposal.profile === RP03 ? beforeFormula : undefined, confirmed: true, proposal: true };
"""
new="""  const draft:RepairDraft={ profile: proposal.profile!, sheet: proposal.sheet, targets, confirmed: true, proposal: true };
  if (proposal.profile === RP01) draft.role = role;
  if (proposal.profile === RP02) { draft.anchor = anchor; draft.anchor_formula = formula?.text ?? ''; }
  if (proposal.profile === RP03 && beforeFormula) draft.before_formula = beforeFormula;
"""
if old not in s:
    raise SystemExit('draft line not found')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8',newline='\n')
