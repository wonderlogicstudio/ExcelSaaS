import { CheckCircle2, CircleHelp, FileSearch, LoaderCircle, ShieldAlert } from 'lucide-react';
import type {
  Finding,
  FindingUserStatus,
  FormulaAuditResult,
  FormulaAuditStatus,
  ScanResult,
} from '../types';
import { userStatusLabel } from '../lib/diagnosisCsv';
import type { FeedbackCategory, FeedbackRepository } from '../lib/feedback';

interface FormulaAuditPanelProps {
  baseResult: ScanResult;
  sourceFile: File | null;
  auditResult: FormulaAuditResult | null;
  busy: boolean;
  error: string | null;
  statuses: Record<string, FindingUserStatus>;
  feedbackRepository: FeedbackRepository | null;
  onRun: () => void;
  onStatusChange: (findingKey: string, status: FindingUserStatus) => void;
}

const userStatusOptions: FindingUserStatus[] = [
  'UNREVIEWED',
  'REVIEWED',
  'PLANNED_REPAIR',
  'IGNORED',
  'MARKED_NORMAL',
];

const statusCopy: Record<FormulaAuditStatus, { label: string; description: string }> = {
  COMPLETED: {
    label: '분석 완료',
    description: '후보가 없더라도 파일의 수식이나 계산 결과가 정확하다는 뜻은 아닙니다.',
  },
  ABSTAINED_INSUFFICIENT_EVIDENCE: {
    label: '근거 부족으로 유보',
    description: '비교할 수 있는 주변 패턴이 충분하지 않아 후보를 만들지 않았습니다.',
  },
  SKIPPED_TRUNCATED: {
    label: '잘린 검사로 생략',
    description: '기본 검사 범위가 완전하지 않아 수식 패턴 정밀검사를 실행하지 않았습니다.',
  },
  SKIPPED_FORMULA_LIMIT: {
    label: '수식 셀 한도로 생략',
    description: '내부 베타의 검증된 수식 셀 범위(1~30,000개)를 넘었습니다.',
  },
  SKIPPED_WORKBOOK_LIMIT: {
    label: '워크북 규모 한도로 생략',
    description: '이 내부 베타에서 검증한 시트 수 범위를 넘어 정밀검사를 실행하지 않았습니다.',
  },
  SKIPPED_CANDIDATE_LIMIT: {
    label: '후보 수 한도로 유보',
    description: '일부 후보만 보여 주지 않기 위해 정밀검사 결과를 유보했습니다.',
  },
  SKIPPED_UNSUPPORTED_STRUCTURE: {
    label: '미지원 구조로 생략',
    description: '지원하지 않는 수식 구조는 안전하게 후보화하지 않습니다.',
  },
  FAILED: {
    label: '감사 실패, 기본 결과 유지',
    description: '수식 패턴 정밀검사를 완료하지 못했습니다. 무료 진단 결과는 바뀌지 않습니다.',
  },
};

function candidateIdentity(candidate: Finding): string {
  return candidate.finding_key ?? candidate.id;
}

function eligibleMessage(baseResult: ScanResult, sourceFile: File | null): string | null {
  if (!sourceFile) {
    return '샘플 결과에는 실행하지 않습니다. 같은 브라우저에서 선택한 테스트용 파일로만 실행할 수 있습니다.';
  }
  if (baseResult.workbook.scan_truncated) {
    return '기본 무료 진단이 일부 셀만 검사해 이번 수식 패턴 정밀검사는 실행하지 않습니다.';
  }
  if (baseResult.workbook.formula_count === 0) {
    return '기본 무료 진단에서 수식 셀을 찾지 못해 비교할 수 있는 수식 패턴이 없습니다.';
  }
  if (baseResult.workbook.formula_count > 30_000) {
    return '수식 셀이 30,000개를 넘어 내부 베타의 검증된 범위에서는 실행하지 않습니다.';
  }
  return null;
}

