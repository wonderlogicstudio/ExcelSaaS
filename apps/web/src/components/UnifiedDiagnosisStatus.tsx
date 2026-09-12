import type { FindingUserStatus, FormulaAuditResult } from '../types';
import { formulaAuditStatusCopy } from './FormulaAuditPanel';

export interface IntegratedFormulaAudit {
  result: FormulaAuditResult | null;
  busy: boolean;
  error: string | null;
  blockedReason: string | null;
  statuses: Record<string, FindingUserStatus>;
  onRetry: () => void;
  onStatusChange: (findingKey: string, status: FindingUserStatus) => void;
}

export function integratedAuditState(audit: IntegratedFormulaAudit) {
  if (audit.busy) return { label: '검사 중', detail: '주변 수식의 반복 패턴을 확인하고 있습니다.', complete: false };
  if (audit.error) return { label: '완료하지 못함', detail: audit.error, complete: false };
  if (audit.blockedReason) return { label: '미실행', detail: audit.blockedReason, complete: false };
  if (audit.result?.status === 'COMPLETED') return {
    label: `완료 · 검토 후보 ${audit.result.candidates.length}건`,
    detail: '패턴 차이는 검토 후보이며, 잘못된 수식이나 업무 정답을 확정하지 않습니다.', complete: true,
  };
  if (audit.result) return { ...formulaAuditStatusCopy[audit.result.status], detail: formulaAuditStatusCopy[audit.result.status].description, complete: false };
  return { label: '대기', detail: '구조 검사에 이어 수식 패턴을 확인합니다.', complete: false };
}

export function UnifiedDiagnosisStatus({ audit, truncated, compact = false }: { audit: IntegratedFormulaAudit; truncated: boolean; compact?: boolean }) {
  const state = integratedAuditState(audit);
  return <section className="diagnosis-status" aria-label="검사 진행과 범위">
    <div className="diagnosis-status__checks" aria-live="polite">
      <p><strong>구조 위험 검사</strong><span>{truncated ? '부분 완료' : '완료'}</span></p>
      <p><strong>수식 패턴 검사</strong><span data-audit-status={state.complete ? 'COMPLETED' : audit.busy ? 'PENDING' : 'INCOMPLETE'}>{compact && state.complete ? '완료' : state.label}</span></p>
    </div>
    <p className="diagnosis-status__detail">{state.detail}</p>
    {audit.error && <p role="alert">수식 패턴 검사를 완료하지 못했습니다. 구조 검사 결과는 유지됩니다. {audit.error}</p>}
    {!audit.busy && !audit.blockedReason && (audit.error || audit.result?.status === 'FAILED') &&
      <button className="button button--outline button--small" type="button" onClick={audit.onRetry}>완료하지 못한 검사 다시 시도</button>}
    <details className="diagnosis-status__scope">
      <summary>검사 범위와 한계</summary>
      <p>파일 구조·명시적 수식 오류·외부 참조·숨김 구조와 지원하는 A1 수식의 주변 반복 패턴을 검사합니다. 같은 셀에 다른 규칙이 적용되면 각각 한 항목으로 셉니다.</p>
      <p>구조 위험과 수식 검토 후보를 한 목록에서 보여줍니다. 기존 구조 위험 점수·견적·CSV·직접 재검사 비교에는 구조 검사 결과만 반영합니다.</p>
      <p>Excel 계산 결과·업무 규칙은 검증하지 않습니다. 수식·매크로·외부 연결을 실행하거나 원본 파일을 수정하지 않습니다.</p>
      {truncated && <p>안전 제한으로 일부 셀만 검사했습니다. 전체 파일을 검사한 결과가 아닙니다.</p>}
      {audit.result && <p>수식 패턴 검사: 수식 셀 {audit.result.formula_cell_count.toLocaleString('ko-KR')}개 · 검사 시트 {audit.result.audited_sheet_count}개 · 후보 영역 {audit.result.audited_formula_region_count}개</p>}
    </details>
  </section>;
}
