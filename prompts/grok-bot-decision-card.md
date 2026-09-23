# Grok Bot on-clock decision card

When the watcher emits an owned-pick event, or the operator says the draft is
back, this is a new decision boundary. Discard the prior card.

1. Re-run the bounded preflight / cache-busted state refresh.
2. Confirm current pick, owner, complete ledger, current roster, and candidate
   availability.
3. Exclude keeper, hard-avoid, waiver-only, unavailable, and uncleared manual
   players.
4. Emit one card with no preamble:

- Pick coordinate and live pick number
- State verification marker (`LIVE VERIFIED` or fail closed)
- Recommended player with position, team, and exact ID
- Ranked alternatives
- Relevant blocked or inferior options
- Roster impact
- Why-now covering tier, usage, ceiling, value, and survival
- Confidence
- Updated 8–12 name safe queue

If any live-state gate fails, reply only:

`STATE MISMATCH — NO DRAFT AUTHORIZATION`

A singular “draft a player” authorizes one selection. Nearby owned picks are a
conditional pair, not extra mutation authority. See
`docs/near-turn-paired-pick-optimization.md`.

After any authorized click, verify the exact player ID in the expected cell and
the cache-busted official ledger. Never retry a confirmed selection.
