import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/arums/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright-core@1.60.0/node_modules/playwright-core');

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages()[0] || await context.newPage();
await page.goto('https://syosetu.com/usernovelmanage/top/ncode/3145031/', { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});

const data = await page.evaluate(() => {
  const rows = [];
  for (const a of document.querySelectorAll('a[href*="noveldataid/"], a[href*="draftepisodeid/"]')) {
    const href = a.href;
    const container = a.closest('tr, li, article, section, div') || a.parentElement || a;
    const text = (container.textContent || '').replace(/\s+/g, ' ').trim();
    const titleMatch = text.match(/第\s*([0-9０-９]+)\s*話[^|]*?(?=(公開|予約|下書き|$))/) || text.match(/第([0-9０-９]+)話[^|]*/);
    rows.push({ href, text: text.slice(0, 500), title: titleMatch ? titleMatch[0] : '' });
  }
  return {
    title: document.title,
    url: location.href,
    text: document.body.textContent.replace(/\s+/g, ' ').slice(0, 1500),
    links: rows,
  };
});

console.log(JSON.stringify(data, null, 2));
await browser.close();
