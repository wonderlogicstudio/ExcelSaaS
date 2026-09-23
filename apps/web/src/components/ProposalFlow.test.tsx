import { useState } from 'react';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { RepairProposalPicker } from './RepairProposalPicker';
import { RepairIntentEditor } from './RepairIntent';
import { DeliveryWorkspace, type DeliveryJob } from './DeliveryWorkspace';
import { RepairDelivery } from './RepairDelivery';
import { RepairPlanPreview, type PlanDetail } from './RepairPlanPreview';
import { noRepairIntent, RP01, RP02, RP03 } from '../lib/repairProposals';
import { demoResult } from '../data/demo';
import type { Finding } from '../types';
const evidence=vi.hoisted(()=>({readSourceCells:vi.fn(),readSourceSheets:vi.fn()}));
vi.mock('../lib/workbookEvidence',()=>evidence);
const file=new File(['synthetic-test-only'],'synthetic.xlsx');
const COMBINED='COMBINED_RP01_RP02_REPAIR_V1';
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
  fireEvent.click(screen.getByRole('radio',{name:/구분하는 번호/}));expect(screen.getByRole('button',{name:'이 묶음만 변경 예시 확인'})).toBeDisabled();
  fireEvent.click(screen.getByRole('radio',{name:/^금액/}));
  fireEvent.click(screen.getByRole('checkbox',{name:/선택한 칸은 계산할/}));
  fireEvent.click(screen.getByRole('button',{name:'이 묶음만 변경 예시 확인'}));
  expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:RP01,sheet:'정산',targets:['B2'],role:'AMOUNT',confirmed:true,proposal:true}));
  fireEvent.change(screen.getByLabelText('제안을 확인할 시트'),{target:{value:'메모'}});
  expect(screen.getByRole('status')).toHaveTextContent('발견된 수정 후보가 없습니다');
 });

 it('collects numeric and blank-formula proposals into one combined 수정 목록 draft',async()=>{
  evidence.readSourceCells
   .mockResolvedValueOnce([{cell:'B2',type:'text',text:'1,200'}])
   .mockResolvedValueOnce([{cell:'F3',type:'blank',text:'빈 셀'},{cell:'F2',type:'formula',text:'=C2*D2',cached:'10'},{cell:'F4',type:'formula',text:'=C4*D4',cached:'14'}]);
  const prepare=vi.fn();
  const view=render(<RepairProposalPicker findings={[f('B2'),f('F3','FORMULA_PATTERN_GAP')]} sheets={['정산']} file={file} selection={{findings:[],locked:false,toggle:vi.fn()}} intent={noRepairIntent} available onPrepare={prepare}/>);
  await waitFor(()=>expect(view.container.querySelector('input[value="AMOUNT"]')).toBeTruthy());
  fireEvent.click(view.container.querySelector('input[value="AMOUNT"]')!);
  fireEvent.click(view.container.querySelector('.delivery-check input[type="checkbox"]')!);
  fireEvent.click(screen.getByRole('button',{name:'변경 목록에 추가'}));
  const optionButtons=Array.from(view.container.querySelectorAll<HTMLButtonElement>('.proposal-option button'));
  fireEvent.click(optionButtons.find(button=>!button.disabled)!);
  await waitFor(()=>expect(evidence.readSourceCells).toHaveBeenCalledTimes(2));
  await waitFor(()=>expect(view.container.querySelector('.proposal-anchor select')).toHaveValue('F2'));
  fireEvent.click(view.container.querySelector('.delivery-check input[type="checkbox"]')!);
  fireEvent.click(screen.getByRole('button',{name:'변경 목록에 추가'}));
  fireEvent.click(screen.getByRole('button',{name:'선택한 2곳의 변경 예시 확인'}));
  expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:COMBINED,confirmed:true,proposal:true,targets:['B2','F3'],items:[expect.objectContaining({profile:RP01,targets:['B2']}),expect.objectContaining({profile:RP02,targets:['F3'],anchor:'F2',anchor_formula:'=C2*D2'})]}));
 });
 it('clears the basket when the upstream step 1 selection changes but keeps it while switching sheets',async()=>{
  evidence.readSourceCells.mockResolvedValue([{cell:'B2',type:'text',text:'1,200'}]);
  const prepare=vi.fn();
  function Harness(){
    const [selection,setSelection]=useState({findings:[f('B2')],locked:false,toggle:vi.fn()});
    return <><button type="button" onClick={()=>setSelection({findings:[f('B3')],locked:false,toggle:vi.fn()})}>change upstream selection</button><RepairProposalPicker findings={[f('B2'),f('B3'),{...f('B2'),sheet:'다른'}]} sheets={['정산','다른']} file={file} selection={selection} intent={noRepairIntent} available onPrepare={prepare}/></>;
  }
  render(<Harness/>);
  await waitFor(()=>expect(screen.getByRole('radio',{name:/^금액/})).toBeInTheDocument());
  fireEvent.click(screen.getByRole('radio',{name:/^금액/}));
  fireEvent.click(screen.getByRole('checkbox',{name:/선택한 칸은 계산할/}));
  fireEvent.click(screen.getByRole('button',{name:'변경 목록에 추가'}));
  expect(screen.getByRole('region',{name:'선택한 수정 목록'})).toHaveTextContent('선택한 1곳');
  fireEvent.click(screen.getByText('담은 묶음 1개 보기'));
  expect(screen.getByRole('button',{name:'정산 B열 숫자 텍스트 정리 1곳 제외'})).toBeVisible();
  fireEvent.change(screen.getByLabelText('제안을 확인할 시트'),{target:{value:'다른'}});
  expect(screen.getByRole('region',{name:'선택한 수정 목록'})).toHaveTextContent('선택한 1곳');
  fireEvent.click(screen.getByRole('button',{name:'change upstream selection'}));
  await waitFor(()=>expect(screen.queryByRole('region',{name:'선택한 수정 목록'})).not.toBeInTheDocument());
  expect(screen.getByText('1단계 선택이 바뀌어 기존 수정 목록을 비웠습니다.')).toBeInTheDocument();
  expect(prepare).not.toHaveBeenCalled();
 });
 it('shows an added basket state, undo, and an explicit update when criteria change',async()=>{
  evidence.readSourceCells.mockResolvedValue([{cell:'B2',type:'text',text:'1,200'}]);
  const prepare=vi.fn();
  render(<RepairProposalPicker findings={[f('B2'),f('B3')]} sheets={['정산']} file={file} selection={{findings:[],locked:false,toggle:vi.fn()}} intent={noRepairIntent} available onPrepare={prepare}/>);
  await waitFor(()=>expect(screen.getByRole('radio',{name:/^금액/})).toBeInTheDocument());
  fireEvent.click(screen.getByRole('radio',{name:/^금액/}));
  fireEvent.click(screen.getByRole('checkbox',{name:/선택한 칸은 계산할/}));
  fireEvent.click(screen.getByRole('button',{name:'변경 목록에 추가'}));
  expect(screen.getByRole('button',{name:'✓ 추가됨'})).toBeDisabled();
  expect(screen.getByRole('button',{name:'되돌리기'})).toBeVisible();
  expect(screen.getByRole('region',{name:'선택한 수정 목록'})).toHaveTextContent('선택한 2곳');
  expect(screen.getByRole('button',{name:'선택한 2곳의 변경 예시 확인'})).toBeVisible();
  fireEvent.click(screen.getByLabelText('B3'));
  expect(screen.getByText(/목록은 아직 이전 선택/)).toBeVisible();
  fireEvent.click(screen.getByRole('checkbox',{name:/선택한 칸은 계산할/}));
  fireEvent.click(screen.getByRole('button',{name:'목록 업데이트'}));
  expect(screen.getByRole('region',{name:'선택한 수정 목록'})).toHaveTextContent('선택한 1곳');
  fireEvent.click(screen.getByRole('button',{name:'되돌리기'}));
  expect(screen.queryByRole('region',{name:'선택한 수정 목록'})).not.toBeInTheDocument();
  expect(prepare).not.toHaveBeenCalled();
 });
 it('carries the selected real anchor formula without requiring cell or formula typing or auto-confirmation',async()=>{
  evidence.readSourceCells.mockResolvedValue([{cell:'F3',type:'blank',text:'빈 셀'},{cell:'F2',type:'formula',text:'=C2*D2',cached:'10'},{cell:'F4',type:'formula',text:'=C4*D4',cached:'14'}]);const prepare=vi.fn();
  render(<RepairProposalPicker findings={[f('F3','FORMULA_PATTERN_GAP')]} sheets={['정산']} file={file} selection={{findings:[],locked:false,toggle:vi.fn()}} intent={noRepairIntent} available onPrepare={prepare}/>);
  await screen.findByText('비어 있는 칸');
  expect(screen.getByRole('checkbox',{name:/선택한 빈 칸도/})).not.toBeChecked();
  fireEvent.change(screen.getByLabelText('어느 칸과 같은 방식으로 계산할까요?'),{target:{value:'F4'}});
  fireEvent.click(screen.getByRole('checkbox',{name:/선택한 빈 칸도/}));
  fireEvent.click(screen.getByRole('button',{name:'이 묶음만 변경 예시 확인'}));
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
  fireEvent.click(screen.getAllByText(/빈 셀 수식 복원/).find(el=>el.tagName==='SUMMARY')!);
  expect(screen.getByText('=C3*D3')).toBeVisible();
  expect(screen.queryByRole('button',{name:'전체 1곳의 정확한 변경·수식 확인'})).not.toBeInTheDocument();
  if(status==='matched'){await waitFor(()=>expect(gate).toHaveBeenLastCalledWith(true));expect(screen.getByRole('button',{name:'이 변경계획 승인'})).toBeDisabled();}
  else {expect(screen.queryByRole('button',{name:'이 변경계획 승인'})).not.toBeInTheDocument();expect(gate).toHaveBeenLastCalledWith(false);}
 });

 it('opens the exact monthly RP03 patch group by default without opening legacy groups',async()=>{
  const monthlyJob={...plan,policy:{profile:RP03,sheet:'Budget',targets:['N18'],before_formula:'=N15-N14',confirmed:true},plan_summary:{...plan.plan_summary,digest:'monthly-plan'}} as DeliveryJob;
  const monthlyDetail:PlanDetail={digest:'monthly-plan',expires_at:Date.now()/1000+600,patches:[{candidate_id:'m',sheet:'Budget',cell:'N18',profile_version:RP03,change_kind:'MONTHLY_FORMULA_REPLACEMENT',before:{type:'formula',value:'=N15-N14'},after:{type:'formula',value:"='M10'!B16-'M10'!B15"}}],impact:[{sheet:'Budget',cell:'N18',before:{type:'error',value:'#VALUE!'},after:{type:'number',value:-5}}]};
  vi.stubGlobal('fetch',vi.fn(async()=>ok(monthlyDetail)));
  render(<RepairPlanPreview job={monthlyJob} onJob={vi.fn()} guidedStep={3} intent={noRepairIntent}/>);
  await screen.findByText("='M10'!B16-'M10'!B15");
  expect(screen.getByText("='M10'!B16-'M10'!B15")).toBeVisible();
  expect(screen.getByText('숫자 -5')).toBeVisible();
 });
 it('summarizes both repair types for a combined policy without top-level targets',async()=>{
  const combinedJob={...plan,policy:{profile:COMBINED,items:[{profile:RP01,sheet:'정산',targets:['B2'],role:'AMOUNT',confirmed:true},{profile:RP02,sheet:'정산',targets:['F3'],anchor:'F2',anchor_formula:'=C2*D2',confirmed:true}]}} as DeliveryJob;
  const combinedDetail:PlanDetail={...detail,patches:[{candidate_id:'n',sheet:'정산',cell:'B2',profile_version:RP01,before:{type:'text',value:'1,200'},after:{type:'number',value:1200}},{candidate_id:'f',sheet:'정산',cell:'F3',profile_version:RP02,before:{type:'blank',value:null},after:{type:'formula',value:'=C3*D3'}}],impact:[{sheet:'정산',cell:'B2',before:{type:'text',value:'1,200'},after:{type:'number',value:1200}},{sheet:'정산',cell:'F3',before:{type:'number',value:0},after:{type:'number',value:12}},{sheet:'정산',cell:'J10',before:{type:'number',value:20},after:{type:'number',value:1232}}]};
  vi.stubGlobal('fetch',vi.fn(async()=>ok(combinedDetail)));
  render(<RepairPlanPreview job={combinedJob} onJob={vi.fn()} guidedStep={2} intent={noRepairIntent}/>);
  await screen.findByRole('region',{name:'대표 수정 예시'});
  expect(screen.getByText(/숫자 텍스트 정리 1곳/)).toBeVisible();
  expect(screen.getByText(/빈 셀 수식 복원 1곳/)).toBeVisible();
 });
 it('rechecks a revised same-source combined draft without uploading the source again',async()=>{
  const actions:Record<string,unknown>[]=[]; let revision=1; let currentPolicy:unknown=null;
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{const a=JSON.parse(String(init?.body));actions.push(a); if(a.action==='capabilities')return ok({max_bytes:2097152}); if(a.action==='create_input')return ok({...base,job_id:'same-source',revision:revision++}); if(a.action==='preflight'){currentPolicy=a.policy;return ok({...base,job_id:'same-source',revision:revision++,policy:a.policy,preflight:plan.preflight,status:'INPUT_READY'});} if(a.action==='prepare_plan')return ok({...plan,job_id:'same-source',revision:revision++,policy:currentPolicy,plan_summary:{...plan.plan_summary,digest:`plan-${revision}`}}); return ok(plan);}));
  const first={profile:RP01,sheet:'정산',targets:['B2'],role:'AMOUNT',confirmed:true,proposal:true};
  const second={profile:COMBINED,sheet:'정산',targets:['B2','F3'],confirmed:true,proposal:true,items:[first,{profile:RP02,sheet:'정산',targets:['F3'],anchor:'F2',anchor_formula:'=C2*D2',confirmed:true,proposal:true}]};
  const view=render(<DeliveryWorkspace file={file} reviewDraft={first} intent={noRepairIntent}/>);
  fireEvent.click(await screen.findByRole('checkbox',{name:/업로드 권한/}));
  fireEvent.click(screen.getByRole('button',{name:'이 원본으로 수정 범위 확인'}));
  await waitFor(()=>expect(actions.filter(a=>a.action==='prepare_plan')).toHaveLength(1));
  view.rerender(<DeliveryWorkspace file={file} reviewDraft={second} intent={noRepairIntent}/>);
  await waitFor(()=>expect(actions.filter(a=>a.action==='prepare_plan')).toHaveLength(2));
  expect(actions.filter(a=>a.action==='create_input')).toHaveLength(1);
  expect(actions.filter(a=>a.action==='preflight').at(-1)).toMatchObject({policy:{profile:COMBINED,items:[expect.objectContaining({profile:RP01,targets:['B2']}),expect.objectContaining({profile:RP02,targets:['F3'],anchor:'F2'})]}});
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

 it('starts all three ready downloads from one explicit click and keeps fallback buttons',async()=>{
  const ready={...plan,status:'READY',approval_status:'APPROVED',delivery:{delivery_id:'d1',patch_count:1,expires_at:Date.now()/1000+600,files:{REPAIRED_XLSX:{bytes:10},CHANGES_XLSX:{bytes:10},VERIFICATION_HTML:{bytes:10}}}};
  const actions:string[]=[];
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{const action=JSON.parse(String(init?.body)).action;actions.push(action);return ok({filename:`${actions.length}.bin`,mime:'application/octet-stream',file_base64:'eA=='});}));
  vi.stubGlobal('URL',{createObjectURL:vi.fn(()=>`blob:${actions.length}`),revokeObjectURL:vi.fn()});
  const clicks=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>undefined);
  render(<RepairDelivery job={ready as DeliveryJob} detail={detail} onJob={vi.fn()} mode="delivery"/>);
  expect(screen.getByRole('button',{name:'세 파일 모두 받기'})).toBeEnabled();
  expect(screen.getByRole('button',{name:/수정본 XLSX 받기/})).toBeVisible();
  fireEvent.click(screen.getByRole('button',{name:'세 파일 모두 받기'}));
  await waitFor(()=>expect(actions.filter(a=>a==='download')).toHaveLength(3));
  expect(clicks).toHaveBeenCalledTimes(3);
 });
 it('reports a partial all-download failure and prevents repeated clicks while busy',async()=>{
  let release!:()=>void;
  const ready={...plan,status:'READY',approval_status:'APPROVED',delivery:{delivery_id:'d1',patch_count:1,expires_at:Date.now()/1000+600,files:{REPAIRED_XLSX:{bytes:10},CHANGES_XLSX:{bytes:10},VERIFICATION_HTML:{bytes:10}}}};
  const actions:string[]=[];
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{const body=JSON.parse(String(init?.body));actions.push(`${body.action}:${body.kind??''}`); if(body.action==='get')return ok(ready); if(body.kind==='REPAIRED_XLSX')await new Promise<void>(resolve=>{release=resolve;}); if(body.kind==='CHANGES_XLSX')throw new Error('changes download failed'); return ok({filename:`${body.kind}.bin`,mime:'application/octet-stream',file_base64:'eA=='});}));
  vi.stubGlobal('URL',{createObjectURL:vi.fn(()=>'blob:one'),revokeObjectURL:vi.fn()});
  vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>undefined);
  render(<RepairDelivery job={ready as DeliveryJob} detail={detail} onJob={vi.fn()} mode="delivery"/>);
  const all=screen.getByRole('button',{name:'세 파일 모두 받기'});
  fireEvent.click(all);
  await waitFor(()=>expect(all).toBeDisabled());
  fireEvent.click(all);
  expect(actions.filter(a=>a==='download:REPAIRED_XLSX')).toHaveLength(1);
  await act(async()=>{release();});
  await screen.findByRole('alert');
  expect(screen.getByRole('alert')).toHaveTextContent('서버에 연결하지 못했습니다');
  expect(actions).toContain('get:');
  expect(actions.filter(a=>a.startsWith('download:'))).toEqual(['download:REPAIRED_XLSX','download:CHANGES_XLSX']);
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

 it('sends a monthly RP03 request with source-derived before_formula and no typed address or formula',async()=>{
  evidence.readSourceCells.mockResolvedValue([{cell:'N18',type:'formula',text:'=N15-N14',cached:'#VALUE!'}]);
  const prepare=vi.fn();
  const monthly={...f('N18','FORMULA_PATTERN_OUTLIER'),sheet:'Budget',formula_pattern:{pattern_type:'DOMINANT_NORMALIZED_PATTERN_OUTLIER',formula_region:'N18',dominant_pattern_id:'m',neighbor_count:4,evidence_locations:['L18','M18','O18','P18'],detection_basis:'synthetic',current_limitations:[],pattern_subtype:'REFERENCE_SHEET_DRIFT'}} as Finding;
  render(<RepairProposalPicker findings={[monthly]} sheets={['Budget']} file={file} selection={{findings:[],locked:false,toggle:vi.fn()}} intent={noRepairIntent} available onPrepare={prepare}/>);
  await waitFor(()=>expect(screen.getAllByText('=N15-N14').length).toBeGreaterThan(0));
  expect(screen.getAllByText(/검증 필요 후보/).length).toBeGreaterThan(0);
  expect(screen.queryByRole('checkbox',{name:/월별 수식 후보/})).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:'선택한 월별 수식 서버 검증으로 변경 예시 확인'}));
  expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:RP03,sheet:'Budget',targets:['N18'],before_formula:'=N15-N14',confirmed:true,proposal:true}));
  expect(prepare.mock.calls[0][0]).not.toHaveProperty('anchor_formula');
 });
 it('keeps a monthly basket single-target and refuses mixing without erasing the existing choice',async()=>{
  evidence.readSourceCells.mockResolvedValue([{cell:'N18',type:'formula',text:'=N15-N14',cached:'#VALUE!'},{cell:'O18',type:'formula',text:'=O15-O14',cached:'#VALUE!'}]);
  const prepare=vi.fn();
  const m1={...f('N18','FORMULA_PATTERN_OUTLIER'),sheet:'Budget',formula_pattern:{pattern_type:'DOMINANT_NORMALIZED_PATTERN_OUTLIER',formula_region:'N18',dominant_pattern_id:'m',neighbor_count:4,evidence_locations:['L18','M18','O18','P18'],detection_basis:'synthetic',current_limitations:[],pattern_subtype:'REFERENCE_SHEET_DRIFT'}} as Finding;
  const m2={...f('O18','FORMULA_PATTERN_OUTLIER'),sheet:'Budget',formula_pattern:{pattern_type:'DOMINANT_NORMALIZED_PATTERN_OUTLIER',formula_region:'O18',dominant_pattern_id:'m',neighbor_count:4,evidence_locations:['L18','M18','N18','P18'],detection_basis:'synthetic',current_limitations:[],pattern_subtype:'REFERENCE_SHEET_DRIFT'}} as Finding;
  render(<RepairProposalPicker findings={[m1,m2]} sheets={['Budget']} file={file} selection={{findings:[],locked:false,toggle:vi.fn()}} intent={noRepairIntent} available onPrepare={prepare}/>);
  await waitFor(()=>expect(screen.getAllByText('=N15-N14').length).toBeGreaterThan(0));
  expect(screen.queryByRole('checkbox',{name:/월별 수식 후보/})).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:'변경 목록에 추가'}));
  expect(screen.getByRole('region',{name:'선택한 수정 목록'})).toHaveTextContent('선택한 1곳');
  fireEvent.click(screen.getAllByRole('button',{name:'이 수정 제안 보기'}).at(-1)!);
  await waitFor(()=>expect(screen.getAllByText('=O15-O14').length).toBeGreaterThan(0));
  expect(screen.queryByRole('checkbox',{name:/월별 수식 후보/})).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:'변경 목록에 추가'}));
  expect(screen.getAllByText(/월별 수식 후보는 다른 수정 묶음과 함께 보낼 수 없습니다/).length).toBeGreaterThan(0);
  expect(screen.getByRole('region',{name:'선택한 수정 목록'})).toHaveTextContent('선택한 1곳');
  fireEvent.click(screen.getByRole('button',{name:'선택한 1곳의 변경 예시 확인'}));
  expect(prepare).toHaveBeenCalledWith(expect.objectContaining({profile:RP03,targets:['N18'],before_formula:'=N15-N14'}));
 });
 it('passes monthly before_formula through the delivery preflight request',async()=>{
  const actions:Record<string,unknown>[]=[];
  vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{const a=JSON.parse(String(init?.body));actions.push(a);return ok(a.action==='capabilities'?{max_bytes:2097152,payment_mode:'OFF'}:a.action==='create_input'?base:a.action==='preflight'?{...base,revision:2,policy:a.policy,preflight:plan.preflight}:{...plan,policy:a.policy});}));
  render(<DeliveryWorkspace file={file} reviewDraft={{profile:RP03,sheet:'Budget',targets:['N18'],before_formula:'=N15-N14',confirmed:true,proposal:true}}/>);
  fireEvent.click(await screen.findByRole('checkbox',{name:/업로드 권한/}));
  fireEvent.click(screen.getByRole('button',{name:/원본으로 수정 범위 확인/}));
  await waitFor(()=>expect(actions.some(a=>a.action==='preflight')).toBe(true));
  expect(actions.find(a=>a.action==='preflight')).toMatchObject({policy:{profile:RP03,sheet:'Budget',targets:['N18'],before_formula:'=N15-N14',confirmed:true}});
 });
});
