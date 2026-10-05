from pathlib import Path
p=Path('apps/web/src/components/ProposalExample.test.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace("import { noRepairIntent, RP01, RP02 } from '../lib/repairProposals';", "import { noRepairIntent, RP01, RP02, RP03 } from '../lib/repairProposals';")
insert=r'''

  it('shows monthly examples from backend-calculated impact without product hardcoding the value', () => {
    const monthlyJob = { ...job, policy: { profile: RP03, sheet: 'Budget', targets: ['N18'], before_formula: '=N15-N14', confirmed: true } } as DeliveryJob;
    const monthlyDetail: PlanDetail = {
      digest: 'monthly-01',
      expires_at: Date.now() / 1000 + 600,
      patches: [{ candidate_id: 'm1', sheet: 'Budget', cell: 'N18', profile_version: RP03, change_kind: 'MONTHLY_FORMULA_REPLACEMENT', before: { type: 'error', value: '#VALUE!' }, after: { type: 'formula', value: "='M10'!B16-'M10'!B15" } }],
      impact: [{ sheet: 'Budget', cell: 'N18', before: { type: 'error', value: '#VALUE!' }, after: { type: 'number', value: -5 } }],
    };
    render(<ProposalExample detail={monthlyDetail} job={monthlyJob} intent={noRepairIntent} />);
    const region = screen.getByRole('region', { name: '대표 수정 예시' });

    expect(within(region).getByText(/월별 수식 검증/)).toBeVisible();
    expect(within(region).getByText('-5')).toBeVisible();
  });
'''
marker='\n});\n'
idx=s.rfind(marker)
if idx==-1:
    raise SystemExit('proposal example end not found')
s=s[:idx]+insert+s[idx:]
p.write_text(s,encoding='utf-8',newline='\n')
