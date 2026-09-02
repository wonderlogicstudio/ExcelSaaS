import { describe, expect, it, beforeEach } from 'vitest';
import { FEEDBACK_STORAGE_KEY, LocalFeedbackRepository } from './feedback';

describe('LocalFeedbackRepository', () => {
  beforeEach(() => window.localStorage.clear());

  it('stores only the approved, value-free feedback fields and can clear them', () => {
    const repository = new LocalFeedbackRepository(window.localStorage);
    const record = repository.save({
      feedback_scope: 'FINDING',
      feedback_category: 'POSSIBLE_FALSE_POSITIVE',
      rule_code: 'FORMULA_PATTERN_OUTLIER',
      opaque_finding_id: '2cbb8cb0-2177-46e8-b96e-d4e75d7d5768',
      scanner_version: '0.1.3',
    });

    expect(Object.keys(record).sort()).toEqual([
      'created_at',
      'feedback_category',
      'feedback_id',
      'feedback_scope',
      'opaque_finding_id',
      'rating',
      'rule_code',
      'scanner_version',
    ]);
    expect(JSON.stringify(repository.list())).not.toContain('filename');
    expect(JSON.stringify(repository.list())).not.toContain('sheet');
    expect(JSON.stringify(repository.list())).not.toContain('formula');
    expect(JSON.stringify(repository.list())).not.toContain('memo');

    repository.clear();
    expect(repository.list()).toEqual([]);
    expect(window.localStorage.getItem(FEEDBACK_STORAGE_KEY)).toBeNull();
  });

  it('removes legacy memo text when local feedback is read', () => {
    window.localStorage.setItem(FEEDBACK_STORAGE_KEY, JSON.stringify([{
      feedback_id: 'legacy',
      feedback_scope: 'RESULT',
      feedback_category: 'OTHER',
      memo: 'do not retain this',
      scanner_version: '0.1.3',
      created_at: '2026-09-02T00:00:00Z',
    }]));
    const repository = new LocalFeedbackRepository(window.localStorage);
    expect(JSON.stringify(repository.list())).not.toContain('memo');
    expect(window.localStorage.getItem(FEEDBACK_STORAGE_KEY)).not.toContain('memo');
  });
});
