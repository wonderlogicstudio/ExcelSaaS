import { cleanup, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ProposalExample } from './ProposalExample';
import type { DeliveryJob } from './DeliveryWorkspace';
import type { PlanDetail } from './RepairPlanPreview';
import { noRepairIntent, RP01, RP02 } from '../lib/repairProposals';

const combined = 'COMBINED_RP01_RP02_REPAIR_V1';

const job: DeliveryJob = {
  job_id: 'examples-01',
  revision: 1,
  status: 'PREVIEW_VALIDATED',
  source_hash: 'synthetic',
  expires_at: Date.now() / 1000 + 600,
  sheets: [{ name: '정산', cell_count: 20 }],
  purchase_enabled: false,
  source_unchanged: true,
  preflight: null,
  policy: {
    profile: combined,
    confirmed: true,
    items: [
      { profile: RP01, sheet: '정산', targets: ['B2', 'B3'], role: 'AMOUNT', confirmed: true },
      { profile: RP02, sheet: '정산', targets: ['F3'], anchor: 'F2', anchor_formula: '=C2*D2', confirmed: true },
    ],
  },
};

const detail: PlanDetail = {
  digest: 'examples-01',
  expires_at: Date.now() / 1000 + 600,
  patches: [
    { candidate_id: 'n1', sheet: '정산', cell: 'B2', profile_version: RP01, before: { type: 'text', value: '1,200' }, after: { type: 'number', value: 1200 } },
    { candidate_id: 'n2', sheet: '정산', cell: 'B3', profile_version: RP01, before: { type: 'text', value: '2,300' }, after: { type: 'number', value: 2300 } },
    { candidate_id: 'f1', sheet: '정산', cell: 'F3', profile_version: RP02, before: { type: 'blank', value: null }, after: { type: 'formula', value: '=C3*D3' } },
  ],
  impact: [
    { sheet: '정산', cell: 'B2', before: { type: 'text', value: '1,200' }, after: { type: 'number', value: 1200 } },
    { sheet: '정산', cell: 'B3', before: { type: 'text', value: '2,300' }, after: { type: 'number', value: 2300 } },
    { sheet: '정산', cell: 'F3', before: { type: 'number', value: 0 }, after: { type: 'number', value: 12 } },
    { sheet: '정산', cell: 'J10', before: { type: 'number', value: 20 }, after: { type: 'number', value: 3512 } },
  ],
};

describe('ProposalExample', () => {
  afterEach(cleanup);

  it('shows one representative for each selected repair type and upfront type/cell totals', () => {
    render(<ProposalExample detail={detail} job={job} intent={noRepairIntent} />);
    const region = screen.getByRole('region', { name: '대표 수정 예시' });

    expect(within(region).getByText('2종류 · 총 3곳 수정 예정', { exact: false })).toBeVisible();
    expect(within(region).getByText('숫자 텍스트 정리 2곳', { exact: false })).toBeVisible();
    expect(within(region).getByText('빈 셀 수식 복원 1곳', { exact: false })).toBeVisible();
    expect(within(region).getAllByText(/대표 예시/)).toHaveLength(2);
    expect(within(region).getByText('정산 · B2', { exact: false })).toBeVisible();
    expect(within(region).getByText('정산 · F3', { exact: false })).toBeVisible();
    expect(within(region).queryByText('정산 · B3', { exact: false })).not.toBeInTheDocument();
    expect(within(region).getByText('12')).toBeVisible();
  });

  it('shows a single representative and one-type summary for a single repair type', () => {
    render(<ProposalExample detail={{ ...detail, patches: detail.patches.slice(0, 2), impact: detail.impact.slice(0, 2) }} job={{ ...job, policy: { profile: RP01, sheet: '정산', targets: ['B2', 'B3'], role: 'AMOUNT', confirmed: true } }} intent={noRepairIntent} />);
    const region = screen.getByRole('region', { name: '대표 수정 예시' });

    expect(within(region).getByText('1종류 · 총 2곳 수정 예정', { exact: false })).toBeVisible();
    expect(within(region).getAllByText(/대표 예시/)).toHaveLength(1);
  });

  it('prefers the requested cell inside its own repair type while keeping one representative per type', () => {
    render(<ProposalExample detail={detail} job={job} intent={{ ...noRepairIntent, enabled: true, sheet: '정산', cell: 'B3', expected: '2300' }} />);
    const region = screen.getByRole('region', { name: '대표 수정 예시' });

    expect(within(region).getByText('정산 · B3', { exact: false })).toBeVisible();
    expect(within(region).getByText('정산 · F3', { exact: false })).toBeVisible();
    expect(within(region).queryByText('정산 · B2', { exact: false })).not.toBeInTheDocument();
    expect(within(region).getByText('원하는 결과와 대조 완료')).toBeVisible();
  });

  it('does not invent a computed formula result when the plan detail lacks one', () => {
    const noFormulaImpact = { ...detail, impact: detail.impact.filter(i => i.cell !== 'F3') };
    render(<ProposalExample detail={noFormulaImpact} job={job} intent={noRepairIntent} />);
    const region = screen.getByRole('region', { name: '대표 수정 예시' });

    expect(within(region).getByText('계산 결과를 확인하지 못함')).toBeVisible();
    expect(within(region).getByText('이 예시 셀의 계산 결과는 아직 확인하지 못했습니다.', { exact: false })).toBeVisible();
    expect(within(region).queryByText('12')).not.toBeInTheDocument();
  });
});
