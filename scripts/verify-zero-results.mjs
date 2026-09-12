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
const manifest = JSON.parse(await readFile(join(pack, 'expected/m4c_manifest.json'), 'utf8'));
const controls = {
  zero: join(pack, 'samples', manifest.scenarios[0].file),
  positive: join(root, 'samples/demo-risky-workbook.xlsx'),
};
const hash = async (path) => createHash('sha256').update(await readFile(path)).digest('hex');
const hashes = Object.fromEntries(await Promise.all(Object.entries(controls).map(async ([key, path]) => [key, await hash(path)])));
const output = join(root, 'artifacts/verification/d01-zero');
const captures = join(root, 'artifacts/screenshots/d01-zero');
await mkdir(output, { recursive: true });
await mkdir(captures, { recursive: true });
const evidence = { kind: 'LOCAL_SYNTHETIC_API_BROWSER', live_beta_verified: false, package_examples_used: false, checks: [], source_hashes: hashes };
const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    await context.route('**/*', (route) => ['127.0.0.1', 'localhost'].includes(new URL(route.request().url()).hostname) ? route.continue() : route.abort());
    const page = await context.newPage();
    const posts = [];
    const errors = [];
    page.on('request', (request) => { if (request.method() === 'POST') posts.push(new URL(request.url()).pathname); });
    page.on('pageerror', (error) => errors.push(error.name));
    await page.goto('http://127.0.0.1:5187');
    const upload = async (path) => {
      const pending = page.waitForResponse((r) => new URL(r.url()).pathname.endsWith('/v1/scans') && r.request().method() === 'POST');
      await page.getByLabel('엑셀 파일 선택', { exact: true }).setInputFiles(path);
      const response = await pending;
      assert.equal(response.status(), 200);
      return response.json();
    };
    const zero = await upload(controls.zero);
    assert.equal(zero.summary.issue_count, 0);
    assert.equal(zero.workbook.formula_count, 301);
    assert.equal(zero.workbook.scanned_cell_count, 832);
    await page.getByRole('heading', { name: '무료 구조 검사: 발견 0건', exact: true }).waitFor();
    const note = page.getByRole('note', { name: '발견 0건 해석' });
    assert((await note.innerText()).includes('수식 검증을 통과했다는 뜻은 아닙니다.'));
    assert((await page.locator('.results-header').innerText()).includes('수식 문자열 301개'));
    assert.equal(await page.locator('#formula-audit').count(), 0);
    assert.equal(await page.locator('details.finding').count(), 0);
    assert((await page.getByRole('article', { name: '승인 기반 수정 패키지', exact: true }).getByRole('button').isDisabled()));
    await page.locator('.results-header').evaluate((element) => element.scrollIntoView({ block: 'start', behavior: 'instant' }));
    await page.evaluate(() => window.scrollBy(0, -(document.querySelector('header').getBoundingClientRect().height + 16)));
    const titleBox = await page.locator('#results-title').boundingBox();
    const headerBox = await page.locator('header').boundingBox();
    assert(titleBox.y >= headerBox.y + headerBox.height);
    await page.screenshot({ path: join(captures, `zero-${width}.png`) });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.getByRole('button', { name: '다른 파일 검사', exact: true }).click();
    const positive = await upload(controls.positive);
    assert.equal(positive.summary.issue_count, 12);
    await page.getByRole('heading', { name: '중요한 구조적 문제가 발견됐습니다.', exact: true }).waitFor();
    assert.equal(await page.locator('details.finding').count(), 12);
    assert.equal(await page.getByRole('note', { name: '발견 0건 해석' }).count(), 0);
    assert.deepEqual(posts, ['/v1/scans', '/v1/scans']);
    assert.deepEqual(errors, []);
    evidence.checks.push({ width, zero_free_findings: 0, zero_formula_strings: 301, zero_scanned_cells: 832,
      positive_findings: 12, formula_audit_requests: 0, browser_errors: 0, horizontal_overflow: false,
      screenshot: `artifacts/screenshots/d01-zero/zero-${width}.png` });
    await context.close();
  }
  for (const [key, path] of Object.entries(controls)) assert.equal(await hash(path), hashes[key]);
  evidence.status = 'PASS';
  await writeFile(join(output, 'browser.json'), JSON.stringify(evidence, null, 2) + '\n');
  process.stdout.write(JSON.stringify(evidence) + '\n');
} finally { await browser.close(); }
