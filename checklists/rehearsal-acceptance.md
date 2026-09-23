# Rehearsal acceptance gates

A plan-driven mock tests operational discipline, not whether the resulting
roster looks plausible.

Before starting the clock:

- [ ] Reconcile every keeper to exact owner, platform ID, overall pick, and displayed round coordinate
- [ ] Remember that a snake-draft seat number and the displayed within-round pick differ in even rounds
- [ ] Prove search, selection, exact-ID read-back, timer parser, and logging in pre-draft or non-scoring state
- [ ] Prepare a live-safe queue with ranked pivots
- [ ] Persist raw clock text, recommendation, alternatives, roster, rationale, exact selected ID, and verification for every owned pick

Invalidate the attempt if any of these occur:

- [ ] A keeper is mapped to the wrong owner or cell
- [ ] An owned pick times out or auto-picks
- [ ] The selected ID differs
- [ ] The executor improvises outside the approved board
- [ ] Telemetry loses the clock or state
- [ ] Live state becomes inconsistent

Do not continue an invalid attempt and later rationalize the roster. Start a
fresh mock after correcting and testing the cause. Only one clean,
uninterrupted, fully verified run can support a readiness verdict. Full auto
is earned from that verdict, not from a strong final roster.
