// Offline checks of the console client's repaired functions (API-08, API-10, API-11): the functions are extracted from
// app.js unchanged and run in a fake DOM/network context with node's vm module, the way the audit's reproduction did.
// No browser, no network, no application writes. Exit code 0 when every assertion holds; tests/test_audit_console.py runs it.
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(here, "../attest/app/static/app.js"), "utf8");
function extract(start, next) {
  const a = source.indexOf(start), b = source.indexOf(next, a);
  assert.ok(a >= 0 && b > a, `cannot extract the slice from ${start} to ${next}`);
  return source.slice(a, b);
}
const results = {};

// API-10: copyPatch changes the clipboard only after a successful response.
{
  const ctx = {
    clipboard: undefined, url: null,
    fetch: async () => ({ ok: false, status: 404, text: async () => '{"detail":"artifact missing"}' }),
    navigator: { clipboard: { writeText: async (value) => { ctx.clipboard = value; } } },
    setTimeout: () => 0, location: {}, btn: { textContent: "Copy patch" },
  };
  vm.createContext(ctx);
  vm.runInContext(extract("async function copyPatch(", "async function copyLink("), ctx);
  await vm.runInContext("copyPatch(btn, 'synthetic-run')", ctx);
  assert.equal(ctx.clipboard, undefined, "a 404 must leave the clipboard untouched");
  assert.match(ctx.btn.textContent, /^Copy failed \(404\)/);
  ctx.fetch = async () => ({ ok: false, status: 503, text: async () => '{"error":"bundle_incomplete"}' });
  ctx.btn.textContent = "Copy patch";
  await vm.runInContext("copyPatch(btn, 'synthetic-run')", ctx);
  assert.equal(ctx.clipboard, undefined, "a 503 must leave the clipboard untouched");
  assert.match(ctx.btn.textContent, /^Copy failed \(503\)/);
  ctx.fetch = async (url) => { ctx.url = url; return { ok: true, status: 200, text: async () => "diff --git a/x b/x\n+1\n" }; };
  ctx.btn.textContent = "Copy patch";
  await vm.runInContext("copyPatch(btn, 'synthetic-run', '/api/runs/synthetic-run/artifacts/candidate.patch?token=t')", ctx);
  assert.equal(ctx.clipboard, "diff --git a/x b/x\n+1\n", "a 200 copies the exact patch text");
  assert.equal(ctx.btn.textContent, "Copied");
  assert.equal(ctx.url, "/api/runs/synthetic-run/artifacts/candidate.patch?token=t", "the rendered (token-bearing) URL is used");
  results.copy_patch_requires_ok = "ok";
}

// API-11: applyLiveUpdate shows the authoritative position, never a count derived from the queue size.
{
  const q = {
    state: { detail: { run: { run_id: "B" } }, live: { events: [], lastSeq: 0, status: "queued", meters: {} } },
    $: () => null, $$: () => [], reachedIndex: () => 0, dur: String, secsBetween: () => 0, usd: String, vclass: (v) => v,
    liveHeaderText: () => ({ evidence: {} }), guide: { ctx: "queued" }, guideRefresh: () => {}, guideSet: () => {},
  };
  vm.createContext(q);
  vm.runInContext(extract("function applyLiveUpdate(", "async function pollLive("), q);
  vm.runInContext("applyLiveUpdate({ status: 'queued', events: [], queue: 2, current: 'A', position: 1 })", q);
  assert.equal(q.state.live.queueAhead, 1, "A running, B first in the queue: one run ahead of B");
  vm.runInContext("applyLiveUpdate({ status: 'queued', events: [], queue: 3, current: 'A', position: 1 })", q);
  assert.equal(q.state.live.queueAhead, 1, "D appended behind C does not change B's position");
  vm.runInContext("applyLiveUpdate({ status: 'queued', events: [], queue: 3, current: 'A' })", q);
  assert.equal(q.state.live.queueAhead, null, "without a position nothing is inferred from the queue size");
  vm.runInContext("applyLiveUpdate({ status: 'queued', events: [], queue: 3, current: 'A', position: 2 })", q);
  assert.equal(q.state.live.queueAhead, 2, "C reports two ahead");
  results.queue_position_is_authoritative = "ok";
}

// API-08: pollLive retries the final detail fetch with a visible recovery state and renders the terminal verdict without a reload.
{
  let detailCalls = 0;
  const rendered = [];
  const mainEl = { innerHTML: "" };
  const t = {
    state: { runId: "synthetic-run", runs: [], live: { lastSeq: 0, timer: 123, polls: 0 }, detail: { run: { status: "running" } } },
    window: { attestDebug: {} },
    api: async (url) => {
      if (url.includes("/events")) return { status: "finished" };
      detailCalls++;
      if (detailCalls === 1) { const e = new Error("synthetic transient detail failure"); e.status = 503; e.code = "bundle_incomplete"; e.retryAfter = 2; throw e; }
      return { run: { run_id: "synthetic-run", status: "finished", verdict: "VERIFIED" }, bundle: {} };
    },
    stopLive: () => { t.state.live.timer = null; }, loadRuns: async () => {}, loadHealth: () => {},
    renderFinished: (d) => { rendered.push(d); t.state.detail = d; },
    $: () => null, main: () => mainEl, caseBar: () => "", esc: String, setTimeout: (fn) => fn(),
  };
  vm.createContext(t);
  vm.runInContext(extract("async function pollLive(", "function loadingView("), t);
  await vm.runInContext("pollLive()", t);
  assert.equal(detailCalls, 2, "the first detail fetch failed, the second succeeded");
  assert.equal(rendered.length, 1, "the terminal view rendered once");
  assert.equal(t.state.detail.run.status, "finished");
  assert.equal(t.state.detail.run.verdict, "VERIFIED");
  assert.equal(t.state.live.timer, null);
  // persistent failure: bounded attempts, then an explicit recoverable error with a Retry control (never a stale running view)
  detailCalls = 0; rendered.length = 0;
  t.api = async (url) => { if (url.includes("/events")) return { status: "finished" }; detailCalls++; throw new Error("synthetic persistent failure"); };
  t.state.detail = { run: { status: "running" } }; t.state.live = { lastSeq: 0, timer: 123, polls: 0 };
  await vm.runInContext("pollLive()", t);
  assert.equal(detailCalls, 5, "five bounded attempts");
  assert.equal(rendered.length, 0);
  assert.match(mainEl.innerHTML, /data-retry-final="synthetic-run"/, "a Retry control is offered");
  assert.match(mainEl.innerHTML, /synthetic persistent failure/);
  // the Retry control re-runs the final fetch and installs the terminal view
  t.api = async () => ({ run: { run_id: "synthetic-run", status: "finished", verdict: "NEEDS HUMAN" }, bundle: {} });
  const ok = await vm.runInContext("finishLive('synthetic-run')", t);
  assert.equal(ok, true);
  assert.equal(rendered.length, 1);
  assert.equal(t.state.detail.run.verdict, "NEEDS HUMAN");
  results.terminal_detail_retried = "ok";
}

console.log(JSON.stringify({ ok: true, checks: results }));
