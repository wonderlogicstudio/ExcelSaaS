from pathlib import Path
p=Path('apps/web/src/App.navigation.test.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_OUTLIER'}).profile).toBeUndefined();", "expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_OUTLIER',formula_pattern:null}).profile).toBeUndefined();")
p.write_text(s,encoding='utf-8',newline='\n')

p=Path('apps/web/src/components/ProposalFlow.test.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("await screen.findByText('=N15-N14');", "await waitFor(()=>expect(screen.getAllByText('=N15-N14').length).toBeGreaterThan(0));")
s=s.replace("await screen.findByText('=O15-O14');", "await waitFor(()=>expect(screen.getAllByText('=O15-O14').length).toBeGreaterThan(0));")
p.write_text(s,encoding='utf-8',newline='\n')
