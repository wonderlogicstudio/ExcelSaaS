import {
  AlertOctagon,
  AlertTriangle,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  FileClock,
  Info,
  RotateCcw,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import type { Finding, RepairClass, ScanResult, Severity } from '../types';
import { formatCurrency, formatFileSize, formatPercent } from '../lib/format';

interface ResultsPanelProps {
  result: ScanResult;
  isDemo: boolean;
  onReset: () => void;
}

const severityLabel: Record<Severity, string> = {
  critical: '중요',
  warning: '주의',
  info: '참고',
};

const repairLabel: Record<RepairClass, string> = {
  SAFE_CANDIDATE: '자동 수정 후보',
  CONFIRMATION_REQUIRED: '사용자 확인 필요',
  EXPERT_REVIEW: '전문가 검토',
  INFORMATION_ONLY: '정보 제공',
};

function SeverityIcon({ severity }: { severity: Severity }) {
  if (severity === 'critical') return <AlertOctagon size={18} />;
  if (severity === 'warning') return <AlertTriangle size={18} />;
  return <Info size={18} />;
}

function FindingCard({ finding }: { finding: Finding }) {
  return (
    <article className={`finding finding--${finding.severity}`}>
      <div className="finding__icon" aria-hidden="true">
        <SeverityIcon severity={finding.severity} />
      </div>
      <div className="finding__body">
        <div className="finding__heading">
          <span className={`severity severity--${finding.severity}`}>
            {severityLabel[finding.severity]}
          </span>
          <code>{finding.rule_code}</code>
          {(finding.sheet || finding.cell) && (
            <span className="finding__location">
              {[finding.sheet, finding.cell].filter(Boolean).join(' · ')}
            </span>
          )}
        </div>
        <h4>{finding.title}</h4>
        <p>{finding.description}</p>
        <div className="finding__meta">
          <span>{repairLabel[finding.repair_class]}</span>
          <span>신뢰도 {formatPercent(finding.confidence)}</span>
        </div>
      </div>
    </article>
  );
}

export function ResultsPanel({ result, isDemo, onReset }: ResultsPanelProps) {
  const { summary, workbook, quote } = result;
  const riskLabel = {
    low: '낮음',
    moderate: '보통',
    high: '높음',
    critical: '매우 높음',
  }[summary.risk_band];
  const resultHeadline =
    summary.issue_count === 0
      ? '정적 검사 기준에서는 구조적 위험을 찾지 못했습니다.'
      : summary.critical_count > 0
        ? '중요한 구조적 문제가 발견됐습니다.'
        : summary.warning_count > 0
          ? '정적 검사에서 확인할 항목이 발견됐습니다.'
          : '정적 검사에서 참고할 개선 항목이 발견됐습니다.';

  return (
    <section className="results-section" id="results" aria-labelledby="results-title">
      <div className="shell">
        <div className="section-kicker">
          <CheckCircle2 size={17} />
          {isDemo ? '샘플 진단 완료' : '정적 진단 완료'}
        </div>
        <div className="results-header">
          <div>
            <h2 id="results-title">{resultHeadline}</h2>
            <p>
              <strong>{result.filename}</strong> · {formatFileSize(result.file_size_bytes)} · 규칙 세트{' '}
              {result.rule_set_version}
            </p>
          </div>
          <button className="button button--ghost" type="button" onClick={onReset}>
            <RotateCcw size={17} />
            다른 파일 검사
          </button>
        </div>

        <div className="result-grid result-grid--summary">
          <article className="risk-card">
            <div
              className={`risk-ring risk-ring--${summary.risk_band}`}
              aria-label={`위험 점수 ${summary.risk_score}점, ${riskLabel}`}
            >
              <span>{summary.risk_score}</span>
              <small>/ 100</small>
            </div>
            <div>
              <span className="card-label">정적 검사 위험도</span>
              <h3>{riskLabel}</h3>
              <p>정적 검사에서 발견한 구조적 위험의 우선순위 점수입니다. 실제 계산 결과나 업무 판단의 정확도를 보장하지 않습니다.</p>
            </div>
          </article>

          <article className="metric-card">
            <span className="card-label">발견 항목</span>
            <strong>{summary.issue_count}</strong>
            <div className="metric-breakdown">
              <span className="metric-dot metric-dot--critical" /> 중요 {summary.critical_count}
              <span className="metric-dot metric-dot--warning" /> 주의 {summary.warning_count}
              <span className="metric-dot metric-dot--info" /> 참고 {summary.info_count}
            </div>
          </article>

          <article className="metric-card">
            <span className="card-label">자동 수정 후보</span>
            <strong>{summary.safe_candidate_count}</strong>
            <p>규칙상 자동 수정 후보 · 사용자 확인 필요 {summary.confirmation_required_count}건</p>
          </article>

          <article className="metric-card">
            <span className="card-label">검토 난이도</span>
            <strong className="metric-card__word">
              {{
                basic: '기본',
                standard: '표준',
                advanced: '고급',
                expert: '전문가',
              }[summary.complexity_band]}
            </strong>
            <p>전문가 검토 필요 항목 {summary.expert_review_count}건</p>
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

        <div className="result-columns">
          <div className="findings-panel">
            <div className="panel-heading">
              <div>
                <span className="card-label">근거가 있는 진단</span>
                <h3>우선 확인할 항목</h3>
              </div>
              <span>{Math.min(result.findings.length, 6)}개 표시</span>
            </div>
            <div className="finding-list">
              {result.findings.slice(0, 6).map((finding) => (
                <FindingCard key={finding.id} finding={finding} />
              ))}
            </div>
            {result.findings.length > 6 && (
              <button className="text-button" type="button" disabled>
                전체 {result.findings.length}개 보기 <ChevronRight size={16} />
              </button>
            )}
          </div>

          <aside className="quote-panel" aria-label="수정 범위와 예상 금액 미리보기">
            <div className="quote-panel__eyebrow">
              <Sparkles size={17} />
              수정 범위와 예상 금액
            </div>
            <h3>{quote.headline}</h3>
            <div className="quote-price">
              <strong>{formatCurrency(quote.amount)}</strong>
              {quote.amount !== null && <span>파일 1개 기준</span>}
            </div>

            <div className="quote-factors">
              {quote.factors.map((factor) => (
                <span key={factor}>{factor}</span>
              ))}
            </div>

            <div className="scope-list">
              <h4>추후 수정 제공 시 예상 범위</h4>
              {quote.included.map((item) => (
                <p key={item}>
                  <Check size={16} />
                  {item}
                </p>
              ))}
            </div>

            <div className="scope-list scope-list--excluded">
              <h4>예상 범위에서 제외</h4>
              {quote.excluded.map((item) => (
                <p key={item}>
                  <ChevronRight size={16} />
                  {item}
                </p>
              ))}
            </div>

            <button className="button button--primary button--wide" type="button" disabled>
              수정 기능은 아직 제공하지 않습니다
              <FileClock size={18} />
            </button>
            <p className="prototype-note">
              이 테스트 버전에서는 결제, 전문가 견적 요청, 실제 파일 수정 기능을 제공하지 않습니다.
            </p>
          </aside>
        </div>

        <div className="limitations-card">
          <ShieldAlert size={22} aria-hidden="true" />
          <div>
            <h3>정적 검사 결과를 해석할 때 알아둘 점</h3>
            <ul>
              {result.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="result-next-step">
          <div>
            <FileClock size={24} />
            <div>
              <strong>현재는 진단 결과와 예상 범위를 확인하는 단계입니다.</strong>
              <span>결제와 실제 수정 기능은 제공하지 않습니다. 결과가 이해되는지와 문제 범위·예상 금액이 납득되는지를 먼저 확인해 주세요.</span>
            </div>
          </div>
          <button className="button button--outline" type="button" disabled>
            <CircleHelp size={17} />
            결제·수정 기능 준비 중
          </button>
        </div>
      </div>
    </section>
  );
}
