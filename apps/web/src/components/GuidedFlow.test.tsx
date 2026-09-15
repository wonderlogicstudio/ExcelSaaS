import { useEffect, useState } from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CoreFlowTabs, initialDeliveryProgress, type CoreStep } from './CoreFlowTabs';
import { DeliveryWorkspace, type DeliveryJob } from './DeliveryWorkspace';
import { RepairPlanPreview, type PlanDetail } from './RepairPlanPreview';
const job:DeliveryJob={job_id:'synthetic',revision:3,status:'PREVIEW_VALIDATED',source_hash:'source',expires_at:Date.now()/1000+900,sheets:[{name:'Data',cell_count:5}],preflight:{status:'PRELIMINARY_ONLY',eligible_count:1,reason_codes:[],purchase_enabled:false,targets:[]},purchase_enabled:false,source_unchanged:true,entitlement_active:true,repair_execution_available:true,approval_status:'UNAPPROVED',plan_summary:{digest:'plan-a',status:'PREVIEW_VALIDATED',patch_count:1,impact_count:2,formula_impact_count:2,coverage:{formula_count:4},reference:{status:'PASS',case_count:36}}};
const detail:PlanDetail={digest:'plan-a',expires_at:Date.now()/1000+600,patches:[{candidate_id:'p1',sheet:'Data',cell:'F31',before:{type:'blank',value:null},after:{type:'formula',value:'=ROUND(C31*D31*(1-E31),0)'}}],impact:[{sheet:'Data',cell:'F31',before:{type:'number',value:0},after:{type:'number',value:5232}},{sheet:'Data',cell:'J130',before:{type:'number',value:932691},after:{type:'number',value:937923}}]};
const response=(value:unknown)=>({ok:true,status:200,json:async()=>value} as Response);
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.useRealTimers();});
describe('guided approval boundaries',()=>{
 it('locks later tabs and supports keyboard navigation only through completed prerequisites',()=>{
  function Harness(){const [step,setStep]=useState<CoreStep>(1);return <CoreFlowTabs active={step} diagnosisComplete progress={initialDeliveryProgress} onChange={setStep}/>;}
  render(<Harness/>);const tabs=screen.getAllByRole('tab');expect(tabs[2]).toBeDisabled();expect(tabs[3]).toBeDisabled();
  fireEvent.keyDown(tabs[0],{key:'End'});expect(tabs[1]).toHaveAttribute('aria-selected','true');expect(tabs[1]).toHaveFocus();
  fireEvent.keyDown(tabs[1],{key:'ArrowRight'});expect(tabs[0]).toHaveAttribute('aria-selected','true');
 });
 it.each([{entitlement_active:false},{plan_summary:{...job.plan_summary!,status:'PREVIEW_UNVERIFIED'}},{status:'PLAN_EXPIRED'},{status:'CANCELLED'}])('does not unlock approval with incomplete or expired job %j',override=>{
  const progress=vi.fn();render(<DeliveryWorkspace initialJob={{...job,...override}} guidedStep={2} onProgress={progress}/>);
  expect(progress).toHaveBeenLastCalledWith({approvalAvailable:false,deliveryAvailable:false,ready:false});
 });
 it('locks approval again when business criteria change and keeps confirmation unchecked',()=>{
  const progress=vi.fn();render(<DeliveryWorkspace initialJob={job} guidedStep={2} onProgress={progress}/>);
  expect(progress).toHaveBeenLastCalledWith({approvalAvailable:true,deliveryAvailable:false,ready:false});
  fireEvent.click(screen.getByText('수정 기준과 대상'));
  fireEvent.change(screen.getByLabelText('대상 셀'),{target:{value:'B2'}});
  expect(progress).toHaveBeenLastCalledWith({approvalAvailable:false,deliveryAvailable:false,ready:false});
  expect(screen.getByRole('checkbox',{name:/선택한 셀은 ID가 아닌/})).not.toBeChecked();
  expect(screen.queryByRole('button',{name:'3단계 · 변경 내용과 예상 결과 확인'})).not.toBeInTheDocument();
 });
 it('shows calculated expected values and records exact approval without automatically executing',async()=>{
  const actions:Record<string,unknown>[]=[];
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{const action=JSON.parse(init.body);actions.push(action);return response(action.action==='plan_details'?detail:{...job,status:'APPROVED',approval_status:'APPROVED'});}));
  function Harness(){
   const [current,setCurrent]=useState(job),[step,setStep]=useState<CoreStep>(3),[pending,setPending]=useState<CoreStep|null>(null);
   const maxStep:CoreStep=current.approval_status==='APPROVED'?4:3;
   useEffect(()=>{if(pending&&pending<=maxStep){setStep(pending);setPending(null);}},[pending,maxStep]);
   const guarded=(next:CoreStep)=>{if(next<=maxStep){setPending(null);setStep(next);}else setPending(next);};
   return <><button type="button" onClick={()=>guarded(3)}>3단계로 이동</button><RepairPlanPreview job={current} onJob={setCurrent} guidedStep={step} onNextStep={guarded}/><output aria-label="현재 단계">{step}</output></>;
  }
  render(<Harness/>);await screen.findByText('=ROUND(C31*D31*(1-E31),0)');
  expect(screen.queryByRole('button',{name:'전체 1곳의 정확한 변경·수식 확인'})).not.toBeInTheDocument();
  expect(screen.getByText('숫자 5,232')).toBeVisible();
  expect(screen.getByText('숫자 937,923')).toBeVisible();
  expect(screen.getByText('=ROUND(C31*D31*(1-E31),0)')).toBeVisible();
  expect(screen.getByRole('button',{name:'이 변경계획 승인'})).toBeDisabled();
  fireEvent.click(screen.getByRole('checkbox',{name:/위 1개 셀의 정확한/}));
  await waitFor(()=>expect(screen.getByRole('button',{name:'이 변경계획 승인'})).toBeEnabled());
  fireEvent.click(screen.getByRole('button',{name:'이 변경계획 승인'}));
  await waitFor(()=>expect(screen.getByRole('button',{name:'승인한 사본 만들기'})).toBeVisible());
  expect(screen.getByLabelText('현재 단계')).toHaveTextContent('4');
  expect(actions.map(a=>a.action)).toEqual(['plan_details','approve_plan']);
  expect(actions[1]).toMatchObject({plan_digest:'plan-a',candidate_ids:['p1'],acknowledge_exact_changes:true});
  fireEvent.click(screen.getByRole('button',{name:'3단계로 이동'}));
  await waitFor(()=>expect(screen.getByLabelText('현재 단계')).toHaveTextContent('3'));
  expect(screen.getByRole('button',{name:'승인 취소하고 범위 다시 확인'})).toBeVisible();
  expect(screen.getByRole('button',{name:'4단계 · 승인한 결과 받기'})).toBeVisible();
  expect(screen.queryByRole('button',{name:'승인한 사본 만들기'})).not.toBeInTheDocument();
  expect(actions.some(a=>a.action==='execute')).toBe(false);
 });
 it('keeps stage 2 when the user leaves approval before the approval response',async()=>{
  const actions:Record<string,unknown>[]=[];let finish!:(v:Response)=>void;const approved=new Promise<Response>(resolve=>{finish=resolve;});
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{const action=JSON.parse(init.body);actions.push(action);return action.action==='plan_details'?response(detail):action.action==='approve_plan'?approved:response(job);}));
  function Harness(){
   const [current,setCurrent]=useState(job),[step,setStep]=useState<CoreStep>(3),[pending,setPending]=useState<CoreStep|null>(null);
   const maxStep:CoreStep=current.approval_status==='APPROVED'?4:3;
   useEffect(()=>{if(pending&&pending<=maxStep){setStep(pending);setPending(null);}},[pending,maxStep]);
   const guarded=(next:CoreStep)=>{if(next<=maxStep){setPending(null);setStep(next);}else setPending(next);};
   return <><button type="button" onClick={()=>{setPending(null);setStep(2);}}>2단계로 이동</button><button type="button" aria-label="stage-three-return" onClick={()=>guarded(3)}>3</button><RepairPlanPreview job={current} onJob={setCurrent} guidedStep={step} onNextStep={guarded}/><output aria-label="현재 단계">{step}</output></>;
  }
  render(<Harness/>);await screen.findByText('=ROUND(C31*D31*(1-E31),0)');
  fireEvent.click(screen.getByRole('checkbox',{name:/위 1개 셀의 정확한/}));
  await waitFor(()=>expect(screen.getByRole('button',{name:'이 변경계획 승인'})).toBeEnabled());
  fireEvent.click(screen.getByRole('button',{name:'이 변경계획 승인'}));
  fireEvent.click(screen.getByRole('button',{name:'2단계로 이동'}));
  finish(response({...job,status:'APPROVED',approval_status:'APPROVED'}));
  await waitFor(()=>expect(actions.some(a=>a.action==='approve_plan')).toBe(true));
  expect(screen.getByLabelText('현재 단계')).toHaveTextContent('2');
  expect(screen.queryByRole('button',{name:'승인한 사본 만들기'})).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:'stage-three-return'}));
  await waitFor(()=>expect(document.querySelector('.delivery-execution .button--ghost')).toBeVisible());
  expect(screen.getByLabelText('현재 단계')).toHaveTextContent('3');
  expect(screen.queryByRole('button',{name:'승인된 사본 만들기'})).not.toBeInTheDocument();
 });
 it('disables manual plan calculation while an automatic prepare is still busy',()=>{
  render(<RepairPlanPreview job={{...job,entitlement_active:false}} onJob={vi.fn()} guidedStep={2} externalBusy/>);
  expect(screen.getByRole('button',{name:/변경 후 계산 영향/})).toBeDisabled();
 });
 it('does not accept delayed exact details from the previous plan',async()=>{
  let finish!:(v:Response)=>void;const pending=new Promise<Response>(r=>finish=r);
  vi.stubGlobal('fetch',vi.fn(()=>pending));const onJob=vi.fn();
  const view=render(<RepairPlanPreview job={job} onJob={onJob} guidedStep={3}/>);
  view.rerender(<RepairPlanPreview job={{...job,plan_summary:{...job.plan_summary!,digest:'plan-b'}}} onJob={onJob} guidedStep={3}/>);
  finish(response(detail));await waitFor(()=>expect(screen.queryByText('숫자 5,232')).not.toBeInTheDocument());
  expect(screen.queryByRole('button',{name:'이 변경계획 승인'})).not.toBeInTheDocument();
 });
 it('removes expired details and blocks approval even when refresh fails',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>JSON.parse(init.body).action==='plan_details'?response({...detail,expires_at:Date.now()/1000+0.12}):Promise.reject(new Error('synthetic offline'))));
  function Harness(){const [current,setCurrent]=useState(job);return <RepairPlanPreview job={current} onJob={setCurrent} guidedStep={3}/>;}
  render(<Harness/>);await waitFor(()=>expect(screen.getByRole('region',{name:'대표 수정 예시'})).toBeVisible());
  await waitFor(()=>expect(screen.getByRole('alert')).toHaveTextContent('계획이 만료되었습니다'));
  expect(screen.queryByRole('button',{name:'이 변경계획 승인'})).not.toBeInTheDocument();
  expect(screen.queryByRole('region',{name:'대표 수정 예시'})).not.toBeInTheDocument();
 });
});
