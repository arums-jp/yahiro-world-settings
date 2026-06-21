import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/arums/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright-core@1.60.0/node_modules/playwright-core');

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages()[0] || await context.newPage();
page.setDefaultTimeout(10000);

await page.goto('https://syosetu.com/draftepisode/view/draftepisodeid/7011889/', { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
await page.locator('a.js-post_input_button, a:has-text("投稿")').first().click();
await page.waitForTimeout(1000);
await page.locator('#reserve-on').check({ force: true });
await page.locator('input[name="reserve_date"]').evaluate((element) => {
  element.removeAttribute('readonly');
  element.value = '2026/09/01';
  element.dispatchEvent(new Event('input', { bubbles: true }));
  element.dispatchEvent(new Event('change', { bubbles: true }));
});
await page.locator('select[name="reserve_hour"]').selectOption('20');
await page.locator('select[name="reserve_minutes"]').selectOption('10');

const before = await page.evaluate(() => ({
  values: {
    reserve: [...document.querySelectorAll('input[name="reserve"]')].map((el) => ({ id: el.id, value: el.value, checked: el.checked })),
    date: [...document.querySelectorAll('input[name="reserve_date"]')].map((el) => ({ value: el.value, visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length) })),
    hour: [...document.querySelectorAll('select[name="reserve_hour"]')].map((el) => el.value),
    minute: [...document.querySelectorAll('select[name="reserve_minutes"]')].map((el) => el.value),
  },
  buttons: [...document.querySelectorAll('button, input[type="submit"], a')]
    .map((el) => ({ text: (el.textContent || '').replace(/\s+/g, ' ').trim(), value: el.value || '', href: el.href || '', visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length) }))
    .filter((x) => x.visible && (x.text || x.value)),
}));
console.log('BEFORE_CONFIRM');
console.log(JSON.stringify(before, null, 2));

await page.locator('button:has-text("投稿[確認]"), input[type="submit"][value*="確認"]').first().click();
await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
await page.waitForTimeout(1000);

const after = await page.evaluate(() => ({
  title: document.title,
  url: location.href,
  text: document.body.textContent.replace(/\s+/g, ' ').trim().slice(0, 3000),
  buttons: [...document.querySelectorAll('button, input[type="submit"], a')]
    .map((el) => ({ text: (el.textContent || '').replace(/\s+/g, ' ').trim(), value: el.value || '', href: el.href || '', visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length) }))
    .filter((x) => x.visible && (x.text || x.value)),
}));
console.log('AFTER_CONFIRM');
console.log(JSON.stringify(after, null, 2));

await browser.close();
