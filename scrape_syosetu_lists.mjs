import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/arums/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright-core@1.60.0/node_modules/playwright-core');

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages()[0] || await context.newPage();

async function scrape(url) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  return page.evaluate(() => {
    const entries = [];
    for (const a of document.querySelectorAll('a[href*="noveldataid/"], a[href*="draftepisodeid/"]')) {
      const href = a.href;
      const container = a.closest('tr, li, article, section, div') || a.parentElement || a;
      const text = (container.textContent || '').replace(/\s+/g, ' ').trim();
      const epMatch = text.match(/ep\.(\d+)/) || text.match(/第\s*(\d+)\s*話/) || text.match(/第([0-9０-９]+)話/);
      const idMatch = href.match(/(?:noveldataid|draftepisodeid)\/(\d+)/);
      entries.push({
        episode: epMatch ? Number(epMatch[1].replace(/[０-９]/g, (char) => String(char.charCodeAt(0) - 0xff10))) : null,
        id: idMatch ? Number(idMatch[1]) : null,
        kind: href.includes('noveldataid') ? 'noveldata' : 'draft',
        href,
        text,
      });
    }
    return {
      title: document.title,
      url: location.href,
      body: document.body.textContent.replace(/\s+/g, ' ').trim().slice(0, 1000),
      entries,
    };
  });
}

const result = {
  manage: await scrape('https://syosetu.com/usernovelmanage/top/ncode/3145031/'),
  drafts: await scrape('https://syosetu.com/usernovelmanage/top/ncode/3145031/?filter=draft'),
};
console.log(JSON.stringify(result, null, 2));
await browser.close();
