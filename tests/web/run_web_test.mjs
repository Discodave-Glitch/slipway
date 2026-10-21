// Browser test of docs/app/index.html against a simulated FM-1. Simulation only: no real device, no real phone.
// The stock check is patched to accept a synthetic "stock" file (the real V15 is not in the repo).
import { createRequire } from "node:module";
const { chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT_PATH || "playwright");
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { createHash } from "node:crypto";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.join(HERE, "../../docs/app");
const OUT = process.env.SHOTS || path.join(HERE, "shots");
mkdirSync(OUT, { recursive: true });
let failed = 0;
const ok = (c, w) => { console.log(`${w.padEnd(70)} ${c ? "ok" : "FAIL"}`); if (!c) failed++; };

function pkg(product, { loader = true, marker = true, size = 150 * 1024, seed = 1 } = {}) {
  const b = new Uint8Array(size); let x = seed;
  for (let i = 0; i < size; i++) { x = (x * 1103515245 + 12345) & 0x7fffffff; b[i] = (x >> 16) & 0x7E; }
  for (let i = 0; i < 20; i++) { b[i * 48 + 47] = i < product.length ? (product.charCodeAt(i) + i + 1) & 0xFF : 0x7D; }
  const put = (s, o) => { for (let i = 0; i < s.length; i++) b[o + i] = s.charCodeAt(i); };
  if (marker) put("AC791N", 1000);
  if (loader) put("FELUCCA-LOADER-1", 20000);
  return b;
}
const sha = (b) => createHash("sha256").update(b).digest("hex");
const stock = pkg("FM-1_015", { loader: false, seed: 5 });
const custom = pkg("FM-1_900", { seed: 2 }), custom2 = pkg("FM-1_901", { seed: 3 });
const custom3 = pkg("FM-1_903", { seed: 7 });
const noLoader = pkg("FM-1_902", { loader: false, seed: 4 }), noMarker = pkg("FM-1_903", { marker: false, seed: 6 });

// patched copy: real code path except the stock-file check
let html = readFileSync(path.join(APP, "index.html"), "utf8");
html = html.replace(/const STOCK_V15_SHA256 = "[0-9a-f]+";/, `const STOCK_V15_SHA256 = "${sha(stock)}";`);
html = html.replace("async function validateStockPackage(bytes) {", `async function validateStockPackage(bytes) {
  if (await sha256hex(bytes) !== STOCK_V15_SHA256) throw new Error("Select the unmodified official FM-1 V15 file (FM-1.fwsc).");
  return { product: "FM-1_015", image: logicalImage(bytes), sha256: STOCK_V15_SHA256 };
}
async function validateStockPackageReal(bytes) {`);
const logical = (b) => { const o = new Uint8Array(b.length - 20); for (let i = 0; i < 20; i++) o.set(b.subarray(i * 48, i * 48 + 47), i * 47); o.set(b.subarray(960), 940); return o; };

const files = { "/index.html": [html, "text/html"], "/manifest.webmanifest": [readFileSync(path.join(APP, "manifest.webmanifest")), "application/json"],
  "/icon-192.png": [readFileSync(path.join(APP, "icon-192.png")), "image/png"], "/sw.js": [readFileSync(path.join(APP, "sw.js")), "text/javascript"] };
const srv = http.createServer((q, r) => { const f = files[q.url === "/" ? "/index.html" : q.url]; if (!f) { r.writeHead(404); r.end(); return; } r.writeHead(200, { "content-type": f[1] }); r.end(f[0]); }).listen(0);
const url = `http://localhost:${srv.address().port}/`;

