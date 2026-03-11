/**
 * NABERAL KIS Estimator - 프론트엔드 전수 검사 (E2E)
 * 랄프 위검 무한 검증 루프 방식
 *
 * 실행: node tests/e2e_frontend_test.js
 */
const { chromium } = require('playwright');

const BASE = 'http://localhost:3000';

const PAGES = [
  { path: '/', name: 'Home (→ dashboard redirect)', expectRedirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard (대시보드)' },
  { path: '/quote', name: 'Quote (견적 생성)' },
  { path: '/ai-manager', name: 'AI Manager (AI 매니저)' },
  { path: '/erp', name: 'ERP (전사자원관리)' },
  { path: '/calendar', name: 'Calendar (캘린더)' },
  { path: '/drawings', name: 'Drawings (도면 관리)' },
  { path: '/email', name: 'Email (이메일)' },
  { path: '/settings', name: 'Settings (설정)' },
  { path: '/login', name: 'Login (로그인)' },
];

async function testPage(context, pageInfo) {
  const tab = await context.newPage();
  const jsErrors = [];
  const consoleErrors = [];
  const networkErrors = [];
  const warnings = [];

  tab.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text().substring(0, 200));
    if (msg.type() === 'warning') warnings.push(msg.text().substring(0, 200));
  });
  tab.on('pageerror', err => jsErrors.push(err.message.substring(0, 200)));
  tab.on('requestfailed', req => {
    const url = req.url();
    if (!url.includes('favicon') && !url.includes('_next/static'))
      networkErrors.push(`${req.failure()?.errorText || 'unknown'}: ${url.substring(0, 100)}`);
  });

  const result = {
    page: pageInfo.name,
    path: pageInfo.path,
    checks: {},
    issues: [],
    verdict: 'PASS'
  };

  try {
    // 1. 페이지 로딩
    const resp = await tab.goto(`${BASE}${pageInfo.path}`, { waitUntil: 'networkidle', timeout: 30000 });
    result.checks.httpStatus = resp ? resp.status() : 0;
    result.checks.finalUrl = tab.url().replace(BASE, '');

    // 2. 리다이렉트 확인
    if (pageInfo.expectRedirect) {
      result.checks.redirectOk = tab.url().includes(pageInfo.expectRedirect);
      if (!result.checks.redirectOk) result.issues.push(`REDIRECT FAIL: expected ${pageInfo.expectRedirect}, got ${result.checks.finalUrl}`);
    }

    // 3. 콘텐츠 존재 확인
    const bodyText = await tab.textContent('body').catch(() => '');
    result.checks.hasContent = bodyText && bodyText.trim().length > 10;
    if (!result.checks.hasContent) result.issues.push('NO CONTENT: 페이지 콘텐츠 없음');

    // 4. Next.js 에러 페이지 감지
    result.checks.hasErrorPage = bodyText.includes('Application error') ||
      bodyText.includes('Internal Server Error') ||
      bodyText.includes('This page could not be found') ||
      (bodyText.includes('404') && bodyText.length < 200);
    if (result.checks.hasErrorPage) result.issues.push('ERROR PAGE DETECTED');

    // 5. 레이아웃 요소 확인
    result.checks.hasSidebar = await tab.$('[class*="sidebar"], [class*="Sidebar"], aside, nav').then(el => !!el).catch(() => false);

    // 6. 인터랙티브 요소 확인
    result.checks.hasButtons = await tab.$$('button').then(els => els.length).catch(() => 0);
    result.checks.hasInputs = await tab.$$('input, textarea, select').then(els => els.length).catch(() => 0);
    result.checks.hasLinks = await tab.$$('a').then(els => els.length).catch(() => 0);

    // 7. 이미지 깨짐 확인
    const brokenImages = await tab.$$eval('img', imgs =>
      imgs.filter(img => !img.complete || img.naturalWidth === 0).map(img => img.src)
    ).catch(() => []);
    result.checks.brokenImages = brokenImages.length;
    if (brokenImages.length > 0) result.issues.push(`BROKEN IMAGES (${brokenImages.length}): ${brokenImages.slice(0, 2).join(', ')}`);

    // 8. 접근성 기본 체크
    result.checks.hasTitle = await tab.title().then(t => t.length > 0).catch(() => false);
    result.checks.hasLang = await tab.$('html[lang]').then(el => !!el).catch(() => false);

    // 9. 반응형 확인 (모바일 뷰포트)
    await tab.setViewportSize({ width: 375, height: 812 });
    await tab.waitForTimeout(500);
    const mobileContent = await tab.textContent('body').catch(() => '');
    result.checks.mobileRendering = mobileContent && mobileContent.trim().length > 10;
    if (!result.checks.mobileRendering) result.issues.push('MOBILE RENDERING FAIL');
    await tab.setViewportSize({ width: 1920, height: 1080 });

    // 10. JS/Console 에러
    result.checks.jsErrors = jsErrors.length;
    result.checks.consoleErrors = consoleErrors.length;
    result.checks.networkErrors = networkErrors.length;
    if (jsErrors.length > 0) result.issues.push(`JS ERRORS (${jsErrors.length}): ${jsErrors.slice(0, 2).join(' | ')}`);
    if (networkErrors.length > 0) result.issues.push(`NETWORK ERRORS (${networkErrors.length}): ${networkErrors.slice(0, 2).join(' | ')}`);

    // Verdict
    if (result.checks.httpStatus !== 200 || result.checks.hasErrorPage || jsErrors.length > 0) {
      result.verdict = 'FAIL';
    } else if (consoleErrors.length > 0 || networkErrors.length > 0 || !result.checks.hasContent) {
      result.verdict = 'WARN';
    }
  } catch (e) {
    result.verdict = 'FAIL';
    result.issues.push(`EXCEPTION: ${e.message.substring(0, 200)}`);
  }

  await tab.close();
  return result;
}

