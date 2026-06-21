import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('C:/Users/arums/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/playwright-core@1.60.0/node_modules/playwright-core');

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const arg = process.argv[i];
  if (arg.startsWith('--')) {
    args.set(arg.slice(2), process.argv[i + 1] && !process.argv[i + 1].startsWith('--') ? process.argv[++i] : 'true');
  }
}

const port = Number(args.get('port') || 9223);
const startEpisode = Number(args.get('start') || 31);
const endEpisode = Number(args.get('end') || 71);

const drafts = [
  [31, 7011851],
  [32, 7011852],
  [33, 7011855],
  [34, 7011856],
  [35, 7011857],
  [36, 7011858],
  [37, 7011859],
  [38, 7011860],
  [39, 7011861],
  [40, 7011862],
  [41, 7011863],
  [42, 7011864],
  [43, 7011866],
  [44, 7011867],
  [45, 7011868],
  [46, 7011870],
  [47, 7011871],
  [48, 7011873],
  [49, 7011875],
  [50, 7011876],
  [51, 7011877],
  [52, 7011879],
  [53, 7011880],
  [54, 7011881],
  [55, 7011882],
  [56, 7011883],
  [57, 7011884],
  [58, 7011886],
  [59, 7011887],
  [60, 7011888],
  [61, 7011889],
  [62, 7011890],
  [63, 7011891],
  [64, 7011892],
  [65, 7197042],
  [66, 7197044],
  [67, 7197045],
  [68, 7197046],
  [69, 7197047],
  [70, 7197048],
  [71, 7197049],
].filter(([episode]) => episode >= startEpisode && episode <= endEpisode);

function pad(number) {
  return String(number).padStart(2, '0');
}

function scheduleForEpisode(episode) {
  const date = new Date(Date.UTC(2026, 5, 23));
  let slots = episode - 31;
  while (slots > 0) {
    date.setUTCDate(date.getUTCDate() + 1);
    const day = date.getUTCDay();
    if (day === 2 || day === 4 || day === 6) {
      slots -= 1;
    }
  }
  return {
    ymdDash: `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`,
    ymdSlash: `${date.getUTCFullYear()}/${pad(date.getUTCMonth() + 1)}/${pad(date.getUTCDate())}`,
    hour: '20',
    minute: '10',
  };
}

async function clickFirstVisible(page, selectors, timeout = 5000) {
  const deadline = Date.now() + timeout;
  let lastError;
  while (Date.now() < deadline) {
    for (const selector of selectors) {
      const locator = page.locator(selector).first();
      try {
        if ((await locator.count()) > 0 && await locator.isVisible()) {
          await locator.click();
          return selector;
        }
      } catch (error) {
        lastError = error;
      }
    }
    await page.waitForTimeout(250);
  }
  throw new Error(`No visible clickable selector found: ${selectors.join(', ')}${lastError ? ` (${lastError.message})` : ''}`);
}

async function setReserveDate(page, value) {
  await page.waitForSelector('input[name="reserve_date"]', { state: 'attached', timeout: 10000 });
  await page.locator('input[name="reserve_date"]').evaluate((element, nextValue) => {
    element.removeAttribute('readonly');
    element.value = nextValue;
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  }, value);
}

async function reserveOne(page, episode, draftId) {
  const schedule = scheduleForEpisode(episode);
  const url = `https://syosetu.com/draftepisode/view/draftepisodeid/${draftId}/`;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});

  const bodyText = await page.locator('body').innerText({ timeout: 10000 });
  if (bodyText.includes('ログイン') && bodyText.includes('パスワード')) {
    throw new Error('Login appears to be required.');
  }
  if (bodyText.includes('存在しません') || bodyText.includes('見つかりません')) {
    throw new Error(`Draft ${draftId} is not available.`);
  }

  await clickFirstVisible(page, [
    `a.js-post_input_button[data-draftepisodeid="${draftId}"]`,
    'a:has-text("投稿")',
    'button:has-text("投稿")',
  ]);

  await page.waitForSelector('#reserve-on, input[name="reserve"][value="1"], input[name="reserve"][value="on"]', { timeout: 10000 });
  const reserveOn = page.locator('#reserve-on').first();
  if (await reserveOn.count()) {
    await reserveOn.check({ force: true });
  } else {
    await page.locator('input[name="reserve"]').last().check({ force: true });
  }
  await setReserveDate(page, schedule.ymdSlash);
  await page.locator('select[name="reserve_hour"]').selectOption(schedule.hour);
  await page.locator('select[name="reserve_minutes"]').selectOption(schedule.minute);

  await clickFirstVisible(page, [
    'button:has-text("投稿[確認]")',
    'input[type="submit"][value*="投稿"][value*="確認"]',
    'button:has-text("確認")',
  ]);
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});

  const confirmText = await page.locator('body').innerText({ timeout: 10000 });
  if (confirmText.includes('エラーが発生') || confirmText.includes('入力してください') || confirmText.includes('正しく入力')) {
    throw new Error(`Confirmation page reported an error for episode ${episode}: ${confirmText.slice(0, 500).replace(/\s+/g, ' ')}`);
  }

  await clickFirstVisible(page, [
    'a:has-text("実行する")',
    'button:has-text("実行する")',
    'input[type="submit"][value*="実行"]',
    'button:has-text("投稿[実行]")',
  ], 10000);
  await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});

  const doneText = await page.locator('body').innerText({ timeout: 10000 });
  if (doneText.includes('エラーが発生')) {
    throw new Error(`Execution page reported an error for episode ${episode}: ${doneText.slice(0, 500).replace(/\s+/g, ' ')}`);
  }

  console.log(`RESERVED ${episode} ${schedule.ymdDash} ${schedule.hour}:${schedule.minute} draft=${draftId}`);
}

const browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
const context = browser.contexts()[0] || await browser.newContext();
const page = context.pages()[0] || await context.newPage();
page.setDefaultTimeout(10000);

try {
  for (const [episode, draftId] of drafts) {
    await reserveOne(page, episode, draftId);
  }
} finally {
  await browser.close();
}
