---
name: fantasy-draft-decision-operations
description: Use for fantasy draft and in-season decision safety.
version: 1.6.0
author: Grok Bot
license: MIT
metadata:
  grok_bot:
    tags: [fantasy-football, draft, decision-support, live-operations, safety]
    category: gaming
---

# Fantasy Draft Decision Operations

## When to Use

Load this skill when reviewing a live or mock fantasy draft, reconciling keeper or traded-pick boards, maintaining a state-aware draft queue, issuing exact-ID recommendations, or deciding whether draft execution is safe to authorize.

Use it when acting as a disciplined reviewer or recommendation engine—not as a generic fantasy analyst. The goal is a reproducible decision process that combines a frozen local board with authoritative live availability and roster state.

This is **Grok Bot** (two words). It is not a rankings product, not a Sleeper write client, and not ThreadPlay.

## Core operating model

Separate four concerns:

1. **Doctrine** — league rules, roster construction, risk tolerance, keeper rules, and output contract.
2. **Static decision product** — exact player IDs, ranks, tiers, eligibility, manual gates, hard avoids, and fallback order.
3. **Live state** — draft ID, status, final order, traded ownership, pick ledger, current owner, rosters, and timer.
4. **Execution** — handled by a separately authorized writer. A reviewer recommends and verifies; it does not click unless explicitly assigned that role.

Never let a strong static board substitute for missing live state.

The live loop is:

`doctrine → frozen board → live Sleeper state → decision card → optional click → exact-ID verify`

If any live-state gate fails, respond with:

`STATE MISMATCH — NO DRAFT AUTHORIZATION`

Then list verified static facts separately from unverified live facts. Never present provisional coordinates as actual picks.

## Source authority

Establish the source order before making recommendations. A robust default is:

1. User-approved playbook or league doctrine.
2. Master player board.
3. Position tiers.
4. Rookie/keeper option board.
5. Hard-avoid and manual-review controls.
6. Keeper cells.
7. Pick ownership.
8. Current live draft state.

Live state controls current pick, owner, roster, and player availability. The frozen board controls value. When a lower-authority file adds a stricter safety restriction, use the union of restrictions unless the doctrine explicitly says otherwise.

## Input refresh and discovery

1. Locate the canonical local repository or artifact bundle from `LEAGUE_DATA_DIR`. Never rediscover it by scanning the operator's home directory.
2. If it is a clean tracked repository, fetch the canonical remote before concluding that required files are missing. Inspect the remote tree first; fast-forward only when the working tree is clean and the update is unambiguous.
3. Read every required artifact before evaluating players.
4. Validate schemas, exact IDs, row counts, uniqueness, status enums, and as-of timestamps deterministically.
5. Treat filename variations as acceptable only after confirming the content and schema match the requested role.

Do not browse for new player research while a draft clock is running. Reading the official draft API is state retrieval, not player research.

## Non-blocking real-draft initiation

A real-draft initiation must not become a long LLM workflow that monopolizes the messaging session. The setup path is bounded and deterministic:

1. Require `LEAGUE_DATA_DIR`, `LEAGUE_ID`, `DRAFT_ID`, and `TEAM_NAME`. Do not invent ids and do not scan the filesystem for them.
2. Run `scripts/live_preflight.py` once. It batches read-only Sleeper API calls, validates the local artifacts, reconciles order/ownership/keepers, and emits one compact JSON result. It must normally finish within 15 seconds.
3. Treat platform-specific keeper timing correctly. Keeper picks are expected to populate when Sleeper transitions from `pre_draft` to `drafting`; zero preloaded picks during `pre_draft` is therefore a pending-state warning, not a blocker by itself. At the transition, allow a bounded 20-second API-consistency grace period, then require every listed keeper ID in its exact cell before issuing or executing a selection.
4. If it returns `BLOCK`, report the blocker immediately with `STATE MISMATCH — NO DRAFT AUTHORIZATION` and release the chat. Do not continue into browser selector research, session-history searches, repo-wide discovery, repeated API reads, or speculative repair.
5. If it returns `PASS`, perform at most one already-rehearsed browser identity/control verification batch. If that batch fails, fail closed and switch to watcher + human phone submission; do not debug selectors during initiation or while the clock runs.
6. Arm the detached watcher as a background process, verify it started, then return a final `ARMED` receipt so the main session lock is released. The watcher—not a live LLM turn—waits between picks.
7. On the watcher event, immediately re-run the bounded preflight/state refresh, produce the decision, submit only if execution remains verified, verify exact ID, re-arm, and return.

