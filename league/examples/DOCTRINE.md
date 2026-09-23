# Harbor Cats Invitational — example doctrine (FAKE)

This playbook is a public-template stand-in. It is not a real league contract.

## Format

- 12-team keeper, full PPR
- Starters: QB, 2 RB, 2 WR, TE, 2 FLEX
- Bench / IR: 6 bench, 2 restricted IR
- Scoring callouts: 6-point passing TD, -2 INT, no yardage bonuses
- Two keepers occupy exact draft cells and remove those live selections

## Control boundary

Sleeper's public API is read-only. League-changing actions require the operator's
explicit approval. Writes happen only as a browser click plus exact-ID verify,
or by the human on a phone.

## Operating model

Doctrine → frozen board → live Sleeper state → decision card → optional click → exact-ID verify.

If any live-state gate fails, the only authorized reply is:

`STATE MISMATCH — NO DRAFT AUTHORIZATION`

## Modes

- **Show me** — recommendation only.
- **Ask me** — recommendation plus an explicit approval gate before any click.
- **Full auto** — earned after clean rehearsals; still requires exact-ID verify and fails closed.

## Queue

Keep 8–12 currently legal names in a rolling queue. Never load a static fallback
board wholesale into Sleeper auto-pick.
