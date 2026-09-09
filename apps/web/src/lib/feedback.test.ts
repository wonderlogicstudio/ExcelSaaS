import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  FEEDBACK_STORAGE_KEY,
  HostedFormulaAuditFeedbackRepository,
  LocalFeedbackRepository,
} from './feedback';

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

  it('sends only the hosted Formula Audit allowlist and retains no browser record', async () => {
    const calls: Array<[string, RequestInit | undefined]> = [];
    const send = vi.fn(async (input: string, init?: RequestInit) => {
      calls.push([input, init]);
      return new Response(null, { status: 202 });
    });
    const repository = new HostedFormulaAuditFeedbackRepository(send as typeof fetch);

    await repository.save({
      feedback_scope: 'FINDING',
      feedback_category: 'POSSIBLE_FALSE_POSITIVE',
      rule_code: 'FORMULA_PATTERN_OUTLIER',
      opaque_finding_id: 'never-sent',
      subtype: 'REFERENCE_CELL_DRIFT',
      scanner_version: 'ignored-by-hosted-repository',
    });

    expect(calls).toHaveLength(1);
    const [, init] = calls[0]!;
    expect(init).toBeDefined();
    const requestInit = init!;
    expect(requestInit.method).toBe('POST');
    const body = JSON.parse(requestInit.body as string);
    expect(Object.keys(body).sort()).toEqual([
      'feedback_category',
      'feedback_session_id',
      'rule_code',
      'subtype',
    ]);
    expect(JSON.stringify(body)).not.toContain('never-sent');
    expect(repository.list()).toEqual([]);
  });

  it('rejects an unsupported hosted category without sending it', async () => {
    const send = vi.fn();
    const repository = new HostedFormulaAuditFeedbackRepository(send as typeof fetch);

    await expect(repository.save({
      feedback_scope: 'FINDING',
      feedback_category: 'NOT_HELPFUL',
      rule_code: 'FORMULA_PATTERN_OUTLIER',
      subtype: 'REFERENCE_CELL_DRIFT',
      scanner_version: '0.1.3',
    })).rejects.toThrow('INVALID_HOSTED_FEEDBACK');
    expect(send).not.toHaveBeenCalled();
  });
});
