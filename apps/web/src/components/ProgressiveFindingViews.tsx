import { reviewKey, type ReviewSelection } from '../lib/repairReview';
import { ReviewChoice } from './RepairReview';
import type { Finding, FindingUserStatus } from '../types';
import { findingIdentity } from '../lib/revalidation';
import { useState } from 'react';
import { reviewNoteLabel } from '../lib/reviewNotes';
import { OriginalFormulaComparison } from './OriginalFormulaComparison';

type Evidence = { label: string; value: string; specific?: boolean };
// Only identical explanatory fields move to the type level. Locations and pattern
// differences always stay with their cell, even when their strings happen to match.
export function findingEvidence(f: Finding): Evidence[] {
  const g = f.guidance; const p = f.formula_pattern;
  return [
    { label: '발견된 사실', value: p?.evidence_summary ?? g?.detected_fact ?? f.description },
    { label: '셀의 관찰 내용', value: f.description },
    { label: '발생 가능한 영향', value: g?.possible_impact ?? '' },
    { label: '사용자 권장 행동', value: g?.recommended_next_action ?? '' },
    { label: 'Excel에서 확인하는 방법', value: g?.how_to_check_in_excel.join(' · ') ?? '' },
    { label: '정상일 수 있는 조건', value: p?.normal_case_possibility ?? g?.when_it_may_be_normal.join(' ') ?? '' },
    { label: '조치를 우선 권장하는 경우', value: g?.when_action_is_recommended.join(' ') ?? '' },
    { label: '이번 검사에서 확인하지 않은 내용', value: g?.unchecked_scope.join(' ') ?? p?.current_limitations.join(' ') ?? '' },
    { label: '다음 정밀검증 항목', value: g?.recommended_next_checks.join(' · ') ?? '' },
    { label: '세부 탐지 유형', value: p?.pattern_subtype ?? '', specific: true },
    { label: '주변 패턴과 현재 패턴의 차이', value: p?.current_pattern_summary ?? '', specific: true },
    { label: '비교에 사용한 주변 위치', value: (p?.comparison_locations ?? p?.evidence_locations ?? []).join(' · '), specific: true },
    { label: '검사한 수식 영역', value: p?.formula_region ?? '', specific: true },
    { label: '해결 경로 · 준비 중', value: g?.repair_readiness ? `${g.repair_readiness.label} · ${g.repair_readiness.explanation} ${g.repair_readiness.required_steps.join(' → ')}` : '' },
  ].filter((item, index, rows) => item.value && (item.specific || !rows.slice(0, index).some(previous => previous.value === item.value)));
}

export function commonEvidence(findings: Finding[]): Evidence[] {
  if (!findings.length) return [];
  return findingEvidence(findings[0]).filter(item => !item.specific && findings.every(finding =>
    findingEvidence(finding).some(other => other.label === item.label && other.value === item.value)));
}

const sharedAtResult = new Set(['정상일 수 있는 조건', '조치를 우선 권장하는 경우', '이번 검사에서 확인하지 않은 내용', '다음 정밀검증 항목', '해결 경로 · 준비 중']);
export function GeneralFindingGuidance({ findings, limitations }: { findings: Finding[]; limitations: string[] }) {
  const rows = new Map<string, Evidence>();
  for (const f of findings) for (const item of findingEvidence(f)) if (sharedAtResult.has(item.label)) rows.set(item.label + item.value, item);
  return <><h4>판단할 때 참고할 내용</h4><EvidenceList items={[...rows.values()]}/><ul>{[...new Set(limitations)].map(item => <li key={item}>{item}</li>)}</ul></>;
}
function SharedEvidence({ items }: { items: Evidence[] }) {
  return <div className="diagnosis-common-evidence"><EvidenceList items={items.filter(item => !sharedAtResult.has(item.label))}/></div>;
}
function EvidenceList({ items }: { items: Evidence[] }) {
  return <dl className="diagnosis-evidence">{items.map(item => <div key={item.label + item.value}><dt>{item.label}</dt><dd>{item.value}</dd></div>)}</dl>;
}
interface Props {
  sourceFile?: File | null;
  reviewSelection?: ReviewSelection;
  findings: Finding[]; allFindings: Finding[]; mode: 'groups' | 'table';
  statuses: Record<string, FindingUserStatus>;
  categoryLabel: (finding: Finding) => string;
  onStatusChange: (finding: Finding, status: FindingUserStatus) => void;
  onReviewGroup: (findings: Finding[]) => void;
}
const severityLabels = { critical: '중요', warning: '주의', info: '참고' };
const groupTitle = (f: Finding) => f.rule_code === 'FORMULA_PATTERN_GAP' ? '반복 수식의 누락·상수 대체 후보'
  : f.rule_code === 'FORMULA_PATTERN_OUTLIER' ? '주변 수식과 다른 패턴 후보' : f.title;

