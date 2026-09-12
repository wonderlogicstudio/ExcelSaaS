import type { Finding } from '../types';
import { findingIdentity, type RevalidationComparison } from '../lib/revalidation';

function FindingLocation({ finding }: { finding: Finding }) {
  if (!finding.sheet && !finding.cell) {
    return <>통합문서 수준 (시트·셀 지정 없음)</>;
  }
  return <>{finding.sheet ? `시트: ${finding.sheet}` : '시트 지정 없음'} · {finding.cell ? `셀: ${finding.cell}` : '셀 지정 없음'}</>;
}

function ComparisonGroup({ id, title, findings, previous = false }: {
  id: string;
  title: string;
  findings: Finding[];
  previous?: boolean;
}) {
  return (
    <article aria-labelledby={id}>
      <strong className="revalidation-group__count">{findings.length}</strong>
      <h4 id={id}>{title}</h4>
      {findings.length === 0 ? <p>해당 항목이 없습니다.</p> : (
        <details className="revalidation-details">
          <summary>항목 위치 보기 · {findings.length}건</summary>
          <ul aria-label={`${title} 항목 위치`}>
            {findings.map((finding) => (
              <li key={findingIdentity(finding)}>
                <span className="revalidation-details__title">{finding.title}</span>
                <span className="revalidation-details__rule">{finding.rule_code}</span>
                <span>{previous ? '이전 위치' : '현재 위치'} — <FindingLocation finding={finding} /></span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  );
}

export function RevalidationPanel({ comparison, onPrepareRevalidation }: {
  comparison: RevalidationComparison | null;
  onPrepareRevalidation: () => void;
}) {
  return (
    <section className="revalidation-panel" aria-labelledby="revalidation-title">
      <div className="panel-heading">
        <div><span className="card-label">직접 수정한 파일의 동일 규칙 재검사</span><h3 id="revalidation-title">수정 후 다시 검사</h3></div>
        <button className="button button--outline button--small" type="button" onClick={onPrepareRevalidation}>수정 후 파일 선택</button>
      </div>
      {comparison ? (
        <>
          {comparison.versionMismatch && <p className="revalidation-panel__warning">scanner 또는 규칙 세트 버전이 달라 비교 결과가 근사치일 수 있습니다.</p>}
          {(comparison.previousWasTruncated || comparison.currentWasTruncated) && <p className="revalidation-panel__warning">두 검사 중 하나 이상이 일부 셀만 검사했습니다. 비교 범위가 완전하지 않을 수 있습니다.</p>}
          <div className="revalidation-grid">
            <ComparisonGroup id="revalidation-removed" title="이번 재검사에서 더 이상 탐지되지 않음" findings={comparison.noLongerDetected} previous />
            <ComparisonGroup id="revalidation-continuing" title="계속 탐지됨" findings={comparison.stillDetected} />
            <ComparisonGroup id="revalidation-new" title="새롭게 탐지됨" findings={comparison.newlyDetected} />
          </div>
          <p>‘더 이상 탐지되지 않음’은 같은 정적 규칙이 이번 위치에서 신호를 찾지 못했다는 뜻일 뿐, 업무적 해결이나 계산 결과의 정확성을 보장하지 않습니다.</p>
          <p className="revalidation-panel__limits">규칙과 위치를 기준으로 비교합니다. 시트 이름을 바꾸거나 셀을 이동하면 같은 항목이 ‘더 이상 탐지되지 않음’과 ‘새롭게 탐지됨’으로 나뉠 수 있습니다. 셀 값이나 계산 결과의 변경은 비교하지 않습니다.</p>
        </>
      ) : (
        <p>결과를 확인한 뒤 Excel에서 직접 수정하고, 수정한 파일을 선택하세요. 이전 원본 파일은 보관하지 않으며 같은 브라우저 화면에서 이전 결과와 현재 결과만 비교합니다.</p>
      )}
    </section>
  );
}
