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

## Rollback

`/opt/attest/app.prev` is the 17 Oct 17:17 build (pinned code, M3 console). Restore with
`mv /opt/attest/app /opt/attest/app.failed && mv /opt/attest/app.prev /opt/attest/app && systemctl restart attest.service`,
or stop the service and remove only its vhost with `rollback.sh`. Not exercised today.

## Files

`before-20261018a-20261018T083410Z.txt`, `after-20261018a-20261018T083514Z.txt` (host snapshots), `health-after-20261018a.json`,
`screens/` (production captures; excluded from the public export like every screenshot).
