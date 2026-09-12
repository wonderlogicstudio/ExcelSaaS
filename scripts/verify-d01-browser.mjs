// Product integration against a separately started loopback API + Vite app.
// Bootstrap: npm install --prefix artifacts/verification/d01/browser-runtime
//   --no-save --package-lock=false --ignore-scripts playwright@1.63.0
// Uses a fresh headless Chrome profile, never an existing user browser session.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.WORKBOOKCARE_PLAYWRIGHT_MODULE
  || join(root, 'artifacts/verification/d01/browser-runtime/node_modules/playwright'));
const base = process.env.D01_WEB_URL || 'http://127.0.0.1:5187';
assert.equal(new URL(base).hostname, '127.0.0.1', 'Only loopback product tests are allowed');
const evidenceDir = join(root, 'artifacts/verification/d01');
const screenshots = join(root, 'artifacts/screenshots/d01');
await mkdir(screenshots, { recursive: true });
const sample = join(root, 'samples/demo-risky-workbook.xlsx');
const capped = join(evidenceDir, 'synthetic-many-findings.xlsx');
const sha = async (path) => createHash('sha256').update(await readFile(path)).digest('hex');
const sourceHashes = { sample: await sha(sample), capped: await sha(capped) };
const result = { evidence_type: 'LOCAL_PRODUCT_BROWSER_AND_API_SYNTHETIC',
  package_examples_used: false, excel_reference_verified: false, pg_verified: false,
  source_hashes_before: sourceHashes, checks: [], screenshots: [], status: 'RUNNING' };
const browser = await chromium.launch({ channel: 'chrome', headless: true });
result.browser_version = browser.version();

