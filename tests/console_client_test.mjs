// Offline checks of the console client's repaired functions (API-08, API-10, API-11 and R5-07): the functions are extracted
// from app.js unchanged and run in a fake DOM/network context with node's vm module, the way the audit's reproduction did.
// No browser, no network, no application writes. Exit code 0 when every assertion holds; tests/test_audit_console.py runs it.
// Every credential below is synthetic and assembled at run time (the public export scans tests/ for secret-shaped literals).
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

const TOKEN = "synthetic-" + "team-token";

// API-10 (and R5-07): copyPatch changes the clipboard only after a successful response; it fetches the plain artifact path
// with the team token in the header, so no credential enters a URL, and falls back to the download link only without a clipboard.
{
  const ctx = {
    clipboard: undefined, url: null, headers: null,
    fetch: async () => ({ ok: false, status: 404, text: async () => '{"detail":"artifact missing"}' }),
    navigator: { clipboard: { writeText: async (value) => { ctx.clipboard = value; } } },
    setTimeout: () => 0, location: {}, btn: { textContent: "Copy patch" },
    authHeaders: () => ({ "X-Attest-Token": TOKEN }), artUrl: (runId, name) => `/api/runs/${runId}/artifacts/${name}?ticket=synthetic`,
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
  ctx.fetch = async (url, opts) => { ctx.url = url; ctx.headers = (opts || {}).headers || {}; return { ok: true, status: 200, text: async () => "diff --git a/x b/x\n+1\n" }; };
  ctx.btn.textContent = "Copy patch";
  await vm.runInContext("copyPatch(btn, 'synthetic-run')", ctx);
  assert.equal(ctx.clipboard, "diff --git a/x b/x\n+1\n", "a 200 copies the exact patch text");
  assert.equal(ctx.btn.textContent, "Copied");
  assert.equal(ctx.url, "/api/runs/synthetic-run/artifacts/candidate.patch", "the plain artifact path: no token and no ticket in the URL");
  assert.equal(ctx.headers["X-Attest-Token"], TOKEN, "the team token travels in the header");
  assert.equal(ctx.location.href, undefined, "no navigation while the clipboard works");
  ctx.navigator.clipboard.writeText = async () => { throw new Error("clipboard unavailable"); };
  await vm.runInContext("copyPatch(btn, 'synthetic-run')", ctx);
  assert.equal(ctx.location.href, "/api/runs/synthetic-run/artifacts/candidate.patch?ticket=synthetic", "the fallback is the (ticketed) download link");
  assert.ok(!String(ctx.location.href).includes(TOKEN) && !String(ctx.url).includes(TOKEN), "the token value never appears in a URL");
  results.copy_patch_requires_ok = "ok";
}

// R5-07: artUrl/zipUrl never contain the token; a team run's links carry its ticket (minted once per run view) and nothing
// else does; public runs and signed-out viewers get no ticket at all.
{
  const posts = [];
  const a = {
    state: { runId: "team-run", token: TOKEN, team: true, ticket: null, detail: null, live: { status: null } },
    api: async (url, opts) => { posts.push([url, (opts || {}).method || "GET"]); return { ticket: "team-run.1760000000." + "ab".repeat(32), expires_in_s: 600 }; },
    setTimeout: () => 7, clearTimeout: () => {}, main: () => null, $$: () => [],
  };
  vm.createContext(a);
  vm.runInContext(extract("const authHeaders", "async function api("), a);
  assert.equal(vm.runInContext("JSON.stringify(authHeaders())", a), JSON.stringify({ "X-Attest-Token": TOKEN }), "reads carry the header after sign-in");
  assert.equal(vm.runInContext("artUrl('team-run', 'PROOF.md')", a), "/api/runs/team-run/artifacts/PROOF.md", "no ticket yet: no credential of any kind");
  assert.equal(vm.runInContext("zipUrl('team-run')", a), "/api/runs/team-run/bundle.zip");
  const t1 = await vm.runInContext("ensureTicket({ run_id: 'team-run', visibility: 'team' })", a);
  const t2 = await vm.runInContext("ensureTicket({ run_id: 'team-run', visibility: 'team' })", a);
  assert.equal(t1, "team-run.1760000000." + "ab".repeat(32));
  assert.equal(t1, t2, "one ticket per run view: the second call reuses it");
  assert.deepEqual(posts, [["/api/runs/team-run/download-ticket", "POST"]]);
  const art = vm.runInContext("artUrl('team-run', 'candidate.patch')", a), zip = vm.runInContext("zipUrl('team-run')", a);
  assert.equal(art, `/api/runs/team-run/artifacts/candidate.patch?ticket=${encodeURIComponent(t1)}`);
  assert.equal(zip, `/api/runs/team-run/bundle.zip?ticket=${encodeURIComponent(t1)}`);
  for (const url of [art, zip]) { assert.ok(!url.includes(TOKEN), "the token value is not in the URL"); assert.ok(!url.includes("token="), "no token parameter"); }
  assert.equal(vm.runInContext("artUrl('other-run', 'PROOF.md')", a), "/api/runs/other-run/artifacts/PROOF.md", "another run's links do not carry this ticket");
  assert.equal(vm.runInContext("zipUrl('other-run')", a), "/api/runs/other-run/bundle.zip");
  posts.length = 0;
  assert.equal(await vm.runInContext("ensureTicket({ run_id: 'public-run', visibility: 'public' })", a), null, "a public run gets no ticket");
  assert.deepEqual(posts, []);
  assert.equal(vm.runInContext("state.ticket", a), null, "and the previous run's ticket is dropped");
  assert.equal(vm.runInContext("zipUrl('public-run')", a), "/api/runs/public-run/bundle.zip", "public downloads carry no credential");
  vm.runInContext("state.team = false", a);
  assert.equal(vm.runInContext("JSON.stringify(authHeaders())", a), "{}", "signed out: no header");
  assert.equal(await vm.runInContext("ensureTicket({ run_id: 'team-run', visibility: 'team' })", a), null, "signed out: no ticket");
  assert.deepEqual(posts, []);
  vm.runInContext("state.team = true", a);
  a.api = async () => { const e = new Error("synthetic refusal"); e.status = 403; throw e; };
  assert.equal(await vm.runInContext("ensureTicket({ run_id: 'team-run', visibility: 'team' })", a), null, "a refused ticket leaves the links uncredentialed");
  assert.equal(vm.runInContext("zipUrl('team-run')", a), "/api/runs/team-run/bundle.zip");
  results.download_urls_carry_tickets_never_the_token = "ok";
}

// API-11: applyLiveUpdate shows the authoritative position, never a count derived from the queue size.
{
  const q = {
    state: { detail: { run: { run_id: "B" } }, live: { events: [], lastSeq: 0, status: "queued", meters: {} } },
    $: () => null, $$: () => [], reachedIndex: () => 0, dur: String, secsBetween: () => 0, usd: String, inferenceCost: (provider, v) => String(v), vclass: (v) => v,
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
    ensureTicket: async () => null,  // R5-07: the terminal view asks for a download ticket before it renders; stubbed here
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

// Revision 8: a live run starts only from the confirmation step. The Run button sends nothing; the confirmation's own button sends
// the request with X-Attest-Confirm; a hidden (closed or lapsed) confirmation sends nothing; and on a public host an automated
// browser (navigator.webdriver) is refused before any request exists.
{
  const elements = {};
  const el = (id) => (elements[id] = elements[id] || { id, hidden: true, disabled: false, textContent: "", className: "", value: "",
    focus() {}, scrollIntoView() {} });
  const sent = [];
  const c = {
    state: { mode: "live", profile: "nebius", profiles: [{ id: "nebius", public: true, short: "Nemotron" }], token: "", health: { budget: { per_run_cap_usd: 0.5, daily_cap_usd: 2, remaining_usd: 1.94 } } },
    $: (sel) => el(sel.replace(/^#/, "")), currentTask: () => ({ task_id: "durationkit-units-001", title: "Accept unit suffixes" }),
    currentProfile: () => ({ id: "nebius", public: true }), usd: (v) => "$" + Number(v).toFixed(3), REDUCED: true,
    api: async (path, opts) => { sent.push({ path, opts }); return { run_id: "r1", position: 0 }; },
    loadRuns: async () => {}, openRun: async () => {}, loadHealth: () => {}, renderEstimate: () => {},
    setTimeout: (fn, ms) => { c.timers.push([fn, ms]); return c.timers.length; }, clearTimeout: () => {}, timers: [],
    AUTOMATED: false, LOCAL_HOST: false,
  };
  vm.createContext(c);
  vm.runInContext(extract("const CONFIRM_MS = ", "async function signIn("), c);
  await vm.runInContext("startRun()", c);
  assert.equal(sent.length, 0, "the Run button sends nothing in live mode");
  assert.equal(el("confirm").hidden, false, "it opens the confirmation instead");
  assert.match(el("confirm-text").textContent, /billed to this project/);
  assert.match(el("confirm-text").textContent, /Sandboxes/);
  assert.match(el("confirm-text").textContent, /Tavily/);
  assert.equal(el("confirm-go").disabled, true, "the confirm button is briefly disabled, so a double click never passes through");
  await vm.runInContext("confirmStart()", c);
  assert.equal(sent.length, 0, "a press while the confirm button is still disabled sends nothing");
  c.timers.find(([, ms]) => ms === 700)[0]();  // the short disable lapses
  vm.runInContext("confirmClose()", c);
  await vm.runInContext("confirmStart()", c);
  assert.equal(sent.length, 0, "a closed (cancelled or lapsed) confirmation sends nothing");
  await vm.runInContext("startRun()", c); c.timers.filter(([, ms]) => ms === 700).pop()[0]();
  c.AUTOMATED = true;
  vm.runInContext("AUTOMATED = true", c);
  await vm.runInContext("confirmStart()", c);
  assert.equal(sent.length, 0, "an automated browser on a public host sends nothing");
  assert.match(el("start-note").textContent, /not started from an automated browser/);
  vm.runInContext("AUTOMATED = false", c);
  await vm.runInContext("startRun()", c); c.timers.filter(([, ms]) => ms === 700).pop()[0]();
  await vm.runInContext("confirmStart()", c);
  assert.equal(sent.length, 1, "the confirmed press sends exactly one request");
  assert.equal(sent[0].path, "/api/runs");
  assert.equal(sent[0].opts.method, "POST");
  assert.equal(sent[0].opts.headers["X-Attest-Confirm"], "start-run", "with the confirmation header the server requires");
  assert.deepEqual(JSON.parse(sent[0].opts.body), { task_id: "durationkit-units-001", provider: "nebius", admin_token: null });
  results.live_run_needs_confirmation = "ok";
}

// Revision 9: a run held for reconciliation (an operation's outcome is uncertain) is offered no new run; an ordinary ERROR still is.
{
  const ctx = { esc: (s) => String(s), artUrl: (id, name) => `/a/${id}/${name}`, zipUrl: (id) => `/z/${id}` };
  vm.createContext(ctx);
  vm.runInContext(extract("  function heldForReconciliation(", "  function caseBar("), ctx);
  const held = vm.runInContext(`actionsHtml({run_id: "r1", task_id: "t", status: "error", error_code: "reconciliation_required", has_artifacts: true},
                                           {bundle: {verdict: {verdict: "ERROR"}, reconciliation: {required: true}}})`, ctx);
  assert.ok(!held.includes("data-new-run"), "a held run offers no new run");
  assert.match(held, /Held for reconciliation/);
  const paused = vm.runInContext(`actionsHtml({run_id: "r2", task_id: "t", status: "error", error_code: "paused_for_reconciliation"}, null)`, ctx);
  assert.ok(!paused.includes("data-new-run"), "a run the service paused offers no new run either");
  const fromBundle = vm.runInContext(`actionsHtml({run_id: "r3", task_id: "t", status: "finished", has_artifacts: true},
                                                 {bundle: {verdict: {verdict: "ERROR"}, reconciliation: {required: true}}})`, ctx);
  assert.ok(!fromBundle.includes("data-new-run"), "the bundle's reconciliation record alone is enough");
  const ordinary = vm.runInContext(`actionsHtml({run_id: "r4", task_id: "t", status: "error", error_code: "pipeline_error"}, null)`, ctx);
  assert.ok(ordinary.includes("data-new-run"), "an ordinary infrastructure error still offers a new run");
  results.held_run_offers_no_new_run = "ok";
}

// Revision 10: while a run is held for reconciliation or the service has failed closed, the status chip says runs are paused and the
// live start is not offered (the API would answer 503); low disk keeps its own wording.
{
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(extract("  function pausedReason(", "  async function loadHealth("), ctx);
  assert.equal(vm.runInContext(`pausedReason({disk: {accepting_runs: true}, reconciliation: {accepting_runs: true}})`, ctx), null);
  assert.equal(vm.runInContext(`pausedReason({disk: {accepting_runs: true}, reconciliation: {accepting_runs: false, holds_open: 1}})`, ctx), "paused for reconciliation");
  assert.equal(vm.runInContext(`pausedReason({disk: {accepting_runs: true}, reconciliation: {accepting_runs: false, holds_open: 0, fail_closed: true}})`, ctx),
               "paused for reconciliation", "failed closed with no hold in the store is paused too");
  assert.equal(vm.runInContext(`pausedReason({disk: {accepting_runs: false}, reconciliation: {accepting_runs: false}})`, ctx), "paused, low disk");
  assert.equal(vm.runInContext(`pausedReason({})`, ctx), null, "an older service without the field is not paused by the page");
  results.paused_state_is_shown = "ok";
}

console.log(JSON.stringify({ ok: true, checks: results }));