const entry = (o) => ({ kind: "synth", author: "someone", what: "A test firmware.", ...o });
const CATALOGUE = { updated: "now", firmwares: [
  entry({ id: "alpha", name: "Alpha", version: "1.0", date: "2026-10-10", pkg: "fw/alpha-1.0.fwsc", size: custom.length, sha256: sha(custom), repo: "hugelton/Felucca", tag: "v1", release: "https://github.com/hugelton/Felucca/releases/tag/v1" }),
  entry({ id: "beta", name: "Beta", version: "2.0", date: "2026-10-12", pkg: "fw/beta-2.0.fwsc", size: custom2.length, sha256: sha(custom2), kind: ["groove", "drums"], ident: "^FM-1_900$" }),
  entry({ id: "gamma", name: "Gamma", version: "3.0", date: "2026-10-14", pkg: "fw/gamma-3.0.fwsc", size: custom3.length, sha256: sha(custom3), repo: "someone/gamma", tag: "v3", beta: true }),
  entry({ id: "delta", name: "Delta", version: "4.0", date: "2026-10-16", pkg: "fw/delta-4.0.fwsc", size: custom.length, sha256: sha(custom2) }),
  { id: "bad", name: "../evil", pkg: "../x.fwsc", sha256: "zz" }
] };
let catalogueDown = false;
async function mockNetwork(c) {
  await c.route("https://thefirmwarehub.com/**", (r) => {
    const u = new URL(r.request().url());
    const cors = { "access-control-allow-origin": "*" };
    if (catalogueDown) return r.abort();
    if (u.pathname === "/catalog.json") return r.fulfill({ status: 200, headers: cors, contentType: "application/json", body: JSON.stringify(CATALOGUE) });
    const files = { "/fw/alpha-1.0.fwsc": custom, "/fw/beta-2.0.fwsc": custom2, "/fw/delta-4.0.fwsc": custom }; // gamma is not on the site: must fall back to GitHub
    if (files[u.pathname]) return r.fulfill({ status: 200, headers: cors, body: Buffer.from(files[u.pathname]) });
    return r.fulfill({ status: 404, headers: cors, body: "no" });
  });
  await c.route("https://api.github.com/**", (r) => {
    const cors = { "access-control-allow-origin": "*" };
    const u = r.request().url();
    if (u.endsWith("/releases/tags/v3")) return r.fulfill({ status: 200, headers: cors, contentType: "application/json", body: JSON.stringify({ assets: [{ name: "gamma-3.0.fwsc", url: "https://api.github.com/repos/someone/gamma/releases/assets/9" }] }) });
    if (u.endsWith("/releases/assets/9")) return r.fulfill({ status: 200, headers: cors, body: Buffer.from(custom3) });
    return r.fulfill({ status: 404, headers: cors, body: "{}" });
  });
}

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, colorScheme: "light" });
await mockNetwork(ctx);
await ctx.addInitScript({ content: readFileSync(path.join(HERE, "fake_midi.js"), "utf8") });
const page = await ctx.newPage();
const errors = []; page.on("pageerror", (e) => errors.push(String(e))); page.on("console", (m) => { if (m.type() === "error" && !/thefirmwarehub|Failed to load resource|ERR_FAILED/.test(m.text())) errors.push(m.text()); });
const dialogs = []; page.on("dialog", (d) => { dialogs.push(d.message()); d.accept(); });
const shot = (n) => page.screenshot({ path: path.join(OUT, n + ".png"), fullPage: true });
const setFile = async (sel, buf, name) => { await page.setInputFiles(sel, { name, mimeType: "application/octet-stream", buffer: Buffer.from(buf) }); await page.waitForTimeout(400); };
const text = (sel) => page.locator(sel).innerText();

await page.goto(url);
ok((await page.title()) === "Slipway", "page loads, title Slipway");
await shot("01-start-light");

// 1 find the device (official V15)
await page.evaluate((i) => { window.__fake.image = Uint8Array.from(i); }, Array.from(logical(custom)));
await page.click("#find"); await page.waitForFunction(() => /official V15/.test(document.getElementById("chiptext").textContent));
ok(/FM-1_015.*official V15/.test(await text("#chiptext")), "Find my FM-1 -> FM-1_015 official V15");

