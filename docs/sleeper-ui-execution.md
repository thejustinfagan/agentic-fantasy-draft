# Sleeper browser UI draft execution

Use this reference only when the agent is explicitly authorized to execute a
Sleeper live pick or create/play a Sleeper mock. Prefer the official live draft
API for exact IDs, ownership, and availability; use the UI techniques below for
interaction and read-back.

Sleeper's public API is **read only**. A click in the already-authenticated
browser is a write. Exact-ID verify after the click is mandatory.

## Preflight

1. Open the named league and verify league ID, team count, scoring, roster size, rounds, timer, and keeper treatment.
2. Classify the mock as a real-draft rehearsal or an exploratory game. A rehearsal must include keeper cells and approved doctrine; an exploratory mock must not be reported as readiness evidence.
3. Record every browser tab opened so it can be closed afterward.

## Sleeper surface scoping

Sleeper exposes different objects on different surfaces. Scope every visibility claim to the source actually inspected:

- The web **Mock Drafts / Draftboards** page shows mock boards associated with that account and tab state.
- The mobile **league list** can show multiple league-bound draft rooms with `PRE-DRAFT`, `DRAFTING`, and “N picks away” status even when those names do not appear in web Draftboards.
- A league name, league-bound draft room, and standalone mock-board title are not interchangeable identities.

If the user supplies a screenshot, direct draft URL, draft ID, league ID, or named app surface, inspect that direct source first. Never conclude that a named room “does not exist” merely because it is absent from web Draftboards. Report the bounded fact instead—for example, “not visible in this account’s web Mock Drafts list”—and identify which other Sleeper surface remains unchecked. When reading a screenshot, transcribe every visible room name and status before interpreting which entries are open.

## Opening and claiming

- The league pre-draft page may render `MOCK DRAFTS` as a `.draft-button` inside a custom `perfect-scrollbar` container. `window.scrollTo()` does not move this panel. Dispatch a wheel event over the panel, then recompute the target's visible rectangle before clicking.
- Claim controls may be duplicated in the DOM. Associate each visible `.claim-text` with its parent team label and click only a node whose rectangle is inside the viewport.
- After claiming, verify the user's team name/avatar replaced the claim control at the intended slot.
- `START DRAFT` opens a JavaScript confirmation. Accept it only when the user has authorized starting that mock. After handling the dialog, verify picks begin populating.

## Keeper cells and snake coordinates

For an untraded snake draft with `T` teams, seat `s`, and round `r`:

```text
within_round = s                    if r is odd
within_round = T + 1 - s            if r is even
overall_pick = (r - 1) * T + within_round
cell_label = r.within_round
```

The displayed cell suffix is the pick's position within that round, not always the team's seat. Example: seat 3 in a 12-team Round 14 owns `14.10`, overall pick 166; `14.3` belongs to seat 10. Use the authoritative pick-ownership map instead of this formula when picks are traded.

Before starting a rehearsal, verify every keeper as a tuple of `(owner/seat, round, displayed cell, overall pick, exact player ID)`. Sleeper mock picks manually preloaded before the start may return `is_keeper: null`; prove keeper state from the exact cell, slot/owner, round, pick number, and player ID rather than relying on that flag.

## Reliable on-clock loop

1. Refresh live draft state and confirm the user's current owned pick. Treat every resume after an interruption as a new decision boundary: an earlier recommendation may already have been selected in a prior user cell.
2. DOM fallback: isolate the user's team-column text and treat an empty pick containing `MM:SS` as on-clock only after confirming the draft ledger agrees.
3. Read the available-player list and current roster requirements fresh.
4. Select the exact player control. In Sleeper's rankings table, clicking the **player name** opens the player-profile modal and does not draft or queue the player. The left circular plus / `.draft-button-wrapper .draft-button` is the immediate draft control; the separate blue document-style icon adds the player to the queue.
5. If using the queue path, first require the Queue panel to contain exactly one matching full name, position, and NFL team. The far-right circular plus beneath the Queue panel's `DRAFT` header submits that queued player. Click it once. The queue becoming empty is only a UI transition signal, not final proof.
6. Verify the chosen exact player appears in the user's team ledger at the expected pick before waiting again. A drafted cell normally exposes an avatar with `aria-label="nfl Player <ID>"`, which provides immediate exact-ID confirmation when the public API is lagging.
7. Reconcile the same exact player ID, pick number, owner, roster, and monotonic ledger through a cache-busted official API read. Never retry after either the board cell or official ledger confirms success.
8. Poll every ~2 seconds until the next verified user turn. Do not infer success from a click response alone and do not duplicate a pick.

When native background input cannot safely address the intended browser window, do not keep replaying coordinates or shortcuts against an ambiguous window. If an already-controlled browser tab is authenticated to the intended Sleeper account, record that tab's original URL, navigate that tab to the exact verified draft URL, perform the normal single-click/ledger verification flow, and restore the original URL afterward. Never assume account sharing or authentication—prove the named league, the user's team identity, and on-clock state in the rendered page before mutation.

