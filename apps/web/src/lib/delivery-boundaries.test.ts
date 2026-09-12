import { describe, expect, it } from 'vitest';
import { demoResult } from '../data/demo';
import { buildDiagnosisCsv } from './diagnosisCsv';
import { compareScanResults } from './revalidation';

describe('D01 observed gaps', () => {
  it.each(['=1+1', '+1+1', '-1+1', '@SUM(A1)', '  =1+1', '\t=1+1', '\r=1+1', '\n=1+1'])('neutralizes a formula-like filename %j without dropping its row', (filename) => {
    const csv = buildDiagnosisCsv({ ...demoResult, filename, findings: demoResult.findings.slice(0, 1) }, {});
    const firstField = csv.slice(csv.indexOf('\r\n') + 2).split(',')[0];
    expect(firstField.replace(/^"/, '')).toMatch(/^'/);
  });

  it('reports omitted finding details as incomplete comparison coverage', () => {
    const current = { ...demoResult, findings: [] };
    expect(compareScanResults(demoResult, current)).toMatchObject({
      comparisonComplete: false,
      previousOmittedCount: 0,
      currentOmittedCount: demoResult.summary.issue_count,
    });
  });
});
