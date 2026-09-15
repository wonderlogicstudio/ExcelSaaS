import { useState } from 'react';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DeliveryWorkspace, type DeliveryJob } from './DeliveryWorkspace';
import { RepairPlanPreview, type PlanDetail } from './RepairPlanPreview';
import { RepairDelivery } from './RepairDelivery';

const ok = (value: unknown) => ({ok:true,json:async()=>value} as Response);
const plan: DeliveryJob = {
  job_id:'scroll-a',revision:1,source_hash:'synthetic',status:'PREVIEW_VALIDATED',expires_at:Date.now()/1000+900,
  sheets:[{name:'Sheet',cell_count:3}],purchase_enabled:false,source_unchanged:true,
  preflight:{status:'PRELIMINARY_ONLY',eligible_count:1,reason_codes:[],purchase_enabled:false,targets:[]},
  synthetic_rehearsal_available:true,repair_execution_available:true,entitlement_active:false,
  plan_summary:{digest:'a',status:'PREVIEW_VALIDATED',patch_count:1,impact_count:1,formula_impact_count:1,coverage:{formula_count:1},reference:{status:'PASS'}},
};
const detail: PlanDetail = {digest:'a',expires_at:Date.now()/1000+600,patches:[{candidate_id:'one',sheet:'Sheet',cell:'A1',before:{type:'text',value:'2'},after:{type:'number',value:2}}],impact:[]};
const ready: DeliveryJob = {...plan,status:'READY',approval_status:'APPROVED',delivery:{delivery_id:'files',patch_count:1,expires_at:Date.now()/1000+600,files:{REPAIRED_XLSX:{bytes:1}}}};
const frame = () => act(async () => { await new Promise<void>(resolve => requestAnimationFrame(() => resolve())); });
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();});

describe('scroll requests follow the current user action',()=>{
  it('resolves the newly opened workspace heading after it mounts',async()=>{
    vi.stubGlobal('fetch',vi.fn(async()=>ok({max_bytes:2097152})));
    const scroll=vi.spyOn(Element.prototype,'scrollIntoView');
    render(<DeliveryWorkspace guidedStep={2}/>);
    fireEvent.click(screen.getByRole('button',{name:'확인할 셀 직접 지정하기'}));
    const heading=await screen.findByRole('heading',{name:'선택한 항목을 고칠 수 있는지 확인'});
    await waitFor(()=>expect(heading).toHaveFocus());
    expect(scroll.mock.instances).toEqual([heading]);
  });

  it.each([false,true])('recalculate reveals its committed summary; leave and return=%s',async(leave)=>{
    let finish!:(response:Response)=>void;
    vi.stubGlobal('fetch',vi.fn(async(_url,init)=>JSON.parse(String(init?.body)).action==='prepare_plan'?new Promise<Response>(resolve=>{finish=resolve;}):ok({payment_mode:'OFF'})));
    const scroll=vi.spyOn(Element.prototype,'scrollIntoView');
    function Harness(){const [job,setJob]=useState(plan);const [step,setStep]=useState<1|2>(2);return <><button onClick={()=>setStep(step===2?1:2)}>toggle step</button><RepairPlanPreview job={job} onJob={setJob} guidedStep={step}/></>;}
    render(<Harness/>);
    fireEvent.click(screen.getByRole('button',{name:'변경 후 계산 영향 다시 확인'}));
    if(leave){fireEvent.click(screen.getByText('toggle step'));fireEvent.click(screen.getByText('toggle step'));}
    await act(async()=>finish(ok({...plan,revision:2})));
    await frame();
    if(leave)expect(scroll).not.toHaveBeenCalled();
    else expect(screen.getByRole('heading',{name:'수정 범위와 계산 검증 완료'})).toHaveFocus();
  });

  it.each([false,true])('grant reveals only the loaded example for its original visit; leave and return=%s',async(leave)=>{
    let finishGrant!:(response:Response)=>void;
    let finishDetail!:(response:Response)=>void;
    vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{
      const action=JSON.parse(String(init?.body)).action;
      if(action==='synthetic_rehearsal')return new Promise<Response>(resolve=>{finishGrant=resolve;});
      if(action==='plan_details')return new Promise<Response>(resolve=>{finishDetail=resolve;});
      return ok(action==='capabilities'?{payment_mode:'OFF'}:{...plan,entitlement_active:true});
    }));
    const scroll=vi.spyOn(Element.prototype,'scrollIntoView');
    function Harness(){const [job,setJob]=useState(plan);const [step,setStep]=useState<1|2>(2);return <><button onClick={()=>setStep(step===2?1:2)}>toggle step</button><RepairPlanPreview job={job} onJob={setJob} guidedStep={step}/></>;}
    render(<Harness/>);
    await screen.findByRole('button',{name:'검증한 수정 예시 보기'});
    fireEvent.click(screen.getByRole('checkbox',{name:'결제가 아닌 합성 파일 시험임을 확인합니다.'}));
    fireEvent.click(screen.getByRole('button',{name:'검증한 수정 예시 보기'}));
    if(leave){fireEvent.click(screen.getByText('toggle step'));fireEvent.click(screen.getByText('toggle step'));}
    await act(async()=>finishGrant(ok({})));
    await waitFor(()=>expect(finishDetail).toBeTypeOf('function'));
    expect(scroll).not.toHaveBeenCalled();
    await act(async()=>finishDetail(ok(detail)));
    const heading=await screen.findByRole('heading',{name:'예를 들면 이렇게 바뀝니다'});
    await frame();
    if(leave)expect(scroll).not.toHaveBeenCalled();
    else {expect(heading).toHaveFocus();expect(scroll.mock.instances).toEqual([heading]);}
  });

  it.each(['leave-return','job-change','cancel'] as const)('does not reveal late READY after %s',async(change)=>{
    let finish!:(response:Response)=>void;
    vi.stubGlobal('fetch',vi.fn(async()=>new Promise<Response>(resolve=>{finish=resolve;})));
    const scroll=vi.spyOn(Element.prototype,'scrollIntoView');
    function Harness(){const [job,setJob]=useState<DeliveryJob>({...plan,approval_status:'APPROVED'});const [mode,setMode]=useState<'approval'|'delivery'>('delivery');return <><button onClick={()=>setMode(mode==='delivery'?'approval':'delivery')}>toggle step</button><button onClick={()=>setJob({...job,job_id:'scroll-b'})}>change job</button><button onClick={()=>setJob({...job,status:'CANCEL_REQUESTED'})}>cancel</button><RepairDelivery job={job} detail={detail} onJob={setJob} mode={mode}/></>;}
    render(<Harness/>);
    fireEvent.click(screen.getByRole('button',{name:'승인한 사본 만들기'}));
    if(change==='leave-return'){fireEvent.click(screen.getByText('toggle step'));fireEvent.click(screen.getByText('toggle step'));await frame();}
    else fireEvent.click(screen.getByText(change==='job-change'?'change job':'cancel'));
    scroll.mockClear();
    await act(async()=>finish(ok(ready)));
    await frame();
    expect(scroll).not.toHaveBeenCalled();
  });
});
