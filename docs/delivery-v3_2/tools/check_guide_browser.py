"""Test offline documentation UI, not the WorkbookCare app or real payment/approval."""
from pathlib import Path
import json, argparse, shutil
from playwright.sync_api import sync_playwright

def main():
    p=argparse.ArgumentParser();p.add_argument('--chromium',default=shutil.which('chromium') or shutil.which('chromium-browser'), help='Optional Chromium executable; otherwise use the Playwright browser');a=p.parse_args()
    root=Path(__file__).resolve().parents[1]; results=[]; loading=[]
    def load_doc(page,path):
        # Direct file:// navigation was blocked by this environment; test the exact
        # local HTML content in a fresh document, without claiming file-mode success.
        page.set_content(path.read_text(encoding='utf-8'))
        loading.append({'document':path.name,'mode':'HTML set_content','reason':'file:// blocked by environment policy; direct mode not verified'})
    def check(name,ok):
        results.append({'name':name,'passed':bool(ok)})
        if not ok:raise AssertionError(name)
    cmds=json.loads((root/'commands.json').read_text(encoding='utf-8'))
    with sync_playwright() as pl:
        browser=pl.chromium.launch(executable_path=a.chromium,headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1400,'height':900},accept_downloads=True)
        page=context.new_page(); load_doc(page,root/'START_HERE.html')
        check('document_loaded',page.title().startswith('WorkbookCare V3.2'))
        check('eight_choices',page.locator('#bundle option').count()==8)
        for c in cmds:
            page.select_option('#bundle',c['id'])
            check(c['id']+'_exact_prompt',page.locator('#prompt').input_value()==c['text'])
            check(c['id']+'_scope',c['scope'] in page.locator('#scope').inner_text())
            check(c['id']+'_md_link',page.locator('#bundle-link').get_attribute('href')==f"bundles/{c['id']}.md")
            with page.expect_download() as d:
                page.click('#save')
            downloaded=d.value
            check(c['id']+'_download_content',Path(downloaded.path()).read_text(encoding='utf-8')==c['text'])
        page.select_option('#bundle','D01')
        page.click('#select')
        check('selection_range',page.locator('#prompt').evaluate('(e)=>e.selectionStart===0 && e.selectionEnd===e.value.length'))
        page.evaluate("Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('denied'))},configurable:true})")
        page.click('#copy'); page.wait_for_timeout(100)
        check('clipboard_denied_fallback','Ctrl+C' in page.locator('#status').inner_text())
        for width in [1400,768,390,320]:
            page.set_viewport_size({'width':width,'height':900})
            check('no_overflow_'+str(width),page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        page.set_viewport_size({'width':1400,'height':900});page.screenshot(path=str(root/'qa/GUIDE_DESKTOP.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(root/'qa/GUIDE_MOBILE.png'),full_page=True)
        page.close(); page=context.new_page(); page.set_viewport_size({'width':390,'height':844})
        load_doc(page,root/'examples/DELIVERY_GUIDE.html')
        check('repair_default_visible',page.locator('#repair').is_visible())
        check('comparison_default_hidden',not page.locator('#comparison').is_visible())
        page.select_option('#product','comparison')
        check('comparison_switch',page.locator('#comparison').is_visible() and not page.locator('#repair').is_visible())
        page.select_option('#product','repair')
        check('repair_switch',page.locator('#repair').is_visible() and not page.locator('#comparison').is_visible())
        check('delivery_mobile_no_overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
        page.set_viewport_size({'width':1400,'height':900});page.screenshot(path=str(root/'qa/DELIVERY_DESKTOP.png'),full_page=True)
        page.close(); page=context.new_page()
        load_doc(page,root/'examples/repair_delivery/verification_DEMO.html')
        check('sample_not_product_claim','실제 WorkbookCare 엔진' in page.locator('body').inner_text())
        check('sample_not_ready','NOT_READY' in page.locator('body').inner_text())
        browser.close()
    data={'scope':'offline documentation UI only','loading':loading, 'checks':results,'passed':sum(x['passed'] for x in results),'failed':sum(not x['passed'] for x in results),'not_tested':['Windows double click','real OS clipboard read/write','production website','mobile physical device','screen reader']}
    (root/'qa/GUIDE_BROWSER_RESULTS.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed':data['passed'],'failed':data['failed']}))
if __name__=='__main__':main()
