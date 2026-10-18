# Console redesign, second pass (18 Oct 2026): verification record

The owner's review of the M3 console: the brand was not visible, a newcomer got no guidance, there was too little
motion, and the page did not look like a finished product; the home page had to say what problem the project solves,
who provides the core capabilities and how to use it, with one clear entry point. The second pass is described in
`attest-console.md` ("Console redesign, second pass"). It changes only `attest/app/static/` (`index.html`, `styles.css`,
`app.js`): the server, the API and the package digest recorded in bundles are untouched.

Evidence level of everything in this folder: **internal rehearsal**. The pages were exercised by a script in a real
browser against recorded evidence; no outside person has used the new console yet.

## What was verified in a real browser

`capture.py` starts its own console (uvicorn from `.venv`) on a free port with a temporary data directory, imports five
recorded run directories from the reports (the 15 Oct judge run of durationkit, VERIFIED; the rle-encode hold and the
plain agent's rle-encode run of 15 Oct; the roman-to-numeral contract dispute; the HTTP 422 provider error of the first
Nebius pilot attempt) and replays the judge run as synthetic fixtures with `scripts/console_replay.py` (`replay-running`
at 6 s per event, `replay-queued` with a 240 s delayed start, `replay-refresh` at 0.8 s per event for the keyed-update
test). Google Chrome (Playwright, `channel="chrome"`, headless), viewports 1440 x 960 and 390 x 844, dark scheme, fonts
loaded from Google Fonts during the capture. Record: `capture-record.json`; screenshots: `screens/` (excluded from the
public export and from the deployment bundle, like every development screenshot).

| Screen (`screens/`) | What it shows |
| --- | --- |
| `home-1440.png`, `home-hero-1440.png`, `home-390.png` | the home page: hero with the start panel, problem, phase chain, providers, how to use, recorded evidence, frozen evaluation, footer |
| `home-how-1440.png` | the "How it works" section reached from the navigation of a run page (view switch without reload) |
| `verified-overview-1440.png`, `verified-overview-390.png`, `verified-tests-1440.png`, `verified-activity-1440.png`, `verified-files-1440.png`, `verified-patch-1440.png` | the VERIFIED case file, every tab |
| `needs-human-overview-1440.png`, `needs-human-tests-1440.png`, `needs-human-tests-390.png` | the rle-encode hold with the failing sealed test, its counterexample block and the arbiter's classification |
| `contract-dispute-tests-1440.png` | the roman-to-numeral hold (contract dispute) |
| `error-overview-1440.png`, `error-overview-390.png` | the ERROR case file with exhibit E7 |
| `running-overview-1440.png`, `running-overview-390.png`, `queued-overview-1440.png` | the live views on synthetic fixtures, labelled as such on screen |
| `guide-step1-1440.png` to `guide-step4-1440.png` | the guide on the hold: decision, can I accept it, gates (tab switched by the guide), counterexample (spotlighted) |
| `verified-tests-scrolled-compact-1440.png` | the sticky decision header compacted after a 900 px scroll |
| `running-after-refreshes-1440.png` | the running view after 20 refresh cycles |

| Check | Result |
| --- | --- |
| Page errors and console errors across all captures | none |
| Guide opens on a finished run; step 3 switches to the Tests tab; step 4 spotlights the counterexample block (`counter error spot`); closing hides the panel, shows the launcher and stores `off` | as expected |
| Brand link from a run page returns to `/` without a reload; view `home`; the shared workspace form is moved into `workspace-slot-home` | yes |
| Sticky decision header compact after a 900 px scroll | true |
| Keyboard: ArrowRight from the Overview tab selects Patch (`#patch`); ArrowDown in the history moves to the next row; Enter opens it and marks it current | as expected |
| Keyed updates: 20 polls at 300 ms on a replay advancing every 0.8 s; the `stages-help` disclosure open before and after; focus on `det-stages-help` before and after; log rows 5 to 13; full renders 1; the guide's title moved from "Now: Writing the specification" to "Now: Implementing" without a re-render of the pane | ok |
| Offline suite (`.venv/bin/python -m unittest discover -s tests -q`), including the console tests that the public page and the static files name no gateway and that `/runs/{id}` serves the console for deep links | 145 tests, OK |
| `grep -il "codex\|axiqo" attest/app/static/*` | no match |

Visual review by the author on the captures above (two rounds): the first round found the navigation tagline colliding
with the section links at 1440 px, the phase descriptions invisible in a full-page capture because they waited for an
intersection observer, the price pill squeezing the live-mode text in the rail, and a spotlight rule that would have
un-stuck the decision header; all four were fixed and re-captured. The guide covered most of a phone screen on first
open, so it now starts collapsed on screens up to 900 px wide.

## Second round, after the owner's review of the live site (09:00 to 09:40 UTC)

The owner reported the live page as broken and motionless and not in the spirit of their reference sites. The
deployment report (`reports/attest-deployment-2026-10-18/README.md`) records the cause on the delivery side (assets
cached from the previous build) and the fix. On the design side the page was brought up to the reference energy, and a
defect in every capture above was found and fixed:

- **Correction to the first round.** In all first-round screenshots the brand mark rendered as a bare caret: the SVG
  holding the mark's gradient definition was `display:none`, and Chrome does not resolve `url(#…)` paint servers from
  hidden SVGs, so the ring and the check (both gradient-stroked) were invisible. The definitions now live in a zero-size,
  visually hidden SVG; the mark renders with its dashed seal ring, inner ring and check (`screens/lockup-1440.png`).
- **Visual pass.** A gradient brand lockup with the mark above the headline and a "built on" line naming the providers;
  a two-row navigation (brand and status, then a section bar with an underlined active link); pill buttons; a stronger
  three-colour aurora with a grain overlay; a drawn underline under "with proof"; totals that count up once; blocks
  that rise once as they scroll into view; a guide line at the left with a beacon that follows the reading position.
- **Reduced motion.** Instead of removing every animation, the looping and travelling effects stop and one-shot
  entrances become instant, the policy the reference sites use.

Re-captured with `capture.py --quick`: 24 screens, no page or console errors, every behavioural check as before; the
offline suite still passes (145 tests) and the static files still name no gateway. The live site was then rendered in
fresh desktop and phone browsers (see the deployment report).

## Not verified, stated plainly

- No outside developer or judge has used the page; the guide's wording is the author's.
- The light colour scheme of M3 no longer exists; the page declares `color-scheme: dark`.
- Offline, Instrument Serif falls back to the declared system serif; the captures had network access to the font service.
- The demo run of 17 Oct (`durationkit-units-001-20261017T172421506287Z`) lives in the server's data directory and is not
  among the local fixtures, so the hold shown here is the rle-encode hold of 15 Oct.

## Reproduce

```bash
python3 reports/attest-ui-2026-10-18/capture.py            # system python3 with Playwright and Google Chrome; the console runs from .venv
python3 reports/attest-ui-2026-10-18/capture.py --quick    # screenshots and checks without the 20-refresh test
```
