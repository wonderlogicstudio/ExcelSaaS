import type { ReactNode } from 'react';
import type { Finding, FindingUserStatus } from '../types';
import { findingIdentity } from '../lib/revalidation';

interface Props {
  findings: Finding[];
  allFindings: Finding[];
  mode: 'groups' | 'table';
  statuses: Record<string, FindingUserStatus>;
  renderFinding: (finding: Finding, sharedGuidance: boolean) => ReactNode;
  renderGuidance: (finding: Finding) => ReactNode;
  onReviewGroup: (findings: Finding[]) => void;
}

export function FindingViews({ findings, allFindings, mode, statuses, renderFinding, renderGuidance, onReviewGroup }: Props) {
  if (mode === 'table') {
    return (
      <table className="finding-table">
        <caption>필터에 맞는 반환 상세 전체 표 · 위치별 근거와 처리 상태</caption>
        <thead><tr><th scope="col">규칙</th><th scope="col">시트 · 셀</th><th scope="col">근거 · 사용자 처리 상태</th></tr></thead>
        <tbody>{findings.map((finding) => (
          <tr key={findingIdentity(finding)}>
            <td data-label="규칙">{finding.rule_code}</td>
            <td data-label="시트 · 셀">{finding.sheet || '시트 지정 없음'} · {finding.cell || '셀 지정 없음'}</td>
            <td data-label="근거 · 사용자 처리 상태">{renderFinding(finding, false)}</td>
          </tr>
        ))}</tbody>
      </table>
    );
  }
  const groups = new Map<string, Finding[]>();
  for (const finding of findings) {
    const group = groups.get(finding.rule_code) ?? [];
    group.push(finding);
    groups.set(finding.rule_code, group);
  }
  return <div className="finding-list">{[...groups.entries()].map(([rule, leaves]) => (
    <section className="finding-group" key={rule} aria-label={`${rule} 유형`}>
      <div className="finding-group__heading">
        <div><h4>{leaves[0].title}</h4><code>{rule}</code><p>필터 표시 {leaves.length}건 / 이 유형의 반환 상세 {allFindings.filter((finding) => finding.rule_code === rule).length}건</p></div>
        <button className="button button--outline button--small" type="button"
          disabled={leaves.every((finding) => statuses[findingIdentity(finding)] === 'REVIEWED')}
          onClick={() => onReviewGroup(leaves)}>표시된 {leaves.length}개 확인함</button>
      </div>
      <p className="finding-group__notice">개인 처리 상태만 바뀝니다. 변경 승인이나 파일 수정은 실행하지 않습니다.</p>
      <details className="finding-group__guide"><summary>유형 설명과 Excel 확인 방법</summary>{renderGuidance(leaves[0])}</details>
      {leaves.map((finding) => renderFinding(finding, true))}
    </section>
  ))}</div>;
}
