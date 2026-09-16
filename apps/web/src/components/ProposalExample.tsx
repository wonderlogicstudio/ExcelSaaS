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
  return (p.profile_version ?? p.change_kind) === 'RP01_NUMERIC_TEXT_FIELD_V1' || p.change_kind === 'TYPE_NORMALIZATION' ? '숫자 텍스트 정리' : '빈 셀 수식 복원';
}
export function ProposalExample({ detail, job, intent }: { detail: PlanDetail; job: DeliveryJob; intent?: RepairIntent }) {
  const policyCells = policyTargets(job.policy);
  const preferred = intent?.enabled && detail.patches.some(p => p.sheet === intent.sheet && p.cell === intent.cell)
    ? { sheet: intent.sheet, cell: intent.cell }
    : policyCells[0];
  const patch = detail.patches.find(p => p.cell === preferred?.cell && p.sheet === preferred?.sheet) ?? detail.patches[0];
  if (!patch) return null;
  const calculated = detail.impact.find(i => i.sheet === patch.sheet && i.cell === patch.cell);
  const after = patch.after.type === 'formula' ? calculated?.after : patch.after;
  const verdict = intentVerdict(intent, detail, job.policy);
  const indirect = detail.impact.filter(i => !detail.patches.some(p => p.sheet === i.sheet && p.cell === i.cell));
  const byType = detail.patches.reduce<Record<string, number>>((acc, p) => { const key = patchType(p); acc[key] = (acc[key] ?? 0) + 1; return acc; }, {});
  const typeSummary = Object.entries(byType).map(([name, count]) => `${name} ${count}곳`).join(' · ');
  return <section className="proposal-example" aria-label="대표 수정 예시"><span className="section-kicker">검증한 제안 · 아직 원본 변경 없음</span><h3>예를 들면 이렇게 바뀝니다</h3>
    <p><strong>{patch.sheet} · {patch.cell}</strong> · 선택한 {detail.patches.length}곳 중 한 가지 예시</p>
    <div className="proposal-before-after"><div><span>현재</span><strong data-proposal-before={patch.cell}>{label(patch.before)}</strong></div><span aria-hidden="true">→</span><div><span>{patch.after.type === 'formula' ? '이 방식으로 채우면' : '숫자로 바꾸면'}</span><strong data-proposal-after={patch.cell}>{after ? label(after) : '계산 결과를 확인하지 못함'}</strong></div></div>
    <p>{patch.after.type === 'formula' ? '선택한 기준 수식을 해당 행으로 옮긴 후 지원 엔진에서 실제로 계산한 값입니다.' : '문자 표기를 계산할 수 있는 숫자 타입으로 바꿀 예시입니다. 합계 등에 미치는 영향도 함께 검사했습니다.'}</p>
    <p>수정할 위치 {detail.patches.length}곳({typeSummary}) · 함께 달라지는 계산 결과 {indirect.length}곳. 아래 정확한 변경계획에서 모든 세부 항목을 펼쳐 확인할 수 있습니다.</p>
    {intent?.enabled && <div className={`proposal-intent-verdict is-${verdict.status}`} role="status"><strong>{verdict.status === 'matched' ? '원하는 결과와 대조 완료' : verdict.status === 'mismatch' ? '원하는 결과와 다릅니다' : '요청을 아직 확인할 수 없습니다'}</strong><p>{verdict.message}</p>{!['none','matched'].includes(verdict.status) && <p>현재 요청으로는 변경 승인에 진행할 수 없습니다. ‘다른 제안으로 다시 선택’에서 요청 또는 규칙을 다시 확인하세요.</p>}</div>}
  </section>;
}