function FindingCell({ finding, shared, status, formula, sourceFile, reviewSelection, onStatusChange }: {
  finding: Finding; shared: Evidence[]; status: FindingUserStatus; formula: boolean; sourceFile?: File | null;
  reviewSelection?: ReviewSelection; onStatusChange: Props['onStatusChange'];
}) {
  const [open, setOpen] = useState(false);
  const specific = findingEvidence(finding).filter(item => !sharedAtResult.has(item.label) && !shared.some(common => common.label === item.label && common.value === item.value));
  return <details className={`diagnosis-cell ${formula ? 'formula-audit-finding' : 'finding'}`} onToggle={event => { if (event.target === event.currentTarget) setOpen(event.currentTarget.open); }}>
    <summary className="diagnosis-cell__summary">
      <strong className={formula ? 'formula-audit-finding__location' : 'finding__location'}>{[finding.sheet, finding.cell].filter(Boolean).join(' · ') || '통합문서 전체'}</strong>
      {status !== 'UNREVIEWED' && <span>내 메모: {reviewNoteLabel[status]}</span>}<span aria-hidden="true">수식·근거 보기</span>
    </summary>
    <div className="diagnosis-cell__details">
      <OriginalFormulaComparison file={sourceFile} finding={finding} active={open}/>
      <EvidenceList items={specific.filter(item => !item.specific && (!finding.formula_pattern || !['발견된 사실','셀의 관찰 내용'].includes(item.label)))} />
      {finding.formula_pattern && <p className="finding-next-action">주변과 다른 계산이 의도된 것인지 확인하세요. 아래에 포함하면 2단계에서 지원 여부와 수정 기준을 검토합니다.</p>}
      {reviewSelection && <ReviewChoice finding={finding} selection={reviewSelection}/>}
      <details className="finding-notes"><summary>내 검토 메모 · 선택사항</summary><label className="finding__status-control"><span>개인 메모</span>
        <select aria-label={`${finding.rule_code} ${finding.sheet ?? ''} ${finding.cell ?? ''} 사용자 처리 상태`} value={status} onChange={event => onStatusChange(finding, event.target.value as FindingUserStatus)}>
          {(Object.keys(reviewNoteLabel) as FindingUserStatus[]).map(option => <option key={option} value={option}>{reviewNoteLabel[option]}</option>)}
        </select></label></details>
      <details className="diagnosis-technical"><summary>기술 상세</summary><p>규칙 {finding.rule_code} · {finding.guidance?.evidence_grade ?? '탐지 근거 참고'}</p><EvidenceList items={specific.filter(item => item.specific)}/></details>
    </div>
  </details>;
}
export function ProgressiveFindingViews({ findings, allFindings, mode, statuses, categoryLabel, onStatusChange, onReviewGroup, reviewSelection, sourceFile }: Props) {
  const groups = new Map<string, Finding[]>();
  for (const f of findings) groups.set(f.rule_code, [...(groups.get(f.rule_code) ?? []), f]);
  const commonByRule = new Map([...groups.keys()].map(rule => [rule, commonEvidence(allFindings.filter(f => f.rule_code === rule)).filter(item => !sharedAtResult.has(item.label) && !(allFindings.find(f => f.rule_code === rule)?.formula_pattern && ['발견된 사실','셀의 관찰 내용'].includes(item.label)))]));
  const cell = (finding: Finding, shared: Evidence[]) => <FindingCell key={findingIdentity(finding)} finding={finding} shared={shared} status={statuses[findingIdentity(finding)] ?? 'UNREVIEWED'} formula={categoryLabel(finding) === '수식 검토 후보'} sourceFile={sourceFile} reviewSelection={reviewSelection} onStatusChange={onStatusChange}/>;
  if (mode === 'table') return <>
    <details className="diagnosis-table-guides"><summary>유형별 공통 설명</summary>{[...groups.entries()].map(([rule, leaves]) => <section key={rule}><h4>{groupTitle(leaves[0])}</h4><EvidenceList items={commonByRule.get(rule)!}/></section>)}</details>
    <table className="finding-table"><caption>필터에 맞는 반환 상세 전체 표 · 위치별 근거와 처리 상태</caption>
      <thead><tr><th scope="col">검사 종류</th><th scope="col">규칙</th><th scope="col">시트 · 셀</th><th scope="col">위치별 근거 · 처리 상태</th></tr></thead>
      <tbody>{findings.map(f => <tr key={findingIdentity(f)}><td data-label="검사 종류">{categoryLabel(f)}</td><td data-label="규칙">{f.rule_code}</td><td data-label="시트 · 셀">{f.sheet || '통합문서'} · {f.cell || '전체'}</td><td data-label="위치별 근거 · 처리 상태">{cell(f, commonByRule.get(f.rule_code)!)}</td></tr>)}</tbody>
    </table>
  </>;
  return <div className="finding-list">{[...groups.entries()].map(([rule, leaves]) => {
    const allOfType = allFindings.filter(f => f.rule_code === rule), common = commonByRule.get(rule)!;
    const severity = leaves.some(f => f.severity === 'critical') ? 'critical' : leaves.some(f => f.severity === 'warning') ? 'warning' : 'info';
    return <section className="finding-group diagnosis-type" key={rule} aria-label={`${rule} 유형`}><details className="diagnosis-type__disclosure">
      <summary className="diagnosis-type__summary"><span className={`severity severity--${severity}`}>{severityLabels[severity]}</span><h4>{groupTitle(leaves[0])}</h4><span className="diagnosis-type__count">{leaves.length}건{leaves.length !== allOfType.length ? ` / 전체 ${allOfType.length}건` : ''}</span><span className="diagnosis-source">{categoryLabel(leaves[0])}</span></summary>
      <div className="diagnosis-type__body"><SharedEvidence items={common}/>
        <div className="diagnosis-type__locations-heading"><h5>위치와 원본 비교</h5>{reviewSelection && <button type="button" className="button button--outline button--small" disabled={reviewSelection.locked || leaves.every(f => reviewSelection.findings.some(selected => reviewKey(selected) === reviewKey(f)))} onClick={() => { for (const f of leaves) if (!reviewSelection.findings.some(selected => reviewKey(selected) === reviewKey(f))) reviewSelection.toggle(f); }}>표시된 {leaves.length}개를 2단계에 포함</button>}</div>
        <div className="diagnosis-cell-list">{[...new Set(leaves.map(f => f.sheet ?? '통합문서'))].map(sheet => <section className="diagnosis-sheet" key={sheet} aria-label={`${sheet} 위치`}><h5>{sheet} · {leaves.filter(f => (f.sheet ?? '통합문서') === sheet).length}개 위치</h5>{leaves.filter(f => (f.sheet ?? '통합문서') === sheet).map(f => cell(f, common))}</section>)}</div>
        <details className="finding-bulk-notes"><summary>이 유형의 메모 일괄 변경</summary><button className="button button--ghost button--small" type="button" disabled={leaves.every(f => statuses[findingIdentity(f)] === 'REVIEWED')} onClick={() => onReviewGroup(leaves)}>표시된 {leaves.length}개를 읽어봄으로 메모</button></details>
      </div></details></section>;
  })}</div>;
}
