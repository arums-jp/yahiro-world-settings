#!/usr/bin/env node
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

function argValue(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
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

const snapshot = await page.evaluate(() => {
  function compact(text) {
    return (text || "").replace(/\s+/g, " ").trim().slice(0, 120);
  }

  function labelFor(el) {
    const id = el.getAttribute("id");
    if (id) {
      const label = document.querySelector(`label[for="${CSS.escape(id)}"]`);
      if (label) return compact(label.textContent);
    }
    const parentLabel = el.closest("label");
    if (parentLabel) return compact(parentLabel.textContent);
    const row = el.closest("tr, .form-group, .p-form__item, dl, li, div");
    return row ? compact(row.textContent) : "";
  }

  const controls = [...document.querySelectorAll("input, textarea, select, button, a")]
    .filter((el) => {
      const style = getComputedStyle(el);
      return style.display !== "none" && style.visibility !== "hidden";
    })
    .map((el, index) => ({
      index,
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute("type") || "",
      name: el.getAttribute("name") || "",
      id: el.getAttribute("id") || "",
      href: el.tagName.toLowerCase() === "a" ? el.getAttribute("href") || "" : "",
      placeholder: el.getAttribute("placeholder") || "",
      ariaLabel: el.getAttribute("aria-label") || "",
      label: labelFor(el),
      text: compact(el.textContent),
      valueLength:
        el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement
          ? el.value.length
          : undefined,
    }));

  return {
    title: document.title,
    url: location.href,
    headings: [...document.querySelectorAll("h1, h2, h3")].map((el) => compact(el.textContent)),
    controls,
  };
});

console.log(JSON.stringify(snapshot, null, 2));
await browser.close();
