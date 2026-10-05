from pathlib import Path
p=Path('apps/web/src/components/RepairProposalPicker.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace('    {notice && <p className="proposal-basket-warning" role="status">{notice}</p>}\n','')
p.write_text(s,encoding='utf-8',newline='\n')
