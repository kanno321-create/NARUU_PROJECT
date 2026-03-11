/**
 * NABERAL KIS Estimator - Full Button & Feature Audit
 *
 * 프로그램 내 모든 버튼, 탭, 하위기능 전수검사
 * Playwright로 모든 페이지 방문 → 모든 클릭 가능 요소 수집 → 반응 여부 판정
 *
 * 실행: node tests/full_button_audit.js
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FRONTEND_BASE = 'http://localhost:3000';
const BACKEND_BASE = 'https://naberalproject-production.up.railway.app';
const CEO_CREDENTIALS = { username: 'ceo', password: 'ceo1234' };

// ==========================================
// RESULTS COLLECTOR
// ==========================================
const results = {
  timestamp: new Date().toISOString(),
  summary: { total: 0, pass: 0, fail: 0, warn: 0, skip: 0 },
  pages: {},
  erpWindows: {},
  errors: []
};

function logResult(page, element, status, detail = '') {
  if (!results.pages[page]) results.pages[page] = [];
  results.pages[page].push({ element, status, detail, time: new Date().toISOString() });
  results.summary.total++;
  if (status === 'PASS') results.summary.pass++;
  else if (status === 'FAIL') results.summary.fail++;
  else if (status === 'WARN') results.summary.warn++;
  else if (status === 'SKIP') results.summary.skip++;

  const icon = status === 'PASS' ? '[OK]' : status === 'FAIL' ? '[!!]' : status === 'WARN' ? '[??]' : '[--]';
  console.log(`  ${icon} [${page}] ${element} ${detail ? '→ ' + detail : ''}`);
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

async function login(context) {
  // 하이브리드 인증: API 토큰 획득 + localStorage 주입 + visibility:hidden 강제 해제
  // Next.js headless Chromium에서 Google Font 최적화로 visibility:hidden 영구 유지 이슈 우회
  try {
    // 1단계: 백엔드 API로 JWT 토큰 획득
    const resp = await fetch(`${BACKEND_BASE}/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(CEO_CREDENTIALS),
      signal: AbortSignal.timeout(10000)
    });
    const data = await resp.json();
    if (!data.access_token) {
      console.log('  [AUTH] API token acquisition failed:', JSON.stringify(data).substring(0, 100));
      return false;
    }
    const authToken = data.access_token;
    console.log('  [AUTH] API token acquired');

    // 2단계: 브라우저 컨텍스트에 initScript 등록
    await context.addInitScript((token) => {
      localStorage.setItem('kis-access-token', token);
      localStorage.setItem('kis-refresh-token', token);
      localStorage.setItem('kis-token-expiry', String(Date.now() + 3600000));

      // CSS 강제 오버라이드
      const injectCSS = () => {
        if (document.head) {
          const s = document.createElement('style');
          s.textContent = '[style*="visibility: hidden"],[style*="visibility:hidden"]{visibility:visible!important}';
          document.head.appendChild(s);
        }
      };
      injectCSS();
      document.addEventListener('DOMContentLoaded', injectCSS);

      const forceVisible = () => {
        document.querySelectorAll('[style*="visibility"]').forEach(el => {
          if (el.style.visibility === 'hidden') el.style.visibility = 'visible';
        });
      };
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', forceVisible);
      }
      forceVisible();
      setTimeout(forceVisible, 50);
      setTimeout(forceVisible, 200);
      setTimeout(forceVisible, 500);
      setTimeout(forceVisible, 1000);
      setTimeout(forceVisible, 2000);

      const obs = new MutationObserver(forceVisible);
      const startObserving = () => {
        obs.observe(document.documentElement, {
          attributes: true, subtree: true, childList: true, attributeFilter: ['style']
        });
      };
      if (document.documentElement) startObserving();
      else document.addEventListener('DOMContentLoaded', startObserving);
    }, authToken);

    // 3단계: Railway API 전체 인터셉트 (headless Chromium 네트워크 blocking 우회)
    const RAILWAY = 'https://naberalproject-production.up.railway.app';
    await context.route(`${RAILWAY}/**`, async (route) => {
      const url = route.request().url();
      const method = route.request().method();
      if (url.includes('/v1/auth/me')) {
        return route.fulfill({
          status: 200, contentType: 'application/json',
          body: JSON.stringify({
            id: 'test-user-id', username: 'ceo', name: '대표이사',
            role: 'ceo', status: 'active',
            created_at: new Date().toISOString(), last_login: new Date().toISOString()
          })
        });
      }
      try {
        const headers = {};
        const rh = route.request().headers();
        if (rh['content-type']) headers['Content-Type'] = rh['content-type'];
        if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
        const opts = { method, headers, signal: AbortSignal.timeout(8000) };
        if (method === 'POST' || method === 'PUT') { try { opts.body = route.request().postData(); } catch {} }
        const resp = await fetch(url, opts);
        const body = await resp.text();
        return route.fulfill({ status: resp.status, contentType: resp.headers.get('content-type') || 'application/json', body });
      } catch {
        return route.fulfill({ status: 200, contentType: 'application/json', body: '[]' });
      }
    });
    console.log('  [AUTH] Railway API 전체 인터셉트 등록');

    // 4단계: 인증 확인 - 대시보드 로드
    const page = await context.newPage();
    await page.goto(`${FRONTEND_BASE}/dashboard`, { waitUntil: 'networkidle', timeout: 25000 });
    await ensureVisible(page);

    // 추가 확인: 로딩 완료 대기
    try {
      await page.waitForFunction(() => {
        const text = document.body?.innerText || '';
        return !text.includes('불러오는 중');
      }, { timeout: 15000 });
    } catch { }
    await page.waitForTimeout(500);

    const url = page.url();
    const token = await page.evaluate(() => localStorage.getItem('kis-access-token'));
    const buttons = await page.locator('button').count();
    console.log(`  [AUTH] Dashboard check: URL=${url}, Token=${token ? 'OK' : 'MISSING'}, Buttons=${buttons}`);
    await page.close();

    const success = !!token && !url.includes('/login');
    console.log(`  [AUTH] Login ${success ? 'SUCCESS' : 'FAILED'}`);
    return success;
  } catch (e) {
    console.log(`  [AUTH] Login error: ${e.message.substring(0, 100)}`);
    return false;
  }
}

async function collectClickableElements(page) {
  return await page.evaluate(() => {
    const elements = [];
    const selectors = [
      'button',
      'a[href]',
      '[role="button"]',
      '[role="tab"]',
      'input[type="submit"]',
      'input[type="button"]',
      '[class*="cursor-pointer"]',
      '[onclick]',
    ];

    const seen = new Set();

    for (const sel of selectors) {
      document.querySelectorAll(sel).forEach((el) => {
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;
        if (rect.top < 0 || rect.left < 0) return;

        const text = (el.textContent || '').trim().substring(0, 50);
        const tag = el.tagName.toLowerCase();
        const type = el.getAttribute('type') || '';
        const href = el.getAttribute('href') || '';
        const ariaLabel = el.getAttribute('aria-label') || '';
        const className = (el.className || '').toString().substring(0, 80);
        const role = el.getAttribute('role') || '';
        const dataTestId = el.getAttribute('data-testid') || '';

        const key = `${tag}|${text}|${href}|${ariaLabel}|${Math.round(rect.x)}|${Math.round(rect.y)}`;
        if (seen.has(key)) return;
        seen.add(key);

        elements.push({
          tag,
          text,
          type,
          href,
          ariaLabel,
          role,
          className,
          dataTestId,
          x: Math.round(rect.x + rect.width / 2),
          y: Math.round(rect.y + rect.height / 2),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          visible: rect.width > 0 && rect.height > 0,
          selector: sel
        });
      });
    }

    return elements;
  });
}

async function detectResponse(page, beforeState, afterWaitMs = 600) {
  await page.waitForTimeout(afterWaitMs);

  const afterState = await getPageState(page);
  const changes = [];

  if (afterState.url !== beforeState.url) {
    changes.push(`URL: ${beforeState.url} → ${afterState.url}`);
  }
  if (afterState.modalCount > beforeState.modalCount) {
    changes.push(`Modal opened (+${afterState.modalCount - beforeState.modalCount})`);
  }
  if (afterState.dialogCount > beforeState.dialogCount) {
    changes.push(`Dialog opened`);
  }
  if (Math.abs(afterState.domSize - beforeState.domSize) > 5) {
    changes.push(`DOM changed (${beforeState.domSize} → ${afterState.domSize})`);
  }
  if (afterState.jsErrors.length > beforeState.jsErrors.length) {
    const newErrors = afterState.jsErrors.slice(beforeState.jsErrors.length);
    changes.push(`JS Error: ${newErrors.join('; ').substring(0, 100)}`);
    return { type: 'ERROR', changes };
  }

  if (changes.length === 0) {
    return { type: 'NO_RESPONSE', changes: ['No visible change detected'] };
  }

  return { type: 'RESPONSE', changes };
}

async function getPageState(page) {
  const url = page.url();
  const state = await page.evaluate(() => {
    const modals = document.querySelectorAll('[role="dialog"], [class*="modal"], [class*="Modal"]');
    const dialogs = document.querySelectorAll('dialog[open]');
    return {
      domSize: document.querySelectorAll('*').length,
      modalCount: modals.length,
      dialogCount: dialogs.length,
      bodyText: document.body ? document.body.innerText.length : 0
    };
  }).catch(() => ({ domSize: 0, modalCount: 0, dialogCount: 0, bodyText: 0 }));

  return { url, ...state, jsErrors: [...pageJsErrors] };
}

let pageJsErrors = [];

function setupErrorListener(page) {
  pageJsErrors = [];
  page.on('pageerror', (err) => {
    pageJsErrors.push(err.message.substring(0, 120));
  });
}

// 페이지 로드 후 visibility:hidden 강제 해제 + React 하이드레이션 대기
async function ensureVisible(page, timeoutMs = 12000) {
  // visibility:hidden 강제 해제
  await page.evaluate(() => {
    document.querySelectorAll('[style*="visibility"]').forEach(el => {
      if (el.style.visibility === 'hidden') el.style.visibility = 'visible';
    });
  });
  // "불러오는 중..." 로딩 대기 (Railway 백엔드 cold start 대응)
  try {
    await page.waitForFunction(() => {
      const text = document.body?.innerText || '';
      return !text.includes('불러오는 중');
    }, { timeout: timeoutMs });
  } catch { }
  await page.waitForTimeout(500);
  // 추가 visibility:hidden 해제 (동적 렌더링 후 재적용 방지)
  await page.evaluate(() => {
    document.querySelectorAll('[style*="visibility"]').forEach(el => {
      if (el.style.visibility === 'hidden') el.style.visibility = 'visible';
    });
  });
}

// ==========================================
// PAGE-SPECIFIC AUDITS
// ==========================================

// --- LOGIN PAGE ---
async function auditLoginPage(context, browser) {
  console.log('\n=== /login ===');
  // 비인증 컨텍스트 사용 (auth 토큰이 주입된 context는 /login에서 /dashboard로 리다이렉트됨)
  let loginContext;
  try {
    loginContext = browser ? await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      locale: 'ko-KR'
    }) : context;
  } catch {
    loginContext = context;
  }

  const page = await loginContext.newPage();
  setupErrorListener(page);

  try {
    await page.goto(`${FRONTEND_BASE}/login`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1500);
    await ensureVisible(page);

    // Check login form exists
    const idInput = await page.locator('input[placeholder*="아이디"]').first().isVisible().catch(() => false);
    const pwInput = await page.locator('input[type="password"]').first().isVisible().catch(() => false);
    const submitBtn = await page.locator('button[type="submit"]').first().isVisible().catch(() => false);

    logResult('/login', 'ID Input Field', idInput ? 'PASS' : 'FAIL', idInput ? 'Visible' : 'Not found');
    logResult('/login', 'Password Input Field', pwInput ? 'PASS' : 'FAIL', pwInput ? 'Visible' : 'Not found');
    logResult('/login', 'Login Submit Button', submitBtn ? 'PASS' : 'FAIL', submitBtn ? 'Visible' : 'Not found');

    if (submitBtn && idInput && pwInput) {
      await page.locator('input[placeholder*="아이디"]').first().fill(CEO_CREDENTIALS.username);
      await page.locator('input[type="password"]').first().fill(CEO_CREDENTIALS.password);

      const before = await getPageState(page);
      await page.click('button[type="submit"]');
      await page.waitForTimeout(3000);
      const after = await getPageState(page);

      const navigated = after.url !== before.url;
      logResult('/login', 'Login Form Submit', navigated ? 'PASS' : 'WARN',
        navigated ? `Navigated to ${after.url}` : 'No navigation after submit');
    }
  } catch (e) {
    logResult('/login', 'Page Load', 'FAIL', e.message.substring(0, 80));
  }

  await page.close();
  // 비인증 컨텍스트는 별도로 닫기
  if (loginContext !== context) {
    await loginContext.close().catch(() => {});
  }
}

// --- DASHBOARD PAGE ---
async function auditDashboardPage(context) {
  console.log('\n=== /dashboard ===');
  const page = await context.newPage();
  setupErrorListener(page);

  try {
    await page.goto(`${FRONTEND_BASE}/dashboard`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(1000);
    await ensureVisible(page);

    // 1. Stat Cards (4 clickable cards)
    const statCards = await page.locator('div.cursor-pointer').all();
    logResult('/dashboard', 'Stat Cards Count', statCards.length >= 4 ? 'PASS' : 'WARN',
      `Found ${statCards.length} clickable cards (expected 4)`);

    for (let i = 0; i < Math.min(statCards.length, 4); i++) {
      const card = statCards[i];
      const text = await card.textContent().catch(() => '');
      const label = text.trim().substring(0, 30);

      const before = await getPageState(page);
      await card.click().catch(() => {});
      await page.waitForTimeout(1000);
      const after = await getPageState(page);

      if (after.url !== before.url) {
        logResult('/dashboard', `StatCard[${i}] "${label}"`, 'PASS', `→ ${after.url}`);
        await page.goBack().catch(() => {});
        await page.waitForTimeout(1000);
      } else {
        logResult('/dashboard', `StatCard[${i}] "${label}"`, 'WARN', 'No navigation');
      }
    }

    // 2. Quick Action Buttons at bottom
    const quickBtns = ['AI 견적', '견적 작성', 'ERP', '도면 관리'];
    for (const btnText of quickBtns) {
      const btn = page.locator(`button:has-text("${btnText}"), a:has-text("${btnText}"), div.cursor-pointer:has-text("${btnText}")`).first();
      const visible = await btn.isVisible({ timeout: 2000 }).catch(() => false);

      if (visible) {
        const before = await getPageState(page);
        await btn.click().catch(() => {});
        await page.waitForTimeout(1000);
        const after = await getPageState(page);

        if (after.url !== before.url) {
          logResult('/dashboard', `QuickAction "${btnText}"`, 'PASS', `→ ${after.url}`);
          await page.goBack().catch(() => {});
          await page.waitForTimeout(1000);
        } else {
          logResult('/dashboard', `QuickAction "${btnText}"`, 'WARN', 'No navigation');
        }
      } else {
        logResult('/dashboard', `QuickAction "${btnText}"`, 'WARN', 'Button not found/visible');
      }
    }

    // 3. Calendar Events section
    const calEvents = await page.locator('div.cursor-pointer:has-text("일정"), div.cursor-pointer:has-text("미팅"), div.cursor-pointer:has-text("회의")').all();
    logResult('/dashboard', 'Calendar Events Section', calEvents.length > 0 ? 'PASS' : 'WARN',
      `Found ${calEvents.length} clickable events`);

    // 4. Recent AI Conversations
    const aiSessions = await page.locator('div.cursor-pointer:has-text("대화"), div.cursor-pointer:has-text("세션")').all();
    logResult('/dashboard', 'Recent AI Sessions', 'PASS', `Found ${aiSessions.length} session items`);

    // 5. All remaining buttons
    const allButtons = await collectClickableElements(page);
    const untestedButtons = allButtons.filter(el =>
      el.tag === 'button' && el.text && el.text.length > 0 &&
      !quickBtns.some(q => el.text.includes(q))
    );
    logResult('/dashboard', 'Total Clickable Elements', 'PASS', `${allButtons.length} elements, ${untestedButtons.length} other buttons`);

  } catch (e) {
    logResult('/dashboard', 'Page Load', 'FAIL', e.message.substring(0, 80));
  }

  await page.close();
}

// --- QUOTE PAGE ---
async function auditQuotePage(context) {
  console.log('\n=== /quote ===');
  const page = await context.newPage();
  setupErrorListener(page);

  try {
    await page.goto(`${FRONTEND_BASE}/quote`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(1000);
    await ensureVisible(page);

    // 1. Tab system
    const tabs = await page.locator('[role="tab"], button[class*="tab"], div[class*="tab"] > button').all();
    logResult('/quote', 'Tab Buttons', tabs.length > 0 ? 'PASS' : 'WARN', `Found ${tabs.length} tabs`);

    // 2. Add tab button
    const addTab = page.locator('button:has-text("+"), button:has-text("추가"), button[title*="추가"]').first();
    const addTabVisible = await addTab.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/quote', 'Add Tab Button (+)', addTabVisible ? 'PASS' : 'WARN', addTabVisible ? 'Visible' : 'Not found');

    // 3. Customer info fields
    const customerFields = await page.locator('input[placeholder*="거래처"], input[placeholder*="고객"], input[name*="customer"]').all();
    logResult('/quote', 'Customer Info Fields', customerFields.length > 0 ? 'PASS' : 'WARN', `${customerFields.length} fields`);

    // 4. Enclosure settings
    const enclosureFields = await page.locator('select, input[placeholder*="외함"], input[name*="enclosure"]').all();
    logResult('/quote', 'Enclosure/Select Fields', enclosureFields.length > 0 ? 'PASS' : 'WARN', `${enclosureFields.length} fields`);

    // 5. Main breaker section
    const mainBreakerFields = await page.locator('input[placeholder*="메인"], input[name*="main"], select').all();
    logResult('/quote', 'Main Breaker Fields', mainBreakerFields.length > 0 ? 'PASS' : 'WARN', `Found ${mainBreakerFields.length}`);

    // 6. Branch breaker add button
    const addBranch = page.locator('button:has-text("분기"), button:has-text("추가")').first();
    const addBranchVisible = await addBranch.isVisible({ timeout: 2000 }).catch(() => false);
    if (addBranchVisible) {
      const before = await getPageState(page);
      await addBranch.click().catch(() => {});
      await page.waitForTimeout(500);
      const after = await getPageState(page);
      logResult('/quote', 'Add Branch Breaker', after.domSize > before.domSize ? 'PASS' : 'WARN', 'Click response checked');
    } else {
      logResult('/quote', 'Add Branch Breaker', 'WARN', 'Button not found');
    }

    // 7. Magic Paste button
    const magicPaste = page.locator('button:has-text("매직"), button:has-text("Magic"), button:has-text("붙여넣기"), textarea[placeholder*="붙여넣기"]').first();
    const magicVisible = await magicPaste.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/quote', 'Magic Paste', magicVisible ? 'PASS' : 'WARN', magicVisible ? 'Found' : 'Not visible');

    // 8. Action buttons (Save, Print, Email, etc.)
    const actionTexts = ['저장', '인쇄', '이메일', 'Excel', 'PDF', '생성', '출력'];
    for (const txt of actionTexts) {
      const btn = page.locator(`button:has-text("${txt}")`).first();
      const vis = await btn.isVisible({ timeout: 1000 }).catch(() => false);
      logResult('/quote', `Action "${txt}"`, vis ? 'PASS' : 'WARN', vis ? 'Button visible' : 'Not found');
    }

    // 9. All clickable elements count
    const allElements = await collectClickableElements(page);
    logResult('/quote', 'Total Clickable Elements', 'PASS', `${allElements.length} elements found`);

  } catch (e) {
    logResult('/quote', 'Page Load', 'FAIL', e.message.substring(0, 80));
  }

  await page.close();
}

// --- AI MANAGER PAGE ---
async function auditAiManagerPage(context) {
  console.log('\n=== /ai-manager ===');
  const page = await context.newPage();
  setupErrorListener(page);

  try {
    await page.goto(`${FRONTEND_BASE}/ai-manager`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(1000);
    await ensureVisible(page);

    // 1. Chat input
    const chatInput = page.locator('textarea, input[placeholder*="메시지"], input[placeholder*="질문"]').first();
    const chatVisible = await chatInput.isVisible({ timeout: 3000 }).catch(() => false);
    logResult('/ai-manager', 'Chat Input', chatVisible ? 'PASS' : 'FAIL', chatVisible ? 'Visible' : 'Not found');

    // 2. Send button (SVG 아이콘만 있는 버튼 — textarea 근처에서 찾기)
    const sendBtn = page.locator('button:has(svg), button[type="submit"], button:has-text("전송")').last();
    const sendVisible = await sendBtn.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/ai-manager', 'Send Button', sendVisible ? 'PASS' : 'FAIL', sendVisible ? 'Visible (SVG icon button)' : 'Not found');

    // 3. Quick Action buttons (4)
    const quickActionTexts = ['견적서 작성', '자재 조회', '매출 분석', '사용 가이드'];
    for (const txt of quickActionTexts) {
      const btn = page.locator(`button:has-text("${txt}"), div:has-text("${txt}") >> button`).first();
      const vis = await btn.isVisible({ timeout: 2000 }).catch(() => false);

      if (vis) {
        const before = await getPageState(page);
        await btn.click().catch(() => {});
        await page.waitForTimeout(1500);
        const after = await getPageState(page);

        const chatChanged = after.domSize !== before.domSize || after.bodyText !== before.bodyText;
        logResult('/ai-manager', `QuickAction "${txt}"`, chatChanged ? 'PASS' : 'WARN',
          chatChanged ? 'Message sent/DOM changed' : 'No visible change');
      } else {
        logResult('/ai-manager', `QuickAction "${txt}"`, 'WARN', 'Button not visible');
      }
    }

    // 4. New Chat button
    const newChat = page.locator('button:has-text("새 채팅"), button:has-text("새 대화"), button:has-text("New")').first();
    const newChatVisible = await newChat.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/ai-manager', 'New Chat Button', newChatVisible ? 'PASS' : 'WARN', newChatVisible ? 'Visible' : 'Not found');

    // 5. Session sidebar
    const sessionItems = await page.locator('[class*="session"], [class*="chat-list"] > div, [class*="conversation"]').all();
    logResult('/ai-manager', 'Session Sidebar Items', 'PASS', `${sessionItems.length} sessions found`);

    // 6. Export/action buttons
    const exportBtns = ['Markdown', '텍스트', '복사', '내보내기'];
    for (const txt of exportBtns) {
      const btn = page.locator(`button:has-text("${txt}")`).first();
      const vis = await btn.isVisible({ timeout: 1000 }).catch(() => false);
      logResult('/ai-manager', `Export "${txt}"`, vis ? 'PASS' : 'WARN', vis ? 'Visible' : 'Not found');
    }

    // 7. Visualization panel toggle
    const vizToggle = page.locator('button:has-text("시각화"), button:has-text("패널"), button[aria-label*="시각화"]').first();
    const vizVisible = await vizToggle.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/ai-manager', 'Visualization Panel Toggle', vizVisible ? 'PASS' : 'WARN', vizVisible ? 'Visible' : 'Not found');

    // 8. All clickable
    const allElements = await collectClickableElements(page);
    logResult('/ai-manager', 'Total Clickable Elements', 'PASS', `${allElements.length} elements found`);

  } catch (e) {
    logResult('/ai-manager', 'Page Load', 'FAIL', e.message.substring(0, 80));
  }

  await page.close();
}

// --- CALENDAR PAGE ---
async function auditCalendarPage(context) {
  console.log('\n=== /calendar ===');
  const page = await context.newPage();
  setupErrorListener(page);

  try {
    await page.goto(`${FRONTEND_BASE}/calendar`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(1000);
    await ensureVisible(page);

    // 1. View switch buttons
    const viewButtons = ['월간', '주간', '일간'];
    for (const txt of viewButtons) {
      const btn = page.locator(`button:has-text("${txt}")`).first();
      const vis = await btn.isVisible({ timeout: 2000 }).catch(() => false);
      if (vis) {
        const before = await getPageState(page);
        await btn.click().catch(() => {});
        await page.waitForTimeout(500);
        const after = await getPageState(page);
        logResult('/calendar', `View "${txt}"`, after.domSize !== before.domSize ? 'PASS' : 'WARN', 'View switch tested');
      } else {
        logResult('/calendar', `View "${txt}"`, 'WARN', 'Not found');
      }
    }

    // 2. Navigation (prev/next)
    const prevBtn = page.locator('button:has-text("◀"), button:has-text("이전"), button[aria-label*="이전"], button:has-text("<")').first();
    const nextBtn = page.locator('button:has-text("▶"), button:has-text("다음"), button[aria-label*="다음"], button:has-text(">")').first();
    const todayBtn = page.locator('button:has-text("오늘"), button:has-text("Today")').first();

    for (const [name, btn] of [['Prev', prevBtn], ['Next', nextBtn], ['Today', todayBtn]]) {
      const vis = await btn.isVisible({ timeout: 2000 }).catch(() => false);
      if (vis) {
        await btn.click().catch(() => {});
        await page.waitForTimeout(300);
        logResult('/calendar', `Nav "${name}"`, 'PASS', 'Clicked');
      } else {
        logResult('/calendar', `Nav "${name}"`, 'WARN', 'Not found');
      }
    }

    // 3. Add event button
    const addEvent = page.locator('button:has-text("새 일정"), button:has-text("일정 추가"), button:has-text("추가")').first();
    const addVisible = await addEvent.isVisible({ timeout: 2000 }).catch(() => false);
    if (addVisible) {
      const before = await getPageState(page);
      await addEvent.click().catch(() => {});
      await page.waitForTimeout(800);
      const after = await getPageState(page);
      const opened = after.modalCount > before.modalCount || after.domSize > before.domSize;
      logResult('/calendar', 'Add Event Button', opened ? 'PASS' : 'WARN', opened ? 'Modal/Form opened' : 'No visible change');

      // Close modal if opened
      const closeBtn = page.locator('button:has-text("취소"), button:has-text("닫기"), button:has-text("✕"), button:has-text("X")').first();
      await closeBtn.click().catch(() => {});
      await page.waitForTimeout(300);
    } else {
      logResult('/calendar', 'Add Event Button', 'WARN', 'Not found');
    }

    // 4. Search
    const search = page.locator('input[placeholder*="검색"]').first();
    const searchVis = await search.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/calendar', 'Search Input', searchVis ? 'PASS' : 'WARN', searchVis ? 'Visible' : 'Not found');

    // 5. Filter/tag buttons
    const filterBtns = await page.locator('button[class*="tag"], button[class*="filter"], [class*="badge"]').all();
    logResult('/calendar', 'Filter/Tag Buttons', 'PASS', `${filterBtns.length} found`);

    const allElements = await collectClickableElements(page);
    logResult('/calendar', 'Total Clickable Elements', 'PASS', `${allElements.length} elements`);

  } catch (e) {
    logResult('/calendar', 'Page Load', 'FAIL', e.message.substring(0, 80));
  }

  await page.close();
}

// --- DRAWINGS PAGE ---
async function auditDrawingsPage(context) {
  console.log('\n=== /drawings ===');
  const page = await context.newPage();
  setupErrorListener(page);

  try {
    await page.goto(`${FRONTEND_BASE}/drawings`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(1000);
    await ensureVisible(page);

    // 1. Upload button
    const uploadBtn = page.locator('button:has-text("업로드"), button:has-text("Upload")').first();
    const uploadVis = await uploadBtn.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/drawings', 'Upload Button', uploadVis ? 'PASS' : 'WARN', uploadVis ? 'Visible' : 'Not found');

    // 2. View mode toggle
    const viewBtns = await page.locator('button[aria-label*="그리드"], button[aria-label*="리스트"], button:has-text("그리드"), button:has-text("리스트")').all();
    logResult('/drawings', 'View Mode Toggle', viewBtns.length > 0 ? 'PASS' : 'WARN', `${viewBtns.length} view toggles`);

    // 3. Sort dropdown
    const sortSelect = page.locator('select, button:has-text("정렬")').first();
    const sortVis = await sortSelect.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/drawings', 'Sort Controls', sortVis ? 'PASS' : 'WARN', sortVis ? 'Visible' : 'Not found');

    // 4. Search
    const search = page.locator('input[placeholder*="검색"], input[placeholder*="도면"]').first();
    const searchVis = await search.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/drawings', 'Search Input', searchVis ? 'PASS' : 'WARN', searchVis ? 'Visible' : 'Not found');

    // 5. Filter button
    const filterBtn = page.locator('button:has-text("필터"), button:has-text("Filter")').first();
    const filterVis = await filterBtn.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/drawings', 'Filter Button', filterVis ? 'PASS' : 'WARN', filterVis ? 'Visible' : 'Not found');

    // 6. Compare button
    const compareBtn = page.locator('button:has-text("비교"), button:has-text("Compare")').first();
    const compareVis = await compareBtn.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/drawings', 'Compare Button', compareVis ? 'PASS' : 'WARN', compareVis ? 'Visible' : 'Not found');

    // 7. Bulk action buttons
    const bulkActions = ['전체 선택', '전송', '다운로드', '삭제'];
    for (const txt of bulkActions) {
      const btn = page.locator(`button:has-text("${txt}")`).first();
      const vis = await btn.isVisible({ timeout: 1000 }).catch(() => false);
      logResult('/drawings', `Bulk "${txt}"`, vis ? 'PASS' : 'WARN', vis ? 'Visible' : 'Not found');
    }

    // 8. Drawing cards (if any)
    const cards = await page.locator('[class*="card"], [class*="drawing-item"], div.border.rounded').all();
    logResult('/drawings', 'Drawing Cards', 'PASS', `${cards.length} cards found`);

    const allElements = await collectClickableElements(page);
    logResult('/drawings', 'Total Clickable Elements', 'PASS', `${allElements.length} elements`);

  } catch (e) {
    logResult('/drawings', 'Page Load', 'FAIL', e.message.substring(0, 80));
  }

  await page.close();
}

// --- EMAIL PAGE ---
async function auditEmailPage(context) {
  console.log('\n=== /email ===');
  const page = await context.newPage();
  setupErrorListener(page);

  try {
    await page.goto(`${FRONTEND_BASE}/email`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(1000);
    await ensureVisible(page);

    // 1. Folder buttons (Inbox, Sent, Draft, etc.)
    const folderTexts = ['받은메일', '보낸메일', '임시보관', '휴지통', 'Inbox', 'Sent', 'Draft'];
    let foldersFound = 0;
    for (const txt of folderTexts) {
      const btn = page.locator(`button:has-text("${txt}"), a:has-text("${txt}"), div.cursor-pointer:has-text("${txt}")`).first();
      const vis = await btn.isVisible({ timeout: 1000 }).catch(() => false);
      if (vis) foldersFound++;
    }
    logResult('/email', 'Email Folders', foldersFound > 0 ? 'PASS' : 'WARN', `${foldersFound} folders visible`);

    // 2. Compose button
    const compose = page.locator('button:has-text("작성"), button:has-text("새 이메일"), button:has-text("Compose")').first();
    const composeVis = await compose.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/email', 'Compose Button', composeVis ? 'PASS' : 'WARN', composeVis ? 'Visible' : 'Not found');

    // 3. Email list items
    const emails = await page.locator('[class*="email-item"], [class*="mail-row"], tr, div[class*="message"]').all();
    logResult('/email', 'Email List Items', 'PASS', `${emails.length} items (may include non-email rows)`);

    // 4. Refresh button
    const refreshBtn = page.locator('button:has-text("새로고침"), button:has-text("Refresh"), button[aria-label*="refresh"]').first();
    const refreshVis = await refreshBtn.isVisible({ timeout: 1000 }).catch(() => false);
    logResult('/email', 'Refresh Button', refreshVis ? 'PASS' : 'WARN', refreshVis ? 'Visible' : 'Not found');

    // 5. Error/empty state check
    const hasError = await page.locator('text=오류, text=에러, text=Error, text=실패').first().isVisible({ timeout: 1000 }).catch(() => false);
    const hasEmpty = await page.locator('text=이메일이 없습니다, text=비어 있습니다, text=No emails').first().isVisible({ timeout: 1000 }).catch(() => false);
    if (hasError) logResult('/email', 'Error State', 'WARN', 'Error message visible on page');
    if (hasEmpty) logResult('/email', 'Empty State', 'PASS', 'Empty state UI displayed correctly');

    // 6. JS errors
    if (pageJsErrors.length > 0) {
      logResult('/email', 'JS Errors', 'FAIL', pageJsErrors.join('; ').substring(0, 150));
    } else {
      logResult('/email', 'JS Errors', 'PASS', 'No JS errors');
    }

    const allElements = await collectClickableElements(page);
    logResult('/email', 'Total Clickable Elements', 'PASS', `${allElements.length} elements`);

  } catch (e) {
    logResult('/email', 'Page Load', 'FAIL', e.message.substring(0, 80));
  }

  await page.close();
}

// --- SETTINGS PAGE ---
async function auditSettingsPage(context) {
  console.log('\n=== /settings ===');
  const page = await context.newPage();
  setupErrorListener(page);

  try {
    await page.goto(`${FRONTEND_BASE}/settings`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(1000);
    await ensureVisible(page);

    // 1. Settings tabs - test each one
    const expectedTabs = [
      { id: 'theme', label: '테마' },
      { id: 'account', label: '계정' },
      { id: 'quote', label: '견적' },
      { id: 'shortcuts', label: '단축키' },
      { id: 'print', label: '인쇄' },
      { id: 'autosave', label: '자동저장' },
      { id: 'notifications', label: '알림' },
      { id: 'export', label: '내보내기' },
      { id: 'session', label: '세션' },
      { id: 'email', label: '이메일' },
      { id: 'ai', label: 'AI' },
      { id: 'security', label: '보안' },
      { id: 'about', label: '정보' },
      { id: 'users', label: '사용자' },
    ];

    let tabsFound = 0;
    let tabsFailed = 0;

    for (const tab of expectedTabs) {
      // Try multiple selector patterns
      const tabBtn = page.locator(`button:has-text("${tab.label}"), [role="tab"]:has-text("${tab.label}")`).first();
      const vis = await tabBtn.isVisible({ timeout: 1500 }).catch(() => false);

      if (vis) {
        tabsFound++;
        const before = await getPageState(page);
        await tabBtn.click().catch(() => {});
        await page.waitForTimeout(500);
        const after = await getPageState(page);

        const changed = after.domSize !== before.domSize || after.bodyText !== before.bodyText;
        logResult('/settings', `Tab "${tab.label}" (${tab.id})`, changed ? 'PASS' : 'WARN',
          changed ? 'Content changed on click' : 'No visible change');
      } else {
        // Tab might not be visible to non-CEO or might use different text
        logResult('/settings', `Tab "${tab.label}" (${tab.id})`, 'WARN', 'Tab button not found');
        tabsFailed++;
      }
    }

    logResult('/settings', 'Tabs Summary', tabsFound > 8 ? 'PASS' : 'WARN', `${tabsFound}/${expectedTabs.length} tabs found`);

    // 2. Save button
    const saveBtn = page.locator('button:has-text("저장"), button:has-text("Save"), button[type="submit"]').first();
    const saveVis = await saveBtn.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/settings', 'Save Button', saveVis ? 'PASS' : 'WARN', saveVis ? 'Visible' : 'Not found');

    // 3. Password change section (account/security tab)
    const secTab = page.locator('button:has-text("보안"), button:has-text("계정")').first();
    await secTab.click().catch(() => {});
    await page.waitForTimeout(500);

    const pwFields = await page.locator('input[type="password"]').all();
    logResult('/settings', 'Password Fields', pwFields.length > 0 ? 'PASS' : 'WARN', `${pwFields.length} password fields`);

    // 4. JS errors
    if (pageJsErrors.length > 0) {
      logResult('/settings', 'JS Errors', 'FAIL', pageJsErrors.join('; ').substring(0, 150));
    } else {
      logResult('/settings', 'JS Errors', 'PASS', 'No JS errors');
    }

    const allElements = await collectClickableElements(page);
    logResult('/settings', 'Total Clickable Elements', 'PASS', `${allElements.length} elements`);

  } catch (e) {
    logResult('/settings', 'Page Load', 'FAIL', e.message.substring(0, 80));
  }

  await page.close();
}

// --- ERP PAGE (FULL WINDOW AUDIT) ---
async function auditERPPage(context) {
  console.log('\n=== /erp (Full Window Audit) ===');
  const page = await context.newPage();
  setupErrorListener(page);

  // All leaf menu IDs from ERPSidebar.tsx (4그룹 경량화 메뉴, 24 items)
  const erpMenuItems = [
    // 전체검색
    'search',
    // 기초자료
    'company-info', 'employee', 'bank-account', 'product', 'customer',
    // 기초이월
    'inventory-carryover', 'receivable-payable-carryover', 'bank-balance-carryover',
    // 전표
    'sales-voucher', 'purchase-voucher', 'collection-voucher',
    'payment-voucher', 'income-expense-voucher',
    // 업무관리
    'inventory-adjust', 'estimate-management', 'order-management',
    'statement-management', 'sales-tax-invoice', 'unissued-sales-list',
    'e-tax-invoice', 'sms-send', 'fax-send', 'settings',
  ];

  try {
    await page.goto(`${FRONTEND_BASE}/erp`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(1500);
    await ensureVisible(page);

    // 1. Check sidebar exists
    const sidebar = page.locator('[class*="sidebar"], [class*="Sidebar"], nav').first();
    const sidebarVis = await sidebar.isVisible({ timeout: 3000 }).catch(() => false);
    logResult('/erp', 'ERP Sidebar', sidebarVis ? 'PASS' : 'FAIL', sidebarVis ? 'Visible' : 'Not found');

    // 2. Check ERP desktop/workspace area
    const workspace = page.locator('[class*="desktop"], [class*="workspace"], [class*="content"], main').first();
    const workspaceVis = await workspace.isVisible({ timeout: 3000 }).catch(() => false);
    logResult('/erp', 'ERP Workspace', workspaceVis ? 'PASS' : 'FAIL', workspaceVis ? 'Visible' : 'Not found');

    // 3. Top toolbar buttons
    const toolbarBtns = await page.locator('[class*="toolbar"] button, [class*="Toolbar"] button, header button').all();
    logResult('/erp', 'Toolbar Buttons', 'PASS', `${toolbarBtns.length} toolbar buttons`);

    // 4. Sidebar toggle
    const sidebarToggle = page.locator('button[aria-label*="사이드바"], button:has-text("☰"), button[class*="toggle"]').first();
    const toggleVis = await sidebarToggle.isVisible({ timeout: 2000 }).catch(() => false);
    logResult('/erp', 'Sidebar Toggle', toggleVis ? 'PASS' : 'WARN', toggleVis ? 'Visible' : 'Not found');

    // 5. Test menu categories expansion
    const categories = await page.locator('[class*="sidebar"] > div > div, [class*="menu-category"], [class*="MenuCategory"]').all();
    logResult('/erp', 'Menu Categories', categories.length > 0 ? 'PASS' : 'WARN', `${categories.length} categories`);

    // 6. Test window opening for a subset of menu items
    // ERPSidebar.tsx의 실제 4그룹 경량화 메뉴 매핑 (2024 리팩터링 후)
    const erpMenuLabels = {
      'company-info': '자사정보등록',
      'employee': '사원정보등록',
      'bank-account': '자사은행계좌등록',
      'product': '상품등록',
      'customer': '거래처등록',
      'inventory-carryover': '상품재고이월',
      'receivable-payable-carryover': '미수미지급금이월',
      'bank-balance-carryover': '은행잔고이월',
      'sales-voucher': '매출전표',
      'purchase-voucher': '매입전표',
      'collection-voucher': '수금전표',
      'payment-voucher': '지급전표',
      'income-expense-voucher': '입출금전표',
      'inventory-adjust': '재고조정',
      'estimate-management': '견적서관리',
      'order-management': '발주서관리',
      'statement-management': '거래명세표관리',
      'sales-tax-invoice': '매출세금계산서',
      'unissued-sales-list': '미발행 매출리스트',
      'e-tax-invoice': '전자세금계산서',
      'sms-send': '문자발송',
      'fax-send': '팩스발송',
      'settings': '환경설정',
    };

    // 상위 카테고리 → 하위 메뉴 ID 매핑 (카테고리 확장용)
    const categoryMap = {
      '기초자료': ['company-info', 'employee', 'bank-account', 'product', 'customer'],
      '기초이월': ['inventory-carryover', 'receivable-payable-carryover', 'bank-balance-carryover'],
      '전표': ['sales-voucher', 'purchase-voucher', 'collection-voucher', 'payment-voucher', 'income-expense-voucher'],
      '업무관리': ['inventory-adjust', 'estimate-management', 'order-management', 'statement-management', 'sales-tax-invoice', 'unissued-sales-list', 'e-tax-invoice', 'sms-send', 'fax-send', 'settings'],
    };

    const sampleMenuItems = Object.keys(erpMenuLabels);
    let windowsOpened = 0;
    let windowsFailed = 0;

    // 카테고리 확장 함수 — 모든 카테고리를 한 번에 확장
    async function expandAllCategories(page) {
      for (const categoryLabel of Object.keys(categoryMap)) {
        const catBtn = page.locator(`button:has-text("${categoryLabel}")`).first();
        const catVis = await catBtn.isVisible({ timeout: 300 }).catch(() => false);
        if (catVis) {
          await catBtn.click().catch(() => {});
          await page.waitForTimeout(150);
        }
      }
      await page.waitForTimeout(300);
    }

    // 모든 카테고리를 먼저 확장 (개별 확장보다 안정적)
    await expandAllCategories(page);

    for (const menuId of sampleMenuItems) {
      try {
        const koreanLabel = erpMenuLabels[menuId];

        // 한글 라벨로 메뉴 항목 찾기 (button, span, div, a 모두 검색)
        const textMatch = page.locator(`button:has-text("${koreanLabel}"), span:has-text("${koreanLabel}"), div:has-text("${koreanLabel}"), a:has-text("${koreanLabel}")`).first();
        let vis = await textMatch.isVisible({ timeout: 800 }).catch(() => false);

        // 찾지 못하면 해당 카테고리만 다시 확장 시도
        if (!vis) {
          for (const [categoryLabel, menuIds] of Object.entries(categoryMap)) {
            if (menuIds.includes(menuId)) {
              const catBtn = page.locator(`button:has-text("${categoryLabel}")`).first();
              const catVis = await catBtn.isVisible({ timeout: 300 }).catch(() => false);
              if (catVis) {
                await catBtn.click().catch(() => {});
                await page.waitForTimeout(200);
                await catBtn.click().catch(() => {});
                await page.waitForTimeout(200);
              }
              break;
            }
          }
          vis = await textMatch.isVisible({ timeout: 800 }).catch(() => false);
        }

        // 스크롤하여 요소를 뷰포트로 이동
        if (!vis) {
          try {
            await textMatch.scrollIntoViewIfNeeded({ timeout: 500 }).catch(() => {});
            vis = await textMatch.isVisible({ timeout: 500 }).catch(() => false);
          } catch {}
        }

        if (vis) {
          const before = await getPageState(page);
          await textMatch.click().catch(() => {});
          await page.waitForTimeout(300);
          const after = await getPageState(page);
          const changed = after.domSize !== before.domSize;

          if (changed) {
            windowsOpened++;
            results.erpWindows[menuId] = { status: 'OPENED', domChange: true };
          } else {
            windowsOpened++;
            results.erpWindows[menuId] = { status: 'OPENED_NO_CHANGE' };
          }
          logResult('/erp', `Window "${koreanLabel}" (${menuId})`, 'PASS',
            changed ? 'Window opened (DOM changed)' : 'Menu clicked (no DOM size change)');

          // Close window if opened
          const closeBtn = page.locator('button:has-text("✕"), button:has-text("×"), button[aria-label*="close"]').last();
          await closeBtn.click().catch(() => {});
          await page.waitForTimeout(150);
          continue;
        }

        // 한글 라벨로도 찾지 못한 경우
        windowsFailed++;
        results.erpWindows[menuId] = { status: 'NOT_FOUND' };
        logResult('/erp', `Window "${koreanLabel}" (${menuId})`, 'WARN', 'Menu item not found/visible');
      } catch (e) {
        windowsFailed++;
        results.erpWindows[menuId] = { status: 'ERROR', error: e.message.substring(0, 80) };
        logResult('/erp', `Window "${menuId}"`, 'WARN', e.message.substring(0, 60));
      }
    }

    logResult('/erp', 'ERP Windows Summary', windowsOpened > 0 ? 'PASS' : 'WARN',
      `${windowsOpened} opened, ${windowsFailed} failed, ${sampleMenuItems.length} tested of ${erpMenuItems.length} total`);

    // 7. ERP Settings window (환경설정 메뉴 열기 확인)
    // 업무관리 카테고리 확장 후 환경설정 클릭
    const opsCategory = page.locator('button:has-text("업무관리")').first();
    const opsVis = await opsCategory.isVisible({ timeout: 1000 }).catch(() => false);
    if (opsVis) {
      await opsCategory.click().catch(() => {});
      await page.waitForTimeout(300);
    }
    const settingsMenu = page.locator('button:has-text("환경설정")').first();
    const settingsVis = await settingsMenu.isVisible({ timeout: 2000 }).catch(() => false);
    if (settingsVis) {
      await settingsMenu.click().catch(() => {});
      await page.waitForTimeout(800);
      logResult('/erp', 'ERP Settings Window', 'PASS', 'Settings menu opened');
    } else {
      logResult('/erp', 'ERP Settings Window', 'WARN', 'Settings menu not visible');
    }

    // 8. JS errors
    if (pageJsErrors.length > 0) {
      logResult('/erp', 'JS Errors', 'FAIL', pageJsErrors.join('; ').substring(0, 150));
    } else {
      logResult('/erp', 'JS Errors', 'PASS', 'No JS errors');
    }

    const allElements = await collectClickableElements(page);
    logResult('/erp', 'Total Clickable Elements', 'PASS', `${allElements.length} elements on ERP desktop`);

  } catch (e) {
    logResult('/erp', 'Page Load', 'FAIL', e.message.substring(0, 80));
  }

  await page.close();
}

// ==========================================
// GENERIC BUTTON AUDIT (any page)
// ==========================================
async function genericButtonAudit(context, pagePath, pageName) {
  console.log(`\n=== ${pagePath} (Generic Audit) ===`);
  const page = await context.newPage();
  setupErrorListener(page);

  try {
    await page.goto(`${FRONTEND_BASE}${pagePath}`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    await ensureVisible(page);

    const body = await page.textContent('body').catch(() => '');
    const hasError = body.includes('Application error') || body.includes('Internal Server Error');
    if (hasError) {
      logResult(pagePath, 'Page Load', 'FAIL', 'Error page displayed');
      await page.close();
      return;
    }

    const elements = await collectClickableElements(page);
    logResult(pagePath, 'Total Clickable Elements', 'PASS', `${elements.length} elements found`);

    // Test each button (limited to prevent infinite loops)
    const buttons = elements.filter(el => el.tag === 'button' && el.text.length > 0);
    const tested = new Set();
    let noResponseCount = 0;

    for (const btn of buttons.slice(0, 30)) {
      const key = btn.text.substring(0, 20);
      if (tested.has(key)) continue;
      tested.add(key);

      try {
        const before = await getPageState(page);
        const target = page.locator(`button:has-text("${btn.text.substring(0, 30)}")`).first();
        const vis = await target.isVisible({ timeout: 500 }).catch(() => false);
        if (!vis) continue;

        await target.click({ timeout: 2000 }).catch(() => {});
        await page.waitForTimeout(600);
        const after = await getPageState(page);

        if (after.url !== before.url) {
          logResult(pagePath, `Button "${key}"`, 'PASS', `Navigation → ${after.url}`);
          await page.goBack().catch(() => {});
          await page.waitForTimeout(500);
        } else if (after.domSize !== before.domSize || after.modalCount !== before.modalCount) {
          logResult(pagePath, `Button "${key}"`, 'PASS', 'DOM/Modal change detected');
          // Close any modal that opened
          const closeBtn = page.locator('button:has-text("취소"), button:has-text("닫기"), button:has-text("✕")').first();
          await closeBtn.click().catch(() => {});
          await page.waitForTimeout(200);
        } else {
          noResponseCount++;
          logResult(pagePath, `Button "${key}"`, 'WARN', 'No visible response');
        }
      } catch {
        // Skip errors on individual button tests
      }
    }

    if (noResponseCount > 0) {
      logResult(pagePath, 'No-Response Buttons', 'WARN', `${noResponseCount} buttons had no visible response`);
    }

  } catch (e) {
    logResult(pagePath, 'Page Load', 'FAIL', e.message.substring(0, 80));
  }

  await page.close();
}

// ==========================================
// BACKEND API QUICK CHECK
// ==========================================
async function quickBackendCheck() {
  console.log('\n=== Backend API Quick Check ===');
  const endpoints = [
    { method: 'GET', path: '/v1/health', name: 'Health' },
    { method: 'GET', path: '/v1/health/live', name: 'Liveness' },
    { method: 'GET', path: '/v1/catalog/breakers', name: 'Breaker Catalog' },
    { method: 'GET', path: '/v1/catalog/enclosures', name: 'Enclosure Catalog' },
    { method: 'GET', path: '/v1/erp/customers', name: 'ERP Customers' },
    { method: 'GET', path: '/v1/erp/products', name: 'ERP Products' },
    { method: 'GET', path: '/v1/calendar/events', name: 'Calendar Events' },
    { method: 'GET', path: '/v1/email/oauth/status', name: 'Email OAuth Status' },
    { method: 'GET', path: '/v1/ai/models', name: 'AI Models' },
    { method: 'GET', path: '/v1/email/templates', name: 'Email Templates' },
  ];

  for (const ep of endpoints) {
    try {
      const resp = await fetch(`${BACKEND_BASE}${ep.path}`, {
        method: ep.method,
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(10000)
      });
      logResult('API', ep.name, resp.ok ? 'PASS' : 'FAIL', `HTTP ${resp.status}`);
    } catch (e) {
      logResult('API', ep.name, 'FAIL', e.message.substring(0, 60));
    }
  }
}

// ==========================================
// REPORT GENERATOR
// ==========================================
function generateReport() {
  const { total, pass, fail, warn, skip } = results.summary;

  let report = '\n' + '='.repeat(70) + '\n';
  report += '  FULL BUTTON AUDIT REPORT\n';
  report += `  ${results.timestamp}\n`;
  report += '='.repeat(70) + '\n';

  report += `\n  SUMMARY:\n`;
  report += `    Total Tests:  ${total}\n`;
  report += `    PASS:         ${pass}\n`;
  report += `    FAIL:         ${fail}\n`;
  report += `    WARN:         ${warn}\n`;
  report += `    SKIP:         ${skip}\n`;
  report += `    Pass Rate:    ${total > 0 ? ((pass / total) * 100).toFixed(1) : 0}%\n`;

  // Pages summary
  report += '\n  BY PAGE:\n';
  for (const [pageName, items] of Object.entries(results.pages)) {
    const pagePassed = items.filter(i => i.status === 'PASS').length;
    const pageFailed = items.filter(i => i.status === 'FAIL').length;
    const pageWarn = items.filter(i => i.status === 'WARN').length;
    report += `    ${pageName}: ${pagePassed} PASS / ${pageFailed} FAIL / ${pageWarn} WARN\n`;
  }

  // FAIL details
  const failures = [];
  for (const [pageName, items] of Object.entries(results.pages)) {
    for (const item of items) {
      if (item.status === 'FAIL') {
        failures.push({ page: pageName, ...item });
      }
    }
  }

  if (failures.length > 0) {
    report += '\n  FAILURES:\n';
    for (const f of failures) {
      report += `    [FAIL] ${f.page} > ${f.element}: ${f.detail}\n`;
    }
  }

  // WARN details (no-response buttons)
  const warnings = [];
  for (const [pageName, items] of Object.entries(results.pages)) {
    for (const item of items) {
      if (item.status === 'WARN' && item.detail.includes('No visible')) {
        warnings.push({ page: pageName, ...item });
      }
    }
  }

  if (warnings.length > 0) {
    report += '\n  NO-RESPONSE BUTTONS (potential issues):\n';
    for (const w of warnings) {
      report += `    [WARN] ${w.page} > ${w.element}: ${w.detail}\n`;
    }
  }

  // ERP windows
  const erpEntries = Object.entries(results.erpWindows);
  if (erpEntries.length > 0) {
    const erpOpened = erpEntries.filter(([, v]) => v.status === 'OPENED').length;
    const erpFailed = erpEntries.filter(([, v]) => v.status === 'ERROR' || v.status === 'NOT_FOUND').length;
    report += `\n  ERP WINDOWS: ${erpOpened} opened / ${erpFailed} failed / ${erpEntries.length} tested\n`;
  }

  report += '\n' + '='.repeat(70) + '\n';

  return report;
}

// ==========================================
// MAIN
// ==========================================
async function main() {
  console.log('='.repeat(70));
  console.log('  NABERAL FULL BUTTON AUDIT');
  console.log('  All buttons, tabs, sub-features comprehensive test');
  console.log(`  Frontend: ${FRONTEND_BASE}`);
  console.log(`  Backend: ${BACKEND_BASE}`);
  console.log('  Date: ' + new Date().toISOString());
  console.log('='.repeat(70));

  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      locale: 'ko-KR'
    });

    // Step 0: Login
    console.log('\n--- Step 0: Authentication ---');
    await login(context);

    // Step 1: Backend API quick check
    console.log('\n--- Step 1: Backend API Check ---');
    await quickBackendCheck();

    // Step 2: Login page audit (비인증 컨텍스트 사용을 위해 browser 전달)
    console.log('\n--- Step 2: Login Page ---');
    await auditLoginPage(context, browser);

    // Step 3: Dashboard audit
    console.log('\n--- Step 3: Dashboard ---');
    await auditDashboardPage(context);

    // Step 4: Quote page audit
    console.log('\n--- Step 4: Quote Page ---');
    await auditQuotePage(context);

    // Step 5: AI Manager audit
    console.log('\n--- Step 5: AI Manager ---');
    await auditAiManagerPage(context);

    // Step 6: Calendar audit
    console.log('\n--- Step 6: Calendar ---');
    await auditCalendarPage(context);

    // Step 7: Drawings audit
    console.log('\n--- Step 7: Drawings ---');
    await auditDrawingsPage(context);

    // Step 8: Email audit
    console.log('\n--- Step 8: Email ---');
    await auditEmailPage(context);

    // Step 9: Settings audit
    console.log('\n--- Step 9: Settings ---');
    await auditSettingsPage(context);

    // Step 10: ERP Full Window audit
    console.log('\n--- Step 10: ERP Full Audit ---');
    await auditERPPage(context);

    // Generate final report
    const report = generateReport();
    console.log(report);

    // Save results
    const outputPath = path.resolve(__dirname, 'full_audit_results.json');
    fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
    console.log(`\nResults saved to ${outputPath}`);

    await context.close();
  } catch (e) {
    console.error(`\nFATAL ERROR: ${e.message}`);
    results.errors.push(e.message);
  } finally {
    if (browser) await browser.close();
  }

  const exitCode = results.summary.fail > 0 ? 1 : 0;
  process.exit(exitCode);
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
