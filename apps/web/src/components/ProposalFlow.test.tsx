import { useState } from 'react';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { RepairProposalPicker } from './RepairProposalPicker';
import { RepairIntentEditor } from './RepairIntent';
import { DeliveryWorkspace, type DeliveryJob } from './DeliveryWorkspace';
import { RepairDelivery } from './RepairDelivery';
import { RepairPlanPreview, type PlanDetail } from './RepairPlanPreview';
import { noRepairIntent, RP01, RP02 } from '../lib/repairProposals';
import { demoResult } from '../data/demo';
import type { Finding } from '../types';
const evidence=vi.hoisted(()=>({readSourceCells:vi.fn(),readSourceSheets:vi.fn()}));
vi.mock('../lib/workbookEvidence',()=>evidence);
const file=new File(['synthetic-test-only'],'synthetic.xlsx');
const f=(cell:string,rule_code='NUMBER_STORED_AS_TEXT')=>({...demoResult.findings[0],sheet:'정산',cell,rule_code,formula_pattern:rule_code==='FORMULA_PATTERN_GAP'?{pattern_subtype:'BLANK_GAP_CANDIDATE',comparison_locations:['F2','F4'],evidence_locations:['F2','F4']}:null} as Finding);
const ok=(v:unknown)=>({ok:true,json:async()=>v} as Response);
const base:DeliveryJob={job_id:'synthetic',revision:1,status:'INPUT_READY',source_hash:'synthetic-only',expires_at:Date.now()/1000+900,sheets:[{name:'정산',cell_count:10}],preflight:null,purchase_enabled:false,source_unchanged:true};
const plan:DeliveryJob={...base,revision:3,status:'PREVIEW_VALIDATED',entitlement_active:true,repair_execution_available:true,policy:{profile:RP02,sheet:'정산',targets:['F3'],anchor:'F2',anchor_formula:'=C2*D2',confirmed:true},preflight:{status:'PRELIMINARY_ONLY',eligible_count:1,reason_codes:[],targets:[],purchase_enabled:false},plan_summary:{digest:'plan-a',status:'PREVIEW_VALIDATED',patch_count:1,impact_count:2,formula_impact_count:2,coverage:{formula_count:2},reference:{status:'PASS',case_count:36}}};
const detail:PlanDetail={digest:'plan-a',expires_at:Date.now()/1000+600,patches:[{candidate_id:'one',sheet:'정산',cell:'F3',before:{type:'blank',value:null},after:{type:'formula',value:'=C3*D3'}}],impact:[{sheet:'정산',cell:'F3',before:{type:'number',value:0},after:{type:'number',value:12}},{sheet:'정산',cell:'J10',before:{type:'number',value:20},after:{type:'number',value:32}}]};
afterEach(()=>{cleanup();vi.useRealTimers();vi.unstubAllGlobals();vi.clearAllMocks()});
describe('proposal-led UI contracts, not actual engine evidence',()=>{
 it('offers sheets including no candidates, preserves the exact chosen subset and blocks identifier conversion',async()=>{
  evidence.readSourceCells.mockResolvedValue([{cell:'B2',type:'text',text:'1,200'}]); const prepare=vi.fn();
  const selection={findings:[f('B2')],locked:false,toggle:vi.fn()};
  render(<RepairProposalPicker findings={[f('B2'),f('B3')]} sheets={['정산','메모']} file={file} selection={selection} intent={noRepairIntent} available onPrepare={prepare}/>);
  await screen.findByText('문자 “1,200”');
  expect(screen.getByLabelText('1단계에서 고른 1개만 제안받기')).toBeChecked();
  expect(screen.getByRole('option',{name:'메모 · 발견된 수정 후보 없음'})).toBeInTheDocument();
  fireEvent.click(screen.getByRole('radio',{name:/구분하는 번호/}));expect(screen.getByRole('button',{name:'이 제안으로 수정 예시 확인'})).toBeDisabled();
  fireEvent.click(screen.getByRole('radio',{name:/^금액/}));
  fireEvent.click(screen.getByRole('checkbox',{name:/선택한 칸은 계산할/}));
  fireEvent.click(screen.getByRole('button',{name:'이 제안으로 수정 예시 확인'}));
  expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:RP01,sheet:'정산',targets:['B2'],role:'AMOUNT',confirmed:true,proposal:true}));
  fireEvent.change(screen.getByLabelText('제안을 확인할 시트'),{target:{value:'메모'}});
  expect(screen.getByRole('status')).toHaveTextContent('발견된 수정 후보가 없습니다');
 });
 it('carries the selected real anchor formula without requiring cell or formula typing or auto-confirmation',async()=>{
  evidence.readSourceCells.mockResolvedValue([{cell:'F3',type:'blank',text:'빈 셀'},{cell:'F2',type:'formula',text:'=C2*D2',cached:'10'},{cell:'F4',type:'formula',text:'=C4*D4',cached:'14'}]);const prepare=vi.fn();
  render(<RepairProposalPicker findings={[f('F3','FORMULA_PATTERN_GAP')]} sheets={['정산']} file={file} selection={{findings:[],locked:false,toggle:vi.fn()}} intent={noRepairIntent} available onPrepare={prepare}/>);
  await screen.findByText('비어 있는 칸');
  expect(screen.getByRole('checkbox',{name:/선택한 빈 칸도/})).not.toBeChecked();
  fireEvent.change(screen.getByLabelText('어느 칸과 같은 방식으로 계산할까요?'),{target:{value:'F4'}});
  fireEvent.click(screen.getByRole('checkbox',{name:/선택한 빈 칸도/}));
  fireEvent.click(screen.getByRole('button',{name:'이 제안으로 수정 예시 확인'}));
  expect(prepare).toHaveBeenCalledWith(expect.objectContaining({targets:['F3'],anchor:'F4',anchor_formula:'=C4*D4',confirmed:true}));
 });
 it('does not use delayed source evidence from a previous sheet',async()=>{
  let finish!:(v:unknown)=>void;evidence.readSourceCells.mockImplementationOnce(()=>new Promise(r=>finish=r)).mockResolvedValue([{cell:'B2',type:'text',text:'7'}]);
  render(<RepairProposalPicker findings={[f('B2'),{...f('B2'),sheet:'다른'}]} sheets={['정산','다른']} file={file} selection={{findings:[],locked:false,toggle:vi.fn()}} intent={noRepairIntent} available onPrepare={vi.fn()}/>);
  await waitFor(()=>expect(evidence.readSourceCells).toHaveBeenCalled());fireEvent.change(screen.getByLabelText('제안을 확인할 시트'),{target:{value:'다른'}});
  await screen.findByText('문자 “7”');finish([{cell:'B2',type:'text',text:'OLD-DO-NOT-USE'}]);
  await waitFor(()=>expect(screen.queryByText('문자 “OLD-DO-NOT-USE”')).not.toBeInTheDocument());
 });
 it('keeps optional intent local and unchecked business details out of the server request',async()=>{
  const network=vi.fn();vi.stubGlobal('fetch',network);
  function Harness(){const [value,set]=useState(noRepairIntent);return <RepairIntentEditor value={value} onChange={set} findings={[f('B2')]} sheets={['정산']} locked={false}/>;}
  render(<Harness/>);expect(screen.queryByLabelText('원하는 숫자')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('checkbox',{name:'별도 의견 없이 규칙으로 확인할게요'}));
  fireEvent.change(screen.getByLabelText('확인할 위치'),{target:{value:'B2'}});fireEvent.change(screen.getByLabelText('원하는 숫자'),{target:{value:'12'}});
  expect(screen.getByLabelText('원하는 숫자')).toHaveValue('12');expect(network).not.toHaveBeenCalled();
 });
 it('checks an explicitly chosen proposal and calculates it after source consent, without approval or execution',async()=>{
  const actions:Record<string,unknown>[]=[];
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{const a=JSON.parse(init.body);actions.push(a);return ok(a.action==='capabilities'?{max_bytes:2097152,payment_mode:'OFF'}:a.action==='create_input'?base:a.action==='preflight'?{...base,revision:2,preflight:plan.preflight}:{...plan,entitlement_active:false});}));
  render(<DeliveryWorkspace file={file} reviewDraft={{profile:RP01,sheet:'정산',targets:['B2'],role:'AMOUNT',confirmed:true,proposal:true}}/>);
  await screen.findByRole('button',{name:'이 원본으로 수정 범위 확인'});
  expect(actions.map(a=>a.action)).toEqual(['capabilities']);
  fireEvent.click(screen.getByRole('checkbox',{name:/업로드 권한이 있는/}));fireEvent.click(screen.getByRole('button',{name:'이 원본으로 수정 범위 확인'}));
  await waitFor(()=>expect(actions.some(a=>a.action==='prepare_plan')).toBe(true));
  expect(actions.find(a=>a.action==='preflight')).toMatchObject({policy:{profile:RP01,sheet:'정산',targets:['B2'],role:'AMOUNT',confirmed:true}});
  expect(actions.some(a=>['approve_plan','execute','synthetic_rehearsal'].includes(String(a.action)))).toBe(false);
 });
 it.each([['12','matched'],['10','mismatch'],['','unverified']])('shows a real representative and gates exact approval for requested %s (%s)',async(expected,status)=>{
  vi.stubGlobal('fetch',vi.fn(async()=>ok(detail)));const gate=vi.fn();
  render(<RepairPlanPreview job={plan} onJob={vi.fn()} guidedStep={3} intent={{...noRepairIntent,enabled:true,sheet:'정산',cell:'F3',expected}} onIntentCheck={gate}/>);
  const representative=await screen.findByRole('region',{name:'대표 수정 예시'});
  expect(within(representative).getByText('12',{exact:true})).toBeVisible();
  expect(screen.getByText('=C3*D3')).toBeVisible();
  expect(screen.queryByRole('button',{name:'전체 1곳의 정확한 변경·수식 확인'})).not.toBeInTheDocument();
  if(status==='matched'){await waitFor(()=>expect(gate).toHaveBeenLastCalledWith(true));expect(screen.getByRole('button',{name:'이 변경계획 승인'})).toBeDisabled();}
  else {expect(screen.queryByRole('button',{name:'이 변경계획 승인'})).not.toBeInTheDocument();expect(gate).toHaveBeenLastCalledWith(false);}
 });
 it('reveals the calculated step 2 result once and consumes stale reveal requests after leaving the step',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>ok(detail)));
  const scroll=vi.spyOn(Element.prototype,'scrollIntoView');
  const focus=vi.spyOn(HTMLElement.prototype,'focus');
  const view=render(<RepairPlanPreview job={plan} onJob={vi.fn()} guidedStep={2} planRevealToken={0}/>);
  await screen.findByText('예를 들면 이렇게 바뀝니다');
  scroll.mockClear();focus.mockClear();
  view.rerender(<RepairPlanPreview job={plan} onJob={vi.fn()} guidedStep={2} planRevealToken={1}/>);
  await waitFor(()=>expect(scroll).toHaveBeenCalledTimes(1));
  expect(focus).toHaveBeenCalledWith({preventScroll:true});
  scroll.mockClear();focus.mockClear();
  view.rerender(<RepairPlanPreview job={plan} onJob={vi.fn()} guidedStep={1} planRevealToken={2}/>);
  await waitFor(()=>expect(scroll).toHaveBeenCalledTimes(0));
  view.rerender(<RepairPlanPreview job={plan} onJob={vi.fn()} guidedStep={2} planRevealToken={2}/>);
  await waitFor(()=>expect(scroll).toHaveBeenCalledTimes(0));
 });
 it('reveals the step 2 plan summary and trial CTA before entitlement unlocks the verified example',async()=>{
  const trialPlan={...plan,entitlement_active:false,internal_rehearsal:false,synthetic_rehearsal_available:true};
  vi.stubGlobal('fetch',vi.fn(async()=>ok({payment_mode:'OFF'})));
  const scroll=vi.spyOn(Element.prototype,'scrollIntoView');
  render(<RepairPlanPreview job={trialPlan} onJob={vi.fn()} guidedStep={2} planRevealToken={1}/>);
  await screen.findByText('검증한 수정 예시 보기');
  await waitFor(()=>expect(scroll).toHaveBeenCalledTimes(1));
 });
 it('reveals step 3 only from the current explicit next-step action',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>ok(detail)));
  const scroll=vi.spyOn(Element.prototype,'scrollIntoView');
  function Harness(){const [step,setStep]=useState<2|3>(2);return <RepairPlanPreview job={plan} onJob={vi.fn()} guidedStep={step} onNextStep={next=>{if(next===2||next===3)setStep(next);}}/>;}
  render(<Harness/>);
  await screen.findByText('예를 들면 이렇게 바뀝니다');
  scroll.mockClear();
  fireEvent.click(screen.getByRole('button',{name:/3/}));
  await waitFor(()=>expect(scroll).toHaveBeenCalledTimes(1));
  expect(screen.getByText(/바꾸려는 내용과 계산 결과/)).toBeInTheDocument();
 });
 it('reveals delivery files once after user-triggered execution reaches ready',async()=>{
  const ready={...plan,status:'READY',approval_status:'APPROVED',delivery:{delivery_id:'d1',patch_count:1,expires_at:Date.now()/1000+600,files:{REPAIRED_XLSX:{bytes:10},CHANGES_XLSX:{bytes:10},VERIFICATION_HTML:{bytes:10}}}};
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>ok(JSON.parse(String(init?.body)).action==='execute'?ready:ready)));
  const scroll=vi.spyOn(Element.prototype,'scrollIntoView');
  const focus=vi.spyOn(HTMLElement.prototype,'focus');
  function Harness(){const [job,setJob]=useState<DeliveryJob>({...plan,approval_status:'APPROVED'});return <RepairDelivery job={job} detail={detail} onJob={setJob} mode="delivery"/>;}
  render(<Harness/>);
  fireEvent.click(screen.getByRole('button',{name:/사본|실행/}));
  await screen.findByText(/준비되었습니다/);
  await waitFor(()=>expect(scroll).toHaveBeenCalledTimes(1));
  expect(focus).toHaveBeenCalledWith({preventScroll:true});
 });
 it('does not reveal a late execution result after leaving the delivery step',async()=>{
  let finish!:(value:Response)=>void;
  const ready={...plan,status:'READY',approval_status:'APPROVED',delivery:{delivery_id:'d1',patch_count:1,expires_at:Date.now()/1000+600,files:{REPAIRED_XLSX:{bytes:10}}}};
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>JSON.parse(String(init?.body)).action==='execute'?new Promise<Response>(resolve=>{finish=resolve;}):ok(ready)));
  const scroll=vi.spyOn(Element.prototype,'scrollIntoView');
  function Harness(){const [job,setJob]=useState<DeliveryJob>({...plan,approval_status:'APPROVED'});const [mode,setMode]=useState<'approval'|'delivery'>('delivery');return <><button type="button" onClick={()=>setMode('approval')}>back to approval</button><RepairDelivery job={job} detail={detail} onJob={setJob} mode={mode}/></>;}
  render(<Harness/>);
  fireEvent.click(screen.getByRole('button',{name:/사본|실행/}));
  fireEvent.click(screen.getByRole('button',{name:'back to approval'}));
  finish(ok(ready));
  await waitFor(()=>expect(screen.getByText('정확한 변경 승인')).toBeInTheDocument());
  expect(scroll).not.toHaveBeenCalled();
 });
 it('reveals a polled ready result once even if the execute response also returns ready',async()=>{
  let finish!:(value:Response)=>void;
  const ready={...plan,status:'READY',approval_status:'APPROVED',delivery:{delivery_id:'d1',patch_count:1,expires_at:Date.now()/1000+600,files:{REPAIRED_XLSX:{bytes:10}}}};
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{const action=JSON.parse(String(init?.body)).action;if(action==='execute')return new Promise<Response>(resolve=>{finish=resolve;});return ok(ready);}));
  const scroll=vi.spyOn(Element.prototype,'scrollIntoView');
  function Harness(){const [job,setJob]=useState<DeliveryJob>({...plan,approval_status:'APPROVED'});return <RepairDelivery job={job} detail={detail} onJob={setJob} mode="delivery"/>;}
  render(<Harness/>);
  fireEvent.click(screen.getByRole('button',{name:/사본|실행/}));
  await waitFor(()=>expect(scroll).toHaveBeenCalledTimes(1));
  await act(async()=>{finish(ok(ready));});
  expect(scroll).toHaveBeenCalledTimes(1);
 });
});
