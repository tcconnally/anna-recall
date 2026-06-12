# Claims Audit — anna-recall

**Date:** 2026-06-12 · **Audited:** README.md vs code on `master`

## Findings (ranked by judge visibility)

### MEDIUM — Existing `tests` CI never runs

`.github/workflows/test.yml` triggers on `main`, but the default branch is
`master` — the workflow has never executed on a push. The new smoke-test
workflow (`ci/smoke-tests` branch) targets `master` and is green; `test.yml`
should be fixed the same way (one-word change).

### LOW — "battle-tested persistent memory backend"

Mimir is real, healthy, and has a meaningful Rust test suite, but it was
created 2026-06-06 — six days before this audit. "Battle-tested" is the kind
of adjective a judge can puncture with one question. "Tested, fully local"
is accurate and still strong.

### RESOLVED (previously HIGH) — deadlock and dead-Mimir handling

The deep-dive gaps are closed on current `master`:
- stdout drained by a dedicated reader thread with timeout semantics; stderr is `DEVNULL` specifically to avoid the undrained-pipe deadlock (commented in code).
- Dead backend → one restart attempt, then a typed `MimirUnavailable` error; no restart loop on handshake failure.
- 15/15 unit tests pass, with backend calls stubbed at the `_mcp_send` seam.

## Verified claims

- Persistent memory via Mimir MCP (store/recall/context/stats/health wired through the plugin protocol). ✓
- Tests run with no real mimir binary, as the test docstring claims. ✓