try {
  for (const width of [1440, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce', acceptDownloads: true });
    // No cloud requests, external fonts, or analytics are allowed in this test.
    await context.route('**/*', (route) => {
      const url = new URL(route.request().url());
      return ['127.0.0.1', 'localhost'].includes(url.hostname) ? route.continue() : route.abort();
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.name));
    const posts = [];
    page.on('request', (request) => { if (request.method() === 'POST') posts.push(new URL(request.url()).pathname); });
    await page.goto(base);
    await page.getByRole('heading', { name: '승인 기반 수정 패키지', exact: true }).waitFor();
    const repair = page.getByRole('article', { name: '승인 기반 수정 패키지', exact: true });
    const comparison = page.getByRole('article', { name: '두 자료 비교 보고서', exact: true });
    assert.equal(await repair.locator('.product-deliverables li').count(), 3);
    assert.equal(await comparison.locator('.product-deliverables li').count(), 2);
    assert(await repair.getByRole('button').isDisabled());
    assert(await comparison.getByRole('button').isDisabled());
    assert((await comparison.innerText()).includes('비교 자료 B는 정답이 아닙니다'));
    assert((await comparison.innerText()).includes('수정본 미포함'));
    if (width === 1440) {
      await page.getByRole('navigation', { name: '주요 메뉴', exact: true }).getByRole('link', { name: '두 자료 비교', exact: true }).click();
      assert.equal(new URL(page.url()).hash, '#two-file-comparison');
    }
    const productShot = `products-${width}.png`;
    await (width === 1440 ? page.locator('.product-cards') : repair).screenshot({ path: join(screenshots, productShot) });
    result.screenshots.push(`artifacts/screenshots/d01/${productShot}`);

    const upload = async (path) => {
      const pending = page.waitForResponse((response) => response.url().endsWith('/v1/scans') && response.request().method() === 'POST');
      await page.getByLabel('엑셀 파일 선택', { exact: true }).setInputFiles(path);
      const response = await pending;
      assert.equal(response.status(), 200);
      const payload = await response.json();
      await page.getByRole('heading', { name: '전체 Finding 목록', exact: true }).waitFor();
      return payload;
    };
    const scan = await upload(sample);
    assert.equal(await page.locator('details.finding').count(), scan.findings.length);
    assert.equal(await page.locator('#formula-audit').count(), 0);
    assert((await page.locator('.finding-coverage').innerText()).includes(`전체 발견 ${scan.summary.issue_count}건`));
    for (const offering of scan.products) {
      const card = page.getByRole('article', { name: offering.title, exact: true });
      for (const artifact of offering.deliverables) assert((await card.innerText()).includes(artifact.label));
    }
    const csvDownload = async () => {
      const pending = page.waitForEvent('download');
      await page.getByRole('button', { name: '진단 결과 CSV 다운로드', exact: true }).first().click();
      const download = await pending;
      assert.equal(download.suggestedFilename(), scan.products.find((p) => p.product_id === 'FREE_DIAGNOSIS').deliverables[0].filename);
      return readFile(await download.path());
    };
    const csvBefore = await csvDownload();
    assert.deepEqual([...csvBefore.subarray(0, 3)], [239, 187, 191]);
    const groupsRadio = page.getByRole('radio', { name: '유형별 보기', exact: true });
    const tableRadio = page.getByRole('radio', { name: '전체 항목 표', exact: true });
    await groupsRadio.focus();
    await page.keyboard.press('ArrowRight');
    assert(await tableRadio.isChecked());
    assert.equal(await page.locator('.finding-table tbody tr').count(), scan.findings.length);
    assert((await page.getByText(`규칙 기반 우선순위 점수 ${scan.summary.risk_score} / 100`, { exact: true }).innerText()).length > 0);
    assert.deepEqual(await csvDownload(), csvBefore);
    await page.locator('.finding-table').scrollIntoViewIfNeeded();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'Horizontal overflow in full table');
    const tableBounds = await page.locator('.finding-table').boundingBox();
    const captionBounds = await page.locator('.finding-table caption').boundingBox();
    assert(captionBounds.width >= tableBounds.width - 2 && captionBounds.height < 100,
      'Full-table caption must have readable width and height on mobile');
    const tableShot = `table-${width}.png`;
    await page.screenshot({ path: join(screenshots, tableShot) });
    result.screenshots.push(`artifacts/screenshots/d01/${tableShot}`);
    await tableRadio.focus();
    await page.keyboard.press('ArrowLeft');
    assert(await groupsRadio.isChecked());

    const guide = page.locator('.finding-group__guide').first();
    await guide.locator('summary').focus();
    await page.keyboard.press('Enter');
    assert.equal(await guide.getAttribute('open'), '');
    assert(await guide.locator('summary').evaluate((element) => element.matches(':focus-visible')));
    const groupShot = `group-${width}.png`;
    await page.locator('.finding-group').first().screenshot({ path: join(screenshots, groupShot) });
    result.screenshots.push(`artifacts/screenshots/d01/${groupShot}`);
    await page.keyboard.press('Enter');
    assert.equal(await guide.getAttribute('open'), null);
    assert(await guide.locator('summary').evaluate((element) => document.activeElement === element));
    const statusFilter = page.getByRole('combobox', { name: '처리 상태로 보기', exact: true });
    await statusFilter.selectOption('UNREVIEWED');
    await page.locator('.finding-group__heading button').first().focus();
    await page.keyboard.press('Enter');
    assert(await statusFilter.evaluate((element) => document.activeElement === element));
    assert.deepEqual(posts, ['/v1/scans'], 'Group review must not submit approval/payment requests');
    assert(await repair.getByRole('button').isDisabled());
    await page.getByRole('button', { name: '필터 초기화', exact: true }).click();
    assert.equal(await page.locator('details.finding').count(), scan.findings.length);
    assert((await page.locator('details.finding select').first().inputValue()) === 'REVIEWED');

    await page.getByRole('button', { name: '수정 후 다시 검사', exact: true }).click();
    const next = await upload(capped);
    assert(next.finding_counts.omitted_details > 0);
    assert.equal(await page.getByRole('combobox', { name: '처리 상태로 보기', exact: true }).inputValue(), 'all');
    await page.getByRole('heading', { name: '이전 상세에만 있음 · 미탐지 여부 확인 불가', exact: true }).waitFor();
    await page.getByRole('heading', { name: '현재 상세에만 있음 · 신규 여부 확인 불가', exact: true }).waitFor();
    assert.equal(await page.locator('details.finding').count(), next.finding_counts.returned_details);
    const cappedCsv = await csvDownload();
    assert(cappedCsv.toString('utf8').includes(",'=1+1,"), 'Formula-like sheet label must be escaped in the real CSV');
    const truncatedShot = `counts-${width}.png`;
    await page.locator('#all-findings-title').scrollIntoViewIfNeeded();
    await page.screenshot({ path: join(screenshots, truncatedShot) });
    result.screenshots.push(`artifacts/screenshots/d01/${truncatedShot}`);
    await page.getByRole('combobox', { name: '처리 상태로 보기', exact: true }).selectOption('MARKED_NORMAL');
    assert.equal(await page.locator('details.finding').count(), 0);
    assert((await page.locator('.finding-coverage').innerText()).includes('필터 표시 0건'));
    assert(await page.getByText('선택한 조건에 맞는 항목이 없습니다.', { exact: false }).isVisible());
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), 'Horizontal overflow in grouped/empty view');
    assert.deepEqual(errors, []);
    assert.deepEqual(posts, ['/v1/scans', '/v1/scans']);
    result.checks.push({ width, passed: true, initial_leaf_count: scan.findings.length,
      capped_counts: next.finding_counts, csv_group_table_equal: true,
      keyboard_focus_and_native_disclosure: true, group_review_has_no_approval_requests: true,
      paid_actions_disabled: true, m4_not_exposed: true, horizontal_overflow: false,
      synthetic_uploads: posts.length, page_errors: errors.length });
    await context.close();
  }
  result.source_hashes_after = { sample: await sha(sample), capped: await sha(capped) };
  assert.deepEqual(result.source_hashes_after, sourceHashes);
  result.status = 'PASS';
} catch (error) {
  result.status = 'FAIL';
  result.failure = String(error.message).slice(0, 1000);
  process.exitCode = 1;
} finally {
  await browser.close();
  await writeFile(join(evidenceDir, 'browser-result.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result, null, 2));
}