Do not create a `todo` list for live initiation. Do not load unrelated skills, inspect historical mock sessions, fetch the same endpoint repeatedly, or open/map the draft UI before deterministic state gates pass. Initialization is successful only when the user can continue using the chat while the watcher waits.

## Mandatory preflight

Do not issue a live recommendation until all required gates pass:

- Exact league and draft identity.
- Draft status is appropriate for the requested mode.
- Final slot/order is known from live state.
- All draft cells are unique and ownership is reconciled after trades.
- Keeper-occupied cells are mapped to exact IDs and owners.
- The user's actual remaining live selections are derived from live ownership, not ordinary snake spacing.
- Pick ledger is monotonic and complete through the current pick.
- Current team roster matches keepers plus verified selections.
- Every candidate has an exact platform ID.
- Keeper, hard-avoid, waiver-only, unavailable, and uncleared manual players are excluded.
- A state-aware rolling queue can be produced.

If any live-state gate fails, respond with:

`STATE MISMATCH — NO DRAFT AUTHORIZATION`

## Static versus live language

Use explicit labels:

- **Static verified:** internally consistent local artifacts.
- **Provisional:** computed from an order or ownership map that the playbook says is not final.
- **Live verified:** reconciled against the current official draft state.
- **Unknown:** unavailable or contradictory.

A static count of eligible players is not the current available-player count once any mock selections may exist. A static board head is not a safe rolling queue until every listed player is checked against the live ledger.

## Eligibility reconciliation

Build eligibility from the union of all restrictive sources:

- Board availability/status.
- Hard-avoid file.
- Manual-review file or manual gate fields.
- Rookie option board flags.
- Keeper cells.
- Live drafted-player IDs.

Rules:

- A `MANUAL` status remains blocked even if its clearance text is blank.
- A player absent from the master board cannot enter the queue merely because the live platform lists them.
- Missing exact ID is a hard block.
- If counts differ across QA and source files, compute and report the set difference rather than comparing totals alone.
- Duplicated restrictions are harmless; omissions must not silently clear a player.

## Rolling safe queue

Maintain 8–12 candidates that are all legal and acceptable now.

1. Remove every drafted, kept, hard-avoid, waiver-only, manual, or identity-unresolved player.
2. Apply round floors and earliest acceptable pick constraints.
3. Apply roster checkpoint and position-cap rules.
4. Keep enough RB/WR or other high-flexibility positions to avoid queue-driven roster distortion.
5. Include a scarce onesie position only when it creates a real tier edge and remains construction-safe.
6. Rebuild after every pick, trade, pause, undo, manual selection, or state refresh.

Never publish a static fallback slice as a verified live queue. If live availability is missing, say the queue is withheld.

## Extreme all-superflex and position-light formats

Do not import conventional one-QB or ordinary superflex roster geometry into leagues where most or all starting cells accept quarterbacks.

1. Read the exact live `roster_positions` array before setting positional caps. If every starting cell is `SUPER_FLEX`, each drafted quarterback may be a real starter rather than bench insurance.
2. Compare candidates by **marginal starting-lineup value under the league's actual scoring**, then apply scarcity, injury stability, and opportunity cost. Do not force RB/WR merely to make the roster look conventional.
3. In reduced passing-TD formats, distinguish pocket production from rushing leverage. Low passing-TD value suppresses some quarterbacks without erasing the edge of high-volume or rushing quarterbacks.
4. Do not impose an arbitrary QB cap. Select another quarterback when its realistic starter value and tier scarcity beat the best legal RB/WR/TE alternative and enough remaining capital exists to complete a competitive lineup.
5. Conversely, do not draft quarterbacks from a raw projection alone when the projection depends on an unstable starting role, stale team assignment, or implausible assumptions. Prefer secure roles and record uncertainty.
6. Track **fillable starter cells**, not familiar position counts. After every pick, confirm that remaining selections can still create a strong legal lineup plus usable depth.
7. Explain the strategy in format-native language: how many quarterbacks can start, why their scoring edge survives, what tier is disappearing, and the explicit condition for continuing or pivoting. Avoid saying “we are done at three” unless the value model actually says so.

Extreme all-flex drafting is value-first: keep adding quarterbacks whenever the live, role-reliable comparison supports it; never announce or enforce a preset QB cap merely for conventional balance.

