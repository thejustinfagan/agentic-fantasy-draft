# Architecture

This template packages the operating model from a real Grok Bot draft run.
It is a decision product with a hard execution boundary, not a write client.

```text
┌──────────────┐   ┌─────────────────┐   ┌──────────────────┐
│   Doctrine   │ → │ Frozen board    │ → │ Live Sleeper GET │
│  (rules,     │   │ (exact IDs,     │   │ (order, ledger,  │
│   risk,      │   │  tiers, gates,  │   │  keepers, timer) │
│   contract)  │   │  keepers)       │   │                  │
└──────────────┘   └─────────────────┘   └────────┬─────────┘
                                                  │
                                                  ▼
                                    ┌──────────────────────┐
                                    │     Decision card    │
                                    │  (exact ID + pivots) │
                                    └──────────┬───────────┘
                         Show me               │
                         human phone           │ Ask me / earned Full auto
                                               ▼
                                    ┌──────────────────────┐
                                    │ Browser click once   │
                                    │ + exact-ID verify    │
                                    └──────────────────────┘
```

If live state and the frozen artifacts disagree, stop:

```text
STATE MISMATCH — NO DRAFT AUTHORIZATION
```

## Layers

| Layer | Owns | Must not own |
|---|---|---|
| Doctrine | Format, roster math, risk, output contract | Live pick numbers |
| Frozen board | Value, tiers, eligibility gates, exact IDs | Current availability |
| Live Sleeper state | Order, ownership, ledger, timer, rosters | Player quality |
| Decision card | One recommendation and ranked pivots | Mutation |
| Executor | One authorized click | Research, queue invention |
| Verifier | Exact ID in expected cell + official ledger | A second click after success |

## Source authority

Highest to lowest, except that a lower file may only **add** restrictions:

1. Operator-approved doctrine (`DOCTRINE.md`)
2. Master player board
3. Position tiers
4. Rookie / keeper option board
5. Hard-avoid and manual gates
6. Keeper cells
7. Pick ownership
8. Current official draft state

Live state wins for current pick, owner, roster, and availability. The frozen
board wins for value. Union all safety restrictions.

## Scripts

All identity is environment or CLI. There are no baked-in league ids.

| Script | Role |
|---|---|
| `live_preflight.py` | One bounded JSON preflight. Exit 0 = `PASS`. Exit 2 = fail closed. |
| `sleeper_turn_watcher.py` | Read-only wake-up. Emits `ON_CLOCK` or `STATE_MISMATCH`. Does not click. |
| `verify_sleeper_keepers.py` | Snake-cell math plus optional live exact-ID keeper check. |

Required environment:

- `LEAGUE_DATA_DIR`
- `LEAGUE_ID`
- `DRAFT_ID`
- `TEAM_NAME`

`TEAM_NAME` may be the team label or the manager label (Harbor Cats or Cole Voss
in the fake examples). Keepers resolve against every alias on that row.

## Schemas

Season objects stay machine-checkable and secret-free:

- `schemas/approval_card.schema.json` — immutable approval card; generated cards start `NOT_APPROVED`
- `schemas/decision_row.schema.json` — unified forecast / hold / waiver / trade row
- `schemas/season_state.schema.json` — normalized GET-only snapshot
- `schemas/action_event.schema.json` — audit event without credentials

Draft execution modes (`SHOW_ME`, `ASK_ME`, `FULL_AUTO`) are recorded separately
from season `DISARMED` / `SHADOW`. A shadow review may run automatically and
still be unable to mutate.

## Keeper geometry

Untraded snake, `T` teams, seat `s`, round `r`:

```text
within_round = s                 if r is odd
within_round = T + 1 - s         if r is even
overall_pick = (r - 1) * T + within_round
cell_label   = r.within_round
```

Displayed even-round suffixes are not seat numbers. Traded picks use the
ownership artifact, not this formula. A keeper cell removes a live selection
even when it populates later in the board.

## Fail-closed rules

- Missing env, artifacts, or exact IDs → `BLOCK`
- Draft / league identity mismatch → `BLOCK`
- Ownership row count ≠ live `teams × rounds` → `BLOCK`
- Artifact owned cells ≠ live owned cells → `BLOCK`
- After `drafting` starts, wrong keeper ID in a cell → `BLOCK`
- Watcher sees the wrong recorded player on `--resume-after-pick` → `STATE_MISMATCH`
- Verifier exception after a possible click → state is **unknown**; read the official cell before any retry
- Confirmed exact ID → never click again

`pre_draft` with zero preloaded keepers is a warning, not a blocker. The
20-second grace period applies only at the `drafting` transition.

## In-season

The same boundary holds after the draft. Waivers, free agents, IR, lineups, and
trades may be analyzed automatically. Cards remain `NOT_APPROVED`. Execution
stays disarmed until the operator approves an exact-ID payload. Tiny positive
trade deltas are `NO TRADE`. See `docs/in-season-waiver-trade-shadow-review.md`.
