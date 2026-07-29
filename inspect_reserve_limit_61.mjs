import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/arums/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright-core@1.60.0/node_modules/playwright-core');

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages()[0] || await context.newPage();
await page.goto('https://syosetu.com/draftepisode/view/draftepisodeid/7011889/', { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
await page.locator('a.js-post_input_button, a:has-text("投稿")').first().click();
await page.waitForTimeout(1000);

const data = await page.evaluate(() => {
  const date = document.querySelector('input[name="reserve_date"]');
  return {
    title: document.title,
    url: location.href,
    modalText: [...document.querySelectorAll('[role="dialog"], .modal, form')]
      .map((el) => (el.textContent || '').replace(/\s+/g, ' ').trim())
      .filter(Boolean)
      .slice(0, 5),
    dateAttrs: date ? Object.fromEntries([...date.attributes].map((attr) => [attr.name, attr.value])) : null,
    dateValue: date ? date.value : null,
    hourOptions: [...document.querySelectorAll('select[name="reserve_hour"] option')].map((option) => option.value),
    minuteOptions: [...document.querySelectorAll('select[name="reserve_minutes"] option')].map((option) => option.value),
  };
});

console.log(JSON.stringify(data, null, 2));
await browser.close();
