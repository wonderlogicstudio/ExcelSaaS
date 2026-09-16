import type { Finding } from '../types';
import type { PlanDetail } from '../components/RepairPlanPreview';
import { reviewDisposition } from './repairReview';

export const RP01 = 'RP01_NUMERIC_TEXT_FIELD_V1';
export const RP02 = 'RP02_APPROVED_FORMULA_RESTORE_V1';
export type RepairIntent = { enabled: boolean; kind: 'number' | 'same_formula'; sheet: string; cell: string; expected: string; anchor: string };
export const noRepairIntent: RepairIntent = { enabled: false, kind: 'number', sheet: '', cell: '', expected: '', anchor: '' };
export type RepairProposal = { id: string; sheet: string; column: string; profile?: string; title: string; explanation: string; findings: Finding[] };
export type RepairPolicyItem = { profile: string; sheet: string; targets: string[]; anchor?: string };
export type RepairPolicy = RepairPolicyItem | { profile: string; items: RepairPolicyItem[] };
export const cellOrder = (a: string, b: string) => a.localeCompare(b, 'en', { numeric: true });
export function proposalGroups(findings: Finding[]): RepairProposal[] {
  const result = new Map<string, RepairProposal>();
  for (const f of findings) {
    const profile = reviewDisposition(f).profile, sheet = f.sheet ?? '통합문서', column = f.cell?.match(/^[A-Z]+/)?.[0] ?? '';
    const id = JSON.stringify([sheet, column, profile ?? f.formula_pattern?.pattern_subtype ?? f.rule_code]);
    let group = result.get(id);
    if (!group) {
      const range = f.formula_pattern?.pattern_subtype === 'RANGE_BOUNDARY_DRIFT';
      const constant = f.formula_pattern?.pattern_subtype === 'CONSTANT_OVERRIDE_CANDIDATE';
      group = { id, sheet, column, profile, findings: [],
        title: profile === RP01 ? '문자로 저장된 숫자를 계산에 포함하기' : profile === RP02 ? '비어 있는 계산 칸을 같은 방식으로 채우기' : range ? '합계·참조 범위의 차이 확인' : constant ? '수식 대신 입력한 고정값 확인' : f.title,
        explanation: profile === RP01 ? '표시된 문자를 숫자로 바꾸면 합계에 포함되는 값이 달라질 수 있습니다. 금액·개수인지 확인한 뒤 실제 영향을 계산합니다.'
          : profile === RP02 ? '주변의 계산 칸을 기준으로 제안합니다. 같은 업무 계산을 해야 하는 빈 칸인지 확인해야 합니다.'
            : range ? '어느 범위가 업무상 맞는지 추가 판단이 필요합니다. 현재는 기존 SUM 범위를 바꾸거나 변경 후 값을 계산하는 제안을 제공하지 않습니다.'
              : constant ? '직접 입력한 조정값일 수 있습니다. 현재 엔진은 값이 있는 셀을 수식으로 덮어쓰지 않습니다.' : '현재 규칙으로 수정안을 만들 수 없습니다. 무료 진단의 위치·근거는 확인할 수 있습니다.' };
      result.set(id, group);
    }
    if (!group.findings.some(x => x.cell === f.cell)) group.findings.push(f);
  }
  return [...result.values()].map(p => ({ ...p, findings: p.findings.sort((a, b) => cellOrder(a.cell ?? '', b.cell ?? '')) }));
}
// Canonical decimal comparison, without lossy Number conversion or a tolerance that hides differences.
export function canonicalDecimal(value: unknown): string | null {
  const raw = String(value ?? '').trim();
  if (!raw || raw.length > 80 || !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?$/.test(raw)) return null;
  const [mantissa, exponent = '0'] = raw.toLowerCase().split('e'), shift = Number(exponent);
  if (Math.abs(shift) > 100) return null;
  const negative = mantissa.startsWith('-'); const [whole, fraction = ''] = mantissa.replace(/^[+-]/, '').split('.');
  let digits = ((whole || '0') + fraction).replace(/^0+/, '') || '0', scale = fraction.length - shift;
  if (scale < 0) { digits += '0'.repeat(-scale); scale = 0; }
  while (scale > 0 && digits.endsWith('0')) { digits = digits.slice(0, -1); scale--; }
  if (!digits || /^0+$/.test(digits)) return '0';
  return `${negative ? '-' : ''}${digits}:${scale}`;
}
export function intentVerdict(intent: RepairIntent | undefined, detail: PlanDetail, policy?: RepairPolicy) {
  if (!intent?.enabled) return { status: 'none' as const, message: '별도 요청 없이 선택한 규칙으로 계산했습니다.' };
  if (!intent.sheet || !intent.cell) return { status: 'unverified' as const, message: '원하는 결과를 확인할 위치를 먼저 선택하세요.' };
  if (intent.kind === 'same_formula') {
    const patch = detail.patches.find(p => p.sheet === intent.sheet && p.cell === intent.cell && p.before.type === 'blank' && p.after.type === 'formula');
    const policies = policy && 'items' in policy ? policy.items : policy ? [policy] : [];
    const matches = patch && intent.anchor && policies.some(item => item.profile === RP02 && item.sheet === intent.sheet && item.targets.includes(intent.cell) && item.anchor === intent.anchor);
    return matches ? { status: 'matched' as const, message: `${intent.sheet} ${intent.cell}에 ${intent.anchor}의 계산 방식을 적용한 제안입니다. 행에 맞게 참조를 옮겨 계산했습니다.` }
      : { status: 'unverified' as const, message: '요청한 기준 셀·대상과 이번 제안이 다릅니다. 같은 계산 방식 적용은 실제 빈 셀 복원에서만 확인할 수 있습니다.' };
  }
  const expected = canonicalDecimal(intent.expected);
  if (expected === null) return { status: 'unverified' as const, message: '원하는 숫자를 올바르게 입력해야 요청과 대조할 수 있습니다. 계산값을 원하는 숫자로 덮어쓰지 않습니다.' };
  const calculated = detail.impact.find(x => x.sheet === intent.sheet && x.cell === intent.cell)?.after;
  const patch = detail.patches.find(x => x.sheet === intent.sheet && x.cell === intent.cell)?.after;
  const actual = calculated ?? patch;
  if (!actual || actual.type !== 'number' || canonicalDecimal(actual.value) === null) return { status: 'unverified' as const, message: '이번 변경계획에 이 위치의 검증된 숫자 결과가 없습니다. 요청이 충족됐다고 판단할 수 없습니다.' };
  return canonicalDecimal(actual.value) === expected
    ? { status: 'matched' as const, message: `요청한 ${intent.sheet} ${intent.cell}의 숫자와 이번 계산 결과가 일치합니다.` }
    : { status: 'mismatch' as const, message: `요청한 ${intent.expected}와 계산 결과 ${String(actual.value)}가 다릅니다. 요청을 맞추려고 값이나 수식을 임의로 바꾸지 않았습니다.` };
}
