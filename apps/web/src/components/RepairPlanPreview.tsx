import { useEffect, useRef, useState } from 'react';
import { RepairDelivery } from './RepairDelivery';
import { OrderStatus } from './OrderStatus';
import { deliveryRequest, type DeliveryJob } from './DeliveryWorkspace';
import type { CoreStep } from './CoreFlowTabs';

export type PlanDetail = { digest:string; patches:{candidate_id:string;sheet:string;cell:string;before:{type:string;value:unknown};after:{type:string;value:unknown}}[];
  impact:{sheet:string;cell:string;before:{type:string;value:unknown};after:{type:string;value:unknown}}[]; expires_at:number; technical_changes?:{kind:string}[] };
function display(cell:{type:string;value:unknown}) {
  if(cell.type==='blank')return '빈 셀'; if(cell.type==='text')return `문자 “${String(cell.value)}”`; if(cell.type==='formula')return String(cell.value);
  if(cell.type==='number')return `숫자 ${Number(cell.value).toLocaleString('ko-KR',{maximumFractionDigits:15})}`; return String(cell.value);
}
export function RepairPlanPreview({ job, onJob, guidedStep, onNextStep }: { job:DeliveryJob; onJob:(job:DeliveryJob)=>void; guidedStep?:CoreStep; onNextStep?:(step:CoreStep)=>void }) {
  const [busy,setBusy]=useState(false), [error,setError]=useState<string|null>(null), [detail,setDetail]=useState<PlanDetail|null>(null);
  const [detailBusy,setDetailBusy]=useState(false); const [expiredDigest,setExpiredDigest]=useState<string|null>(null); const abort=useRef<AbortController|null>(null);
  const plan=job.plan_summary; const rights=!!(job.internal_rehearsal||job.entitlement_active); const currentDetail=detail?.digest===plan?.digest ? detail : null;
  const scopeVisible=!guidedStep||guidedStep===2;
  const validPlan=plan?.status==='PREVIEW_VALIDATED'&&!['PLAN_EXPIRED','CANCELLED','INPUT_EXPIRED'].includes(job.status);
  useEffect(()=>()=>abort.current?.abort(),[]);
  useEffect(()=>{setDetail(null);setError(null);},[job.job_id,plan?.digest]);
  const run=async(work:(signal:AbortSignal)=>Promise<void>)=>{abort.current?.abort();const c=new AbortController();abort.current=c;setBusy(true);setError(null);
    try{await work(c.signal);}catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:'계산하지 못했습니다.');}finally{if(!c.signal.aborted)setBusy(false);}};
  useEffect(()=>{
    if(guidedStep!==3||!rights||!plan||plan.status!=='PREVIEW_VALIDATED'||currentDetail||expiredDigest===plan.digest||job.status==='PLAN_EXPIRED')return;
    const c=new AbortController();setDetailBusy(true);setError(null);const digest=plan.digest;
    deliveryRequest<PlanDetail>({action:'plan_details',job_id:job.job_id},c.signal).then(value=>{if(!c.signal.aborted&&value.digest===digest)setDetail(value);}).catch(e=>{if(!c.signal.aborted)setError(e instanceof Error?e.message:'변경계획을 불러오지 못했습니다.');}).finally(()=>{if(!c.signal.aborted)setDetailBusy(false);});
    return()=>{c.abort();};
  },[guidedStep,rights,job.job_id,plan?.digest,plan?.status,currentDetail?.digest,expiredDigest,job.status]);
  useEffect(()=>{if(!currentDetail||job.status==='READY')return;const timer=setTimeout(()=>{setExpiredDigest(currentDetail.digest);setDetail(null);onJob({...job,status:'PLAN_EXPIRED'});deliveryRequest<DeliveryJob>({action:'get',job_id:job.job_id}).then(onJob).catch(()=>setError('계획이 만료되었습니다. 새 계획을 확인하세요.'));},Math.max(0,currentDetail.expires_at*1000-Date.now()));return()=>clearTimeout(timer);},[currentDetail?.digest,currentDetail?.expires_at,job.job_id,job.status,onJob]);
  const detailsView=currentDetail && <section aria-label="정확한 변경계획"><h3>바꾸려는 내용과 계산 결과</h3><p>사용자가 지정한 기준으로 계산한 변경안입니다. 업무상 정답인지 확인한 뒤 승인하세요. 선택을 바꾸면 다시 계산합니다.</p>
    <div className="delivery-plan-patches">{currentDetail.patches.map(p=>{const calculated=currentDetail.impact.find(i=>i.sheet===p.sheet&&i.cell===p.cell);return <article className="delivery-patch" key={p.sheet+p.cell} data-plan-cell={p.cell}><h4>{p.sheet} · {p.cell}</h4><dl><dt>원본의 값·수식</dt><dd>{display(p.before)}</dd><dt>승인하면 적용할 값·수식</dt><dd>{display(p.after)}</dd>{p.after.type==='formula'&&calculated&&<><dt>이 변경안의 예상 결과 · 계산 검증함</dt><dd data-impact-cell={p.cell}>{display(calculated.after)}</dd></>}</dl></article>;})}</div>
    <h4>함께 달라지는 계산 결과</h4><p>직접 바꾸는 셀 이외에 영향을 받는 수식입니다. 저장된 계산 캐시가 아니라 지원 엔진에서 다시 계산한 결과입니다.</p>
    <div className="delivery-plan-patches">{currentDetail.impact.filter(i=>!currentDetail.patches.some(p=>p.sheet===i.sheet&&p.cell===i.cell)).map(p=><article className="delivery-patch" key={p.sheet+p.cell} data-impact-cell={p.cell}><h5>{p.sheet} · {p.cell}</h5><dl><dt>변경 전 계산</dt><dd>{display(p.before)}</dd><dt>변경안 적용 후 계산</dt><dd>{display(p.after)}</dd></dl></article>)}</div>
  </section>;
  return <section className="delivery-plan delivery-step" aria-label="변경계획 계산">
    <div hidden={!scopeVisible} className="delivery-plan-review"><h3>변경 후 계산 영향 확인</h3><p>선택한 기준을 사본에 적용했을 때의 수식과 결과를 검사합니다. 원본은 바꾸지 않습니다.</p>
      <button type="button" className="button button--primary" disabled={busy||['APPROVED','RUNNING','CANCEL_REQUESTED','READY'].includes(job.status)} onClick={()=>run(async signal=>{setExpiredDigest(null);onJob(await deliveryRequest<DeliveryJob>({action:'prepare_plan',job_id:job.job_id,revision:job.revision,source_hash:job.source_hash},signal));})}>{plan?'변경 후 계산 영향 다시 확인':'변경 후 계산 영향 확인하기'}</button>
      {plan&&<div className="delivery-plan-summary" role="status"><h4>{validPlan?'수정 범위와 계산 검증 완료':job.status==='PLAN_EXPIRED'?'이전 계획 만료 · 다시 계산 필요':job.status==='CANCELLED'?'변경 취소됨 · 새 계획 필요':'계산 완료 · 기준 엔진 검증 필요'}</h4><p>변경 대상 {plan.patch_count}개 · 영향을 받는 수식 {plan.formula_impact_count}곳</p>
        <details><summary>검증 범위</summary><p>전체 수식 {plan.coverage.formula_count}개 계산 · 저장된 계산 캐시 사용 안 함</p><p>{plan.reference.status==='PASS'?`지원 범위의 합성 시험 ${plan.reference.case_count}개를 Excel 기준과 대조했습니다.`:'Excel 기준 대조를 완료하지 못해 수정 제공을 차단했습니다.'}</p></details>
        <p className="scope-price-status">제공 파일: 별도 수정본 XLSX · 변경내역 XLSX · 재검증 HTML<br/>가격: 일반 구매 준비 중 · 아직 확정하지 않았습니다.</p>
      </div>}
      {scopeVisible&&validPlan&&job.status!=='READY'&&<OrderStatus job={job} onRefresh={async()=>onJob(await deliveryRequest<DeliveryJob>({action:'get',job_id:job.job_id}))}/>}
      {guidedStep&&validPlan&&rights&&<button type="button" className="button button--primary" onClick={()=>onNextStep?.(3)}>3단계 · 변경 내용과 예상 결과 확인</button>}
    </div>
    {(!guidedStep||guidedStep===3)&&validPlan&&rights&&<>
      {detailBusy&&<p role="status">검증한 변경계획을 불러오고 있습니다…</p>}
      {(!guidedStep||(!currentDetail&&!detailBusy))&&<button type="button" className="button button--outline" disabled={busy} onClick={()=>run(async signal=>setDetail(await deliveryRequest<PlanDetail>({action:'plan_details',job_id:job.job_id},signal)))}>정확한 변경계획 보기</button>}
      {detailsView}
    </>}
    {(currentDetail||job.status==='READY')&&(!guidedStep||guidedStep>=3)&&(rights||job.status==='READY')&&<RepairDelivery job={job} detail={currentDetail??{digest:'',patches:[],impact:[],expires_at:job.expires_at}} onJob={onJob} mode={guidedStep===3?'approval':guidedStep===4?'delivery':'all'} onContinue={()=>onNextStep?.(4)}/>}
    {guidedStep===4&&currentDetail&&<details className="delivery-approved-copy"><summary>승인한 변경 내용 다시 보기</summary>{detailsView}</details>}
    {busy&&<p role="status">사본에서 계산 중입니다…</p>}{error&&<p role="alert">{error}</p>}
  </section>;
}
