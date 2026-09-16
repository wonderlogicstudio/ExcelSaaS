import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { demoResult } from './data/demo';
import type { Finding } from './types';
import type { DeliveryJob } from './components/DeliveryWorkspace';

const api = vi.hoisted(() => {
  class ScanApiError extends Error {}
  return { scanWorkbook: vi.fn(), runFormulaAudit: vi.fn(), resolveApiBaseUrl: vi.fn(() => ''), ScanApiError };
});
const evidence = vi.hoisted(() => ({ readSourceCells: vi.fn(), readSourceSheets: vi.fn() }));

vi.mock('./lib/api', () => api);
vi.mock('./lib/workbookEvidence', () => evidence);

const ok = (value: unknown) => ({ ok: true, json: async () => value } as Response);
const finding = (cell: string) => ({
  ...demoResult.findings[0],
  sheet: '정산',
  cell,
  rule_code: 'NUMBER_STORED_AS_TEXT',
  formula_pattern: null,
} as Finding);
const baseJob: DeliveryJob = {
  job_id: 'same-source-job',
  revision: 1,
  source_hash: 'source-hash',
  status: 'INPUT_READY',
  expires_at: Date.now() / 1000 + 900,
  sheets: [{ name: '정산', cell_count: 10 }],
  preflight: null,
  purchase_enabled: false,
  source_unchanged: true,
};
const planJob: DeliveryJob = {
  ...baseJob,
  revision: 3,
  status: 'PREVIEW_VALIDATED',
  entitlement_active: true,
  repair_execution_available: true,
  preflight: { status: 'PRELIMINARY_ONLY', eligible_count: 1, reason_codes: [], targets: [], purchase_enabled: false },
  plan_summary: { digest: 'plan-a', status: 'PREVIEW_VALIDATED', patch_count: 1, impact_count: 1, formula_impact_count: 0, coverage: { formula_count: 0 }, reference: { status: 'PASS', case_count: 1 } },
};

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe('App proposal reselection flow', () => {
  it('restarts proposal selection without deleting or reuploading the retained delivery job', async () => {
    vi.stubEnv('VITE_PRODUCT_ENV', 'internal_beta');
    vi.stubEnv('VITE_DELIVERY_BETA_ENABLED', 'true');
    vi.stubEnv('VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED', 'false');
    vi.stubEnv('VITE_FORMULA_AUDIT_HOSTED_BETA_ENABLED', 'false');
    api.scanWorkbook.mockResolvedValue({
      ...demoResult,
      analysis_id: 'analysis-reselect',
      filename: 'synthetic.xlsx',
      findings: [finding('B2'), finding('B3')],
      summary: { ...demoResult.summary, issue_count: 2, safe_candidate_count: 2, repair_review_candidate_count: 2 },
    });
    evidence.readSourceSheets.mockResolvedValue(['정산']);
    evidence.readSourceCells.mockResolvedValue([{ cell: 'B2', type: 'text', text: '1,200' }]);
    const actions: Record<string, any>[] = [];
    let revision = 2;
    let currentPolicy: unknown;
    vi.stubGlobal('fetch', vi.fn(async (_url, init) => {
      const action = JSON.parse(String(init?.body));
      actions.push(action);
      if (action.action === 'capabilities') return ok({ max_bytes: 2_097_152, payment_mode: 'OFF' });
      if (action.action === 'create_input') return ok({ ...baseJob, job_id: 'same-source-job', revision: revision++ });
      if (action.action === 'preflight') {
        currentPolicy = action.policy;
        return ok({ ...baseJob, job_id: action.job_id, revision: revision++, policy: action.policy, preflight: planJob.preflight });
      }
      if (action.action === 'prepare_plan') return ok({ ...planJob, job_id: action.job_id, revision: revision++, policy: currentPolicy, plan_summary: { ...planJob.plan_summary!, digest: `plan-${revision}` } });
      return ok(planJob);
    }));

    const { default: App } = await import('./App');
    const view = render(<App />);
    fireEvent.change(view.container.querySelector<HTMLInputElement>('input[type="file"]')!, { target: { files: [new File(['synthetic'], 'synthetic.xlsx')] } });
    fireEvent.click(await screen.findByRole('button', { name: '시트별 수정 제안 보기' }));
    await screen.findByRole('heading', { name: '어떤 시트의 수정 제안을 볼까요?' });
    fireEvent.click(view.container.querySelector('.proposal-option button')!);
    const details = await screen.findByRole('region', { name: /정산 B열 제안/ });
    fireEvent.click(within(details).getByLabelText('B3'));
    fireEvent.click(details.querySelector<HTMLInputElement>('input[value="AMOUNT"]')!);
    fireEvent.click(details.querySelector<HTMLInputElement>('.delivery-check input[type="checkbox"]')!);
    fireEvent.click(within(details).getByRole('button', { name: '이 제안으로 수정 예시 확인' }));
    fireEvent.click(await screen.findByRole('checkbox', { name: /업로드 권한/ }));
    fireEvent.click(screen.getByRole('button', { name: /원본으로 수정 범위 확인/ }));
    await waitFor(() => expect(actions.filter(action => action.action === 'prepare_plan')).toHaveLength(1));

    fireEvent.click(screen.getByRole('button', { name: '다른 제안으로 다시 선택' }));
    await screen.findByRole('heading', { name: '어떤 시트의 수정 제안을 볼까요?' });
    fireEvent.click(within(details).getByLabelText('B3'));
    fireEvent.click(details.querySelector<HTMLInputElement>('.delivery-check input[type="checkbox"]')!);
    fireEvent.click(within(details).getByRole('button', { name: '이 제안으로 수정 예시 확인' }));

    await waitFor(() => expect(actions.filter(action => action.action === 'prepare_plan')).toHaveLength(2));
    expect(actions.filter(action => action.action === 'delete')).toHaveLength(0);
    expect(actions.filter(action => action.action === 'create_input')).toHaveLength(1);
    expect(actions.filter(action => action.action === 'preflight').map(action => action.job_id)).toEqual(['same-source-job', 'same-source-job']);
    expect(actions.filter(action => action.action === 'preflight').at(-1)?.policy).toMatchObject({ targets: ['B2', 'B3'] });
  });
});
