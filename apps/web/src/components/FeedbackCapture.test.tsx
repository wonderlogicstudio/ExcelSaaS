import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { ResultFeedbackPanel } from './FeedbackCapture';
import { LocalFeedbackRepository } from '../lib/feedback';

describe('FeedbackCapture', () => {
  beforeEach(() => window.localStorage.clear());

  it('keeps a test result opinion in the local repository and allows deletion', async () => {
    const repository = new LocalFeedbackRepository(window.localStorage);
    render(<ResultFeedbackPanel repository={repository} scannerVersion="0.1.3" />);

    fireEvent.change(screen.getByLabelText('결과 의견 유형'), {
      target: { value: 'NEEDS_REPAIR_OR_REVIEW_COPY' },
    });
    fireEvent.click(screen.getByRole('button', { name: '의견 저장' }));

    await waitFor(() => {
      expect(screen.getByText('이 브라우저에만 저장했습니다.')).toBeInTheDocument();
    });
    expect(repository.list()).toMatchObject([{
      feedback_scope: 'RESULT',
      feedback_category: 'NEEDS_REPAIR_OR_REVIEW_COPY',
      scanner_version: '0.1.3',
      rule_code: null,
      opaque_finding_id: null,
    }]);

    fireEvent.click(screen.getByRole('button', { name: '이 브라우저의 테스트 의견 삭제' }));
    expect(repository.list()).toEqual([]);
  });
});