## Correlated assets and asymmetric keepers

Treat roster assets by their joint outcome distribution, not only by position counts or independent player scores.

- **Same-backfield pairs:** two players from one NFL backfield may resolve into one lead plus one handcuff. They occupy two fantasy roster spots but must not be counted as two independent weekly RB/FLEX outcomes.
- **Selection test:** draft the correlated partner only when its standalone value plus deliberate backfield-insurance value materially beats the best independent RB/WR alternative. Existing ownership is not, by itself, a reason to complete the pair.
- **Construction response:** when a lead/handcuff pair is selected, preserve enough independent RB/WR paths—often by carrying another RB—rather than allowing nominal position counts to hide concentrated exposure.
- **Uncertain roles:** state both branches explicitly (A leads/B handcuffs, or B leads/A handcuffs). Do not silently freeze a depth-chart assumption when the value proposition is the ability to own either outcome.
- **Asymmetric keepers:** a cheap keeper can have legitimate starter ceiling and a low floor. Such a keeper removes the obligation to force the position; it does not automatically close the position. Permit a second player only on a material, construction-safe value fall, and treat future trade value as optional upside rather than the primary drafting rationale.
- **Study validity:** if a completed simulation treated correlated teammates as independent or treated a volatile keeper as closing a position, preserve its pick ledger but mark those strategic conclusions superseded. A choice-point replay is diagnostic; only fresh mocks under the corrected model are new readiness evidence.

Put league/player-specific pairings and thresholds in the league reference, not in this class-level section.

## Long human-paced drafts and token discipline

Treat wall-clock duration and model usage as separate concerns. A 60–90 minute draft does not require a 60–90 minute LLM turn.

- Keep the messaging gateway/session available for the full draft, but run the model only on meaningful state changes and owned picks. Idle waiting should consume no model tokens.
- Poll the official draft endpoint with a deterministic watcher or lightweight script; wake the reasoning model only when the ledger changes, ownership changes, or the user is approaching/on the clock. Do not spend an LLM call on every poll.
- Start a fresh dedicated draft session shortly before preflight when the current conversation contains unrelated research, coding, or tool logs. Durable league doctrine and local artifacts survive the reset; carrying a giant unrelated transcript is usually a larger usage cost than the choice between adjacent model tiers.
- Prefer the strongest reliable model for the relatively small number of high-stakes decision cards. Downgrade for quota conservation only when the user explicitly prefers the trade-off; do not downgrade merely because humans draft slowly.
- Be precise about “always on”: the gateway and deterministic watcher can remain active, while the model itself is event-driven rather than continuously thinking. State the dependency on host, gateway, network, and official API health.
- Before the live window, verify the watcher can detect ledger changes, identify the current owner, and survive the full expected duration. If monitoring is unavailable, require the user to supply updates rather than implying autonomous coverage.

When the operator says to start or “just do it,” keep setup narration to one compact acknowledgement at most; execute the preflight and return the verified result or exact blocker.

## Continuous live-attendance mode

When the user explicitly expects the agent to watch and execute the draft live, do not treat a detached watcher event as equivalent attendance unless that exact event-to-agent delivery path has passed a timed end-to-end rehearsal. Detecting a ledger change is not enough; the agent must receive it with enough clock remaining to decide, submit, and verify.

1. Complete the bounded initiation first and emit one visible `LIVE WATCH ACTIVE` receipt. Do not bury the acknowledgement behind setup narration or a long initialization workflow.
2. Keep the active agent turn attached with deterministic, cache-busted API polling that returns directly from the tool call at a milestone or two picks before the user's turn. The wait loop performs no model calls while state is unchanged and must remain interruptible by user steering.
3. Use bounded milestones rather than one opaque draft-length wait. On each return, report only the current pick and next owned pick, then resume immediately.
4. At two picks away, recompute the legal candidate set. At the owned pick, re-fetch availability, submit the exact approved player, verify exact ID in the expected cell, and immediately resume the next bounded watch.
5. Keep platform auto-pick **OFF** unless the user explicitly authorizes it. Never silently enable auto-pick to compensate for late watcher delivery; that changes the requested operating model.
6. Lowering the reasoning model tier does not repair gateway wake latency. Separate model-cost decisions from notification-delivery reliability.
7. If active attendance cannot be maintained and the detached path has not passed the latency rehearsal, say monitoring cannot be guaranteed and require human submission rather than claiming coverage.

