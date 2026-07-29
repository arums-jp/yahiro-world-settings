import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/arums/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright-core@1.60.0/node_modules/playwright-core');

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages().find((p) => p.url().includes('syosetu.com')) || context.pages()[0] || await context.newPage();
await page.waitForLoadState('domcontentloaded', { timeout: 5000 }).catch(() => {});
const data = await page.evaluate(() => ({
  title: document.title,
  url: location.href,
  text: document.body.textContent.replace(/\s+/g, ' ').trim().slice(0, 3000),
  controls: [...document.querySelectorAll('a, button, input, select')]
    .filter((el) => {
      const style = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
    })
    .map((el) => ({
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute('type') || '',
      name: el.getAttribute('name') || '',
      id: el.id || '',
      value: el instanceof HTMLInputElement || el instanceof HTMLSelectElement ? el.value : '',
      text: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 120),
      href: el instanceof HTMLAnchorElement ? el.href : '',
    })),
}));
console.log(JSON.stringify(data, null, 2));
await browser.close();
