import {useEffect,useRef,useState} from 'react';
import {deliveryRequest,type DeliveryJob} from './DeliveryWorkspace';
import type {PlanDetail} from './RepairPlanPreview';
import { revealElement } from '../lib/reveal';

const labels:Record<string,string>={REPAIRED_XLSX:'수정본 XLSX',CHANGES_XLSX:'변경내역 XLSX',VERIFICATION_HTML:'재검증 HTML'};
export function RepairDelivery({job,detail,onJob,mode='all',onContinue,onApprovalStart,onApproved}:{job:DeliveryJob;detail:PlanDetail;onJob:(job:DeliveryJob)=>void;mode?:'all'|'approval'|'delivery';onContinue?:()=>void;onApprovalStart?:(planDigest:string)=>number|null;onApproved?:(planDigest:string,token:number|null)=>void}){
 const [receiptVerified,setReceiptVerified]=useState(false);
 const headingRef=useRef<HTMLHeadingElement>(null);
 const modeRef=useRef(mode);
 const executionRevealPending=useRef<number|null>(null);
 const revealEpoch=useRef(0);
 const identity=`${job.job_id}:${detail.digest}:${mode}`;
 const previousIdentity=useRef(identity);
 if(previousIdentity.current!==identity){previousIdentity.current=identity;revealEpoch.current+=1;executionRevealPending.current=null;}
 const [readyReveal,setReadyReveal]=useState<number|null>(null);
 const [selected,setSelected]=useState<string[]>([]);
 const [ack,setAck]=useState(false);const [busy,setBusy]=useState(false);const [error,setError]=useState<string|null>(null);
 useEffect(()=>{setAck(false);setSelected([]);setReceiptVerified(false)},[detail.digest]);
 useEffect(()=>()=>{revealEpoch.current+=1;executionRevealPending.current=null;},[]);
 useEffect(()=>{const previous=modeRef.current;modeRef.current=mode;if(previous!==mode&&mode==='delivery')return revealElement(headingRef.current);},[mode]);
 useEffect(()=>{
  if(['CANCEL_REQUESTED','CANCELLED','PLAN_EXPIRED','INPUT_EXPIRED'].includes(job.status)){revealEpoch.current+=1;executionRevealPending.current=null;}
  if(job.status==='READY'&&executionRevealPending.current===revealEpoch.current){executionRevealPending.current=null;setReadyReveal(revealEpoch.current);}
 },[job.status]);
 useEffect(()=>{if(readyReveal!==null&&readyReveal===revealEpoch.current&&mode==='delivery'&&job.status==='READY')return revealElement(headingRef.current,'start',()=>readyReveal===revealEpoch.current);},[readyReveal,mode,job.status]);
 useEffect(()=>{
  if(!['RUNNING','CANCEL_REQUESTED'].includes(job.status))return;
  const c=new AbortController();let timer:ReturnType<typeof setTimeout>;
  const poll=async()=>{try{const next=await deliveryRequest<DeliveryJob>({action:'get',job_id:job.job_id},c.signal);onJob(next);}catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:'최신 상태를 확인하지 못했습니다.');}finally{if(!c.signal.aborted)timer=setTimeout(poll,1200);}};
  timer=setTimeout(poll,600);return()=>{c.abort();clearTimeout(timer);};
 },[job.job_id,job.status,onJob]);
 const run=async(work:()=>Promise<void>)=>{setBusy(true);setError(null);try{await work();}catch(e){setError(e instanceof Error?e.message:'작업을 완료하지 못했습니다.');try{onJob(await deliveryRequest<DeliveryJob>({action:'get',job_id:job.job_id}));}catch{/* Keep the original actionable error. */}}finally{setBusy(false);}};
 const active=['RUNNING','CANCEL_REQUESTED'].includes(job.status);
 const download=(kind:string)=>run(async()=>{
  const file=await deliveryRequest<{filename:string;mime:string;file_base64:string}>({action:'download',job_id:job.job_id,kind});
  const data=Uint8Array.from(atob(file.file_base64),c=>c.charCodeAt(0));const url=URL.createObjectURL(new Blob([data],{type:file.mime}));
  const link=document.createElement('a');link.href=url;link.download=file.filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 });
 const approvalOnly=mode==='approval';
 return <section className="delivery-execution delivery-step" aria-label="변경 승인과 납품"><h3 ref={headingRef} tabIndex={-1}>{approvalOnly?'정확한 변경 승인':mode==='delivery'?'승인한 결과 받기':job.status==='READY'?'수정 패키지 수령':'변경 승인과 납품'}</h3>
  {job.status!=='READY'&&mode!=='delivery'&&<p>위 셀의 변경과 계산 영향을 승인하면 원본과 분리된 사본을 만듭니다.</p>}
  {job.status!=='READY'&&mode!=='delivery'&&<details className="delivery-technical"><summary>함께 적용할 계산 정보 확인</summary><p>계획에 포함된 수식 {detail.technical_changes?.filter(c=>c.kind==='FORMULA_CACHE').length??0}개의 계산 캐시를 갱신하고, Excel에서 다시 계산하도록 설정합니다. 필요한 시트 범위 갱신도 계획에 포함됩니다.</p><p>비대상 셀의 업무 값·수식·서식은 보존 여부를 별도로 검사합니다.</p></details>}
  {approvalOnly && (job.approval_status==='APPROVED'||job.status==='READY') ? <div role="status"><p>현재 변경계획 승인 완료 · 결제나 앞 단계의 기준 확인과 별도로 기록했습니다.</p><button type="button" className="button button--primary" onClick={onContinue}>4단계 · 승인한 결과 받기</button>{job.status==='APPROVED'&&<button type="button" className="button button--ghost" disabled={busy} onClick={()=>run(async()=>onJob(await deliveryRequest<DeliveryJob>({action:'cancel',job_id:job.job_id})))}>승인 취소하고 범위 다시 확인</button>}</div>
  : job.status==='READY'&&job.delivery ? <div className="delivery-ready" role="status"><h4>승인한 {job.delivery.patch_count}개 변경의 세 파일이 준비되었습니다</h4><p>원본 보존·승인 범위·실제 재계산·파일 일치를 확인했습니다. 남은 위험과 검증 범위는 재검증 HTML에서 확인하세요.</p>
   <div className="delivery-downloads">{Object.keys(job.delivery.files).map(kind=><button key={kind} type="button" className="button button--outline" disabled={busy} onClick={()=>download(kind)}>{labels[kind]??kind} 받기</button>)}</div><p>보관 만료: {new Date(job.delivery.expires_at*1000).toLocaleString('ko-KR')} · 이 작업의 파일은 다시 결제하지 않고 받을 수 있습니다.</p></div>
  : active ? <div role="status"><h4>{job.status==='CANCEL_REQUESTED'?'취소 요청됨 · 실행 종료와 임시 파일 정리 중':'승인한 사본을 만들고 검증 중'}</h4><p>필수 세 파일의 검증이 끝난 뒤 다운로드가 열립니다.</p><button type="button" className="button button--outline" disabled={job.status==='CANCEL_REQUESTED'} onClick={()=>run(async()=>onJob(await deliveryRequest<DeliveryJob>({action:'cancel',job_id:job.job_id})))}>실행 취소</button></div>
  : job.status==='CANCELLED' ? <p role="status">취소 완료 · 수정본을 게시하지 않았습니다. 새 계획을 계산하면 다시 시작할 수 있습니다.</p>
  : <>
   {mode!=='delivery' && <details className="delivery-reselection"><summary>일부 대상만 다시 선택하거나 전체 변경 거부</summary><p>다시 선택하면 전체 계산 영향을 새로 확인하고 기존 승인은 취소됩니다.</p>{detail.patches.map(p=><label className="delivery-check" key={p.candidate_id}><input type="checkbox" aria-label={`${p.sheet} ${p.cell} 다시 선택`} checked={selected.includes(p.candidate_id)} onChange={e=>setSelected(old=>e.target.checked?[...old,p.candidate_id]:old.filter(id=>id!==p.candidate_id))}/>{p.sheet} · {p.cell}</label>)}<button type="button" className="button button--outline" disabled={busy||selected.length===0} onClick={()=>run(async()=>onJob(await deliveryRequest<DeliveryJob>({action:'reselect_plan',job_id:job.job_id,revision:job.revision,plan_digest:detail.digest,candidate_ids:selected})))}>선택한 대상만 새 계획 계산</button><button type="button" className="button button--ghost" disabled={busy} onClick={()=>run(async()=>onJob(await deliveryRequest<DeliveryJob>({action:'cancel',job_id:job.job_id})))}>전체 변경 거부·취소</button></details>}
   {job.status==='QUARANTINED' &&<p role="alert">검증을 완료하지 못해 파일을 격리했습니다. 다운로드할 수 없습니다. 같은 승인 범위의 재시도에는 추가 결제가 없습니다.</p>}
   {job.approval_status!=='APPROVED' ? mode==='delivery' ? <p>3단계에서 정확한 변경을 먼저 승인하세요.</p> : <><label className="delivery-check"><input type="checkbox" checked={ack} disabled={busy||!job.repair_execution_available} onChange={e=>setAck(e.target.checked)}/>위 {detail.patches.length}개 셀의 정확한 전후 변경과 계산 영향을 확인하고, 별도 사본에 적용하는 것을 승인합니다.</label>
    <button type="button" className="button button--primary" disabled={!ack||busy||!job.repair_execution_available} onClick={()=>run(async()=>{const approvalToken=onApprovalStart?.(detail.digest)??null;const approved=await deliveryRequest<DeliveryJob>({action:'approve_plan',job_id:job.job_id,revision:job.revision,plan_digest:detail.digest,candidate_ids:detail.patches.map(p=>p.candidate_id),acknowledge_exact_changes:true});if(approved.approval_status==='APPROVED'||approved.status==='READY')onApproved?.(detail.digest,approvalToken);onJob(approved);})}>이 변경계획 승인</button></>
    : <><p>현재 변경계획 승인 완료 · 결제나 앞 단계의 기준 확인과 별도로 기록했습니다.</p><button type="button" className="button button--primary" disabled={busy} onClick={()=>run(async()=>{executionRevealPending.current=revealEpoch.current;onJob({...job,status:'RUNNING'});const next=await deliveryRequest<DeliveryJob>({action:'execute',job_id:job.job_id});onJob(next);})}>{job.status==='QUARANTINED'?'같은 승인 범위 다시 실행':'승인한 사본 만들기'}</button></>}
   {!job.repair_execution_available&&<p>파일 호환성 또는 수정 권리 검증이 완료되어야 실행할 수 있습니다.</p>}
  </>}
  {job.approval_receipt&&<details className="delivery-technical"><summary>승인 기록과 원본 연결 확인</summary><p>원본 SHA-256: <code>{job.approval_receipt.payload.source_hash}</code></p><p>변경계획 SHA-256: <code>{job.approval_receipt.payload.plan_digest}</code></p><button type="button" className="button button--outline" disabled={busy} onClick={()=>run(async()=>{const proof=await deliveryRequest<{signature_valid:boolean}>({action:'verify_approval_receipt',job_id:job.job_id});setReceiptVerified(proof.signature_valid)})}>승인 기록 서버 검증</button>{receiptVerified&&<p role="status">서버 서명이 원본·변경계획과 일치합니다. 이 기록은 새 자료의 실행 권리가 아닙니다.</p>}</details>}
  {error&&<p role="alert">{error}</p>}
 </section>;
}
