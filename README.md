# Agentic fantasy draft

Public template for running a fantasy draft the way a [Grok Bot](https://x.com/i/status/2102419898571825304) actually ran one: doctrine first, a frozen exact-ID board second, live Sleeper state third, a decision card fourth, and only then an optional click that must verify the exact player ID.

> “I Let a Grok Bot Run My Fantasy Draft.” — [x.com/i/status/2102419898571825304](https://x.com/i/status/2102419898571825304)

**Grok Bot** is two words. This repository is a method kit, not a rankings feed.

## What this is

A reusable operating contract plus the scripts that keep it honest:

1. Load league doctrine.
2. Freeze a local decision board (exact Sleeper IDs, tiers, keepers, hard avoids).
3. Reconcile live Sleeper state with a bounded, read-only preflight.
4. Emit one decision card.
5. Optionally click once in an already-authenticated browser.
6. Verify the exact ID in the expected cell and the cache-busted official ledger.

If any live-state gate fails, the only authorized reply is:

```text
STATE MISMATCH — NO DRAFT AUTHORIZATION
```

## What this is not

- A rankings product
- A Sleeper write client or unofficial API mutator
- ThreadPlay
- A license to dump a fallback CSV into Sleeper auto-pick

Sleeper's public API is **GET only**. Writes are a browser click plus exact-ID verify, or a human on a phone.

## Modes

| Mode | What happens |
|---|---|
| **Show me** | Decision card only. Human submits. |
| **Ask me** | Card plus an explicit one-pick approval gate. |
| **Full auto** | Earned after clean counted rehearsals. Watcher label encodes draft-scoped auto-submit. Exact-ID gates still apply. |

Full auto is earned, never assumed. Platform auto-pick stays **OFF** unless the operator explicitly enables it.

## Quick start

```bash
python3 -m unittest discover -s skills/fantasy-draft-decision-operations/scripts/tests -v
```

Point the scripts at a **private** copy of your league artifacts, never at committed live ids:

```bash
export LEAGUE_DATA_DIR=/path/to/private/league-data
export LEAGUE_ID=your-sleeper-league-id
export DRAFT_ID=your-sleeper-draft-id
export TEAM_NAME="Harbor Cats"   # example only; use your real team label locally

python3 skills/fantasy-draft-decision-operations/scripts/live_preflight.py
python3 skills/fantasy-draft-decision-operations/scripts/sleeper_turn_watcher.py \
  --owned-picks 2,7,10 \
  --teams 4 --rounds 4 \
  --event-label HARBOR_CATS_ON_CLOCK
python3 skills/fantasy-draft-decision-operations/scripts/verify_sleeper_keepers.py \
  league/examples/keeper_manifest.json --teams 12
```

`league/examples/` is an obviously fake Harbor Cats / Cole Voss league. Copy it. Replace it. Do not treat `fake-*` ids as real players.

## Layout

```text
README.md
ARCHITECTURE.md
LICENSE
skills/fantasy-draft-decision-operations/
  SKILL.md
  scripts/live_preflight.py
  scripts/sleeper_turn_watcher.py
  scripts/verify_sleeper_keepers.py
  scripts/tests/
  references/
league/examples/          # FAKE Harbor Cats fixtures
schemas/                  # approval card, decision row, season state, action event
docs/
prompts/
checklists/
```

## Operating documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — layers, authority order, fail-closed boundary
- [docs/decision-product-method.md](docs/decision-product-method.md) — how the frozen board is built
- [docs/operating-modes.md](docs/operating-modes.md) — Show me / Ask me / Full auto
- [docs/control-boundary.md](docs/control-boundary.md) — read-only API, write paths
- [docs/sleeper-ui-execution.md](docs/sleeper-ui-execution.md) — authorized browser click + verify
- [docs/near-turn-paired-pick-optimization.md](docs/near-turn-paired-pick-optimization.md)
- [docs/in-season-waiver-trade-shadow-review.md](docs/in-season-waiver-trade-shadow-review.md)
- [skills/fantasy-draft-decision-operations/SKILL.md](skills/fantasy-draft-decision-operations/SKILL.md) — the agent contract

## Data-source policy

Use free/public sources only. Sleeper is authoritative for live league state.
Official NFL/team sources should confirm schedules, game status, and material
injury news. Never commit credentials, cookies, tokens, browser profiles, or
authenticated session data.

## License

MIT. Use the method. Keep the fail-closed phrase. Do not ship someone else's
real league dump inside a fork.
