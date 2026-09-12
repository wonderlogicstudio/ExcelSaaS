import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const root=resolve('.');const require=createRequire(import.meta.url);
const {chromium}=require(join(root,'artifacts/verification/d01/browser-runtime/node_modules/playwright'));
const output=join(root,'artifacts/verification/d04');const pictures=join(root,'artifacts/screenshots/d04');
await mkdir(output,{recursive:true});await mkdir(pictures,{recursive:true});
const expected=JSON.parse(await readFile(join(root,'samples/delivery-v3_2/expected.json'),'utf8'));
const browser=await chromium.launch({channel:'chrome',headless:true});const evidence={kind:'ACTUAL_PRODUCT_SCREEN_APPROVAL_API_ENGINE_AND_THREE_DOWNLOADED_FILES',rows:[],screenshots:[]};
try{
 for(const width of [1440,390])for(const profile of ['RP01','RP02']){
  const page=await browser.newPage({viewport:{width,height:1000},reducedMotion:'reduce',acceptDownloads:true});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:5189');
  await page.getByLabel('엑셀 파일 선택',{exact:true}).setInputFiles(join(root,'samples/delivery-v3_2/delivery-rp01-rp02.xlsx'));
  await page.locator('[data-audit-status=COMPLETED]').waitFor();
  await page.getByRole('button',{name:'수정 범위 사전 확인',exact:true}).click();
  await page.getByLabel('업로드 권한이 있는 합성 파일이며 사전 검사와 임시 보관에 동의합니다.').check();
  const created=page.waitForResponse(r=>r.url().endsWith('/v1/delivery')&&r.request().postDataJSON()?.action==='create_input');
  await page.getByRole('button',{name:'원본 고정하고 계속',exact:true}).click();
  const initial=await(await created).json();
  execFileSync(join(root,'apps/api/.venv/Scripts/python.exe'),['-m','app.delivery_rehearsal','--job-id',initial.job_id],{cwd:join(root,'apps/api'),env:process.env,stdio:'pipe'});
  const box=page.locator('#repair-preflight');
  await box.getByRole('button',{name:'최신 작업 상태 확인'}).click();
  await box.getByLabel('수정 종류',{exact:true}).selectOption(profile==='RP01'?'RP01_NUMERIC_TEXT_FIELD_V1':'RP02_APPROVED_FORMULA_RESTORE_V1');
  await box.getByLabel('대상 셀',{exact:true}).fill(profile==='RP01'?'B2, B3':'F3');
  if(profile==='RP01')await box.getByLabel('필드 역할',{exact:true}).selectOption('AMOUNT');
  else{await box.getByLabel('기준 셀',{exact:true}).fill('F2');await box.getByLabel('기준 셀의 현재 수식',{exact:true}).fill(expected.rp02.formula_after.replaceAll('3','2'));}
  await box.getByRole('checkbox').check();
  await box.getByRole('button',{name:'선택한 범위 사전 검사',exact:true}).click();
  await box.getByRole('button',{name:'선택한 변경계획 계산',exact:true}).click();
  await box.getByText('변경계획 계산 검증 완료',{exact:true}).waitFor();
  await box.getByRole('button',{name:'정확한 변경계획 보기'}).click();
  const delivery=box.getByRole('region',{name:'변경 승인과 납품'});
  await delivery.waitFor();
  assert.equal(await delivery.getByRole('button',{name:'이 변경계획 승인',exact:true}).isDisabled(),true);
  assert.equal(await delivery.getByRole('button',{name:'승인한 사본 만들기',exact:true}).count(),0);
  if(profile==='RP01'){
   for(const [cell,value] of Object.entries(expected.rp01.type_values))assert.ok((await box.locator(`[data-plan-cell=${cell}]`).innerText()).includes(value.toLocaleString('ko-KR')));
   assert.ok((await box.locator('[data-impact-cell=H2]').innerText()).includes(expected.rp01.after_H2.toLocaleString('ko-KR')));
  }else{
   assert.ok((await box.locator('[data-plan-cell=F3]').innerText()).includes(expected.rp02.formula_after));
   assert.ok((await box.locator('[data-impact-cell=F3]').innerText()).includes(expected.rp02.after_F3.toLocaleString('ko-KR')));
   assert.ok((await box.locator('[data-impact-cell=F12]').innerText()).includes(expected.rp02.after_F12.toLocaleString('ko-KR')));
  }
  await delivery.scrollIntoViewIfNeeded();
  let shot=join(pictures,`${width}-${profile}-approval.png`);await page.screenshot({path:shot});evidence.screenshots.push(shot);
  await delivery.getByRole('checkbox').check();await delivery.getByRole('button',{name:'이 변경계획 승인',exact:true}).click();
  const result=page.waitForResponse(r=>r.url().endsWith('/v1/delivery')&&r.request().postDataJSON()?.action==='execute');
  await delivery.getByRole('button',{name:'승인한 사본 만들기',exact:true}).click();
  const response=await result;assert.equal(response.status(),200);const completed=await response.json();assert.equal(completed.status,'READY');assert.equal(completed.payment_status,'NOT_PURCHASED');
  await delivery.getByRole('heading',{name:`승인한 ${profile==='RP01'?2:1}개 변경의 세 파일이 준비되었습니다`,exact:true}).waitFor();
  await delivery.scrollIntoViewIfNeeded();shot=join(pictures,`${width}-${profile}-ready.png`);await page.screenshot({path:shot});evidence.screenshots.push(shot);
  const dir=join(output,'browser-downloads',String(width));await mkdir(dir,{recursive:true});const files={};
  for(const [kind,label,suffix] of [['REPAIRED_XLSX','수정본 XLSX 받기','.xlsx'],['CHANGES_XLSX','변경내역 XLSX 받기','.xlsx'],['VERIFICATION_HTML','재검증 HTML 받기','.html']]){
   const event=page.waitForEvent('download');await delivery.getByRole('button',{name:label,exact:true}).click();const download=await event;const path=join(dir,`${profile}-${kind}${suffix}`);await download.saveAs(path);
   const bytes=await readFile(path);const hash=createHash('sha256').update(bytes).digest('hex');assert.equal(hash,completed.delivery.files[kind].sha256);files[kind]={path,sha256:hash,bytes:bytes.length};
  }
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);
  const report=await browser.newPage({viewport:{width,height:1000},reducedMotion:'reduce'});await report.goto(pathToFileURL(files.VERIFICATION_HTML.path).href);
  assert.ok((await report.locator(`[data-result-cell=${profile==='RP01'?'H2':'F12'}]`).innerText()).includes((profile==='RP01'?expected.rp01.after_H2:expected.rp02.after_F12).toLocaleString('ko-KR')));
  assert.equal(await report.locator('[data-change-cell]').count(),profile==='RP01'?2:1);
  assert.equal(await report.locator('[data-provenance=source_hash]').textContent(),initial.source_hash);
  assert.equal(await report.locator('[data-provenance=output_hash]').textContent(),files.REPAIRED_XLSX.sha256);
  await report.locator('[data-result-cell]').last().scrollIntoViewIfNeeded();shot=join(pictures,`${width}-${profile}-verification.png`);await report.screenshot({path:shot});evidence.screenshots.push(shot);
  assert.equal(await report.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  evidence.rows.push({width,profile,source_hash:initial.source_hash,plan_digest:completed.plan_summary.digest,separate_approval_required:true,all_three_downloaded:true,screen_expected_match:true,ready:true,files});
  await report.close();await page.close();
 }
 await writeFile(join(output,'browser.json'),JSON.stringify(evidence,null,2)+'\n');console.log(JSON.stringify({cases:evidence.rows.length,screenshots:evidence.screenshots.length,actual_downloaded_files:12,expected_values_on_screen:true,exit_code:0}));
}finally{await browser.close();}
