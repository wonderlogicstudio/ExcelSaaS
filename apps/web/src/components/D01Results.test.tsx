import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { demoResult } from '../data/demo';
import { M25ResultsPanel } from './M25ResultsPanel';
import { buildDiagnosisCsv } from '../lib/diagnosisCsv';
import { compareScanResults, findingIdentity } from '../lib/revalidation';
import type { FindingUserStatus } from '../types';

const findings = ['A1', 'A2', 'B1'].map((cell, i) => ({ ...demoResult.findings[0], id: `synthetic-${cell}`,
  finding_key: `synthetic-${cell}`, sheet: i === 1 ? '합성 B' : '합성 A', cell,
  rule_code: i < 2 ? 'FORMULA_REF_ERROR' : 'FORMULA_ERROR_LITERAL', title: '합성 위치 점검',
}));
const result = { ...demoResult, findings, summary: { ...demoResult.summary, issue_count: 3 } };

describe('D01 free diagnosis integration', () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it('preserves every leaf, score and full CSV when switching groups/table and keeping filters', () => {
    const before = JSON.stringify(result);
    const csv = buildDiagnosisCsv(result, {});
    const { container } = render(<M25ResultsPanel result={result} isDemo onReset={() => undefined} />);
    expect(container.querySelectorAll('.finding-group')).toHaveLength(2);
    expect(container.querySelectorAll('details.finding')).toHaveLength(3);
    expect(container.querySelectorAll('.finding-group__guide')).toHaveLength(2);
    fireEvent.change(screen.getByLabelText('시트'), { target: { value: 'sheet:합성 A' } });
    fireEvent.click(screen.getByLabelText('전체 항목 표'));
    expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(3);
    expect(screen.getByLabelText('시트')).toHaveValue('sheet:합성 A');
    expect(screen.getByText('규칙 기반 우선순위 점수 62 / 100')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('유형별 보기'));
    expect(container.querySelectorAll('details.finding')).toHaveLength(2);
    fireEvent.click(screen.getByRole('button', { name: '필터 초기화' }));
    expect(container.querySelectorAll('details.finding')).toHaveLength(3);
    expect(buildDiagnosisCsv(result, {})).toBe(csv);
    expect(JSON.stringify(result)).toBe(before);
  });

  it('group review changes only visible leaf handling, never approval, purchase, storage or requests', () => {
    const network = vi.spyOn(globalThis, 'fetch');
    const storage = vi.spyOn(Storage.prototype, 'setItem');
    const changes = vi.fn();
    function Stateful() {
      const [statuses, setStatuses] = useState<Record<string, FindingUserStatus>>({});
      return <M25ResultsPanel result={result} isDemo statuses={statuses} onReset={() => undefined}
        onStatusChange={(key, value) => { changes(key, value); setStatuses((current) => ({ ...current, [key]: value })); }} />;
    }
    const { container } = render(<Stateful />);
    fireEvent.change(screen.getByLabelText('시트'), { target: { value: 'sheet:합성 A' } });
    fireEvent.change(screen.getByLabelText('처리 상태로 보기'), { target: { value: 'UNREVIEWED' } });
    fireEvent.click(within(screen.getByRole('region', { name: 'FORMULA_REF_ERROR 유형' })).getByRole('button', { name: '표시된 1개 확인함' }));
    expect(changes).toHaveBeenCalledExactlyOnceWith(findingIdentity(findings[0]), 'REVIEWED');
    expect(screen.getByLabelText('처리 상태로 보기')).toHaveFocus();
    fireEvent.click(screen.getByRole('button', { name: '필터 초기화' }));
    const controls = [...container.querySelectorAll<HTMLSelectElement>('details.finding select')];
    expect(controls.map((control) => control.value)).toEqual(['REVIEWED', 'UNREVIEWED', 'UNREVIEWED']);
    fireEvent.change(controls[0], { target: { value: 'MARKED_NORMAL' } });
    expect(changes).toHaveBeenLastCalledWith(findingIdentity(findings[0]), 'MARKED_NORMAL');
    expect(network).not.toHaveBeenCalled();
    expect(storage).not.toHaveBeenCalled();
    expect(result).not.toHaveProperty('approval');
    expect(result.products?.every((product) => !product.purchase_enabled)).toBe(true);
    expect(screen.queryByRole('button', { name: '이 변경계획 승인' })).not.toBeInTheDocument();
  });

  it('separates total/returned/omitted/filtered counts and never calls missing details clean', () => {
    const partial = { ...result, findings: findings.slice(0, 1), workbook: { ...result.workbook, scan_truncated: true } };
    const { rerender } = render(<M25ResultsPanel result={partial} isDemo onReset={() => undefined} />);
    expect(screen.getByText('전체 발견 3건 · 반환 상세 1건 · 상세 생략 2건 · 필터 표시 1건')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('처리 상태로 보기'), { target: { value: 'REVIEWED' } });
    expect(screen.getByText(/필터 표시 0건/)).toBeInTheDocument();
    expect(screen.getByText(/선택한 조건에 맞는 항목이 없습니다/)).toBeInTheDocument();
    expect(screen.getByText(/검사하지 않은 셀의 위험 신호는 포함하지 않습니다/)).toBeInTheDocument();
    rerender(<M25ResultsPanel result={{ ...partial, analysis_id: 'synthetic-empty-details', findings: [] }} isDemo onReset={() => undefined} />);
    expect(screen.getByText(/발견된 항목의 반환 상세가 없습니다/)).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: '무료 구조 검사: 발견 0건' })).not.toBeInTheDocument();
  });

  it('does not certify disappearance or novelty when either scan omits details', () => {
    const partial = { ...result, findings: findings.slice(1) };
    render(<M25ResultsPanel result={partial} isDemo revalidationComparison={compareScanResults(result, partial)} onReset={() => undefined} />);
    expect(screen.getByRole('article', { name: '이전 상세에만 있음 · 미탐지 여부 확인 불가' })).toBeInTheDocument();
    expect(screen.getByRole('article', { name: '현재 상세에만 있음 · 신규 여부 확인 불가' })).toBeInTheDocument();
    expect(screen.getByText(/상세 생략: 이전 검사 0건 · 현재 검사 1건/)).toBeInTheDocument();
  });
});
