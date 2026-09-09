import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { LegalPage } from './LegalPage';

describe('Hosted Beta legal drafts', () => {
  it('states the verified file-handling boundaries without a zero-retention claim', () => {
    render(<LegalPage kind="privacy" />);

    expect(screen.getByRole('heading', { name: '개인정보 처리 안내 초안' })).toBeInTheDocument();
    expect(screen.getByText(/자동삭제의 실제 만료 관측은 외부 초대 전에 완료해야 하는 검증 항목/)).toBeInTheDocument();
    expect(screen.getByText(/파일명, 시트명, 셀 위치, Finding key, 수식, 셀 값/)).toBeInTheDocument();
    expect(screen.getByText(/무보관 또는 즉시 삭제를 보장한다고 주장하지 않습니다/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '서비스로 돌아가기' })).toHaveAttribute('href', '/');
  });

  it('labels the beta limitations and does not imply automated repair', () => {
    render(<LegalPage kind="terms" />);

    expect(screen.getByRole('heading', { name: '이용 안내 및 Beta Notice' })).toBeInTheDocument();
    expect(screen.getByText(/Formula Pattern Candidate는 확정 오류가 아닙니다/)).toBeInTheDocument();
    expect(screen.getByText(/자동 수정, 결제 및 실제 수정 서비스는 현재 제공하지 않습니다/)).toBeInTheDocument();
  });
});
