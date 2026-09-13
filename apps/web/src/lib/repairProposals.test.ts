import { describe, expect, it } from 'vitest';
import { demoResult } from '../data/demo';
import { canonicalDecimal, intentVerdict, noRepairIntent, proposalGroups, RP01, RP02 } from './repairProposals';
import type { PlanDetail } from '../components/RepairPlanPreview';
import type { Finding } from '../types';
const f = (sheet:string, cell:string, rule_code='NUMBER_STORED_AS_TEXT', subtype?:string) => ({...demoResult.findings[0],sheet,cell,rule_code,...(subtype?{formula_pattern:{pattern_subtype:subtype}}:{})} as Finding);
const detail:PlanDetail={digest:'synthetic',expires_at:1,patches:[{candidate_id:'one',sheet:'정산',cell:'B2',before:{type:'text',value:'1,200'},after:{type:'number',value:1200}}],impact:[{sheet:'정산',cell:'J10',before:{type:'number',value:0},after:{type:'number',value:'9007199254740993'}}]};
describe('bounded rule proposals and owner intent',()=>{
 it('groups only exact detected cells by sheet and column; existing outliers and constants stay unsupported',()=>{
  const groups=proposalGroups([f('정산','B12'),f('정산','B2'),f('정산','B2'),f('정산','C2'),f('다른','B2'),f('정산','F2','FORMULA_PATTERN_GAP','BLANK_GAP_CANDIDATE'),f('정산','G2','FORMULA_PATTERN_GAP','CONSTANT_OVERRIDE_CANDIDATE'),f('정산','H2','FORMULA_PATTERN_OUTLIER','RANGE_BOUNDARY_DRIFT')]);
  expect(groups.map(g=>[g.sheet,g.column,g.profile,g.findings.map(x=>x.cell)])).toEqual([['정산','B',RP01,['B2','B12']],['정산','C',RP01,['C2']],['다른','B',RP01,['B2']],['정산','F',RP02,['F2']],['정산','G',undefined,['G2']],['정산','H',undefined,['H2']]]);
  expect(groups[5].explanation).toContain('기존 SUM 범위를 바꾸거나');
 });
 it.each([['1.2000','+1.2'],['-0.00','0'],['.001','1e-3'],['1000','1e3']])('compares equivalent decimals exactly %s / %s',(a,b)=>expect(canonicalDecimal(a)).toBe(canonicalDecimal(b)));
 it('never rounds distinct large integers into the same expected value or accepts arbitrary expressions',()=>{
  expect(canonicalDecimal('9007199254740993')).not.toBe(canonicalDecimal('9007199254740992'));
  for(const v of ['=SUM(A1:A3)','NaN','Infinity','1,200','1e999','', '  '])expect(canonicalDecimal(v)).toBeNull();
 });
 it('does not affect a no-opinion plan and separates match, mismatch and unverified scope',()=>{
  expect(intentVerdict(noRepairIntent,detail).status).toBe('none');
  const intent={...noRepairIntent,enabled:true,sheet:'정산',cell:'B2',expected:'1200'};
  expect(intentVerdict(intent,detail).status).toBe('matched');
  expect(intentVerdict({...intent,expected:'1201'},detail).status).toBe('mismatch');
  expect(intentVerdict({...intent,cell:'B3'},detail).status).toBe('unverified');
  expect(intentVerdict({...intent,cell:'J10',expected:'9007199254740993'},detail).status).toBe('matched');
  expect(intentVerdict({...intent,cell:'J10',expected:'9007199254740992'},detail).status).toBe('mismatch');
 });
 it('accepts a reference-cell request only in the exact selected blank-restore policy',()=>{
  const intent={...noRepairIntent,enabled:true,kind:'same_formula' as const,sheet:'정산',cell:'F3',anchor:'F2'};
  const policy={profile:RP02,sheet:'정산',targets:['F3'],anchor:'F2'};
  const restored:PlanDetail={...detail,patches:[{candidate_id:'formula',sheet:'정산',cell:'F3',before:{type:'blank',value:null},after:{type:'formula',value:'=C3*D3'}}]};
  expect(intentVerdict(intent,detail,policy).status).toBe('unverified');
  expect(intentVerdict(intent,restored,policy).status).toBe('matched');
  for(const change of [{profile:RP01},{sheet:'다른'},{targets:['F4']},{anchor:'F4'}])expect(intentVerdict(intent,restored,{...policy,...change}).status).toBe('unverified');
 });
});
