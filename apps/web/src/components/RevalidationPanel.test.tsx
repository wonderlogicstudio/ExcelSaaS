import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { demoResult } from '../data/demo';
import { compareScanResults } from '../lib/revalidation';
import type { Finding } from '../types';
import { RevalidationPanel } from './RevalidationPanel';

function finding(cell: string | null, sheet: string | null = '합성 비교'): Finding {
  return { ...demoResult.findings[0], id: `synthetic-${sheet}-${cell}`, finding_key: `synthetic-${sheet}-${cell}`, sheet, cell };
}

function comparison(previous: Finding[], current: Finding[]) {
  return compareScanResults({ ...demoResult, findings: previous }, { ...demoResult, findings: current });
}

describe('re-validation location details', () => {
  afterEach(cleanup);

  it('distinguishes repeated rules by location and uses previous vs current metadata', () => {
    const before = [finding('A1'), finding('B2')];
    const after = [{ ...finding('B2'), title: '현재 검사 제목' }, finding('C3')];
    const result = comparison(before, after);
    const unchanged = JSON.stringify(result);
    render(<RevalidationPanel comparison={result} onPrepareRevalidation={() => undefined} />);

    for (const [title, location, entryTitle] of [
      ['이번 재검사에서 더 이상 탐지되지 않음', '이전 위치 — 시트: 합성 비교 · 셀: A1', before[0].title],
      ['계속 탐지됨', '현재 위치 — 시트: 합성 비교 · 셀: B2', after[0].title],
      ['새롭게 탐지됨', '현재 위치 — 시트: 합성 비교 · 셀: C3', after[1].title],
    ]) {
      const group = screen.getByRole('article', { name: title });
      const disclosure = group.querySelector('details')!;
      expect(disclosure).not.toHaveAttribute('open');
      fireEvent.click(within(group).getByText('항목 위치 보기 · 1건'));
      expect(disclosure).toHaveAttribute('open');
      expect(within(group).getByRole('listitem')).toHaveTextContent(entryTitle);
      expect(within(group).getByText(location)).toBeVisible();
      expect(within(group).getByText(before[0].rule_code)).toBeVisible();
    }
    expect(JSON.stringify(result)).toBe(unchanged);
  });

  it('keeps every distinct location and makes missing location scope explicit without exposing other fields', () => {
    const rows = [finding(null, null), finding(null), finding('D4', null), ...Array.from({ length: 24 }, (_, i) => finding(`E${i + 1}`))];
    const result = comparison([], rows.map((row) => ({ ...row, description: 'SYNTHETIC_PRIVATE_DESCRIPTION' })));
    render(<RevalidationPanel comparison={result} onPrepareRevalidation={() => undefined} />);
    fireEvent.click(screen.getByText('항목 위치 보기 · 27건'));
    const group = screen.getByRole('article', { name: '새롭게 탐지됨' });
    expect(within(group).getAllByRole('listitem')).toHaveLength(27);
    expect(within(group).getByText('현재 위치 — 통합문서 수준 (시트·셀 지정 없음)')).toBeVisible();
    expect(within(group).getByText('현재 위치 — 시트: 합성 비교 · 셀 지정 없음')).toBeVisible();
    expect(within(group).getByText('현재 위치 — 시트 지정 없음 · 셀: D4')).toBeVisible();
    expect(within(group).getAllByRole('listitem').at(-1)).toHaveTextContent('셀: E24');
    expect(screen.queryByText('SYNTHETIC_PRIVATE_DESCRIPTION')).not.toBeInTheDocument();
    expect(screen.queryByText(rows[0].finding_key!)).not.toBeInTheDocument();
  });

  it.each(['previousWasTruncated', 'currentWasTruncated'] as const)('retains version and %s warnings and the limits on interpretation', (limit) => {
    render(<RevalidationPanel comparison={{ ...comparison([finding('A1')], []), versionMismatch: true, [limit]: true }} onPrepareRevalidation={() => undefined} />);
    expect(screen.getByText(/규칙 세트 버전이 달라/)).toBeVisible();
    expect(screen.getByText(/비교 범위가 완전하지 않을 수/)).toBeVisible();
    expect(screen.getByText(/업무적 해결이나 계산 결과의 정확성을 보장하지 않습니다/)).toBeVisible();
    expect(screen.getByText(/시트 이름을 바꾸거나 셀을 이동하면/)).toHaveTextContent('셀 값이나 계산 결과의 변경은 비교하지 않습니다.');
  });

  it('keeps empty groups and first-scan instructions usable without empty disclosures', () => {
    const onPrepareRevalidation = vi.fn();
    const { container, rerender } = render(<RevalidationPanel comparison={comparison([], [])} onPrepareRevalidation={onPrepareRevalidation} />);
    expect(screen.getAllByText('해당 항목이 없습니다.')).toHaveLength(3);
    expect(container.querySelector('details')).toBeNull();
    rerender(<RevalidationPanel comparison={null} onPrepareRevalidation={onPrepareRevalidation} />);
    expect(screen.getByText(/같은 브라우저 화면에서 이전 결과와 현재 결과만 비교합니다/)).toBeVisible();
    expect(screen.queryByRole('article')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '수정 후 파일 선택' }));
    expect(onPrepareRevalidation).toHaveBeenCalledOnce();
  });
});
