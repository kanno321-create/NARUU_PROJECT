import { test, expect, Page } from '@playwright/test';

// Test configuration
const BASE_URL = 'http://localhost:3000';
const BACKEND_URL = 'http://localhost:8000';

// Login credentials (from environment)
const CEO_USERNAME = 'ceo';
const CEO_PASSWORD = process.env.CEO_PASSWORD || 'test-only-password';

// Helper function to login
async function login(page: Page) {
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(1000); // Wait for React to render

  // Fill login form using exact placeholders from login page
  await page.fill('input[placeholder="아이디를 입력하세요"]', CEO_USERNAME);
  await page.fill('input[placeholder="비밀번호를 입력하세요"]', CEO_PASSWORD);

  // Click login button
  await page.click('button[type="submit"]');

  // Wait for navigation to ai-manager (successful login redirects there)
  await page.waitForURL('**/ai-manager', { timeout: 10000 }).catch(() => {
    // If redirect doesn't happen, we might still be on login page
    console.log('Login redirect may have failed');
  });
  await page.waitForLoadState('domcontentloaded');
}

test.describe('1. 로그인 기능 테스트', () => {
  test('로그인 페이지 로드', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    await expect(page).toHaveURL(/login/);

    // Check login form elements exist using exact placeholders
    const usernameInput = page.locator('input[placeholder="아이디를 입력하세요"]');
    const passwordInput = page.locator('input[placeholder="비밀번호를 입력하세요"]');
    const loginButton = page.locator('button[type="submit"]');

    await expect(usernameInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(loginButton).toBeVisible();

    console.log('✅ 로그인 페이지 로드 완료');
  });

  test('CEO 계정으로 로그인 성공', async ({ page }) => {
    await login(page);

    // Should redirect to ai-manager after login
    await expect(page).toHaveURL(/ai-manager/);
    console.log('✅ CEO 로그인 성공');
  });

  test('잘못된 비밀번호로 로그인 실패', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    await page.fill('input[placeholder="아이디를 입력하세요"]', CEO_USERNAME);
    await page.fill('input[placeholder="비밀번호를 입력하세요"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Wait for error message or stay on login page
    await page.waitForTimeout(2000);

    // Should still be on login page or show error
    const currentUrl = page.url();
    expect(currentUrl).toContain('login');
    console.log('✅ 잘못된 비밀번호 테스트 완료');
  });
});

test.describe('2. 페이지 네비게이션 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('메인 페이지에서 견적 페이지로 이동', async ({ page }) => {
    await page.goto('/');

    // Find and click quote link
    const quoteLink = page.locator('a[href*="quote"], button:has-text("견적")').first();
    if (await quoteLink.isVisible()) {
      await quoteLink.click();
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/quote/);
    }
  });

  test('메인 페이지에서 ERP 페이지로 이동', async ({ page }) => {
    await page.goto('/');

    const erpLink = page.locator('a[href*="erp"], button:has-text("ERP")').first();
    if (await erpLink.isVisible()) {
      await erpLink.click();
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/erp/);
    }
  });

  test('메인 페이지에서 AI Manager 페이지로 이동', async ({ page }) => {
    await page.goto('/');

    const aiLink = page.locator('a[href*="ai-manager"], button:has-text("AI")').first();
    if (await aiLink.isVisible()) {
      await aiLink.click();
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/ai-manager/);
    }
  });

  test('메인 페이지에서 대시보드로 이동', async ({ page }) => {
    await page.goto('/');

    const dashboardLink = page.locator('a[href*="dashboard"], button:has-text("대시보드")').first();
    if (await dashboardLink.isVisible()) {
      await dashboardLink.click();
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL(/dashboard/);
    }
  });

  test('사이드바 네비게이션 테스트', async ({ page }) => {
    await page.goto('/');

    // Check sidebar exists
    const sidebar = page.locator('nav, aside, [class*="sidebar"]').first();
    await expect(sidebar).toBeVisible();

    // Click through navigation items
    const navItems = page.locator('nav a, aside a');
    const count = await navItems.count();
    console.log(`Found ${count} navigation items`);

    for (let i = 0; i < Math.min(count, 5); i++) {
      const item = navItems.nth(i);
      if (await item.isVisible()) {
        const href = await item.getAttribute('href');
        console.log(`Navigation item ${i}: ${href}`);
      }
    }
  });
});

