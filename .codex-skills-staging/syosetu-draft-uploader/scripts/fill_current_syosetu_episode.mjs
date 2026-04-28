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
      "Usage: node fill_current_syosetu_episode.mjs --episodes episodes.json --number N [options]",
      "Options:",
      "  --port 9223",
      "  --title-selector CSS",
      "  --body-selector CSS",
      "  --save-selector CSS",
      "  --write       Fill the form. Omit for dry-run detection only.",
      "  --click-save  Click the save selector after filling.",
    ].join("\n"),
  );
}

const episodesPath = argValue("--episodes");
const number = Number(argValue("--number"));
if (!episodesPath || !Number.isInteger(number)) {
  usage();
  process.exit(2);
}

const payload = JSON.parse(await fs.readFile(episodesPath, "utf-8"));
const episode = payload.episodes.find((item) => item.number === number);
if (!episode) {
  throw new Error(`Episode ${number} not found in ${episodesPath}`);
}

const port = argValue("--port", "9223");
const browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
const pages = browser.contexts().flatMap((context) => context.pages());
const page =
  pages.find((candidate) => candidate.url().includes("syosetu.com")) ??
  pages[0];

if (!page) {
  throw new Error("No open Chrome pages found through CDP.");
}

await page.bringToFront();

async function detectSelectors() {
  return page.evaluate(() => {
    function selectorFor(el) {
      if (el.id) return `#${CSS.escape(el.id)}`;
      if (el.name) return `${el.tagName.toLowerCase()}[name="${CSS.escape(el.name)}"]`;
      const form = el.closest("form");
      const peers = [...(form || document).querySelectorAll(el.tagName.toLowerCase())];
      const index = peers.indexOf(el) + 1;
      return `${el.tagName.toLowerCase()}:nth-of-type(${index})`;
    }

    function labelFor(el) {
      const id = el.getAttribute("id");
      if (id) {
        const label = document.querySelector(`label[for="${CSS.escape(id)}"]`);
        if (label) return label.textContent || "";
      }
      const parentLabel = el.closest("label");
      if (parentLabel) return parentLabel.textContent || "";
      const row = el.closest("tr, .form-group, .p-form__item, dl, li, div");
      return row ? row.textContent || "" : "";
    }

    function scoreTitle(el) {
      const haystack = `${el.name} ${el.id} ${el.placeholder} ${el.getAttribute("aria-label") || ""} ${labelFor(el)}`;
      let score = 0;
      if (/サブタイトル|部分タイトル|話タイトル|章タイトル|タイトル/.test(haystack)) score += 10;
      if (/subtitle|title/i.test(haystack)) score += 5;
      if (el.tagName.toLowerCase() === "input") score += 2;
      return score;
    }

    function scoreBody(el) {
      const haystack = `${el.name} ${el.id} ${el.placeholder} ${el.getAttribute("aria-label") || ""} ${labelFor(el)}`;
      let score = 0;
      if (/本文|小説本文|原稿/.test(haystack)) score += 10;
      if (/honbun|body|text|novel/i.test(haystack)) score += 5;
      score += Math.min(5, Math.floor((Number(el.rows) || 0) / 5));
      return score;
    }

    function scoreSave(el) {
      const haystack = `${el.name} ${el.id} ${el.value || ""} ${el.textContent || ""} ${labelFor(el)}`;
      let score = 0;
      if (/下書き保存/.test(haystack)) score += 20;
      if (/保存|登録/.test(haystack)) score += 5;
      if ((el.getAttribute("type") || "").toLowerCase() === "submit") score += 3;
      return score;
    }

    const titleCandidates = [...document.querySelectorAll('input:not([type]), input[type="text"], textarea')]
      .map((el) => ({ selector: selectorFor(el), score: scoreTitle(el), label: labelFor(el).replace(/\s+/g, " ").trim().slice(0, 100) }))
      .sort((a, b) => b.score - a.score);

    const bodyCandidates = [...document.querySelectorAll("textarea")]
      .map((el) => ({ selector: selectorFor(el), score: scoreBody(el), label: labelFor(el).replace(/\s+/g, " ").trim().slice(0, 100) }))
      .sort((a, b) => b.score - a.score);

    const saveCandidates = [...document.querySelectorAll('button, input[type="submit"]')]
      .map((el) => ({ selector: selectorFor(el), score: scoreSave(el), label: labelFor(el).replace(/\s+/g, " ").trim().slice(0, 100), text: (el.value || el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 50) }))
      .sort((a, b) => b.score - a.score);

    return {
      title: titleCandidates[0] || null,
      body: bodyCandidates[0] || null,
      save: saveCandidates[0] || null,
      titleCandidates: titleCandidates.slice(0, 5),
      bodyCandidates: bodyCandidates.slice(0, 5),
      saveCandidates: saveCandidates.slice(0, 5),
    };
  });
}

const detected = await detectSelectors();
const titleSelector = argValue("--title-selector", detected.title?.selector);
const bodySelector = argValue("--body-selector", detected.body?.selector);
const saveSelector = argValue("--save-selector", detected.save?.selector);

const summary = {
  pageTitle: await page.title(),
  pageUrl: page.url(),
  episode: {
    number: episode.number,
    title: episode.title,
    path: episode.path,
    char_count: episode.char_count,
  },
  detected,
  selected: {
    titleSelector,
    bodySelector,
    saveSelector,
  },
  write: hasFlag("--write"),
  clickSave: hasFlag("--click-save"),
};

console.log(JSON.stringify(summary, null, 2));

if (!hasFlag("--write")) {
  console.log("DRY_RUN_ONLY");
  await browser.close();
  process.exit(0);
}

if (!titleSelector || !bodySelector) {
  throw new Error("Title/body selectors are required. Pass --title-selector and --body-selector explicitly.");
}

await page.fill(titleSelector, episode.title);
await page.fill(bodySelector, episode.body);
console.log("FILLED_NOT_SAVED");

if (hasFlag("--click-save")) {
  if (!saveSelector) {
    throw new Error("--save-selector is required with --click-save");
  }
  await page.click(saveSelector);
  console.log("CLICKED_SAVE");
}

await browser.close();
