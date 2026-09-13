import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { deflateRawSync } from 'node:zlib';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { readFormulaContext, readSourceCells, readSourceSheets } from './workbookEvidence';
import { demoResult } from '../data/demo';
import type { Finding } from '../types';

const ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main';
const rn='http://schemas.openxmlformats.org/officeDocument/2006/relationships';
const finding=(cell='F22',refs=['F21','F23']):Finding=>({...demoResult.findings[0],sheet:'온라인',cell,formula_pattern:{pattern_type:'OUTLIER',formula_region:'F6:F165',dominant_pattern_id:'one',current_pattern_id:'two',neighbor_count:2,evidence_locations:refs,detection_basis:'synthetic',current_limitations:[]}} as unknown as Finding);
const crcTable=Array.from({length:256},(_,v)=>{for(let n=0;n<8;n++)v=v&1?(v>>>1)^0xedb88320:v>>>1;return v>>>0;});
const crc=(b:Buffer)=>b.reduce((v,c)=>crcTable[(v^c)&255]^(v>>>8),0xffffffff)^0xffffffff;
function zip(parts:[string,string][], compressed=true){
 const locals:Buffer[]=[],centrals:Buffer[]=[];let offset=0;
 for(const [name,text] of parts){const n=Buffer.from(name),plain=Buffer.from(text),data=compressed?deflateRawSync(plain):plain;
  const local=Buffer.alloc(30),central=Buffer.alloc(46);local.writeUInt32LE(0x04034b50);central.writeUInt32LE(0x02014b50);
  local.writeUInt16LE(compressed?8:0,8);central.writeUInt16LE(compressed?8:0,10);
  for(const [buffer,at] of [[local,14],[central,16]] as const){buffer.writeUInt32LE(crc(plain)>>>0,at);buffer.writeUInt32LE(data.length,at+4);buffer.writeUInt32LE(plain.length,at+8);}
  local.writeUInt16LE(n.length,26);central.writeUInt16LE(n.length,28);central.writeUInt32LE(offset,42);
  locals.push(local,n,data);centrals.push(central,n);offset+=local.length+n.length+data.length;
 }
 const directory=Buffer.concat(centrals),end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50);end.writeUInt16LE(parts.length,8);end.writeUInt16LE(parts.length,10);end.writeUInt32LE(directory.length,12);end.writeUInt32LE(offset,16);
 return Buffer.concat([...locals,directory,end]);
}
const parts=(cells:string):[string,string][]=>[
 ['xl/workbook.xml',`<workbook xmlns="${ns}" xmlns:r="${rn}"><sheets><sheet name="온라인" r:id="r1"/></sheets></workbook>`],
 ['xl/_rels/workbook.xml.rels',`<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="${rn}/worksheet" Target="worksheets/sheet1.xml"/></Relationships>`],
 ['xl/worksheets/sheet1.xml',`<worksheet xmlns="${ns}"><sheetData><row r="22">${cells}</row></sheetData></worksheet>`],
];
const file=(bytes:Buffer)=>new File([new Uint8Array(bytes)],'synthetic.xlsx');
afterEach(()=>vi.unstubAllGlobals());
describe('bounded original evidence, separate from static API and calculation',()=>{
 it('reads exact frozen complex-file formulas and stored cache without replacing the outlier',async()=>{
  const bytes=readFileSync(resolve(process.cwd(),'../../samples/WorkbookCare_Complex_Validation_2026-09-13/01_다채널정산_혼합오류.xlsx'));
  const network=vi.fn();vi.stubGlobal('fetch',network);
  const context=await readFormulaContext(file(bytes),finding());
  expect(context.target).toEqual({cell:'F22',type:'formula',text:'=C22*D21',cached:'2384'});
  expect(context.comparisons.map(c=>c.text)).toEqual(['=C21*D21','=C23*D23']);
  expect(network).not.toHaveBeenCalled();
  expect((await readFormulaContext(file(bytes),finding('I95',['I94','I96']))).target).toEqual({cell:'I95',type:'number',text:'42'});
  expect((await readFormulaContext(file(bytes),finding('I145',['I144','I146']))).target.type).toBe('blank');
 });
 it.each([true,false])('supports deflated/stored ZIP (%s), escaped text, and shared strings without interpreting formulas',async compressed=>{
  const p=parts('<c r="F22" t="s"><v>0</v></c>');p.push(['xl/sharedStrings.xml',`<sst xmlns="${ns}"><si><t>&lt;img onerror="throw"&gt;=HYPERLINK("x")</t></si></sst>`]);
  const value=await readFormulaContext(file(zip(p,compressed)),finding());
  expect(value.target.type).toBe('text');expect(value.target.text).toBe('<img onerror="throw">=HYPERLINK("x")');
 });
 it('distinguishes shared formula, constant zero, empty text and a true blank',async()=>{
  for(const [xml,type] of [['<f t="shared" si="0"/>','unsupported'],['<v>0</v>','number'],['<is><t/></is>','text'],['','blank']]){
   const data=parts(`<c r="F22"${type==='text'?' t="inlineStr"':''}>${xml}</c>`);
   expect((await readFormulaContext(file(zip(data)),finding())).target.type).toBe(type);
  }
 });
 it.each(['<!DOCTYPE worksheet [<!ENTITY secret "unsafe">]>', '<!ENTITY x "unsafe">'])('rejects XML declarations %s',async declaration=>{
  const p=parts('');p[2][1]=declaration+p[2][1];await expect(readFormulaContext(file(zip(p)),finding())).rejects.toThrow();
 });
 it.each(['../escape.xml','/escape.xml','xl\\escape.xml','xl/%2e%2e/escape.xml'])('rejects archive path %s',async name=>{
  await expect(readFormulaContext(file(zip([...parts(''),[name,'unsafe']])),finding())).rejects.toThrow();
 });
 it('rejects duplicates, external sheet references and malformed shared-string indices',async()=>{
  const duplicate=parts('');duplicate.push(duplicate[0]);await expect(readFormulaContext(file(zip(duplicate)),finding())).rejects.toThrow();
  const external=parts('');external[1][1]=external[1][1].replace('Target="','TargetMode="External" Target="');await expect(readFormulaContext(file(zip(external)),finding())).rejects.toThrow();
  await expect(readFormulaContext(file(zip(parts('<c r="F22" t="s"><v/></c>'))),finding())).rejects.toThrow();
 });
 it('rejects CRC corruption, local metadata mismatch and understated inflated size',async()=>{
  for(const kind of ['crc','method','size']){
   const bytes=zip(parts('<c r="F22"><v>7</v></c>'));const central=bytes.readUInt32LE(bytes.length-6);
   if(kind==='crc'){bytes.writeUInt32LE(0,14);bytes.writeUInt32LE(0,central+16);}
   if(kind==='method')bytes.writeUInt16LE(0,8);
   if(kind==='size'){bytes.writeUInt32LE(1,22);bytes.writeUInt32LE(1,central+24);}
   await expect(readFormulaContext(file(bytes),finding())).rejects.toThrow();
  }
 });
 it('bounds total declared size, XML size and source size before retaining data',async()=>{
  const bytes=zip(parts(''));const central=bytes.readUInt32LE(bytes.length-6);bytes.writeUInt32LE(65*1024*1024,central+24);
  await expect(readFormulaContext(file(bytes),finding())).rejects.toThrow();
  await expect(readFormulaContext(file(zip(parts(' '.repeat(8*1024*1024)))),finding())).rejects.toThrow();
  const large=file(zip(parts('')));Object.defineProperty(large,'size',{value:10*1024*1024+1});await expect(readFormulaContext(large,finding())).rejects.toThrow();
 });
 it('honors cancellation and reports unsupported browsers without fabricating context',async()=>{
  const c=new AbortController();c.abort();await expect(readFormulaContext(file(zip(parts(''))),finding(),c.signal)).rejects.toThrow();
  vi.stubGlobal('DecompressionStream',undefined);await expect(readFormulaContext(file(zip(parts(''))),finding())).rejects.toThrow();
 });
});

