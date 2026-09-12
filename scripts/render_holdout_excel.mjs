import {createRequire} from 'node:module';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
const root=resolve('.');const require=createRequire(import.meta.url);
const {chromium}=require(join(root,'artifacts/verification/d01/browser-runtime/node_modules/playwright'));
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 for(const name of ['RP01-holdout-excel','RP02-holdout-excel','comparison-holdout-excel']){
  const page=await browser.newPage({viewport:{width:1440,height:1100}});
  await page.goto(pathToFileURL(join(root,'artifacts/verification/d08',name+'.pdf')).href);
  await page.waitForTimeout(2200);
  await page.screenshot({path:join(root,'artifacts/screenshots/d08',name+'.png')});
  await page.close();
 }
 console.log('Three actual Excel-exported PDFs rendered in Chrome; screenshots saved for visual inspection.');
}finally{await browser.close()}
