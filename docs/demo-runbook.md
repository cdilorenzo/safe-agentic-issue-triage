# n8n demo runbook (10–15 minute presentation)

## Preconditions

- Import `workflows/safe-agentic-issue-triage.json` into a **private** n8n project.
- Select the Chat Model credential. Verify your account supports the model or select another supported model.
- Ensure `interactive_approval_enabled` is **false**.
- Keep the workflow inactive and do not expose a public trigger.

## Demo flow

1. **60 seconds — why:** Explain that issue text and model output are both untrusted; the model can propose but cannot authorize itself.
2. **1 minute — boundaries:** Show green/blue canvas notes, especially one true n8n `AI Triage Agent` connected to a read-only Code Tool, followed by independent Code/IF validation.
3. **3 minutes — run all fixtures:** Click **Test workflow**, open the `Final Audit Record` output and inspect fields per case. `TC5` should reject before any LLM call.
4. **2 minutes — security:** Show TC3, independent auth/token flags, HIGH risk and human review requirement; show TC4 prompt injection escalation.
5. **1 minute — ambiguity:** Show TC2 high uncertainty and reviewer clarification.
6. **1 minute — reproducibility:** Point out `npm run check`, `tests/fixtures.json`, and the generated JSON file under source control.
7. **30 seconds — limitations:** No real GitHub writes, code execution or production claim; optional approval records only a dry-run decision.

## Troubleshooting

- **Missing model credential:** open `OpenAI Chat Model` and select/create it. Do not paste credentials into JSON.
- **Unsupported model name:** choose one supported in your n8n account.
- **Invalid AI output:** inspect `Validate AI Output` → `validation_errors`. Strict schema is intentional. Re-run once; record failure if persistent.
- **Item-linking error:** inspect the paired items in `AI Triage Agent` and `Issue Context`. n8n versions can differ; do not claim that the workflow passed until these links are verified.
- **GitHub read fails:** public endpoint may be rate-limited; the workflow must fail closed. Demo fixtures do not require live GitHub.
- **Optional Wait Form inaccessible:** configure Basic Auth and ensure correct form URL from the actual execution. The default route avoids this node.
- **One failure prevents all other cases from reaching audit:** inspect the n8n execution graph; adjust node error handling and record the change before updating evidence.

## Real screenshots to add (not included)

- `assets/n8n-canvas.png` — a readable screenshot of the imported canvas.
- `assets/n8n-audit.png` — actual `Final Audit Record` output with `test_pass` results.
- Optional `assets/agent-tool-trace.png` — actual AI Agent trace showing the tool invocation.

Never commit a screenshot containing credentials, secrets, internal company names or real approval URLs.

Detailed German instructions: [SETUP-UND-TEST-DE.md](SETUP-UND-TEST-DE.md).