This is a live-operation mode, not an initiation default. Do not enter an idle wait before the bounded preflight has completed and the user has asked for continuous attendance.

## On-the-clock loop

A resumed draft is a new decision boundary. When the user says the draft is back, asks to continue, or authorizes a pick after any interruption, discard the prior on-clock card and fetch official state again. The previously recommended player may already occupy an earlier user cell, and the user may now own a different pick. Never submit from the prior card until the current pick, current owner, complete ledger, current roster, and candidate availability have all been revalidated.

For every selection:

1. Fetch the live pick ledger and ownership.
2. Confirm current pick, owner on the clock, and the user's next actual selection.
3. Mark the newly drafted exact ID unavailable.
4. Update all rosters and positional-run context.
5. Recompute tier breaks, wait cost, and likely survival to the next owned pick.
6. Apply roster guardrails and phase-specific scoring.
7. Generate one recommendation and ranked pivots.
8. Re-fetch state immediately before any external executor acts.
9. Verify the recorded selection afterward by exact ID.

Any commissioner undo, pick trade, or ownership change invalidates the prior recommendation.

### Pick-scoped authorization and near-turn pairs

A request to “draft a player” authorizes exactly one selection. If the user owns another pick moments later, stop after verifying the first pick and require a fresh request unless continuous attendance or multi-pick auto-submit was explicitly authorized for that draft. Never stretch urgency into broader mutation authority.

When owned picks are separated by only a few opponent selections, optimize the decision as a pair without pre-authorizing the second mutation: draft the candidate least likely to survive now, retain likely survivors as conditional next-turn targets, then discard that plan and rebuild from official state when the next owned cell arrives. Use actual scoring and fillable starter value—not conventional position balance—and never call the conditional target a verified live queue before the intervening ledger is known. See `references/near-turn-paired-pick-optimization.md`.

## Detached watcher mode

For a human-paced draft, do not keep an LLM inference loop running between picks. Arm a cheap deterministic watcher instead:

1. Complete the full live-state preflight first, including exact keeper cells and the authoritative set of owned live pick numbers.
2. Poll cache-busted official draft and pick-ledger endpoints from an ordinary background process.
3. Treat the current pick as the smallest unfilled overall pick only after preloaded keepers and ownership have been reconciled. Do not infer it from elapsed time.
4. Emit one run-correlated `ON_CLOCK` event and exit only when that exact current pick is owned by the user. Emit `STATE_MISMATCH` after bounded API failures or an unexpected status.
5. Let the event wake the agent session. The agent must immediately re-fetch live state and regenerate its decision packet before recommending or clicking.
6. Treat execution mode as draft-scoped authorization. A generic `ON_CLOCK` event is recommendation-only. When the user explicitly authorizes automatic submission for that exact draft, encode the mode in the watcher event label (for example, `<LEAGUE>_AUTO_SUBMIT_ON_CLOCK`) so a fresh wake session does not lose the authorization boundary. The label never replaces the mandatory current-owner, exact-pick, availability, browser-identity, and exact-ID gates.
7. After submission, verify the exact player ID in both the expected draft cell and the cache-busted official ledger, then arm a fresh watcher for the next owned pick. Never omit an unresolved current owned pick merely to make a future-pick watcher stay quiet. If a next-turn process must be prepared before the current cell is filled, invoke the watcher with `--resume-after-pick N --expected-player-id ID`; it must wait for and verify that exact recorded selection before monitoring later owned picks.
8. A watcher is a read-only detector and wake-up mechanism, not a draft executor. Do not imply it will submit a player. Selection requires a separately authorized and rehearsed executor; absent that authorization, issue the decision card and wait for human submission.
9. On pause, undo, trade, or commissioner mutation, invalidate the event and rerun preflight.

This watcher consumes no model tokens while state is unchanged. Do not replace it with recurring LLM polling. Before a counted rehearsal, prove the search selector, enabled draft control, exact-ID cell read-back, raw clock parser, and logging path outside the clock. A timed-out or auto-picked owned cell invalidates the attempt even if the auto-picked player was an acceptable alternative.

A reference watcher implementation is available at `scripts/sleeper_turn_watcher.py`.

## Decision-card discipline

When the user supplies an exact on-clock format, follow it literally and include no preamble or postscript. A good card contains:

