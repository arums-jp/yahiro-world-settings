import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const browser = await chromium.connectOverCDP("http://127.0.0.1:9223");
const context = browser.contexts()[0];
const page = context.pages().find((p) => p.url().includes("syosetu.com")) || context.pages()[0] || (await context.newPage());

await page.goto("https://syosetu.com/draftepisode/view/draftepisodeid/7011851/", { waitUntil: "domcontentloaded" });
await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {});

await page.locator('a.js-post_input_button, a:has-text("投稿")').first().click();
await page.waitForTimeout(1000);

const data = await page.evaluate(() => ({
  title: document.title,
  url: location.href,
  text: document.body.textContent.replace(/\s+/g, " ").slice(0, 1000),
  controls: [...document.querySelectorAll("input, select, button, a")]
    .filter((el) => {
      const s = getComputedStyle(el);
      return s.display !== "none" && s.visibility !== "hidden";
    })
    .map((el, i) => ({
      i,
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute("type") || "",
      name: el.getAttribute("name") || "",
      id: el.id || "",
      value: el instanceof HTMLInputElement ? el.value : el instanceof HTMLSelectElement ? el.value : "",
      text: (el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 80),
      href: el.tagName.toLowerCase() === "a" ? el.getAttribute("href") || "" : "",
    })),
}));

console.log(JSON.stringify(data, null, 2));
await browser.close();
