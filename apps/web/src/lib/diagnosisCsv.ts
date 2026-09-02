import type { FindingUserStatus, ScanResult } from '../types';
import { findingIdentity } from './revalidation';

export const userStatusLabel: Record<FindingUserStatus, string> = {
  UNREVIEWED: '확인 전',
  REVIEWED: '확인함',
  PLANNED_REPAIR: '수정 예정',
  IGNORED: '무시',
  MARKED_NORMAL: '정상으로 판단',
};

export const csvHeaders = [
  '검사 파일명',
  '검사 일시',
  'scanner version',
  'rule set version',
  '검사 범위',
  'scan truncated 여부',
  'rule code',
  'severity',
  'action category',
  'sheet',
  'cell 또는 range',
  '발견된 사실',
  '발생 가능한 영향',
  '탐지 근거',
  '사용자 권장 행동',
  'Excel 확인 방법',
  '현재 검사 한계',
  '사용자 처리 상태',
] as const;

function escapeCsv(value: string | number | boolean | null | undefined): string {
  const text = value === null || value === undefined ? '' : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function buildDiagnosisCsv(
  result: ScanResult,
  statuses: Record<string, FindingUserStatus>,
): string {
  const rows = result.findings.map((finding) => {
    const guidance = finding.guidance;
    const status = statuses[findingIdentity(finding)] ?? 'UNREVIEWED';
    return [
      result.filename,
      result.scanned_at,
      result.scanner_version,
      result.rule_set_version,
      '무료 정적 구조 검사',
      result.workbook.scan_truncated ? '예' : '아니요',
      finding.rule_code,
      finding.severity,
      guidance?.action_category ?? 'INFO_ONLY',
      finding.sheet ?? '',
      finding.cell ?? '',
      guidance?.detected_fact ?? finding.description,
      guidance?.possible_impact ?? '',
      guidance?.evidence_grade ?? 'REFERENCE_SIGNAL',
      guidance?.recommended_next_action ?? '',
      guidance?.how_to_check_in_excel.join(' / ') ?? '',
      guidance?.unchecked_scope.join(' / ') ?? '',
      userStatusLabel[status],
    ];
  });

  return `\uFEFF${[csvHeaders, ...rows].map((row) => row.map(escapeCsv).join(',')).join('\r\n')}`;
}

export function downloadDiagnosisCsv(
  result: ScanResult,
  statuses: Record<string, FindingUserStatus>,
): void {
  const blob = new Blob([buildDiagnosisCsv(result, statuses)], {
    type: 'text/csv;charset=utf-8',
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'workbookcare-diagnosis.csv';
  anchor.click();
  URL.revokeObjectURL(url);
}