- Pick coordinate and live pick number.
- State verification marker.
- Recommended player with position, team, and exact ID.
- Ranked alternatives.
- Relevant blocked or inferior options.
- Roster impact.
- Why-now explanation covering tier, usage, ceiling, value, and survival.
- Confidence.
- Updated safe queue.

If the recommendation is unclear, name the missing information and provide only the safest eligible fallback. Do not bluff.

## Execution modes

- **Show me** — recommendation only.
- **Ask me** — recommendation plus an explicit approval gate before any click. One request authorizes one pick.
- **Full auto** — earned after clean counted rehearsals for that exact draft. Encode the authorization in the watcher event label. Exact-ID verify still applies.

Sleeper's public API is read only. Writes are a browser click plus exact-ID verify, or the human on a phone.

## In-season waiver and trade shadow reviews

Use a two-stage process: a deterministic screen creates candidates; an evidence and roster-construction review decides whether any candidate deserves an approval card. Never equate “highest available score” or a barely positive trade delta with an actionable move.

1. Refresh the public official league state, validate identity/freshness/checksum, and compare it with the previous normalized snapshot before evaluating moves.
2. Separate waiver-status players from free agents. If a public endpoint cannot establish an exact waiver deadline, state that limitation and do not manufacture a claim deadline.
3. Treat a frozen board as shortlist evidence, not current role truth. Refresh material role, injury, and depth-chart evidence before promoting a mutable recommendation.
4. Evaluate the named drop and roster geometry, not only global player score. Count usable RB/WR depth, onesie redundancy, bye exposure, internal replacements, and correlated assets. A small board upgrade that creates TE3/QB3 in a one-QB/one-TE league while discarding scarce RB/WR depth is normally a HOLD.
5. When current evidence reverses or materially weakens an automatically generated card, mark the reviewed recommendation HOLD/superseded; do not ask the user to reject a move the review itself no longer supports. The old card must remain unapproved and must never execute.
6. Use exhaustive exact-ID trade screening only as candidate generation. For every surviving package require: exact owners and player IDs, legal post-trade rosters, positive two-sided starter deltas, materiality beyond model uncertainty, depth and concentration effects, current role/health evidence, bye/playoff fit, keeper economics, counterpart need, market plausibility, an exact opening offer, and an exact walk-away price.
7. Do not promote tiny mathematical gains. If the modeled edge is smaller than the uncertainty introduced by stale projections, injury, role ambiguity, or depth loss, issue `NO TRADE` even if a permissive helper labels the package plausible.
8. Scope trade verdicts to the structures actually searched. A bilateral one-for-one scan may conclude `NO QUALIFYING 1-FOR-1 TRADE`; it must not claim that no trade exists across multi-player or multi-team structures. Before evaluating multi-team deals, verify the league and platform support the proposed participant count rather than assuming it is unlimited. Model the full deal atomically, require exact incoming/outgoing assets and legal post-trade rosters for every participant, and require every team to clear its own walk-away threshold. Never present disconnected bilateral legs as safe when one leg can fail independently.
9. Keep analysis, approval, and execution separate. A shadow review may run automatically; every league mutation still requires the user’s exact approval; a disarmed system must remain unable to submit even an approved card.
10. Close with machine-verifiable receipts: snapshot identifier, candidates evaluated, exact search-space scope, cards created/approved, validation result, execution flag, and mutation count. Preserve a concise report under an ignored output path for hindsight replay.

For a worked waiver/trade reconciliation and the reusable rejection rules, read `references/in-season-waiver-trade-shadow-review.md`.

## Direct-execution mode

When the user explicitly asks the agent to create, play, or complete a mock, the agent is the authorized executor rather than a reviewer. Keep the reviewer and executor roles distinct, but do not withhold clicks merely because the default workflow is reviewer-only.

Before creating the mock, classify the objective:

- **Real-draft rehearsal:** reproduce the league's keeper cells, roster rules, scoring, final slot/order, and approved doctrine. Use exact platform IDs and enforce the normal preflight and guardrails.
- **Entertainment / exploratory mock:** it may use a fresh slot or alternate construction, but label it as non-rehearsal. Do not treat its roster or result as readiness evidence for the real draft.

Execution loop:

