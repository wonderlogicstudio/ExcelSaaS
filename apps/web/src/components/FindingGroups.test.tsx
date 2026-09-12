import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { demoResult } from '../data/demo';
import { buildDiagnosisCsv } from '../lib/diagnosisCsv';
import { M25ResultsPanel } from './M25ResultsPanel';

const title = '중첩이 깊은 수식';
const findings = Array.from({ length: 49 }, (_, index) => ({
  ...demoResult.findings[0], id: `group-case-${index}`, finding_key: `group-case-${index}`,
  rule_code: 'FORMULA_DEEP_NESTING', title, sheet: '합성 채권', cell: `J${index + 2}`,
}));
const result = { ...demoResult, findings, summary: { ...demoResult.summary, issue_count: 49 } };

describe('same-rule finding groups', () => {
  afterEach(cleanup);

  it('starts with one collapsed group for 49 findings and exposes all locations on demand', () => {
    const original = JSON.stringify(result);
    const csv = buildDiagnosisCsv(result, {});
    const { container } = render(<M25ResultsPanel result={result} isDemo onReset={() => undefined} />);
    const group = screen.getByRole('region', { name: 'FORMULA_DEEP_NESTING 유형' });
    expect(container.querySelectorAll('.finding-group')).toHaveLength(1);
    const locations = group.querySelector('details.finding-group__locations');
    expect(locations).not.toBeNull();
    expect(locations).not.toHaveAttribute('open');
    const firstLocation = group.querySelector('details.finding > summary');
    expect(firstLocation).not.toBeVisible();
    fireEvent.click(within(group).getByText('개별 위치 49개 보기'));
    expect(locations).toHaveAttribute('open');
    expect(firstLocation).toBeVisible();
    expect(group.querySelectorAll('details.finding')).toHaveLength(49);
    fireEvent.click(within(group).getByText('개별 위치 49개 보기'));
    expect(firstLocation).not.toBeVisible();
    fireEvent.click(screen.getByLabelText('전체 항목 표'));
    expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(50);
    expect(buildDiagnosisCsv(result, {})).toBe(csv);
    expect(JSON.stringify(result)).toBe(original);
  });

  it('shows the common title once and retains individual location/evidence/status details', () => {
    render(<M25ResultsPanel result={result} isDemo onReset={() => undefined} />);
    const group = screen.getByRole('region', { name: 'FORMULA_DEEP_NESTING 유형' });
    expect(within(group).getAllByRole('heading', { name: title, hidden: true })).toHaveLength(1);
    fireEvent.click(within(group).getByText('개별 위치 49개 보기'));
    const leaf = group.querySelector('details.finding')!;
    fireEvent.click(leaf.querySelector('summary')!);
    expect(within(leaf as HTMLElement).getByLabelText('FORMULA_DEEP_NESTING 사용자 처리 상태')).toBeVisible();
    expect(leaf).toHaveTextContent('합성 채권 · J2');
    expect(leaf).toHaveTextContent(findings[0].description);
  });
});
