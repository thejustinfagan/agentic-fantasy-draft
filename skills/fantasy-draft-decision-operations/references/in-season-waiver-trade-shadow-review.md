# In-season waiver and trade shadow review

## Why this reference exists

A deterministic season engine can be structurally safe yet still promote bad
fantasy moves when its candidate generator substitutes a global board score for
roster construction or treats any positive trade delta as material. This
reference records the proven reconciliation pattern.

## Proven review sequence

1. Fetch public league and schedule state with a GET-only client.
2. Validate league/roster identity, freshness, source checksums, and normalized-state checksum.
3. Compare against the previous snapshot and report operational changes separately from retrieval metadata.
4. Generate waiver, free-agent, and exhaustive exact-ID trade candidates.
5. Review each candidate against current role/injury evidence and the full roster shape.
6. Promote only evidence-qualified moves to approval; emit HOLD/NO TRADE for the rest.
7. Validate all artifacts and assert execution remains disabled, every existing card remains unapproved, and mutation count is zero.

## Worked rejection (Harbor Cats / Cole Voss — FAKE)

A Week 1 shadow run found no qualifying waiver-status players but ranked a
free-agent tight end (Nico Vale) as the highest available add and a cheap
running-back keeper (Reed Calder) as the lowest frozen-board roster asset. A
score-only bridge therefore produced “add Vale, drop Calder.” Human-quality
reconciliation rejected it:

- Harbor Cats already carried two tight ends, so Vale would be TE3.
- Dropping Calder reduced scarce RB depth.
- Current free reporting supported Vale’s role but also listed Calder as a
  co-starting back with meaningful inside-the-20 work.
- The small frozen-board difference did not overcome role and construction
  uncertainty.

The correct output was HOLD with no promoted waiver/free-agent approval—not
“approve the top scored pair.”

The same run exhaustively evaluated thousands of one-for-one swaps. A handful
were nominally positive for both lineups, but Harbor Cats gains were well under
a projected point. The candidates either created QB3, reduced RB/WR depth,
carried injury/snap uncertainty, or provided negligible counterpart gain. All
were rejected as NO TRADE.

## Reusable rejection rules

Reject or hold when any applies:

- No exact public waiver deadline can be verified.
- Candidate availability, drop ownership, lock state, or exact identity is uncertain.
- The recommendation creates redundant QB3/TE3 value in an ordinary one-QB/one-TE format while sacrificing flexible depth.
- The drop has contingent role or scarce-position optionality not represented in the frozen score.
- Projection/board timestamps predate material current role or injury news.
- Trade gain is positive but smaller than reasonable projection uncertainty.
- Counterpart benefit is nominal, their need is not evidenced, or the offer depends on irrational acceptance.
- Keeper cost, playoff alignment, or injury risk is missing when it is central to the trade thesis.
- The opening offer and walk-away package are not exact-ID payloads.

## Output contract

A good shadow report states:

- snapshot checksum and timestamp;
- waiver-status count, free-agent candidates considered, and exact uncertainty;
- trade concepts evaluated and the surviving/rejected packages;
- exact names and platform IDs without exposing private credentials;
- direct verdict: ACT, HOLD, or NO TRADE;
- whether any approval card was promoted;
- execution-enabled flag and observed mutation count;
- the next evidence trigger for rerunning analysis.

Never leave a superseded automatically generated candidate looking actionable.
Explicitly label it HOLD/superseded, keep it unapproved, and regenerate the
packet before any future approval discussion.
