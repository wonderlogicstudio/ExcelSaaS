import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import type { ComponentProps } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { demoResult } from '../data/demo';
import type { Finding, FormulaAuditResult } from '../types';
import type { FeedbackRepository } from '../lib/feedback';
import { buildDiagnosisCsv } from '../lib/diagnosisCsv';
import { FormulaAuditPanel } from './FormulaAuditPanel';

const candidate: Finding = {
  id: 'audit-candidate-1',
  finding_key: 'FORMULA_PATTERN_OUTLIER|pattern|c4',
  rule_code: 'FORMULA_PATTERN_OUTLIER',
  severity: 'warning',
  title: '주변 수식과 다른 패턴 후보',
  description: '주변 반복 수식과 다른 구조를 확인한 후보입니다.',
  sheet: 'Pattern',
  cell: 'C4',
  confidence: 0,
  repair_class: 'EXPERT_REVIEW',
  formula_pattern: {
    pattern_type: 'DOMINANT_NORMALIZED_PATTERN_OUTLIER',
    formula_region: 'C2:C6',
    dominant_pattern_id: 'dominant-pattern',
    current_pattern_id: 'current-pattern',
    neighbor_count: 4,
    evidence_locations: ['C2', 'C3', 'C5', 'C6'],
    comparison_locations: ['C2', 'C3', 'C5', 'C6'],
    detection_basis: '주변 수식 비교',
    evidence_summary: '대상 수식의 함수 구성이 주변 반복 패턴과 다릅니다.',
    dominant_pattern_summary: '주변 수식은 같은 함수와 참조 구조가 반복됩니다.',
    current_pattern_summary: '대상 수식은 주변과 다른 함수 구성을 사용합니다.',
    normal_case_possibility: '소계 또는 의도된 예외 계산일 수 있습니다.',
    current_limitations: ['계산 결과와 업무 규칙은 확인하지 않았습니다.'],
    pattern_subtype: 'FUNCTION_PATTERN_DRIFT',
  },
  guidance: {
    evidence_grade: 'PATTERN_INFERENCE',
    action_category: 'DEEP_VALIDATION_REQUIRED',
    repair_eligibility: 'CURRENTLY_NOT_SUPPORTED',
    user_confirmation_required: true,
    detected_fact: '주변 수식과 다른 패턴 후보입니다.',
    possible_impact: '추가 확인이 필요할 수 있습니다.',
    how_to_check_in_excel: ['C4와 주변 수식을 비교'],
    when_it_may_be_normal: ['의도된 예외 계산인 경우'],
    when_action_is_recommended: ['같은 계산이 필요한 경우'],
    recommended_next_action: '직접 확인하세요.',
    unchecked_scope: ['계산 결과와 업무 규칙은 확인하지 않았습니다.'],
    recommended_next_checks: ['주변 수식 비교'],
  },
};

const completedResult: FormulaAuditResult = {
  status: 'COMPLETED',
  formula_cell_count: 5,
  audited_sheet_count: 1,
  audited_formula_region_count: 1,
  candidates: [candidate],
  limitations: ['수식 계산 결과와 업무 규칙은 확인하지 않았습니다.'],
  elapsed_ms: 24,
  scanner_version: '0.1.3',
  rule_set_version: '2026.09.4',
};

function renderPanel(overrides: Partial<ComponentProps<typeof FormulaAuditPanel>> = {}) {
  const repository: FeedbackRepository = {
    list: () => [],
    save: vi.fn((draft) => ({
      feedback_id: 'feedback-1',
      feedback_scope: draft.feedback_scope,
      feedback_category: draft.feedback_category,
      rating: draft.rating ?? null,
      rule_code: draft.rule_code ?? null,
      opaque_finding_id: draft.opaque_finding_id ?? null,
      scanner_version: draft.scanner_version,
      created_at: '2026-09-01T00:00:00Z',
    })),
    clear: () => undefined,
  };
  const onRun = vi.fn();
  return {
    repository,
    onRun,
    ...render(
      <FormulaAuditPanel
        baseResult={{ ...demoResult, workbook: { ...demoResult.workbook, formula_count: 5 } }}
        sourceFile={new File(['test'], 'pattern-check.xlsx')}
        auditResult={completedResult}
        busy={false}
        error={null}
        statuses={{}}
        feedbackRepository={repository}
        onRun={onRun}
        onStatusChange={() => undefined}
        {...overrides}
      />,
    ),
  };
}

describe('FormulaAuditPanel', () => {
  afterEach(cleanup);

  it('keeps the internal audit separate and progressively reveals candidate evidence', () => {
    const { onRun } = renderPanel();

    expect(screen.getByRole('heading', { name: '수식 패턴 정밀검사' })).toBeInTheDocument();
    expect(screen.getByText('기본 위험 점수·견적·CSV에 반영하지 않음')).toBeInTheDocument();
    expect(screen.getByText('후보 있음')).toBeInTheDocument();
    const finding = document.querySelector('details.formula-audit-finding');
    expect(finding).not.toHaveAttribute('open');
    fireEvent.click(screen.getByText('주변 수식과 다른 패턴 후보'));
    expect(finding).toHaveAttribute('open');
    expect(screen.getByText('비교에 사용한 주변 위치')).toBeInTheDocument();
    expect(screen.getByText('C2 · C3 · C5 · C6')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '수식 패턴 정밀검사 다시 실행' }));
    expect(onRun).toHaveBeenCalledOnce();
    expect(screen.queryByText(/자동 수정 가능|수정본 생성 가능|확정 오류/)).not.toBeInTheDocument();
  });

  it('shows an indeterminate analysis state and blocks a truncated free scan', () => {
    const { rerender } = renderPanel({ busy: true, auditResult: null });
    expect(screen.getByText('분석 중')).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();

    rerender(
      <FormulaAuditPanel
        baseResult={{ ...demoResult, workbook: { ...demoResult.workbook, scan_truncated: true } }}
        sourceFile={new File(['test'], 'truncated.xlsx')}
        auditResult={null}
        busy={false}
        error={null}
        statuses={{}}
        feedbackRepository={null}
        onRun={() => undefined}
        onStatusChange={() => undefined}
      />,
    );
    expect(screen.getByText('기본 무료 진단이 일부 셀만 검사해 이번 수식 패턴 정밀검사는 실행하지 않습니다.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '수식 패턴 정밀검사 실행' })).toBeDisabled();
  });

  it('does not change the free result or its CSV when an audit is requested', () => {
    const beforeCsv = buildDiagnosisCsv(demoResult, {});
    const beforeContract = JSON.stringify({
      findings: demoResult.findings,
      summary: demoResult.summary,
      quote: demoResult.quote,
    });
    const { onRun } = renderPanel();

    fireEvent.click(screen.getByRole('button', { name: '수식 패턴 정밀검사 다시 실행' }));

    expect(onRun).toHaveBeenCalledOnce();
    expect(buildDiagnosisCsv(demoResult, {})).toBe(beforeCsv);
    expect(JSON.stringify({
      findings: demoResult.findings,
      summary: demoResult.summary,
      quote: demoResult.quote,
    })).toBe(beforeContract);
  });
});
