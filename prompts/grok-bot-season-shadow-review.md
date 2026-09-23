# Grok Bot in-season shadow review

Use `docs/in-season-waiver-trade-shadow-review.md`.

1. GET-only public league state. No cookies, tokens, or writes.
2. Validate identity, freshness, and checksums.
3. Separate waiver-status players from free agents. If the public endpoint
   cannot establish an exact waiver deadline, say so.
4. Treat the frozen board as shortlist evidence, not current role truth.
5. Evaluate the named drop and roster geometry, not only global player score.
6. Promote only evidence-qualified moves. Tiny positive trade deltas are
   `NO TRADE`.
7. Every generated card stays `NOT_APPROVED`. Execution stays `DISARMED`.
8. Close with machine-verifiable receipts: snapshot id, candidates evaluated,
   search-space scope, cards created/approved, validation result, execution
   flag, mutation count (must be zero).

If current evidence reverses an automatic candidate, mark it HOLD/superseded.
Do not ask the operator to reject a move the review itself no longer supports.
