import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/arums/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright-core@1.60.0/node_modules/playwright-core');

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages()[0] || await context.newPage();

async function getEntries(url) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  return page.evaluate(() => {
    const map = new Map();
    for (const a of document.querySelectorAll('a[href*="noveldataid/"], a[href*="draftepisodeid/"]')) {
      const href = a.href;
      if (href.includes('/updateinput/')) continue;
      const container = a.closest('tr, li, article, section, div') || a.parentElement || a;
      const text = (container.textContent || '').replace(/\s+/g, ' ').trim();
      const epMatch = text.match(/ep\.(\d+)/) || text.match(/第\s*(\d+)\s*話/) || text.match(/第([0-9０-９]+)話/);
      const idMatch = href.match(/(?:noveldataid|draftepisodeid)\/(\d+)/);
      if (!epMatch || !idMatch) continue;
      const episode = Number(epMatch[1].replace(/[０-９]/g, (char) => String(char.charCodeAt(0) - 0xff10)));
      map.set(episode, {
        episode,
        id: Number(idMatch[1]),
        kind: href.includes('noveldataid') ? 'noveldata' : 'draft',
        status: text.includes('予約中') ? 'reserved' : text.includes('下書き') ? 'draft' : 'published',
        href,
        text,
      });
    }
    return [...map.values()].sort((a, b) => a.episode - b.episode);
  });
}

const manage = await getEntries('https://syosetu.com/usernovelmanage/top/ncode/3145031/');
const drafts = await getEntries('https://syosetu.com/usernovelmanage/top/ncode/3145031/?filter=draft');
for (const entry of [...manage, ...drafts].sort((a, b) => a.episode - b.episode)) {
  if (entry.episode >= 31) {
    console.log([entry.episode, entry.status, entry.kind, entry.id, entry.href].join('\t'));
  }
}
await browser.close();
