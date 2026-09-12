import { useEffect, useRef, useState } from 'react';
import {OrderStatus} from './OrderStatus';
import {RepairPlanPreview} from './RepairPlanPreview';
import { resolveApiBaseUrl } from '../lib/api';

type Preflight = { status: string; eligible_count: number; reason_codes: string[]; purchase_enabled: boolean;
  targets: {sheet:string;cell:string;eligible:boolean;current_type:string;reason_codes:string[]}[] };
export type DeliveryJob = {order_id?:string|null;entitlement_active?:boolean;policy?:{profile:string;sheet:string;targets:string[];role?:string;anchor?:string;anchor_formula?:string;confirmed:boolean};job_id:string;revision:number;source_hash:string;status:string;expires_at:number;
  repair_execution_available?:boolean;approval_status?:string;delivery?:{delivery_id:string;patch_count:number;expires_at:number;files:Record<string,{bytes:number}>}|null;
  internal_rehearsal?:boolean;plan_summary?:{digest:string;status:string;patch_count:number;impact_count:number;formula_impact_count:number;coverage:{formula_count:number};reference:{status:string;case_count?:number}}|null;
  sheets:{name:string;cell_count:number}[];preflight:Preflight|null;purchase_enabled:boolean;source_unchanged:boolean};
const RP01='RP01_NUMERIC_TEXT_FIELD_V1';const RP02='RP02_APPROVED_FORMULA_RESTORE_V1';
const reasons:Record<string,string>={
  UNCONFIRMED_BUSINESS_INTENT:'필드의 업무 의미와 적용 대상을 확인해야 합니다.',
  UNCONFIRMED_ANCHOR:'기준 셀의 현재 수식과 같은 업무 규칙 적용 여부를 확인하세요.',
  INELIGIBLE_TARGETS:'선택한 셀 중 지원하지 않는 대상이 있습니다. 해당 셀을 제외하고 다시 검사하세요.',
  NO_ELIGIBLE_CHANGES:'현재 선택에서 형식 조건을 충족하는 변경 대상이 없습니다.',
  NOT_UNAMBIGUOUS_INTEGER_TEXT:'선행 0·단위·날짜·공백·소수·초과 정밀도 또는 숫자 텍스트가 아닌 셀입니다.',
  TARGET_NOT_TRUE_BLANK:'실제 빈 셀이 아닙니다. 빈 문자열·수식·값을 덮어쓰지 않습니다.',
  UNSUPPORTED_PACKAGE_PART:'차트·확장 기능 등 아직 보존을 검증하지 않은 파일 구조가 있습니다.',
  UNSUPPORTED_SHEET_STRUCTURE:'보호·병합·표 등 지원하지 않는 시트 구조가 있습니다.',
  UNSUPPORTED_FORMULA:'현재 범위에서 검증하지 않은 함수나 참조가 있습니다.',
  HIDDEN_SHEET:'숨김 시트를 포함한 파일은 현재 수정 범위에서 제외됩니다.',
  HIDDEN_STRUCTURE:'숨김 행 또는 열이 있는 구조는 현재 수정 범위에서 제외됩니다.',
  EXTERNAL_RELATIONSHIP:'외부 연결이 있는 파일은 수정하지 않습니다.',
};
const cellTypes:Record<string,string>={text:'문자',number:'숫자',formula:'수식',blank:'빈 셀',boolean:'논리값',error:'오류',date:'날짜'};
const apiBase=resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL,import.meta.env.PROD);
export async function deliveryRequest<T>(body:object,signal?:AbortSignal):Promise<T>{
  const response=await fetch(`${apiBase}/v1/delivery`,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json','X-WorkbookCare-CSRF':'1'},body:JSON.stringify(body),signal});
  const result=await response.json();
  if(!response.ok)throw new Error(result.error?.message??'작업을 처리하지 못했습니다. 최신 상태를 다시 확인하세요.');
  return result as T;
}
function fileBase64(file:File):Promise<string>{return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onerror=()=>reject(new Error('파일을 읽지 못했습니다.'));reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.readAsDataURL(file);});}

