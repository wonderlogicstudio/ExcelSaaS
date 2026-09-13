import { useRef } from 'react';
export type CoreStep = 1 | 2 | 3 | 4;
export type DeliveryProgress = { approvalAvailable: boolean; deliveryAvailable: boolean; ready: boolean };
export const initialDeliveryProgress: DeliveryProgress = { approvalAvailable: false, deliveryAvailable: false, ready: false };
const steps = [
  { number: 1, title: '무료 진단', detail: '위치와 수식 비교' },
  { number: 2, title: '수정 범위·검증', detail: '대상과 지원 여부' },
  { number: 3, title: '변경 승인', detail: '전후 값과 영향' },
  { number: 4, title: '결과 받기', detail: '수정본·변경내역·재검증' },
] as const;
export function CoreFlowTabs({ active, diagnosisComplete, progress, onChange }: { active: CoreStep; diagnosisComplete: boolean; progress: DeliveryProgress; onChange: (step: CoreStep) => void }) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const enabled = [true, diagnosisComplete, diagnosisComplete && progress.approvalAvailable, diagnosisComplete && progress.deliveryAvailable];
  const complete = [diagnosisComplete, progress.approvalAvailable, progress.deliveryAvailable, progress.ready];
  const reasons = ['', '무료 진단이 끝나면 열립니다.', '지원 범위 검증과 이용 권리 확인 후 열립니다.', '정확한 변경을 별도로 승인하면 열립니다.'];
  return <section className="core-flow shell" aria-label="진단부터 결과까지">
    <div className="core-flow__tabs" role="tablist" aria-label="작업 단계">{steps.map((step, index) => <button key={step.number} ref={element => { refs.current[index] = element; }} id={`core-tab-${step.number}`} type="button" role="tab"
      aria-selected={active === step.number} aria-controls={step.number === 1 ? 'core-diagnosis-panel' : 'core-work-panel'} disabled={!enabled[index]} tabIndex={active === step.number ? 0 : -1}
      onClick={() => onChange(step.number)} onKeyDown={event => {
        if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault(); const available = steps.filter((_, i) => enabled[i]).map(s => s.number); const current = available.indexOf(step.number);
        const next = event.key === 'Home' ? available[0] : event.key === 'End' ? available.at(-1)! : available[(current + (event.key === 'ArrowRight' ? 1 : -1) + available.length) % available.length];
        onChange(next); refs.current[next - 1]?.focus();
      }}>
      <span className="core-flow__number">{step.number}</span><strong>{step.title}</strong><small>{step.detail}</small>
      <span className="core-flow__state">{active === step.number ? '현재 단계' : complete[index] ? '완료 · 다시 보기' : enabled[index] ? '진행 가능' : '앞 단계 완료 후'}</span>
    </button>)}</div>
    <p className="core-flow__note">{active === 1 ? '먼저 결과를 이해하고, 확인할 항목을 선택해 다음 단계로 이동하세요.' : active === 2 ? '어떤 셀을 어떤 기준으로 바꿀지 정하고 지원 여부를 검사합니다. 아직 변경하지 않습니다.' : active === 3 ? '정확한 변경 전후와 계산 결과를 확인한 뒤 별도로 승인하세요.' : '승인한 변경만 사본에 적용하고 검증한 파일을 받습니다.'}</p>
    <span className="sr-only">{steps.filter((_, i) => !enabled[i]).map(s => `${s.title}: ${reasons[s.number - 1]}`).join(' ')}</span>
  </section>;
}
