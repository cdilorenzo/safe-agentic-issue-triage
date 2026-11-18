// SECURITY BOUNDARY: model output is untrusted. Fail closed on missing/invalid schema.
const ctx = $('Issue Context').item.json;
const levels = ['low','medium','high'];
const issues = [];
const raw = typeof $json.output === 'string' ? $json.output.trim() : '';
let triage = null;
if ($json.error) issues.push('agent_error');
if (!raw) issues.push('empty_agent_output');
else {
  const body = raw.replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'');
  try { triage = JSON.parse(body); }
  catch { issues.push('invalid_json'); }
}
const str = (v,max=1000) => typeof v==='string' && v.trim().length>0 && v.length<=max;
const arr = (v,min,max) => Array.isArray(v) && v.length>=min && v.length<=max && v.every(x=>str(x,1000));
if (triage && typeof triage === 'object' && !Array.isArray(triage)) {
  const keys=['summary','acceptance_criteria','implementation_steps','test_plan','affected_components','uncertainty','risk_assessment'];
  if (Object.keys(triage).sort().join('|')!==keys.sort().join('|')) issues.push('unexpected_or_missing_top_level_keys');
  if (!str(triage.summary,3000)) issues.push('invalid_summary');
  if (!arr(triage.acceptance_criteria,1,8)) issues.push('invalid_acceptance_criteria');
  if (!arr(triage.implementation_steps,1,10)) issues.push('invalid_implementation_steps');
  if (!arr(triage.test_plan,1,8)) issues.push('invalid_test_plan');
  if (!arr(triage.affected_components,1,10)) issues.push('invalid_affected_components');
  const u = triage.uncertainty;
  if (!u || !levels.includes(u.level) || !arr(u.open_questions,0,10)) issues.push('invalid_uncertainty');
  else if (u.level==='high' && u.open_questions.length===0) issues.push('high_uncertainty_requires_questions');
  const r=triage.risk_assessment;
  if (!r || !levels.includes(r.level) || !str(r.rationale,3000) || typeof r.security_sensitive!=='boolean') issues.push('invalid_risk_assessment');
} else if (triage !== null) { issues.push('output_not_object'); triage = null; }

// Independent risk policy: scan original issue, never trust model's risk label.
const scan = [ctx.issue_title,ctx.issue_body,ctx.issue_labels,triage?.affected_components?.join(' ')||''].join('\n');
const rules = [
  ['authentication',/\b(auth|authentication|login|mfa|2fa|sso|oauth|jwt|session|password)\b/i],
  ['authorization',/\b(authz|authori[sz]ation|rbac|permission|privilege|admin|roles?)\b/i],
  ['secrets',/\b(secret|secrets|tokens?|api[ _-]?keys?|credentials?|private key|vault)\b/i],
  ['sensitive_data',/\b(pii|personal data|gdpr|hipaa|ssn|payment|bank account|encrypt|decrypt)\b/i],
  ['prompt_injection',/ignore (all )?(previous|prior)|system prompt|override (the )?(rules|instructions)|developer message|force[- ]push/i]
];
const detFlags=rules.filter(([_,re])=>re.test(scan)).map(([flag])=>flag);
const agentSteps=(triage?.implementation_steps||[]).join(' ');
const blocked=/(^|[.;\n]\s*)(force[- ]push|push directly to (main|master)|deploy to prod|run rm -rf|remove (all )?(security )?checks)/i;
if (blocked.test(agentSteps)) { issues.push('dangerous_agent_implementation_step'); detFlags.push('suggested_privileged_action'); }
const srcBody=String(ctx.issue_body||'');
const vague=/\b(maybe|not sure|somehow|sometimes|faster|better|improve|asap|soon)\b/i.test(ctx.issue_title+' '+srcBody);
const ambiguous=srcBody.trim().length===0 || (srcBody.length<200 && vague);
const valid=issues.length===0 && triage!==null;
const rank={low:0,medium:1,high:2};
let risk=valid ? triage.risk_assessment.level:'not_assessed';
if (valid && triage.risk_assessment.security_sensitive) risk='high';
if (detFlags.length) risk='high';
let uncertainty=valid ? triage.uncertainty.level:'not_assessed';
if (valid && ambiguous) uncertainty='high';
const flags=[...detFlags.map(x=>'det:'+x)];
if (valid) flags.push('agent_risk:'+triage.risk_assessment.level,'agent_uncertainty:'+triage.uncertainty.level);
if (ambiguous) flags.push('det:ambiguous_requirements');
return {json:{...ctx,is_valid:valid,triage:valid?triage:null,
  validation_errors:issues.join('; '),risk_level:risk,uncertainty_level:uncertainty,
  deterministic_risk_flags:detFlags,risk_flags:flags.join(', '),
  processing_outcome:valid?'validated':'failed_closed_invalid_agent_output',
  requires_human_review:valid && (risk==='high'||risk==='medium'),
  review_decision:valid?'pending':'not_applicable_failed_closed',
  write_action:'disabled_by_design',external_write_performed:false,
  merge_deploy_or_execute_performed:false}};