describe('reused evidence reader for selectable sheets and proposal cells',()=>{
 it('lists every frozen source sheet and reads requested cells without changing the source',async()=>{
  const bytes=readFileSync(resolve(process.cwd(),'../../samples/WorkbookCare_Complex_Validation_2026-09-13/03_정산수정_연쇄계산.xlsx'));
  const source=file(bytes),network=vi.fn();vi.stubGlobal('fetch',network);
  expect(await readSourceSheets(source)).toEqual(['정산','보존정보']);
  const cells=await readSourceCells(source,'정산',['F8','F31']);
  expect(cells).toEqual([{cell:'F8',type:'formula',text:'=ROUND(C8*D8*(1-E8),0)',cached:'1742'},{cell:'F31',type:'blank',text:'빈 셀'}]);
  expect(network).not.toHaveBeenCalled();
 });
 it('fails closed on excessive requested cells and unknown or external sheet names',async()=>{
  const source=file(zip(parts('')));
  await expect(readSourceCells(source,'온라인',Array.from({length:65},(_,i)=>'A'+(i+1)))).rejects.toThrow();
  for(const name of ['missing','https://example.invalid/sheet'])await expect(readSourceCells(source,name,['F22'])).rejects.toThrow();
  await expect(readSourceCells(source,'온라인',['A0'])).rejects.toThrow();
 });
});