async function main() {
  console.log('='.repeat(80));
  console.log('  NABERAL FRONTEND E2E TEST - Ralph Wiggum Verification');
  console.log('  Target: ' + BASE);
  console.log('  Date: ' + new Date().toISOString());
  console.log('='.repeat(80));

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });

  let pass = 0, warn = 0, fail = 0;
  const allResults = [];

  for (const page of PAGES) {
    const r = await testPage(context, page);
    allResults.push(r);

    const icon = r.verdict === 'PASS' ? '[PASS]' : r.verdict === 'WARN' ? '[WARN]' : '[FAIL]';
    console.log(`\n${icon} ${r.page}`);
    console.log(`  HTTP: ${r.checks.httpStatus} | URL: ${r.checks.finalUrl || r.path}`);
    console.log(`  Content: ${r.checks.hasContent ? 'O' : 'X'} | Sidebar: ${r.checks.hasSidebar ? 'O' : 'X'} | Buttons: ${r.checks.hasButtons} | Inputs: ${r.checks.hasInputs}`);
    console.log(`  Mobile: ${r.checks.mobileRendering ? 'O' : 'X'} | BrokenImg: ${r.checks.brokenImages} | JSErr: ${r.checks.jsErrors} | NetErr: ${r.checks.networkErrors}`);

    if (r.issues.length > 0) {
      for (const issue of r.issues) console.log(`  >> ${issue}`);
    }

    if (r.verdict === 'PASS') pass++;
    else if (r.verdict === 'WARN') warn++;
    else fail++;
  }

  console.log('\n' + '='.repeat(80));
  console.log(`  RESULT: ${pass} PASS / ${warn} WARN / ${fail} FAIL / ${PAGES.length} TOTAL`);
  console.log('='.repeat(80));

  await browser.close();

  // JSON 결과 저장
  const fs = require('fs');
  fs.writeFileSync('tests/e2e_results.json', JSON.stringify(allResults, null, 2));
  console.log('\nResults saved to tests/e2e_results.json');

  process.exit(fail > 0 ? 1 : 0);
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
