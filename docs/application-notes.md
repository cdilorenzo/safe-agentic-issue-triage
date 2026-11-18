# Application evidence for n8n Staff Platform Engineer (Agentic Engineering)

## Recommended submission

1. Repository link: `https://github.com/cdilorenzo/safe-agentic-issue-triage` **after you create and publish it**.
2. Actual n8n canvas screenshot, created from your running instance.
3. A short description of the trust boundary and quantitative test evidence (only if verified end to end).
4. Optionally link to independent personal reference architecture: `https://github.com/cdilorenzo/incident-weaver`.

## Ready-to-paste project summary (English)

**Safe Agentic Issue Triage — personal n8n engineering demo**

I built an n8n issue-triage workflow to demonstrate controlled AI-assisted software engineering. A tool-enabled AI Agent proposes acceptance criteria, implementation steps and tests, while independent deterministic gates validate the output schema, escalate security-sensitive issues and route proposals to human review. The workflow uses synthetic test cases, includes a prompt-injection scenario and explicitly excludes external writes, merging and deployment. I maintain its guardrails as tested JavaScript sources, generate the n8n workflow reproducibly and validate it in GitHub Actions.

**Important:** Add a sentence with *actual n8n run outcomes* only after you have tested the imported workflow. The offline tests do not establish live LLM success.

## Suggested repository description

`n8n AI Agent issue triage: read-only tools, deterministic policy gates, human-review boundaries and reproducible tests.`

## Suggested repository topics

`n8n` · `agentic-ai` · `ai-engineering` · `software-architecture` · `ai-safety` · `developer-productivity` · `human-in-the-loop`

## Publish to your personal GitHub account

```bash
cd safe-agentic-issue-triage
npm run check
git init
git add .
git commit -m "Add safe agentic issue triage portfolio demo"
gh auth login # choose your PERSONAL GitHub account
gh repo create cdilorenzo/safe-agentic-issue-triage --public --source=. --remote=origin --push
```

This command creates a **public** repository. Run it yourself only after reviewing code, tests and license, and confirming you want to publish. The project has not been automatically pushed to GitHub.

## Release checklist

- [ ] Import verified in own n8n instance
- [ ] All fixtures executed and results reviewed
- [ ] No real credentials or company IP in export
- [ ] Personal account selected before publishing
- [ ] Real screenshot added to `assets/`
- [ ] CI green on GitHub
- [ ] Repository URL and screenshot supplied in application
