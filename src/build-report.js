// Pure presentation and routing. There is deliberately NO external write node.
const d=$json;
if (!d.is_valid || !d.triage) throw new Error('Invalid agent data must never reach report builder');
const t=d.triage;
const review=d.risk_level==='high'?'human_review_required':d.uncertainty_level==='high'?'needs_clarification':d.risk_level==='medium'?'human_review_recommended':'report_only';
const mdBullet=a=>(a||[]).map(x=>'- '+String(x)).join('\n');
const mdCheck=a=>(a||[]).map(x=>'- [ ] '+String(x)).join('\n');
const mdOrder=a=>(a||[]).map((x,i)=>(i+1)+'. '+String(x)).join('\n');
const scrub=s=>String(s||'').replace(/\|/g,'\\|').replace(/[\r\n]/g,' ');
const report=[
  '# Safe Agentic Issue Triage: '+scrub(d.issue_title),
  '', '| Field | Value |','|---|---|',
  '| Issue | '+scrub(d.issue_url)+' |',
  '| Case | '+scrub(d.test_case)+' |',
  '| Source | '+scrub(d.data_source)+' |',
  '| Risk | **'+d.risk_level.toUpperCase()+'** |',
  '| Uncertainty | '+d.uncertainty_level+' |',
  '| Review | '+review+' |',
  '| External write | **disabled by design** |',
  '', '> Untrusted issue text and AI-generated suggestions. Review before implementation. No code was executed, no changes written.',
  '', '## Summary',t.summary,
  '', '## Acceptance criteria',mdCheck(t.acceptance_criteria),
  '', '## Implementation proposal (human engineer)',mdOrder(t.implementation_steps),
  '', '## Test plan',mdCheck(t.test_plan),
  '', '## Affected components',mdBullet(t.affected_components),
  '', '## Uncertainty / questions',t.uncertainty.open_questions.length?mdBullet(t.uncertainty.open_questions):'- None identified by the model',
  '', '## Risk', '- AI assessment: '+t.risk_assessment.level+' — '+t.risk_assessment.rationale,
  '- Independent risk flags: '+(d.deterministic_risk_flags.length?d.deterministic_risk_flags.join(', '):'none'),
  '', '## Human reviewer checklist',
  '- [ ] Confirm requirements and acceptance criteria',
  '- [ ] Review security implications and deterministic flags',
  '- [ ] Approve or reject proposed implementation outside this dry-run',
  ''
].join('\n');
return {json:{...d,processing_outcome:'report_generated',review_decision:review,
  requires_human_review:d.risk_level==='high'||d.risk_level==='medium',
  write_action:'disabled_by_design',report_markdown:report}};
