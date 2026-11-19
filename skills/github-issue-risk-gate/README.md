# GitHub Issue Risk Gate

**A read-only Agent Skill for engineering issue triage.** AI drafts acceptance criteria, an implementation outline and test cases. A separate single-file Python risk gate checks the schema, detects risky terms and refuses to authorize execution.

**Runs with:** Python 3.9+ and an agent able to run a local Python script. No external Python packages, credentials, paid Agensi tools or n8n instance are required for pasted issue text. Public GitHub URLs additionally require a read-only retrieval capability in the agent; if unavailable, paste the issue instead.

**Try it:** `python3 scripts/issue_risk_gate.py --input examples/docs-low-risk.json --format markdown`

See `SKILL.md` for the agent's mandatory workflow, `references/input-contract.md` for the schema and `references/risk-model.md` for risks and limitations.

Author: Claudio Di Lorenzo. MIT licensed. This standalone Agent Skill lives alongside the original n8n reference workflow in the same repository; neither runtime depends on the other.

**Project repository:** https://github.com/cdilorenzo/safe-agentic-issue-triage
