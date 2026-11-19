# Agensi listing — paste-ready content

This is creator-facing material, **not** part of the buyer's skill ZIP.

## Recommended settings

- **Title:** GitHub Issue Risk Gate — Deterministic Guardrails for AI Coding Agents
- **Short summary:** Turn GitHub issues into actionable engineering plans, then independently validate risk and test coverage before anyone starts coding.
- **Price for v1:** Free. Validate actual installations and feedback before offering a paid edition.
- **Category:** AI Agents & LLM Ops (or Code Review / Security & Compliance if a better fit is available).
- **Tags:** GitHub, Issue Triage, AI Coding Agents, Security, Agentic AI, Code Review, Deterministic Validation, Test Planning
- **Skill type:** Single Skill (exactly one SKILL.md)
- **Version:** 1.0.0
- **Requires / permissions:** Python 3.9+ and an agent that can run local scripts; local read of provided issue data; optional *read-only* GitHub access for public issue URLs. No credentials, paid tools, n8n setup, repository write permissions, or GitHub installations required for pasted issue text.
- **Creator:** Claudio Di Lorenzo
- **Repository:** `https://github.com/cdilorenzo/safe-agentic-issue-triage` (existing public repository). After updating it, set Documentation URL to `https://github.com/cdilorenzo/safe-agentic-issue-triage/tree/main/skills/github-issue-risk-gate`.

## Full description (English)

**AI can draft a coding plan. It should not approve its own risk assessment.**

GitHub Issue Risk Gate turns a GitHub issue or pasted issue description into a structured implementation-readiness review. Your AI coding agent proposes a minimal change, measurable acceptance criteria, positive/negative tests, and outstanding questions. Then an independent, single-file Python gate validates that plan, detects security-sensitive topics and risky change patterns, and escalates cases requiring human review.

**What you get**

- A portable Agent Skill (`SKILL.md`) usable by agents that support skills and local Python execution.
- Strict input validation that blocks malformed proposals and suspicious GitHub URL variants.
- Risk escalation for authentication and MFA, secrets, personal/regulated data, payments, destructive operations, production systems and embedded prompt-injection patterns.
- Medium-risk indicators for schema migrations, reliability/concurrency and public API contracts.
- Test-plan coverage checks: positive, negative/failure-path, security and documentation tests where applicable.
- Structured JSON or readable Markdown results with stable signal IDs, quality gaps and open questions.
- Six synthetic examples and a Python test suite. The gate script has no third-party dependencies, network calls or credential access.

**Control boundary:** The AI proposes; deterministic rules inspect; a human reviews. This skill **never** posts to GitHub, changes files, writes code, deploys or authorizes actions. Even `ready_for_review` means review is still needed, not that an implementation is approved.

**How it works:** Give your agent an issue title and body, or a public GitHub Issue URL if it has an existing read-only retrieval tool. The agent drafts a JSON plan and executes the included Python validator in its own environment. No n8n server or paid Agensi API calls are needed. If local Python execution isn't available, it must clearly mark the assessment unverified.

**Important limitation:** The independent gate is heuristic and does not read source code or prove security, architectural correctness or compliance. Detection can miss implicit risks or novel prompt injections. Treat the result as a disciplined handoff for a human engineering review.

Created independently by Claudio Di Lorenzo; packaged in the same repository as the Safe Agentic Issue Triage n8n reference workflow, with a separate runtime and tests.

## Use-case examples

1. Triage a backlog issue before assigning a coding agent; find missing acceptance criteria.
2. Detect authentication or secrets-related changes that need expert review.
3. Draft concrete positive and negative tests for a backend feature.
4. Identify prompt-injection text embedded in GitHub issue descriptions.
5. Produce a machine-readable risk report for a manual review checklist.

## Suggested example prompt to display in the listing

> Use GitHub Issue Risk Gate on this issue before coding. Draft the smallest viable implementation, two testable acceptance criteria, positive and negative test cases, and then run the deterministic gate. Report independent risk flags, open questions, and whether manual review is required. Do not modify GitHub or any repository files.

For an offline public demo, paste the issue from `examples/docs-low-risk.json` and ask the agent to run the gate; for a high-risk demo use `examples/auth-high-risk.json`.

## Evidence — only state what has actually been verified

- Local black-box tests: `python -m unittest discover -s tests/agent_skill -p "test_*.py" -v` from the repository root.
- Isolated temporary-file execution: tested without any sibling files.
- Full agent-to-Agensi MCP delivery and live marketplace acceptance: **not yet verified**. Do not say "tested in Claude Code, Codex and Cursor" without performing those live tests.
- No verified sales, usage, conversion rates or marketplace rankings are claimed.

## Upload steps

1. At https://www.agensi.io/sell, sign in and enable **Creator Mode** in dashboard settings if needed.
2. Click **Submit a Skill** in Creator Dashboard.
3. Upload **`skill.zip`** — the small ZIP, not the entire GitHub repository ZIP.
4. Review auto-populated fields and paste the title, summary, description, use cases and tags above.
5. Set price to **Free** for the initial listing. Do not configure paid tools or add credential requirements.
6. State Python 3.9+ and local script execution as requirements; optional GitHub read-only access for URL-based lookups.
7. Submit for Agensi security scan/human review. Resolve any reviewer feedback before claiming approval.
8. Once live, install your own listing through Agensi MCP in a script-capable agent and test both the docs fixture and MFA fixture. Inspect exact outputs and correct any incompatibility.

Official sources at time of preparation:
- https://www.agensi.io/docs/packaging
- https://www.agensi.io/docs/what-you-can-sell
- https://www.agensi.io/docs/creator-faq
- https://www.agensi.io/learn/how-to-sell-skills-on-agensi

Agensi controls the final UI, publishing account, review and listing URL; these cannot be completed by this offline repository package.
