import type { FindingCounts, ScanResult } from '../types';

// Derive from existing fields as well, for older scan responses without counts.
export function findingCounts(result: ScanResult): FindingCounts {
  return {
    total_detected: result.summary.issue_count,
    returned_details: result.findings.length,
    omitted_details: Math.max(0, result.summary.issue_count - result.findings.length),
    scan_complete: !result.workbook.scan_truncated,
  };
}
