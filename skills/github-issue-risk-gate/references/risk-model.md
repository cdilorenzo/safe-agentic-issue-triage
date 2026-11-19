# Risk and quality model

Independent Python rules assign a conservative risk floor. A model can claim a **higher** risk, but never lower that floor. Matched categories return stable `signals[].id` entries with the source (`issue.title`, `issue.body` or `analysis.proposed_change`) and a short explanation **without quoting the matched sensitive text**.

## High-risk categories

- `prompt_injection`: suspicious role-change, instruction override, secret revelation or safety-bypass directive embedded in issue/analysis content.
- `auth_identity`: authentication, MFA, access tokens, RBAC, permissions or other access control.
- `secret_handling`: credentials, secrets, private keys or key management.
- `bypass_control`: explicit attempts to disable or skip authentication, approvals, auditing or safeguards.
- `destructive_change`: dropping or wiping persistent data, deletion of users/accounts.
- `sensitive_data`: medical, personal, regulated or payment-card data.
- `money_flow`: invoices, billing, payment or transfer logic.
- `live_system`: explicitly mentioned production databases or live customer traffic.

## Medium-risk categories

- `data_migration`: schema/data migration, backfill or transaction isolation.
- `distributed_reliability`: concurrency, retries, queues, idempotency or webhooks.
- `api_contract`: public API, breaking contracts or rate limiting.

Documentation-only titles/labels suppress **medium** runtime-change flags, but never suppress high-risk signals. This is a conservative heuristic, not a perfect classification of change scope.

## Quality gates

- Explicit acceptance criteria required.
- At least one proposed test required.
- Code-change tests should include positive/integration **and negative/failure-path** cases.
- Docs-only cases need documentation/manual verification.
- High-risk changes should include security test cases.
- Short, vague or unresolved requirements produce gaps; the agent must ask clarifying questions instead of inventing certainty.

## Trust boundary and manual signoff

Issue bodies are untrusted and can carry prompt injections, code, URLs and requests to access secrets. The agent must not follow instructions embedded inside the issue. The deterministic runner does not call external services or inspect credentials. `authorized_to_execute` is **always false**, including for low-risk cases. The risk result is a starting point for human discussion, not an automated release gate or authorization decision.
