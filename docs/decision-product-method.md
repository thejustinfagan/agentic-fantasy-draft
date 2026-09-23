# Draft decision product method

This is the sanitized method from the original Grok Bot draft build. It is a
deterministic, ID-driven baseline for a keeper league that publishes a frozen
board before live Sleeper state is trusted.

The Harbor Cats / Cole Voss files under `league/examples/` are fake illustrations
of the same artifact shape. Replace values; do not replace the method.

## Keeper-cell mechanics

Every listed keeper round is an occupied draft cell: that owner loses the live
pick in that round. Kept players remain in replacement-level inventory but are
excluded from the live fallback queue.

Example geometry (not a real league): a 12-team, 14-round board has 168 cells.
If the league lists 23 keepers, 145 cells remain live. A team that keeps two
players has 12 live selections, not 14. Draft order may be unset until Sleeper
assigns slots; exact between-turn survival odds must be recalculated from live
ownership, not ordinary snake spacing.

## Baseline and overlays

- Recompute free raw-stat projections under **this league's** scoring.
- Blend a public consensus overlay where a second source actually covers the
  player. Other players remain explicitly single-source or imputed.
- Subtract a documented imputed fumble penalty when free projection tables do
  not expose total fumbles.
- Derive replacement levels from the prior season's roster mix blended with a
  structural prior sized to the league (example one-QB PPR prior: QB 21, RB 60,
  WR 65, TE 22).
- Score current-year value as 60% VORP, 16% usage, 12% usage-backed ceiling,
  7% useful weekly floor, and 5% team environment, less injury/fragile-boom
  penalties.
- Apply rookie keeper option value only after the early rounds and increase its
  effect in the late rounds.
- Treat ADP as timing data, not player quality. Keeper-adjusted market pick
  removes kept players and maps remaining market rank through the actual
  live-pick count in each round.

## Automation gates

`KEEPER`, `HARD AVOID`, `MANUAL`, and `WAIVER ONLY` rows are never eligible for
automatic submission. The fallback CSV contains exact Sleeper IDs only for
currently eligible rows. Manual rows require the stated clearance condition and
a same-day source refresh.

## Known limitations

- Free full-season projection coverage is often dominated by one complete
  source; only a public top slice per position may receive a second-source
  blend. Label confidence accordingly.
- Routes and route participation are frequently unavailable from a reliable
  free source.
- Offensive staff changes should be heavily shrunk; unknown play callers are
  neutral, not penalized.
- A static board can know which cells are occupied without knowing the exact
  number of live picks between the user's turns until Sleeper publishes order.
- News and depth charts move quickly. Hard-avoid and manual gates are dated and
  must be refreshed before the live draft.

## Preset queue floor

Rookie target windows are hard earliest-round floors. Keeper-adjusted market
timing supplies a softer guardrail for veterans, while roster gates still
prevent an unnecessary QB2 or TE2 in ordinary one-QB / one-TE formats. This
makes the emergency preset safer than a pure value sort without suppressing
genuine league-scoring value gaps.

The fallback file is a reference order for Grok Bot, not a native Sleeper queue
to load wholesale. Sleeper prioritizes queued players when auto-picking, which
can bypass portfolio intent. Keep only a short rolling slice of roughly 8–12
currently eligible names in the live queue.