1. Verify league identity, format, scoring, roster size, and whether keepers are embedded in the mock.
2. Claim only the intended slot and verify the user's team label appears there.
3. Start only after the user has authorized playing the mock; accept the irreversible-start confirmation only for that mock.
4. Detect the user's turn from live draft state, not from elapsed time or highlighted styling alone.
5. Re-read available players and roster construction on every turn.
6. Submit one player, then verify the exact player appears in the user's pick ledger before continuing.
7. Poll until the next verified user turn; never duplicate a click after an unverified response.
8. At completion, verify all rounds are filled, report the roster and draft ID/URL, distinguish mock effects from real-roster effects, and close tabs opened for the task.

For Sleeper's browser UI controls, exact snake-cell formulas, cache-safe API verification, custom scroll containers, and React-search quirks, read `references/sleeper-ui-execution.md`.

## Rehearsal acceptance gates

A plan-driven mock tests operational discipline, not whether the resulting roster looks plausible. Before starting the clock:

- Reconcile every keeper to its exact owner, platform ID, overall pick, and displayed round coordinate. Remember that a snake-draft seat number and the displayed within-round pick differ in even rounds.
- Prove the search, selection, exact-ID read-back, timer parser, and logging path in pre-draft or non-scoring state. Never debug interaction mechanics during a counted rehearsal.
- Prepare a live-safe queue with ranked pivots so a missing primary row never becomes on-clock research.
- Persist the raw clock text, recommendation, alternatives, roster state, rationale inputs, exact selected ID, and verification result for every owned pick.

Treat the attempt as invalid if any keeper is mapped to the wrong owner/cell, an owned pick times out, the selected ID differs, the executor improvises outside the approved board, telemetry loses the clock/state, or the live state becomes inconsistent. Do not continue an invalid attempt and later rationalize the roster. Start a fresh mock after correcting and testing the cause. Only one clean, uninterrupted, fully verified run can support a readiness verdict.

## Multi-slot sensitivity studies

When asked to simulate every draft position:

1. Declare how the user's roster moves between slots. A controlled default swaps the user with the base-order roster occupying each tested slot while holding the other slots fixed.
2. Move **every team's keeper cells** through that scenario mapping; never move only the user's keepers.
3. Run one fresh, independently verified draft per slot and persist each result immediately so partial progress survives interruption.
4. Verify official completion, unique player IDs equal to `team_count × roster_size`, user-owned cells, all keeper cells, safety gates, clocks, and construction in every scenario.
5. Aggregate first-round bands, opening structures, QB timing, RB/WR construction, player exposure, and decision times.
6. Label the result correctly: one CPU mock per slot measures **slot sensitivity**, not survival probabilities and not every opponent-order permutation. Repeated exposure under one CPU policy is a recurring branch, not a must-draft instruction.
7. Keep roster construction as approved ranges until remaining seats force a minimum; do not convert a preferred build into a rigid quota too early.
8. Time QB and other onesies from tier loss, wait cost, and likely survival to the next owned pick—not from a hard round trigger.

## League-wide post-draft analysis

Use this workflow when the request is to grade every team after a completed draft. A league power ranking, a draft-process grade, and a roster-construction grade are different products; compute them separately before reconciling them.

### Deterministic reconstruction

1. Fetch the official completed pick ledger, draft metadata, league rosters, and user/team identities once with cache-busting.
2. Resolve draft slot, roster ID, displayed team name, user name, and actual pick ownership. Traded picks—not ordinary snake spacing—determine which manager made each live selection.
3. Label every cell as official keeper or live selection by exact platform ID. Treat every keeper as unavailable from draft start, even when its populated cell is numerically later than the historical pick being reconstructed.
4. Join the completed ledger to the frozen player board, position tiers, rookie/keeper board, manual gates, and market timing. Preserve stale-source disagreements instead of silently coercing them.
5. Validate before grading: `team_count × roster_size` ledger cells, exact roster size for every team, unique player IDs, every pick assigned once, expected keeper count, and every roster/player represented in the report.

### Score roster power and process separately

For every team, calculate and review at least:

- Optimized legal starting lineup under the actual QB/RB/WR/TE/FLEX rules.
- Top RB/WR core sized to the league's weekly RB/WR/FLEX demand.
- RB/WR depth after the starting core.
- Best usable QB and TE, not the sum of all rostered onesies.
- Extra QB/TE opportunity cost in a short bench.
- Current projection, frozen-board quality, tiers, confidence, health/role gates, and keeper surplus.
- Position counts, correlated backfields or passing-game outcomes, and number of independent weekly paths.
- Live acquisition value relative to the legal pool at that exact cell—not only global preseason rank or raw market ADP.

