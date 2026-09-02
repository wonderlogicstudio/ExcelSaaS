import type { Finding, ScanResult } from '../types';

export interface RevalidationComparison {
  versionMismatch: boolean;
  previousWasTruncated: boolean;
  currentWasTruncated: boolean;
  noLongerDetected: Finding[];
  stillDetected: Finding[];
  newlyDetected: Finding[];
}

export function findingIdentity(finding: Finding): string {
  if (finding.finding_key) return finding.finding_key;

  const location = [finding.sheet, finding.cell]
    .filter((value): value is string => Boolean(value?.trim()))
    .map((value) => value.trim().toLocaleLowerCase('en-US'))
    .join('|');
  return location ? `${finding.rule_code}|${location}` : finding.rule_code;
}

function indexUniqueFindings(findings: Finding[]): Map<string, Finding> {
  const indexed = new Map<string, Finding>();
  for (const finding of findings) {
    const key = findingIdentity(finding);
    if (!indexed.has(key)) indexed.set(key, finding);
  }
  return indexed;
}

/**
 * Compare two static scan results from one open browser session.
 * A missing key only means the same static rule did not detect that location
 * this time; it does not prove a business error was fixed.
 */
export function compareScanResults(
  previous: ScanResult,
  current: ScanResult,
): RevalidationComparison {
  const previousFindings = indexUniqueFindings(previous.findings);
  const currentFindings = indexUniqueFindings(current.findings);

  const noLongerDetected = [...previousFindings.entries()]
    .filter(([key]) => !currentFindings.has(key))
    .map(([, finding]) => finding);
  const stillDetected = [...currentFindings.entries()]
    .filter(([key]) => previousFindings.has(key))
    .map(([, finding]) => finding);
  const newlyDetected = [...currentFindings.entries()]
    .filter(([key]) => !previousFindings.has(key))
    .map(([, finding]) => finding);

  return {
    versionMismatch: previous.scanner_version !== current.scanner_version
      || previous.rule_set_version !== current.rule_set_version,
    previousWasTruncated: previous.workbook.scan_truncated,
    currentWasTruncated: current.workbook.scan_truncated,
    noLongerDetected,
    stillDetected,
    newlyDetected,
  };
}
