# Preventing accidental spending (revision 8, 19 October 2026)

A public Nemotron run on the console is paid by design. Revision 7 made a malformed request harmless (422 before anything
exists); a well-formed one still started a run. Revision 8 makes every start an explicit, two-sided act and keeps the services'
costs apart.

## A run starts only on explicit confirmation

| Layer | What it does | Evidence |
| --- | --- | --- |
| Server | `POST /api/runs` answers 428 unless the request carries `X-Attest-Confirm: start-run`, checked first in the handler: no row, queue entry, reservation or provider exists for a refused request, for public and team requests alike. The header is documented in the public OpenAPI schema. | `tests/test_audit_console.py`, class `ExplicitStart` (missing, empty, wrong and differently cased values; team requests; the malformed body still refused first; the confirmed request reaches admission) |
| Console | In live mode the Run button only opens a confirmation that states what the run reserves against the daily cap and that Sandboxes and Tavily are metered separately. Only the confirmation's own button sends the request with the header; it is disabled for 0.7 s when it appears (a double click never passes through), lapses after a minute, closes when the task, mode or profile changes, and closes on Escape. | `tests/console_client_test.mjs`, check `live_run_needs_confirmation`; the layout audit's confirmation states (`../console/`) |
| Automated browsers | On any host but the local one, the page refuses to start a run when `navigator.webdriver` is true (Playwright, Selenium, WebDriver-driven Chrome), before any request exists. | the same JS check; the production browser check after the deployment (`../console/`) |
| Automated checks | Every browser check of the live console in this pass (and the video recording) blocks every request that is not a GET inside the browser, before it is sent, with service workers blocked so nothing bypasses the block, and counts what it blocked. Curl checks of production use GET only. | `scripts/console_layout_audit.py`; the counts in each audit report |
| Harness | The evaluation harness runs on the development gateway by default and refuses a Nebius batch without an explicit `--approve-usd` budget and call cap. Unchanged since revision 4. | `scripts/run_evaluation.py --help` |

On the deployed console (0.8.0, after the deployment of 19 Oct 20:42 UTC; `reports/attest-deployment-2026-10-19e/`): at every
width from 320 to 1440 px, in a visible Chrome window and in headless sweeps, the Run button in live mode opened the confirmation
and sent nothing, and the confirmation's own button was refused by the page ("Live runs are not started from an automated browser
on this host. Open the console in a regular browser to start one.") before any request existed. In the window and the full sweep
2,572 GET requests left the browser and no other request; the browser's guard, which aborts every other method, had nothing to
abort. The other browser runs against production in this pass used the same guard, and those that wrote a record (two repeats at
414 px and the evidence screenshots) show no other request either. The
428 answer to a request without the header is verified by the local tests only; no POST was sent to production.

No new paid Nebius inference, smoke test, evaluation or demo run was started in this pass; the $10 proposal in `FREEZE.md`
remains unapproved.

## Costs kept apart

Inference, Token Factory Sandboxes and Tavily search are separate services with separate billing:

- The ledger, the bundle, the console and `PROOF.md` state one money figure: inference. On the Nemotron profile it is USD from the
  public price table, conservative (an uncertain call counts at its reservation); on the development profile it is the team's
  gateway allowance, recorded in tokens, which the console now shows as "team allowance", never as "$0.00".
- Token Factory Sandboxes operations are recorded with their count and guest time; their raw cost diagnostics have no confirmed
  currency and are never shown as USD. Nebius's console says Sandboxes runs are free during the beta; this project has not
  reconciled that against an invoice, so no record claims that Sandboxes cost nothing.
- Tavily is used only when a specification names outside documentation, on the console's runs; each run's grounding record holds
  the number of search calls (one API credit per basic search that reached Tavily) and the account's usage before and after. The
  evaluation harness runs without Tavily.
- The harness writes all three side by side (`services` in `evaluation.json`, a line in `RESULTS.md`) and never adds them up.
  Records written before revision 8 that state "$0" for a development batch now carry an appended note that the figure is the
  inference ledger (`reports/attest-revision5-repairs-2026-10-19/README.md`, `reports/attest-revision6-repairs-2026-10-19/README.md`).

Cost figures in every record dated 15 to 19 Oct 2026 are inference ledger figures in the same sense: Nemotron USD, or for the
development gateway no USD at all; the Sandboxes operations those runs used are listed in their bundles, and no record assigns
them a cost.
