# Input and output contract

This document supports the `github-issue-risk-gate` skill. The agent must use a real, unmodified execution of `scripts/issue_risk_gate.py` to claim deterministic verification.

## Input JSON

Provide exactly two top-level objects: `issue` and `analysis`. Unknown fields are rejected. This prevents silently misinterpreting AI output as validated data.

`issue`:

| Field | Type | Rule |
|---|---|---|
| `title` | string | Required, nonblank, max 300 characters |
| `body` | string | Required, may be empty, max 20,000 characters |
| `url` | string | Optional, must be exact `https://github.com/OWNER/REPO/issues/NUMBER` without query/fragment |
| `number` | integer | Optional, positive; must match URL number if URL present |
| `labels` | string[] | Optional; max 20 values, each max 80 characters |

`analysis` (all fields required):

| Field | Type | Rule |
|---|---|---|
| `summary` | string | Nonblank, max 1,200 characters |
| `proposed_change` | string | Nonblank, max 1,200 characters |
| `acceptance_criteria` | string[] | Max 12, 280 characters each; missing items are flagged |
| `tests` | object[] | Max 16; each has exactly `kind`, `scenario`, `expected` |
| `questions` | string[] | Max 10; each max 280 characters |
| `claimed_risk` | enum | `low`, `medium`, `high` |
| `reasoning` | string | Nonblank, max 1,200 characters |

Test `kind`: `positive`, `negative`, `security`, `regression`, `integration`, `documentation`, `manual`. `scenario` and `expected` must both be nonempty strings of at most 300 characters. Max entire input: 64 KB UTF-8.

## Invocation

Python 3.9+ standard library only. Paths below are examples; an Agensi-compatible agent may execute the same script from a temporary file instead of the skill directory.

```sh
python3 scripts/issue_risk_gate.py --input examples/docs-low-risk.json --format json
python3 scripts/issue_risk_gate.py --input examples/auth-high-risk.json --format markdown --strict
python3 scripts/issue_risk_gate.py --input - --format json < examples/docs-low-risk.json
```

`--strict`: exit `0` only for `ready_for_review`, `1` for otherwise valid gated analyses, and `2` for malformed/invalid inputs. Without `--strict`, a correctly parsed high-risk issue returns exit `0` because the tool successfully produced a risk report (its status still requires review). Invalid input always exits `2`.

## Output contract

`gate.status` is one of:

- `ready_for_review`: no heuristic risk blocker and no quality gaps; **not approval**.
- `needs_clarification`: missing tests, vague requirements or open questions.
- `requires_human_review`: medium/high risk or prompt-injection indicator; escalate, do not execute.
- `blocked`: schema, URL or input-file failure; no usable triage.

Additional machine-readable values: `gate.computed_risk`, `gate.agent_claimed_risk`, `gate.risk_escalated`, `gate.human_signoff_required=true`, `gate.authorized_to_execute=false`, `signals` (rule IDs and descriptions), `quality_gaps`, `open_questions` and `proposal`.

The output does not include the raw issue body. It does reproduce the agent's proposed summary and acceptance criteria, so do not include secrets or unnecessary personal data in those fields.

## Honest limitations

This is a deterministic **keyword/rule-based** gate plus model-generated planning, not a static code analyzer, full threat model, semantic domain-boundary checker or security guarantee. It can miss synonyms, implicit requirements and malicious instructions that evade its patterns. It has not inspected source files or run actual acceptance tests. A human remains accountable for the decision and any later code changes.