Sleeper's public draft endpoints may return a stale pre-draft response after the browser board has completed. For authoritative post-click or post-draft API verification, add a unique cache-busting query parameter and `Cache-Control: no-cache`, then reconcile the returned exact IDs against the DOM ledger. Record both sources when they disagree temporarily; never reinterpret a stale API response as an undo.

Example DOM polling skeleton. Derive the team boundary from the current DOM instead of hard-coding neighbor labels:

```python
import re, time
for _ in range(40):
    time.sleep(2)
    text = js("document.body.innerText") or ""
    team = re.search(r"Harbor Cats\\nHarbor Cats\\n(.*?)(?=\\nSalt Wren\\n)", text, re.S)
    if team and re.search(r"\\n\\d\\d:\\d\\d\\n", team.group(1)):
        break
```

## Exact identity and click verification

A filtered Sleeper rankings row may not expose the platform player ID even when the drafted board cell does. In that case:

1. Filter by the approved player's full name.
2. Before clicking, match full name, position, and NFL team to the exact-ID decision product.
3. Sleeper may expose duplicate exact-name text nodes: one hidden/auxiliary node with no draft controls and one visible rankings row. Resolve every matching accessibility/DOM node and retain only the node whose visible ancestor has class `player-rank-item2`, contains the expected full name/position/team, and contains exactly one visible `.draft-button`. A raw exact-name count of two is not itself a blocker; clicking without this ancestor filter is.
4. Click the visible left `.draft-button` for that validated row—not the queue control. When the control is unlabeled in the semantic tree, derive its fresh bounding rectangle from the validated row and click its center once.
5. Read the expected draft cell immediately afterward. It normally carries an avatar with `aria-label="nfl Player <exact_id>"`, but some players render only the abbreviated name/position/team and no avatar element. In that case, require the expected board cell to show the unique name/position/team tuple and use the cache-busted official ledger cell for the exact ID.
6. Verify the same exact ID, pick number, owner, and roster in the official pick ledger. If the first click is unverifiable, refresh the cell before any retry. **An exact official API cell plus the matching board name/position/team is success even when the avatar is absent; never retry a confirmed selection.**

### Post-click verifier exception safety

After the single authorized click, any verifier exception means the mutation is **unknown**, not failed. Before considering another click, fetch the cache-busted official ledger and inspect the exact expected cell. If that cell contains the intended player ID, owner, and roster, record success and rearm; never replay the click.

Keep browser `js(...)` read-backs JSON-serializable. Return primitives or plain objects—for example:

```javascript
!!document.querySelector('[aria-label="nfl Player <exact_id>"]')
```

Do not return a raw DOM element such as `document.querySelector(...)`; CDP `returnByValue` can fail while serializing the node after the draft mutation has already succeeded. A serialization failure must not be mistaken for a failed submission.

## API freshness and split-state checks

Sleeper's public draft endpoints may briefly serve a stale cached `pre_draft` object or only the manually preloaded picks while the browser board has advanced. When API and DOM disagree:

- Re-fetch the official endpoint with a unique query parameter and `Cache-Control: no-cache` / `Pragma: no-cache` headers.
- Compare `status`, `last_picked`, pick count, maximum pick number, and exact selected IDs.
- Record the discrepancy as a telemetry event; do not silently treat the stale response as current.
- Use exact DOM cell state for immediate post-click verification only in authorized direct-execution mode, then reconcile to the refreshed official ledger before declaring completion.

## Counted-rehearsal telemetry

Before starting the irreversible clock, test the timer parser and logger against the actual rendered cell format. Persist the raw active-cell text as well as parsed `MM:SS`; an `unknown` clock value makes the telemetry incomplete even if the pick landed quickly. A counted attempt must also log the recommendation, ranked pivots, roster state, rationale inputs, exact selected ID, and decision-to-verification time.

A pre-draft search can prove row identity and geometry while Sleeper still renders the draft control as disabled; it does **not** prove that the enabled on-clock click path works. Exercise the complete enabled-control → click → exact-cell-ID read-back path in a disposable, explicitly non-counted draft before starting a counted rehearsal. Do not debug selectors, helper syntax, or click verification under the counted clock. If an owned cell times out or auto-picks, invalidate the entire attempt even when the auto-picked player was an approved alternative.

Any wrong keeper cell, timeout, identity mismatch, off-board improvisation, or broken clock/state telemetry invalidates that attempt; correct and test the cause, then create a fresh mock.

## Dynamic row geometry

Sleeper's filtered player row can move when `scrollIntoView()`, viewport resizing, a panel expansion, or responsive layout changes the table height. Do not reuse an absolute click coordinate from a prior player or prior viewport.

1. Set the controlled search input to the exact approved full name and wait for the filtered row.
2. Confirm full name, position, NFL team, and projected pick in the current rendered row.
3. Derive the immediate draft control from the current row's DOM relationship and fresh bounding rectangle; if that is unavailable, capture a fresh screenshot and click the visible left-plus control for that row.
4. After the click, require a roster-count change or the exact expected board cell before considering the action delivered.
5. If the state did not change, capture fresh geometry before one retry. Never blindly replay the same pixel coordinate, because a viewport transition may have moved the control.
6. Reconcile the result to the cache-busted official API by exact player ID.

