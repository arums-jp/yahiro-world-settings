#!/usr/bin/env node
import { createRequire } from "node:module";
import fs from "node:fs/promises";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

function argValue(name, fallback = undefined) {
  const index = process.argv.indexOf(name);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
}

function hasFlag(name) {
  return process.argv.includes(name);
}

function usage() {
  console.error(
    [
      "Usage: node upload_syosetu_drafts.mjs --episodes episodes.json --ncode N --yes-save-drafts [options]",
      "Options:",
      "  --port 9223",
      "  --start N",
      "  --end N",
      "  --delay-ms 1200",
    ].join("\n"),
  );
}

const episodesPath = argValue("--episodes");
const ncode = argValue("--ncode");
if (!episodesPath || !ncode || !hasFlag("--yes-save-drafts")) {
  usage();
  process.exit(2);
}

const start = argValue("--start") ? Number(argValue("--start")) : -Infinity;
const end = argValue("--end") ? Number(argValue("--end")) : Infinity;
const delayMs = Number(argValue("--delay-ms", "1200"));
const port = argValue("--port", "9223");

const payload = JSON.parse(await fs.readFile(episodesPath, "utf-8"));
const episodes = payload.episodes
  .filter((item) => item.number >= start && item.number <= end)
  .sort((a, b) => a.number - b.number);

if (episodes.length === 0) {
  throw new Error("No episodes matched the requested range.");
}

const browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
const contexts = browser.contexts();
const page =
  contexts.flatMap((context) => context.pages()).find((candidate) => candidate.url().includes("syosetu.com")) ??
  (await contexts[0].newPage());

await page.bringToFront();

async function sleep(ms) {
  await page.waitForTimeout(ms);
}

async function waitForInputForm() {
  await page.waitForSelector('input[name="subtitle"]', { timeout: 30000 });
  await page.waitForSelector('textarea[name="novel"], textarea#novel', { timeout: 30000 });
}

async function clickDraftSave() {
  return page.evaluate(() => {
    const candidates = [...document.querySelectorAll('button, input[type="submit"]')];
    const visible = candidates.filter((el) => {
      const text = (el.value || el.textContent || "").replace(/\s+/g, " ").trim();
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      return (
        text === "下書き保存" &&
        !el.disabled &&
        rect.width > 0 &&
        rect.height > 0 &&
        style.display !== "none" &&
        style.visibility !== "hidden"
      );
    });
    const el = visible.find((candidate) => candidate.tagName.toLowerCase() === "input") || visible[0];
    if (!el) return false;
    el.scrollIntoView({ block: "center" });
    el.click();
    return true;
  });
}

async function saveEpisode(episode) {
  const inputUrl = `https://syosetu.com/draftepisode/input/ncode/${ncode}/`;
  await page.goto(inputUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
  await waitForInputForm();

  if (episode.body.length < 200 || episode.body.length > 70000) {
    throw new Error(`Episode ${episode.number} body length is outside Syosetu limits: ${episode.body.length}`);
  }

  await page.fill('input[name="subtitle"]', episode.title);
  await page.fill('textarea[name="novel"], textarea#novel', episode.body);

  const subtitleValue = await page.inputValue('input[name="subtitle"]');
  const bodyValue = await page.inputValue('textarea[name="novel"], textarea#novel');
  if (subtitleValue !== episode.title || bodyValue !== episode.body) {
    throw new Error(`Episode ${episode.number} did not fill correctly.`);
  }

  const waitForView = page
    .waitForURL(/\/draftepisode\/view\/draftepisodeid\/\d+\//, {
      timeout: 60000,
      waitUntil: "domcontentloaded",
    })
    .catch(() => null);

  const clicked = await clickDraftSave();
  if (!clicked) {
    throw new Error(`Episode ${episode.number}: draft save button was not found.`);
  }

  await waitForView;
  await page.waitForLoadState("domcontentloaded", { timeout: 30000 }).catch(() => {});
  await sleep(500);

  const url = page.url();
  const text = await page.locator("body").innerText({ timeout: 30000 });
  if (!url.includes("/draftepisode/view/draftepisodeid/")) {
    throw new Error(`Episode ${episode.number}: save did not reach a draft detail page. Current URL: ${url}\n${text.slice(0, 600)}`);
  }
  if (!text.includes("下書き") || !text.includes(episode.title)) {
    throw new Error(`Episode ${episode.number}: saved page did not show expected draft title.\n${text.slice(0, 600)}`);
  }

  const draftId = url.match(/draftepisodeid\/(\d+)/)?.[1] ?? "";
  return { number: episode.number, title: episode.title, draftId, url };
}

const results = [];
try {
  console.log(`Uploading ${episodes.length} episode(s) to ncode ${ncode}.`);
  for (const episode of episodes) {
    const result = await saveEpisode(episode);
    results.push(result);
    console.log(`SAVED ${String(episode.number).padStart(2, "0")} ${result.draftId} ${episode.title}`);
    if (delayMs > 0) await sleep(delayMs);
  }
  console.log("UPLOAD_COMPLETE");
  console.log(JSON.stringify({ ncode, count: results.length, results }, null, 2));
} finally {
  await browser.close();
}