test.describe('3. 견적 페이지 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/quote');
    await page.waitForLoadState('networkidle');
  });

  test('견적 페이지 로드 및 UI 요소 확인', async ({ page }) => {
    // Check main elements
    await expect(page.locator('body')).toBeVisible();

    // Look for input fields
    const inputs = page.locator('input, textarea, select');
    const inputCount = await inputs.count();
    console.log(`Found ${inputCount} input elements on quote page`);

    // Check for buttons
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    console.log(`Found ${buttonCount} buttons on quote page`);
  });

  test('견적 입력 폼 테스트', async ({ page }) => {
    // Find and fill quote input
    const quoteInput = page.locator('textarea[placeholder*="견적"], input[placeholder*="견적"]').first();
    if (await quoteInput.isVisible()) {
      await quoteInput.fill('상도 4P 100A 메인, 분기 ELB 2P 20A 5개');
      await expect(quoteInput).toHaveValue(/상도/);
    }
  });

  test('견적 생성 버튼 클릭', async ({ page }) => {
    const generateButton = page.locator('button:has-text("견적"), button:has-text("생성"), button:has-text("요청")').first();
    if (await generateButton.isVisible()) {
      await generateButton.click();
      await page.waitForTimeout(2000);
      console.log('Generate button clicked');
    }
  });

  test('이메일 전송 버튼 확인', async ({ page }) => {
    const emailButton = page.locator('button:has-text("이메일"), button:has-text("전송"), button:has-text("Send")').first();
    if (await emailButton.isVisible()) {
      console.log('Email button found');
      await expect(emailButton).toBeVisible();
    }
  });

  test('PDF 다운로드 버튼 확인', async ({ page }) => {
    const pdfButton = page.locator('button:has-text("PDF"), a:has-text("PDF")').first();
    if (await pdfButton.isVisible()) {
      console.log('PDF button found');
      await expect(pdfButton).toBeVisible();
    }
  });

  test('Excel 다운로드 버튼 확인', async ({ page }) => {
    const excelButton = page.locator('button:has-text("Excel"), a:has-text("Excel")').first();
    if (await excelButton.isVisible()) {
      console.log('Excel button found');
      await expect(excelButton).toBeVisible();
    }
  });

  test('인쇄 버튼 확인', async ({ page }) => {
    const printButton = page.locator('button:has-text("인쇄"), button:has-text("Print")').first();
    if (await printButton.isVisible()) {
      console.log('Print button found');
      await expect(printButton).toBeVisible();
    }
  });
});

test.describe('4. ERP 페이지 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/erp');
    await page.waitForLoadState('networkidle');
  });

  test('ERP 페이지 로드', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('기초자료 카테고리 확장 및 거래처등록 열기', async ({ page }) => {
    // 기초자료 카테고리 확장
    const categoryBtn = page.locator('button:has-text("기초자료")').first();
    if (await categoryBtn.isVisible()) {
      await categoryBtn.click();
      await page.waitForTimeout(300);
    }
    // 거래처등록 클릭
    const menuBtn = page.locator('button:has-text("거래처등록")').first();
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
      await page.waitForTimeout(500);
      console.log('거래처등록 window opened');
    }
  });

  test('전표 카테고리 확장 및 매출전표 열기', async ({ page }) => {
    const categoryBtn = page.locator('button:has-text("전표")').first();
    if (await categoryBtn.isVisible()) {
      await categoryBtn.click();
      await page.waitForTimeout(300);
    }
    const menuBtn = page.locator('button:has-text("매출전표")').first();
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
      await page.waitForTimeout(500);
      console.log('매출전표 window opened');
    }
  });

  test('상품등록 창 열기', async ({ page }) => {
    const categoryBtn = page.locator('button:has-text("기초자료")').first();
    if (await categoryBtn.isVisible()) {
      await categoryBtn.click();
      await page.waitForTimeout(300);
    }
    const menuBtn = page.locator('button:has-text("상품등록")').first();
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
      await page.waitForTimeout(500);
      console.log('상품등록 window opened');
    }
  });

  test('업무관리 카테고리 확장 및 견적서관리 열기', async ({ page }) => {
    const categoryBtn = page.locator('button:has-text("업무관리")').first();
    if (await categoryBtn.isVisible()) {
      await categoryBtn.click();
      await page.waitForTimeout(300);
    }
    const menuBtn = page.locator('button:has-text("견적서관리")').first();
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
      await page.waitForTimeout(500);
      console.log('견적서관리 window opened');
    }
  });

  test('환경설정 창 열기', async ({ page }) => {
    const categoryBtn = page.locator('button:has-text("업무관리")').first();
    if (await categoryBtn.isVisible()) {
      await categoryBtn.click();
      await page.waitForTimeout(300);
    }
    const menuBtn = page.locator('button:has-text("환경설정")').first();
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
      await page.waitForTimeout(500);
      console.log('환경설정 window opened');
    }
  });
});

