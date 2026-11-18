# Contributing

This is an architecture-first personal reference implementation. Please open an issue describing the intended security or testing effect before proposing major changes.

- Edit the JS sources in `src/` and expected fixtures in `tests/fixtures.json`, not just the generated JSON.
- Run `npm run check` and include a reproducible failing test for bugs.
- Keep external writes, arbitrary URL fetching, credential access and production execution **out of scope** without a new reviewed security model.
- Do not weaken quality gates to make a model output pass.
- Document observed n8n runtime behavior separately from offline mock tests.
