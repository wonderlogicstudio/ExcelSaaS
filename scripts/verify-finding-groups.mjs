// Actual local browser/API controls; isolated Chrome profile and synthetic files only.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(import.meta.url);
const { chromium } = require(join(root, 'artifacts/verification/d01/browser-runtime/node_modules/playwright'));
const pack = join(root, 'samples/WorkbookCare_M4C_Sample_Pack_2026-09-01/WorkbookCare_M4C_Sample_Pack');
const extra = join(root, 'samples/WorkbookCare_M4C_Additional_Pack');
const mainManifest = JSON.parse(await readFile(join(pack, 'expected/m4c_manifest.json'), 'utf8'));
const extraManifest = JSON.parse(await readFile(join(extra, 'expected/m4c_additional_manifest.json'), 'utf8'));
const files = {
  case03: join(pack, 'samples', mainManifest.scenarios[2].file),
  case11: join(extra, 'samples', extraManifest.scenarios[0].file),
  zero: join(pack, 'samples', mainManifest.scenarios[0].file),
  demo: join(root, 'samples/demo-risky-workbook.xlsx'),
};
const sha = async (path) => createHash('sha256').update(await readFile(path)).digest('hex');
const hashes = Object.fromEntries(await Promise.all(Object.entries(files).map(async ([key, path]) => [key, await sha(path)])));
const output = join(root, 'artifacts/verification/d01-groups');
const captures = join(root, 'artifacts/screenshots/d01-groups');
await mkdir(output, { recursive: true });
await mkdir(captures, { recursive: true });
const evidence = { kind: 'ACTUAL_LOCAL_BROWSER_API_SYNTHETIC', authenticated_beta_ui_verified: false,
  excel_calculation_or_pg_verified: false, input_hashes: hashes, checks: [] };