function FormulaAuditFindingCard({
  candidate,
  status,
  scannerVersion,
  feedbackRepository,
  onStatusChange,
}: {
  candidate: Finding;
  status: FindingUserStatus;
  scannerVersion: string;
  feedbackRepository: FeedbackRepository | null;
  onStatusChange: (status: FindingUserStatus) => void;
}) {
  const evidence = candidate.formula_pattern;
  const identity = candidateIdentity(candidate);
  const saveFeedback = (category: FeedbackCategory) => {
    feedbackRepository?.save({
      feedback_scope: 'FINDING',
      feedback_category: category,
      rating: category === 'HELPFUL' ? 'POSITIVE' : null,
      rule_code: candidate.rule_code,
      opaque_finding_id: candidate.id,
      scanner_version: scannerVersion,
    });
  };

  return (
    <details className="formula-audit-finding">
      <summary className="formula-audit-finding__summary">
        <span className="severity severity--warning">주의</span>
        <code>{candidate.rule_code}</code>
        <strong>{candidate.title}</strong>
        <span className="formula-audit-finding__location">{[candidate.sheet, candidate.cell].filter(Boolean).join(' · ')}</span>
        <span className="formula-audit-finding__hint" aria-hidden="true">자세히 보기</span>
      </summary>
      <div className="formula-audit-finding__details">
        <dl className="formula-audit-finding__evidence">
          <div><dt>발견된 사실</dt><dd>{evidence?.evidence_summary ?? candidate.description}</dd></div>
          <div><dt>주변 패턴과 현재 패턴의 차이</dt><dd>{evidence?.current_pattern_summary ?? '현재 패턴을 주변 반복 수식과 비교했습니다.'}</dd></div>
          <div><dt>비교에 사용한 주변 위치</dt><dd>{(evidence?.comparison_locations ?? evidence?.evidence_locations ?? []).join(' · ') || '비교 위치 정보가 없습니다.'}</dd></div>
          <div><dt>검사한 수식 영역</dt><dd>{evidence?.formula_region ?? '지원 범위의 주변 수식 영역'}</dd></div>
          <div><dt>업무적으로 정상일 수 있는 경우</dt><dd>{evidence?.normal_case_possibility ?? '업무상 의도된 예외 수식 또는 입력인 경우'}</dd></div>
          <div><dt>Excel에서 확인하는 방법</dt><dd>{candidate.guidance?.how_to_check_in_excel.join(' · ') ?? '표시된 위치와 주변 수식을 Excel에서 직접 비교하세요.'}</dd></div>
          <div><dt>현재 검사에서 확인하지 않은 내용</dt><dd>{candidate.guidance?.unchecked_scope.join(' ') ?? evidence?.current_limitations.join(' ')}</dd></div>
        </dl>

        <label className="finding__status-control">
          <span>사용자 처리 상태</span>
          <select
            aria-label={`${candidate.rule_code} 수식 감사 사용자 처리 상태`}
            value={status}
            onChange={(event) => onStatusChange(event.target.value as FindingUserStatus)}
          >
            {userStatusOptions.map((option) => <option key={option} value={option}>{userStatusLabel[option]}</option>)}
          </select>
        </label>

        {feedbackRepository && (
          <div className="formula-audit-feedback" aria-label="수식 패턴 정밀검사 의견">
            <strong>이 후보 설명은 어땠나요?</strong>
            <div>
              <button type="button" onClick={() => saveFeedback('HELPFUL')}>도움이 됨</button>
              <button type="button" onClick={() => saveFeedback('POSSIBLE_FALSE_POSITIVE')}>오탐 의심</button>
              <button type="button" onClick={() => saveFeedback('EXPLANATION_INSUFFICIENT')}>설명 부족</button>
            </div>
            <small>의견 유형만 이 브라우저에 저장합니다. 메모와 파일 내용은 입력·전송하지 않습니다.</small>
          </div>
        )}
      </div>
    </details>
  );
}

