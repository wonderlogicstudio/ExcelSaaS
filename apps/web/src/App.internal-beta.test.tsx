import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

describe('WorkbookCare internal formula-audit entry', () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it('places the separate M4 audit before a long free Finding list after an uploaded scan', async () => {
    vi.stubEnv('VITE_FORMULA_AUDIT_INTERNAL_BETA_ENABLED', 'true');
    vi.stubGlobal('fetch', vi.fn(async () => {
      const { demoResult } = await import('./data/demo');
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ...demoResult,
          filename: 'm4c-synthetic.xlsx',
          workbook: {
            ...demoResult.workbook,
            formula_count: 12,
            scan_truncated: false,
          },
        }),
      };
    }));

    const { default: App } = await import('./App');
    render(<App />);

    const input = screen.getByLabelText('엑셀 파일 선택');
    fireEvent.change(input, {
      target: {
        files: [
          new File(['synthetic workbook payload'], 'm4c-synthetic.xlsx', {
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          }),
        ],
      },
    });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '수식 패턴 정밀검사' })).toBeInTheDocument();
    });

    const auditSection = document.querySelector('#formula-audit');
    const freeResults = document.querySelector('#results');
    if (!auditSection || !freeResults) {
      throw new Error('Expected both the internal audit and free Results sections.');
    }
    expect(
      auditSection.compareDocumentPosition(freeResults) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
  });
});
