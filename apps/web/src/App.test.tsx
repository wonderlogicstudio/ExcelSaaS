import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { act } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App';

describe('WorkbookCare landing page', () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it('explains the concrete scan scope and exposes the primary CTA', () => {
    render(<App />);

    expect(
      screen.getByRole('heading', { name: /문제를 찾고, 수정 방향을 정리하세요/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /문제를 찾고, 수정 여부를 결정하세요/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /답변보다, 수정 판단의 근거를 확인하세요/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', { name: /파일은 건드리지 않고 확인합니다/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /무료.*진단/i }).length).toBeGreaterThan(0);
    expect(screen.getByText('원본 파일 변경 없음')).toBeInTheDocument();
  });

  it('moves the free-diagnosis CTA to the visible upload card', () => {
    const scrollIntoView = vi.spyOn(Element.prototype, 'scrollIntoView');
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: '테스트용 파일 무료 진단' }));

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' });
    scrollIntoView.mockRestore();
  });

  it('maps each header menu item to its matching titled section', () => {
    render(<App />);
    const navigation = screen.getByRole('navigation', { name: '주요 메뉴' });
    const menuDestinations = [
      ['무료 진단', '#free-diagnosis'],
      ['정밀 검증', '#precision-verification'],
      ['자동화 의뢰', '#automation-consultation'],
      ['파일 처리 원칙', '#file-handling-principles'],
      ['FAQ', '#faq'],
    ];

    for (const [label, href] of menuDestinations) {
      const link = navigation.querySelector(`a[href="${href}"]`);
      expect(link).toHaveTextContent(label);
      expect(document.querySelector(href)?.querySelector('h1, h2')).not.toBeNull();
    }
  });

  it('runs the sample flow and displays the beta price range and planned verification status', async () => {
    vi.useFakeTimers();
    render(<App />);

    fireEvent.click(screen.getAllByRole('button', { name: /샘플 결과 보기/i })[0]);
    expect(screen.getByText('파일 구조와 수식 참조를 검사하고 있습니다.')).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2200);
    });

    expect(screen.getByRole('heading', { name: /중요한 구조적 문제가 발견됐습니다/i })).toBeInTheDocument();
    expect(screen.getByText('29,000원 ~ 49,000원')).toBeInTheDocument();
    expect(screen.getByText('정밀 검증 · 준비 중')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /정밀 검증·수정 기능 준비 중/i })).toBeDisabled();
  });

  it('starts a same-session re-validation without keeping the previous workbook file', async () => {
    vi.useFakeTimers();
    render(<App />);

    fireEvent.click(screen.getAllByRole('button', { name: /샘플 결과 보기/i })[0]);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2200);
    });

    fireEvent.click(screen.getByRole('button', { name: '수정 후 다시 검사' }));

    expect(screen.getByText('직접 수정한 테스트용 파일을 다시 선택하세요.')).toBeInTheDocument();
    expect(screen.getByText('이전 검사 결과와 같은 정적 규칙으로 비교합니다. 이전 원본 파일은 보관하지 않습니다.')).toBeInTheDocument();
  });

  it('completes a same-session sample re-validation and exposes continuing finding locations', async () => {
    vi.useFakeTimers();
    render(<App />);
    fireEvent.click(screen.getAllByRole('button', { name: /샘플 결과 보기/i })[0]);
    await act(async () => { await vi.advanceTimersByTimeAsync(2200); });
    fireEvent.click(screen.getByRole('button', { name: '수정 후 다시 검사' }));
    fireEvent.click(screen.getAllByRole('button', { name: /샘플 결과 보기/i })[0]);
    await act(async () => { await vi.advanceTimersByTimeAsync(2200); });
    const group = screen.getByRole('article', { name: '계속 탐지됨' });
    fireEvent.click(group.querySelector('summary')!);
    expect(group.querySelector('details')).toHaveAttribute('open');
    expect(group).toHaveTextContent('현재 위치 —');
    expect(screen.getByRole('article', { name: '이번 재검사에서 더 이상 탐지되지 않음' })).toHaveTextContent('해당 항목이 없습니다.');
    expect(screen.getByRole('article', { name: '새롭게 탐지됨' })).toHaveTextContent('해당 항목이 없습니다.');
  });

  it('rejects unsupported files before calling the API', () => {
    render(<App />);
    const input = screen.getByLabelText('엑셀 파일 선택');
    const file = new File(['not a workbook'], 'notes.txt', { type: 'text/plain' });

    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByRole('alert')).toHaveTextContent('.xlsx와 .xlsm 파일만');
  });

  it('rejects an over-limit workbook before calling the API', () => {
    render(<App />);
    const input = screen.getByLabelText('엑셀 파일 선택');
    const file = new File(['synthetic'], 'synthetic-too-large.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    Object.defineProperty(file, 'size', { value: 10 * 1024 * 1024 + 1 });

    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByRole('alert')).toHaveTextContent('10MB');
  });
});