const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce', acceptDownloads: true });
    await context.route('**/*', (route) => ['127.0.0.1', 'localhost'].includes(new URL(route.request().url()).hostname) ? route.continue() : route.abort());
    const page = await context.newPage();
    const posts = [];
    const errors = [];
    page.on('request', (request) => { if (request.method() === 'POST') posts.push(new URL(request.url()).pathname); });
    page.on('pageerror', (error) => errors.push(error.name));
    await page.goto('http://127.0.0.1:5187');
    const upload = async (path, expectedCount) => {
      const pending = page.waitForResponse((r) => new URL(r.url()).pathname.endsWith('/v1/scans') && r.request().method() === 'POST');
      await page.getByLabel('엑셀 파일 선택', { exact: true }).setInputFiles(path);
      const response = await pending;
      assert.equal(response.status(), 200);
      const payload = await response.json();
      assert.equal(payload.summary.issue_count, expectedCount);
      await page.getByText(`전체 발견 ${expectedCount}건 · 반환 상세 ${expectedCount}건 · 상세 생략 0건 · 필터 표시 ${expectedCount}건`, { exact: true }).waitFor();
      return payload;
    };
    const csv = async () => {
      const pending = page.waitForEvent('download');
      await page.getByRole('button', { name: '진단 결과 CSV 다운로드', exact: true }).first().click();
      return readFile(await (await pending).path());
    };
    const scan = await upload(files.case03, 49);
    const originalCsv = await csv();
    assert.equal(originalCsv.toString('utf8').trim().split('\r\n').length, 50);
    const group = page.getByRole('region', { name: 'FORMULA_DEEP_NESTING 유형' });
    assert.equal(await page.locator('.finding-group').count(), 1);
    const locations = group.locator('.finding-group__locations');
    const toggle = locations.locator(':scope > summary');
    assert.equal(await locations.getAttribute('open'), null);
    assert.equal(await locations.locator('.finding__summary:visible').count(), 0);
    assert.equal(await group.getByRole('heading', { name: scan.findings[0].title, exact: true }).count(), 1);
    await group.screenshot({ path: join(captures, `collapsed-${width}.png`) });
    await toggle.focus();
    await page.keyboard.press('Enter');
    assert.equal(await locations.getAttribute('open'), '');
    assert.equal(await locations.locator('.finding__summary:visible').count(), 49);
    assert.equal(await group.getByRole('heading', { name: scan.findings[0].title, exact: true }).count(), 1);
    const actualLocations = await locations.locator('.finding__location').allTextContents();
    assert.deepEqual(actualLocations, scan.findings.map((f) => [f.sheet, f.cell].filter(Boolean).join(' · ')));
    const first = locations.locator('details.finding').first();
    await first.locator(':scope > summary').focus();
    await page.keyboard.press('Enter');
    assert(await first.getByRole('combobox').isVisible());
    assert((await first.locator('.finding__details').innerText()).includes(scan.findings[0].description));
    await first.locator(':scope > summary').focus();
    await page.keyboard.press('Enter');
    await toggle.evaluate((element) => element.scrollIntoView({ block: 'start', behavior: 'instant' }));
    await page.evaluate(() => window.scrollBy(0, -(document.querySelector('header').getBoundingClientRect().height + 16)));
    await page.screenshot({ path: join(captures, `expanded-${width}.png`) });
    await toggle.focus();
    await page.keyboard.press('Space');
    assert.equal(await locations.getAttribute('open'), null);
    assert(await toggle.evaluate((element) => element === document.activeElement && element.matches(':focus-visible')));
    assert.deepEqual(await csv(), originalCsv);
    await page.getByRole('radio', { name: '전체 항목 표', exact: true }).click();
    assert.equal(await page.locator('.finding-table tbody tr').count(), 49);
    assert.deepEqual(await csv(), originalCsv);
    await page.getByRole('radio', { name: '유형별 보기', exact: true }).click();
    assert.equal(await locations.getAttribute('open'), null);
    const sheet = scan.findings[0].sheet;
    const filtered = scan.findings.filter((finding) => finding.sheet === sheet).length;
    await page.getByRole('combobox', { name: '시트', exact: true }).selectOption(`sheet:${sheet}`);
    assert((await toggle.innerText()).includes(`개별 위치 ${filtered}개 보기`));
    assert.deepEqual(await csv(), originalCsv);
    assert.equal(await locations.getAttribute('open'), null);
    await page.getByRole('button', { name: '필터 초기화', exact: true }).click();
    assert((await toggle.innerText()).includes('개별 위치 49개 보기'));
    assert((await page.getByText(`규칙 기반 우선순위 점수 ${scan.summary.risk_score} / 100`, { exact: true }).innerText()).length > 0);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.getByRole('button', { name: '다른 파일 검사', exact: true }).click();
    await upload(files.case11, 59);
    assert.equal(await page.locator('.finding-group').count(), 1);
    assert.equal(await page.locator('.finding-group__locations[open]').count(), 0);
    await page.getByRole('button', { name: '다른 파일 검사', exact: true }).click();
    const demo = await upload(files.demo, 12);
    assert.equal(await page.locator('.finding-group').count(), new Set(demo.findings.map((f) => f.rule_code)).size);
    assert.equal(await page.locator('.finding-group__locations[open]').count(), 0);
    await page.getByRole('button', { name: '다른 파일 검사', exact: true }).click();
    await upload(files.zero, 0);
    assert.equal(await page.locator('.finding-group').count(), 0);
    assert.equal(await page.locator('#formula-audit').count(), 0);
    assert.deepEqual(posts, Array(4).fill('/v1/scans'));
    assert.deepEqual(errors, []);
    evidence.checks.push({ width, case03_findings: 49, case03_groups: 1, case11_findings: 59, case11_groups: 1,
      default_locations_hidden: true, all_49_locations_preserved: true, common_title_occurrences: 1,
      keyboard_expand_collapse_focus: 'PASS', csv_bytes_unchanged_across_views_and_filters: true,
      individual_evidence_and_status_accessible: true, new_scan_disclosures_reset: true,
      positive_control_findings: 12, zero_control_findings: 0, formula_audit_requests: 0,
      browser_errors: 0, horizontal_overflow: false,
      screenshots: [`artifacts/screenshots/d01-groups/collapsed-${width}.png`, `artifacts/screenshots/d01-groups/expanded-${width}.png`] });
    await context.close();
  }
  for (const [key, path] of Object.entries(files)) assert.equal(await sha(path), hashes[key]);
  evidence.status = 'PASS';
  await writeFile(join(output, 'browser.json'), JSON.stringify(evidence, null, 2) + '\n');
  process.stdout.write(JSON.stringify(evidence) + '\n');
} finally { await browser.close(); }