A filtered UI rank or ADP can serve as a last-second sanity signal, but it does not replace the approved local board. If it reveals a very large discrepancy and the pick was being forced only by a roster quota, recompute whether the minimum is truly forced by the number of seats remaining before clicking.

## React search control

The player search is typically:

```css
input[placeholder^="Find player"]
```

Typing a unique player name is useful when the virtualized row is off-screen. Passing an empty string to a typing helper may not clear a controlled React input. A validated clear pattern is:

```javascript
(() => {
  const input = document.querySelector('input[placeholder^="Find player"]');
  const setter = Object.getOwnPropertyDescriptor(
    HTMLInputElement.prototype, 'value'
  ).set;
  setter.call(input, '');
  input.dispatchEvent(new Event('input', { bubbles: true }));
  return input.value;
})()
```

After clearing, verify the unfiltered rankings returned before choosing another player.

## Background-tab virtualization and exact CDP recovery

A pre-existing authenticated Chrome tab can remain semantically reachable while Sleeper's `ReactVirtualized__Grid` collapses to `height: 0px` because the page is backgrounded (`document.visibilityState === "hidden"`). Do not treat an empty ranking container as proof that no players are available, and do not manipulate an unrelated active tab.

When the authorized Chrome instance was already launched with a known remote-debugging port:

1. Enumerate `/json/list` and identify the Sleeper target by the exact draft URL. Require exactly one match.
2. Record the exact current personal/work tab target that must be restored; never guess from title alone.
3. Activate only the exact Sleeper target, call `Page.bringToFront`, enable focus emulation if required, and wait for `document.visibilityState === "visible"` plus a nonzero `.ReactVirtualized__Grid` height.
4. Filter with the approved full name and require exactly one `.player-rank-item2` containing the expected full name, position, and NFL team, with exactly one visible `.draft-button`.
5. Re-fetch the cache-busted official ledger immediately before the single click. Afterward, verify the exact official cell and matching board semantics; never retry after either source confirms success.
6. Disable focus emulation and reactivate the recorded prior tab in a `finally` path, whether execution passes, blocks, or throws.

This is a recovery path for a user-authorized, already-authenticated draft target—not permission to launch/copy profiles, inspect unrelated pages, or bypass draft-scoped authorization.

## Privacy-safe complete-board screenshots

When the user wants the entire completed draftboard as a shareable image, do not treat the ordinary viewport as the board. Sleeper can render all columns and rounds inside `.draft-board` while `.top-container` clips the lower rounds and `.bottom-container` covers them.

1. Inspect the direct draft URL and official APIs first. Use `/v1/draft/<draft_id>`, `/picks`, and `/v1/league/<league_id>/users` to verify the expected team count, round count, exact displayed manager identities, and completed ledger.
2. Inspect live geometry before changing anything. Compare `.draft-board`, `.column-container`, and `.top-container` bounding rectangles plus their `scrollWidth`, `scrollHeight`, `clientWidth`, and `clientHeight`. Derive capture dimensions from those values; do not hard-code dimensions from a prior league or viewport.
3. If a native capture shows a blank GPU-composited page while the browser semantic tree still exposes the board, and that Chrome instance was intentionally launched with a known remote-debugging port, attach to its existing page target through CDP. `Page.captureScreenshot` with `fromSurface: true` captures the rendered surface without opening or focusing another tab. Never relaunch or copy an authenticated profile merely for a screenshot.
4. Apply screenshot-only DOM changes with one temporary style element and temporary classes:
   - expand `.top-container` to the measured bottom of `.draft-board` and remove its clipping;
   - hide `.bottom-container` and the custom scrollbar rails;
   - size the page/root to the measured board extent;
   - capture only the league header plus the complete board.
5. Redact identities from DOM-backed selectors, not guessed pixels. Resolve manager display names from the league users API, preserve only the user's explicit allowlist, and black out every other `.header-text`, corresponding header `.avatar` background, and `.pick-traded` ownership label. Keep player names, NFL teams, positions, and pick coordinates readable—the privacy target is manager/team identity, not the roster data.
6. Sleeper may cap header text width and visually ellipsize an allowed name. Temporarily relax `max-width`, overflow, and text-overflow for allowlisted headers so the complete permitted name is legible.
7. Capture with a clip derived from the current board rectangle, then remove every injected class and style in a `finally`/cleanup path. Do not close or reload a pre-existing user tab merely to restore it.
8. Visually verify the delivered artifact: all team columns, every round, both explicitly allowed identities, no unredacted manager header or traded-pick label, readable player names, and no lower-panel overlay or clipping.

Black rectangles are preferable to blur for privacy because they do not preserve recoverable letter shapes. Redact duplicate sticky/non-sticky header nodes as well as the visible copy; Sleeper may render both at nearly identical coordinates.

## Completion and cleanup

- Verify every user round is filled and the board shows its completed state.
- Report the draft ID/URL, slot, roster, and that no real roster changed.
- If the mock was exploratory, say so explicitly.
- Close only tabs opened for the task. With CDP, list page targets first and close targets whose Sleeper URLs were created during the run; leave pre-existing personal tabs untouched.
