import {useEffect,useRef,useState} from 'react';
import {deliveryRequest,type DeliveryJob} from './DeliveryWorkspace';

export type PlanDetail={digest:string;patches:{sheet:string;cell:string;before:{type:string;value:unknown};after:{type:string;value:unknown}}[];
  impact:{sheet:string;cell:string;before:{type:string;value:unknown};after:{type:string;value:unknown}}[];expires_at:number};
function display(cell:{type:string;value:unknown}){
  if(cell.type==='blank')return '빈 셀';
  if(cell.type==='text')return `문자 “${String(cell.value)}”`;
  if(cell.type==='formula')return String(cell.value);
  if(cell.type==='number')return `숫자 ${Number(cell.value).toLocaleString('ko-KR',{maximumFractionDigits:15})}`;
  return String(cell.value);
}
export function RepairPlanPreview({job,onJob}:{job:DeliveryJob;onJob:(job:DeliveryJob)=>void}){
 const [busy,setBusy]=useState(false);const [error,setError]=useState<string|null>(null);const [detail,setDetail]=useState<PlanDetail|null>(null);
 const abort=useRef<AbortController|null>(null);
 useEffect(()=>()=>abort.current?.abort(),[]);
 useEffect(()=>setDetail(null),[job.plan_summary?.digest]);
 const run=async(work:(signal:AbortSignal)=>Promise<void>)=>{abort.current?.abort();const c=new AbortController();abort.current=c;setBusy(true);setError(null);
   try{await work(c.signal);}catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:'계산하지 못했습니다.');}finally{if(!c.signal.aborted)setBusy(false);}};
 const plan=job.plan_summary;
 return <section className="delivery-plan delivery-step" aria-label="변경계획 계산"><h3>4. 변경계획 계산</h3>
  <p>선택한 변경을 사본에서 함께 계산해 전체 수식과 영향을 확인합니다. 아직 원본을 수정하거나 변경을 승인하지 않습니다.</p>
  <button type="button" className="button button--primary" disabled={busy} onClick={()=>run(async signal=>{
    onJob(await deliveryRequest<DeliveryJob>({action:'prepare_plan',job_id:job.job_id,revision:job.revision,source_hash:job.source_hash},signal));
  })}>{plan?'변경계획 다시 계산':'선택한 변경계획 계산'}</button>
  {plan&&<div className="delivery-plan-summary" role="status"><h4>{plan.status==='PREVIEW_VALIDATED'?'변경계획 계산 검증 완료':'계산 완료 · 기준 엔진 검증 필요'}</h4>
   <p>선택한 변경 {plan.patch_count}건 · 수식 계산 영향 {plan.formula_impact_count}곳</p><p>전체 수식 {plan.coverage.formula_count}개 계산 · 저장된 계산 캐시 사용 안 함</p>
   <p>{plan.reference.status==='PASS'?`지원 범위의 합성 시험 ${plan.reference.case_count}개를 Excel 기준과 대조했습니다.`:'Excel 기준 대조를 완료하지 못해 수정 제공을 차단했습니다.'}</p>
   <p>파일 보존·납품과 구매 절차의 검증이 남아 있습니다. 현재 구매할 수 없습니다.</p>
   {job.internal_rehearsal&&<><p className="delivery-beta-note">내부 합성 검증권 · 실제 결제 또는 고객 구매 권리가 아닙니다.</p>
    <button type="button" className="button button--outline" disabled={busy} onClick={()=>run(async signal=>setDetail(await deliveryRequest<PlanDetail>({action:'plan_details',job_id:job.job_id},signal)))}>정확한 변경계획 보기</button></>}
  </div>}
  {detail&&<section aria-label="정확한 변경계획"><h4>승인 전 확인할 정확한 변경</h4><p>이 미리보기는 변경 승인이 아닙니다. 선택을 바꾸면 전체 영향을 다시 계산합니다.</p>
   <div className="delivery-plan-patches">{detail.patches.map(p=>{
    const calculated=detail.impact.find(i=>i.sheet===p.sheet&&i.cell===p.cell);
    return <article className="delivery-patch" key={p.sheet+p.cell} data-plan-cell={p.cell}><h5>{p.sheet} · {p.cell}</h5><dl><dt>현재</dt><dd>{display(p.before)}</dd><dt>계획</dt><dd>{display(p.after)}</dd>
     {p.after.type==='formula'&&calculated&&<><dt>계획 적용 후 계산 결과</dt><dd data-impact-cell={p.cell}>{display(calculated.after)}</dd></>}
    </dl></article>;
   })}</div>
   <h4>연결된 수식의 결과 변화</h4><p>직접 바꾸는 셀은 위에서 확인하고, 그 변경의 영향을 받는 수식은 아래에서 확인하세요.</p>
   <div className="delivery-plan-patches">{detail.impact.filter(i=>!detail.patches.some(p=>p.sheet===i.sheet&&p.cell===i.cell)).map(p=><article className="delivery-patch" key={p.sheet+p.cell} data-impact-cell={p.cell}><h5>{p.sheet} · {p.cell}</h5><dl><dt>현재 계산</dt><dd>{display(p.before)}</dd><dt>계획 적용 후 계산</dt><dd>{display(p.after)}</dd></dl></article>)}</div>
  </section>}
  {busy&&<p role="status">사본에서 계산 중입니다…</p>}{error&&<p role="alert">{error}</p>}
 </section>;
}
