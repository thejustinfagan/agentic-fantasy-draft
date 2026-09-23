# Mode checklist

- [ ] **Show me** — card only; human phone or human click
- [ ] **Ask me** — card plus explicit one-pick approval
- [ ] **Full auto** — earned; watcher label encodes draft-scoped auto-submit; exact-ID gates still apply

Always:

- [ ] Sleeper public API remains GET-only
- [ ] Platform auto-pick stays OFF unless the operator explicitly enables it
- [ ] Fail closed with `STATE MISMATCH — NO DRAFT AUTHORIZATION`
- [ ] Never treat a watcher event as a write
