// Execute the original, narrowly extracted client functions in a fake DOM/network context.
// No browser, external network, credentials or application writes.
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";

const audit = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(audit, "../../attest/app/static/app.js"), "utf8");
function extract(start, next) {
  const a = source.indexOf(start), b = source.indexOf(next, a);
  assert.ok(a >= 0 && b > a);
  return source.slice(a, b);
}
const results = { scope: "offline JavaScript functions extracted unchanged from app.js", checks: {} };

const copy = {
  fetch: async () => ({ ok: false, status: 404, text: async () => '{"detail":"artifact missing"}' }),
  navigator: { clipboard: { writeText: async value => { copy.clipboard = value; } } },
  setTimeout: () => 0, location: {}, btn: { textContent: "Copy patch" },
};
vm.createContext(copy);
vm.runInContext(extract("async function copyPatch(", "async function copyLink("), copy);
await vm.runInContext("copyPatch(btn, 'synthetic-run')", copy);
assert.equal(copy.btn.textContent, "Copied");
assert.equal(copy.clipboard, '{"detail":"artifact missing"}');
results.checks.copy_patch_false_success = { artifact_status: 404, button: copy.btn.textContent, copied: copy.clipboard, confirmed: true };

const q = {
  state: { detail: { run: { run_id: "B" } }, live: { events: [], lastSeq: 0, status: "queued", meters: {} } },
  $: () => null, $$: () => [], reachedIndex: () => 0, dur: String, secsBetween: () => 0, usd: String,
  liveHeaderText: () => ({ evidence: {} }), guide: { ctx: "queued" }, guideRefresh: () => {},
};
vm.createContext(q);
vm.runInContext(extract("function applyLiveUpdate(", "async function pollLive("), q);
vm.runInContext("applyLiveUpdate({ status: 'queued', events: [], queue: 2, current: 'A' })", q);
assert.equal(q.state.live.queueAhead, 2);
results.checks.queue_position_counts_later_runs = {
  actual_order: "A running; B queued first; C queued second", selected_run: "B",
  expected_runs_ahead: 1, shown_runs_ahead: q.state.live.queueAhead, confirmed: true,
};

const terminal = {
  state: { runId: "synthetic-run", live: { lastSeq: 0, timer: 123, polls: 0 }, detail: { run: { status: "running" } } },
  window: { attestDebug: {} },
  api: async url => { if (url.includes("/events")) return { status: "finished" }; throw new Error("synthetic transient detail failure"); },
  stopLive: () => { terminal.state.live.timer = null; }, loadRuns: async () => {},
  renderFinished: () => { terminal.rendered = true; }, loadHealth: () => {},
};
vm.createContext(terminal);
vm.runInContext(extract("async function pollLive(", "function loadingView("), terminal);
await vm.runInContext("pollLive()", terminal);
assert.equal(terminal.state.live.timer, null);
assert.equal(terminal.rendered, undefined);
assert.equal(terminal.state.detail.run.status, "running");
results.checks.terminal_detail_failure_stops_refresh = {
  terminal_event_status: "finished", detail_request: "transient failure", polling_timer: terminal.state.live.timer,
  displayed_detail_status: terminal.state.detail.run.status, rendered_terminal_view: !!terminal.rendered, confirmed: true,
};
fs.writeFileSync(path.join(audit, "console-repro-results.json"), JSON.stringify(results, null, 2) + "\n");
console.log(JSON.stringify({ check_count: Object.keys(results.checks).length, all_behavior_assertions_passed: true }));
