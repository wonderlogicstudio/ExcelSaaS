import type { Finding } from '../types';
import { reviewDisposition, reviewKey, RP03, type RepairDraft, type ReviewSelection } from '../lib/repairReview';

export function ReviewChoice({ finding, selection }: { finding: Finding; selection: ReviewSelection }) {
  return <div className="repair-review-choice"><span>{reviewDisposition(finding).label}</span>
    <label><input type="checkbox" checked={selection.findings.some(f => reviewKey(f) === reviewKey(finding))} disabled={selection.locked}
      onChange={() => selection.toggle(finding)}/>2단계에 포함 · {finding.sheet ?? '통합문서'} {finding.cell ?? '전체'}</label>
  </div>;
}
export function RepairReview({ selection, available, hasFile, onPrepare }: { selection: ReviewSelection; available: boolean; hasFile: boolean; onPrepare: (draft: RepairDraft) => void }) {
  const groups = new Map<string, RepairDraft>();
  for (const f of selection.findings) {
    const disposition = reviewDisposition(f); if (!disposition.profile || !f.sheet || !f.cell) continue;
    const key = JSON.stringify([disposition.profile, f.sheet, disposition.profile === RP03 ? f.cell : '']);
    const group = groups.get(key) ?? { profile: disposition.profile, sheet: f.sheet, targets: [] };
    if (!group.targets.includes(f.cell)) group.targets.push(f.cell); groups.set(key, group);
  }
  const candidates = selection.findings.filter(f => reviewDisposition(f).profile).length;
  return <section id="repair-review" className="repair-review shell" aria-labelledby="repair-review-title" tabIndex={-1}>
    <h2 id="repair-review-title">선택한 항목의 수정 방법 확인</h2>
    <p>1단계에서 포함한 항목입니다. 이번에는 수정할 셀과 업무 기준을 정하고, 파일을 보존하며 처리할 수 있는지 확인합니다.</p>
    <div className="review-counts"><strong>검토 선택 {selection.findings.length}건</strong><span>지원 여부 검사 후보 {candidates}건</span><span>자동 수정 미지원·판단 필요 {selection.findings.length - candidates}건</span></div>
    {selection.findings.length > 0 && <details><summary>선택한 {selection.findings.length}개 위치 확인·제외</summary><ul className="review-selected">{selection.findings.map(f => <li key={reviewKey(f)}><span><strong>{f.sheet ?? '통합문서'} · {f.cell ?? '전체'}</strong> {reviewDisposition(f).label}</span><button type="button" className="text-link" disabled={selection.locked} onClick={() => selection.toggle(f)} aria-label={`${f.sheet ?? '통합문서'} ${f.cell ?? '전체'} 검토 선택 제외`}>제외</button></li>)}</ul></details>}
    {selection.locked ? <p role="status">이 원본의 검토 범위를 고정했습니다. 아래 ‘수정 기준과 대상’에서 변경한 뒤 다시 검사할 수 있습니다.</p>
      : available && hasFile && groups.size > 0 ? <><p>한 번에 같은 시트·수정 종류를 검사합니다. 다른 유형은 이 작업에서 바꾸지 않습니다.</p><div className="review-actions">{[...groups.entries()].map(([key, draft]) => <button key={key} type="button" className="button button--primary" onClick={() => onPrepare(draft)}>{draft.sheet} · {draft.targets.length}개 {draft.profile.startsWith('RP01') ? '숫자 셀' : '빈 셀'} 수정 방법 확인</button>)}</div></>
        : !available || !hasFile ? <p>등록된 합성 파일을 직접 업로드한 보호 베타에서 검사·승인을 시험할 수 있습니다. 일반 구매는 준비 중입니다.</p>
          : selection.findings.length ? <p>선택한 항목은 현재 자동 수정 경로가 없습니다. 무료 근거를 확인하거나 지원하는 숫자 텍스트·빈 셀을 직접 지정하세요.</p> : <p>1단계에서 항목을 포함하거나, 아래에서 확인할 셀을 직접 지정하세요.</p>}
  </section>;
}
