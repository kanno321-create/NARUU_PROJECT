/**
 * Diagnostic: Why does "불러오는 중" persist?
 * Captures console logs, network requests, and DOM state
 */
const { chromium } = require('playwright');

const FRONTEND = 'http://localhost:3000';
const BACKEND = 'https://naberalproject-production.up.railway.app';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });

  // Step 1: Get auth token via Node.js
  let authToken = null;
  try {
    const resp = await fetch(`${BACKEND}/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'ceo', password: 'ceo1234' }),
      signal: AbortSignal.timeout(10000)
    });
    const data = await resp.json();
    authToken = data.access_token;
    console.log(`[1] Token acquired: ${authToken ? 'YES' : 'NO'}`);
  } catch (e) {
    console.log(`[1] Token FAILED: ${e.message}`);
  }

  // Step 2: addInitScript for localStorage
  await context.addInitScript((token) => {
    localStorage.setItem('kis-access-token', token);
    localStorage.setItem('kis-refresh-token', token);
    localStorage.setItem('kis-token-expiry', String(Date.now() + 3600000));
    // CSS override
    const s = document.createElement('style');
    s.textContent = '[style*="visibility: hidden"],[style*="visibility:hidden"]{visibility:visible!important}';
    if (document.head) document.head.appendChild(s);
    else document.addEventListener('DOMContentLoaded', () => document.head.appendChild(s));
  }, authToken);

  // Step 3: Route interception with logging
  let routeCount = 0;
  await context.route(`${BACKEND}/**`, async (route) => {
    routeCount++;
    const url = route.request().url();
    console.log(`  [ROUTE #${routeCount}] ${route.request().method()} ${url.replace(BACKEND, '')}`);

    if (url.includes('/v1/auth/me')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-user', username: 'ceo', name: '대표이사',
          role: 'ceo', status: 'active'
        })
      });
    }
    // All other Railway calls: return empty 200
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: '[]'
    });
  });

  // Step 4: Also try glob pattern route
  await context.route('**/v1/auth/**', async (route) => {
    console.log(`  [GLOB-ROUTE] ${route.request().method()} ${route.request().url()}`);
    if (route.request().url().includes('/v1/auth/me')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'test-user', username: 'ceo', name: '대표이사', role: 'ceo', status: 'active' })
      });
    }
    return route.continue();
  });

  // Step 5: Open page and capture everything
  const page = await context.newPage();

  // Capture console logs
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.text().includes('auth') || msg.text().includes('Auth') || msg.text().includes('token') || msg.text().includes('Token') || msg.text().includes('fetch') || msg.text().includes('Error')) {
      console.log(`  [CONSOLE:${msg.type()}] ${msg.text().substring(0, 200)}`);
    }
  });

  // Capture network requests
  page.on('request', req => {
    const url = req.url();
    if (url.includes('railway') || url.includes('/v1/')) {
      console.log(`  [REQUEST] ${req.method()} ${url.substring(0, 120)}`);
    }
  });

  page.on('response', resp => {
    const url = resp.url();
    if (url.includes('railway') || url.includes('/v1/')) {
      console.log(`  [RESPONSE] ${resp.status()} ${url.substring(0, 120)}`);
    }
  });

  page.on('requestfailed', req => {
    console.log(`  [REQ-FAIL] ${req.url().substring(0, 120)} → ${req.failure()?.errorText}`);
  });

  console.log('\n[2] Loading dashboard...');
  await page.goto(`${FRONTEND}/dashboard`, { waitUntil: 'domcontentloaded', timeout: 30000 });

  // Force visibility
  await page.evaluate(() => {
    document.querySelectorAll('[style*="visibility"]').forEach(el => {
      if (el.style.visibility === 'hidden') el.style.visibility = 'visible';
    });
  });

  // Check at intervals
  for (let i = 1; i <= 8; i++) {
    await page.waitForTimeout(2000);
    await page.evaluate(() => {
      document.querySelectorAll('[style*="visibility"]').forEach(el => {
        if (el.style.visibility === 'hidden') el.style.visibility = 'visible';
      });
    });
    const state = await page.evaluate(() => {
      return {
        url: window.location.href,
        bodyText: document.body?.innerText?.substring(0, 100) || 'EMPTY',
        buttonCount: document.querySelectorAll('button').length,
        hasLoading: (document.body?.innerText || '').includes('불러오는 중'),
        localStorage: {
          token: !!localStorage.getItem('kis-access-token'),
          expiry: localStorage.getItem('kis-token-expiry'),
        },
        allDivs: document.querySelectorAll('div').length,
        visHidden: document.querySelectorAll('[style*="visibility: hidden"], [style*="visibility:hidden"]').length,
      };
    });
    console.log(`\n[3] T+${i*2}s: buttons=${state.buttonCount}, loading=${state.hasLoading}, divs=${state.allDivs}, visHidden=${state.visHidden}, url=${state.url}`);
    console.log(`   body: "${state.bodyText}"`);
    console.log(`   localStorage: token=${state.localStorage.token}, expiry=${state.localStorage.expiry}`);

    if (state.buttonCount > 2 && !state.hasLoading) {
      console.log('[4] Page loaded successfully!');
      break;
    }
  }

  console.log(`\n[5] Total routes intercepted: ${routeCount}`);

  const finalHTML = await page.content();
  console.log(`\n[6] HTML length: ${finalHTML.length}`);
  console.log(`   First 500 chars: ${finalHTML.substring(0, 500)}`);

  await browser.close();
})();
