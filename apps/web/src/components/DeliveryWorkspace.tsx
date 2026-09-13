import type { CoreStep, DeliveryProgress } from './CoreFlowTabs';
import type { RepairDraft } from '../lib/repairReview';
import type { RepairIntent } from '../lib/repairProposals';
import { useEffect, useRef, useState } from 'react';
import {RepairPlanPreview} from './RepairPlanPreview';
import { resolveApiBaseUrl } from '../lib/api';

type Preflight = { status: string; eligible_count: number; reason_codes: string[]; purchase_enabled: boolean;
  targets: {sheet:string;cell:string;eligible:boolean;current_type:string;reason_codes:string[]}[] };
export type DeliveryJob = {synthetic_rehearsal_available?:boolean;approval_receipt?:{payload:{source_hash:string;plan_digest:string};signature:string}|null;order_id?:string|null;entitlement_active?:boolean;policy?:{profile:string;sheet:string;targets:string[];role?:string;anchor?:string;anchor_formula?:string;confirmed:boolean};job_id:string;revision:number;source_hash:string;status:string;expires_at:number;
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
  UNSUPPORTED_CELL_ORDER:'셀의 저장 순서가 비정상입니다. Excel에서 파일 복구 여부를 확인하세요. 현재는 수정하지 않습니다.',
  UNSUPPORTED_PACKAGE_PART:'차트·확장 기능 등 아직 보존을 검증하지 않은 파일 구조가 있습니다.',
  UNSUPPORTED_SHEET_STRUCTURE:'보호·병합·표 등 지원하지 않는 시트 구조가 있습니다.',
  UNSUPPORTED_FORMULA:'현재 범위에서 검증하지 않은 함수나 참조가 있습니다.',
  HIDDEN_SHEET:'숨김 시트를 포함한 파일은 현재 수정 범위에서 제외됩니다.',
  HIDDEN_STRUCTURE:'숨김 행 또는 열이 있는 구조는 현재 수정 범위에서 제외됩니다.',
  EXTERNAL_RELATIONSHIP:'외부 연결이 있는 파일은 수정하지 않습니다.',
};
const cellTypes:Record<string,string>={text:'문자',number:'숫자',formula:'수식',blank:'빈 셀',boolean:'논리값',error:'오류',date:'날짜'};
const apiBase=resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL,import.meta.env.PROD);
export class DeliveryRequestError extends Error{constructor(message:string,public code:string){super(message)}}
export async function deliveryRequest<T>(body:object,signal?:AbortSignal):Promise<T>{
  const response=await fetch(`${apiBase}/v1/delivery`,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json','X-WorkbookCare-CSRF':'1'},body:JSON.stringify(body),signal}).catch(error=>{if(signal?.aborted)throw error;throw new DeliveryRequestError('서버에 연결하지 못했습니다. 연결을 확인한 뒤 다시 시도하세요.','NETWORK_UNAVAILABLE')});
  const result=await response.json();
  if(!response.ok)throw new DeliveryRequestError(result.error?.message??'작업을 처리하지 못했습니다. 최신 상태를 다시 확인하세요.',result.error?.code??'REQUEST_FAILED');
  return result as T;
}
function fileBase64(file:File):Promise<string>{return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onerror=()=>reject(new Error('파일을 읽지 못했습니다.'));reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.readAsDataURL(file);});}

