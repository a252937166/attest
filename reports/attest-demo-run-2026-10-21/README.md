# The owner-approved live run of 21 Oct 2026 (the demonstration film)

On 21 Oct 2026 the owner approved one real Nemotron run on the public console, started on camera through the page, for the
demonstration film. This folder records it: the run, how it was started, what it cost, and the offline check of its bundle.

| Item | Value |
| --- | --- |
| Run | `semver-is-compatible-pr368-v2-20261021T070345824312Z` |
| Task | Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests |
| Started, finished (UTC) | 07:03:45.9, 07:09:35.0 (5 min 49 s) |
| Console | 0.10.3, the public Nemotron profile (judge-demo), a $0.50 cap for the run |
| Verdict | **NO CHANGE** |
| What happened | Nemotron 3 Ultra wrote the specification (17 criteria). The contract audit found it consistent. Nemotron 3 Super sealed 17 tests, accepted on the third sealing attempt (sha256 `18f3c7cae3e0`). The red check found 16 of 17 failing on the unmodified base, as required. The implementer (Nemotron 3 Super) then used its whole budget of 12 turns without producing a patch: its last edit was refused by the write policy, because the text it targeted occurs three times in the file. There was no candidate, so nothing was verified and nothing was certified, and the page says so. |
| Inference | $0.143683, 17 model calls (Ultra 2, Super 15), 170,412 tokens in, 54,120 out |
| Sandboxes | 6 operations |
| Offline check | From a fresh clone of the public repository, `python3 -m attest check` on the zip downloaded from the console: OK, EVIDENCE COMPLETE for verdict NO CHANGE (protocol v5, manifest verified). 19 checks, 0 errors, 0 warnings (`terminal/check-output.txt`). |

## How it was started and recorded

The recorder is scratchpad tooling for the film, not part of the product. It drives Chrome at 1920 x 1080 (device scale 2) and aborts
every request that is not a GET or HEAD, except the explicit allowlist of this shot:
- one `POST /api/runs`, used once, at 20.1 s into the recording, by the page's own confirmation button;
- the download-ticket POSTs, used once, for the bundle download at the end.

The page refuses to start a paid run from a browser that declares automation (`navigator.webdriver`). For this one owner-approved run,
the recording browser was launched without that declaration (`--disable-blink-features=AutomationControlled`), so the recorded click
went through the same confirmation step a person uses. The guard in the product is unchanged. The server's own protections all applied
unchanged: the `X-Attest-Confirm` header, the per-visitor rate limit, and the per-run and daily caps.

Budget on 21 Oct (UTC day):
- before the run: $1.4319 committed, $0.5681 remaining;
- during the run: $0.50 reserved;
- after the run: $0.143683 committed for it, so $1.575583 in all and $0.42 remaining.

No further public run could start that day, by design: a run reserves its whole $0.50 cap.

The outcome was not chosen. The film shows this run as it happened, from the click to the NO CHANGE verdict, the bundle download and
the offline check. For what an accepted patch looks like, it then shows a VERIFIED run from the 21 Oct evaluation; that was the
owner's decision after the run.

## Files

- `semver-is-compatible-pr368-v2-20261021T070345824312Z-proof-bundle.zip`: the bundle as downloaded from the console on camera. The zip
  stays in the private tree, because the public export takes no archive. Its unpacked contents are in
  `bundle/semver-is-compatible-pr368-v2-20261021T070345824312Z/`, which `python3 -m attest check` reads as a run directory.
- `terminal/session.sh`, `terminal/session.cast`: the real terminal session (asciinema 2.4.0, 110 x 24) of the fresh clone and the
  check, replayed in the film. The script types each command at a human pace, then runs it.
- `terminal/check-output.txt`: the check's output, from the cast.
- `recording.json`: the recorder's marks for the shot, with local paths removed: each stage change with the meters at that moment, the
  allowed request, and the download.
