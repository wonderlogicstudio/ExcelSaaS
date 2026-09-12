import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdir,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
const root=resolve('.');const require=createRequire(import.meta.url);
const {chromium}=require(join(root,'artifacts/verification/d01/browser-runtime/node_modules/playwright'));
const output=join(root,'artifacts/verification/d02');const pictures=join(root,'artifacts/screenshots/d02');
await mkdir(output,{recursive:true});await mkdir(pictures,{recursive:true});
const browser=await chromium.launch({channel:'chrome',headless:true});const evidence={kind:'ACTUAL_PRODUCT_UI_AND_API',rows:[],screenshots:[]};
try {
 for(const width of [1440,390]){
  const page=await browser.newPage({viewport:{width,height:1000},reducedMotion:'reduce'});const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:5189');
  await page.getByLabel('엑셀 파일 선택',{exact:true}).setInputFiles(join(root,'samples/delivery-v3_2/delivery-rp01-rp02.xlsx'));
  await page.locator('[data-audit-status=COMPLETED]').waitFor();
  await page.getByRole('button',{name:'수정 범위 사전 확인',exact:true}).click();
  await page.getByLabel('업로드 권한이 있는 합성 파일이며 사전 검사와 임시 보관에 동의합니다.').check();
  await page.getByRole('button',{name:'원본 고정하고 계속',exact:true}).click();
  await page.getByText('원본 고정 완료 · 변경하지 않음 · 1개 시트',{exact:true}).waitFor();
  const box=page.locator('#repair-preflight');
  const check=async(targets,expected,profile='RP01_NUMERIC_TEXT_FIELD_V1',role='AMOUNT')=>{
   await box.getByLabel('수정 종류',{exact:true}).selectOption(profile);
   await box.getByLabel('대상 셀',{exact:true}).fill(targets);
   if(profile.startsWith('RP01'))await box.getByLabel('필드 역할',{exact:true}).selectOption(role);
   else {await box.getByLabel('기준 셀',{exact:true}).fill('F2');await box.getByLabel('기준 셀의 현재 수식',{exact:true}).fill('=ROUND(C2*D2*(1-E2),0)');}
   await box.getByRole('checkbox').check();
   await box.getByRole('button',{name:'선택한 범위 사전 검사',exact:true}).click();
   await box.getByRole('region',{name:'사전 검사 결과'}).waitFor();
   assert.equal(await box.getByText(`형식 조건 충족 ${expected}건`,{exact:true}).count(),1);
   assert.equal(await box.getByRole('button',{name:'견적·수정 실행 준비 중'}).isDisabled(),true);
   evidence.rows.push({width,targets,profile,role,expected_count:expected,actual_count:expected,rows:await box.locator('tbody').innerText()});
  };
  await check('B2, B3',2);
  await box.getByRole('heading',{name:'3. 사전 검사 결과'}).scrollIntoViewIfNeeded();
  const shot=join(pictures,`d02-${width}-numeric.png`);await page.screenshot({path:shot});evidence.screenshots.push(shot);
  await check('A2',0,'RP01_NUMERIC_TEXT_FIELD_V1','ID');
  await check('B4, B5, B6, B7, B8, B9, B10, B11, B12',0);
  await check('F3',1,'RP02_APPROVED_FORMULA_RESTORE_V1');
  await check('G3, H3, I3, J3',0,'RP02_APPROVED_FORMULA_RESTORE_V1');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  await box.getByRole('heading',{name:'3. 사전 검사 결과'}).scrollIntoViewIfNeeded();
  const negative=join(pictures,`d02-${width}-blank-exclusions.png`);await page.screenshot({path:negative});evidence.screenshots.push(negative);
  await box.getByRole('button',{name:'사전 검사 원본 삭제'}).click();
  await box.getByRole('button',{name:'원본 고정하고 계속'}).waitFor();
  assert.deepEqual(errors,[]);await page.close();
 }
 await writeFile(join(output,'browser.json'),JSON.stringify(evidence,null,2)+'\n');
 console.log(JSON.stringify({cases:evidence.rows.length,screenshots:evidence.screenshots.length,expected_values_on_screen:true,exit_code:0}));
} finally {await browser.close();}
