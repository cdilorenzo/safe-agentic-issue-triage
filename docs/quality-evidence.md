# Quality evidence and verification limits

## Evidence presently available

The repository includes **16 deterministic unit tests** plus a static n8n JSON validator. These have been run successfully with Node.js 22 in the authoring environment.

| Automated offline check | Status |
|---|---|
| TC1 normal documentation | PASS with mock model output |
| TC2 ambiguous issue | PASS with mock model output |
| TC3 security-sensitive issue | PASS with deliberately optimistic mock model |
| TC4 prompt injection | PASS with deliberately optimistic mock model |
| TC5 invalid URL | PASS without model |
| Arbitrary-host / SSRF-style URLs rejected | PASS |
| Malformed JSON fails closed | PASS |
| Missing `security_sensitive` Boolean fails closed | PASS |
| Extra JSON schema fields rejected | PASS |
| Optional approval never causes writes | PASS |
| Final audit omits raw issue body/transcript | PASS |
| Read-only risk tool identifies obvious sensitive signals | PASS |
| Assertions reject tampered outputs | PASS |
| GitHub PR-like payload rejected; empty issue accepted | PASS |
| Human rejection and timeout remain no-write decisions | PASS |
| AI tool name matches agent instruction and has correct model/tool edges | PASS |
| Workflow structure, connections, code syntax and secret-reference checks | PASS (static validation) |

The `tests/fixtures.json` cases are embedded in the generated workflow. n8n's `Assert Expectations` node evaluates the actual results at runtime. The offline tests run the **same JS source files** that are embedded into the workflow, so they validate real guardrail logic rather than a separate pseudocode implementation.

## Live verification and remaining limitations

- **Verified:** imported and executed successfully in n8n Cloud on 2026-11-18 (execution #9).
- **Verified:** Gemini 2.5 Flash-Lite completed the five-scenario live run.
- Agent actually invoking its read-only tool as instructed (inspect the n8n trace).
- **Verified:** 5/5 live scenario assertions passed. Authentic audit screenshots still need to be added.
- Optional authenticated Wait Form, approval, rejection and expiry scenarios in n8n.
- Live public GitHub API success/failure on this n8n instance.
- Long-term output consistency, accuracy, hallucination rate or operational latency/cost.

## Acceptance gate before using in a job application

1. Import the JSON into n8n; resolve any node-version incompatibilities and assign a model credential.
2. Execute all five fixtures, inspect **every** `test_pass` and failed case, and record model name and n8n version.
3. Confirm the agent actually calls `inspect_issue_risk` and cannot use mutating external tools.
4. Confirm the high-risk and prompt-injection cases never reach any side-effecting node.
5. Capture an authentic canvas screenshot plus at least one audit-results screenshot. Do **not** manufacture test evidence.
6. If demonstrating optional approval, configure Basic Auth and verify approve, reject and timeout outcomes on your own instance.
7. Inspect exported JSON and screenshots for credentials and personal/private content before publishing.

A failed live test is important evidence: adjust the workflow and document the result rather than changing expected assertions merely to make a pass.