export function DeliveryWorkspace({ file, initialJob, reviewDraft, onSourceFixed, compactEntry = false, guidedStep, onProgress, onNextStep, intent, onRestartProposal }: {
  intent?: RepairIntent; onRestartProposal?: () => void; compactEntry?: boolean; file?: File; initialJob?: DeliveryJob; reviewDraft?: RepairDraft; onSourceFixed?: (fixed: boolean) => void;
  guidedStep?: CoreStep; onProgress?: (progress: DeliveryProgress) => void; onNextStep?: (step: CoreStep) => void;
}) {
  const [open, setOpen] = useState(Boolean(initialJob)); const [consent, setConsent] = useState(false); const [job, setJob] = useState<DeliveryJob | null>(initialJob ?? null);
  const [intentSatisfied, setIntentSatisfied] = useState(!intent?.enabled);
  useEffect(() => { setIntentSatisfied(!intent?.enabled); }, [job?.plan_summary?.digest, intent]);
  const [busy, setBusy] = useState(false); const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState(RP01); const [sheet, setSheet] = useState(''); const [targets, setTargets] = useState('');
  const [role, setRole] = useState(''); const [anchor, setAnchor] = useState(''); const [formula, setFormula] = useState(''); const [confirmed, setConfirmed] = useState(false);
  const [dirty, setDirty] = useState(false); const [maxBytes, setMaxBytes] = useState<number | null>(null); const abort = useRef<AbortController | null>(null);
  const heading = useRef<HTMLHeadingElement>(null); const scopeVisible = !guidedStep || guidedStep === 2;
  const expire = () => { onSourceFixed?.(false); setJob(null); setConsent(false); setConfirmed(false); setError('원본 보관이 만료되었습니다. 기존 주문에서 복구 또는 취소를 선택하고 같은 원본을 새로 업로드하세요.'); };
  useEffect(() => { if (!job) return; const timer = setTimeout(expire, Math.max(0, job.expires_at * 1000 - Date.now())); return () => clearTimeout(timer); }, [job?.job_id, job?.expires_at]);
  useEffect(() => () => abort.current?.abort(), []);
  useEffect(() => { const p = initialJob?.policy; if (p) { setProfile(p.profile); setSheet(p.sheet); setTargets(p.targets.join(', ')); setRole(p.role ?? ''); setAnchor(p.anchor ?? ''); setFormula(p.anchor_formula ?? ''); setConfirmed(p.confirmed); } }, [initialJob]);
  useEffect(() => {
    const usable = !!job && !dirty && job.plan_summary?.status === 'PREVIEW_VALIDATED' && !['PLAN_EXPIRED','CANCELLED','INPUT_EXPIRED'].includes(job.status);
    onProgress?.({ approvalAvailable: usable && intentSatisfied && !!(job?.internal_rehearsal || job?.entitlement_active || job?.status === 'READY'),
      deliveryAvailable: usable && intentSatisfied && !!(job?.approval_status === 'APPROVED' || job?.status === 'READY'), ready: job?.status === 'READY' });
  }, [job?.job_id, job?.status, job?.plan_summary?.digest, job?.plan_summary?.status, job?.internal_rehearsal, job?.entitlement_active, job?.approval_status, dirty, intentSatisfied, onProgress]);
  const run = async (work: (signal: AbortSignal) => Promise<void>) => {
    abort.current?.abort(); const controller = new AbortController(); abort.current = controller; setBusy(true); setError(null);
    try { await work(controller.signal); } catch (e) { if (!controller.signal.aborted) { if (e instanceof DeliveryRequestError && ['INPUT_EXPIRED','JOB_NOT_FOUND'].includes(e.code)) expire(); else setError(e instanceof Error ? e.message : '작업을 처리하지 못했습니다.'); } }
    finally { if (!controller.signal.aborted) setBusy(false); }
  };
  const edit = (change: () => void) => { change(); setConfirmed(false); setDirty(true); };
  const start = () => run(async signal => { const caps = await deliveryRequest<{ max_bytes: number }>({ action: 'capabilities' }, signal); setMaxBytes(caps.max_bytes); setOpen(true); requestAnimationFrame(() => heading.current?.focus()); });
  useEffect(() => { if (reviewDraft && !job) { setProfile(reviewDraft.profile); setSheet(reviewDraft.sheet); setTargets(reviewDraft.targets.join(', ')); setConfirmed(reviewDraft.confirmed === true); setRole(reviewDraft.role ?? ''); setAnchor(reviewDraft.anchor ?? ''); setFormula(reviewDraft.anchor_formula ?? ''); void start(); } }, [reviewDraft]);
  const upload = () => run(async signal => {
    if (!file) throw new Error('새 원본 파일을 선택하세요.'); if (!consent) throw new Error('업로드 권한과 검사 동의를 확인하세요.');
    if (maxBytes !== null && file.size > maxBytes) throw new Error(`수정 가능 여부 검사는 ${maxBytes / 1024 / 1024}MiB 이하 파일만 지원합니다.`);
    const next = await deliveryRequest<DeliveryJob>({ action: 'create_input', filename: file.name, file_base64: await fileBase64(file), consent: true, request_key: crypto.randomUUID() }, signal);
    if (signal.aborted) return;
    setJob(next); setSheet(reviewDraft?.sheet ?? next.sheets[0]?.name ?? ''); setDirty(false); onSourceFixed?.(true);
    if (reviewDraft?.proposal && confirmed) {
      const checked = await deliveryRequest<DeliveryJob>({ action: 'preflight', job_id: next.job_id, revision: next.revision, source_hash: next.source_hash,
        policy: { profile, sheet, targets: targets.split(/[\s,]+/).filter(Boolean), role, anchor, anchor_formula: formula, confirmed } }, signal);
      if (signal.aborted) return; setJob(checked);
      if (checked.preflight?.status === 'PRELIMINARY_ONLY') {
        const prepared = await deliveryRequest<DeliveryJob>({ action: 'prepare_plan', job_id: checked.job_id, revision: checked.revision, source_hash: checked.source_hash }, signal);
        if (!signal.aborted) setJob(prepared);
      }
    }
  });
  const check = () => run(async signal => {
    if (!job) return;
    const next = await deliveryRequest<DeliveryJob>({ action: 'preflight', job_id: job.job_id, revision: job.revision, source_hash: job.source_hash,
      policy: { profile, sheet, targets: targets.split(/[\s,]+/).filter(Boolean).map(x => x.toUpperCase()), role, anchor: anchor.toUpperCase(), anchor_formula: formula, confirmed } }, signal);
    setJob(next); setDirty(false);
  });
  if (!open) return <section className={`delivery-entry shell ${compactEntry ? 'delivery-manual' : ''}`}><h3>직접 지정이 필요한 경우</h3><p>수정 제안을 먼저 확인하세요. 목록에 없는 숫자 텍스트 또는 실제 빈 셀을 검사할 때 사용합니다. 셀과 수정 기준을 지정한 뒤 지원 여부를 확인합니다.</p><button className="button button--outline" type="button" disabled={busy} onClick={start}>확인할 셀 직접 지정하기</button>{error && <p role="alert">{error}</p>}</section>;
  return <section id="repair-preflight" className="delivery-workspace shell" aria-label="선택한 항목의 수정 가능 여부">
    <div hidden={!scopeVisible}>
      <h2 ref={heading} tabIndex={-1}>{reviewDraft?.proposal ? '선택한 제안의 실제 결과 확인' : '선택한 항목을 고칠 수 있는지 확인'}</h2>
      <p>원본 보존 조건과 수정 기준을 먼저 검사하고, 지원하는 범위에서 변경 후 계산 영향을 확인합니다.</p>
      <p className="delivery-beta-note">등록된 합성 파일 시험 · 일반 구매 준비 중 · 원본과 결과 15분 보관</p>
      {!job ? <div className="delivery-step"><h3>검사할 원본 확인</h3>{reviewDraft?.proposal && <p>선택한 {reviewDraft.sheet}의 {reviewDraft.targets.length}곳을 기존 규칙으로 검사합니다. 지원 조건을 통과하면 변경안을 계산합니다. 아직 수정하지 않습니다.</p>}<p>{file?.name ?? '고정된 합성 원본'} · {maxBytes === null ? '지원 한도 확인 중' : `최대 ${maxBytes / 1024 / 1024}MiB`}</p>
        <label className="delivery-check"><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/>업로드 권한이 있는 합성 파일이며 사전 검사와 임시 보관에 동의합니다.</label>
        <button className="button button--primary" type="button" disabled={busy || !consent} onClick={upload}>이 원본으로 수정 범위 확인</button></div>
        : <><p className="delivery-source-status">원본 확인 완료 · 변경하지 않음 · {job.sheets.length}개 시트</p>
          <details className="delivery-criteria" open={(!reviewDraft?.proposal && !job.preflight) || dirty}><summary>수정 기준과 대상</summary><fieldset className="delivery-step" disabled={busy || ['APPROVED','RUNNING','CANCEL_REQUESTED','READY'].includes(job.status)}><legend>어떤 셀을 어떤 기준으로 바꿀까요?</legend>
            <div className="delivery-form-grid"><label>수정 종류<select aria-label="수정 종류" value={profile} onChange={e => edit(() => setProfile(e.target.value))}><option value={RP01}>숫자 텍스트의 타입 정리</option><option value={RP02}>승인할 기준 수식으로 빈 셀 복원</option></select></label>
              <label>대상 시트<select aria-label="대상 시트" value={sheet} onChange={e => edit(() => setSheet(e.target.value))}>{job.sheets.map(s => <option key={s.name}>{s.name}</option>)}</select></label>
              <label>대상 셀<input aria-label="대상 셀" value={targets} onChange={e => edit(() => setTargets(e.target.value))} placeholder="예: B2, B3"/><small>각 셀을 쉼표로 구분하세요. 범위를 자동 확대하지 않습니다.</small></label>
              {profile === RP01 ? <label>이 숫자는 어떤 용도인가요?<select aria-label="이 숫자는 어떤 용도인가요?" value={role} onChange={e => edit(() => setRole(e.target.value))}><option value="">선택하세요</option><option value="AMOUNT">계산할 금액 · 매출·비용·정산액</option><option value="QUANTITY">계산할 개수 · 상품 수·인원</option><option value="ID">구분하는 번호 · 고객번호·계좌 (수정 불가)</option></select></label>
                : <><label>기준 셀<input aria-label="기준 셀" value={anchor} onChange={e => edit(() => setAnchor(e.target.value))} placeholder="예: F2"/></label><label>기준 셀의 현재 수식<input aria-label="기준 셀의 현재 수식" value={formula} onChange={e => edit(() => setFormula(e.target.value))} placeholder="1단계의 원본 비교 또는 Excel에서 기준 수식을 확인하세요"/></label></>}
            </div><label className="delivery-check"><input type="checkbox" checked={confirmed} onChange={e => { setConfirmed(e.target.checked); setDirty(true); }}/>{profile === RP01 ? '선택한 셀은 ID가 아닌 금액·수량 필드이며 지정한 숫자 해석을 적용합니다.' : '기준 수식을 확인했으며 선택한 빈 셀에도 같은 업무 규칙을 적용합니다.'}</label>
            <button className="button button--primary" type="button" disabled={busy || !targets || !confirmed} onClick={check}>이 기준으로 지원 여부 검사</button>
          </fieldset></details>
          {dirty && job.preflight && <p role="status">기준이 바뀌었습니다. 다시 검사하기 전에는 변경 승인으로 진행할 수 없습니다.</p>}
          {job.preflight && !dirty && !job.plan_summary && <section className="delivery-preflight-result" aria-label="지원 여부 검사 결과"><h3>지원 여부 검사 결과</h3><strong>{job.preflight.status === 'PRELIMINARY_ONLY' ? '셀 형식 확인 완료 · 계산 검증이 남았습니다' : '현재 범위는 수정할 수 없습니다'}</strong>
            <p>형식 조건 충족 {job.preflight.eligible_count}건</p><p>{job.preflight.status === 'PRELIMINARY_ONLY' ? '아래에서 변경 후 계산 영향을 검사하세요. 이 단계는 변경 승인이나 가격 확정이 아닙니다.' : '아래 이유를 확인하고 기준 또는 대상을 바꾸세요. 현재 범위로는 주문·변경 승인을 진행할 수 없습니다.'}</p>
            <ul>{[...new Set([...job.preflight.reason_codes,...job.preflight.targets.flatMap(t => t.reason_codes)])].map(code => <li key={code}>{reasons[code] ?? '지원 범위를 충족하지 않습니다. 직접 확인이 필요합니다.'}</li>)}</ul>
            <table className="delivery-targets"><caption>선택한 셀의 지원 여부</caption><thead><tr><th>위치</th><th>현재 타입</th><th>검사 결과</th></tr></thead><tbody>{job.preflight.targets.map(t => <tr key={t.sheet + t.cell}><td>{t.sheet} · {t.cell}</td><td>{cellTypes[t.current_type] ?? t.current_type}</td><td>{t.eligible ? '형식 조건 충족' : '지원 제외'}</td></tr>)}</tbody></table>
          </section>}
        </>}
    </div>
    {job?.status === 'PLAN_EXPIRED' && <p role="status">변경계획이 만료되었습니다. 2단계에서 다시 계산한 뒤 새로 승인하세요.</p>}
    {job?.preflight?.status === 'PRELIMINARY_ONLY' && !dirty && <RepairPlanPreview job={job} onJob={setJob} guidedStep={guidedStep} onNextStep={onNextStep} intent={intent} onIntentCheck={setIntentSatisfied}/>}
    {job && onRestartProposal && <button type="button" className="button button--ghost proposal-restart" disabled={busy || ['APPROVED','RUNNING','CANCEL_REQUESTED','READY'].includes(job.status)} onClick={() => run(async signal => {
      const next = await deliveryRequest<{status:string}>({action:'delete',job_id:job.job_id},signal);
      if (next.status === 'DELETED') { onSourceFixed?.(false); onRestartProposal(); }
    })}>다른 제안으로 다시 선택</button>}
    {job && <details className="delivery-job-tools"><summary>작업 상태·원본 관리</summary><div className="delivery-actions"><button className="button button--outline" type="button" disabled={busy} onClick={() => run(async signal => { setJob(await deliveryRequest<DeliveryJob>({ action:'get',job_id:job.job_id },signal)); })}>최신 작업 상태 확인</button><button className="button button--ghost" type="button" disabled={busy} onClick={() => run(async signal => { const next = await deliveryRequest<DeliveryJob | { status:'DELETED' }>({ action:'delete',job_id:job.job_id },signal); if(next.status === 'DELETED'){ onSourceFixed?.(false); setJob(null); setConsent(false); setConfirmed(false); } else setJob(next as DeliveryJob); })}>사전 검사 원본 삭제</button></div></details>}
    {busy && <p role="status">처리 중입니다…</p>}{error && <p role="alert">{error}</p>}
  </section>;
}
