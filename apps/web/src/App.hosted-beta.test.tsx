import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { demoResult } from './data/demo';

const base = {
  ...demoResult, findings: [],
  summary: { ...demoResult.summary, issue_count: 0 },
  workbook: { ...demoResult.workbook, formula_count: 12, scan_truncated: false },
};
function audit(cell = 'C4', count = 1) {
  return {
    status: 'COMPLETED', formula_cell_count: 12, audited_sheet_count: 1,
    audited_formula_region_count: 2, elapsed_ms: 1, limitations: [],
    scanner_version: '0.1.3', rule_set_version: '2026.09.5',
    candidates: Array.from({ length: count }, (_, i) => ({
      ...demoResult.findings[0], id: `${cell}-${i}`, finding_key: `${cell}-${i}`,
      title: `검토 후보 ${cell}`, rule_code: 'FORMULA_PATTERN_OUTLIER',
      sheet: 'Pattern', cell: i === 0 ? cell : `D${i + 2}`,
    })),
  };
}
function ok(value: unknown) {
  return { ok: true, status: 200, json: async () => value } as Response;
}
function upload(name = 'synthetic.xlsx') {
  const file = new File(['synthetic only'], name);
  fireEvent.change(screen.getByLabelText('엑셀 파일 선택'), { target: { files: [file] } });
  return file;
}
async function start(fetcher: typeof fetch, productEnv = 'hosted_beta') {
  vi.stubEnv('VITE_FORMULA_AUDIT_HOSTED_BETA_ENABLED', 'true');
  vi.stubEnv('VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED', 'false');
  vi.stubEnv('VITE_PRODUCT_ENV', productEnv);
  vi.stubGlobal('fetch', fetcher);
  const { default: App } = await import('./App');
  render(<App />);
}

describe('approved protected-beta M4 upload flow', () => {
  afterEach(() => { cleanup(); vi.unstubAllEnvs(); vi.unstubAllGlobals(); vi.resetModules(); });

  it('automatically checks the same file and shows four pattern candidates in one results list', async () => {
    const fetcher = vi.fn(async (url) => ok(String(url).endsWith('/formula-audits') ? audit('C4', 4) : base));
    await start(fetcher);
    const file = upload();
    await waitFor(() => expect(document.querySelectorAll('.formula-audit-finding')).toHaveLength(4));
    expect(fetcher).toHaveBeenCalledTimes(2);
    for (const [, init] of fetcher.mock.calls as unknown as [string, RequestInit][]) {
      expect((init.body as FormData).get('file')).toBe(file);
    }
    expect(screen.getByRole('heading', { name: '확인할 항목 4건' })).toBeInTheDocument();
    expect(screen.getByText('구조 위험 0건 · 수식 검토 후보 4건')).toBeInTheDocument();
    expect(document.querySelectorAll('#results .findings-panel')).toHaveLength(1);
    expect(document.querySelector('#formula-audit')).toBeNull();
    expect(document.querySelector('#results .finding-group__locations')).not.toHaveAttribute('open');
    expect(screen.queryByRole('button', { name: '도움이 됨' })).not.toBeInTheDocument();
  });

  it('keeps a failed audit visible without replacing the successful free result', async () => {
    await start(vi.fn(async (url) => String(url).endsWith('/formula-audits')
      ? { ok: false, status: 503, json: async () => ({ error: { code: 'SYNTHETIC', message: '검사 연결 실패' } }) } as Response
      : ok(base)));
    upload();
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('검사 연결 실패'));
    expect(screen.getByRole('heading', { name: '완료한 검사 범위에서 발견 0건' })).toBeInTheDocument();
    expect(screen.queryByText('후보 없음')).not.toBeInTheDocument();
  });

  it('discards an older audit after a new file was uploaded', async () => {
    let finishOld!: (value: Response) => void;
    const oldAudit = new Promise<Response>((resolve) => { finishOld = resolve; });
    let audits = 0;
    await start(vi.fn(async (url) => {
      if (!String(url).endsWith('/formula-audits')) return ok(base);
      audits += 1;
      return audits === 1 ? oldAudit : ok(audit('F8'));
    }));
    upload('first-synthetic.xlsx');
    await waitFor(() => expect(audits).toBe(1));
    expect(screen.getByLabelText('엑셀 파일 선택')).toBeDisabled();
    expect(screen.getByText('수식 패턴 확인')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '수식 패턴을 확인하고 있습니다' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '다른 파일 검사' }));
    upload('second-synthetic.xlsx');
    await waitFor(() => expect(screen.getByText('Pattern · F8')).toBeInTheDocument());
    finishOld(ok(audit('C4')));
    await waitFor(() => expect(screen.queryByText('Pattern · C4')).not.toBeInTheDocument());
    expect(screen.getByText('Pattern · F8')).toBeInTheDocument();
  });

  it('discards a pending audit when the result is reset', async () => {
    let finish!: (value: Response) => void;
    const pending = new Promise<Response>((resolve) => { finish = resolve; });
    let auditRequested = false;
    await start(vi.fn(async (url) => {
      if (!String(url).endsWith('/formula-audits')) return ok(base);
      auditRequested = true;
      return pending;
    }));
    upload();
    await waitFor(() => expect(auditRequested).toBe(true));
    fireEvent.click(screen.getByRole('button', { name: '다른 파일 검사' }));
    finish(ok(audit()));
    await waitFor(() => expect(document.querySelector('#formula-audit')).toBeNull());
    expect(document.querySelector('#results')).toBeNull();
  });

  it('does not activate hosted automatic M4 for a production build', async () => {
    const fetcher = vi.fn(async () => ok(base));
    await start(fetcher, 'production');
    upload();
    await waitFor(() => expect(screen.getByRole('heading', { name: '무료 구조 검사: 발견 0건' })).toBeInTheDocument());
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(document.querySelector('#formula-audit')).toBeNull();
  });

  it('does not automatically audit a truncated free scan', async () => {
    const fetcher = vi.fn(async () => ok({ ...base, workbook: { ...base.workbook, scan_truncated: true } }));
    await start(fetcher);
    upload();
    await waitFor(() => expect(screen.getByText('기본 무료 진단이 일부 셀만 검사해 이번 수식 패턴 정밀검사는 실행하지 않습니다.')).toBeInTheDocument());
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
