import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const root=resolve('.');const require=createRequire(import.meta.url);
const {chromium}=require(join(root,'artifacts/verification/d01/browser-runtime/node_modules/playwright'));
const output=join(root,'artifacts/verification/d05');const pictures=join(root,'artifacts/screenshots/d05');
await mkdir(output,{recursive:true});await mkdir(pictures,{recursive:true});
const browser=await chromium.launch({channel:'chrome',headless:true});
const evidence={kind:'ACTUAL_PRODUCT_COMPARISON_UI_API_CHILD_AND_DOWNLOADED_REPORTS',rows:[],screenshots:[]};
try{
 for(const [width,kind,caseName] of [[1440,'csv','baseline'],[390,'csv','baseline'],[1440,'xlsx','baseline'],[390,'xlsx','baseline'],[390,'csv','equal'],[1440,'csv','large']]){
  const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce',acceptDownloads:true});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:5189');await page.getByRole('button',{name:'두 파일 비교 사전 확인',exact:true}).click();
  const box=page.getByRole('region',{name:'두 파일 비교 작업',exact:true});
  for(const side of ['A','B'])await box.getByLabel(`비교할 ${side} 파일`,{exact:true}).setInputFiles(join(root,`samples/delivery-v3_2/comparison-${caseName}-${side}.${kind}`));
  await box.getByRole('checkbox').check();
  let response=page.waitForResponse(r=>r.url().endsWith('/v1/delivery')&&r.request().postDataJSON()?.action==='create_comparison');
  await box.getByRole('button',{name:'두 원본 고정하고 기준 선택',exact:true}).click();let result=await response;assert.equal(result.status(),200);const original=await result.json();
  for(const side of ['A','B']){await box.getByLabel(`${side} 비교 기간`,{exact:true}).fill('2026년 9월 합성');await box.getByLabel(`${side} 금액 의미`,{exact:true}).fill('부가세 포함 총액');}
  await box.getByLabel('두 자료의 기간·금액 의미와 KRW 원 단위가 같고, 선택한 헤더·키·금액 열이 맞음을 확인합니다.',{exact:true}).check();
  response=page.waitForResponse(r=>r.url().endsWith('/v1/delivery')&&r.request().postDataJSON()?.action==='prepare_comparison');
  await box.getByRole('button',{name:'비교 가능 범위 확인',exact:true}).click();result=await response;assert.equal(result.status(),200);const preflight=await result.json();assert.equal(preflight.result,null);assert.equal(preflight.purchase_enabled,false);
  if(caseName==='baseline'){
   assert.equal(preflight.preflight.comparable_pair_count,3);assert.equal(preflight.preflight.input_issues.length,2);
   await box.getByLabel('중복·자료오류는 보류하고 모든 원천 행을 보고서에 남기는 제한을 확인했습니다.',{exact:true}).check();
  }
  execFileSync(join(root,'apps/api/.venv/Scripts/python.exe'),['-m','app.delivery_rehearsal','--job-id',original.job_id],{cwd:join(root,'apps/api'),env:process.env,stdio:'pipe'});
  await box.getByRole('button',{name:'비교 작업 상태 확인',exact:true}).click();
  response=page.waitForResponse(r=>r.url().endsWith('/v1/delivery')&&r.request().postDataJSON()?.action==='execute_comparison');
  await box.getByRole('button',{name:'비교 보고서 만들기',exact:true}).click();result=await response;assert.equal(result.status(),200);const complete=await result.json();assert.equal(complete.status,'READY');assert.equal(complete.includes_repaired_workbook,false);
  await box.getByRole('heading',{name:'비교 보고서 두 파일이 준비되었습니다',exact:true}).waitFor();
  const results=box.getByRole('region',{name:'두 파일 비교 결과',exact:true});await results.evaluate(el=>el.scrollIntoView({block:"start"}));
  const expected=caseName==='baseline'?{counts:{MATCHED:2,AMOUNT_DIFF:1,ONLY_A:1,ONLY_B:1,AMBIGUOUS:1,INPUT_ERROR:2},groups:8,rows:14,A:'47,900원',B:'51,000원',key:'0002',delta:'-2,000원'}:caseName==='equal'?{counts:{MATCHED:2,AMOUNT_DIFF:0,ONLY_A:0,ONLY_B:0,AMBIGUOUS:0,INPUT_ERROR:0},groups:2,rows:4,A:'100원',B:'100원'}:{counts:{MATCHED:0,AMOUNT_DIFF:1,ONLY_A:0,ONLY_B:0,AMBIGUOUS:0,INPUT_ERROR:0},groups:1,rows:2,A:'10,000,000,000,000,001원',B:'10,000,000,000,000,000원',key:'K',delta:'1원'};
  assert.deepEqual(complete.result.summary.counts,expected.counts);
  assert.ok((await results.locator('[data-comparison-summary]').innerText()).includes(`전체 ${expected.groups}그룹`));
  assert.equal(await results.locator('[data-comparison-total=A]').innerText(),expected.A);assert.equal(await results.locator('[data-comparison-total=B]').innerText(),expected.B);
  for(const [status,count] of Object.entries(expected.counts))assert.ok((await results.locator(`[data-comparison-status=${status}]>summary`).innerText()).includes(`${count}그룹`));
  let shot=join(pictures,`${width}-${kind}-${caseName}-summary.png`);await page.screenshot({path:shot});evidence.screenshots.push(shot);
  if(expected.key){const group=results.locator('[data-comparison-status=AMOUNT_DIFF]');await group.locator(':scope>summary').click();const record=group.locator(`[data-comparison-key="${expected.key}"]`);await record.locator(':scope>summary').click();assert.equal(await record.locator('[data-comparison-delta]').innerText(),expected.delta);await record.scrollIntoViewIfNeeded();shot=join(pictures,`${width}-${kind}-${caseName}-detail.png`);await page.screenshot({path:shot});evidence.screenshots.push(shot);}
  if(caseName==='baseline'){
   const dup=results.locator('[data-comparison-status=AMBIGUOUS]');await dup.locator(':scope>summary').click();await dup.locator('[data-comparison-key="0004"]>summary').click();await dup.locator('[data-comparison-row]').first().waitFor();assert.equal(await dup.locator('[data-comparison-row]').count(),3);
   const invalid=results.locator('[data-comparison-status=INPUT_ERROR]');await invalid.locator(':scope>summary').click();await invalid.locator('[data-comparison-key="0007"]>summary').click();await invalid.locator('[data-comparison-key="0007"] [data-comparison-row]').first().waitFor();assert.equal(await invalid.locator('[data-comparison-key="0007"] [data-comparison-row]').count(),2);
  }
  await results.getByRole('button',{name:'전체 원천 행 표 보기',exact:true}).click();await results.locator('[data-comparison-row]').first().waitFor();assert.equal(await results.locator('[data-comparison-row]').count(),expected.rows);
  const dir=join(output,'browser-downloads',`${width}-${kind}-${caseName}`);await mkdir(dir,{recursive:true});const files={};
  for(const [kind,label,suffix] of [['COMPARISON_REPORT_XLSX','비교 보고서 XLSX 받기','.xlsx'],['COMPARISON_VERIFICATION_HTML','비교 재검증 HTML 받기','.html']]){
   const event=page.waitForEvent('download');await box.getByRole('button',{name:label,exact:true}).click();const download=await event;const path=join(dir,kind+suffix);await download.saveAs(path);const data=await readFile(path);const hash=createHash('sha256').update(data).digest('hex');assert.equal(hash,complete.delivery.files[kind].sha256);files[kind]={path,sha256:hash,bytes:data.length};
  }
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);
  await page.reload();await page.getByRole('button',{name:'두 파일 비교 사전 확인',exact:true}).click();await page.getByRole('heading',{name:'비교 보고서 두 파일이 준비되었습니다',exact:true}).waitFor();assert.equal(await page.locator('[data-comparison-total=A]').innerText(),expected.A);
  const report=await context.newPage();await report.goto(pathToFileURL(files.COMPARISON_VERIFICATION_HTML.path).href);assert.equal(await report.locator('[data-source-row]').count(),expected.rows);assert.equal(await report.locator('[data-total=A]').innerText(),expected.A.replaceAll(',','').replace('원',''));assert.equal(await report.locator('[data-total=B]').innerText(),expected.B.replaceAll(',','').replace('원',''));assert.ok((await report.locator('[data-summary=groups]').innerText()).includes(`${expected.groups}그룹`));assert.equal(await report.locator('[data-info=spec_hash]').textContent(),complete.spec_hash);
  shot=join(pictures,`${width}-${kind}-${caseName}-html.png`);await report.screenshot({path:shot});evidence.screenshots.push(shot);assert.equal(await report.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  evidence.rows.push({width,kind,caseName,expected,source_pair_hash:original.source_pair_hash,spec_hash:complete.spec_hash,screen_expected_match:true,reconnect:true,files});await context.close();
 }
 await writeFile(join(output,'browser.json'),JSON.stringify(evidence,null,2)+'\n');console.log(JSON.stringify({cases:evidence.rows.length,screenshots:evidence.screenshots.length,actual_downloaded_files:12,expected_values_on_screen:true,exit_code:0}));
}finally{await browser.close();}
