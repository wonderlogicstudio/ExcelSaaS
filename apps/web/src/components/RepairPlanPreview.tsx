import { useEffect, useRef, useState } from 'react';
import { RepairDelivery } from './RepairDelivery';
import { OrderStatus } from './OrderStatus';
import { deliveryRequest, type DeliveryJob } from './DeliveryWorkspace';
import type { CoreStep } from './CoreFlowTabs';
import { revealElement } from '../lib/reveal';
import { ProposalExample } from './ProposalExample';
import { intentVerdict, type RepairIntent } from '../lib/repairProposals';

export type PlanDetail = { digest:string; patches:{candidate_id:string;sheet:string;cell:string;profile_version?:string;change_kind?:string;before:{type:string;value:unknown};after:{type:string;value:unknown}}[];
  impact:{sheet:string;cell:string;before:{type:string;value:unknown};after:{type:string;value:unknown}}[]; expires_at:number; technical_changes?:{kind:string}[] };
function display(cell:{type:string;value:unknown}) {
  if(cell.type==='blank')return '빈 셀'; if(cell.type==='text')return `문자 “${String(cell.value)}”`; if(cell.type==='formula')return String(cell.value);
  if(cell.type==='number')return `숫자 ${Number(cell.value).toLocaleString('ko-KR',{maximumFractionDigits:15})}`; return String(cell.value);
}
function patchKindLabel(p:{profile_version?:string;change_kind?:string;after:{type:string}}) {
  const kind = p.profile_version ?? p.change_kind;
  if (kind === 'RP01_NUMERIC_TEXT_FIELD_V1' || p.change_kind === 'TYPE_NORMALIZATION') return '숫자 텍스트 정리';
  if (kind === 'RP03_MONTHLY_SHEET_FORMULA_REPLACEMENT_V1' || p.change_kind === 'MONTHLY_FORMULA_REPLACEMENT') return '월별 수식 검증';
  return '빈 셀 수식 복원';
}
export function RepairPlanPreview({ job, onJob, guidedStep, onNextStep, intent, onIntentCheck, externalBusy=false, planRevealToken=0 }: { job:DeliveryJob; onJob:(job:DeliveryJob)=>void; guidedStep?:CoreStep; onNextStep?:(step:CoreStep)=>void; intent?:RepairIntent; onIntentCheck?:(satisfied:boolean)=>void; externalBusy?:boolean; planRevealToken?:number }) {
  const [busy,setBusy]=useState(false), [error,setError]=useState<string|null>(null), [detail,setDetail]=useState<PlanDetail|null>(null);
  const [reviewedDigest,setReviewedDigest]=useState<string|null>(null);
  const [approvalAdvanceDigest,setApprovalAdvanceDigest]=useState<string|null>(null);
  const approvalRequestSeq=useRef(0);
  const approvalNavigation=useRef<{digest:string;token:number;active:boolean}|null>(null);
  const guidedStepRef=useRef<CoreStep|undefined>(guidedStep);
  guidedStepRef.current=guidedStep;
  const [detailBusy,setDetailBusy]=useState(false); const [expiredDigest,setExpiredDigest]=useState<string|null>(null); const abort=useRef<AbortController|null>(null);
  const plan=job.plan_summary; const rights=!!(job.internal_rehearsal||job.entitlement_active); const currentDetail=detail?.digest===plan?.digest ? detail : null;
  const summaryHeading = useRef<HTMLHeadingElement>(null);
  const exampleSection = useRef<HTMLDivElement>(null);
  const exactHeading = useRef<HTMLHeadingElement>(null);
  const viewEpoch = useRef(0);
  const viewIdentity = `${job.job_id}:${guidedStep ?? 'all'}`;
  const previousView = useRef(viewIdentity);
  if (previousView.current !== viewIdentity) { previousView.current = viewIdentity; viewEpoch.current += 1; }
  const [resultReveal, setResultReveal] = useState<{epoch:number; kind:'plan'|'example'}|null>(null);
  const revealedResult = useRef<typeof resultReveal>(null);
  const lastPlanReveal = useRef(0);
  const beginResultReveal = (kind:'plan'|'example') => {
    const epoch = viewEpoch.current;
    return () => { if (viewEpoch.current === epoch) setResultReveal({epoch,kind}); };
  };
  const scopeVisible=!guidedStep||guidedStep===2;
  const validPlan=plan?.status==='PREVIEW_VALIDATED'&&!['PLAN_EXPIRED','CANCELLED','INPUT_EXPIRED'].includes(job.status);
  useEffect(()=>()=>{abort.current?.abort();viewEpoch.current += 1;},[]);
  useEffect(()=>{
    if (planRevealToken === lastPlanReveal.current) return;
    lastPlanReveal.current = planRevealToken;
    if (scopeVisible) setResultReveal({epoch:viewEpoch.current,kind:'plan'});
  },[planRevealToken,scopeVisible]);
  useEffect(()=>{
    if (!resultReveal || resultReveal.epoch !== viewEpoch.current || !scopeVisible || !plan || ['PLAN_EXPIRED','CANCELLED','INPUT_EXPIRED'].includes(job.status)) return;
    if ((resultReveal.kind === 'example' || rights) && !currentDetail) return;
    const target = rights && currentDetail ? exampleSection.current?.querySelector<HTMLHeadingElement>('h3') ?? null : summaryHeading.current;
    if (!target) return;
    target.tabIndex = -1;
    const cancel = revealElement(target, 'start', () => {
      if (resultReveal.epoch !== viewEpoch.current || revealedResult.current === resultReveal) return false;
      revealedResult.current = resultReveal; return true;
    });
    return cancel;
  },[resultReveal,scopeVisible,plan?.digest,rights,currentDetail?.digest,job.status]);
  useEffect(()=>{
    if (guidedStep === 3 && currentDetail && validPlan) return revealElement(exactHeading.current);
  },[guidedStep,currentDetail?.digest,validPlan]);
  useEffect(()=>{approvalNavigation.current=null;setDetail(null);setError(null);setReviewedDigest(null);setApprovalAdvanceDigest(null);},[job.job_id,plan?.digest]);
  useEffect(()=>{if(guidedStep!==3){approvalNavigation.current=null;setApprovalAdvanceDigest(null);}},[guidedStep]);
  const verdict=currentDetail?intentVerdict(intent,currentDetail,job.policy):null;
  const requestSatisfied=!intent?.enabled || verdict?.status==='matched';
  useEffect(()=>{if(guidedStep===3&&currentDetail)setReviewedDigest(currentDetail.digest);},[guidedStep,currentDetail?.digest]);
  useEffect(()=>{onIntentCheck?.(requestSatisfied && (!intent?.enabled || !!currentDetail));},[requestSatisfied,currentDetail?.digest,intent?.enabled,onIntentCheck]);
  useEffect(()=>{if(guidedStep===3&&currentDetail&&approvalAdvanceDigest===currentDetail.digest&&job.approval_status==='APPROVED'&&job.plan_summary?.digest===currentDetail.digest){approvalNavigation.current=null;setApprovalAdvanceDigest(null);onNextStep?.(4);}},[guidedStep,currentDetail?.digest,approvalAdvanceDigest,job.approval_status,job.plan_summary?.digest,onNextStep]);
  const patchGroups=currentDetail?[...new Map(currentDetail.patches.map(p=>[`${p.sheet}:${p.profile_version??p.change_kind??p.after.type}`,currentDetail.patches.filter(x=>x.sheet===p.sheet&&(x.profile_version??x.change_kind??x.after.type)===(p.profile_version??p.change_kind??p.after.type))])).values()]:[];
  const indirectImpacts=currentDetail?currentDetail.impact.filter(i=>!currentDetail.patches.some(p=>p.sheet===i.sheet&&p.cell===i.cell)):[];
  const impactGroups=[...new Map(indirectImpacts.map(i=>[i.sheet,indirectImpacts.filter(x=>x.sheet===i.sheet)])).values()];
  const singleMonthlyPatchGroup = patchGroups.length === 1 && patchGroups[0].some(p => (p.profile_version ?? p.change_kind) === 'RP03_MONTHLY_SHEET_FORMULA_REPLACEMENT_V1' || p.change_kind === 'MONTHLY_FORMULA_REPLACEMENT');
  const kindSummary=patchGroups.map(group=>`${patchKindLabel(group[0])} ${group.length}곳`).join(' · ');
  const beginApprovalNavigation=(planDigest:string)=>{
    if(guidedStepRef.current!==3)return null;
    const token=approvalRequestSeq.current+1;approvalRequestSeq.current=token;
    approvalNavigation.current={digest:planDigest,token,active:true};setApprovalAdvanceDigest(null);
    return token;
  };
  const completeApprovalNavigation=(planDigest:string,token:number|null)=>{
    const pending=approvalNavigation.current;
    if(token!==null&&pending?.active&&pending.digest===planDigest&&pending.token===token&&guidedStepRef.current===3)setApprovalAdvanceDigest(planDigest);
  };
  const run=async(work:(signal:AbortSignal)=>Promise<void>)=>{abort.current?.abort();const c=new AbortController();abort.current=c;setBusy(true);setError(null);
    try{await work(c.signal);}catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:'계산하지 못했습니다.');}finally{if(!c.signal.aborted)setBusy(false);}};
  useEffect(()=>{
    if((guidedStep!==2&&guidedStep!==3)||!rights||!plan||plan.status!=='PREVIEW_VALIDATED'||currentDetail||expiredDigest===plan.digest||['PLAN_EXPIRED','CANCELLED','INPUT_EXPIRED'].includes(job.status))return;
    const c=new AbortController();setDetailBusy(true);setError(null);const digest=plan.digest;
    deliveryRequest<PlanDetail>({action:'plan_details',job_id:job.job_id},c.signal).then(value=>{if(!c.signal.aborted&&value.digest===digest)setDetail(value);}).catch(e=>{if(!c.signal.aborted)setError(e instanceof Error?e.message:'변경계획을 불러오지 못했습니다.');}).finally(()=>{if(!c.signal.aborted)setDetailBusy(false);});
    return()=>{c.abort();};
  },[guidedStep,rights,job.job_id,plan?.digest,plan?.status,currentDetail?.digest,expiredDigest,job.status]);
  useEffect(()=>{if(!currentDetail||job.status==='READY')return;const timer=setTimeout(()=>{setExpiredDigest(currentDetail.digest);setDetail(null);onJob({...job,status:'PLAN_EXPIRED'});deliveryRequest<DeliveryJob>({action:'get',job_id:job.job_id}).then(onJob).catch(()=>setError('계획이 만료되었습니다. 새 계획을 확인하세요.'));},Math.max(0,currentDetail.expires_at*1000-Date.now()));return()=>clearTimeout(timer);},[currentDetail?.digest,currentDetail?.expires_at,job.job_id,job.status,onJob]);
  const detailsView=currentDetail && <section aria-label="정확한 변경계획"><h3 ref={guidedStep===3?exactHeading:undefined} tabIndex={-1}>바꾸려는 내용과 계산 결과</h3><p>사용자가 지정한 기준으로 계산한 변경안입니다. 업무상 정답인지 확인한 뒤 승인하세요. 선택을 바꾸면 다시 계산합니다.</p>
    <p className="delivery-plan-key-summary">직접 바뀌는 내용: {kindSummary || `${currentDetail.patches.length}곳`} · 함께 달라지는 계산 결과: {indirectImpacts.length}곳</p>
    {patchGroups.map(group=><details key={`${group[0].sheet}:${group[0].profile_version??group[0].change_kind??group[0].after.type}`} className="delivery-plan-group" open={singleMonthlyPatchGroup}><summary>{group[0].sheet} · {patchKindLabel(group[0])} {group.length}곳</summary><div className="delivery-plan-patches">{group.map(p=>{const calculated=currentDetail.impact.find(i=>i.sheet===p.sheet&&i.cell===p.cell);return <article className="delivery-patch" key={p.sheet+p.cell} data-plan-cell={p.cell}><h4>{p.sheet} · {p.cell}</h4><dl><dt>원본의 값·수식</dt><dd>{display(p.before)}</dd><dt>승인하면 적용할 값·수식</dt><dd>{display(p.after)}</dd>{p.after.type==='formula'&&calculated&&<><dt>이 변경안의 예상 결과 · 계산 검증함</dt><dd data-impact-cell={p.cell}>{display(calculated.after)}</dd></>}</dl></article>;})}</div></details>)}
    <h4>함께 달라지는 계산 결과</h4><p>직접 바꾸는 셀 이외에 영향을 받는 수식입니다. 저장된 계산 캐시가 아니라 지원 엔진에서 다시 계산한 결과입니다.</p>
    {impactGroups.length ? impactGroups.map(group=><details key={group[0].sheet} className="delivery-plan-group"><summary>{group[0].sheet} · 계산 영향 {group.length}곳</summary><div className="delivery-plan-patches">{group.map(p=><article className="delivery-patch" key={p.sheet+p.cell} data-impact-cell={p.cell}><h5>{p.sheet} · {p.cell}</h5><dl><dt>변경 전 계산</dt><dd>{display(p.before)}</dd><dt>변경안 적용 후 계산</dt><dd>{display(p.after)}</dd></dl></article>)}</div></details>) : <p>직접 바꾸는 셀 밖의 추가 계산 영향은 없습니다.</p>}
  </section>;
  return <section className="delivery-plan delivery-step" aria-label="변경계획 계산">
    <div hidden={!scopeVisible} className="delivery-plan-review"><h3>변경 후 계산 영향 확인</h3><p>선택한 기준을 사본에 적용했을 때의 수식과 결과를 검사합니다. 원본은 바꾸지 않습니다.</p>
      <button type="button" className="button button--primary" disabled={busy||externalBusy||['APPROVED','RUNNING','CANCEL_REQUESTED','READY'].includes(job.status)} onClick={()=>{const reveal=beginResultReveal('plan');void run(async signal=>{setExpiredDigest(null);const next=await deliveryRequest<DeliveryJob>({action:'prepare_plan',job_id:job.job_id,revision:job.revision,source_hash:job.source_hash},signal);if(!signal.aborted){onJob(next);reveal();}});}}>{plan?'변경 후 계산 영향 다시 확인':'변경 후 계산 영향 확인하기'}</button>
      {plan&&<div className="delivery-plan-summary" role="status"><h4 ref={summaryHeading} tabIndex={-1}>{validPlan?'수정 범위와 계산 검증 완료':job.status==='PLAN_EXPIRED'?'이전 계획 만료 · 다시 계산 필요':job.status==='CANCELLED'?'변경 취소됨 · 새 계획 필요':'계산 완료 · 기준 엔진 검증 필요'}</h4><p>변경 대상 {plan.patch_count}개 · 영향을 받는 수식 {plan.formula_impact_count}곳</p>
        <details><summary>검증 범위</summary><p>전체 수식 {plan.coverage.formula_count}개 계산 · 저장된 계산 캐시 사용 안 함</p><p>{plan.reference.status==='PASS'?`지원 범위의 합성 시험 ${plan.reference.case_count}개를 Excel 기준과 대조했습니다.`:'Excel 기준 대조를 완료하지 못해 수정 제공을 차단했습니다.'}</p></details>
        <p className="scope-price-status">제공 파일: 별도 수정본 XLSX · 변경내역 XLSX · 재검증 HTML<br/>가격: 일반 구매 준비 중 · 아직 확정하지 않았습니다.</p>
      </div>}
      {scopeVisible&&validPlan&&job.status!=='READY'&&<OrderStatus proposalPreview job={job} onActionStart={()=>beginResultReveal('example')} onRefresh={async()=>onJob(await deliveryRequest<DeliveryJob>({action:'get',job_id:job.job_id}))}/>}
    </div>
    {validPlan&&rights&&currentDetail&&(!guidedStep||guidedStep===2||guidedStep===3)&&<div ref={exampleSection}><ProposalExample detail={currentDetail} job={job} intent={intent}/></div>}
      {guidedStep===2&&validPlan&&rights&&currentDetail&&requestSatisfied&&<button type="button" className="button button--primary" onClick={()=>onNextStep?.(3)}>3단계 · 변경 내용과 예상 결과 확인</button>}
    {(!guidedStep||guidedStep===2||guidedStep===3)&&validPlan&&rights&&<>
      {detailBusy&&<p role="status">검증한 변경계획을 불러오고 있습니다…</p>}
      {(!guidedStep||(!currentDetail&&!detailBusy))&&<button type="button" className="button button--outline" disabled={busy||externalBusy} onClick={()=>run(async signal=>setDetail(await deliveryRequest<PlanDetail>({action:'plan_details',job_id:job.job_id},signal)))}>정확한 변경계획 보기</button>}
      {guidedStep===3 && currentDetail && <div className="proposal-exact">{detailsView}</div>}
      {!guidedStep && detailsView}
    </>}
    {(currentDetail||job.status==='READY')&&(!guidedStep||guidedStep>=3)&&(rights||job.status==='READY')&&requestSatisfied&&(!guidedStep||guidedStep===3||guidedStep===4||reviewedDigest===currentDetail?.digest||job.status==='READY')&&<RepairDelivery job={job} detail={currentDetail??{digest:'',patches:[],impact:[],expires_at:job.expires_at}} onJob={onJob} mode={guidedStep===3?'approval':guidedStep===4?'delivery':'all'} onContinue={()=>onNextStep?.(4)} onApprovalStart={beginApprovalNavigation} onApproved={completeApprovalNavigation}/>}
    {guidedStep===4&&currentDetail&&<details className="delivery-approved-copy"><summary>승인한 변경 내용 다시 보기</summary>{detailsView}</details>}
    {busy&&<p role="status">사본에서 계산 중입니다…</p>}{error&&<p role="alert">{error}</p>}
  </section>;
}
