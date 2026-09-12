import { cleanup, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { demoResult } from '../data/demo';
import { buildDiagnosisCsv } from '../lib/diagnosisCsv';
import type { ScanResult } from '../types';
import { M25ResultsPanel } from './M25ResultsPanel';

const zero: ScanResult = {
  ...demoResult, findings: [],
  summary: { ...demoResult.summary, issue_count: 0, critical_count: 0, warning_count: 0, info_count: 0,
    risk_score: 0, risk_band: 'low', safe_candidate_count: 0, confirmation_required_count: 0,
    expert_review_count: 0, information_only_count: 0, repair_review_candidate_count: 0 },
  workbook: { ...demoResult.workbook, sheet_count: 5, scanned_cell_count: 832, formula_count: 301,
    scan_truncated: false },
};

describe('D01 owner-reported M4 files with zero free findings', () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it('reports free counts and unperformed formula checks without inventing findings or running M4', () => {
    const fetch = vi.spyOn(globalThis, 'fetch');
    const initial = JSON.stringify(zero);
    const csv = buildDiagnosisCsv(zero, {});
    render(<M25ResultsPanel result={zero} isDemo={false} onReset={() => undefined} />);
    expect(screen.getByRole('heading', { name: '무료 구조 검사: 발견 0건' })).toBeInTheDocument();
    expect(screen.getByText('파일에서 읽은 범위: 시트 5개 · 내용이 있는 셀 832개 · 수식 문자열 301개')).toBeInTheDocument();
    const note = screen.getByRole('note', { name: '발견 0건 해석' });
    expect(note).toHaveTextContent('수식 검증을 통과했다는 뜻은 아닙니다.');
    expect(note).toHaveTextContent('수식 패턴 이탈·누락');
    expect(note).toHaveTextContent('별도 수식 검사');
    expect(screen.getByText('수식 패턴 이탈·누락 검사')).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
    expect(JSON.stringify(zero)).toBe(initial);
    expect(buildDiagnosisCsv(zero, {})).toBe(csv);
    expect(screen.getByText('규칙 기반 우선순위 점수 0 / 100')).toBeInTheDocument();
  });

  it('distinguishes a truncated zero and an empty workbook from a complete zero result', () => {
    const { rerender } = render(<M25ResultsPanel result={{ ...zero, workbook: { ...zero.workbook, scan_truncated: true } }} isDemo={false} onReset={() => undefined} />);
    expect(screen.getByRole('heading', { name: '무료 구조 검사: 일부 범위에서 발견 0건' })).toBeInTheDocument();
    const scope = screen.getByRole('region', { name: '이번 무료 진단에서 확인한 범위' });
    expect(within(scope).getByText('부분 수행')).toBeInTheDocument();
    expect(within(scope).queryByText('완료')).not.toBeInTheDocument();
    rerender(<M25ResultsPanel result={{ ...zero, analysis_id: 'synthetic-empty', workbook: { ...zero.workbook, scanned_cell_count: 0, formula_count: 0 } }} isDemo={false} onReset={() => undefined} />);
    expect(screen.getByRole('heading', { name: '무료 구조 검사: 읽은 셀 0개' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: '무료 구조 검사: 발견 0건' })).not.toBeInTheDocument();
  });
});
