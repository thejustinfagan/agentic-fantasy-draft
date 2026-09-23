# Execution modes

Three modes. Full auto is earned, never assumed.

## Show me

Recommendation only. Grok Bot refreshes live state, builds a decision card, and
stops. The human submits on the phone or in the browser.

## Ask me

Same decision card, plus an explicit approval gate before any click. A request
to "draft a player" authorizes exactly one selection. Nearby owned picks are a
planning pair, not extra mutation authority.

## Full auto

Automatic submission for that exact draft after clean counted rehearsals. The
watcher event label must encode the authorization (for example
`HARBOR_CATS_AUTO_SUBMIT_ON_CLOCK`) so a fresh wake session does not lose the
boundary. The label never replaces current-owner, exact-pick, availability,
browser-identity, and exact-ID gates.

If any live-state gate fails, every mode collapses to:

`STATE MISMATCH — NO DRAFT AUTHORIZATION`

Platform auto-pick stays **OFF** unless the operator explicitly authorizes it.
Never silently enable auto-pick to compensate for late watcher delivery.
