import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import type { ComponentProps } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { demoResult } from '../data/demo';
import type { ScanResult } from '../types';
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
  afterEach(cleanup);

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
});
