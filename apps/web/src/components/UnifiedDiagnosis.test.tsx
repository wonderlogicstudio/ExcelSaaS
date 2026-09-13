import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { demoResult } from '../data/demo';
import { M25ResultsPanel } from './M25ResultsPanel';
import type { FindingUserStatus, FormulaAuditResult, ScanResult } from '../types';
import * as csv from '../lib/diagnosisCsv';

const structure = { ...demoResult.findings[0], id: 'shared-key', finding_key: 'shared-key', rule_code: 'FORMULA_REF_ERROR', sheet: '구조', cell: 'A1' };
const candidate = { ...structure, severity: 'warning' as const, rule_code: 'FORMULA_PATTERN_OUTLIER', title: '수식 패턴 검토 후보', sheet: '수식', cell: 'C4' };
const base: ScanResult = { ...demoResult, findings: [structure], summary: { ...demoResult.summary, issue_count: 3 }, finding_counts: { total_detected: 3, returned_details: 1, omitted_details: 2, scan_complete: true } };
const auditResult: FormulaAuditResult = { status: 'COMPLETED', formula_cell_count: 10, audited_sheet_count: 1, audited_formula_region_count: 1, candidates: [candidate], limitations: [], scanner_version: '0.1.3', rule_set_version: '2026.09.5' };
const audit = { result: auditResult, busy: false, error: null, blockedReason: null, statuses: {}, onRetry: vi.fn(), onStatusChange: vi.fn() };

describe('D01 integrated structure and pattern diagnosis', () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });
  it('uses one list with truthful combined/omitted counts and source filters across table and groups', () => {
    const before = JSON.stringify(base);
    const { container } = render(<M25ResultsPanel result={base} isDemo={false} formulaAudit={audit} onReset={vi.fn()} />);
    expect(screen.getByRole('heading', { name: '확인할 항목 4건' })).toBeInTheDocument();
    expect(screen.getByText('전체 발견 4건 · 반환 상세 2건 · 상세 생략 2건 · 필터 표시 2건')).toBeInTheDocument();
    expect(container.querySelectorAll('.findings-panel')).toHaveLength(1);
    expect(container.querySelectorAll('.finding-group')).toHaveLength(2);
    fireEvent.change(screen.getByLabelText('검사 종류'), { target: { value: 'formula' } });
    fireEvent.click(screen.getByLabelText('전체 항목 표'));
    expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(2);
    expect(within(screen.getByRole('table')).getByText('수식 검토 후보')).toBeInTheDocument();
    expect(within(screen.getByRole('table')).queryByText('FORMULA_REF_ERROR')).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('시트'), { target: { value: 'sheet:구조' } });
    expect(screen.getByText(/선택한 조건에 맞는 항목이 없습니다/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '필터 초기화' }));
    expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(3);
    expect(screen.getByText('규칙 기반 우선순위 점수 62 / 100')).toBeInTheDocument();
    expect(JSON.stringify(base)).toBe(before);
  });

  it('keeps colliding original keys and CSV isolated while handling both sources in one list', () => {
    const download = vi.spyOn(csv, 'downloadDiagnosisCsv').mockImplementation(() => undefined);
    const changes = vi.fn();
    const network = vi.spyOn(globalThis, 'fetch');
    const storage = vi.spyOn(Storage.prototype, 'setItem');
    function Stateful() {
      const [states, setStates] = useState<Record<string, FindingUserStatus>>({});
      return <M25ResultsPanel result={base} isDemo={false} onReset={vi.fn()} onStatusChange={changes}
        formulaAudit={{ ...audit, statuses: states, onStatusChange: (key, status) => setStates(current => ({ ...current, [key]: status })) }} />;
    }
    render(<Stateful />);
    fireEvent.change(screen.getByLabelText('처리 상태로 보기'), { target: { value: 'UNREVIEWED' } });
    fireEvent.click(screen.getByRole('region', { name: 'FORMULA_PATTERN_OUTLIER 유형' }).querySelector('summary')!);
    fireEvent.click(within(screen.getByRole('region', { name: 'FORMULA_PATTERN_OUTLIER 유형' })).getByText('이 유형의 메모 일괄 변경'));
    fireEvent.click(within(screen.getByRole('region', { name: 'FORMULA_PATTERN_OUTLIER 유형' })).getByRole('button', { name: '표시된 1개를 읽어봄으로 메모' }));
    expect(screen.getByLabelText('처리 상태로 보기')).toHaveFocus();
    expect(screen.getByRole('region', { name: 'FORMULA_REF_ERROR 유형' })).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'FORMULA_PATTERN_OUTLIER 유형' })).not.toBeInTheDocument();
    expect(changes).not.toHaveBeenCalled();
    fireEvent.click(screen.getAllByRole('button', { name: '진단 결과 CSV 다운로드' })[0]);
    expect(download).toHaveBeenCalledExactlyOnceWith(base, {});
    expect(network).not.toHaveBeenCalled(); expect(storage).not.toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: '이 변경계획 승인' })).not.toBeInTheDocument();
  });

  it('does not report pending, failed or skipped pattern checks as completed zero', () => {
    const zero = { ...base, findings: [], finding_counts: null, summary: { ...base.summary, issue_count: 0 } };
    const { rerender } = render(<M25ResultsPanel result={zero} isDemo={false} formulaAudit={{ ...audit, result: null, busy: true }} onReset={vi.fn()} />);
    expect(screen.getByRole('heading', { name: '수식 패턴을 확인하고 있습니다' })).toBeInTheDocument();
    expect(screen.queryByText('완료 · 검토 후보 0건')).not.toBeInTheDocument();
    rerender(<M25ResultsPanel result={zero} isDemo={false} formulaAudit={{ ...audit, result: null, error: '합성 연결 오류' }} onReset={vi.fn()} />);
    expect(screen.getByRole('alert')).toHaveTextContent('합성 연결 오류');
    fireEvent.click(screen.getByRole('button', { name: '완료하지 못한 검사 다시 시도' }));
    expect(audit.onRetry).toHaveBeenCalledOnce();
    expect(screen.queryByText('검사 완료')).not.toBeInTheDocument();
    rerender(<M25ResultsPanel result={zero} isDemo={false} formulaAudit={{ ...audit, result: { ...auditResult, status: 'SKIPPED_CANDIDATE_LIMIT' } }} onReset={vi.fn()} />);
    expect(screen.getByText('후보 수 한도로 유보')).toBeInTheDocument();
    expect(document.querySelectorAll('.formula-audit-finding')).toHaveLength(0);
    expect(screen.queryByText('완료 · 검토 후보 0건')).not.toBeInTheDocument();
  });

  it('keeps a real completed zero distinct from unperformed pattern scope', () => {
    const zero = { ...base, findings: [], finding_counts: null, summary: { ...base.summary, issue_count: 0 } };
    render(<M25ResultsPanel result={zero} isDemo={false} formulaAudit={{ ...audit, result: { ...auditResult, candidates: [] } }} onReset={vi.fn()} />);
    expect(screen.getByRole('heading', { name: '검사 범위에서 발견된 항목이 없습니다' })).toBeInTheDocument();
    expect(document.querySelector('[data-audit-status=COMPLETED]')).toHaveTextContent('완료');
    expect(screen.queryByText('수식 패턴 이탈·누락 검사')).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: '수식 패턴 정밀검사' })).not.toBeInTheDocument();
  });
});
