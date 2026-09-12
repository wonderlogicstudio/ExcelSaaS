import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useState, type ComponentProps } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { demoResult } from '../data/demo';
import type { FindingUserStatus, ScanResult } from '../types';
import * as diagnosisCsv from '../lib/diagnosisCsv';
import { compareScanResults } from '../lib/revalidation';
import { M25ResultsPanel } from './M25ResultsPanel';

function renderResult(
  result: ScanResult,
  overrides: Partial<ComponentProps<typeof M25ResultsPanel>> = {},
) {
  return render(
    <M25ResultsPanel
      result={result}
      isDemo={false}
      statuses={{}}
      revalidationComparison={null}
      onStatusChange={() => undefined}
      onPrepareRevalidation={() => undefined}
      onReset={() => undefined}
      {...overrides}
    />,
  );
}

function withFindings(findings: ScanResult['findings'], summary: Partial<ScanResult['summary']> = {}): ScanResult {
  return {
    ...demoResult,
    findings,
    summary: {
      ...demoResult.summary,
      issue_count: findings.length,
      critical_count: findings.filter((finding) => finding.severity === 'critical').length,
      warning_count: findings.filter((finding) => finding.severity === 'warning').length,
      info_count: findings.filter((finding) => finding.severity === 'info').length,
      safe_candidate_count: findings.filter((finding) => finding.repair_class === 'SAFE_CANDIDATE').length,
      confirmation_required_count: findings.filter(
        (finding) => finding.repair_class === 'CONFIRMATION_REQUIRED',
      ).length,
      expert_review_count: findings.filter((finding) => finding.repair_class === 'EXPERT_REVIEW').length,
      information_only_count: findings.filter(
        (finding) => finding.repair_class === 'INFORMATION_ONLY',
      ).length,
      repair_review_candidate_count: findings.filter(
        (finding) => finding.repair_class !== 'INFORMATION_ONLY',
      ).length,
      ...summary,
    },
  };
}