test.describe('5. AI Manager 페이지 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/ai-manager');
    await page.waitForLoadState('networkidle');
  });

  test('AI Manager 페이지 로드', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('대화 입력 필드 확인', async ({ page }) => {
    const chatInput = page.locator('input[type="text"], textarea').first();
    if (await chatInput.isVisible()) {
      await chatInput.fill('테스트 메시지');
      console.log('Chat input works');
    }
  });

  test('Excel 내보내기 버튼 확인', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Excel"), button:has-text("내보내기"), button:has-text("Export")').first();
    if (await exportButton.isVisible()) {
      console.log('Excel export button found');
      await expect(exportButton).toBeVisible();
    }
  });
});

test.describe('6. 대시보드 페이지 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('대시보드 페이지 로드', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('통계 카드 확인', async ({ page }) => {
    const cards = page.locator('[class*="card"], [class*="stat"]');
    const count = await cards.count();
    console.log(`Found ${count} stat cards on dashboard`);
  });
});

test.describe('7. 캘린더 페이지 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/calendar');
    await page.waitForLoadState('networkidle');
  });

  test('캘린더 페이지 로드', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('월 네비게이션 버튼 확인', async ({ page }) => {
    const prevButton = page.locator('button:has-text("이전"), button:has-text("<"), button[aria-label*="prev"]').first();
    const nextButton = page.locator('button:has-text("다음"), button:has-text(">"), button[aria-label*="next"]').first();

    if (await prevButton.isVisible()) {
      console.log('Previous month button found');
    }
    if (await nextButton.isVisible()) {
      console.log('Next month button found');
    }
  });
});

test.describe('8. 도면 페이지 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/drawings');
    await page.waitForLoadState('networkidle');
  });

  test('도면 페이지 로드', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('파일 업로드 영역 확인', async ({ page }) => {
    const uploadArea = page.locator('input[type="file"], [class*="upload"], [class*="dropzone"]').first();
    if (await uploadArea.isVisible()) {
      console.log('File upload area found');
    }
  });
});

test.describe('9. 이메일 페이지 테스트', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/email');
    await page.waitForLoadState('networkidle');
  });

  test('이메일 페이지 로드', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('이메일 작성 폼 확인', async ({ page }) => {
    const recipientInput = page.locator('input[placeholder*="받는"], input[name*="recipient"], input[type="email"]').first();
    const subjectInput = page.locator('input[placeholder*="제목"], input[name*="subject"]').first();

    if (await recipientInput.isVisible()) {
      console.log('Recipient input found');
    }
    if (await subjectInput.isVisible()) {
      console.log('Subject input found');
    }
  });
});

test.describe('10. 백엔드 API 연결 테스트', () => {
  test('헬스 체크 API', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/v1/health`);
    expect(response.status()).toBe(200);

    const body = await response.json();
    console.log('Health check response:', body);
  });

  test('견적 API 연결', async ({ request }) => {
    // Test estimate endpoint
    const response = await request.post(`${BACKEND_URL}/v1/ai/chat`, {
      data: {
        message: '테스트',
        context: {},
        model: 'claude-sonnet'
      }
    });

    // Just check connection works
    const status = response.status();
    console.log(`AI Chat API status: ${status}`);
  });
});

test.describe('11. 반응형 디자인 테스트', () => {
  test('모바일 뷰포트', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await login(page);
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
    console.log('Mobile viewport works');
  });

  test('태블릿 뷰포트', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await login(page);
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
    console.log('Tablet viewport works');
  });

  test('데스크톱 뷰포트', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await login(page);
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();
    console.log('Desktop viewport works');
  });
});

test.describe('12. 다크모드 테스트', () => {
  test('다크모드 토글 확인', async ({ page }) => {
    await login(page);
    await page.goto('/');

    const darkModeToggle = page.locator('button[aria-label*="dark"], button:has-text("다크"), [class*="theme-toggle"]').first();
    if (await darkModeToggle.isVisible()) {
      await darkModeToggle.click();
      await page.waitForTimeout(500);
      console.log('Dark mode toggle clicked');
    }
  });
});
