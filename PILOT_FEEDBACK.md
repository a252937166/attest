# Attest pilot feedback

Fill in what applies; delete the rest. Attach the run directory (`runs/<task>-<timestamp>`, zipped). It contains no
credentials. Thank you.

## Who and what

- Repository and commit you used:
- Your statement (or the file):
- Date, Attest version (`python -c "import attest; print(attest.__version__)"`):

## Setup

- Did `preflight` pass on the first try? If not, what did it print?
- Time from clone to first `attest run`:

## Import

- Did the import refuse anything? Which limit did it name, and was the message enough to fix it?
- Did `SOURCE.json` match what you expected (file count, skipped files)?

## Run

- Verdict and the first reason line from `PROOF.md`:
- Did the sealed tests match what you meant by your statement? Which test was wrong or missing, if any?
- Did the breaker find anything real? Anything it asserted that your contract never required?
- If the arbiter ran: do you agree with its classification?
- Wall time and committed USD (from the ledger section of `PROOF.md`):

## Bundle

- Did `attest check` pass? If not, paste the first failing line.
- What in `PROOF.md` did you read first, and what did you not understand?

## Anything else

- The one thing you would change:
- Would you run it on a second task? Why or why not?