export function DeliveryWorkspace({file,initialJob}:{file?:File;initialJob?:DeliveryJob}){
  const [open,setOpen]=useState(Boolean(initialJob));const [consent,setConsent]=useState(false);const [job,setJob]=useState<DeliveryJob|null>(initialJob??null);
  const [busy,setBusy]=useState(false);const [error,setError]=useState<string|null>(null);
  const [profile,setProfile]=useState(RP01);const [sheet,setSheet]=useState('');const [targets,setTargets]=useState('');
  const [role,setRole]=useState('');const [anchor,setAnchor]=useState('');const [formula,setFormula]=useState('');const [confirmed,setConfirmed]=useState(false);
  const [dirty,setDirty]=useState(false);const [maxBytes,setMaxBytes]=useState<number|null>(null);const abort=useRef<AbortController|null>(null);
  const heading=useRef<HTMLHeadingElement>(null);
  useEffect(()=>()=>abort.current?.abort(),[]);
  useEffect(()=>{const p=initialJob?.policy;if(p){setProfile(p.profile);setSheet(p.sheet);setTargets(p.targets.join(', '));setRole(p.role??'');setAnchor(p.anchor??'');setFormula(p.anchor_formula??'');setConfirmed(p.confirmed)}},[initialJob]);
  const run=async(work:(signal:AbortSignal)=>Promise<void>)=>{
    abort.current?.abort();const controller=new AbortController();abort.current=controller;setBusy(true);setError(null);
    try{await work(controller.signal);}catch(e){if(!controller.signal.aborted)setError(e instanceof Error?e.message:'작업을 처리하지 못했습니다.');}
    finally{if(!controller.signal.aborted)setBusy(false);}
  };
  const edit=(change:()=>void)=>{change();setConfirmed(false);setDirty(true);};
  const start=()=>run(async signal=>{const limits=await deliveryRequest<{max_bytes:number}>({action:'capabilities'},signal);setMaxBytes(limits.max_bytes);setOpen(true);requestAnimationFrame(()=>heading.current?.focus());});
  const upload=()=>run(async signal=>{
    if(!file)throw new Error('새 원본 파일을 선택하세요.');
    if(!consent)throw new Error('업로드 권한과 검사 동의를 확인하세요.');
    if(maxBytes!==null&&file.size>maxBytes)throw new Error(`사전 검사는 ${maxBytes/1024/1024}MiB 이하 파일만 지원합니다.`);
    const next=await deliveryRequest<DeliveryJob>({action:'create_input',filename:file.name,file_base64:await fileBase64(file),consent:true,request_key:crypto.randomUUID()},signal);
    setJob(next);setSheet(next.sheets[0]?.name??'');setDirty(false);
  });
  const check=()=>run(async signal=>{
    if(!job)return;
    const next=await deliveryRequest<DeliveryJob>({action:'preflight',job_id:job.job_id,revision:job.revision,source_hash:job.source_hash,
      policy:{profile,sheet,targets:targets.split(/[\s,]+/).filter(Boolean).map(x=>x.toUpperCase()),role,anchor:anchor.toUpperCase(),anchor_formula:formula,confirmed}},signal);
    setJob(next);setDirty(false);
  });
  if(!open)return <section className="delivery-entry shell"><h3>수정할 범위를 먼저 확인하세요</h3><p>지원하는 변경 종류와 원본 조건을 확인하는 사전 검사입니다. 현재 결제와 파일 수정은 제공하지 않습니다.</p>
    <button className="button button--outline" type="button" disabled={busy} onClick={start}>수정 범위 사전 확인</button>{error&&<p role="alert">{error}</p>}</section>;
  return <section id="repair-preflight" className="delivery-workspace shell" aria-label="수정 범위 사전 확인">
    <h2 ref={heading} tabIndex={-1}>수정 범위 사전 확인</h2><p>원본을 고정하고, 직접 지정한 업무 기준과 셀만 확인합니다. 이 확인은 변경 승인이 아닙니다.</p>
    <p className="delivery-beta-note">합성 파일용 사전 검사 베타 · 실제 결제 없음. 별도 내부 검증권이 있는 합성 작업만 승인 후 사본을 만들 수 있습니다. 작업은 15분 뒤 만료되며 서버 재시작 시 사라질 수 있습니다.</p>
    {!job ? <div className="delivery-step"><h3>1. 원본 고정</h3><p>{file?.name??'고정된 합성 원본'} · {maxBytes===null?'지원 한도 확인 중':`최대 ${maxBytes/1024/1024}MiB`}</p>
      <label className="delivery-check"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>업로드 권한이 있는 합성 파일이며 사전 검사와 임시 보관에 동의합니다.</label>
      <button className="button button--primary" type="button" disabled={busy||!consent} onClick={upload}>원본 고정하고 계속</button></div>
      : <><p className="delivery-source-status">원본 고정 완료 · 변경하지 않음 · {job.sheets.length}개 시트</p>
        <fieldset className="delivery-step" disabled={busy||['APPROVED','RUNNING','CANCEL_REQUESTED','READY'].includes(job.status)}><legend>2. 수정 기준 확인</legend>
          <div className="delivery-form-grid"><label>수정 종류<select aria-label="수정 종류" value={profile} onChange={e=>edit(()=>setProfile(e.target.value))}><option value={RP01}>숫자 텍스트의 타입 정리</option><option value={RP02}>승인할 기준 수식으로 빈 셀 복원</option></select></label>
            <label>대상 시트<select aria-label="대상 시트" value={sheet} onChange={e=>edit(()=>setSheet(e.target.value))}>{job.sheets.map(s=><option key={s.name}>{s.name}</option>)}</select></label>
            <label>대상 셀<input aria-label="대상 셀" value={targets} onChange={e=>edit(()=>setTargets(e.target.value))} placeholder="예: B2, B3"/><small>각 셀을 쉼표로 구분하세요. 범위를 자동 확대하지 않습니다.</small></label>
            {profile===RP01 ? <label>필드 역할<select aria-label="필드 역할" value={role} onChange={e=>edit(()=>setRole(e.target.value))}><option value="">선택하세요</option><option value="AMOUNT">금액</option><option value="QUANTITY">수량</option><option value="ID">ID·계좌·식별자 (수정 불가)</option></select></label>
              : <><label>기준 셀<input aria-label="기준 셀" value={anchor} onChange={e=>edit(()=>setAnchor(e.target.value))} placeholder="예: F2"/></label><label>기준 셀의 현재 수식<input aria-label="기준 셀의 현재 수식" value={formula} onChange={e=>edit(()=>setFormula(e.target.value))} placeholder="Excel에서 기준 수식을 복사하세요"/></label></>}
          </div>
          <label className="delivery-check"><input type="checkbox" checked={confirmed} onChange={e=>{setConfirmed(e.target.checked);setDirty(true);}}/>{profile===RP01?'선택한 셀은 ID가 아닌 금액·수량 필드이며 지정한 숫자 해석을 적용합니다.':'기준 수식을 확인했으며 선택한 빈 셀에도 같은 업무 규칙을 적용합니다.'}</label>
          <button className="button button--primary" type="button" disabled={busy||!targets||!confirmed} onClick={check}>선택한 범위 사전 검사</button>
        </fieldset>
        {dirty&&job.preflight&&<p role="status">기준이 바뀌었습니다. 새 기준으로 다시 검사해야 합니다.</p>}
        {job.preflight&&!dirty&&<section className="delivery-preflight-result" aria-label="사전 검사 결과"><h3>3. 사전 검사 결과</h3>
          <strong>{job.preflight.status==='PRELIMINARY_ONLY'?'대상 형식 확인 · 추가 검증 필요':'선택한 범위의 수정 조건 미충족'}</strong>
          <p>형식 조건 충족 {job.preflight.eligible_count}건</p><p>{job.plan_summary?'아래에서 변경계획과 승인 단계를 확인하세요. 현재 일반 구매는 제공하지 않습니다.':'다음 단계에서 계산 영향을 확인할 수 있습니다. 아직 수정 가능 또는 견적 가능 상태가 아닙니다.'}</p>
          <ul>{[...new Set([...job.preflight.reason_codes,...job.preflight.targets.flatMap(t=>t.reason_codes)])].map(code=><li key={code}>{reasons[code]??'지원 범위를 충족하지 않습니다. 현재는 수동 확인이 필요합니다.'}</li>)}</ul>
          <table className="delivery-targets"><caption>선택한 셀의 실제 사전 검사</caption><thead><tr><th>위치</th><th>현재 타입</th><th>확인 결과</th></tr></thead><tbody>{job.preflight.targets.map(t=><tr key={t.sheet+t.cell}><td>{t.sheet} · {t.cell}</td><td>{cellTypes[t.current_type]??t.current_type}</td><td>{t.eligible?'형식 조건 충족':'지원 제외'}</td></tr>)}</tbody></table>
          <button className="button button--primary" type="button" disabled>견적·수정 실행 준비 중</button>
        </section>}
        {job.plan_summary&&!dirty&&<OrderStatus job={job} onRefresh={async()=>setJob(await deliveryRequest<DeliveryJob>({action:'get',job_id:job.job_id}))}/>}
        {job.preflight?.status==='PRELIMINARY_ONLY'&&!dirty&&<RepairPlanPreview job={job} onJob={setJob}/>}
        <div className="delivery-actions"><button className="button button--outline" type="button" disabled={busy} onClick={()=>run(async signal=>{setJob(await deliveryRequest<DeliveryJob>({action:'get',job_id:job.job_id},signal));})}>최신 작업 상태 확인</button>
          <button className="button button--ghost" type="button" disabled={busy} onClick={()=>run(async signal=>{const next=await deliveryRequest<DeliveryJob|{status:'DELETED'}>({action:'delete',job_id:job.job_id},signal);if(next.status==='DELETED'){setJob(null);setConsent(false);setConfirmed(false);}else{setJob(next as DeliveryJob);}})}>사전 검사 원본 삭제</button></div>
      </>}
    {busy&&<p role="status">처리 중입니다…</p>}{error&&<p role="alert">{error}</p>}
  </section>;
}
