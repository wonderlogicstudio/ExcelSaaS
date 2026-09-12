import type { Finding, FindingUserStatus } from '../types';
import { findingIdentity } from '../lib/revalidation';
import { userStatusLabel } from '../lib/diagnosisCsv';

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

function SharedEvidence({ items }: { items: Evidence[] }) {
  const primaryLabels = new Set(['발견된 사실', '발생 가능한 영향', 'Excel에서 확인하는 방법']);
  const primary = items.filter(item => primaryLabels.has(item.label));
  const extra = items.filter(item => !primaryLabels.has(item.label));
  return <div className="diagnosis-common-evidence"><EvidenceList items={primary}/>
    {extra.length>0 && <details><summary>추가 판단 기준과 검사 한계</summary><EvidenceList items={extra}/></details>}
  </div>;
}

function EvidenceList({ items }: { items: Evidence[] }) {
  return <dl className="diagnosis-evidence">{items.map(item => <div key={item.label}><dt>{item.label}</dt><dd>{item.value}</dd></div>)}</dl>;
}

interface Props {
  findings: Finding[]; allFindings: Finding[]; mode: 'groups' | 'table';
  statuses: Record<string, FindingUserStatus>;
  categoryLabel: (finding: Finding) => string;
  onStatusChange: (finding: Finding, status: FindingUserStatus) => void;
  onReviewGroup: (findings: Finding[]) => void;
}

const severityLabels = { critical: '중요', warning: '주의', info: '참고' };
const groupTitle = (f: Finding) => f.rule_code === 'FORMULA_PATTERN_GAP' ? '반복 수식의 누락·상수 대체 후보'
  : f.rule_code === 'FORMULA_PATTERN_OUTLIER' ? '주변 수식과 다른 패턴 후보' : f.title;

export function ProgressiveFindingViews({ findings, allFindings, mode, statuses, categoryLabel, onStatusChange, onReviewGroup }: Props) {
  const groups = new Map<string, Finding[]>();
  for (const f of findings) groups.set(f.rule_code, [...(groups.get(f.rule_code) ?? []), f]);
  const commonByRule = new Map([...groups.keys()].map(rule => [rule, commonEvidence(allFindings.filter(f=>f.rule_code===rule))]));
  const cell = (finding: Finding, shared: Evidence[]) => {
    const status = statuses[findingIdentity(finding)] ?? 'UNREVIEWED';
    const specific = findingEvidence(finding).filter(item => !shared.some(common => common.label === item.label && common.value === item.value));
    const formula = categoryLabel(finding) === '수식 검토 후보';
    return <details key={findingIdentity(finding)} className={`diagnosis-cell ${formula ? 'formula-audit-finding' : 'finding'}`}>
      <summary className="diagnosis-cell__summary">
        <strong className={formula ? 'formula-audit-finding__location' : 'finding__location'}>{[finding.sheet, finding.cell].filter(Boolean).join(' · ') || '통합문서 전체'}</strong>
        <span>{userStatusLabel[status]}</span><span aria-hidden="true">위치 근거 보기</span>
      </summary>
      <div className="diagnosis-cell__details">
        <EvidenceList items={specific} />
        {!specific.length && <p>이 위치에 위의 유형 설명이 적용됩니다.</p>}
        <label className="finding__status-control"><span>사용자 처리 상태</span>
          <select aria-label={`${finding.rule_code} ${finding.sheet ?? ''} ${finding.cell ?? ''} 사용자 처리 상태`} value={status}
            onChange={event => onStatusChange(finding, event.target.value as FindingUserStatus)}>
            {(Object.keys(userStatusLabel) as FindingUserStatus[]).map(option => <option key={option} value={option}>{userStatusLabel[option]}</option>)}
          </select>
        </label>
      </div>
    </details>;
  };
  if (mode === 'table') return <>
    <details className="diagnosis-table-guides"><summary>유형별 공통 설명</summary>{[...groups.entries()].map(([rule, leaves]) =>
      <section key={rule}><h4>{groupTitle(leaves[0])}</h4><EvidenceList items={commonByRule.get(rule)!} /></section>)}</details>
    <table className="finding-table"><caption>필터에 맞는 반환 상세 전체 표 · 위치별 근거와 처리 상태</caption>
      <thead><tr><th scope="col">검사 종류</th><th scope="col">규칙</th><th scope="col">시트 · 셀</th><th scope="col">위치별 근거 · 처리 상태</th></tr></thead>
      <tbody>{findings.map(f => <tr key={findingIdentity(f)}><td data-label="검사 종류">{categoryLabel(f)}</td><td data-label="규칙">{f.rule_code}</td>
        <td data-label="시트 · 셀">{f.sheet || '통합문서'} · {f.cell || '전체'}</td><td data-label="위치별 근거 · 처리 상태">{cell(f,commonByRule.get(f.rule_code)!)}</td></tr>)}</tbody>
    </table>
  </>;
  return <div className="finding-list">{[...groups.entries()].map(([rule, leaves]) => {
    const allOfType = allFindings.filter(f => f.rule_code === rule);
    const common = commonByRule.get(rule)!;
    const severity = leaves.some(f=>f.severity==='critical') ? 'critical' : leaves.some(f=>f.severity==='warning') ? 'warning' : 'info';
    return <section className="finding-group diagnosis-type" key={rule} aria-label={`${rule} 유형`}>
      <details className="diagnosis-type__disclosure">
        <summary className="diagnosis-type__summary">
          <span className={`severity severity--${severity}`}>{severityLabels[severity]}</span>
          <h4>{groupTitle(leaves[0])}</h4><span className="diagnosis-type__count">{leaves.length}건{leaves.length!==allOfType.length ? ` / 전체 ${allOfType.length}건` : ''}</span>
          <span className="diagnosis-source">{categoryLabel(leaves[0])}</span>
        </summary>
        <div className="diagnosis-type__body">
          <code>{rule}</code><SharedEvidence items={common} />
          <div className="diagnosis-type__locations-heading"><h5>위치별 근거</h5>
            <button className="button button--outline button--small" type="button" disabled={leaves.every(f=>statuses[findingIdentity(f)]==='REVIEWED')}
              onClick={()=>onReviewGroup(leaves)}>표시된 {leaves.length}개 확인함</button>
          </div>
          <div className="diagnosis-cell-list">{leaves.map(f => cell(f,common))}</div>
        </div>
      </details>
    </section>;
  })}</div>;
}
