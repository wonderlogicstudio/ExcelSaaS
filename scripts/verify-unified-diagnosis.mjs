import assert from 'node:assert/strict';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';

const root = resolve('.');
const require = createRequire(import.meta.url);
const { chromium } = require(join(root, 'artifacts/verification/d01/browser-runtime/node_modules/playwright'));
const output = join(root, 'artifacts/verification/d01-unified');
const pictures = join(root, 'artifacts/screenshots/d01-unified');
await mkdir(output, { recursive: true });
await mkdir(pictures, { recursive: true });
const packs = [
  ['samples/WorkbookCare_M4C_Sample_Pack_2026-09-01/WorkbookCare_M4C_Sample_Pack', 'm4c_manifest.json'],
  ['samples/WorkbookCare_M4C_Additional_Pack', 'm4c_additional_manifest.json'],
];
const cases = [];
for (const [directory, manifestFile] of packs) {
  const manifest = JSON.parse(await readFile(join(root, directory, 'expected', manifestFile), 'utf8'));
  for (const scenario of manifest.scenarios) cases.push({
    case: scenario.file.slice(0, 2), path: join(root, directory, 'samples', scenario.file),
    expected: manifest.expected_findings.filter(item => item.file === scenario.file)
      .map(item => [item.sheet, item.cell, item.expected_rule, item.expected_subtype].join('|')).sort(),
  });
}
const controls = JSON.parse(await readFile(join(root, 'artifacts/verification/d01-workbook-packs/api-controls.json'), 'utf8'));
const result = { evidence_kind: 'ACTUAL_LOCAL_BROWSER_UNIFIED_DIAGNOSIS', rows: [], screenshots: [], checks: [] };
const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  for (const width of [1440, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
    const pageErrors = [];
    const calls = [];
    page.on('pageerror', error => pageErrors.push(error.message));
    page.on('request', request => { if (request.url().includes('/v1/')) calls.push(new URL(request.url()).pathname); });
    await page.goto(process.env.M4_UI_BASE_URL || 'http://127.0.0.1:5189');
    const selected = width === 1440 ? cases : cases.filter(c => ['01', '03', '11', '20'].includes(c.case));
    for (const scenario of selected) {
      if (await page.getByRole('button', { name: '다른 파일 검사', exact: true }).count()) {
        await page.getByRole('button', { name: '다른 파일 검사', exact: true }).click();
      }
      const beforeCalls = calls.length;
      const auditResponse = page.waitForResponse(r => r.url().endsWith('/v1/formula-audits') && r.request().method() === 'POST');
      await page.getByLabel('엑셀 파일 선택', { exact: true }).setInputFiles(scenario.path);
      const response = await auditResponse;
      assert.equal(response.status(), 200);
      const payload = await response.json();
      assert.equal(payload.status, 'COMPLETED');
      await page.locator('[data-audit-status=COMPLETED]').waitFor();
      assert.equal(await page.locator('#formula-audit').count(), 0);
      assert.equal(await page.locator('#results .findings-panel').count(), 1);
      const actual = await page.locator('.formula-audit-finding').evaluateAll(elements => elements.map(el => {
        const location = el.querySelector('.formula-audit-finding__location').textContent.split(' · ');
        const rule = el.querySelector('summary code').textContent;
        const type = [...el.querySelectorAll('dt')].find(dt => dt.textContent === '세부 탐지 유형').nextElementSibling.textContent;
        return [...location, rule, type].join('|');
      }).sort());
      assert.deepEqual(actual, scenario.expected);
      assert.deepEqual(calls.slice(beforeCalls), ['/v1/scans', '/v1/formula-audits']);
      const coverage = await page.getByText(/^전체 발견 \d+건/).innerText();
      const expectedFree = controls.rows.find(row => row.synthetic_case === scenario.case).free_findings;
      const total = expectedFree + actual.length;
      assert.ok(coverage.startsWith(`전체 발견 ${total}건 · 반환 상세 ${total}건 · 상세 생략 0건`));
      assert.equal(await page.locator('.diagnosis-breakdown').innerText(), `구조 위험 ${expectedFree}건 · 수식 검토 후보 ${actual.length}건`);
      assert.equal(await page.getByRole('heading', {name: total ? `확인할 항목 ${total}건` : '검사 범위에서 발견된 항목이 없습니다', exact:true}).count(), 1);
      assert.equal(await page.locator('#results .finding-group__locations[open]').count(), 0);
      assert.equal(await page.locator('#results .formula-audit-feedback').count(), 0);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false);
      result.rows.push({ width, total, case: scenario.case, expected: actual.length, actual: actual.length, exact_location_rule_subtype: true, free_findings: expectedFree });
      if (scenario.case === '03') {
        await page.locator('#results').scrollIntoViewIfNeeded();
        const relative = `artifacts/screenshots/d01-unified/collapsed-${width}.png`;
        await page.screenshot({ path: join(root, relative) });
        result.screenshots.push(relative);
        const group = page.getByRole('region', {name:'FORMULA_PATTERN_OUTLIER 유형', exact:true}).locator('.finding-group__locations');
        await group.locator(':scope > summary').focus();
        await page.keyboard.press('Enter');
        assert.equal(await group.getAttribute('open'), '');
        await group.locator('.formula-audit-finding > summary').first().click();
        assert.equal(await group.locator('.formula-audit-finding').first().getAttribute('open'), '');
        if (width === 390) {
          const layout = await group.locator('.formula-audit-finding__summary').first().evaluate(summary => {
            const parent = summary.getBoundingClientRect();
            const boxes = [...summary.children].map(child => child.getBoundingClientRect());
            return boxes.every((box, index) => box.left >= parent.left && box.right <= parent.right + 1
              && (index === 0 || box.top >= boxes[index - 1].bottom));
          });
          assert.equal(layout, true, 'Mobile candidate summary items must remain contained and not overlap');
          result.checks.push({ width, candidate_summary_contained_without_overlap: true });
        }
        const expanded = `artifacts/screenshots/d01-unified/expanded-${width}.png`;
        await page.screenshot({ path: join(root, expanded) });
        result.screenshots.push(expanded);
        const csv = async () => {
          const download = page.waitForEvent('download');
          await page.getByRole('button', { name: '진단 결과 CSV 다운로드', exact: true }).first().click();
          return readFile(await (await download).path());
        };
        const csvBefore = await csv();
        const m4Calls = calls.filter(path => path.endsWith('/formula-audits')).length;
        await page.getByRole('region', {name:'FORMULA_PATTERN_OUTLIER 유형', exact:true}).getByRole('button', { name: '표시된 2개 확인함', exact: true }).click();
        const csvAfter = await csv();
        assert.deepEqual(csvAfter, csvBefore);
        assert.equal(calls.filter(path => path.endsWith('/formula-audits')).length, m4Calls);
        assert.equal(await page.getByText(/^전체 발견 \d+건/).innerText(), coverage);
        result.checks.push({ width, keyboard_disclosure: true, leaf_evidence: true, m4_review_free_csv_unchanged: true, review_network_calls: 0 });
        await page.getByLabel('검사 종류', {exact:true}).selectOption('formula');
        await page.getByLabel('전체 항목 표', {exact:true}).check();
        assert.equal(await page.locator('.finding-table tbody tr').count(), actual.length);

        const readableTitle = await page.locator('.finding-table .formula-audit-finding__summary').first().evaluate(summary => {
          const title = summary.querySelector('strong');
          const style = getComputedStyle(summary);
          const contentWidth = summary.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
          return title.getBoundingClientRect().width >= Math.min(180, contentWidth * .8);
        });
        assert.equal(readableTitle, true, 'Formula title must have readable width inside the table cell');
        result.checks.push({width, formula_table_title_readable:true});
        const tablePath = `artifacts/screenshots/d01-unified/table-${width}.png`;
        await page.locator('.finding-table').scrollIntoViewIfNeeded();
        await page.screenshot({path:join(root,tablePath)});
        result.screenshots.push(tablePath);
        assert.deepEqual(await csv(), csvBefore);
        await page.getByLabel('중요도', {exact:true}).selectOption('info');
        assert.equal(await page.locator('.finding-table tbody tr').count(), 0);
        await page.getByRole('button', {name:'필터 초기화', exact:true}).click();
        assert.equal(await page.locator('.finding-table tbody tr').count(), total);
        assert.deepEqual(await csv(), csvBefore);
        await page.getByLabel('유형별 보기', {exact:true}).check();
        assert.equal(await page.locator('.finding-group').count(), 3);
        assert.equal(await page.locator('.formula-audit-finding select').evaluateAll(nodes=>nodes.filter(n=>n.value==='REVIEWED').length),2);
        assert.equal(await page.locator('details.finding select').evaluateAll(nodes=>nodes.filter(n=>n.value!=='UNREVIEWED').length),0);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false);
        result.checks.push({width, source_filter_table_full_locations:true, combined_filter_empty:true, csv_before_after_filters_identical:true, status_preserved_after_filter_reset:true});

      }
      console.log(JSON.stringify({ width, case: scenario.case, exact: actual.length }));
    }
    assert.deepEqual(pageErrors, []);
    await page.close();
  }
  result.status = 'PASS';
  result.total_unique_expected_candidates = result.rows.filter(row => row.width === 1440).reduce((n,row) => n + row.actual, 0);
  assert.equal(result.total_unique_expected_candidates, 72);
  await writeFile(join(output,'local-browser.json'),JSON.stringify(result,null,2)+'\n');
} finally { await browser.close(); }
