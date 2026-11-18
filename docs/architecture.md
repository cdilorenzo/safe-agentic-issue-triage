# Architecture decisions and tradeoffs

## Purpose

Show how a bounded AI Agent can contribute engineering analysis without receiving authority to approve or execute changes. The important demonstration is **technical responsibility boundaries**, not a large number of connected services.

## Layers

1. **Deterministic intake**: manual trigger, synthetic issues, strict URL parser. Real GitHub input is allowed only through a fixed `api.github.com` endpoint, using GET. The issue URL is parsed into owner, repository and issue number rather than passed as a general HTTP URL. Input is bounded before the model.
2. **Agentic triage**: n8n AI Agent calls a custom read-only inspection tool and proposes a JSON analysis. The model has no secrets, memory, filesystem, shell, GitHub write tools or deployment tools. Model instructions do not guarantee compliance; the model's output is considered untrusted.
3. **Independent deterministic policy**: a strict output shape and type checker validates the entire proposed report. Security-sensitive keywords in the **original issue**, not just model suggestions, elevate risk. Explicit prompt-injection patterns elevate risk. High ambiguity triggers clarification.
4. **Review**: a Markdown proposal clearly states the dry-run nature. A high or medium risk case needs human review. An optional Wait form can record a human decision after Basic Auth configuration. Approving only updates an audit record.
5. **Assertions and evidence**: cases contain independent expected outcomes. Every path that completes in the editor ends in an audit record with explicit success/failure. The project tests core policy code separately in Node.js.

## Agentic vs deterministic

| Agentic — can vary between LLM runs | Deterministic — can be unit tested |
|---|---|
| Summarize issue / propose acceptance criteria | Validate URL and restrict network destination |
|---|---|
| Suggest implementation steps and tests | Strict schema and bounds checking |
| Identify potential affected components | Apply source-text risk escalation |
| Judge model uncertainty (advisory) | Force high uncertainty for known ambiguous patterns |
| Use read-only risk-inspection tool | Require approval and keep write actions impossible |

**Reason for the tool:** n8n AI Agent expects a tool connection. This demonstration gives the agent a meaningful **side-effect-free** capability, not a pointless calculator tool or a privileged GitHub tool. The downstream deterministic check is still authoritative; tool invocation must be verified in the actual n8n trace.

## Design changes compared with the initial private draft

- Added `inspect_issue_risk` Custom Code Tool to the n8n Agent so it has a connected `ai_tool` capability.
- Replaced free-text `expected` strings with structured assertions and included prompt-injection and invalid-input fixtures.
- Strengthened validation: exact top-level keys, `security_sensitive` Boolean, bounded arrays, explicit fail-closed outputs.
- Rechecked security-sensitive risk independently using the issue, not the model's classification.
- Removed published Form Trigger, source-instance n8n workflow ID, Data Table ID and all credential bindings for a portable **inactive** export.
- Made optional interactive approval require Basic Auth; no external write sink exists even after approval.
- Added reproducible sources, deterministic unit tests and CI so reviewers can inspect the guardrails without running an LLM.

## Known limits / next steps

- The risk patterns are deliberately **heuristic** and not a substitute for security review. A cleverly phrased attack can evade simple keywords.
- The agent is not a general-purpose coding agent. It plans and categorizes; it does not call repositories, run tests, commit, merge, deploy or change operational systems.
- The inspection tool is deterministic and receives text supplied by the agent. Actual calls, inputs and outcomes should be inspected in n8n execution traces.
- Reviewers cannot approve real changes: human decisions are evidence-only in this demo. A production version needs proper identity, role authorization, audit immutability, approval expiry rules and tightly scoped write adapters.
- AI output stability requires a real n8n execution and multiple model runs. Unit tests use intentionally mocked output to validate the surrounding policy.
- n8n may evolve node schema and supported model names. If importing into a different version, check model/tool/Wait nodes in the editor.
- Public GitHub API calls without credentials have rate limits; failed fetches are fail-closed.
- Execution outputs are not guaranteed to be durably retained forever. The example omits persistent storage to avoid instance-specific identifiers and privacy issues.

## Compatibility

The exported node versions follow n8n 2.x-era AI Agent / Custom Code Tool / Code / Wait node shapes and are designed to import in a current n8n Cloud instance. **No live runtime import has been executed in this repository build process.** The model credential and optional Wait Basic Auth credential must be set by the end user.