Do not use total-roster projection as the primary ranking. It over-rewards QB2/TE2/TE3 points that cannot all enter a one-QB/one-TE lineup. Likewise, do not let clean position counts hide low-quality or contingent players.

Issue separate grades for:

1. **Final roster power** — likely weekly lineup, ceiling, resilience, and championship outlook.
2. **Live player acquisition** — value and fit of the actual non-keeper selections.
3. **Construction** — allocation, independent RB/WR depth, onesie opportunity cost, and correlation.
4. **Keeper economics** — current surplus and future optionality at the charged cells.
5. **Execution**, when the agent operated the draft — intended submission, clock result, and exact-ID verification.

A team can rank first in roster power with a poor construction grade because elite keepers or extra early capital overwhelm bench waste. Another team can have textbook construction but low roster power because the selected players lack quality. Explain that distinction explicitly.

### Sensitivity and independent review

Run multiple ranking profiles instead of pretending one score is truth:

- **Projection-heavy:** optimized starters and top RB/WR core.
- **Board-quality-heavy:** frozen final scores, tiers, and at-the-time acquisition value.
- **Depth-heavy:** independent RB/WR recovery paths and injury resilience.

Report rank bands and tiers when adjacent teams change order across profiles. The tier assignment is often more stable than the exact ordinal rank.

For a 12-team league, split independent review into three four-team batches after the deterministic pass. Give reviewers the official reconstruction and league doctrine, require candid grades and a local batch order, and tell them not to assume the executor's decisions were correct. Reconcile findings afterward:

- Preserve substantive disagreement rather than choosing the friendliest review.
- Change grades when the reviewer exposes allocation or timing errors.
- Do not change the power order automatically when only a process grade changes.
- Keep an auto-pick or timeout as an execution failure even when the resulting player is good.
- Treat a board `MANUAL` label as a health/role risk signal in an opponent audit, not automatic proof of a bad pick unless the gate is known to have failed.

### Required report shape

Give every team the same treatment:

- Team identity, slot, and exact QB/RB/WR/TE counts.
- Keepers separated from live selections.
- Full roster and optimized lineup.
- Strongest decisions, clearest reaches, correlations, strengths, weaknesses, and key risks.
- Draft, construction, and keeper grades.
- Championship/playoff/underdog outlook.

Lead with a direct favorite/contender verdict, then power order, tiers, objective comparison, and the team-by-team analyses. End with sensitivity, independent-review reconciliation, and the user's competitive position when relevant.

Before delivery, assert the official team, pick, keeper, and per-roster counts and verify that every team and player appears in the report. If exporting a concise PDF, render and visually inspect every page; do not accept clipping, unreadably dense tables, or a nearly empty trailing methodology page.

## End-of-draft audit

Record:

- Each recommendation, actual choice, exact ID, raw clock text, and decision time.
- Availability, stale-state, safety, doctrine, telemetry, or execution violations.
- Roster checkpoint compliance.
- Queue validity at each user turn.
- Raw-board rank, automatic/queue-legal rank, and roster-fit rank at each choice; never call a redundant or gated raw leader the “best legal alternative.”
- Model errors versus state errors versus survival-timing errors.
- Corrected pre-submission near-misses separately from final-pick mistakes.
- Three concrete changes before the next mock.
- A direct readiness verdict.

Grade three dimensions separately:

1. **Player outcome** — was the recorded player a strong choice from the at-the-time legal set?
2. **Decision process** — did the recommendation respect doctrine, roster fit, timing, correlations, and the approved board?
3. **Execution** — did the intended exact ID reach the correct cell on time and verify cleanly?

A timeout or auto-pick is an execution failure even if the platform lands on a good player; never retroactively present that result as intentional. A candidate searched or loaded but replaced before submission is a process near-miss, not a final-pick mistake, but preserve it because it exposes selector drift. Do not use actual later survival as proof that waiting was obviously correct; judge the wait from the board, survival model, intervening needs, and next owned live cell as they stood then.

When reconstructing historical choice sets, prevent hindsight and keeper leakage:

