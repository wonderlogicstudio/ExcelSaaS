import type { PlanDetail } from './RepairPlanPreview';
import type { RepairIntent } from '../lib/repairProposals';
import { intentVerdict } from '../lib/repairProposals';
import type { DeliveryJob } from './DeliveryWorkspace';

function label(value: { type: string; value: unknown }) {
  if (value.type === 'blank') return '비어 있는 칸';
  if (value.type === 'text') return `문자 “${String(value.value)}”`;
  if (value.type === 'number') return Number(value.value).toLocaleString('ko-KR', { maximumFractionDigits: 15 });
  return value.type === 'formula' ? '수식' : String(value.value);
}
function policyTargets(policy: DeliveryJob['policy']) {
  if (!policy) return [];
  return 'items' in policy ? policy.items.flatMap(item => item.targets.map(cell => ({ sheet: item.sheet, cell }))) : policy.targets.map(cell => ({ sheet: policy.sheet, cell }));
}
function patchType(p: PlanDetail['patches'][number]) {
  const kind = p.profile_version ?? p.change_kind;
  if (kind === 'RP01_NUMERIC_TEXT_FIELD_V1' || p.change_kind === 'TYPE_NORMALIZATION') return '숫자 텍스트 정리';
  if (kind === 'RP03_MONTHLY_SHEET_FORMULA_REPLACEMENT_V1' || p.change_kind === 'MONTHLY_FORMULA_REPLACEMENT') return '월별 수식 검증';
  return '빈 셀 수식 복원';
}
function formatCount(value: number) {
  return value.toLocaleString('ko-KR');
}
export function ProposalExample({ detail, job, intent }: { detail: PlanDetail; job: DeliveryJob; intent?: RepairIntent }) {
  const policyCells = policyTargets(job.policy);
  const preferred = intent?.enabled && detail.patches.some(p => p.sheet === intent.sheet && p.cell === intent.cell)
    ? { sheet: intent.sheet, cell: intent.cell }
    : policyCells[0];
  const preferredPatch = detail.patches.find(p => p.cell === preferred?.cell && p.sheet === preferred?.sheet);
  const representatives = detail.patches.reduce<PlanDetail['patches']>((items, patch) => {
    const type = patchType(patch);
    return items.some(item => patchType(item) === type) ? items : [...items, patch];
  }, []);
  const patches = preferredPatch && !representatives.some(p => p.sheet === preferredPatch.sheet && p.cell === preferredPatch.cell)
    ? [preferredPatch, ...representatives.filter(p => patchType(p) !== patchType(preferredPatch))]
    : representatives;
  if (!patches.length) return null;
  const verdict = intentVerdict(intent, detail, job.policy);
  const indirect = detail.impact.filter(i => !detail.patches.some(p => p.sheet === i.sheet && p.cell === i.cell));
  const byType = detail.patches.reduce<Record<string, number>>((acc, p) => { const key = patchType(p); acc[key] = (acc[key] ?? 0) + 1; return acc; }, {});
  const typeSummary = Object.entries(byType).map(([name, count]) => `${name} ${count}곳`).join(' · ');
  return <section className="proposal-example" aria-label="대표 수정 예시"><span className="section-kicker">검증한 제안 · 아직 원본 변경 없음</span><h3>예를 들면 이렇게 바뀝니다</h3>
    <p><strong>{formatCount(Object.keys(byType).length)}종류 · 총 {formatCount(detail.patches.length)}곳 수정 예정</strong> ({typeSummary})</p>
    <div className="proposal-example-list">{patches.map(patch => {
      const calculated = detail.impact.find(i => i.sheet === patch.sheet && i.cell === patch.cell);
      const kind = patch.profile_version ?? patch.change_kind;
      const monthly = kind === 'RP03_MONTHLY_SHEET_FORMULA_REPLACEMENT_V1' || patch.change_kind === 'MONTHLY_FORMULA_REPLACEMENT';
      const before = monthly ? calculated?.before ?? patch.before : patch.before;
      const after = patch.after.type === 'formula' ? calculated?.after : patch.after;
      return <article className="proposal-example-item" key={`${patch.sheet}:${patch.cell}`}><p><strong>{patch.sheet} · {patch.cell}</strong> · {patchType(patch)} 대표 예시</p>
        <div className="proposal-before-after"><div><span>현재</span><strong data-proposal-before={patch.cell}>{label(before)}</strong></div><span aria-hidden="true">→</span><div><span>{monthly ? '서버가 검증하면' : patch.after.type === 'formula' ? '이 방식으로 채우면' : '숫자로 바꾸면'}</span><strong data-proposal-after={patch.cell}>{after ? label(after) : '계산 결과를 확인하지 못함'}</strong></div></div>
        <p>{monthly
          ? calculated ? '서버가 원본 수식과 실제 오류를 확인한 뒤 계산한 결과입니다.' : '서버가 원본 수식과 실제 오류를 확인해야 계산 결과를 보여줄 수 있습니다.'
          : patch.after.type === 'formula'
            ? calculated ? '선택한 기준 수식을 해당 행으로 옮긴 뒤 지원 엔진이 계산한 실제 결과입니다.' : '선택한 기준 수식을 해당 행으로 옮길 계획입니다. 이 예시 셀의 계산 결과는 아직 확인하지 못했습니다.'
            : '문자 표기를 계산할 수 있는 숫자 타입으로 바꾼 예시입니다. 합계 등에 미치는 영향을 함께 검사했습니다.'}</p>
      </article>;
    })}</div>
    <p>함께 달라지는 계산 결과 {formatCount(indirect.length)}곳. 아래 정확한 변경계획에서 모든 세부 항목을 펼쳐 확인할 수 있습니다.</p>
    {intent?.enabled && <div className={`proposal-intent-verdict is-${verdict.status}`} role="status"><strong>{verdict.status === 'matched' ? '원하는 결과와 대조 완료' : verdict.status === 'mismatch' ? '원하는 결과와 다릅니다' : '요청을 아직 확인할 수 없습니다'}</strong><p>{verdict.message}</p>{!['none','matched'].includes(verdict.status) && <p>현재 요청으로는 변경 승인에 진행할 수 없습니다. ‘다른 제안으로 다시 선택’에서 요청 또는 규칙을 다시 확인하세요.</p>}</div>}
  </section>;
}
