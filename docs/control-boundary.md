# Control boundary

Sleeper's public API is **read only**. This template is not a Sleeper write
client.

## What may run automatically

- Cache-busted `GET` of public league, draft, pick, traded-pick, and roster endpoints
- Local artifact validation
- Watcher polling
- Decision cards
- In-season shadow reviews that remain `DISARMED` / `NOT_APPROVED`

## What may not

- Authenticated Sleeper writes
- Cookie, token, or profile capture
- Queue dumps that turn Sleeper auto-pick into an unsupervised executor
- Stretching “draft a player” into later owned cells
- Any click after `STATE MISMATCH — NO DRAFT AUTHORIZATION`

## Writes

Only two write paths exist:

1. **Browser click + exact-ID verify** in an already-authenticated session the
   operator authorized for that exact draft.
2. **Human phone** after the decision card.

A watcher is a detector. It does not submit a player.
