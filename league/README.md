# League data

Keep real Sleeper ids, owner ids, and live dumps **out of git**.

1. Copy `league/examples/` to a private directory outside this clone, or to
   `league/private/` (gitignored).
2. Replace every `fake-*` id, Harbor Cats label, and Cole Voss placeholder.
3. Export `LEAGUE_DATA_DIR` to that private directory.

`examples/` is a public toy board so the scripts and tests have a shape to
follow. It is not a ranking set.