describe('M2.5 results panel', () => {
  it('keeps comparison details and full CSV independent of P1 filters and resets disclosures on a new scan', () => {
    const download = vi.spyOn(diagnosisCsv, 'downloadDiagnosisCsv').mockImplementation(() => undefined);
    const comparison = compareScanResults(demoResult, demoResult);
    const { container, rerender } = renderResult(demoResult, { revalidationComparison: comparison });
    fireEvent.click(screen.getByText(`항목 위치 보기 · ${comparison.stillDetected.length}건`));
    const disclosure = container.querySelector('.revalidation-details')!;
    expect(disclosure).toHaveAttribute('open');
    fireEvent.change(screen.getByLabelText('처리 상태로 보기'), { target: { value: 'REVIEWED' } });
    expect(container.querySelectorAll('details.finding')).toHaveLength(0);
    expect(disclosure.querySelectorAll('li')).toHaveLength(comparison.stillDetected.length);
    expect(disclosure).toHaveAttribute('open');
    for (const button of screen.getAllByRole('button', { name: /CSV/ })) fireEvent.click(button);
    expect(download).toHaveBeenCalledTimes(2);
    expect(download).toHaveBeenCalledWith(demoResult, {});
    rerender(<M25ResultsPanel result={{ ...demoResult, analysis_id: 'synthetic-next-scan' }} isDemo={false} revalidationComparison={comparison} onReset={() => undefined} />);
    expect(container.querySelector('.revalidation-details')).not.toHaveAttribute('open');
    expect(container.querySelectorAll('details.finding')).toHaveLength(demoResult.findings.length);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('shows the completed and unperformed free-scan scope before the result summary', () => {
    renderResult(demoResult);

    expect(screen.getByRole('heading', { name: '이번 무료 진단에서 확인한 범위' })).toBeInTheDocument();
    expect(screen.getByText('Excel 계산 결과 검증')).toBeInTheDocument();
    expect(screen.getAllByText('탐지 확실도: 직접 확인').length).toBeGreaterThan(0);
    expect(screen.getByText('탐지 확실도는 해당 패턴이 파일에 존재한다는 근거의 강도입니다. 수식, 계산 결과, 업무 논리가 정확하다는 의미는 아닙니다.')).toBeInTheDocument();
    expect(screen.queryByText(/신뢰도\s*\d+%/)).not.toBeInTheDocument();
    expect(screen.getByText('규칙 기반 우선순위 점수 62 / 100')).toBeInTheDocument();
    expect(screen.getByText('이 점수는 발견된 구조 위험 신호의 우선순위를 요약한 값입니다. 파일 전체 계산의 정확도, 업무적 정확성, 금전 손실 가능성을 뜻하지 않습니다.')).toBeInTheDocument();
    expect(screen.getByText('29,000원 ~ 49,000원')).toBeInTheDocument();
    expect(screen.getByText('베타 가격 가설이며 현재 결제는 진행되지 않습니다. 최종 작업 범위와 가격은 향후 사용자 확인 후 확정됩니다.')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: '향후 정밀검증 및 Approved Repair' })).toBeInTheDocument();
    expect(screen.getByText('현재 발견된 10건은 향후 정밀 검증 또는 사용자 승인 전 검토가 필요할 수 있습니다. 정밀 검증과 승인 기반 수정은 아직 제공하지 않습니다.')).toBeInTheDocument();
    expect(screen.getAllByText('정밀 검증 선행 대상 · 준비 중').length).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { name: '전체 Finding 목록' })).toBeInTheDocument();
    expect(screen.getAllByText('Excel에서 확인하는 방법').length).toBeGreaterThan(0);
    expect(screen.queryByText('테스트 의견')).not.toBeInTheDocument();
  });

  it('shows one concise list and summarizes the finding types', () => {
    renderResult(demoResult);

    expect(screen.getByText(`${demoResult.findings.length}개 전체 표시 · 클릭해 자세히 보기`)).toBeInTheDocument();
    expect(document.querySelectorAll('details.finding')).toHaveLength(demoResult.findings.length);
    expect(screen.getByText('문제 유형별 개수')).toBeInTheDocument();
  });

  it('keeps each finding compact until the user expands it', () => {
    const { container } = renderResult(demoResult);
    const firstFinding = container.querySelector('details.finding');

    expect(firstFinding).not.toHaveAttribute('open');
    fireEvent.click(firstFinding!.querySelector('summary')!);
    expect(firstFinding).toHaveAttribute('open');
  });

  it('handles zero, one, and information-only findings without claiming workbook correctness', () => {
    const zeroResult = withFindings([], {
      risk_score: 0,
      risk_band: 'low',
      complexity_score: 0,
      complexity_band: 'basic',
    });
    const { rerender } = renderResult(zeroResult);

    expect(screen.getAllByText('현재 무료 검사 범위에서는 구조적 위험 신호를 발견하지 못했습니다.').length).toBeGreaterThan(0);
    expect(screen.getByText('현재 무료 검사 범위에서는 구조적 위험 신호를 발견하지 못했습니다. 수식의 업무적 정확성, 계산 결과, 업무 규칙 및 통계 모델은 검증하지 않았습니다.')).toBeInTheDocument();
    expect(screen.getByText('0개 전체 표시 · 클릭해 자세히 보기')).toBeInTheDocument();
    expect(screen.getByText('현재 발견 결과 기준으로는 수정 검토 대상을 제안하지 않습니다. 정밀 검증과 승인 기반 수정은 아직 제공하지 않습니다.')).toBeInTheDocument();

    rerender(<M25ResultsPanel result={withFindings(demoResult.findings.slice(0, 1))} isDemo={false} onReset={() => undefined} />);
    expect(screen.getByText('1개 전체 표시 · 클릭해 자세히 보기')).toBeInTheDocument();

    rerender(<M25ResultsPanel result={withFindings(demoResult.findings.slice(0, 2))} isDemo={false} onReset={() => undefined} />);
    expect(screen.getByText('2개 전체 표시 · 클릭해 자세히 보기')).toBeInTheDocument();

    rerender(
      <M25ResultsPanel
        result={withFindings([demoResult.findings.find((finding) => finding.repair_class === 'INFORMATION_ONLY')!])}
        isDemo={false}
        onReset={() => undefined}
      />,
    );
    expect(screen.getAllByText('정보 제공 · 즉시 수정 불필요').length).toBeGreaterThan(0);
  });

  it('lets a user set a local handling status without changing the scan result', () => {
    const onStatusChange = vi.fn();
    renderResult(demoResult, { onStatusChange });

    fireEvent.change(screen.getAllByLabelText('FORMULA_REF_ERROR 사용자 처리 상태')[0], {
      target: { value: 'REVIEWED' },
    });

    expect(onStatusChange).toHaveBeenCalledWith(
      demoResult.findings.find((finding) => finding.rule_code === 'FORMULA_REF_ERROR')!.finding_key,
      'REVIEWED',
    );
    expect(screen.getByRole('heading', { name: '사용자 처리 상태' })).toBeInTheDocument();
    expect(screen.getByText('시스템 판정이나 스캔 결과를 바꾸지 않습니다.')).toBeInTheDocument();
  });

  it('warns when the scanner stopped at the cell safety limit and supports mixed repair classes', () => {
    renderResult({
      ...demoResult,
      workbook: { ...demoResult.workbook, scan_truncated: true },
    });

    expect(screen.getByText('안전 제한 때문에 일부 셀만 검사했습니다. 이 결과는 전체 파일 검사가 아닙니다.')).toBeInTheDocument();
    expect(screen.getAllByText('안전 수정 후보').length).toBeGreaterThan(0);
    expect(screen.getAllByText('사용자 확인 필요').length).toBeGreaterThan(0);
    expect(screen.getAllByText('전문가 검토 필요').length).toBeGreaterThan(0);
    expect(screen.getAllByText('정보 제공 · 즉시 수정 불필요').length).toBeGreaterThan(0);
  });

  const filterResult = withFindings([
    { ...demoResult.findings[0], id: 'triage-1', finding_key: 'triage-1', sheet: '합성 시트', cell: 'A1', severity: 'critical' },
    { ...demoResult.findings[0], id: 'triage-2', finding_key: 'triage-2', sheet: '합성 시트', cell: 'A2', severity: 'warning' },
    { ...demoResult.findings[0], id: 'triage-3', finding_key: 'triage-3', sheet: 'all', cell: 'A3', severity: 'info' },
    { ...demoResult.findings[0], id: 'triage-4', finding_key: 'triage-4', sheet: null, cell: null, severity: 'warning' },
  ]);

  it('combines filters and distinguishes no matches from a clean scan without changing totals or CSV', () => {
    const statuses: Record<string, FindingUserStatus> = { 'triage-2': 'REVIEWED' };
    const download = vi.spyOn(diagnosisCsv, 'downloadDiagnosisCsv').mockImplementation(() => undefined);
    const baseline = JSON.stringify(filterResult);
    const baselineCsv = diagnosisCsv.buildDiagnosisCsv(filterResult, statuses);
    renderResult(filterResult, { statuses });

    fireEvent.change(screen.getByLabelText('중요도'), { target: { value: 'warning' } });
    fireEvent.change(screen.getByLabelText('시트'), { target: { value: 'sheet:합성 시트' } });
    fireEvent.change(screen.getByLabelText('처리 상태로 보기'), { target: { value: 'REVIEWED' } });
    expect(document.querySelectorAll('details.finding')).toHaveLength(1);
    expect(document.querySelector('details.finding')).toHaveTextContent('A2');
    expect(screen.getByRole('status')).toHaveTextContent('총 4개 중 1개 표시');
    expect(screen.getByText('규칙 기반 우선순위 점수 62 / 100')).toBeInTheDocument();
    expect(screen.getByText('29,000원 ~ 49,000원')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('처리 상태로 보기'), { target: { value: 'UNREVIEWED' } });
    expect(document.querySelectorAll('details.finding')).toHaveLength(0);
    expect(screen.getByText(/선택한 조건에 맞는 항목이 없습니다/)).toHaveTextContent('파일에 문제가 없다는 뜻이 아닙니다');
    expect(screen.queryByText('현재 무료 검사 범위에서는 구조적 위험 신호를 발견하지 못했습니다.')).not.toBeInTheDocument();
    for (const button of screen.getAllByRole('button', { name: 'CSV 결과 다운로드' })) fireEvent.click(button);
    expect(download).toHaveBeenCalledTimes(2);
    expect(download).toHaveBeenNthCalledWith(1, filterResult, statuses);
    expect(download).toHaveBeenNthCalledWith(2, filterResult, statuses);
    expect(JSON.stringify(filterResult)).toBe(baseline);
    expect(diagnosisCsv.buildDiagnosisCsv(filterResult, statuses)).toBe(baselineCsv);

    fireEvent.click(screen.getByRole('button', { name: '필터 초기화' }));
    expect(document.querySelectorAll('details.finding')).toHaveLength(4);
    expect(screen.getByRole('status')).toHaveTextContent('4개 전체 표시');
    expect(screen.getByRole('button', { name: '필터 초기화' })).toBeDisabled();
  });

  it('keeps workbook-level findings and a sheet named all individually selectable', () => {
    renderResult(filterResult);
    fireEvent.change(screen.getByLabelText('시트'), { target: { value: 'workbook' } });
    expect(document.querySelectorAll('details.finding')).toHaveLength(1);
    expect(document.querySelector('details.finding .finding__location')).toBeNull();
    fireEvent.change(screen.getByLabelText('시트'), { target: { value: 'sheet:all' } });
    expect(document.querySelectorAll('details.finding')).toHaveLength(1);
    expect(document.querySelector('details.finding')).toHaveTextContent('all · A3');
  });

  it('opens priority findings across all sheets and statuses and moves keyboard focus to the list heading', () => {
    renderResult(filterResult);
    fireEvent.change(screen.getByLabelText('중요도'), { target: { value: 'info' } });
    fireEvent.change(screen.getByLabelText('시트'), { target: { value: 'sheet:all' } });
    fireEvent.change(screen.getByLabelText('처리 상태로 보기'), { target: { value: 'REVIEWED' } });
    fireEvent.click(screen.getByRole('button', { name: '우선 문제 확인하기' }));
    expect(screen.getByLabelText('중요도')).toHaveValue('priority');
    expect(screen.getByLabelText('시트')).toHaveValue('all');
    expect(screen.getByLabelText('처리 상태로 보기')).toHaveValue('all');
    expect(document.querySelectorAll('details.finding')).toHaveLength(3);
    expect(document.querySelectorAll('details.finding--info')).toHaveLength(0);
    expect(document.querySelector('#priority-findings')).toHaveFocus();
  });

  it('updates the filtered work list as a local status changes and preserves status after clearing filters', () => {
    const storage = vi.spyOn(Storage.prototype, 'setItem');
    const fetch = vi.spyOn(globalThis, 'fetch');
    function StatefulResult() {
      const [statuses, setStatuses] = useState<Record<string, FindingUserStatus>>({});
      return <M25ResultsPanel result={filterResult} isDemo={false} statuses={statuses} onReset={() => undefined}
        onStatusChange={(key, status) => setStatuses((current) => ({ ...current, [key]: status }))} />;
    }
    render(<StatefulResult />);
    fireEvent.change(screen.getByLabelText('처리 상태로 보기'), { target: { value: 'UNREVIEWED' } });
    const first = document.querySelector('details.finding')!;
    fireEvent.click(first.querySelector('summary')!);
    fireEvent.change(first.querySelector('select')!, { target: { value: 'REVIEWED' } });
    expect(document.querySelectorAll('details.finding')).toHaveLength(3);
    expect(screen.getByLabelText('처리 상태로 보기')).toHaveFocus();
    expect(screen.getByLabelText('처리 상태로 보기')).toHaveValue('UNREVIEWED');
    fireEvent.click(screen.getByRole('button', { name: '필터 초기화' }));
    expect(document.querySelectorAll('details.finding')).toHaveLength(4);
    expect(document.querySelector('details.finding select')).toHaveValue('REVIEWED');
    expect(storage).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('resets filters when a new scan arrives so new findings cannot be silently hidden', () => {
    const { rerender } = renderResult(filterResult);
    fireEvent.change(screen.getByLabelText('중요도'), { target: { value: 'critical' } });
    fireEvent.change(screen.getByLabelText('시트'), { target: { value: 'sheet:합성 시트' } });
    fireEvent.change(screen.getByLabelText('처리 상태로 보기'), { target: { value: 'REVIEWED' } });
    rerender(<M25ResultsPanel result={{ ...filterResult, analysis_id: 'next-synthetic-scan' }} isDemo={false} onReset={() => undefined} />);
    expect(screen.getByLabelText('중요도')).toHaveValue('all');
    expect(screen.getByLabelText('시트')).toHaveValue('all');
    expect(screen.getByLabelText('처리 상태로 보기')).toHaveValue('all');
    expect(document.querySelectorAll('details.finding')).toHaveLength(4);
  });

  it('does not offer a priority shortcut when only information or no findings exist', () => {
    const { rerender } = renderResult(withFindings([filterResult.findings[2]]));
    expect(screen.getByRole('button', { name: '우선 문제 확인하기' })).toBeDisabled();
    expect(document.querySelectorAll('details.finding')).toHaveLength(1);
    rerender(<M25ResultsPanel result={withFindings([])} isDemo={false} onReset={() => undefined} />);
    expect(screen.getByRole('button', { name: '우선 문제 확인하기' })).toBeDisabled();
    expect(screen.queryByRole('group', { name: '찾아볼 항목 선택' })).not.toBeInTheDocument();
  });
});
