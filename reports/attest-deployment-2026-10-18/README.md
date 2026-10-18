# Deployment of the 18 Oct 2026 console to yungou (08:33 to 08:38 UTC)

What was deployed: the second pass of the console (`attest/app/static/index.html`, `styles.css`, `app.js`: home page,
brand, contextual guide, motion; see `attest-console.md`, "Console redesign, second pass"), the updated console notes and
the UI verification report `reports/attest-ui-2026-10-18/`. No Python file changed, so the package digest recorded in
bundles is the pinned one before and after. No Nebius call was made; a restart spends nothing (the daily budget read
$2.00 of $2.00 before and after).

## Build

- `python3 scripts/export_public.py --out dist/public --force`: every exported bundle verified, no scan hits.
- `deploy/yungou/build_bundle.sh` run from `dist/public`: `app.tar.gz`, 5.2 MB, sha256
  `d87673d4fa0e18eb3c5e6fd236eff4b62f61b3bb127c20f4775b0eaeba3aa16e`, verified again on the server after upload. This was
  the first real run of the script's AppleDouble exclusion added on 17 Oct (then checked with `bash -n` only): the listing
  check passed and the installed tree holds no `._*` file (see below).

## Procedure (UTC)

| Time | Step | Result |
| --- | --- | --- |
| 08:33 | upload of `app.tar.gz`, `install.sh`, `snapshot.sh`, `rollback.sh`, `attest.service`, `attest.axiqo.xyz.conf` to `/var/tmp/attest-deploy/` | bundle digest matches |
| 08:33 | pre-checks | staged `attest.env` identical to `/etc/attest/attest.env` (`diff -q`); health: version 0.3.0, worker alive, current none, queue 0; 39 run rows, none queued or running |
| 08:34 | store backups | `attest.db.bak-20261018a` (plain copy of the main file, 4 KB: the data sat in the 1.99 MB write-ahead log) and `attest.db.bak-20261018a-full` (SQLite backup API, 80 KB, 39 rows) |
| 08:34:10 | `snapshot.sh before-20261018a` | `before-20261018a-20261018T083410Z.txt` |
| 08:34 | `MEMORY_MAX=200M bash install.sh` | pinned dependencies already satisfied; service restarted; nginx configuration test OK (the usual deprecation warnings of other vhosts); previous tree kept as `/opt/attest/app.prev` (the 17 Oct 17:17 build) |
| 08:35:08 | `GET /api/health` (`health-after-20261018a.json`) | ok, version 0.3.0, worker alive, queue 0, nothing reconciled or deduplicated at startup, 1,345 MB free (9.7%), budget: $0 committed, remaining $2.00 |
| 08:35:14 | `snapshot.sh after-20261018a` | `after-20261018a-20261018T083514Z.txt`; diff against before: the timestamp, memory, swap and load lines only; services, listeners, containers, nginx configuration and the other sites' health codes identical |

The health text "$0.0000 committed + 1 active reservation(s) within $2.00" next to `active_runs: 0` is by design:
`nebius_budget_ok` is the recheck a run performs before execution and counts the prospective run itself (`max(1, active)`);
`/api/health` reuses it to say whether another run fits.

## Verification after the install

| Check | Result |
| --- | --- |
| `find /opt/attest/app -name '._*' \| wc -l` | 0 |
| `attest_revision()` on the server | `166cdcbd46a74cd0…` over 35 files (the pinned evaluation revision) |
| `GET /` on 127.0.0.1:4070 | contains the new home page ("Patches should arrive") |
| `/static/app.js`, `/static/styles.css` | 200, 79,341 and 33,430 bytes, the exported files |
| `https://attest.axiqo.xyz/` | 200, "Start here" present |
| `https://attest.axiqo.xyz/api/profiles` | the public Nemotron profile only, `team: false` |
| `/api/runs?limit=200` | 39 rows |
| `attest.service` | active, 48.8 MB resident |
| Real browser on the public URL (headless Chrome, 1440 px) | Instrument Serif loaded; ticker "39 recorded runs, 8 VERIFIED, 11 NEEDS HUMAN, 20 other verdicts"; the 17 Oct demo run `durationkit-units-001-20261017T172421506287Z` opens from the evidence list with its NEEDS HUMAN seal and the guide at "The decision"; no page or console errors (`screens/public-home-1440.png`, `screens/public-demo-run-1440.png`) |

## Correction at 08:38 UTC: one stylesheet rule

