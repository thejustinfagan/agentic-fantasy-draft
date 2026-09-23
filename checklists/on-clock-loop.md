# On-clock loop checklist

A resumed draft is a new decision boundary.

- [ ] Discard the prior on-clock card
- [ ] Fetch the live pick ledger and ownership with cache-busting
- [ ] Confirm current pick, owner on the clock, and the next actual owned selection
- [ ] Mark newly drafted exact IDs unavailable
- [ ] Update rosters and positional-run context
- [ ] Recompute tier breaks, wait cost, and likely survival to the next owned pick
- [ ] Apply roster guardrails and phase-specific scoring
- [ ] Generate one recommendation and ranked pivots
- [ ] Re-fetch state immediately before any executor acts
- [ ] Submit at most once, and only in Ask me / earned Full auto
- [ ] Verify exact ID in the expected cell and the official ledger
- [ ] Re-arm the watcher for the next owned pick

Any commissioner undo, pick trade, or ownership change invalidates the prior
recommendation.