- Treat every official `is_keeper` exact ID as unavailable from draft start, even when its occupied cell is later than the pick being reconstructed or the static board still says `AVAILABLE`.
- Remove non-keeper players only after their actual earlier live selection; do not leak future live picks into a historical availability snapshot.
- Reconcile by exact platform ID rather than display name, and report any stale board/keeper disagreement instead of silently trusting either source.
- Distinguish hard eligibility or rookie earliest-round floors from soft veteran market/queue timing. Log any soft-timing override with the material tier edge, roster safety, and why waiting for a later owned pick was impossible or inferior.

A mock-ready verdict is not real-draft authorization when the official order, ownership, or other live gates remain provisional.

## Post-operation truth and roadmap reconciliation

After a real draft or counted rehearsal, update status documents from evidence rather than carrying the pre-draft roadmap forward unchanged. Audit each subsystem on five separate axes:

1. **Documented** — architecture, rule, or schema is described.
2. **Present** — a runnable or machine-readable artifact exists in the canonical repository.
3. **Exercised** — the artifact or behavior ran in a real or mock workflow.
4. **Qualified** — it passed the required clean rehearsals and fault tests.
5. **Released** — it is committed to the canonical branch and available to every participating agent.

Never collapse these axes into one word such as `built`. In particular:

- A design document is not an implemented selector or guardian.
- A one-off script or skill-side prototype is not a canonical repository runtime.
- Agent-driven browser clicks plus API verification are real execution, but they are not automatically a guardian-protected autonomous system.
- Several successful recovery picks do not erase an earlier timeout, auto-pick, stale-state action, or monitoring miss.
- A strong final roster validates player evaluation and construction more than execution readiness.
- Uncommitted reports and runtime artifacts are evidence, but they are not yet the published contract.

Reconcile roadmap claims in this order:

1. Fetch the official completed ledger and final platform state for external facts: order, ownership, keepers, picks, and result.
2. Inspect canonical repository HEAD, remote HEAD, worktree status, and actual artifact presence for implementation/release claims.
3. Compute row counts, missing IDs, enums, and set differences directly from source files; do not repeat a QA report when the raw artifacts disagree.
4. Use the preserved execution record to classify intended selection, actual recorded selection, operator, timing failure, watcher delivery, and verification path.
5. Separate player outcome, decision process, execution, monitoring, and autonomous-readiness verdicts.

Once the draft is complete, retire obsolete “before draft day” instructions from the active milestone list. The corrected sequence becomes:

1. Freeze the official evidence package.
2. Reconcile stale order, keeper, ownership, and identity artifacts.
3. Correct QA and release the post-draft audit.
4. Implement missing canonical selector/guardian/ledger/executor components.
5. Replay the observed failures deterministically.
6. Progress through Shadow, Approval, Auto, and fault-injected qualification.
7. Require new explicit human authorization before the next live Auto mode.

For a single-Markdown status request, prefer one evidence-backed document with: an honest headline; proven run facts; a layer-by-layer status table; explicit data/QA corrections; designed-versus-implemented architecture; missing runnable artifacts; a post-operation roadmap; acceptance gates; and an evidence basis. Do not average a good football outcome and unsafe execution into a vague overall grade.

## Pitfalls

- Do not assume a named local file is absent until the canonical remote has been checked.
- Do not infer a mock draft ID from the league's scheduled real draft.
- Do not treat `slot_to_roster_id` as a finalized draft order when `draft_order` is null or the doctrine labels it provisional.
- Do not map pick spacing with a normal snake formula when traded picks or keeper cells exist.
- Do not convert a static fallback ranking into a live queue without checking availability.
- Do not clear manual players because a secondary review file omits them.
- Do not click, queue, or submit when assigned only the reviewer role.
- Treat `stop`, `pause`, `never mind`, or notice that another agent is already updating as an immediate mutation barrier. Do not finish the current patch batch or make cleanup edits; stop and wait for explicit new authorization. When work resumes, re-read durable artifacts before editing so concurrent changes are not overwritten.

## Reference implementations

- For Sleeper browser controls, keeper-coordinate mapping, exact-ID read-back, API freshness, counted-rehearsal telemetry, complete-board capture, and privacy-safe manager redaction, read `references/sleeper-ui-execution.md`.
- For near-turn paired picks, read `references/near-turn-paired-pick-optimization.md`.
- For in-season waiver/trade shadow review, read `references/in-season-waiver-trade-shadow-review.md`.
- Before starting an untraded Sleeper snake rehearsal, run `scripts/verify_sleeper_keepers.py` against the exact keeper manifest; with `--draft-id` it cache-busts and verifies the official pick ledger.
