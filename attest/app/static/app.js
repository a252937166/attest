/* Attest console client. One static page, no framework. A run reads like a case file: decision header, tabs, numbered
   exhibits. Live runs are updated in place (keyed updates): the log appends rows, the stepper and meters change text,
   and the detail pane is never rebuilt while a run is in progress, so open disclosures, the selected tab and keyboard
   focus survive every refresh. */
(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const qs = new URLSearchParams(location.search);
  const POLL_MS = Math.max(300, Number(qs.get("poll")) || 4000);
  const usd = (v) => (v == null ? "allowance" : "$" + Number(v).toFixed(3));
  const usdOrNa = (v) => (v == null ? "not billed in USD (team allowance)" : "$" + Number(v).toFixed(4));
  const when = (iso) => (iso ? iso.slice(0, 16).replace("T", " ") + " UTC" : "");
  const secsBetween = (a, b) => (a && b ? Math.max(0, Math.round((new Date(b) - new Date(a)) / 1000)) : null);
  const dur = (s) => (s == null ? "" : s >= 60 ? `${Math.floor(s / 60)} min ${Math.round(s % 60)} s` : `${Math.round(s)} s`);
  const vclass = (v) => (v || "").split(" ")[0];
  const short = (id) => (id || "").split(".").pop();
  const kb = (b) => (b == null ? "" : b >= 1024 ? (b / 1024).toFixed(1) + " KB" : b + " B");
  const STAGES = [["freeze", "Freeze"], ["checkpoint", "Checkpoint"], ["spec", "Specify"], ["seal", "Seal tests"], ["red", "Red check"],
    ["implement", "Implement"], ["verify", "Verify"], ["break", "Break"], ["audit", "Audit"], ["finished", "Attest"]];
  const STAGE_ALIAS = { heldout: "verify", arbitrate: "audit", aborted: "finished", error: "finished", starting: "freeze", queued: null, budget: null, disk: null, retention: "finished" };
  const STAGE_HELP = ["Freeze: hash the task, repository files and specification.", "Checkpoint: build the retained image and run the baseline suite.",
    "Specify and seal tests: an independent model instance writes the contract and the acceptance tests before any code exists.",
    "Red check: the sealed tests must fail on the unmodified base.", "Implement: the implementer works through validated JSON actions and never sees the sealed tests.",
    "Verify: a fresh branch runs the sealed suite, one process per test, nonce-bound; the existing and held-out suites run in their own branches.",
    "Break and audit: mutants, tests written after the patch, the drift audit and, when generated tests fail, the advisory arbitration.",
    "Attest: the verdict is computed only from the recorded gates and the Proof Bundle is written."];
  const PROVIDER_LABEL = { nebius: "Nemotron on Nebius Token Factory" };
  const providerLabel = (p) => PROVIDER_LABEL[p] || "development provider (team allowance)";
  const PROV_TEXT = { live: "Live run started from this console", imported: "Recorded evidence", synthetic: "Synthetic fixture: replayed from a recorded run, not a live execution" };

  const state = { runId: null, tab: "overview", filter: "all", mode: "browse", task: null, profiles: [], profile: null, token: "", team: false,
    tasks: [], runs: [], health: null, detail: null, expanded: new Set(), onlyRed: false,
    live: { timer: null, lastSeq: 0, events: [], status: null, stage: null, meters: {}, polls: 0 } };
  window.attestDebug = { polls: 0, renders: 0, panelRenders: 0 };

  // ------------------------------------------------------------------ storage (per-viewer convenience, never required)
  const storage = {
    get(key) { try { return sessionStorage.getItem(key); } catch (e) { return null; } },
    set(key, value) { try { sessionStorage.setItem(key, value); } catch (e) { /* storage unavailable: the page still works */ } },
  };
  const loadExpanded = (runId) => { state.expanded = new Set(); try { JSON.parse(storage.get("attest.expanded." + runId) || "[]").forEach((k) => state.expanded.add(k)); } catch (e) { /* ignore */ } };
  const saveExpanded = () => { if (state.runId) storage.set("attest.expanded." + state.runId, JSON.stringify([...state.expanded])); };
  const focusId = () => { const a = document.activeElement; return a && a.dataset ? a.dataset.focus || null : null; };
  const restoreFocus = (id) => { if (!id) return; const el = document.querySelector(`[data-focus="${id}"]`); if (el && el !== document.activeElement) el.focus({ preventScroll: true }); };

  async function api(path, opts) {
    const res = await fetch(path, opts);
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(body.detail || body.error || res.statusText);
    return body;
  }

  // ------------------------------------------------------------------ status chips
  function renderStatus() {
    const h = state.health;
    const dot = $("#chip-service-dot"), text = $("#chip-service-text");
    if (!h) { text.textContent = "Service unreachable"; dot.className = "dot idle"; $("#chip-budget-text").textContent = "unknown"; $("#chip-runs-text").textContent = "unknown"; return; }
    const busy = !!h.current || h.queue > 0;
    dot.className = "dot " + (busy ? "live" : "idle");
    text.textContent = busy ? `Live service: ${h.current ? "running " + h.current : ""}${h.queue ? `${h.current ? ", " : ""}${h.queue} queued` : ""}` : "Live service idle, showing recorded evidence";
    const b = h.budget || {};
    $("#chip-budget-text").textContent = b.remaining_usd != null ? `$${Number(b.remaining_usd).toFixed(2)} of $${Number(b.daily_cap_usd).toFixed(2)} left` : "unknown";
    $("#chip-runs-text").textContent = h.disk && h.disk.accepting_runs === false ? "paused, low disk" : "accepted";
  }

  async function loadHealth() {
    try { state.health = await api("/api/health"); } catch (e) { state.health = null; }
    renderStatus(); renderEstimate();
  }

  // ------------------------------------------------------------------ workspace
  const currentTask = () => state.tasks.find((t) => t.task_id === state.task) || state.tasks[0] || null;
  const currentProfile = () => state.profiles.find((p) => p.id === state.profile) || state.profiles[0] || null;

  function renderTasks() {
    const sel = $("#task");
    const keep = state.task;
    sel.innerHTML = state.tasks.map((t) => `<option value="${esc(t.task_id)}">${esc(t.title)}${t.heldout ? " (with held-out tests)" : ""}</option>`).join("");
    if (!state.tasks.some((t) => t.task_id === keep)) state.task = state.tasks[0] ? state.tasks[0].task_id : null;
    if (state.task) sel.value = state.task;
    renderEstimate();
  }

  function renderProfiles() {
    const field = $("#profile-field"), sel = $("#profile");
    const live = state.mode === "live";
    if (state.profiles.length > 1) {
      sel.innerHTML = state.profiles.map((p) => `<option value="${esc(p.id)}">${esc(p.label)}</option>`).join("");
      if (!state.profiles.some((p) => p.id === state.profile)) state.profile = state.profiles[0].id;
      sel.value = state.profile;
      field.hidden = !live;
    } else { field.hidden = true; state.profile = state.profiles[0] ? state.profiles[0].id : null; }
    const p = currentProfile();
    $("#mode-live-label").textContent = `Run live on ${p ? p.short : "Nemotron"}`;
    const h = state.health || {};
    $("#public-note").textContent = `Public runs use the ${state.profiles[0] ? state.profiles[0].short : "Nemotron"} profile: ${h.public_runs_per_hour ?? 3} per hour per visitor, $${Number((h.budget || {}).per_run_cap_usd ?? 0.5).toFixed(2)} per run.`;
  }

  function renderEstimate() {
    const t = currentTask();
    const box = $("#estimate"), go = $("#go");
    if (!t) { box.innerHTML = "No sample tasks are configured."; go.disabled = true; return; }
    const e = t.estimate || {};
    const h = state.health || {};
    const b = h.budget || {};
    const p = currentProfile();
    if (state.mode === "browse") {
      box.innerHTML = e.latest_run_id ? `Opens the latest recorded run of this task (${esc(e.latest_verdict || "finished")}). No inference, no cost.`
        : "No recorded run of this task yet. Pick another task or run it live.";
      go.textContent = "Open the latest recorded run";
      go.disabled = !e.latest_run_id;
    } else {
      const range = e.runs ? `Recorded runs of this task cost <strong>${e.cost_min_usd != null ? `${usd(e.cost_min_usd)} to ${usd(e.cost_max_usd)}` : "an allowance, not USD"}</strong>, <strong>${dur(e.duration_min_s)} to ${dur(e.duration_max_s)}</strong> (${e.runs} run${e.runs === 1 ? "" : "s"}).`
        : "No recorded runs of this task yet, so there is no estimate.";
      const budget = b.remaining_usd != null ? ` Up to ${usd(b.per_run_cap_usd)} is reserved against today's cap while the run is queued or running; <strong>$${Number(b.remaining_usd).toFixed(2)}</strong> remains.` : "";
      box.innerHTML = range + budget;
      go.textContent = `Run live on ${p ? p.short : "Nemotron"}`;
      go.disabled = !(h.worker_alive !== false) || (h.disk && h.disk.accepting_runs === false) || (p && p.public && b.nebius_ok === false);
    }
    renderProfiles();
  }

  async function loadTasks() {
    try { state.tasks = (await api("/api/tasks")).tasks || []; } catch (e) { state.tasks = []; }
    renderTasks();
  }

  async function loadProfiles(token) {
    try {
      const body = token ? await api("/api/profiles", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ admin_token: token }) })
        : await api("/api/profiles");
      state.profiles = body.profiles || []; state.team = !!body.team;
    } catch (e) { if (!state.profiles.length) state.profiles = [{ id: "nebius", label: "NVIDIA Nemotron on Nebius Token Factory", short: "Nemotron", public: true }]; }
    renderEstimate();
  }

  // ------------------------------------------------------------------ history (keyed by run id)
  const FILTERS = [["all", "All"], ["VERIFIED", "Verified"], ["NEEDS HUMAN", "Needs human"], ["ERROR", "Errors"]];
  function rowVerdict(r) { return r.status === "finished" ? r.verdict || "ERROR" : r.status === "error" ? "ERROR" : r.status.toUpperCase(); }
  function rowMatches(r) {
    if (state.filter === "all") return true;
    const v = rowVerdict(r);
    return state.filter === "ERROR" ? v === "ERROR" : v === state.filter;
  }
  function historyRowHtml(r) {
    const s = r.summary || {};
    const v = rowVerdict(r);
    const prov = s.provenance || "imported";
    const stage = r.status === "running" || r.status === "queued" ? (r.stage && r.stage !== r.status ? `, stage ${r.stage}` : "") : "";
    const meta = `${prov === "synthetic" ? "synthetic fixture" : prov === "live" ? "live" : "recorded"}, ${when(r.created_at)}${s.cost_committed_usd != null || s.cost_usd != null ? ", " + usd(s.cost_committed_usd ?? s.cost_usd) : ""}${s.duration_s != null ? ", " + dur(s.duration_s) : ""}${stage}`;
    return `<button type="button" data-run="${esc(r.run_id)}" data-focus="hist-${esc(r.run_id)}" aria-current="${state.runId === r.run_id}">
      <span class="t">${esc(r.task_title)}</span><span class="seal ${vclass(v)}">${esc(v)}</span>
      <span class="m"><span class="dot ${prov === "synthetic" ? "synthetic" : prov === "live" ? "live" : ""}"></span>${esc(meta)}</span></button>`;
  }
  function renderFilters() {
    $("#filters").innerHTML = FILTERS.map(([k, l]) => `<button type="button" data-filter="${k}" data-focus="filter-${k}" aria-pressed="${state.filter === k}">${l}</button>`).join("");
  }
  function renderHistory() {
    const list = $("#history");
    const rows = state.runs.filter(rowMatches);
    const f = focusId();
    const seen = new Set();
    let empty = list.querySelector("li[data-empty]");
    rows.forEach((r, index) => {
      seen.add(r.run_id);
      const html = historyRowHtml(r);
      let li = list.querySelector(`li[data-id="${CSS.escape(r.run_id)}"]`);
      if (!li) { li = document.createElement("li"); li.dataset.id = r.run_id; li.dataset.sig = ""; }
      if (li.dataset.sig !== html) { li.innerHTML = html; li.dataset.sig = html; }
      const at = list.children[index];
      if (at !== li) list.insertBefore(li, at || null);
    });
    $$("li[data-id]", list).forEach((li) => { if (!seen.has(li.dataset.id)) li.remove(); });
    if (!rows.length) {
      if (!empty) { empty = document.createElement("li"); empty.dataset.empty = "1"; list.appendChild(empty); }
      empty.innerHTML = `<p class="note">${state.runs.length ? "No runs match this filter." : "No runs yet. Pick a task and open its recorded run, or run one live."}</p>`;
    } else if (empty) empty.remove();
    restoreFocus(f);
  }
  async function loadRuns() {
    try { const body = await api("/api/runs"); state.runs = body.runs || []; } catch (e) { /* keep the last list */ }
    renderHistory();
  }

  // ------------------------------------------------------------------ run views
  const main = () => $("#main");
  function setRoute(runId, replace) {
    const url = runId ? `/runs/${encodeURIComponent(runId)}#${state.tab}` : "/";
    if (replace) history.replaceState(null, "", url); else history.pushState(null, "", url);
  }
  function stopLive() { if (state.live.timer) { clearInterval(state.live.timer); state.live.timer = null; } }

  function emptyView() {
    return `<div class="empty"><h2>Pick a run from the history, or start one.</h2>
      <p>Attest treats every task as a claim that must be proven. Acceptance tests are sealed before any code exists, the candidate is verified in a fresh sandbox against the pristine sealed copy, and the Proof Bundle records the evidence. Every run ends in one of five verdicts, never a silent guess.</p>
      <div class="verdicts">
        <span class="seal VERIFIED">VERIFIED</span><p>Every gate passed in a fresh sandbox. Accept with the evidence.</p>
        <span class="seal NEEDS">NEEDS HUMAN</span><p>A gate failed or a generated test disagrees with the patch. Hold and decide.</p>
        <span class="seal INFEASIBLE">INFEASIBLE</span><p>The specification stage found the request contradictory or impossible as written.</p>
        <span class="seal NO">NO CHANGE</span><p>The implementer finished without changing any file.</p>
        <span class="seal ERROR">ERROR</span><p>The run did not complete (provider, sandbox, budget or disk). Nothing was certified.</p>
      </div></div>`;
  }

  function provenanceLine(run, detail) {
    const prov = (run.summary || {}).provenance || detail?.provenance || "imported";
    const text = prov === "synthetic" ? PROV_TEXT.synthetic : `${PROV_TEXT[prov] || PROV_TEXT.imported}: profile ${run.profile_label}, ${providerLabel(run.provider)}, ${when(run.started_at || run.created_at)}`;
    return `<p class="provenance"><span class="dot ${prov === "live" ? "live" : prov === "synthetic" ? "synthetic" : ""}"></span>${esc(text)}. Run ${esc(run.run_id)}</p>`;
  }

  function actionsHtml(run, detail) {
    const id = encodeURIComponent(run.run_id);
    const has = !!run.out_dir && !!(detail && detail.bundle);
    const art = (name) => `/api/runs/${id}/artifacts/${name}`;
    const verdict = detail?.bundle?.verdict?.verdict || (run.status === "error" ? "ERROR" : null);
    if (verdict === "ERROR") {
      return `${has ? `<a class="btn" href="/api/runs/${id}/bundle.zip">Download run record</a>` : `<span class="btn" aria-disabled="true" title="No run record was written">Download run record</span>`}
        ${has ? `<a class="btn secondary" href="${art("PROOF.md")}" target="_blank" rel="noopener">Open PROOF.md</a>` : ""}
        <button type="button" class="btn secondary" data-new-run="${esc(run.task_id)}" data-focus="act-new">Start a new run</button>`;
    }
    return `<a class="btn" href="/api/runs/${id}/bundle.zip">Download Proof Bundle</a>
      ${detail?.bundle?.candidate?.diff ? `<button type="button" class="btn secondary" data-copy-patch="${esc(run.run_id)}" data-focus="act-copy">Copy patch</button>` : ""}
      <a class="btn secondary" href="${art("PROOF.md")}" target="_blank" rel="noopener">Open PROOF.md</a>`;
  }

  function decisionHeader(seal, statement, explanation, evidence, provenance, actions) {
    return `<section class="decision" aria-labelledby="decision-h">
      <div><span class="seal big ${vclass(seal)}" id="decision-h" data-k="seal">${esc(seal)}</span></div>
      <div><p class="statement" data-k="statement">${esc(statement)}</p><p class="explain" data-k="explain">${esc(explanation)}</p>
        ${evidence ? `<p class="primary"><span class="exref" data-k="evref">${esc(evidence.ref)}</span><span data-k="evtext">${esc(evidence.text)}</span></p>` : ""}
        ${provenance}</div>
      <div class="actions">${actions}</div></section>`;
  }

  const TABS = [["overview", "Overview"], ["patch", "Patch"], ["tests", "Tests and counterexamples"], ["activity", "Activity"], ["files", "Files"]];
  function tabsHtml(enabled) {
    return `<div class="tabs" role="tablist" aria-label="Run sections">${TABS.map(([k, l]) => {
      const on = enabled[k] !== false;
      return `<button type="button" role="tab" id="tab-${k}" data-tab="${k}" data-focus="tab-${k}" aria-selected="${state.tab === k}" aria-controls="panel" tabindex="${state.tab === k ? 0 : -1}" ${on ? "" : `disabled title="${esc(enabled[k] || "Available when the run finishes")}"`}>${l}</button>`;
    }).join("")}</div>`;
  }
  function det(id, summary, body) {
    return `<details data-id="${esc(id)}" ${state.expanded.has(id) ? "open" : ""}><summary data-focus="det-${esc(id)}">${summary}</summary>${body}</details>`;
  }
  const mark = (status) => status === "pass" ? `<span class="ok">pass</span>` : status === "fail" ? `<span class="fail">fail</span>` : status === "informative" ? `<span class="skipc">advisory</span>` : status === "none" ? `<span class="skipc">none</span>` : `<span class="skipc">not run</span>`;

  function diffStats(diff) {
    const files = []; let cur = null;
    (diff || "").split("\n").forEach((l) => {
      if (l.startsWith("+++ ")) { cur = { path: l.slice(4).replace(/^b\//, ""), add: 0, del: 0 }; files.push(cur); }
      else if (cur && l.startsWith("+") && !l.startsWith("+++")) cur.add++;
      else if (cur && l.startsWith("-") && !l.startsWith("---")) cur.del++;
    });
    return files;
  }
  function diffHtml(diff) {
    return (diff || "").split("\n").map((l) => {
      const cls = l.startsWith("+++") || l.startsWith("---") ? "meta" : l.startsWith("+") ? "add" : l.startsWith("-") ? "del" : l.startsWith("@@") ? "hunk" : "";
      return `<span class="${cls}">${esc(l)}</span>`;
    }).join("\n");
  }
  const filesLine = (files) => files.map((f) => `<span class="mono">${esc(f.path)}</span> <span class="ok">+${f.add}</span> <span class="fail">-${f.del}</span>`).join(", ");

  // ---- panels for a finished run
  function overviewPanel(d) {
    const b = d.bundle, ex = d.exhibits, task = b.task || {}, cand = b.candidate || {}, spec = b.spec || {};
    const files = diffStats(cand.diff);
    const gates = ex.gates || [];
    const pass = gates.filter((g) => g.result === "pass").length, notRun = gates.filter((g) => g.result === "not_run").length, fail = gates.length - pass - notRun;
    const statement = task.statement || "";
    return `<div class="overview">
      <div class="block"><h3>What was requested</h3><p><strong>${esc(task.title || d.run.task_title)}</strong></p>
        <p>${esc(statement.length > 320 ? statement.slice(0, 320) + "…" : statement)}</p>
        ${det("statement", "Full task statement and the frozen specification", `<p>${esc(statement)}</p><p class="note">Frozen requirement: ${(spec.acceptance_criteria || task.acceptance_criteria || []).length} acceptance criteria, specification digest <span class="mono">${esc((task.spec_sha256 || "").slice(0, 12))}</span>, ${Object.keys(task.repo_files_sha256 || {}).length} repository files hashed.${spec.restated_task ? " Specification: " + esc(spec.restated_task) : ""}</p><ol class="plain">${(spec.acceptance_criteria || task.acceptance_criteria || []).map((c) => `<li>${esc(c)}</li>`).join("")}</ol>`)}
      </div>
      <div class="block"><h3>What changed</h3>
        ${files.length ? `<p>${files.length} file${files.length > 1 ? "s" : ""}: ${filesLine(files)}.</p>` : `<p>No patch was produced.</p>`}
        <p>Write scope ${cand.scope_ok === false ? `<span class="fail">violated</span>` : cand.scope_ok ? `<span class="ok">respected</span>` : `<span class="skipc">not checked</span>`}: allowed <span class="mono">${esc((task.allowed_write_globs || []).join(", "))}</span>; protected <span class="mono">${esc((task.protected_globs || []).join(", "))}</span>.</p>
        ${cand.tamper_scan ? `<p class="note">Static tamper scan: ${esc(cand.tamper_scan.summary)}.</p>` : ""}
        <p class="more"><a href="#patch" data-tab-link="patch">Open the patch</a></p>
      </div>
      <div class="block"><h3>Can I accept it</h3>
        <p><span class="seal ${vclass(b.verdict.verdict)}">${esc(b.verdict.verdict)}</span> ${gates.length ? `${pass} of ${gates.length} gates pass${fail ? `, ${fail} fail` : ""}${notRun ? `, ${notRun} not run` : ""}.` : "No gate was reached."}</p>
        ${(b.verdict.reasons || []).length ? `<ul class="plain">${b.verdict.reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>` : ""}
        <h4>What to do</h4><ul class="plain">${(ex.decision.decide || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
        ${(ex.decision.weak || []).length ? `<h4>Weak spots, disclosed</h4><ul class="plain">${ex.decision.weak.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}
        ${(b.verdict.warnings || []).length ? det("warnings", `Warnings recorded by the system (${b.verdict.warnings.length})`, `<ul class="plain">${b.verdict.warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul>`) : ""}
      </div>
      <div class="block"><h3>What the evidence says</h3>
        <div class="tablewrap"><table><tbody>${ex.exhibits.filter((e) => e.shown).map((e) => `<tr><td><span class="exref">${e.ref}</span></td><td>${esc(e.title)}</td><td>${mark(e.status)}</td><td>${esc(e.summary)}</td></tr>`).join("")}</tbody></table></div>
        <p class="more"><a href="#tests" data-tab-link="tests">Open tests and counterexamples</a></p>
      </div></div>`;
  }

  function patchPanel(d) {
    const b = d.bundle, cand = b.candidate || {}, task = b.task || {};
    const files = diffStats(cand.diff);
    if (!cand.diff) return `<div class="block"><p>No patch was produced; the run stopped at stage "${esc(b.stage || "unknown")}".</p></div>`;
    return `<div class="block"><h3>Candidate patch</h3>
      <dl class="kv"><dt>Files</dt><dd>${filesLine(files)}</dd>
      <dt>Write scope</dt><dd>${cand.scope_ok === false ? `<span class="fail">violated: ${esc((cand.violations || []).join("; "))}</span>` : `<span class="ok">respected</span>`}, allowed <span class="mono">${esc((task.allowed_write_globs || []).join(", "))}</span>, protected <span class="mono">${esc((task.protected_globs || []).join(", "))}</span></dd>
      <dt>Digests</dt><dd>${Object.entries(cand.sha256 || {}).map(([p, h]) => `<span class="mono">${esc(p)} ${esc(h.slice(0, 12))}</span>`).join("; ") || "none"}</dd>
      <dt>Implementer</dt><dd>${(b.trajectory || {}).turns || 0} turn(s), ${cand.implementer_finished === false ? "did not declare finished" : "declared finished"}</dd></dl>
      <pre class="code diff" tabindex="0" aria-label="Unified diff" data-focus="diff">${diffHtml(cand.diff)}</pre>
      <p class="note">The diff is reviewed as text here; the verdict never depends on reading it. <a href="/api/runs/${encodeURIComponent(d.run.run_id)}/artifacts/candidate.patch">Download candidate.patch</a> to apply it locally.</p></div>`;
  }

  function counterBlock(c) {
    const a = c.assertion || {};
    const rows = [["test", c.test_id], ["outcome", c.outcome + (c.timed_out ? " (timed out)" : c.signal ? ` (signal ${c.signal})` : "")]];
    if (a.parsed && a.first != null) rows.push(["the test's first argument", a.first], ["the test's second argument", a.second], ["assertion", a.kind]);
    else if (a.message) rows.push([a.kind ? "exception" : "last line", (a.kind ? a.kind + ": " : "") + a.message]);
    else rows.push(["captured output", "none recorded for this test"]);
    const cls = c.classification === "test_defect" ? "verified" : c.classification === "implementation_bug" ? "error" : "";
    return `<div class="counter ${cls}">${rows.map(([k, v]) => `<div><span class="k">${esc(k)}</span>${esc(v)}</div>`).join("")}</div>
      ${c.classification_label ? `<p class="classify"><strong>${esc(c.classification_label)}.</strong> ${c.contract_basis ? esc(c.contract_basis) + " " : ""}${esc(c.rationale || "")}</p>` : `<p class="classify">Not arbitrated: classify this failure yourself (bug in the patch, defective test or contract gap).</p>`}
      ${c.tail ? det("tail-" + c.name, "Captured output of the failing test", `<pre class="code" tabindex="0">${esc(c.tail)}</pre>`) : ""}`;
  }

  function testsPanel(d) {
    const b = d.bundle, ex = d.exhibits, v = b.verification || {}, red = b.red_run || {};
    const E = Object.fromEntries(ex.exhibits.map((e) => [e.ref, e]));
    const cx = ex.counterexamples || [];
    const base = Object.fromEntries((red.tests || []).map((t) => [t.id, t.outcome]));
    const cand = Object.fromEntries(((v.sealed || {}).tests || []).map((t) => [t.id, t.outcome]));
    const ids = [...new Set([...Object.keys(base), ...Object.keys(cand)])].sort();
    const sealedRows = ids.filter((id) => !state.onlyRed || base[id] !== "ok");
    let html = `<section class="exhibit" aria-labelledby="gates-h"><header><h3 id="gates-h">Gates</h3><span class="sum">${ex.gates.length ? "every gate must pass for VERIFIED; a skipped gate is never a pass" : "no gate was reached"}</span></header>
      <div class="tablewrap"><table class="gates"><thead><tr><th>Gate</th><th>Result</th><th>Evidence</th><th>Detail</th></tr></thead><tbody>${ex.gates.map((g) => `<tr><td>${esc(g.label)}</td><td>${mark(g.result)}${g.weak ? ` <span class="skipc">(weak)</span>` : ""}</td><td class="mono">${esc(g.evidence_class)}</td><td>${esc(g.detail)}</td></tr>`).join("") || `<tr><td colspan="4" class="skipc">The run ended before verification.</td></tr>`}</tbody></table></div>
      <p class="note">Evidence classes: bound = per-test exit codes under the supervisor with nonce, digests and canaries checked; stdout = parsed console output of the repository's test command; model = a model judgement.</p></section>`;
    const e1 = E.E1, d1 = e1.detail;
    html += `<section class="exhibit" aria-labelledby="e1-h"><header><span class="exref">E1</span><h3 id="e1-h">${esc(e1.title)}</h3><span class="sum">${mark(e1.status)} ${esc(e1.summary)}</span></header>
      <p class="why">${esc(e1.why)}${d1.author_model ? ` Sealed by ${esc(d1.author_model)}, digest <span class="mono">${esc((d1.sha256 || "").slice(0, 12))}</span>.` : ""}</p>
      ${ids.length ? `<label class="inline-check"><input type="checkbox" id="only-red" data-focus="only-red" ${state.onlyRed ? "checked" : ""}>Show only the tests that failed on the base</label>
      <div class="tablewrap"><table><thead><tr><th>Test</th><th>On the base</th><th>On the candidate</th></tr></thead><tbody>${sealedRows.map((id) => `<tr><td class="mono">${esc(short(id))}</td><td class="${base[id] === "ok" ? "skipc" : base[id] ? "holdc" : "skipc"}">${base[id] === "ok" ? "passes" : base[id] ? "fails, as required" : "not run"}</td><td class="${cand[id] === "ok" ? "ok" : cand[id] ? "fail" : "skipc"}">${cand[id] === "ok" ? "passes" : cand[id] ? "fails (" + esc(cand[id]) + ")" : "not run"}</td></tr>`).join("")}</tbody></table></div>` : ""}
      ${v.binding ? det("binding", `Binding checks (${Object.keys(v.binding.checks || {}).length}) ${v.binding.ok ? "all pass" : "with failures"}`, `<ul class="plain">${Object.entries(v.binding.checks || {}).map(([k, ok]) => `<li class="${ok ? "ok" : "fail"}">${esc(k.replace(/_/g, " "))}: ${ok ? "pass" : "FAIL"}</li>`).join("")}</ul><p class="note">Verification operation <span class="mono">${esc(v.operation_uuid || "")}</span>${d1.canary_ok != null ? `; verifier canaries ${d1.canary_ok ? "intact" : "FLIPPED"}` : ""}. ${(v.order || []).map(esc).join(" ")}</p>`) : `<p class="note">Verification was not reached, so there are no binding checks.</p>`}
      ${cx.filter((c) => c.exhibit === "E1").map((c) => `<h4>Counterexample: ${esc(c.name)}</h4>${counterBlock(c)}`).join("")}</section>`;
    const e2 = E.E2, d2 = e2.detail;
    const mutants = ((b.breaker || {}).mutation || {}).mutants || [];
    html += `<section class="exhibit" aria-labelledby="e2-h"><header><span class="exref">E2</span><h3 id="e2-h">${esc(e2.title)}</h3><span class="sum">${mark(e2.status)} ${esc(e2.summary)}</span></header>
      <p class="why">${esc(e2.why)}</p>
      ${(d2.survivors || []).length ? `<h4>Weak spots</h4><div class="tablewrap"><table><thead><tr><th>File</th><th>Line</th><th>Change the tests did not notice</th></tr></thead><tbody>${d2.survivors.map((s) => `<tr><td class="mono">${esc(s.path)}</td><td>${esc(s.lineno)}</td><td class="mono">${esc(s.description)}</td></tr>`).join("")}</tbody></table></div>` : ""}
      ${mutants.length ? det("mutants", `All mutants (${mutants.length})`, `<div class="tablewrap"><table><thead><tr><th>Mutant</th><th>Line</th><th>Change</th><th>Status</th><th>Caught by</th></tr></thead><tbody>${mutants.map((m) => `<tr><td class="mono">${esc(m.id)}</td><td>${esc(m.lineno)}</td><td class="mono">${esc(m.description)}</td><td class="${m.status === "killed" ? "ok" : m.status === "survived" ? "fail" : "skipc"}">${esc(m.status)}</td><td class="mono">${esc((m.killed_by || []).map(short).join(", "))}</td></tr>`).join("")}</tbody></table></div>`) : ""}</section>`;
    const e3 = E.E3, d3 = e3.detail;
    const advTests = (((b.breaker || {}).adversarial || {}).summary || {}).tests || [];
    html += `<section class="exhibit" aria-labelledby="e3-h"><header><span class="exref">E3</span><h3 id="e3-h">${esc(e3.title)}</h3><span class="sum">${mark(e3.status)} ${esc(e3.summary)}</span></header>
      <p class="why">${esc(e3.why)}${d3.author_model ? ` Written by ${esc(d3.author_model)}, digest <span class="mono">${esc((d3.sha256 || "").slice(0, 12))}</span>.` : ""}</p>
      ${advTests.length ? `<div class="tablewrap"><table><thead><tr><th>Test</th><th>Result</th></tr></thead><tbody>${advTests.map((t) => `<tr><td class="mono">${esc(short(t.id))}</td><td class="${t.outcome === "ok" ? "ok" : "fail"}">${t.outcome === "ok" ? "passes" : "fails (" + esc(t.outcome) + ")"}</td></tr>`).join("")}</tbody></table></div>` : ""}
      ${cx.filter((c) => c.exhibit === "E3").map((c) => `<h4>Counterexample: ${esc(c.name)}</h4>${counterBlock(c)}`).join("")}
      ${d3.notes ? `<p class="note">Breaker notes: ${esc(d3.notes)}</p>` : ""}
      ${advTests.length ? `<p class="note"><a href="/api/runs/${encodeURIComponent(d.run.run_id)}/artifacts/breaker_tests.py">Source of the generated test module</a></p>` : ""}</section>`;
    const e4 = E.E4, d4 = e4.detail;
    html += `<section class="exhibit" aria-labelledby="e4-h"><header><span class="exref">E4</span><h3 id="e4-h">${esc(e4.title)}</h3><span class="sum">${mark(e4.status)} ${esc(e4.summary)}</span></header>
      <p class="why">${esc(e4.why)}${e4.status === "none" ? " This task has none; the controlled evaluation judged it with an independent suite outside the run." : ""}</p>
      ${(d4.failing_ids || []).length ? `<ul class="plain">${d4.failing_ids.map((id) => `<li class="fail">${esc(short(id))}</li>`).join("")}</ul>` : ""}
      ${cx.filter((c) => c.exhibit === "E4").map((c) => `<h4>Counterexample: ${esc(c.name)}</h4>${counterBlock(c)}`).join("")}</section>`;
    const e5 = E.E5, d5 = e5.detail;
    html += `<section class="exhibit" aria-labelledby="e5-h"><header><span class="exref">E5</span><h3 id="e5-h">${esc(e5.title)}</h3><span class="sum">${mark(e5.status)} ${esc(e5.summary)}</span></header>
      <p class="why">${esc(d5.summary || e5.why)}</p>
      ${[...(d5.scope_narrowed || []).map((x) => "narrowed: " + x), ...(d5.scope_widened || []).map((x) => "widened: " + x), ...(d5.unsupported_claims || []).map((x) => "unsupported: " + x)].length ? `<ul class="plain">${[...(d5.scope_narrowed || []).map((x) => "narrowed: " + x), ...(d5.scope_widened || []).map((x) => "widened: " + x), ...(d5.unsupported_claims || []).map((x) => "unsupported: " + x)].map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}</section>`;
    const e6 = E.E6, d6 = e6.detail;
    if (e6.shown) {
      html += `<section class="exhibit" aria-labelledby="e6-h"><header><span class="exref">E6</span><h3 id="e6-h">${esc(e6.title)}</h3><span class="sum">${d6.applied ? "apply mode" : "advisory, verdict unchanged"}</span></header>
        <p class="why">${esc(e6.summary)}</p>
        <div class="tablewrap"><table><thead><tr><th>Failing test</th><th>Classification</th><th>Contract basis</th><th>Rationale</th></tr></thead><tbody>${(d6.classifications || []).map((c) => `<tr><td class="mono">${esc(c.name)}</td><td class="${c.classification === "test_defect" ? "ok" : c.classification === "contract_dispute" ? "holdc" : "fail"}">${esc((c.classification || "").replace(/_/g, " "))}</td><td>${esc(c.contract_basis || "")}</td><td>${esc(c.rationale || "")}</td></tr>`).join("")}</tbody></table></div>
        ${det("arb-rerun", "Corrected modules re-run on the candidate and on the base", `<div class="tablewrap"><table><thead><tr><th>Module</th><th>On the candidate</th><th>On the base</th><th>Cleared</th></tr></thead><tbody>${(d6.reruns || []).map((m) => `<tr><td>${esc(m.module)}</td><td>${esc(m.candidate || "not re-run")}</td><td>${esc(m.base || "not re-run")}</td><td class="${m.cleared ? "ok" : "skipc"}">${m.cleared ? "yes" : "no"}</td></tr>`).join("")}</tbody></table></div><p class="note">${esc(d6.note || "")}</p>`)}</section>`;
    }
    const e7 = E.E7, d7 = e7.detail;
    if (e7.shown) {
      html += `<section class="exhibit" aria-labelledby="e7-h"><header><span class="exref">E7</span><h3 id="e7-h">${esc(e7.title)}</h3><span class="sum">infrastructure, not the patch</span></header>
        <p class="why">${esc(e7.why)}</p>
        <div class="counter error"><div><span class="k">component</span>${esc(d7.component)}</div><div><span class="k">stage</span>${esc(d7.stage || "unknown")}</div><div><span class="k">model calls</span>${d7.model_calls ?? 0}, ${d7.model_calls_failed ?? 0} failed, ${d7.uncertain_unpriced_calls ?? 0} uncertain</div><div><span class="k">sandbox operations</span>${d7.sandbox_operations ?? 0}</div><div><span class="k">committed cost</span>${esc(usd(d7.cost_usd_committed))}${d7.uncertain_unpriced_calls ? " (uncertain calls counted at their reservation)" : ""}</div><div><span class="k">retried</span>no: Attest never replays an uncertain request</div></div>
        <ul class="plain">${(d7.reasons || []).map((r) => `<li>${esc(r)}</li>`).join("")}</ul></section>`;
    }
    return html;
  }

  function reachedIndex(b, events) {
    let last = -1;
    const consider = (s) => { const k = STAGE_ALIAS[s] === undefined ? s : STAGE_ALIAS[s]; const i = STAGES.findIndex(([key]) => key === k); if (i > last) last = i; };
    (events || []).forEach((e) => consider(e.stage));
    if (b) consider(b.stage);
    if (b && b.finished_at_utc && b.verdict && ["VERIFIED", "NEEDS HUMAN"].includes(b.verdict.verdict)) last = STAGES.length - 1;
    return last;
  }
  function stepperHtml(current, live) {
    return `<ol class="stepper" id="stepper" aria-label="Stages">${STAGES.map(([k, l], i) => `<li data-stage="${k}" class="${i < current ? "done" : i === current ? (live ? "current" : "done") : ""}"><span class="dot"></span>${l}</li>`).join("")}</ol>`;
  }
  const logRow = (e) => `<li data-seq="${esc(e.seq)}"><span class="ts">${esc((e.at_utc || "").slice(11, 19))}</span><span class="st">${esc(e.stage || "")}</span><span class="msg">${esc(e.message)}</span></li>`;

  function activityPanel(d) {
    const b = d.bundle, t = (b.ledger || {}).totals || {}, ex = b.execution || {}, prov = b.provenance;
    const events = d.events || [];
    const trail = ((b.trajectory || {}).actions || []).map((a) => ({ at_utc: "", stage: "implement", message: `turn ${a.turn}: ${a.action}${a.path ? " " + a.path : ""}${a.observation ? " -> " + String(a.observation).slice(0, 160) : ""}` }));
    const rows = events.length ? events : trail;
    const roles = ((b.profile || {}).provider || {}).roles || {};
    return `<div class="block"><h3>Timeline</h3>
      ${stepperHtml(reachedIndex(b, events), false)}
      <div class="meter"><div>Wall clock<strong>${esc(dur(secsBetween(b.started_at_utc, b.finished_at_utc)))}</strong></div><div>Model calls<strong>${t.model_calls ?? "-"}</strong></div><div>Sandbox operations<strong>${t.sandbox_operations ?? "-"}</strong></div><div>Committed cost<strong>${esc(usd(t.cost_usd_committed ?? t.cost_usd))}</strong></div></div>
      <ul class="log" aria-label="${events.length ? "Event log" : "Implementer action trail"}">${rows.map(logRow).join("") || `<li class="empty-row">No events were recorded for this run.</li>`}</ul>
      ${!events.length && trail.length ? `<p class="note">This recorded run has no progress events; the implementer's action trail is shown instead.</p>` : ""}
      ${det("calls", `Model calls (${(b.ledger.model_calls || []).length})`, `<div class="tablewrap"><table><thead><tr><th>Stage</th><th>Role</th><th>Model</th><th>Effort</th><th>Tokens in</th><th>Tokens out</th><th>Cost</th><th>Time</th><th>Status</th></tr></thead><tbody>${(b.ledger.model_calls || []).map((c) => `<tr><td>${esc(c.stage)}</td><td>${esc(c.role)}</td><td class="mono">${esc((c.returned_model || c.requested_model || "").split("/").pop())}</td><td>${esc(c.returned_effort || c.requested_effort || "-")}</td><td>${c.tokens_in ?? "-"}</td><td>${c.tokens_out ?? "-"}</td><td>${c.cost_usd != null ? "$" + Number(c.cost_usd).toFixed(5) : "-"}</td><td>${(c.elapsed_ms / 1000).toFixed(1)} s</td><td class="${c.ok ? "ok" : "fail"}">${c.ok ? "ok" : c.malformed_output ? "malformed" : "error"}</td></tr>`).join("")}</tbody></table></div><p class="note">Roles: ${esc(Object.entries(roles).map(([r, m]) => `${r} ${Array.isArray(m) ? m.filter(Boolean).join(":") : String(m).split("/").pop()}`).join(", "))}. Inference cost ${esc(usdOrNa(t.cost_usd))}; tokens in/out/cached ${t.tokens_in}/${t.tokens_out}/${t.tokens_cached}.</p>`)}
      ${det("exec", "Execution identifiers", `<dl class="kv"><dt>Base image</dt><dd class="mono">${esc(ex.base_image_uuid || "-")}</dd><dt>Checkpoint image</dt><dd class="mono">${esc(ex.checkpoint_image_uuid || "-")}</dd><dt>Checkpoint operation</dt><dd class="mono">${esc(ex.checkpoint_operation_uuid || "-")}</dd><dt>Networking after checkpoint</dt><dd>${ex.checkpoint_networking ? "on (install step)" : "off"}</dd><dt>Suite binding</dt><dd>${esc((ex.suite_binding || {}).mode || "stdout")}${(ex.suite_binding || {}).reason ? ": " + esc(ex.suite_binding.reason) : ""}</dd><dt>Verification operation</dt><dd class="mono">${esc((b.verification || {}).operation_uuid || "not reached")}</dd><dt>Sandbox guest time</dt><dd>${t.sandbox_duration_s ?? "-"} s, retained images ${esc((t.sandbox_retained_images || []).join(", ") || "none")}</dd>
        ${prov ? `<dt>Attest revision</dt><dd class="mono">${esc(prov.attest_version || "")} ${esc(((prov.attest_revision || {}).digest || "").slice(0, 12))}</dd><dt>Supervisor</dt><dd class="mono">${esc((prov.supervisor || {}).version || "")} ${esc(((prov.supervisor || {}).sha256 || "").slice(0, 12))}</dd><dt>Sampling</dt><dd>${esc(JSON.stringify(prov.sampling || {}).slice(0, 200))}</dd><dt>Limits</dt><dd>${esc(Object.entries(prov.limits || {}).map(([k, v]) => `${k} ${v}`).join(", "))}</dd>${prov.upstream ? `<dt>Upstream</dt><dd class="mono">${esc(prov.upstream.url || "")} ${esc(prov.upstream.commit || "")} ${esc(prov.upstream.reference || "")}</dd>` : ""}` : `<dt>Provenance record</dt><dd class="skipc">not in this bundle (recorded before milestone M2)</dd>`}</dl>`)}</div>`;
  }

  function filesPanel(d) {
    const b = d.bundle, m = d.manifest || { files: [] }, pr = d.exhibits.proves || { proves: [], does_not_prove: [] };
    const files = m.files || [];
    const mutants = files.filter((f) => /^mutants_/.test(f.path) || /^mutants\//.test(f.path));
    const rest = files.filter((f) => !mutants.includes(f));
    const id = encodeURIComponent(d.run.run_id);
    return `<div class="block"><h3>Proof Bundle</h3>
      <p>Everything below is in the downloadable zip. ${m.recorded ? `A manifest written at the end of the run lists the sha256 of every file; <span class="mono">attest check</span> recomputes them offline. The digests are an integrity check of the files, not a signature and not proof that the sandbox operations happened; that evidence is in the operation ids and the nonce-bound test records.` : `This run predates the artifact manifest, so the digests below were computed when this page loaded, not recorded with the run.`}</p>
      <p><a class="btn" href="/api/runs/${id}/bundle.zip">Download everything (zip)</a></p>
      <ul class="files">${rest.map((f) => `<li><span class="n">${esc(f.path)}</span><span class="p">${esc(f.purpose || "")}</span><span class="s">${kb(f.bytes)}</span><span class="d">sha256 ${esc(f.sha256 || "")}</span></li>`).join("")}
      ${mutants.length ? `<li><span class="n">mutants (${mutants.length} files)</span><span class="p">Source of each mutant used in E2</span><span class="s">${kb(mutants.reduce((a, f) => a + (f.bytes || 0), 0))}</span></li>` : ""}</ul>
      <h3 style="margin-top:22px">What this bundle proves, and what it does not</h3>
      <div class="proves"><div><h4>Proves</h4><ul class="plain">${pr.proves.map((x) => `<li>${esc(x)}</li>`).join("") || "<li>Nothing: no gate was reached.</li>"}</ul></div><div><h4>Does not prove</h4><ul class="plain">${pr.does_not_prove.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div></div>
      ${det("limitations", `Limitations recorded in the bundle (${(b.limitations || []).length})`, `<ul class="plain">${(b.limitations || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`)}</div>`;
  }

  const PANELS = { overview: overviewPanel, patch: patchPanel, tests: testsPanel, activity: activityPanel, files: filesPanel };

  function renderFinished(d) {
    const run = d.run, b = d.bundle;
    window.attestDebug.renders++;
    const f = focusId();
    if (!b) {  // a run that errored before any bundle was written (queue full, budget, disk, interrupted)
      const reason = run.error || "no record was written";
      main().innerHTML = decisionHeader("ERROR", "This run did not complete.", `${reason}. Nothing was certified and no Proof Bundle exists for this run.`,
        { ref: "E7", text: `Failed at stage ${run.stage || "unknown"}; not retried.` }, provenanceLine(run, d), actionsHtml(run, d))
        + tabsHtml({ patch: "No patch exists", tests: "No verification ran", files: "No bundle was written" })
        + `<div class="panel" role="tabpanel" id="panel" aria-labelledby="tab-${state.tab}" tabindex="0"></div>`;
      renderPanel();
      restoreFocus(f);
      return;
    }
    const dec = d.exhibits.decision;
    main().innerHTML = decisionHeader(b.verdict.verdict, dec.statement, dec.explanation, dec.evidence, provenanceLine(run, d), actionsHtml(run, d))
      + tabsHtml({}) + `<div class="panel" role="tabpanel" id="panel" aria-labelledby="tab-${state.tab}" tabindex="0"></div>`;
    renderPanel();
    restoreFocus(f);
    onScroll();
  }

  function renderPanel() {
    const d = state.detail; const panel = $("#panel"); if (!panel || !d) return;
    window.attestDebug.panelRenders++;
    const f = focusId();
    $$("[role=tab]").forEach((t) => { const on = t.dataset.tab === state.tab; t.setAttribute("aria-selected", String(on)); t.tabIndex = on ? 0 : -1; });
    panel.setAttribute("aria-labelledby", `tab-${state.tab}`);
    if (state.live.status) {
      panel.innerHTML = livePanelHtml(d);
    } else if (!d.bundle) {
      panel.innerHTML = state.tab === "activity" ? `<div class="block"><h3>Timeline</h3>${stepperHtml(reachedIndex(null, d.events), false)}<ul class="log" aria-label="Event log">${(d.events || []).map(logRow).join("") || `<li class="empty-row">No events were recorded.</li>`}</ul></div>`
        : `<div class="block"><h3>What happened</h3><p>${esc(d.run.error || "The run ended without a record.")}</p><p class="note">Component failures are recorded as ERROR; the task itself was not judged.</p></div>`;
    } else {
      panel.innerHTML = (PANELS[state.tab] || overviewPanel)(d);
    }
    restoreFocus(f);
  }

  // ---- live run (queued or running): rendered once, then updated in place
  function liveHeaderText(run, status, meters) {
    const title = run.task_title;
    const prov = (run.summary || {}).provenance;
    if (status === "queued") {
      const ahead = state.live.queueAhead;
      return { seal: "QUEUED", statement: ahead ? `Queued behind ${ahead} run${ahead === 1 ? "" : "s"}.` : "Queued, starting next.",
        explanation: `Attest runs one task at a time so that every run gets the full sandbox budget. This run starts when the current one finishes. Task: ${title}.`,
        evidence: { ref: "Hold", text: `${run.provider === "nebius" ? `${usd(((state.health || {}).budget || {}).per_run_cap_usd)} reserved against today's cap while queued; released or replaced by the real cost when the run ends.` : "Team allowance; no Nebius charge is reserved."}` } };
    }
    const started = secsBetween(meters.started_at || run.started_at, new Date().toISOString());
    const since = `Started ${started != null ? dur(started) + " ago" : "just now"}.`;
    return { seal: "RUNNING", statement: `Verifying: ${title}`,
      explanation: prov === "synthetic" ? "Synthetic fixture: the recorded events of a finished run are replayed at a fixed pace to show the live view. No sandbox or model is running." :
        `Live execution with ${providerLabel(run.provider)} and disposable sandbox branches. Evidence appears as each stage completes; the verdict is computed only from recorded gates.`,
      evidence: { ref: prov === "synthetic" ? "Replay" : "Live", text: prov === "synthetic" ? `${since} Replay of a recorded run; nothing is reserved or spent.`
        : `${since} Profile ${run.profile_label}${run.provider === "nebius" ? `, ${usd(((state.health || {}).budget || {}).per_run_cap_usd)} cap for this run` : ""}.` } };
  }
  function livePanelHtml(d) {
    const run = d.run;
    const task = state.tasks.find((t) => t.task_id === run.task_id);
    const statement = task ? task.statement : "";
    const events = state.live.events;
    const requested = `<div class="block"><h3>What was requested</h3><p><strong>${esc(run.task_title)}</strong></p><p>${esc(statement)}${statement.length >= 400 ? "…" : ""}</p></div>`;
    const next = `<div class="block"><h3>What happens next</h3><ol class="plain">${STAGE_HELP.map((s) => `<li>${esc(s)}</li>`).join("")}</ol><p class="note">You can leave this page. The run keeps its place and appears in History with its verdict.</p></div>`;
    const timeline = `<div class="block"><h3>Timeline</h3>${stepperHtml(reachedIndex(null, events), true)}
      <div class="meter"><div>Elapsed<strong id="m-elapsed">${esc(dur(secsBetween(state.live.meters.started_at || run.started_at, new Date().toISOString())) || "0 s")}</strong></div><div>Model calls<strong id="m-calls">${state.live.meters.model_calls ?? 0}</strong></div><div>Sandbox operations<strong id="m-ops">${state.live.meters.sandbox_ops ?? 0}</strong></div><div>Cost so far<strong id="m-cost">${esc(usd(state.live.meters.cost_committed_usd ?? 0))}</strong></div></div>
      <ul class="log" id="log" aria-live="polite" aria-relevant="additions" aria-label="Event log">${events.map(logRow).join("")}</ul>
      <p class="note">Updates are applied to the changed rows only. Keep a disclosure open or your focus on a control while the log grows: neither moves.</p>
      ${det("stages-help", "What each stage does", `<ul class="plain">${STAGE_HELP.map((s) => `<li>${esc(s)}</li>`).join("")}</ul>`)}</div>`;
    if (state.tab === "activity") return timeline;
    return `<div class="overview">${requested}${state.live.status === "queued" ? next : timeline}</div>`;
  }
  function renderLive(d) {
    const run = d.run;
    window.attestDebug.renders++;
    const f = focusId();
    const h = liveHeaderText(run, state.live.status, state.live.meters);
    const actions = `<button type="button" class="btn secondary" data-copy-link data-focus="act-link">Copy link to this run</button>`;
    main().innerHTML = decisionHeader(h.seal, h.statement, h.explanation, h.evidence, provenanceLine(run, d), actions)
      + tabsHtml({ patch: "Available when the run finishes", tests: "Available when the run finishes", files: "Available when the run finishes" })
      + `<div class="panel" role="tabpanel" id="panel" aria-labelledby="tab-${state.tab}" tabindex="0"></div>`;
    if (!["overview", "activity"].includes(state.tab)) state.tab = "overview";
    renderPanel();
    restoreFocus(f);
  }
  function applyLiveUpdate(body) {
    const run = state.detail.run;
    (body.events || []).forEach((e) => { if (e.seq > state.live.lastSeq) { state.live.events.push(e); state.live.lastSeq = e.seq; } });
    state.live.meters = body.meters || state.live.meters;
    // runs ahead of a queued run: the others waiting in the worker queue plus the one being executed
    state.live.queueAhead = Math.max(0, (body.queue || 0) - 1) + (body.current && body.current !== run.run_id ? 1 : 0);
    const statusChanged = body.status !== state.live.status;
    state.live.status = body.status;
    state.live.stage = body.stage;
    // keyed updates: append rows, change texts, never rebuild the pane
    const log = $("#log");
    if (log) {
      const have = new Set($$("li[data-seq]", log).map((li) => Number(li.dataset.seq)));
      const fresh = state.live.events.filter((e) => !have.has(e.seq));
      if (fresh.length) { log.insertAdjacentHTML("beforeend", fresh.map(logRow).join("")); log.scrollTop = log.scrollHeight; }
    }
    const current = reachedIndex(null, state.live.events);
    $$("#stepper li").forEach((li, i) => { li.className = i < current ? "done" : i === current ? "current" : ""; });
    const m = state.live.meters || {};
    const set = (sel, text) => { const el = $(sel); if (el && el.textContent !== text) el.textContent = text; };
    set("#m-elapsed", dur(secsBetween(m.started_at || run.started_at, body.status === "running" ? new Date().toISOString() : m.finished_at || new Date().toISOString())) || "0 s");
    set("#m-calls", String(m.model_calls ?? 0)); set("#m-ops", String(m.sandbox_ops ?? 0)); set("#m-cost", usd(m.cost_committed_usd ?? 0));
    const h = liveHeaderText(run, body.status, m);
    set("[data-k=seal]", h.seal); set("[data-k=statement]", h.statement); set("[data-k=explain]", h.explanation); set("[data-k=evref]", h.evidence.ref); set("[data-k=evtext]", h.evidence.text);
    const seal = $("[data-k=seal]"); if (seal) seal.className = `seal big ${vclass(h.seal)}`;
    if (statusChanged && body.status === "running" && state.tab === "overview") { const f = focusId(); renderPanel(); restoreFocus(f); }
  }
  async function pollLive() {
    const id = state.runId; if (!id) return;
    let body;
    try { body = await api(`/api/runs/${encodeURIComponent(id)}/events?after=${state.live.lastSeq}`); } catch (e) { return; }
    if (state.runId !== id) return;
    state.live.polls++; window.attestDebug.polls = state.live.polls;
    if (body.status === "finished" || body.status === "error") {
      stopLive();
      state.live.status = null;
      await loadRuns();
      const detail = await api(`/api/runs/${encodeURIComponent(id)}`).catch(() => null);
      if (detail && state.runId === id) { state.detail = detail; renderFinished(detail); }
      loadHealth();
      return;
    }
    applyLiveUpdate(body);
    const row = state.runs.find((r) => r.run_id === id);
    if (row && (row.status !== body.status || row.stage !== body.stage)) loadRuns();
  }

  function loadingView(run) {
    const seal = run ? (run.status === "finished" ? run.verdict || "ERROR" : run.status === "error" ? "ERROR" : run.status.toUpperCase()) : "LOADING";
    return decisionHeader(seal, run ? run.task_title : "Loading the run", "Loading the Proof Bundle.", null, run ? provenanceLine(run, null) : "", "")
      + tabsHtml({ overview: "Loading", patch: "Loading", tests: "Loading", activity: "Loading", files: "Loading" });
  }

  async function openRun(id, replace) {
    stopLive();
    state.runId = id; state.detail = null; state.onlyRed = false;
    state.live = { timer: null, lastSeq: 0, events: [], status: null, stage: null, meters: {}, polls: 0 };
    loadExpanded(id);
    const m = location.hash.match(/^#(overview|patch|tests|activity|files)$/);
    state.tab = replace && m ? m[1] : "overview";  // deep links and history navigation keep their tab; a new selection starts at the overview
    setRoute(id, replace);
    const row = state.runs.find((r) => r.run_id === id);
    main().innerHTML = loadingView(row);
    renderHistory();
    let detail;
    try { detail = await api(`/api/runs/${encodeURIComponent(id)}`); } catch (e) {
      main().innerHTML = `<div class="empty"><h2>This run could not be loaded.</h2><p>${esc(e.message)}</p></div>`; return;
    }
    if (state.runId !== id) return;
    state.detail = detail;
    const run = detail.run;
    if (run.status === "queued" || run.status === "running") {
      state.live.status = run.status; state.live.events = detail.events || []; state.live.lastSeq = state.live.events.reduce((a, e) => Math.max(a, e.seq), 0);
      state.live.meters = { model_calls: run.model_calls, sandbox_ops: run.sandbox_ops, cost_committed_usd: run.cost_committed_usd, started_at: run.started_at };
      renderLive(detail);
      state.live.timer = setInterval(pollLive, POLL_MS);
    } else {
      renderFinished(detail);
    }
  }

  function showEmpty() { stopLive(); state.runId = null; state.detail = null; setRoute(null, true); main().innerHTML = emptyView(); renderHistory(); }

  // ------------------------------------------------------------------ actions
  async function startRun() {
    const go = $("#go"), note = $("#start-note");
    const t = currentTask(); if (!t) return;
    if (state.mode === "browse") {
      if (t.estimate && t.estimate.latest_run_id) { await openRun(t.estimate.latest_run_id, false); $("#main").focus({ preventScroll: true }); }
      return;
    }
    go.disabled = true; note.className = "note"; note.textContent = "Starting the run.";
    try {
      const res = await api("/api/runs", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: t.task_id, provider: state.profile || (state.profiles[0] || {}).id, admin_token: state.token || null }) });
      note.textContent = `Queued as ${res.run_id} (position ${res.position}).`;
      await loadRuns(); await openRun(res.run_id, false); loadHealth();
    } catch (e) { note.className = "note err"; note.textContent = "Could not start: " + e.message; }
    finally { go.disabled = false; renderEstimate(); }
  }
  async function signIn() {
    const token = $("#admin").value.trim(); const note = $("#signin-note");
    state.token = token;
    await loadProfiles(token || null);
    note.textContent = state.team ? "Signed in: the team profile is available in the Inference profile list when you choose to run live." : (token ? "That token was not accepted; the public profile stays selected." : "Enter the team token to see the team profile.");
    note.className = state.team || !token ? "note" : "note err";
  }
  async function copyPatch(btn, runId) {
    try {
      const res = await fetch(`/api/runs/${encodeURIComponent(runId)}/artifacts/candidate.patch`);
      const text = await res.text();
      await navigator.clipboard.writeText(text);
      const old = btn.textContent; btn.textContent = "Copied"; setTimeout(() => { btn.textContent = old; }, 2000);
    } catch (e) { location.href = `/api/runs/${encodeURIComponent(runId)}/artifacts/candidate.patch`; }
  }
  async function copyLink(btn) {
    try { await navigator.clipboard.writeText(location.href); const old = btn.textContent; btn.textContent = "Link copied"; setTimeout(() => { btn.textContent = old; }, 2000); }
    catch (e) { btn.textContent = location.href; }
  }
  function onScroll() { const h = $(".decision"); if (h) h.classList.toggle("compact", window.scrollY > 160 && window.innerWidth > 900); }

  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-run],[data-tab],[data-tab-link],[data-filter],[data-copy-patch],[data-copy-link],[data-new-run],[data-home]");
    if (!t) return;
    if (t.dataset.run) { openRun(t.dataset.run, false); }
    else if (t.dataset.tab) { if (t.disabled) return; state.tab = t.dataset.tab; setRoute(state.runId, true); renderPanel(); }
    else if (t.dataset.tabLink) { e.preventDefault(); state.tab = t.dataset.tabLink; setRoute(state.runId, true); renderPanel(); $(`#tab-${state.tab}`)?.focus(); }
    else if (t.dataset.filter) { state.filter = t.dataset.filter; renderFilters(); renderHistory(); $(`[data-focus="filter-${state.filter}"]`)?.focus(); }
    else if (t.dataset.copyPatch) copyPatch(t, t.dataset.copyPatch);
    else if (t.hasAttribute("data-copy-link")) copyLink(t);
    else if (t.dataset.newRun !== undefined) { state.mode = "live"; $("input[name=mode][value=live]").checked = true; if (state.tasks.some((x) => x.task_id === t.dataset.newRun)) { state.task = t.dataset.newRun; $("#task").value = state.task; } renderEstimate(); $("#rail-details").open = true; $("#go").focus(); }
    else if (t.hasAttribute("data-home")) { e.preventDefault(); showEmpty(); }
  });
  document.addEventListener("change", (e) => {
    if (e.target.name === "mode") { state.mode = e.target.value; renderEstimate(); }
    else if (e.target.id === "task") { state.task = e.target.value; renderEstimate(); }
    else if (e.target.id === "profile") { state.profile = e.target.value; renderEstimate(); }
    else if (e.target.id === "only-red") { state.onlyRed = e.target.checked; renderPanel(); }
  });
  document.addEventListener("toggle", (e) => {
    const d = e.target; if (d.tagName !== "DETAILS" || !d.dataset.id) return;
    if (d.open) state.expanded.add(d.dataset.id); else state.expanded.delete(d.dataset.id);
    saveExpanded();
  }, true);
  document.addEventListener("keydown", (e) => {
    const tab = e.target.closest("[role=tab]");
    if (tab) {
      const all = $$("[role=tab]:not([disabled])"); const i = all.indexOf(tab);
      let n = null; if (e.key === "ArrowRight") n = all[(i + 1) % all.length]; if (e.key === "ArrowLeft") n = all[(i - 1 + all.length) % all.length]; if (e.key === "Home") n = all[0]; if (e.key === "End") n = all[all.length - 1];
      if (n) { e.preventDefault(); state.tab = n.dataset.tab; setRoute(state.runId, true); renderPanel(); n.focus(); }
    }
    const h = e.target.closest("#history button");
    if (h && (e.key === "ArrowDown" || e.key === "ArrowUp")) { e.preventDefault(); const all = $$("#history button"); const i = all.indexOf(h); all[e.key === "ArrowDown" ? Math.min(i + 1, all.length - 1) : Math.max(i - 1, 0)].focus(); }
  });
  $("#go").addEventListener("click", startRun);
  $("#signin-go").addEventListener("click", signIn);
  $("#admin").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); signIn(); } });
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("hashchange", () => { const m = location.hash.match(/^#(overview|patch|tests|activity|files)$/); if (m && m[1] !== state.tab) { state.tab = m[1]; renderPanel(); } });
  window.addEventListener("popstate", () => { const m = location.pathname.match(/^\/runs\/(.+)$/); if (m) openRun(decodeURIComponent(m[1]), true); else showEmpty(); });
  function railAuto() { const d = $("#rail-details"); if (!d) return; const narrow = window.innerWidth <= 900; if (narrow && !state.railTouched) d.open = false; if (!narrow) d.open = true; }
  $("#rail-details").addEventListener("toggle", () => { state.railTouched = true; });
  window.addEventListener("resize", railAuto);

  // ------------------------------------------------------------------ boot
  renderFilters();
  railAuto();
  (async () => {
    await Promise.all([loadHealth(), loadProfiles(null), loadTasks(), loadRuns()]);
    const m = location.pathname.match(/^\/runs\/(.+)$/);
    if (m) openRun(decodeURIComponent(m[1]), true); else main().innerHTML = emptyView();
  })();
  setInterval(loadHealth, 10000);
  setInterval(loadRuns, 15000);
})();
