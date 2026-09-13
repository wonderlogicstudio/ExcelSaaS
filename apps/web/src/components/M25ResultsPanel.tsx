import { reviewNoteLabel } from '../lib/reviewNotes';
import type { ReviewSelection } from '../lib/repairReview';
import { ReviewChoice } from './RepairReview';
import { useRef, useState } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  Check,
  CheckCircle2,
  ChevronRight,
  Download,
  FileClock,
  Info,
  ListChecks,
  RotateCcw,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import type {
  ActionCategory,
  EvidenceGrade,
  Finding,
  FindingUserStatus,
  RepairClass,
  ScanResult,
  Severity,
} from '../types';
import { downloadDiagnosisCsv, userStatusLabel } from '../lib/diagnosisCsv';
import { findingIdentity, type RevalidationComparison } from '../lib/revalidation';
import { formatFileSize, formatPriceRange } from '../lib/format';
import type { FeedbackRepository } from '../lib/feedback';
import { FindingFeedbackControl, ResultFeedbackPanel } from './FeedbackCapture';
import { RevalidationPanel } from './RevalidationPanel';
import { FindingViews } from './FindingViews';
import { GeneralFindingGuidance, ProgressiveFindingViews } from './ProgressiveFindingViews';
import { UnifiedDiagnosisStatus, integratedAuditState, type IntegratedFormulaAudit } from './UnifiedDiagnosisStatus';
import { findingCounts } from '../lib/findingCounts';
import { diagnosisCsvArtifact, displayedProducts } from '../lib/products';

interface ResultsPanelProps {
  guided?: boolean; sourceFile?: File | null; reviewReady?: boolean; onContinueReview?: () => void;
  reviewSelection?: ReviewSelection;
  result: ScanResult;
  formulaAudit?: IntegratedFormulaAudit;
  isDemo: boolean;
  statuses?: Record<string, FindingUserStatus>;
  revalidationComparison?: RevalidationComparison | null;
  onStatusChange?: (findingKey: string, status: FindingUserStatus) => void;
  feedbackRepository?: FeedbackRepository | null;
  onPrepareRevalidation?: () => void;
  onReset: () => void;
}

interface FindingTypeSummary {
  ruleCode: string;
  title: string;
  count: number;
  severity: Severity;
}

const severityLabel: Record<Severity, string> = {
  critical: '중요',
  warning: '주의',
  info: '참고',
};

const repairLabel: Record<RepairClass, string> = {
  SAFE_CANDIDATE: '안전 수정 후보',
  CONFIRMATION_REQUIRED: '사용자 확인 필요',
  EXPERT_REVIEW: '전문가 검토 필요',
  INFORMATION_ONLY: '정보 제공 · 즉시 수정 불필요',
};

const actionCategoryLabel: Record<ActionCategory, string> = {
  FIX_RECOMMENDED: '수정 또는 확인 우선 권장',
  USER_CONFIRMATION: '사용자 확인 필요',
  DEEP_VALIDATION_REQUIRED: '정밀 검증 필요',
  INFO_ONLY: '정보 제공',
};

const evidenceGradeLabel: Record<EvidenceGrade, string> = {
  DIRECT_CONFIRMATION: '직접 확인',
  PATTERN_INFERENCE: '패턴 추정',
  REFERENCE_SIGNAL: '참고 신호',
};

const userStatusOptions: FindingUserStatus[] = [
  'UNREVIEWED',
  'REVIEWED',
  'PLANNED_REPAIR',
  'IGNORED',
  'MARKED_NORMAL',
];

type SeverityFilter = 'all' | 'priority' | Severity;

function findingSheetOption(finding: Finding): string {
  return finding.sheet ? `sheet:${finding.sheet}` : 'workbook';
}

const completedScope = [
  '파일 구조 검사',
  '수식 문자열의 명시적 오류 검사',
  '외부 통합문서 참조·숨김 구조 검사',
  '제한적인 데이터 형식·성능 위험 검사',
];

const uncheckedScope = [
  '수식 패턴 이탈·누락 검사',
  'Excel 계산 결과 검증',
  '업무 규칙 검증',
  '회귀·통계 모델 검증',
  'VBA·Power Query 실행',
  '자동화 설계',
];

function SeverityIcon({ severity }: { severity: Severity }) {
  if (severity === 'critical') return <AlertOctagon size={18} />;
  if (severity === 'warning') return <AlertTriangle size={18} />;
  return <Info size={18} />;
}

function summarizeFindingTypes(findings: Finding[]): FindingTypeSummary[] {
  const grouped = new Map<string, FindingTypeSummary>();
  for (const finding of findings) {
    const existing = grouped.get(finding.rule_code);
    if (existing) {
      existing.count += 1;
    } else {
      grouped.set(finding.rule_code, {
        ruleCode: finding.rule_code,
        title: finding.title,
        count: 1,
        severity: finding.severity,
      });
    }
  }
  return [...grouped.values()];
}

function uniqueRecommendedChecks(findings: Finding[]): string[] {
  return [...new Set(findings.flatMap((finding) => finding.guidance?.recommended_next_checks ?? []))];
}

function uniqueNextActions(findings: Finding[]): string[] {
  return [...new Set(findings.map((finding) => finding.guidance?.recommended_next_action).filter(Boolean))] as string[];
}