The production capture showed the Overview of the demo run overflowing the viewport to the right: the two-column grid
let a long exhibit summary widen its column (grid items default to `min-width: auto`). One rule was added to
`styles.css` (`.overview>.block,.proves>div{min-width:0}`), the public export was rebuilt, and the single file was
replaced in place on the server (`scp` to `/opt/attest/app/attest/app/static/styles.css`, root-owned, mode 644; static
files are read from disk per request, so no restart). The server copy's sha256 is
`7765f215af47b0809ed677e85fb40b6b0278a5a82c57600e730a63f74302d08c`, the exported file's digest; 33,595 bytes served. The
re-rendered demo run reports `scrollWidth` equal to `innerWidth` (1440) and the served stylesheet carries the rule
(`screens/public-demo-run-after-css-1440.png`). The deployed tree therefore equals the public export at the time of this
report; the bundle digest `d87673d4…` above describes the tree before this one-file replacement.

## Second deployment of the day, 09:29 UTC: cache-safe assets and the visual pass after the owner's review

The owner opened `https://attest.axiqo.xyz/` after the 08:35 deployment and saw a broken, motionless page unlike their
reference sites. Diagnosis from here: the static files were served with `Last-Modified` and `ETag` but no
`Cache-Control`, so a browser that had loaded the previous console earlier in the day could reuse the old `styles.css`
and `app.js` under heuristic freshness while fetching the new `index.html` (served without validators, hence always
fresh): new markup with the old stylesheet and script is exactly a broken page without motion. Two independent fixes:
the HTML now references `styles.css?v=20261018b` and `app.js?v=20261018b` (no cache holds those URLs), and the vhost
adds `Cache-Control: no-cache` to every response so browsers revalidate against the ETag from now on. The deployment
rule is recorded in `deploy/yungou/README.md`: bump the version query whenever a static file changes.

The same build carries the visual pass the review asked for (`attest-console.md`, "Console redesign, second pass",
second round): the brand lockup, the two-row navigation with a section bar, pill buttons, a stronger aurora with grain,
the drawn underline, counters, scroll-triggered reveals and the beacon line. It also fixes a defect present in every
earlier capture: the SVG that defines the mark's gradient was `display:none`, and Chrome does not resolve paint servers
from hidden SVGs, so the mark had rendered as a bare caret without its ring and check. The definitions are now in a
zero-size, visually hidden SVG and the mark renders completely.

| Time | Step | Result |
| --- | --- | --- |
| 09:27 | export (every bundle verified, no scan hits), `build_bundle.sh` from `dist/public` | `app.tar.gz` 5.0 MB, sha256 `8f0184ace9e82df2feca76f450cc20fb7102fdc6d6ced1f863433d334a4bf385`, no AppleDouble entries |
| 09:28 | upload with `install.sh` and the vhost; pre-checks | digest matches; service idle (current none, queue 0) |
| 09:28 | store backup through the SQLite backup API | `attest.db.bak-20261018b-full`, 39 rows |
| 09:29:03 | `snapshot.sh before-20261018b` | `before-20261018b-20261018T092903Z.txt` |
| 09:29 | `MEMORY_MAX=200M bash install.sh` (installs the vhost, `nginx -t`, reload) | service restarted, nginx configuration test OK |
| 09:29:18 | `GET /api/health` (`health-after-20261018b.json`) | ok, version 0.3.0, worker alive, queue 0, nothing reconciled |
| 09:29:25 | `snapshot.sh after-20261018b` | diff against before: timestamp, memory, swap and load only |

| Check after the install | Result |
| --- | --- |
| `find /opt/attest/app -name '._*' \| wc -l` | 0 |
| `attest_revision()` on the server | `166cdcbd46a74cd0…` over 35 files, unchanged |
| `https://attest.axiqo.xyz/` headers | `Cache-Control: no-cache` |
| `/static/styles.css?v=20261018b`, `/static/app.js?v=20261018b` | 200 with ETag and `Cache-Control: no-cache` |
| Public HTML | references the versioned assets; carries the lockup |
| `/api/runs?limit=200` | 39 rows; service active, 47.2 MB resident |
| Fresh headless Chrome, 1440 px | the versioned assets are what loads; Instrument Serif active; ticker "39 recorded runs, 8 VERIFIED, 11 NEEDS HUMAN, 20 other verdicts"; section bar active on Overview; the demo run opens with its NEEDS HUMAN seal and a sticky header offset under the two-row navigation; no horizontal overflow; no errors (`screens/public-home-b-1440.png`, `screens/public-lockup-b-1440.png`, `screens/public-demo-run-b-1440.png`) |
| Fresh headless Chrome, 390 px | no horizontal overflow, no errors (`screens/public-home-b-390.png`) |