export function FormulaAuditPanel({
  baseResult,
  sourceFile,
  auditResult,
  busy,
  error,
  statuses,
  feedbackRepository,
  onRun,
  onStatusChange,
}: FormulaAuditPanelProps) {
  const blockedReason = eligibleMessage(baseResult, sourceFile);
  const resultStatus = auditResult ? statusCopy[auditResult.status] : null;
  const candidateLabel = auditResult?.status === 'COMPLETED'
    ? auditResult.candidates.length > 0 ? '후보 있음' : '후보 없음'
    : resultStatus?.label;

  return (
    <section className="formula-audit-section" id="formula-audit" aria-labelledby="formula-audit-title">
      <div className="shell">
        <div className="formula-audit-panel">
          <div className="formula-audit-panel__header">
            <div>
              <span className="card-label"><FileSearch size={15} />내부 베타 · 선택형 검사</span>
              <h2 id="formula-audit-title">수식 패턴 정밀검사</h2>
              <p>기본 무료 진단과 분리된 검사입니다. 주변 수식과 다른 패턴 후보만 보여 주며, 수식이 잘못됐는지나 계산 결과의 정답은 판단하지 않습니다.</p>
            </div>
            <span className="formula-audit-panel__separation">기본 위험 점수·견적·CSV에 반영하지 않음</span>
          </div>

          <div className="formula-audit-panel__scope">
            <article><strong>검사 범위</strong><p>지원하는 A1 참조 수식에서 같은 열의 주변 반복 패턴을 비교합니다.</p></article>
            <article><strong>실행 조건</strong><p>기본 진단 완료 · 잘리지 않음 · 수식 셀 1~30,000개 · 같은 브라우저 파일 재전송</p></article>
            <article><strong>확인하지 않음</strong><p>계산 결과, 업무 규칙, 정답 수식, 자동 수정과 수정본 생성</p></article>
          </div>

          <div className="formula-audit-panel__action" aria-live="polite">
            {busy ? (
              <><LoaderCircle className="formula-audit-panel__spinner" size={20} /><div><strong>분석 중</strong><p>수식 패턴을 비교하고 있습니다. 완료 전에는 진행률이나 남은 시간을 표시하지 않습니다.</p></div></>
            ) : blockedReason ? (
              <><CircleHelp size={20} /><div><strong>실행 전</strong><p>{blockedReason}</p></div></>
            ) : (
              <><CheckCircle2 size={20} /><div><strong>{candidateLabel ?? '실행 전'}</strong><p>{resultStatus?.description ?? '같은 브라우저에서 선택한 파일을 다시 전송해 수식 패턴을 비교합니다. 서버에 파일을 보관하는 방식이 아닙니다.'}</p></div></>
            )}
            <button className="button button--primary button--small" type="button" disabled={busy || Boolean(blockedReason)} onClick={onRun}>
              {auditResult ? '수식 패턴 정밀검사 다시 실행' : '수식 패턴 정밀검사 실행'}
            </button>
          </div>

          {error && <p className="formula-audit-panel__error" role="alert">감사 실패, 기본 결과 유지 — {error}</p>}

          {auditResult && (
            <>
              <div className="formula-audit-panel__metrics">
                <span><strong>{auditResult.formula_cell_count.toLocaleString('ko-KR')}</strong> 수식 셀</span>
                <span><strong>{auditResult.audited_sheet_count}</strong> 검사 시트</span>
                <span><strong>{auditResult.audited_formula_region_count}</strong> 후보 수식 영역</span>
                <span><strong>{auditResult.elapsed_ms ?? 0}ms</strong> 처리시간</span>
              </div>

              {auditResult.status === 'COMPLETED' && auditResult.candidates.length > 0 && (
                <div className="formula-audit-finding-list">
                  <div className="panel-heading"><div><span className="card-label">수식 패턴 이상 후보</span><h3>사용자 확인 필요 항목</h3></div><span>{auditResult.candidates.length}개 · 클릭해 자세히 보기</span></div>
                  {auditResult.candidates.map((candidate) => (
                    <FormulaAuditFindingCard
                      key={candidateIdentity(candidate)}
                      candidate={candidate}
                      status={statuses[candidateIdentity(candidate)] ?? 'UNREVIEWED'}
                      scannerVersion={auditResult.scanner_version}
                      feedbackRepository={feedbackRepository}
                      onStatusChange={(status) => onStatusChange(candidateIdentity(candidate), status)}
                    />
                  ))}
                </div>
              )}

              {auditResult.status === 'COMPLETED' && auditResult.candidates.length === 0 && (
                <p className="formula-audit-panel__empty">이번 정밀검사 범위에서 수식 패턴 이상 후보를 만들지 않았습니다. 파일의 수식, 계산 결과, 업무 규칙이 정확하다는 뜻은 아닙니다.</p>
              )}

              {auditResult.limitations.length > 0 && (
                <div className="formula-audit-panel__limits"><ShieldAlert size={18} /><div><strong>이번 수식 패턴 정밀검사의 한계</strong><ul>{auditResult.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div></div>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