function FindingExplanation({ finding }: { finding: Finding }) {
  const guidance = finding.guidance;
  const unchecked = guidance?.unchecked_scope ?? [
    'Excel 계산 결과와 업무적 정확성은 이번 검사에서 확인하지 않았습니다.',
  ];
  const nextChecks = guidance?.recommended_next_checks ?? [
    '발견 위치와 관련 수식·구조의 추가 확인',
  ];
  const howToCheck = guidance?.how_to_check_in_excel ?? ['표시된 위치를 Excel에서 직접 확인'];
  const normalConditions = guidance?.when_it_may_be_normal ?? ['업무상 의도된 구조 또는 수식인 경우'];
  const actionConditions = guidance?.when_action_is_recommended ?? ['표시된 위치의 의도가 불명확한 경우'];

  return <>
        <dl className="finding__evidence">
          <div><dt>발견된 사실</dt><dd>{guidance?.detected_fact ?? finding.description}</dd></div>
          <div><dt>발생 가능한 영향</dt><dd>{guidance?.possible_impact ?? '이 항목의 영향은 추가 확인이 필요합니다.'}</dd></div>
          <div><dt>사용자 권장 행동</dt><dd>{guidance?.recommended_next_action ?? '표시된 위치를 직접 확인하세요.'}</dd></div>
          <div><dt>Excel에서 확인하는 방법</dt><dd>{howToCheck.join(' · ')}</dd></div>
          <div><dt>정상일 수 있는 조건</dt><dd>{normalConditions.join(' ')}</dd></div>
          <div><dt>조치를 우선 권장하는 경우</dt><dd>{actionConditions.join(' ')}</dd></div>
          <div><dt>이번 검사에서 확인하지 않은 내용</dt><dd>{unchecked.join(' ')}</dd></div>
          <div><dt>다음 정밀검증 항목</dt><dd>{nextChecks.join(' · ')}</dd></div>
        </dl>
  </>;
}

function FindingClassification({ finding }: { finding: Finding }) {
  const repairReadiness = finding.guidance?.repair_readiness;
  const evidenceGrade = finding.guidance?.evidence_grade ?? 'REFERENCE_SIGNAL';
  const actionCategory = finding.guidance?.action_category ?? 'INFO_ONLY';
  return <>
        {repairReadiness && (
          <div className="finding__repair-path">
            <strong>향후 해결 경로</strong>
            <span>{repairReadiness.label} · 준비 중</span>
            <p>{repairReadiness.explanation}</p>
            {repairReadiness.required_steps.length > 0 && (
              <small>{repairReadiness.required_steps.join(' → ')}</small>
            )}
          </div>
        )}
        <div className="finding__meta">
          <span>{repairLabel[finding.repair_class]}</span>
          <span>다음 행동: {actionCategoryLabel[actionCategory]}</span>
          <span>탐지 확실도: {evidenceGradeLabel[evidenceGrade]}</span>
        </div>
  </>;
}

function FindingCard({
  finding,
  status,
  onStatusChange,
  feedbackRepository,
  scannerVersion,
  sharedGuidance = false,
}: {
  finding: Finding;
  status: FindingUserStatus;
  onStatusChange: (status: FindingUserStatus) => void;
  feedbackRepository?: FeedbackRepository | null;
  scannerVersion: string;
  sharedGuidance?: boolean;
}) {

  return (
    <details className={`finding finding--${finding.severity}`}>
      <summary className="finding__summary">
      <div className="finding__icon" aria-hidden="true"><SeverityIcon severity={finding.severity} /></div>
      <div className="finding__body">
        <div className="finding__heading">
          <span className={`severity severity--${finding.severity}`}>{severityLabel[finding.severity]}</span>
          {!sharedGuidance && <code>{finding.rule_code}</code>}
          {sharedGuidance && !finding.sheet && !finding.cell && <span>통합문서 전체</span>}
          {(finding.sheet || finding.cell) && (
            <span className="finding__location">{[finding.sheet, finding.cell].filter(Boolean).join(' · ')}</span>
          )}
        </div>
        {sharedGuidance
          ? <p className="finding__handling-summary">{userStatusLabel[status]}</p>
          : <h4>{finding.title}</h4>}
      </div>
      <span className="finding__summary-hint" aria-hidden="true">자세히 보기</span>
      </summary>
      <div className="finding__details">
        {sharedGuidance ? <p>{finding.description}</p> : <FindingExplanation finding={finding} />}
        <FindingClassification finding={finding} />
        <label className="finding__status-control">
          <span>사용자 처리 상태</span>
          <select
            aria-label={`${finding.rule_code} 사용자 처리 상태`}
            value={status}
            onChange={(event) => onStatusChange(event.target.value as FindingUserStatus)}
          >
            {userStatusOptions.map((option) => (
              <option key={option} value={option}>{userStatusLabel[option]}</option>
            ))}
          </select>
        </label>
        {feedbackRepository && (
          <FindingFeedbackControl
            repository={feedbackRepository}
            scannerVersion={scannerVersion}
            ruleCode={finding.rule_code}
            opaqueFindingId={finding.id}
          />
        )}
      </div>
    </details>
  );
}

function ScanScopeCard({ truncated }: { truncated: boolean }) {
  return (
    <section className="scan-scope-card" aria-labelledby="scan-scope-title">
      <div>
        <span className="card-label">무료 진단 범위</span>
        <h2 id="scan-scope-title">이번 무료 진단에서 확인한 범위</h2>
        <p>이번 진단은 파일 구조, 수식 문자열, 제한적인 데이터 패턴에서 위험 신호를 찾는 정적 검사입니다.</p>
      </div>
      <div className="scan-scope-card__lists">
        <div>
          <strong>{truncated ? '부분 수행' : '완료'}</strong>
          <ul>{completedScope.map((item) => <li key={item}><Check size={15} />{item}</li>)}</ul>
        </div>
        <div>
          <strong>미수행</strong>
          <ul>{uncheckedScope.map((item) => <li key={item}><ChevronRight size={15} />{item}</li>)}</ul>
        </div>
      </div>
      {truncated && (
        <p className="scan-scope-card__warning" role="status">
          안전 제한 때문에 일부 셀만 검사했습니다. 이 결과는 전체 파일 검사가 아닙니다.
        </p>
      )}
    </section>
  );
}

export function M25ResultsPanel(props: ResultsPanelProps) {
  return <ResultsContent key={`${props.result.analysis_id}:${props.result.scanned_at}`} {...props} />;
}

