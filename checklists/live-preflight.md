# Live preflight checklist

Do not issue a live recommendation until every gate passes.

- [ ] `LEAGUE_DATA_DIR`, `LEAGUE_ID`, `DRAFT_ID`, and `TEAM_NAME` are set
- [ ] Doctrine, player board, tiers, rookie board, hard avoid, keeper cells, ownership, and draft order files exist
- [ ] Exact IDs are unique; empty IDs fail closed
- [ ] Ownership rows equal live `teams × rounds` and belong to this `DRAFT_ID`
- [ ] Draft status is `pre_draft`, `drafting`, or `paused`
- [ ] Final slot/order is known from live state
- [ ] All draft cells are unique and ownership is reconciled after trades
- [ ] Keeper-occupied cells map to exact IDs and owners
- [ ] Remaining live selections come from live ownership, not ordinary snake spacing
- [ ] Pick ledger is monotonic and complete through the current pick
- [ ] Current team roster matches keepers plus verified selections
- [ ] Every candidate has an exact platform ID
- [ ] Keeper, hard-avoid, waiver-only, unavailable, and uncleared manual players are excluded
- [ ] A state-aware rolling queue of 8–12 names can be produced

If any live-state gate fails:

`STATE MISMATCH — NO DRAFT AUTHORIZATION`
