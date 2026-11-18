# Security and privacy

The workflow is a public **demonstration**, not production-authorization software.

## Trust boundaries

- GitHub issue text and model output are untrusted. Prompt-injection text is never an instruction to the workflow.
- Network target is fixed to public `api.github.com` with HTTP GET only. Invalid URLs fail before any request.
- The Agent has only a read-only pure JavaScript tool, no GitHub write tool or credentials.
- Schema validation, risk escalation, review route and output assertions run **outside** the Agent.
- No n8n Form Trigger, Webhook Trigger or MCP exposure is configured.
- Optional approval requires configuring Basic Auth on the Wait Form before use.
- A reviewer approving a proposal cannot cause an external write: none exists in the exported workflow.

## Credentials and sensitive information

- No API keys, credentials, instance URLs, webhook IDs, personal access tokens, customer data or production issue descriptions should be committed.
- When importing, configure your own model credential inside n8n only.
- Do not publish raw n8n execution exports without inspecting them; they may contain untrusted issue text, operational context and provider information.
- Public GitHub issue bodies are sent to your selected model provider. Do not test company-sensitive issues using this workflow.
- n8n stores execution data according to instance settings; the final audit node minimizes fields but intermediate execution logs can still contain full public issue bodies.

## Residual risks

- Keyword policy is a demonstration heuristic, not a comprehensive policy engine.
- Models can emit malformed, inconsistent or incorrect suggestions; invalid output is blocked from report generation, but valid JSON does not imply correctness.
- Optional public GitHub requests rely on API availability, response shape, rate limits and the n8n HTTP node's behavior.
- A Wait Form's URL is not a strong identity assertion by itself. Configure Basic Auth and use only in a private environment.
- This workflow intentionally does not include protected write actions. Do not add them without separate authenticated authorization and threat modelling.

## Reporting vulnerabilities

Do not include real credentials in issues. For security problems with this portfolio project, use a private contact channel before sharing exploit details publicly.
