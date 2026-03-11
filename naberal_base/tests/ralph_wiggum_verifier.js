/**
 * RALPH WIGGUM VERIFIER - 무한 검증 루프
 *
 * 파일 변경을 감지하면 자동으로 전수 테스트를 돌리고 피드백을 생성합니다.
 * "바보 같은 실수까지 전부 잡아내는" 반복 검사기
 *
 * 실행: node tests/ralph_wiggum_verifier.js
 * 종료: Ctrl+C
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FRONTEND_BASE = 'http://localhost:3000';
const BACKEND_BASE = 'https://naberalproject-production.up.railway.app';

const WATCH_DIRS = [
  path.resolve(__dirname, '../frontend/src'),
  path.resolve(__dirname, '../src/kis_estimator_core'),
];

const PAGES = [
  { path: '/', name: 'Home', expectRedirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard' },
  { path: '/quote', name: 'Quote' },
  { path: '/ai-manager', name: 'AI Manager' },
  { path: '/erp', name: 'ERP' },
  { path: '/calendar', name: 'Calendar' },
  { path: '/drawings', name: 'Drawings' },
  { path: '/email', name: 'Email' },
  { path: '/settings', name: 'Settings' },
  { path: '/login', name: 'Login' },
];

const CRITICAL_API_ENDPOINTS = [
  { method: 'GET', path: '/v1/health', name: 'Health' },
  { method: 'GET', path: '/v1/health/live', name: 'Liveness' },
  { method: 'GET', path: '/v1/catalog/breakers', name: 'Breaker Catalog' },
  { method: 'GET', path: '/v1/catalog/enclosures', name: 'Enclosure Catalog' },
  { method: 'GET', path: '/v1/erp/customers', name: 'ERP Customers' },
  { method: 'GET', path: '/v1/erp/products', name: 'ERP Products' },
  { method: 'GET', path: '/v1/calendar/events', name: 'Calendar Events' },
  { method: 'GET', path: '/v1/email/oauth/status', name: 'Email OAuth Status' },
];

let runCount = 0;
let lastRunTime = null;
let browser = null;

// ==========================================
// FRONTEND QUICK CHECK
// ==========================================
async function quickFrontendCheck() {
  if (!browser) browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const results = [];

  for (const pageInfo of PAGES) {
    const tab = await context.newPage();
    const jsErrors = [];
    tab.on('pageerror', err => jsErrors.push(err.message.substring(0, 100)));

    try {
      const resp = await tab.goto(`${FRONTEND_BASE}${pageInfo.path}`, {
        waitUntil: 'domcontentloaded',
        timeout: 15000
      });
      const status = resp ? resp.status() : 0;
      const body = await tab.textContent('body').catch(() => '');
      const hasError = body.includes('Application error') || body.includes('Internal Server Error');

      results.push({
        name: pageInfo.name,
        path: pageInfo.path,
        status,
        hasContent: body.trim().length > 10,
        hasError,
        jsErrors: jsErrors.length,
        pass: status === 200 && !hasError && jsErrors.length === 0
      });
    } catch (e) {
      results.push({ name: pageInfo.name, path: pageInfo.path, pass: false, error: e.message.substring(0, 80) });
    }
    await tab.close();
  }

  await context.close();
  return results;
}

// ==========================================
// BACKEND QUICK CHECK
// ==========================================
async function quickBackendCheck() {
  const results = [];

  for (const ep of CRITICAL_API_ENDPOINTS) {
    try {
      const resp = await fetch(`${BACKEND_BASE}${ep.path}`, {
        method: ep.method,
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(10000)
      });
      results.push({ name: ep.name, path: ep.path, status: resp.status, pass: resp.ok });
    } catch (e) {
      results.push({ name: ep.name, path: ep.path, pass: false, error: e.message.substring(0, 80) });
    }
  }

  return results;
}

// ==========================================
// REPORT GENERATOR
// ==========================================
function generateReport(feResults, beResults) {
  const timestamp = new Date().toISOString();
  const fePassed = feResults.filter(r => r.pass).length;
  const bePassed = beResults.filter(r => r.pass).length;

  let report = `\n${'='.repeat(60)}\n`;
  report += `  RALPH WIGGUM VERIFICATION #${runCount}\n`;
  report += `  ${timestamp}\n`;
  report += `${'='.repeat(60)}\n`;

  report += `\n  FRONTEND: ${fePassed}/${feResults.length} PASS\n`;
  for (const r of feResults) {
    const icon = r.pass ? '[OK]' : '[!!]';
    report += `    ${icon} ${r.name} (${r.path}) - HTTP ${r.status || 'ERR'}`;
    if (r.jsErrors > 0) report += ` [${r.jsErrors} JS errors]`;
    if (r.hasError) report += ' [ERROR PAGE]';
    if (r.error) report += ` [${r.error}]`;
    report += '\n';
  }

  report += `\n  BACKEND: ${bePassed}/${beResults.length} PASS\n`;
  for (const r of beResults) {
    const icon = r.pass ? '[OK]' : '[!!]';
    report += `    ${icon} ${r.name} (${r.path}) - HTTP ${r.status || 'ERR'}`;
    if (r.error) report += ` [${r.error}]`;
    report += '\n';
  }

  const totalPass = fePassed + bePassed;
  const totalTests = feResults.length + beResults.length;
  report += `\n  TOTAL: ${totalPass}/${totalTests}`;
  if (totalPass === totalTests) report += ' - ALL CLEAR';
  else report += ` - ${totalTests - totalPass} ISSUES FOUND`;
  report += `\n${'='.repeat(60)}\n`;

  return { report, totalPass, totalTests, issues: totalTests - totalPass };
}

// ==========================================
// FILE WATCHER
// ==========================================
function watchForChanges(callback) {
  let debounce = null;

  for (const dir of WATCH_DIRS) {
    if (!fs.existsSync(dir)) continue;

    fs.watch(dir, { recursive: true }, (eventType, filename) => {
      if (!filename) return;
      // Ignore non-source files
      if (filename.includes('node_modules') || filename.includes('.next')) return;
      if (!filename.match(/\.(tsx?|jsx?|css|py)$/)) return;

      if (debounce) clearTimeout(debounce);
      debounce = setTimeout(() => {
        console.log(`\n  [WATCH] Change detected: ${filename}`);
        callback(filename);
      }, 3000); // 3초 디바운스
    });
  }

  console.log(`  [WATCH] Monitoring ${WATCH_DIRS.length} directories for changes...`);
}

// ==========================================
// MAIN LOOP
// ==========================================
async function runVerification(trigger = 'manual') {
  runCount++;
  console.log(`\n  Starting verification #${runCount} (trigger: ${trigger})...`);

  const feResults = await quickFrontendCheck().catch(e => {
    console.log(`  Frontend check failed: ${e.message}`);
    return [{ name: 'Frontend', pass: false, error: e.message }];
  });

  const beResults = await quickBackendCheck().catch(e => {
    console.log(`  Backend check failed: ${e.message}`);
    return [{ name: 'Backend', pass: false, error: e.message }];
  });

  const { report, totalPass, totalTests, issues } = generateReport(feResults, beResults);
  console.log(report);

  // 결과 파일 저장
  const resultFile = {
    run: runCount,
    trigger,
    timestamp: new Date().toISOString(),
    frontend: feResults,
    backend: beResults,
    summary: { totalPass, totalTests, issues }
  };
  fs.writeFileSync('tests/ralph_wiggum_latest.json', JSON.stringify(resultFile, null, 2));

  lastRunTime = new Date();
  return issues;
}

async function main() {
  console.log('='.repeat(60));
  console.log('  RALPH WIGGUM VERIFIER - Infinite Verification Loop');
  console.log('  "I found problems! And then I found more problems!"');
  console.log('='.repeat(60));
  console.log('');
  console.log('  Commands:');
  console.log('    - File changes auto-trigger verification');
  console.log('    - Ctrl+C to stop');
  console.log('');

  // 초기 실행
  await runVerification('initial');

  // 파일 변경 감지
  watchForChanges(async (filename) => {
    await runVerification(`file-change: ${filename}`);
  });

  // 주기적 체크 (5분마다)
  setInterval(async () => {
    console.log('\n  [PERIODIC] Running scheduled verification...');
    await runVerification('periodic-5min');
  }, 5 * 60 * 1000);

  // 프로세스 종료 처리
  process.on('SIGINT', async () => {
    console.log('\n\n  Ralph Wiggum is going home...');
    console.log(`  Total runs: ${runCount}`);
    if (browser) await browser.close();
    process.exit(0);
  });
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
