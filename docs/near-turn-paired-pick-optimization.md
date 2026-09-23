# Near-turn paired-pick optimization

Use this procedure when the user owns two draft selections separated by only a
few opponent picks—for example, a late odd-round pick followed by an early
even-round pick in a snake draft.

## 1. Fix the authorization boundary

- A singular request such as “draft a player” authorizes one mutation.
- A conditional next target is planning, not authorization.
- Stop after exact-ID verification of the first selection unless the user explicitly enabled continuous attendance or multi-pick auto-submit for that exact draft.
- A later “our pick again” or equivalent is a fresh decision boundary: fetch official state again before recommending or clicking.

## 2. Verify the actual pair

From the authoritative live ledger and ownership map, record:

- current pick, owner, roster, and timer/status;
- next actual owned pick after trades and keeper cells;
- number and identities of intervening selections;
- complete roster and fillable starter cells;
- every legal candidate’s exact platform ID and live availability.

Do not infer the next cell from ordinary snake spacing when ownership can move.

## 3. Optimize two opportunities, not two precommitted names

Partition the legal candidates into:

1. **Must take now** — material current value and low survival probability to the next owned pick.
2. **Conditional next targets** — strong value with a plausible survival path.
3. **Pivots** — legal alternatives if intervening picks remove the plan.

At the first pick, compare candidate pairs using:

- marginal starting-lineup value under the actual scoring;
- role security, health, and evidence freshness;
- positional/tier scarcity;
- likely survival to the next owned pick;
- roster resilience and correlated exposure;
- remaining selections needed for a legal, competitive roster.

Do not draft purely from raw projection or raw ADP. In all-superflex or position-light formats, conventional RB/WR/QB/TE balance is not the objective; expected fillable-starter value is. TE premium, reduced passing-TD scoring, or unusual starter geometry can reverse ordinary rankings.

A useful decision rule is:

```text
Take now = highest role-adjusted value whose loss before the next owned pick
           would most reduce the best achievable two-pick outcome.

Next target = best surviving legal candidate after the intervening ledger
              is observed—not the name planned before those picks.
```

## 4. Execute exactly once

Before each authorized selection:

1. Cache-bust the official ledger.
2. Confirm the expected current pick and owner.
3. Confirm the exact candidate ID is undrafted and legal.
4. Match full name, position, and team in the current visible row.
5. Click the immediate draft control once.
6. Verify the expected board cell by exact ID or unique player tuple.
7. Reconcile pick number, player ID, owner, and roster through the cache-busted official API.
8. Stop; do not treat the nearby next pick as implicitly authorized.

## 5. Tool-failure boundary

- If a selector or helper fails before the click line executes, refresh official state and reacquire current row geometry; do not report a mutation.
- If any exception occurs after a possible click, selection state is unknown. Read the exact official cell before retrying.
- Either a confirmed exact DOM cell or confirmed official API cell blocks a repeat click. Reconcile the second source, but never duplicate a confirmed pick.

## Output discipline

After the first pick, report the verified selection and label any later name only as a **conditional target**. At the next owned pick, discard the old card, refresh the ledger and roster, and issue a new decision.
