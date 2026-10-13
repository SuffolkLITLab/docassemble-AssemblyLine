/* Run with Node and Playwright: node --test tests/javascript/interview_list.test.cjs
 * Install Playwright and Chromium first. Set AL_TEST_BROWSER_CHANNEL=msedge to
 * use an installed Edge browser instead of Playwright's bundled Chromium.
 */
const { test, before, after } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const script = fs.readFileSync(path.join(__dirname,
  "../../docassemble/AssemblyLine/data/static/interview_list.js"), "utf8");
let browser;
before(async () => {
  browser = await chromium.launch({ headless: true,
    channel: process.env.AL_TEST_BROWSER_CHANNEL || undefined });
});
after(async () => { await browser.close(); });

async function fixture(t) {
  const page = await browser.newPage();
  t.after(() => page.close());
  await page.setContent(`<a class="al-session-form-title" data-loading-message="Cargando…"
    href="https://example.test/form"><span>Saved form</span></a>
    <a class="al-session-form-title" href="https://example.test/other">Other form</a>
    <a class="al-session-form-title" target="_blank" href="https://example.test/new">New tab</a>
    <a class="al-session-form-title" download href="https://example.test/download">Download</a>
    <a href="https://example.test/delete">Delete</a>`);
  await page.addScriptTag({ content: script });
  return page;
}

test("first click navigates once while repeated clicks show one waiting message", { timeout: 10000 }, async (t) => {
  const page = await fixture(t);
  let requests = 0;
  await page.route("https://example.test/form", async route => {
    requests++;
    await new Promise(resolve => setTimeout(resolve, 250));
    await route.fulfill({ body: "Form reopened", contentType: "text/html" });
  });
    const state = await page.evaluate(() => {
      document.querySelector("a span").click();
      const link = document.querySelector("a");
      link.click();
      link.click();
      return { busy: link.getAttribute("aria-busy"), disabled: link.getAttribute("aria-disabled"),
        statuses: document.querySelectorAll('[role="status"]').length,
        message: link.nextElementSibling.textContent.trim() };
    });
    assert.deepEqual(state, { busy: "true", disabled: "true", statuses: 1, message: "Cargando…" });
    await page.waitForURL("https://example.test/form");
    assert.equal(await page.locator("body").textContent(), "Form reopened");
    assert.equal(requests, 1);
});

test("modified clicks, new tabs, downloads and unrelated links stay available", async (t) => {
  const page = await fixture(t);
  const results = await page.evaluate(() => {
    // Observe the handler's decision before cancelling synthetic navigation.
    const observed = [];
    document.addEventListener("click", event => {
      observed.push({ prevented: event.defaultPrevented,
        statuses: document.querySelectorAll('[role="status"]').length });
      event.preventDefault();
    });
    const links = document.querySelectorAll("a");
    for (const option of [{ ctrlKey: true }, { metaKey: true }, { shiftKey: true },
      { altKey: true }, { button: 1 }]) {
      links[0].dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, ...option }));
    }
    for (const index of [2, 3, 4]) links[index].click();
    return observed;
  });
  assert.equal(results.length, 8);
  for (const result of results) assert.deepEqual(result, { prevented: false, statuses: 0 });
});

test("Back restores the links and keyboard activation can start another navigation", async (t) => {
  const page = await fixture(t);
  await page.evaluate(() => {
    document.addEventListener("click", event => event.preventDefault());
    document.querySelector("a").click();
    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
  });
  assert.equal(await page.locator(".al-session-loading-status").count(), 0);
  assert.equal(await page.locator("a").first().getAttribute("aria-disabled"), null);
  assert.equal(await page.locator("a").first().getAttribute("aria-busy"), null);
  await page.locator("a").first().focus();
  await page.keyboard.press("Enter");
  assert.equal(await page.locator(".al-session-loading-status").count(), 1);
});
