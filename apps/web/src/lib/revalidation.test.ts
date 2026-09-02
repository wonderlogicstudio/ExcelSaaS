import { describe, expect, it } from 'vitest';
import { demoResult } from '../data/demo';
import { compareScanResults } from './revalidation';

describe('same-session re-validation comparison', () => {
  it('separates no-longer-detected, continuing, and newly-detected findings', () => {
    const [removed, continuing, alsoContinuing, newlyDetected] = demoResult.findings;
    const previous = { ...demoResult, findings: [removed, continuing, alsoContinuing] };
    const current = {
      ...demoResult,
      findings: [continuing, alsoContinuing, newlyDetected, continuing],
    };

    const comparison = compareScanResults(previous, current);

    expect(comparison.noLongerDetected.map((finding) => finding.finding_key)).toEqual([removed.finding_key]);
    expect(comparison.stillDetected.map((finding) => finding.finding_key)).toEqual([
      continuing.finding_key,
      alsoContinuing.finding_key,
    ]);
    expect(comparison.newlyDetected.map((finding) => finding.finding_key)).toEqual([newlyDetected.finding_key]);
  });

  it('warns when scanner or rule-set versions do not match', () => {
    const comparison = compareScanResults(
      demoResult,
      { ...demoResult, scanner_version: '0.2.0', rule_set_version: '2026.09.1' },
    );

    expect(comparison.versionMismatch).toBe(true);
  });

  it('keeps the scan-limit warning from either result', () => {
    const comparison = compareScanResults(
      { ...demoResult, workbook: { ...demoResult.workbook, scan_truncated: true } },
      demoResult,
    );

    expect(comparison.previousWasTruncated).toBe(true);
    expect(comparison.currentWasTruncated).toBe(false);
  });
});
