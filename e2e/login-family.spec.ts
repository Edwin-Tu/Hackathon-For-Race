import { test, expect } from '@playwright/test';

test('family user login and dashboard', async ({ page }) => {
  // 假設已有登入頁面
  await page.goto('http://localhost:3000/login');
  await page.fill('input[name="username"]', 'family_user');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  // 登入成功後應導向 family dashboard
  await page.waitForURL('**/family/dashboard');
  await expect(page.locator('text=血糖')).toBeVisible();
  await expect(page.locator('text=心率')).toBeVisible();
});
