# Console: horizontal overflow on phones, the confirmation step and cost labels (revision 8, 19 October 2026)

## How the layout was measured

`scripts/console_layout_audit.py` drives the installed Chrome through Playwright. Widths up to 820 px use mobile emulation (a mobile
viewport with `width=device-width`, touch, overlay scrollbars, device scale 3), wider ones a desktop viewport. On each page and
state it lists (1) every element whose box leaves the viewport without a scroll container around it that fits, (2) every text
that runs past the viewport although its element's box fits (a long token without a break opportunity), (3) every button, link,
chip or seal that an `overflow:hidden` box cuts off, and (4) whether the document itself scrolls sideways. The states: the home
page, with every disclosure open, with live mode selected, with the confirmation open, and with the start refused; each run's
case file on every tab with every disclosure open; a run that does not exist; and the case file with every API call failing
(answered with a synthetic 503 inside the browser). Runs: up to three per verdict, longest identifiers first, public and team
(signed in on the local server). The local server has no credentials of any kind, so nothing it does can be paid; every request
that is not a GET is intercepted in the browser before it is sent (on the local server the sign-in passes and a run start is
answered with a synthetic 422; on the live console every such request is aborted) and counted.

## Before the repair

`layout/before-local-phones.json` (16 runs, 320, 360, 390 and 414 px): 111 of 368 page states had an offender, a clipped control or
a sideways-scrolling document. The causes:

| Where | Widths | Cause |
| --- | --- | --- |
| the provider logo row (Nebius and NVIDIA marks) | 320, 360 | a fixed-width flex row 353 px wide |
| the start form's three steps | 320 | grid tracks of `1fr` take their content's minimum width: the task select is as wide as its longest option |
| the capability figures | 320 | the same `1fr` rule with the figures' tables and labels |
| the decision card's buttons (Open PROOF.md, Copy patch) | 320 to 390 | two columns of buttons that never wrap, cut off by the card's `overflow:hidden` |
| a failure record's error text, counterexample headings, an exhibit's summary | 320 to 375 | long tokens without break opportunities (an SSL error string, test names); the error text made the whole document 387 px wide, which also pushed the fixed Guide button off screen |

The live console (0.7.0) at 390 px had none of these (`layout/before-production-390.json`): the right-edge clipping in the
revision-7 390 px screenshot came from the capture method. Chrome's headless command line lays a page out wider than a 390 px window
and crops the image (`layout/capture-artifact-headless-cli-390.png`, the same capture repeated); an emulated phone viewport shows the
page as it is.

## The repair (`attest/app/static/styles.css`, `app.js`, `index.html`)

Grid tracks that may shrink below their content (`minmax(0,1fr)`) and grid and flex children with `min-width:0`; `overflow-wrap`
on the page (long tokens wrap inside their box) and `anywhere` where a flex item's minimum width matters (exhibit summaries, the
adversarial-test rows, notes and the estimate); the decision buttons wrap their text and stack on narrow screens; below 640 px the
tabs wrap onto several lines (every tab stays visible; the underline follows the selected tab) and the logo row may wrap; below
420 px the logos are smaller, key-value lists and counterexample blocks put the label above the value, and the start form's price
pill sits on its own line. Tables and code blocks keep their own horizontal scroll inside the page.

## After the repair

Local, on the final files (`layout/after-local-all-widths.json`): 16 runs (three per verdict where available, public and team),
320, 360, 375, 390, 414, 768, 1024 and 1440 px, 744 page states, **no offender, no clipped control, no sideways-scrolling
document, no page error**. The requests that were not GETs: the local sign-in at each width (to the key-less local server) and,
after the confirmation was pressed, one start request per width, answered inside the browser with a synthetic 422 (never sent);
the Run button itself sent nothing at any width. Screenshots at 320 px: `layout/after-320-start-and-confirmation.png` (the start
form with the confirmation open), `after-320-decision.png` (stacked decision buttons, a wrapped run id), `after-320-tabs-wrapped.png`,
`after-320-failure-record.png` (the long SSL error text that used to widen the document), and the home page at 320 and 1440 px
(`after-320-home-top.png`, `after-1440-home-top.png`).

The deployed console is audited the same way after the deployment (below).

## On the deployed console (0.8.0, 19 Oct 2026, after 20:42 UTC)

The same audit against https://attest.axiqo.xyz (`reports/attest-deployment-2026-10-19e/`, `browser-production-*.json`; every
request that is not a GET is aborted inside the browser): a visible Chrome window at 390 and 1440 px (182 states) and a headless
sweep at all eight widths (726 states), 14 runs. No offender, no sideways-scrolling document and no page error at any width; 2,051
GET requests in the sweep and no other request. The repaired overflow therefore holds on the live console.

The live checks found what the local ones had not, all outside the overflow measure: at 1024 px the Guide (open by itself on
windows wider than 900 px) covered the case file's Activity and Files tabs, so two tab presses failed; the decision card's text was
squeezed to about 80 px between its seal and its buttons, and the overview's evidence table into a sideways scroll; with every API
call failing the start form claimed that no sample tasks were configured; and on phones the collapsed workspace rail stretched into
an empty band on short pages. Version 0.8.1 repairs all of them (the Guide opens by itself only from 1320 px; the decision's buttons
take their own row below 1320 px; the overview stacks below 1180 px; the failed task list says so; the rail no longer stretches),
and the audit now records a control that cannot be pressed together with what covers it, waits for finite animations before
measuring, and reads the viewport width the page itself sees. The 0.8.1 console is audited in
`reports/attest-deployment-2026-10-19f/`.

## The confirmation step and cost labels

See `../spending/README.md`. In live mode the Run button opens a confirmation; only its own button sends the request. The cost
figures are labelled as inference (the estimate, the history rows, the meters of a live and of a finished run, the failure record,
the hero replay and the frozen-evaluation table), and a development run shows "team allowance" instead of a USD amount. The
frozen-evaluation section now says that its figures measured the version pinned on 17 Oct 2026 (commit 6b786a2e), not the version
the console runs (filled in from the health endpoint).
