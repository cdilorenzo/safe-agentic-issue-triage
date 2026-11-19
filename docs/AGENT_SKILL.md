# GitHub Issue Risk Gate — standalone Agent Skill

This repository provides **two independent implementations of the same safety boundary**:

| Implementation | Location | Requirements |
|---|---|---|
| n8n reference workflow | [`workflows/safe-agentic-issue-triage.json`](../workflows/safe-agentic-issue-triage.json) | n8n + configured AI model |
| Portable coding-agent skill | [`skills/github-issue-risk-gate/`](../skills/github-issue-risk-gate/) | Python 3.9+ and a script-capable agent |

The n8n version uses a JavaScript gate embedded in the automation flow. The standalone skill uses a Python risk gate. They are **not** the same runtime or a shared service; their rules and quality evidence should be evaluated independently.

## Run the Python gate locally

From the repository root, without needing n8n, API keys or external Python dependencies:

```bash
python skills/github-issue-risk-gate/scripts/issue_risk_gate.py --input skills/github-issue-risk-gate/examples/docs-low-risk.json --format markdown
python skills/github-issue-risk-gate/scripts/issue_risk_gate.py --input skills/github-issue-risk-gate/examples/auth-high-risk.json --format json
```

The JSON input contains an `issue` and an AI-proposed `analysis`; see [input contract](../skills/github-issue-risk-gate/references/input-contract.md). The script reports an independent *risk floor* and readiness for a **human review**, never permission to implement or deploy. Its JSON output is on stdout. The gate doesn't retrieve URLs, run model calls or modify files.

## Use in an agent

Point a compatible coding agent at [`SKILL.md`](../skills/github-issue-risk-gate/SKILL.md) or install this skill using the agent's own skill directory conventions. Ask it to triage a pasted issue; if a public GitHub URL is supplied, the agent needs an existing read-only retrieval capability. It must execute the Python gate to claim a validated result.

Example prompt:

> Review this GitHub issue before coding. Draft the minimal implementation scope, explicit acceptance criteria, positive and negative tests, then execute the deterministic Python risk gate. Show triggered rule IDs and any human-review requirement. Do not modify repository content.

**Important:** Local Python tests pass, but live installation via Agensi MCP or specific coding-agent versions is not proven by offline tests alone. Check agent permissions, tool execution and outputs in your own environment.

## Testing and packaging

```bash
python -m unittest discover -s tests/agent_skill -p 'test_*.py' -v
python scripts/package-agent-skill.py
python scripts/check-agent-skill.py
```

The package command writes the standalone upload to `dist/skill.zip` and includes **exactly one** top-level skill folder and `SKILL.md`. The output deliberately excludes the repository's Node code, n8n workflow, test suite, docs outside the skill, credentials and binaries. GitHub Actions runs these steps in the independent `Validate Agent Skill` workflow.

## Agensi documentation URL

Once these files are committed and pushed, use:

`https://github.com/cdilorenzo/safe-agentic-issue-triage/tree/main/skills/github-issue-risk-gate`

The [listing text](AGENSI_LISTING.md) is creator-facing. The exact Agensi listing URL can be added after approval. No purchase, paid API or GitHub write scopes are required for pasted issue text.

## Security limits

The deterministic gate is a conservative heuristic: it can miss novel attacks or implicit threats and may flag benign terms. It does not inspect repository code, authenticate issue contents, certify security or compliance, or authorize action. Public issue data may be supplied to an LLM by the agent; use appropriate data handling policies. See [project security](../SECURITY.md) and [risk model](../skills/github-issue-risk-gate/references/risk-model.md).
