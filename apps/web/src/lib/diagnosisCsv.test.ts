import { describe, expect, it } from 'vitest';
import { demoResult } from '../data/demo';
import { buildDiagnosisCsv, csvHeaders } from './diagnosisCsv';

describe('diagnosis CSV export', () => {
  it('creates a UTF-8 BOM CSV with the requested result fields and user status', () => {
    const firstFinding = demoResult.findings[0];
    const csv = buildDiagnosisCsv(demoResult, {
      [firstFinding.finding_key!]: 'REVIEWED',
    });

    expect(csv.startsWith('\uFEFF')).toBe(true);
    expect(csv).toContain(csvHeaders.join(','));
    expect(csv).toContain('action category');
    expect(csv).toContain('사용자 처리 상태');
    expect(csv).toContain('확인함');
    expect(csv).toContain(firstFinding.rule_code);
  });
});
