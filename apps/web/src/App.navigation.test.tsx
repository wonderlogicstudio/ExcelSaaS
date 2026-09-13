import { cleanup, fireEvent, render, screen, within, waitFor } from '@testing-library/react';
import { act } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { demoResult } from './data/demo';
import { reviewDisposition } from './lib/repairReview';

afterEach(() => { cleanup(); window.history.replaceState({}, '', '/'); vi.useRealTimers(); vi.unstubAllGlobals(); });
const menu = (name: string) => within(screen.getByRole('navigation', { name: '주요 메뉴' })).getByRole('link', { name });
describe('core product navigation and review boundaries', () => {
  it('closes the mobile menu with Escape from its toggle or links and returns focus', () => {
    render(<App/>);
    const toggle = screen.getByRole('button', {name:'메뉴 열기'});
    for (const fromLink of [false, true]) {
      fireEvent.click(toggle);
      expect(toggle).toHaveAttribute('aria-expanded','true');
      const target = fromLink ? menu('정밀 검증') : toggle;
      target.focus();
      fireEvent.keyDown(target, {key:'Escape'});
      expect(toggle).toHaveAttribute('aria-expanded','false');
      expect(toggle).toHaveFocus();
    }
  });

  it('navigates service pages, marks the current page, handles history and unknown paths', async () => {
    vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined);
    render(<App/>);
    fireEvent.click(menu('정밀 검증'));
    expect(window.location.pathname).toBe('/precision-verification');
    expect(screen.getByRole('heading', { name: '추가로 검증할 업무 범위를 확인하세요.' })).toBeVisible();
    expect(menu('정밀 검증')).toHaveAttribute('aria-current', 'page');
    fireEvent.click(menu('업무 자동화'));
    expect(screen.getByRole('heading', { name: '표준 업무 자동화' })).toBeVisible();
    expect(screen.queryByRole('button', { name: /결제/ })).not.toBeInTheDocument();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe('/precision-verification'));
    expect(screen.getByRole('heading', { name: '추가로 검증할 업무 범위를 확인하세요.' })).toBeVisible();
    act(() => { window.history.pushState({}, '', '/unknown'); window.dispatchEvent(new PopStateEvent('popstate')); });
    expect(screen.getByRole('heading', { name: '페이지를 찾을 수 없습니다' })).toBeVisible();
  });
  it.each(['/precision-verification','/compare','/automation','/help','/repair','/orders','/diagnosis','/privacy','/terms'])('renders direct and refreshed %s without inventing a saved workbook', path => {
    window.history.replaceState({}, '', path);
    const first = render(<App/>);
    expect(document.querySelectorAll('[data-product-page]:not([hidden])')).toHaveLength(1);
    expect(document.querySelector('#results')).toBeNull();
    first.unmount(); render(<App/>);
    expect(document.querySelectorAll('[data-product-page]:not([hidden])')).toHaveLength(1);
    expect(document.querySelector('#results')).toBeNull();
  });
  it('retains review selection, status, filters and expanded evidence across menu navigation without a request', async () => {
    vi.useFakeTimers(); vi.spyOn(window,'scrollTo').mockImplementation(() => undefined);
    const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher);
    render(<App/>);
    fireEvent.click(screen.getAllByRole('button', { name: '샘플 결과 보기' })[0]);
    await act(async () => { await vi.advanceTimersByTimeAsync(2200); });
    fireEvent.click(document.querySelector('.diagnosis-type__disclosure > summary')!);
    fireEvent.click(document.querySelector('.diagnosis-cell > summary')!);
    const choice = screen.getAllByRole('checkbox', { name: /2단계에 포함/ })[0];
    fireEvent.click(choice);
    const selected = document.querySelector('#repair-review')!;
    expect(selected).toHaveTextContent('검토 선택 1건');
    const input = document.querySelector<HTMLSelectElement>('.finding__status-control select')!;
    fireEvent.change(input, { target: { value: 'REVIEWED' } });
    const findings = document.querySelector('#results')!;
    fireEvent.click(screen.getByText('필터 및 전체 항목 표'));
    const select = within(findings as HTMLElement).getByRole('combobox', { name: '중요도' });
    fireEvent.change(select, { target: { value: 'warning' } });
    fireEvent.click(menu('비교·대사'));
    expect(findings).not.toBeVisible();
    fireEvent.click(menu('무료 진단'));
    expect(findings).toBeVisible(); expect(select).toHaveValue('warning');
    expect(selected).toHaveTextContent('검토 선택 1건'); expect(fetcher).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: '다른 파일 검사' }));
    expect(document.querySelector('#repair-review')).toBeNull();
  });
  it('does not route modified links and preserves legacy comparison bookmarks', async () => {
    window.history.replaceState({}, '', '/#two-file-comparison'); render(<App/>);
    await waitFor(() => expect(window.location.pathname).toBe('/compare'));
    const link = menu('정밀 검증'); fireEvent.click(link, { ctrlKey: true });
    expect(window.location.pathname).toBe('/compare');
  });
  it('maps only explicit numeric text and true-blank candidates to a server preflight, never infers a formula', () => {
    const f = demoResult.findings[0];
    expect(reviewDisposition({...f,rule_code:'NUMBER_STORED_AS_TEXT',sheet:'Data',cell:'B2'}).profile).toBe('RP01_NUMERIC_TEXT_FIELD_V1');
    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_OUTLIER'}).profile).toBeUndefined();
    expect(reviewDisposition({...f,rule_code:'FORMULA_PATTERN_GAP'}).profile).toBeUndefined();
    expect(reviewDisposition({...f,rule_code:'NUMBER_STORED_AS_TEXT',cell:'B2:B99'}).profile).toBeUndefined();
  });
});