function ResultsContent({
  guided = false, sourceFile, reviewReady = false, onContinueReview,
  result,
  reviewSelection,
  formulaAudit,
  isDemo,
  statuses = {},
  revalidationComparison = null,
  onStatusChange = () => undefined,
  feedbackRepository = null,
  onPrepareRevalidation = () => undefined,
  onReset,
}: ResultsPanelProps) {
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');
  const [viewMode, setViewMode] = useState<'groups' | 'table'>('groups');
  const structureCounts = findingCounts(result);
  const auditState = formulaAudit ? integratedAuditState(formulaAudit) : null;
  const candidates = auditState?.complete ? formulaAudit!.result!.candidates : [];
  // Presentation keys are namespaced; original API keys/statuses remain untouched.
  const entries = [
    ...result.findings.map((finding) => ({ finding, source: 'structure' as const, key: `structure:${findingIdentity(finding)}` })),
    ...candidates.map((finding) => ({ finding, source: 'formula' as const, key: `formula:${findingIdentity(finding)}` })),
  ];
  const entriesByKey = new Map(entries.map((entry) => [entry.key, entry]));
  const allFindings = formulaAudit ? entries.map(({ finding, key }) => ({ ...finding, finding_key: key })) : result.findings;
  const formulaEntry = (finding: Finding) => entriesByKey.get(findingIdentity(finding))?.source === 'formula';
  const viewStatuses = formulaAudit ? Object.fromEntries(entries.map(({ finding, source, key }) => [key,
    (source === 'formula' ? formulaAudit.statuses : statuses)[findingIdentity(finding)] ?? 'UNREVIEWED',
  ])) : statuses;
  const updateStatus = (finding: Finding, status: FindingUserStatus) => {
    const entry = formulaAudit ? entriesByKey.get(findingIdentity(finding)) : undefined;
    if (entry?.source === 'formula') formulaAudit!.onStatusChange(findingIdentity(entry.finding), status);
    else onStatusChange(findingIdentity(entry?.finding ?? finding), status);
  };
  const counts = { ...structureCounts,
    total_detected: structureCounts.total_detected + candidates.length,
    returned_details: structureCounts.returned_details + candidates.length,
  };
  const [sourceFilter, setSourceFilter] = useState<'all' | 'structure' | 'formula'>('all');
  const repairProduct = displayedProducts(result.products).find((product) => product.product_id === 'APPROVED_REPAIR')!;
  const [sheetFilter, setSheetFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState<FindingUserStatus | 'all'>('all');
  const findingsHeadingRef = useRef<HTMLDivElement>(null);
  const statusFilterRef = useRef<HTMLSelectElement>(null);
  const filtersActive = sourceFilter !== 'all' || severityFilter !== 'all' || sheetFilter !== 'all' || statusFilter !== 'all';
  const sheetOptions = [...new Map(allFindings.map((finding) => [
    findingSheetOption(finding), finding.sheet || '통합문서 수준 (시트 지정 없음)',
  ])).entries()];
  const hasPriorityFindings = allFindings.some((finding) => finding.severity !== 'info');
  const visibleFindings = allFindings.filter((finding) => (
    (severityFilter === 'all' || (severityFilter === 'priority'
      ? finding.severity !== 'info'
      : finding.severity === severityFilter))
    && (sheetFilter === 'all' || findingSheetOption(finding) === sheetFilter)
    && (sourceFilter === 'all' || (formulaEntry(finding) ? 'formula' : 'structure') === sourceFilter)
    && (statusFilter === 'all' || (viewStatuses[findingIdentity(finding)] ?? 'UNREVIEWED') === statusFilter)
  ));
  const resetFilters = () => {
    setSourceFilter('all');
    setSeverityFilter('all');
    setSheetFilter('all');
    setStatusFilter('all');
  };
  const showPriorityFindings = () => {
    setSourceFilter('all');
    setSeverityFilter('priority');
    setSheetFilter('all');
    setStatusFilter('all');
    findingsHeadingRef.current?.focus({ preventScroll: true });
    findingsHeadingRef.current?.scrollIntoView({ block: 'start' });
  };
  const { summary, workbook, quote } = result;
  const riskLabel = summary.risk_band === 'low'
    ? '낮음'
    : summary.risk_band === 'moderate'
      ? '보통'
      : summary.risk_band === 'critical'
        ? '높음 · 우선 확인 필요'
        : '높음';
  const resultHeadline = formulaAudit
    ? counts.total_detected > 0 ? `확인할 항목 ${counts.total_detected}건`
      : formulaAudit.busy ? '수식 패턴을 확인하고 있습니다'
        : !auditState?.complete || !counts.scan_complete ? '완료한 검사 범위에서 발견 0건'
          : '검사 범위에서 발견된 항목이 없습니다'
    : summary.issue_count === 0
    ? workbook.scan_truncated
      ? '무료 구조 검사: 일부 범위에서 발견 0건'
      : workbook.scanned_cell_count === 0
        ? '무료 구조 검사: 읽은 셀 0개'
        : '무료 구조 검사: 발견 0건'
    : summary.critical_count > 0
      ? '중요한 구조적 문제가 발견됐습니다.'
      : summary.warning_count > 0
        ? '정적 검사에서 확인할 항목이 발견됐습니다.'
        : '정적 검사에서 참고할 구조 신호가 발견됐습니다.';
  const findingTypes = summarizeFindingTypes(allFindings);
  const recommendedChecks = uniqueRecommendedChecks(allFindings);
  const nextActions = uniqueNextActions(allFindings).slice(0, 3);
  const informationOnlyCount = summary.information_only_count ?? result.findings.filter(
    (finding) => finding.repair_class === 'INFORMATION_ONLY',
  ).length;
  const repairReviewCandidateCount = summary.repair_review_candidate_count ?? (
    summary.safe_candidate_count
    + summary.confirmation_required_count
    + summary.expert_review_count
  );
  const userStatusCounts = userStatusOptions.reduce<Record<FindingUserStatus, number>>((counts, status) => {
    counts[status] = allFindings.filter((finding) => (
      (viewStatuses[findingIdentity(finding)] ?? 'UNREVIEWED') === status
    )).length;
    return counts;
  }, {
    UNREVIEWED: 0,
    REVIEWED: 0,
    PLANNED_REPAIR: 0,
    IGNORED: 0,
    MARKED_NORMAL: 0,
  });
  const resolutionFlow = [
    {
      title: '무료 진단',
      status: '현재 제공',
      description: '파일 구조와 수식 문자열의 위험 신호를 확인합니다.',
    },
    {
      title: '정밀 검증',
      status: '준비 중',
      description: '수식 일관성, 업무 의도, 변경 방법을 추가로 확인합니다.',
    },
    {
      title: '승인 기반 수정',
      status: '향후 제공',
      description: '미리보기와 사용자 승인 뒤 원본과 분리된 수정본을 생성합니다.',
    },
    {
      title: '재검증',
      status: '현재는 직접 재검사',
      description: '직접 수정한 파일을 같은 정적 규칙으로 다시 비교할 수 있습니다.',
    },
    {
      title: '업무 자동화',
      status: '필요 시 준비 중',
      description: '반복 업무가 확인되면 별도 자동화 범위를 검토합니다.',
    },
  ];
  const repairability = [
    ['안전 수정 후보', summary.safe_candidate_count, '규칙이 명확하고 원본 구조를 훼손할 가능성이 낮은 항목입니다. 실제 수정은 제공하지 않습니다.'],
    ['사용자 확인 필요', summary.confirmation_required_count, '업무 의미에 따라 방법이 달라질 수 있는 항목입니다.'],
    ['전문가 검토 필요', summary.expert_review_count, '수정 시 계산 결과나 파일 구조에 영향을 줄 수 있는 항목입니다.'],
    ['정보 제공 · 즉시 수정 불필요', informationOnlyCount, '즉시 수정하지 않아도 되는 구조·성능 참고 항목입니다.'],
  ] as const;

  if (formulaAudit || guided) return (
    <section className="results-section diagnosis-progressive" id="results" aria-labelledby="results-title">
      <div className="shell">
        <div className="results-header"><div>
          <span className="section-kicker">{formulaAudit?.busy ? '검사 진행 중' : (formulaAudit ? auditState?.complete : true) && counts.scan_complete ? '검사 완료' : '일부 검사 완료'}</span>
          <h2 id="results-title">{resultHeadline}</h2>
          <p className="diagnosis-breakdown">구조 위험 {structureCounts.total_detected}건 · 수식 검토 후보 {formulaAudit ? auditState?.complete ? `${candidates.length}건` : '확인 미완료' : '미실행'}</p>
        </div><button className="button button--ghost" type="button" onClick={onReset}><RotateCcw size={17}/>다른 파일 검사</button></div>
        <p className="diagnosis-main-summary">{findingTypes.length}개 문제 유형 · {counts.total_detected}개 확인 위치 · 우선 확인 {allFindings.filter(f => f.severity !== 'info').length}개 반환 상세</p>
        {formulaAudit ? <UnifiedDiagnosisStatus audit={formulaAudit} truncated={workbook.scan_truncated} compact><GeneralFindingGuidance findings={allFindings} limitations={result.limitations}/></UnifiedDiagnosisStatus>
          : <details className="diagnosis-status__scope"><summary>검사 범위와 한계</summary><p>구조 위험만 검사했습니다. 수식 계산과 업무상 정답은 검증하지 않았습니다.</p><GeneralFindingGuidance findings={allFindings} limitations={result.limitations}/></details>}
        {counts.total_detected===0 && !formulaAudit?.busy && <aside className="zero-findings-note" role="note" aria-label="발견 0건 해석">
          <strong>계산 결과와 업무적 정확성을 보장하지 않습니다.</strong>
          <p>{auditState?.complete && counts.scan_complete ? '완료한 검사 범위에서 확인할 항목을 찾지 못했습니다.' : '완료하지 못한 검사나 읽지 못한 범위가 남아 있습니다. 검사 진행과 범위를 확인하세요.'}</p>
        </aside>}
        <details className="diagnosis-summary-details"><summary>규칙 기반 우선순위 점수 {summary.risk_score} / 100</summary>
          <p>구조 위험의 우선순위 점수입니다. 수식 검토 후보는 포함하지 않으며 계산·업무 정확도를 뜻하지 않습니다.</p>
          <p>{result.filename} · {formatFileSize(result.file_size_bytes)} · 시트 {workbook.sheet_count}개 · 내용이 있는 셀 {workbook.scanned_cell_count}개 · 수식 문자열 {workbook.formula_count}개</p>
        </details>
        <div className="findings-panel" ref={findingsHeadingRef} tabIndex={-1}>
          <div className="panel-heading"><h3 id="all-findings-title">문제 유형별 확인</h3><span>{new Set(allFindings.map(f=>f.rule_code)).size}개 유형</span></div>
          <p className="diagnosis-reading-guide">유형을 펼쳐 공통 설명을 읽고, 필요한 위치를 선택해 해당 셀의 근거를 확인하세요.</p>
          <p className="finding-coverage">전체 발견 {counts.total_detected}건 · 반환 상세 {counts.returned_details}건 · 상세 생략 {counts.omitted_details}건 · 필터 표시 {visibleFindings.length}건</p>
          <fieldset className="finding-view-switch"><legend>결과 보기 방식</legend>
              <label><input type="radio" name="finding-view" checked={viewMode==='groups'} onChange={()=>setViewMode('groups')}/>유형별 보기</label>
              <label><input type="radio" name="finding-view" checked={viewMode==='table'} onChange={()=>setViewMode('table')}/>전체 항목 표</label>
            </fieldset>
          <details className="diagnosis-filters"><summary>필터 및 전체 항목 표{filtersActive ? ' · 필터 적용 중' : ''}</summary>
            <fieldset className="finding-filters"><legend>찾아볼 항목 선택</legend><div className="finding-filters__controls">
              <label><span>검사 종류</span><select aria-label="검사 종류" value={sourceFilter} onChange={event=>setSourceFilter(event.target.value as typeof sourceFilter)}>
                <option value="all">모든 검사 항목</option><option value="structure">구조 위험</option><option value="formula">수식 검토 후보</option></select></label>
              <label><span>중요도</span><select aria-label="중요도" value={severityFilter} onChange={event=>setSeverityFilter(event.target.value as SeverityFilter)}>
                <option value="all">모든 중요도</option><option value="priority">중요·주의 우선 확인</option>
                {(['critical','warning','info'] as const).map(s=><option key={s} value={s}>{severityLabel[s]}</option>)}</select></label>
              <label><span>시트</span><select aria-label="시트" value={sheetFilter} onChange={event=>setSheetFilter(event.target.value)}>
                <option value="all">모든 위치</option>{sheetOptions.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
              <label><span>처리 상태로 보기</span><select aria-label="처리 상태로 보기" ref={statusFilterRef} value={statusFilter} onChange={event=>setStatusFilter(event.target.value as FindingUserStatus|'all')}>
                <option value="all">모든 처리 상태</option>{userStatusOptions.map(s=><option key={s} value={s}>{reviewNoteLabel[s]}</option>)}</select></label>
            </div><div className="finding-filters__footer"><p>필터는 표시만 바꿉니다. 읽어봄은 개인 메모입니다.</p>
              <button className="button button--outline button--small" type="button" disabled={!filtersActive} onClick={resetFilters}>필터 초기화</button></div></fieldset>
          </details>
          {visibleFindings.length>0 ? <ProgressiveFindingViews sourceFile={sourceFile} findings={visibleFindings} allFindings={allFindings} mode={viewMode} statuses={viewStatuses} reviewSelection={reviewSelection}
            categoryLabel={finding=>formulaEntry(finding)?'수식 검토 후보':'구조 위험'}
            onStatusChange={(finding,status)=>{updateStatus(finding,status);if(statusFilter!=='all'&&statusFilter!==status)statusFilterRef.current?.focus();}}
            onReviewGroup={findings=>{if(statusFilter!=='all'&&statusFilter!=='REVIEWED')statusFilterRef.current?.focus();for(const f of findings)updateStatus(f,'REVIEWED');}}/>
            : allFindings.length>0 ? <p className="empty-result-note">선택한 조건에 맞는 항목이 없습니다. 필터를 초기화하면 전체 발견 항목을 볼 수 있습니다. 이 표시는 파일에 문제가 없다는 뜻이 아닙니다.</p>
            : counts.total_detected>0 ? <p className="empty-result-note">발견된 항목의 반환 상세가 없습니다. 상세 생략 수와 검사 한계를 확인하세요.</p>
            : <p className="empty-result-note">완료한 검사에서 반환된 항목이 없습니다. 위의 검사 진행과 범위를 확인하세요.</p>}
        </div>
        {reviewSelection && <section className="diagnosis-continue" aria-label="다음 단계로 이동"><div><h3>이 중 고칠 항목을 확인할까요?</h3><p>2단계에 포함한 항목 {reviewSelection.findings.length}개 · 선택만으로 변경하거나 승인하지 않습니다.</p><small>유형 전체 또는 필요한 셀만 포함할 수 있습니다. ‘읽어봄’은 선택과 관계없는 개인 메모입니다.</small></div><button className="button button--primary" type="button" disabled={!reviewReady || !reviewSelection.findings.length} onClick={onContinueReview}>선택한 {reviewSelection.findings.length}개로 수정 범위 확인</button>{reviewReady && <button className="button button--ghost" type="button" onClick={onContinueReview}>대상 셀 직접 지정</button>}</section>}
        <div className="diagnosis-result-tools">
          <div className="diagnosis-csv"><button className="button button--outline" type="button" onClick={()=>downloadDiagnosisCsv(result,statuses)}><Download size={17}/>진단 결과 CSV 다운로드</button>
            <p>CSV 범위: 구조 검사 결과만 포함 · 수식 검토 후보 제외. 필터 적용 전 반환 상세와 개인 처리 상태를 내보냅니다.</p></div>
          <details className="diagnosis-handling"><summary>내 검토 메모 요약</summary><p>개인 메모는 변경 승인에 사용하지 않습니다. 이 화면을 열어 둔 동안만 유지됩니다.</p>
            <div className="user-status-summary">{userStatusOptions.map(s=><span key={s}><strong>{userStatusCounts[s]}</strong>{reviewNoteLabel[s]}</span>)}</div></details>
          <details className="diagnosis-revalidation" open={revalidationComparison ? true : undefined}><summary>직접 수정한 파일 다시 검사</summary>
            <p>직접 재검사 비교는 구조 검사 결과 기준입니다. 수식 후보는 매번 새로 검사합니다.</p>
            <RevalidationPanel comparison={revalidationComparison} onPrepareRevalidation={onPrepareRevalidation}/></details>

        </div>
      </div>
    </section>
  );

  return (
    <section className="results-section" id="results" aria-labelledby="results-title">
      <div className="shell">
        <div className="section-kicker"><CheckCircle2 size={17} />{isDemo ? '샘플 진단 완료' : '정적 진단 완료'}</div>
        <ScanScopeCard truncated={workbook.scan_truncated} />
        <div className="results-header">
          <div>
            <h2 id="results-title">{resultHeadline}</h2>
            <p>파일에서 읽은 범위: 시트 {workbook.sheet_count.toLocaleString('ko-KR')}개 · 내용이 있는 셀 {workbook.scanned_cell_count.toLocaleString('ko-KR')}개 · 수식 문자열 {workbook.formula_count.toLocaleString('ko-KR')}개</p>
            <p><strong>{result.filename}</strong> · {formatFileSize(result.file_size_bytes)} · 규칙 세트 {result.rule_set_version}</p>
          </div>
          <button className="button button--ghost" type="button" onClick={onReset}><RotateCcw size={17} />다른 파일 검사</button>
        </div>

        {summary.issue_count === 0 && (
          <aside className="zero-findings-note" role="note" aria-label="발견 0건 해석">
            <strong>수식 검증을 통과했다는 뜻은 아닙니다.</strong>
            <p>발견 0건은 이번 무료 구조 검사 규칙에서 항목을 찾지 못했다는 뜻입니다. 수식 패턴 이탈·누락 시험 파일의 오류는 별도 수식 검사 대상이며, 이 무료 결과에 포함되지 않습니다.</p>
            <p>수식 패턴·누락, Excel 재계산, 업무적 정확성은 이 검사에서 확인하지 않았습니다.{workbook.scan_truncated ? ' 안전 제한으로 읽지 못한 범위도 남아 있습니다.' : workbook.scanned_cell_count === 0 ? ' 파일에 읽을 수 있는 셀 내용이 있는지도 확인하세요.' : ''}</p>
          </aside>
        )}
        <div className="result-grid result-grid--summary">
          <article className="risk-card">
            <div className={`risk-ring risk-ring--${summary.risk_band}`} aria-label={`구조 위험 상태 ${riskLabel}`}>
              <span>{riskLabel}</span><small>규칙 기준</small>
            </div>
            <div>
              <span className="card-label">탐지된 구조 위험 점수</span>
              <h3>규칙 기반 우선순위 점수 {summary.risk_score} / 100</h3>
              <p>이 점수는 발견된 구조 위험 신호의 우선순위를 요약한 값입니다. 파일 전체 계산의 정확도, 업무적 정확성, 금전 손실 가능성을 뜻하지 않습니다.</p>
            </div>
          </article>
          <article className="metric-card">
            <span className="card-label">발견 항목</span><strong>{summary.issue_count}</strong>
            <div className="metric-breakdown">
              <span className="metric-dot metric-dot--critical" /> 중요 {summary.critical_count}
              <span className="metric-dot metric-dot--warning" /> 주의 {summary.warning_count}
              <span className="metric-dot metric-dot--info" /> 참고 {summary.info_count}
            </div>
          </article>
          <article className="metric-card">
            <span className="card-label">해결 경로 검토 대상</span><strong>{repairReviewCandidateCount}</strong>
            <p>수정 후보·사용자 확인·전문가 검토 분류를 합친 수치이며, 현재 수정 가능을 뜻하지 않습니다.</p>
          </article>
          <article className="metric-card">
            <span className="card-label">검사 상태</span>
            <strong className="metric-card__word">{workbook.scan_truncated ? '일부 검사' : '범위 내 완료'}</strong>
            <p>{workbook.scan_truncated ? '안전 제한으로 일부 셀만 검사했습니다.' : '정의된 무료 검사 범위를 완료했습니다.'}</p>
          </article>
        </div>

        <div className="workbook-strip" aria-label="워크북 구조 요약">
          <span>시트 <strong>{workbook.sheet_count}</strong></span>
          <span>수식 <strong>{workbook.formula_count.toLocaleString('ko-KR')}</strong></span>
          <span>외부 참조 <strong>{workbook.external_link_count}</strong></span>
          <span>숨김 시트 <strong>{workbook.hidden_sheet_count + workbook.very_hidden_sheet_count}</strong></span>
          <span>병합 영역 <strong>{workbook.merged_range_count}</strong></span>
          {workbook.has_macros && <span className="workbook-strip__warning">매크로 포함</span>}
        </div>

        <section className="next-actions-panel" aria-labelledby="next-actions-title">
          <div>
            <span className="card-label">권장 다음 행동</span>
            <h3 id="next-actions-title">무엇부터 확인할까요?</h3>
            <p>무료 결과는 발견 위치와 직접 확인 방법을 제공합니다. 직접 조치한 뒤 같은 규칙으로 다시 검사할 수 있습니다.</p>
          </div>
          {nextActions.length > 0 ? (
            <ol>{nextActions.map((action) => <li key={action}><ListChecks size={17} />{action}</li>)}</ol>
          ) : <p>현재 발견 항목이 없어 특정한 다음 행동을 제안하지 않습니다.</p>}
          <div className="next-actions-panel__buttons">
            <button
              className="button button--outline button--small"
              type="button"
              onClick={showPriorityFindings}
              disabled={!hasPriorityFindings}
            >
              우선 문제 확인하기
            </button>
            <button className="button button--primary button--small" type="button" onClick={onPrepareRevalidation}>수정 후 다시 검사</button>
            <a className="button button--outline button--small" href="#approved-repair">수정 패키지 안내 · 준비 중</a>
            <button className="button button--outline button--small" type="button" onClick={() => downloadDiagnosisCsv(result, statuses)}><Download size={16} />{diagnosisCsvArtifact.label} 다운로드</button>
          </div>
        </section>

        <div className="result-columns">
          <div className="findings-panel">
            <div className="panel-heading" id="priority-findings" ref={findingsHeadingRef} tabIndex={-1}>
              <div><span className="card-label">근거가 있는 무료 결과</span><h3 id="all-findings-title">전체 Finding 목록</h3></div>
              <span role="status" aria-live="polite" aria-atomic="true">
                {filtersActive
                  ? `총 ${result.findings.length}개 중 ${visibleFindings.length}개 표시`
                  : counts.omitted_details > 0 ? `반환 상세 ${result.findings.length}개 표시 · 전체 발견 ${counts.total_detected}건`
                    : viewMode === 'groups'
                      ? `${new Set(visibleFindings.map((finding) => finding.rule_code)).size}개 유형으로 묶음 · 위치 ${visibleFindings.length}건`
                      : `${result.findings.length}개 전체 표시 · 클릭해 자세히 보기`}
              </span>
            </div>
            <p className="finding-coverage" id="finding-coverage">전체 발견 {counts.total_detected}건 · 반환 상세 {counts.returned_details}건 · 상세 생략 {counts.omitted_details}건 · 필터 표시 {visibleFindings.length}건</p>
            {counts.omitted_details > 0 && <p className="empty-result-note">안전 제한으로 일부 발견 항목의 상세가 생략됐습니다. 위험 점수는 전체 발견 기준이며 목록과 CSV에는 반환 상세만 포함됩니다.</p>}
            {!counts.scan_complete && <p className="empty-result-note">전체 발견 수는 검사한 범위 안의 수입니다. 검사하지 않은 셀의 위험 신호는 포함하지 않습니다.</p>}
            <fieldset className="finding-view-switch">
              <legend>결과 보기 방식</legend>
              <label><input type="radio" name="finding-view" value="groups" checked={viewMode === 'groups'} onChange={() => setViewMode('groups')} />유형별 보기</label>
              <label><input type="radio" name="finding-view" value="table" checked={viewMode === 'table'} onChange={() => setViewMode('table')} />전체 항목 표</label>
            </fieldset>
            {result.findings.length > 0 && (
              <fieldset className="finding-filters" aria-describedby="finding-filter-note">
                <legend>찾아볼 항목 선택</legend>
                <div className="finding-filters__controls">
                  <label>
                    <span>중요도</span>
                    <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value as SeverityFilter)}>
                      <option value="all">모든 중요도</option>
                      <option value="priority">중요·주의 우선 확인</option>
                      {(['critical', 'warning', 'info'] as const).map((severity) => (
                        <option key={severity} value={severity}>{severityLabel[severity]}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>시트</span>
                    <select value={sheetFilter} onChange={(event) => setSheetFilter(event.target.value)}>
                      <option value="all">모든 위치</option>
                      {sheetOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                    </select>
                  </label>
                  <label>
                    <span>처리 상태로 보기</span>
                    <select ref={statusFilterRef} value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as FindingUserStatus | 'all')}>
                      <option value="all">모든 처리 상태</option>
                      {userStatusOptions.map((status) => <option key={status} value={status}>{userStatusLabel[status]}</option>)}
                    </select>
                  </label>
                </div>
                <div className="finding-filters__footer">
                  <p id="finding-filter-note">필터는 목록에만 적용됩니다. 진단 요약은 전체 발견, CSV는 필터 적용 전 반환 상세를 기준으로 합니다. 유형별 확인은 표시된 항목의 개인 처리 상태만 바꿉니다.</p>
                  <button className="button button--outline button--small" type="button" onClick={resetFilters} disabled={!filtersActive}>필터 초기화</button>
                </div>
              </fieldset>
            )}
            {visibleFindings.length > 0 ? (
              <FindingViews findings={visibleFindings} allFindings={result.findings} mode={viewMode} statuses={statuses}
                renderGuidance={(finding) => finding.guidance ? <FindingExplanation finding={finding} /> : <p>아래 개별 위치의 근거를 확인하세요.</p>}
                onReviewGroup={(findings) => {
                  if (statusFilter !== 'all' && statusFilter !== 'REVIEWED') statusFilterRef.current?.focus();
                  for (const finding of findings) onStatusChange(findingIdentity(finding), 'REVIEWED');
                }}
                renderFinding={(finding, sharedGuidance) => (
                  <div key={findingIdentity(finding)}><FindingCard finding={finding} sharedGuidance={sharedGuidance}
                    status={statuses[findingIdentity(finding)] ?? 'UNREVIEWED'}
                    onStatusChange={(status) => {
                      onStatusChange(findingIdentity(finding), status);
                      if (statusFilter !== 'all' && statusFilter !== status) statusFilterRef.current?.focus();
                    }}
                    feedbackRepository={feedbackRepository} scannerVersion={result.scanner_version}
                  />{reviewSelection && <ReviewChoice finding={finding} selection={reviewSelection}/>}</div>
                )}
              />
            ) : result.findings.length > 0 ? (
              <p className="empty-result-note">선택한 조건에 맞는 항목이 없습니다. 필터를 초기화하면 전체 발견 항목을 볼 수 있습니다. 이 표시는 파일에 문제가 없다는 뜻이 아닙니다.</p>
            ) : counts.total_detected > 0 ? (
              <p className="empty-result-note">발견된 항목의 반환 상세가 없습니다. 상세 생략 수와 검사 한계를 확인하세요. 문제가 없다는 뜻이 아닙니다.</p>
            ) : (
              <p className="empty-result-note">반환된 무료 구조 검사 항목이 없습니다. 위의 검사 범위와 미수행 항목을 확인하세요. 수식 패턴·누락이나 계산 정확성의 검증 결과가 아닙니다.</p>
            )}

            <div className="finding-types" aria-label="문제 유형별 개수">
              <h4>문제 유형별 개수</h4><p>반환 상세 기준 · 생략된 항목의 유형은 포함하지 않습니다.</p>
              {findingTypes.length > 0 ? (
                <ul>{findingTypes.map((findingType) => (
                  <li key={findingType.ruleCode}>
                    <span className={`severity severity--${findingType.severity}`}>{severityLabel[findingType.severity]}</span>
                    <span>{findingType.title}</span><strong>{findingType.count}건</strong>
                  </li>
                ))}</ul>
              ) : <p>이번 검사에서 발견된 문제 유형이 없습니다.</p>}
            </div>

            <p className="evidence-grade-note">
              탐지 확실도는 해당 패턴이 파일에 존재한다는 근거의 강도입니다. 수식, 계산 결과, 업무 논리가 정확하다는 의미는 아닙니다.
            </p>

            <section className="user-status-panel" aria-labelledby="user-status-title">
              <div className="panel-heading">
                <div><span className="card-label">이 브라우저 화면 안의 개인 메모</span><h3 id="user-status-title">사용자 처리 상태</h3></div>
                <span>시스템 판정이나 스캔 결과를 바꾸지 않습니다. 확인함·정상으로 판단은 변경 승인이 아닙니다.</span>
              </div>
              <div className="user-status-summary">
                {userStatusOptions.map((status) => <span key={status}><strong>{userStatusCounts[status]}</strong>{userStatusLabel[status]}</span>)}
              </div>
              <p>상태는 이 화면을 열어 둔 동안만 관리됩니다. 파일 내용이나 셀 값은 저장하지 않습니다.</p>
            </section>

            <RevalidationPanel comparison={revalidationComparison} onPrepareRevalidation={onPrepareRevalidation} />

            <section className="download-panel" aria-labelledby="download-title">
              <div>
                <span className="card-label">현재 결과를 내보내기</span>
                <h3 id="download-title">{diagnosisCsvArtifact.label} 다운로드</h3>
                <p>UTF-8 BOM CSV로 필터 적용 전 반환 상세의 위치, 근거, 가이드, 처리 상태를 다운로드합니다. 상세 생략 항목과 수정본은 포함하지 않습니다. 수식으로 해석될 수 있는 텍스트는 안전하게 내보냅니다.</p>
              </div>
              <button className="button button--outline" type="button" onClick={() => downloadDiagnosisCsv(result, statuses)}><Download size={17} />{diagnosisCsvArtifact.label} 다운로드</button>
            </section>

            {feedbackRepository && (
              <ResultFeedbackPanel
                repository={feedbackRepository}
                scannerVersion={result.scanner_version}
              />
            )}

            <section className="repairability-section" aria-labelledby="repairability-title">
              <div className="panel-heading">
                <div><span className="card-label">현재 발견 결과 기준</span><h3 id="repairability-title">이 파일의 수정 가능성</h3></div>
                <span>수정 기능은 아직 제공하지 않습니다.</span>
              </div>
              <div className="repairability-grid">
                {repairability.map(([label, count, description]) => (
                  <article key={label} className="repairability-card"><strong>{count}</strong><h4>{label}</h4><p>{description}</p></article>
                ))}
              </div>
            </section>

            <section className="resolution-flow" aria-labelledby="resolution-flow-title">
              <div className="panel-heading">
                <div>
                  <span className="card-label">진단 결과를 해결로 연결하는 단계</span>
                  <h3 id="resolution-flow-title">향후 정밀검증 및 Approved Repair</h3>
                </div>
                <span>현재는 무료 진단과 직접 재검사만 제공합니다.</span>
              </div>
              <p className="resolution-flow__summary">
                {repairReviewCandidateCount > 0
                  ? `현재 발견된 ${repairReviewCandidateCount}건은 향후 정밀 검증 또는 사용자 승인 전 검토가 필요할 수 있습니다.`
                  : '현재 발견 결과 기준으로는 수정 검토 대상을 제안하지 않습니다.'}
                {' '}정밀 검증과 승인 기반 수정은 아직 제공하지 않습니다.
              </p>
              <ol className="resolution-flow__steps">
                {resolutionFlow.map((step, index) => (
                  <li key={step.title} className={index === 0 ? 'is-current' : ''}>
                    <span>{index + 1}</span>
                    <div><strong>{step.title}</strong><em>{step.status}</em><p>{step.description}</p></div>
                  </li>
                ))}
              </ol>
            </section>

            <section className="recommendation-plan" aria-labelledby="recommendation-title">
              <span className="card-label">현재 파일의 실제 발견 결과 기준</span>
              <h3 id="recommendation-title">이 파일의 권장 정밀검증 항목</h3>
              {recommendedChecks.length > 0 ? (
                <ul>{recommendedChecks.map((item) => <li key={item}><Check size={16} />{item}</li>)}</ul>
              ) : <p>현재 발견 항목이 없어 특정 정밀검증 항목을 제안하지 않습니다.</p>}
            </section>
          </div>

          <aside className="quote-panel" aria-label="정밀검증 예상 범위와 베타 가격 가설">
            <div className="quote-panel__eyebrow"><Sparkles size={17} />정밀 검증 · 준비 중</div>
            <h3>{quote.headline}</h3>
            <div className="quote-price">
              <strong>{formatPriceRange(quote.amount_min, quote.amount_max, quote.amount)}</strong>
              <span>{quote.tier} · 베타 예상 가격 범위</span>
            </div>
            {quote.pricing_note && <p className="pricing-note">{quote.pricing_note}</p>}
            <div className="quote-factors">{quote.factors.map((factor) => <span key={factor}>{factor}</span>)}</div>
            <div className="planned-deliverables">
              <h4>승인 기반 수정 패키지의 향후 필수 파일 · 준비 중</h4>
              <ul>{repairProduct.deliverables.map((item) => <li key={item.kind}><FileClock size={16} />{item.label}</li>)}</ul>
              <p>정밀검증은 패키지에 포함할 검증 활동입니다. 위 참고 금액은 구매권이나 변경 승인이 아닙니다.</p>
            </div>
            <div className="scope-list">
              <h4>예상 범위에 포함</h4>
              {quote.included.map((item) => <p key={item}><Check size={16} />{item}</p>)}
            </div>
            <div className="scope-list scope-list--excluded">
              <h4>예상 범위에서 제외</h4>
              {quote.excluded.map((item) => <p key={item}><ChevronRight size={16} />{item}</p>)}
            </div>
            <button className="button button--primary button--wide" type="button" disabled>
              정밀 검증·수정 기능 준비 중<FileClock size={18} />
            </button>
            <p className="prototype-note">이 참고 견적은 구매권이나 변경 승인이 아닙니다. 일반 신청·결제·전문가 견적 요청은 준비 중입니다.</p>
          </aside>
        </div>

        <div className="limitations-card">
          <ShieldAlert size={22} aria-hidden="true" />
          <div><h3>정적 검사 결과를 해석할 때 알아둘 점</h3><ul>{result.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div>
        </div>
      </div>
    </section>
  );
}
