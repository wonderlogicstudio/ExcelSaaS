import type { Finding } from '../types';
import { reviewDisposition, reviewKey, type RepairDraft, type ReviewSelection } from '../lib/repairReview';

export function ReviewChoice({ finding, selection }: { finding: Finding; selection: ReviewSelection }) {
  return <div className="repair-review-choice"><span>{reviewDisposition(finding).label}</span>
    <label><input type="checkbox" checked={selection.findings.some(f => reviewKey(f) === reviewKey(finding))} disabled={selection.locked}
      onChange={() => selection.toggle(finding)}/>수정 검토 선택 · {finding.sheet ?? '통합문서'} {finding.cell ?? '전체'}</label>
  </div>;
}

export function RepairReview({ selection, available, hasFile, onPrepare }: { selection: ReviewSelection; available: boolean; hasFile: boolean; onPrepare: (draft: RepairDraft) => void }) {
  const groups = new Map<string, RepairDraft>();
  for (const f of selection.findings) {
    const disposition = reviewDisposition(f);
    if (!disposition.profile || !f.sheet || !f.cell) continue;
    const key = JSON.stringify([disposition.profile, f.sheet]);
    const group = groups.get(key) ?? { profile: disposition.profile, sheet: f.sheet, targets: [] };
    if (!group.targets.includes(f.cell)) group.targets.push(f.cell);
    groups.set(key, group);
  }
  const candidates = selection.findings.filter(f => reviewDisposition(f).profile).length;
  return <section id="repair-review" className="repair-review shell" aria-labelledby="repair-review-title" tabIndex={-1}>
    <span className="section-kicker">다음 단계 · 수정 의뢰</span><h2 id="repair-review-title">수정할 범위를 먼저 확인하세요</h2>
    <p>문제의 위치·근거를 펼쳐 ‘수정 검토 선택’을 표시하세요. 선택과 ‘확인함’은 결제나 변경 승인이 아닙니다.</p>
    <div className="review-counts"><strong>검토 선택 {selection.findings.length}건</strong><span>사전 검사 후보 {candidates}건</span><span>자동 수정 미지원·판단 필요 {selection.findings.length - candidates}건</span></div>
    <p>후보 수는 수정 가능 수가 아닙니다. 업무 기준·파일 보존·계산 영향을 검사한 뒤에만 지원 범위를 알 수 있습니다.</p>
    {selection.findings.length > 0 && <details open><summary>선택한 위치와 현재 처리 방법</summary><ul className="review-selected">{selection.findings.map(f => <li key={reviewKey(f)}><span><strong>{f.sheet ?? '통합문서'} · {f.cell ?? '전체'}</strong> {reviewDisposition(f).label}</span><button type="button" className="text-link" disabled={selection.locked} onClick={() => selection.toggle(f)} aria-label={`${f.sheet ?? '통합문서'} ${f.cell ?? '전체'} 검토 선택 제외`}>제외</button></li>)}</ul></details>}
    {selection.locked ? <p role="status">사전 검사 원본을 고정했습니다. 아래의 ‘선택한 수정 기준과 대상 확인’에서 범위를 바꾸고 다시 검사하세요. 최종 변경계획을 별도로 승인해야 합니다.</p>
      : available && hasFile && groups.size > 0 ? <><p>한 번에 같은 시트·수정 종류의 범위를 확인합니다. 다른 선택 항목은 이 작업에서 수정하지 않습니다.</p><div className="review-actions">{[...groups.entries()].map(([key, draft]) => <button key={key} type="button" className="button button--primary" onClick={() => onPrepare(draft)}>{draft.sheet} · {draft.targets.length}개 {draft.profile.startsWith('RP01') ? '숫자 셀' : '빈 셀'} 수정 가능 여부 확인</button>)}</div></>
        : !available || !hasFile ? <p>실제 사전 검사는 보호 베타의 업로드한 합성 파일에서 제공합니다. 샘플 결과는 수정 원본이 아닙니다. 일반 구매는 준비 중입니다.</p>
          : <p>현재 선택에 자동 수정 사전 검사 후보가 없습니다. 근거를 직접 확인하거나 아래에서 지원하는 수정 종류·셀을 지정할 수 있습니다.</p>}
    <p className="review-deliverables">제공 흐름: 지원 범위 확인 → 이용 권리 확인 → 정확한 변경계획·별도 승인 → 수정본 XLSX + 변경내역 XLSX + 재검증 HTML. 일반 구매·가격 확정은 준비 중이며, 등록된 합성 파일에만 시험권을 제공합니다.</p>
  </section>;
}