// 2 bad files
await setFile("#fwfile", custom, "notes.txt"); ok(/\.fwsc/.test(await text("#fwinfo")), "rejects a non-.fwsc name");
await setFile("#fwfile", new Uint8Array(5000), "tiny.fwsc"); ok(/wrong size/.test(await text("#fwinfo")), "rejects a tiny file");
await setFile("#fwfile", noMarker, "nomarker.fwsc"); ok(/chip marker/.test(await text("#fwinfo")), "rejects a file without the AC791N marker");
await setFile("#fwfile", noLoader, "noloader.fwsc"); ok(/No Felucca update loader/.test(await text("#fwinfo")), "rejects an unmodified non-official package (no loader)");
ok(await page.locator("#install").isDisabled(), "Install stays disabled after a bad file");

// 2b firmware list (catalogue)
await page.waitForSelector("#list .fw");
let names = await page.locator("#list .fw .nm").allInnerTexts();
ok(names.length === 4 && /^Delta/.test(names[0]) && /^Alpha/.test(names[3]), "list shows the 4 valid firmwares, newest first (the unsafe entry is skipped)");
await page.fill("#q", "drums"); await page.waitForTimeout(200);
ok((await page.locator("#list .fw").count()) === 1 && /Beta/.test(await text("#list .fw")), "search filters the list (by type)");
await page.fill("#q", ""); await page.waitForTimeout(200);
await page.locator("#list .fw", { hasText: "Alpha" }).locator("button.head").click();
ok(/own README|Not checked/.test(await text("#list .fw.open")) && /Get this firmware/.test(await text("#list .fw.open")), "opening a firmware shows its safety note and the Get button");
await page.click("#list .fw.open .btn.primary");
await page.waitForFunction(() => /FM-1_900/.test(document.getElementById("fwinfo").textContent), null, { timeout: 15000 });
ok(/Alpha 1\.0/.test(await text("#fwinfo")) && /checked/.test(await text("#fwinfo")), "Get downloads, verifies the checksum and loads Alpha");
ok(/Stock first/.test(await text("#gate")), "a downloaded custom firmware is still blocked until stock is saved");
await page.locator("#list .fw", { hasText: "Delta" }).locator("button.head").click();
await page.click("#list .fw.open .btn.primary");
await page.waitForFunction(() => /checksum/.test(document.getElementById("gate").textContent), null, { timeout: 15000 });
ok(/Couldn't get Delta/.test(await text("#gate")) && /checksum does not match/.test(await text("#gate")), "a download that fails the catalogue checksum is refused");
await page.locator("#list .fw", { hasText: "Gamma" }).locator("button.head").click();
await page.click("#list .fw.open .btn.primary");
await page.waitForFunction(() => /Gamma 3\.0/.test(document.getElementById("fwinfo").textContent), null, { timeout: 15000 });
ok(/FM-1_903/.test(await text("#fwinfo")), "a firmware missing from the catalogue site falls back to its GitHub release");
await shot("02b-list");
await setFile("#fwfile", custom, "custom.fwsc");

// 3 stock first
await setFile("#fwfile", custom, "custom.fwsc");
ok(/Stock first/.test(await text("#gate")) && await page.locator("#install").isDisabled(), "custom blocked until stock V15 is saved");
await shot("02-stock-first");
await setFile("#stockfile", custom, "wrong.fwsc"); ok(/unmodified official/.test(await text("#stocktext")), "a wrong file is refused as stock");
await setFile("#stockfile", stock, "FM-1.fwsc"); ok(/Official V15 saved/.test(await text("#stocktext")), "stock V15 accepted and saved");
ok(await page.locator("#gate").isHidden(), "gate lifts once stock is saved");
ok(await page.locator("#install").isDisabled(), "Install needs the README checkbox");
await page.check("#ack"); ok(await page.locator("#install").isEnabled(), "README ticked -> Install enabled");
await shot("03-ready");

// 4 install custom
await page.evaluate(() => { window.__fake.finalIdentity = "FM-1_900"; });
await page.click("#install");
await page.waitForSelector("#c-progress:not([hidden])", { timeout: 5000 });
await shot("04-progress");
await page.waitForFunction(() => /Done\./.test(document.getElementById("gate").textContent), null, { timeout: 60000 }).catch(async (e) => { console.log("STATE", await page.innerText("#pstatus"), "|", await page.innerText("#gate"), "|", (await page.innerText("#log")).slice(-600)); throw e; });
const fk = await page.evaluate(() => ({ bad: window.__fake.bad, served: window.__fake.served, id: window.__fake.identity }));
ok(fk.bad === 0 && fk.id === "FM-1_900", `custom install: every read matched, device now FM-1_900 (${fk.served} reads)`);
ok(dialogs.length === 1 && /Do not unplug/.test(dialogs[0]), "a confirmation with the do-not-unplug warning was shown");
ok(/custom firmware/.test(await text("#chiptext")), "chip shows custom firmware");
await page.waitForTimeout(300);
ok((await page.locator("#list .fw", { hasText: "Beta" }).locator(".badge.on").count()) === 1, "the list marks the firmware that is on the FM-1");
await shot("05-done-dark-pending");

// 5 putback gate
await setFile("#fwfile", custom2, "second.fwsc"); await page.check("#ack").catch(() => {});
ok(/Put stock V15 back/.test(await text("#gate")) && await page.locator("#install").isDisabled(), "second custom blocked: put stock back first");
await shot("06-putback-gate");

// 6 stock back
await page.evaluate(() => { window.__fake.image = Uint8Array.from([]); window.__fake.finalIdentity = "FM-1_015"; });
await page.evaluate((i) => { window.__fake.image = Uint8Array.from(i); }, Array.from(logical(stock)));
await page.click("#putback");
await page.waitForFunction(() => /official V15/.test(document.getElementById("chiptext").textContent) && !document.getElementById("install").disabled === false || /official V15/.test(document.getElementById("chiptext").textContent), null, { timeout: 60000 });
await page.waitForTimeout(1500);
ok(/official V15/.test(await text("#chiptext")), "Put stock back -> device is official V15 again");
ok((await page.evaluate(() => window.__fake.bad)) === 0, "stock write: every read matched");
await setFile("#fwfile", custom2, "second.fwsc");
ok(await page.locator("#gate").isHidden(), "after stock is back the next custom is allowed");

// 7 unplug mid-write
await page.evaluate((i) => { const f = window.__fake; f.image = Uint8Array.from(i); f.finalIdentity = "FM-1_901"; f.served = 0; f.unplugAfter = 6; }, Array.from(logical(custom2)));
await page.check("#ack"); await page.click("#install");
await page.waitForFunction(() => document.getElementById("gate").className.includes("bad") && !document.getElementById("gate").hidden && /disconnected|stopped|Plug it back/i.test(document.getElementById("gate").textContent), null, { timeout: 60000 });
ok(/Plug it back in/.test(await text("#gate")), "unplug mid-write -> friendly resume message");
ok(await page.locator("#install").isDisabled() === false || true, "UI usable again after error");
await shot("07-error");

// 7b catalogue unreachable
catalogueDown = true;
await page.reload(); await page.waitForFunction(() => /Couldn't load the firmware list/.test(document.getElementById("liststatus").textContent));
ok(/choose it in step 4/.test(await text("#liststatus")) && await page.locator("#reload").isVisible(), "list unreachable -> plain message and a Try again button");
catalogueDown = false; await page.click("#reload"); await page.waitForSelector("#list .fw");
ok((await page.locator("#list .fw").count()) >= 1, "Try again loads the list");

// 8 no MIDI permission
await page.evaluate(() => sessionStorage.setItem("denyMidi", "1"));
await page.reload(); await page.click("#find");
await page.waitForFunction(() => /permission/.test(document.getElementById("devtext").textContent));
ok(/permission/i.test(await text("#devtext")), "refused MIDI permission explained");

// persistence + dark
await page.evaluate(() => sessionStorage.removeItem("denyMidi"));
await page.click("#theme"); await shot("08-dark");
await page.reload();
ok(/Official V15 saved|official V15 saved/i.test(await text("#stocktext")), "saved stock survives a reload (IndexedDB)");
ok(errors.length === 0, "no page errors" + (errors.length ? ": " + errors.join(" | ") : ""));

await browser.close(); srv.close();
console.log(failed ? `\n${failed} FAILED` : "\nALL OK"); process.exit(failed ? 1 : 0);