A visitor whose browser still holds the 08:35 assets gets the new page on the next normal load: the HTML is never
served from cache and now names asset URLs no cache has seen.

## Third deployment of the day, 10:00 UTC: the console's own design, Nebius-leaning, with technical figures

After the second deployment the owner asked for a layout of Attest's own rather than an echo of their reference site,
the Nebius and stakeholder marks with a visual language close to the Nebius platform (typography included), more
figures illustrating the technical design, and a shorter evidence section (the one-row-per-run list was "long-winded").
The third pass is described in `attest-console.md` ("Console redesign, second pass", third round) and verified in
`reports/attest-ui-2026-10-18/README.md`. Static files only, plus the official Nebius logo file under
`attest/app/static/brand/`; the package digest is unchanged.

| Time | Step | Result |
| --- | --- | --- |
| 09:59 | export (every bundle verified, no scan hits), `build_bundle.sh` from `dist/public` | `app.tar.gz` 5.3 MB, sha256 `832d877866d2ff22d5a4293340196086556b906f46c543833d1ffcc1c41702bb`, the brand folder included, no AppleDouble entries |
| 10:00 | upload with `install.sh` and the vhost; pre-checks | digest matches; service idle (current none, queue 0) |
| 10:00 | store backup through the SQLite backup API | `attest.db.bak-20261018c-full`, 39 rows |
| 10:00:58 | `snapshot.sh before-20261018c` | `before-20261018c-20261018T100058Z.txt` |
| 10:01 | `MEMORY_MAX=200M bash install.sh` | service restarted, nginx configuration test OK |
| 10:01:05 | `GET /api/health` (`health-after-20261018c.json`) | ok, version 0.3.0, worker alive, queue 0, nothing reconciled |
| 10:01:09 | `snapshot.sh after-20261018c` | diff against before: timestamp, memory, swap and load only |

| Check after the install | Result |
| --- | --- |
| `find /opt/attest/app -name '._*' \| wc -l` | 0 |
| `attest_revision()` on the server | `166cdcbd46a74cd0…` over 35 files, unchanged |
| `/static/styles.css?v=20261018c`, `/static/app.js?v=20261018c`, `/static/brand/nebius-logo.svg?v=20261018c` | 200; `Cache-Control: no-cache` on the page |
| Public HTML | references the `20261018c` assets, the bundle replay and the Nebius logo |
| `/api/runs?limit=200` | 39 rows; service active, 40.9 MB resident |
| Fresh headless Chrome, 1440 px | the `20261018c` assets load; Inter, Newsreader and Space Mono active; ticker "39 recorded runs, 8 VERIFIED, 11 NEEDS HUMAN, 20 other verdicts"; per-task table 6 rows, latest list 5 rows; the Proof Bundle replay advances Freeze to Audit within seven seconds and cycles about every twelve; the Nebius logo file decodes at 131 by 36; "Open latest" opens the durationkit case file (NEEDS HUMAN); no errors (`screens/public-home-c-1440.png`, `screens/public-home-c-full-1440.png`, `screens/public-case-c-1440.png`) |

### Correction at 10:05 UTC: phone-width overflow

The phone render of the third pass scrolled sideways (document 476 px wide on a 390 px viewport): the latest-runs rows
kept their metadata on one line and could not shrink. Two rules were changed in `styles.css` (one-column rows with
wrapping metadata under 640 px, and `minmax(0, 1fr)` columns for the replay's stage strip), the export was rebuilt and
the single file replaced in place on the server as on 08:38 (root-owned, mode 644, no restart; browsers revalidate
against the ETag because of the `no-cache` header). Server sha256
`f7687ef48c386aa0c804820458f7933019127fba4bbcee50d5c592561e230d3d`, the exported file's digest, 40,592 bytes served. The
re-rendered site reports a document width equal to the viewport at 390 px and at 1440 px, with no errors
(`screens/public-home-c-390.png`). The bundle digest `832d8778…` describes the tree before this one-file replacement.

## Rollback

`/opt/attest/app.prev` is the 09:29 build of today (pinned code, the second-pass console with the cache fix); the earlier
builds are no longer staged on the host. Restore with
`mv /opt/attest/app /opt/attest/app.failed && mv /opt/attest/app.prev /opt/attest/app && systemctl restart attest.service`,
or stop the service and remove only its vhost with `rollback.sh`. Not exercised today.

## Files

`before-20261018a-20261018T083410Z.txt`, `after-20261018a-20261018T083514Z.txt` (host snapshots), `health-after-20261018a.json`,
`screens/` (production captures; excluded from the public export like every screenshot).
