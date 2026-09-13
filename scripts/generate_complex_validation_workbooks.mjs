import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const out=path.resolve(process.argv[2]);
const specification=JSON.parse(await fs.readFile(path.join(out,'expected/source-spec.json'),'utf8'));
const expected=JSON.parse(await fs.readFile(path.join(out,'expected/expected.json'),'utf8'));
const preview=path.resolve(process.argv[3]);await fs.mkdir(preview,{recursive:true});
async function saveBook(book,file){
 try{await fs.access(file);throw Error('Frozen workbook already exists: '+file);}catch(e){if(e.code!=='ENOENT')throw e;}
 book.recalculate();const xlsx=await SpreadsheetFile.exportXlsx(book);await xlsx.save(file);
}
function formatSheet(sheet,spec){
 sheet.showGridLines=false;const end=spec.last_row;const last=spec.name==='정산'||['온라인','매장','반품'].includes(spec.name)?'M':spec.name==='거래'?'E':spec.name==='월별보고'?'L':String.fromCharCode(64+spec.headers.length);
 const area=sheet.getRange(`A1:${last}${end}`);area.format.font={name:'Arial',size:11,color:'#243447'};area.format.rowHeight=22;area.format.columnWidth=14;area.format.verticalAlignment='center';
 sheet.getRange(`A1:A${end}`).format.columnWidth=20;
 if(spec.name==='보존정보'){sheet.getRange(`B1:B${end}`).format.columnWidth=17;sheet.getRange(`C1:C${end}`).format.columnWidth=55;}
 if(spec.cells.A2&&typeof spec.cells.A2==='string'&&spec.cells.A2.length>8)sheet.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:'#173654'};
 const header=spec.cells.A7===spec.headers[0]?7:spec.cells.A5===spec.headers[0]?5:spec.cells.A4===spec.headers[0]?4:1;
 const c=String.fromCharCode(64+spec.headers.length);sheet.getRange(`A${header}:${c}${header}`).format={fill:'#173654',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:30};
 if(end>40)sheet.freezePanes.freezeRows(header);
 if(['정산','온라인','매장','반품'].includes(spec.name)){
  sheet.getRange(`C8:J${end}`).setNumberFormat('#,##0');sheet.getRange(`E8:E${end}`).setNumberFormat(spec.name==='정산'?'0.00':'#,##0');sheet.getRange('M4:M5').setNumberFormat('0.00');sheet.getRange('M4:M5').format.fill='#FFF2CC';sheet.getRange(`A8:B${end}`).setNumberFormat('@');
  const sumrow=spec.name==='정산'?130:171;sheet.getRange(`A${sumrow}:J${sumrow}`).format.fill='#E9EFF7';sheet.getRange(`A${sumrow}:J${sumrow}`).format.font={bold:true};
 }
 if(spec.name==='거래'){sheet.getRange(`A2:C${end}`).setNumberFormat('@');sheet.getRange(`D2:D${end}`).setNumberFormat('#,##0');sheet.getRange(`D1:D${end}`).format.columnWidth=25;sheet.getRange(`E1:E${end}`).format.columnWidth=25;}
}
for(const [index,spec] of specification.books.entries()){
 const book=Workbook.create();for(const s of spec.sheets)book.worksheets.add(s.name);
 for(const s of spec.sheets){
  const sheet=book.worksheets.getItem(s.name);
  let maxCol=1;for(const cell of [...Object.keys(s.cells),...Object.keys(s.formulas)]){const letters=cell.match(/^[A-Z]+/)[0];let col=0;for(const ch of letters)col=col*26+ch.charCodeAt(0)-64;maxCol=Math.max(maxCol,col);}
  const values=Array.from({length:s.last_row},()=>Array(maxCol).fill(null));
  for(const [cell,value] of Object.entries(s.cells)){const letters=cell.match(/^[A-Z]+/)[0];let c=0;for(const ch of letters)c=c*26+ch.charCodeAt(0)-64;values[Number(cell.match(/\d+$/)[0])-1][c-1]=value;}
  sheet.getRangeByIndexes(0,0,s.last_row,maxCol).values=values;
  // Sparse formula writes preserve intentionally blank and literal replacement cells.
  for(const [cell,formula] of Object.entries(s.formulas))sheet.getRange(cell).formulas=[[formula.replaceAll('거래원장!',"'거래원장'!")]];
  formatSheet(sheet,s);
  if(s.merge)sheet.mergeCells(s.merge);
  if(s.table)sheet.tables.add(s.table.range,true,s.table.name);
  if(s.chart){const chart=sheet.charts.add('bar',sheet.getRange(s.chart.range));chart.title=s.chart.title;chart.setPosition(...s.chart.position);chart.hasLegend=false;chart.yAxis={numberFormatCode:'#,##0',numberFormatSourceLinked:false};}
 }
 book.recalculate();
 for(const [i,s] of spec.sheets.entries()){
  const range=s.name==='월별보고'?'A1:L20':s.name==='정산'||['온라인','매장','반품'].includes(s.name)?'A1:M16':s.name==='보존정보'?'A1:C14':s.name==='거래'?'A1:E12':s.name==='거래원장'?'A1:C12':'A1:F14';
  const png=await book.render({sheetName:s.name,range,scale:1,format:'png'});await fs.writeFile(path.join(preview,`${index+1}-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));
 }
 await saveBook(book,path.join(out,spec.file));
 console.log(JSON.stringify({file:spec.file,sheets:spec.sheets.length,status:'EXPORTED_NOT_PRODUCT_VERIFIED'}));
}
const report=Workbook.create();const summary=report.worksheets.add('예상결과');
const rows=[['시험','입력','예상 결과','확인 범위'],['수식 혼합','01 파일','구조1 + 수식15 = 전체16','4시트·480행·정상 조정행 제외'],['수식 정상','02 파일','구조0 + 수식0','정상 예외40/80/120행'],...Object.entries(expected.repair).map(([name,v])=>[name,'03 파일',`정확 수정 ${v.patch_count}개 / J130 ${v.sum_after.toLocaleString('en-US')}`,v.targets.join(', ')]),['실무 서식','04 파일','수정 차단','표·차트·병합·시트 참조'],['복합키 비교','05 A/B',`${expected.comparison.groups}그룹 / A${expected.comparison.controls.A.rows}행·B${expected.comparison.controls.B.rows}행`,'B 정답 아님 / 미상0처리 금지'],['수식 한도','06 파일','1001개 차단','수정 입력413'],['비교 경계','07 파일','1000행 허용 / 1001행 차단','허용 파일 합계3,503,500']];
summary.getRangeByIndexes(0,0,rows.length,4).values=rows;summary.getRange(`A1:D${rows.length}`).format.font={name:'Arial',size:11};summary.getRange(`A1:D${rows.length}`).format.rowHeight=30;summary.getRange('A1:D1').format={fill:'#173654',font:{bold:true,color:'#FFFFFF'}};summary.getRange('A1:B15').format.columnWidth=23;summary.getRange('C1:D15').format.columnWidth=57;summary.showGridLines=false;
const png=await report.render({sheetName:'예상결과',range:`A1:D${rows.length}`,scale:1,format:'png'});await fs.writeFile(path.join(preview,'expected-results.png'),new Uint8Array(await png.arrayBuffer()));await saveBook(report,path.join(out,'expected/예상결과.xlsx'));
console.log('Complex synthetic workbooks and independent expected summary exported. Product results not used.');
