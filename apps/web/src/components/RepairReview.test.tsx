import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useState } from 'react';
import { ProgressiveFindingViews } from './ProgressiveFindingViews';
import type { Finding } from '../types';
import { RepairReview } from './RepairReview';
import { DeliveryWorkspace, type DeliveryJob } from './DeliveryWorkspace';
import { demoResult } from '../data/demo';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
describe('diagnosis selection to existing preflight',()=>{
 it('bulk selection adds only displayed findings without changing handling status',()=>{
   const status=vi.fn();const f={...demoResult.findings[0],rule_code:'NUMBER_STORED_AS_TEXT',sheet:'Data',cell:'B2',finding_key:'one'};
   const hidden={...f,cell:'B3',finding_key:'two'};
   function Harness(){const [selected,setSelected]=useState<Finding[]>([]);return <><ProgressiveFindingViews findings={[f]} allFindings={[f,hidden]} mode="groups" statuses={{}} categoryLabel={()=>'구조 위험'} onStatusChange={status} onReviewGroup={status} reviewSelection={{findings:selected,locked:false,toggle:row=>setSelected(old=>[...old,row])}}/><output aria-label="검토한 위치">{selected.map(row=>row.cell).join(',')}</output></>}
   render(<Harness/>);fireEvent.click(document.querySelector('.diagnosis-type__disclosure > summary')!);
   fireEvent.click(screen.getByRole('button',{name:'표시된 1개 수정 검토 선택'}));
   expect(screen.getByLabelText('검토한 위치')).toHaveTextContent('B2');
   expect(screen.getByLabelText('검토한 위치')).not.toHaveTextContent('B3');
   expect(screen.getByRole('button',{name:'표시된 1개 수정 검토 선택'})).toBeDisabled();expect(status).not.toHaveBeenCalled();
 });
 it('keeps unsupported choices visible and sends only the chosen profile/sheet subset',()=>{
   const onPrepare=vi.fn();const f=demoResult.findings[0];
   const findings=[{...f,rule_code:'NUMBER_STORED_AS_TEXT',sheet:'Data',cell:'B2'},{...f,rule_code:'NUMBER_STORED_AS_TEXT',sheet:'Other',cell:'B3'},{...f,rule_code:'FORMULA_REF_ERROR',sheet:'Data',cell:'F8'}];
   render(<RepairReview selection={{findings,locked:false,toggle:vi.fn()}} available hasFile onPrepare={onPrepare}/>);
   expect(screen.getByText('자동 수정 미지원·판단 필요 1건')).toBeVisible();
   fireEvent.click(screen.getByRole('button',{name:'Data · 1개 숫자 셀 수정 가능 여부 확인'}));
   expect(onPrepare).toHaveBeenCalledWith({profile:'RP01_NUMERIC_TEXT_FIELD_V1',sheet:'Data',targets:['B2']});
   expect(screen.getByText('Data · F8')).toBeVisible();
 });
 it('seeds cells without business consent, anchor, payment or approval and freezes review selection after upload',async()=>{
   const sourceFixed=vi.fn();const actions:Record<string,unknown>[]=[];
   const job:DeliveryJob={job_id:'synthetic-job',revision:1,source_hash:'synthetic',status:'INPUT_READY',expires_at:Date.now()/1000+900,sheets:[{name:'First',cell_count:1},{name:'Data',cell_count:4}],preflight:null,purchase_enabled:false,source_unchanged:true};
   vi.stubGlobal('fetch',vi.fn(async(_url,init)=>{const body=JSON.parse(init.body);actions.push(body);return{ok:true,json:async()=>body.action==='capabilities'?{max_bytes:2097152}:job};}));
   const view=render(<DeliveryWorkspace file={new File(['synthetic'],'fixture.xlsx')} reviewDraft={{profile:'RP02_APPROVED_FORMULA_RESTORE_V1',sheet:'Data',targets:['F3','F5']}} onSourceFixed={sourceFixed}/>);
   await waitFor(()=>expect(screen.getByRole('button',{name:'원본 고정하고 계속'})).toBeDisabled());
   fireEvent.click(screen.getByRole('checkbox',{name:'업로드 권한이 있는 합성 파일이며 사전 검사와 임시 보관에 동의합니다.'}));
   fireEvent.click(screen.getByRole('button',{name:'원본 고정하고 계속'}));
   await waitFor(()=>expect(screen.getByLabelText('대상 셀')).toHaveValue('F3, F5'));
   expect(screen.getByLabelText('대상 시트')).toHaveValue('Data');
   expect(screen.getByLabelText('기준 셀')).toHaveValue('');
   expect(screen.getByLabelText('기준 셀의 현재 수식')).toHaveValue('');
   expect(screen.getByRole('checkbox',{name:'기준 수식을 확인했으며 선택한 빈 셀에도 같은 업무 규칙을 적용합니다.'})).not.toBeChecked();
   expect(screen.getByRole('button',{name:'선택한 범위 사전 검사'})).toBeDisabled();
   expect(sourceFixed).toHaveBeenCalledWith(true);
   view.rerender(<DeliveryWorkspace reviewDraft={{profile:'RP01_NUMERIC_TEXT_FIELD_V1',sheet:'First',targets:['B2']}} onSourceFixed={sourceFixed}/>);
   expect(screen.getByLabelText('대상 셀')).toHaveValue('F3, F5');
   expect(actions.map(a=>a.action)).toEqual(['capabilities','create_input']);
 });
});
