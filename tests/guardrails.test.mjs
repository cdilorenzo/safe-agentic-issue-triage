import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const files=name=>fs.readFileSync(path.join(root,'src',name),'utf8');
const fixtures=JSON.parse(fs.readFileSync(path.join(root,'tests','fixtures.json'),'utf8'));
function evaluate(name,{item={},upstream={},query='' }={}) {
  const source=files(name);
  const lookup=(s)=>({item:{json:upstream[s]??{}}});
  const exec=new Function('$json','$input','$execution','$','query',source);
  return exec(item,{all:()=>[]},{id:'unit-test'},lookup,query);
}
function context(index) {
  return evaluate('normalize-input.js',{item:fixtures[index]}).json;
}
function syntheticModel({uncertainty='low',risk='low',steps=null,sensitive=false}={}) {
  return {output:JSON.stringify({
    summary:'This is a proposal to update the repository. A human engineer must confirm the requirements and review the suggested changes.',
    acceptance_criteria:['Document expected behavior','Add a regression test'],
    implementation_steps:steps||['Inspect existing implementation','Prepare a small, reviewable change'],
    test_plan:['Run unit tests','Review documentation links'],
    affected_components:['docs/api/overview.md'],
    uncertainty:{level:uncertainty,open_questions:uncertainty==='high'?['Which endpoints are affected?']:[]},
    risk_assessment:{level:risk,rationale:'Classification based on visible issue content',security_sensitive:sensitive}
  })};
}
function validateCase(i,model={}) {
  const ctx=context(i);
  const output=evaluate('validate-output.js',{item:syntheticModel(model),upstream:{'Issue Context':ctx}}).json;
  return {ctx,output};
}
function finish(i,output) {
  const base=evaluate('build-report.js',{item:output}).json;
  const result=evaluate('assert-expectations.js',{item:base}).json;
  const audit=evaluate('final-audit.js',{item:result}).json;
  return audit;
}

test('TC1: documentation -> low-risk report; all invariants pass',()=>{
  const {output}=validateCase(0);
  assert.equal(output.is_valid,true);
  assert.equal(output.risk_level,'low');
  assert.equal(finish(0,output).test_pass,true);
});
test('TC2: vague request -> high uncertainty enforced even if model says low',()=>{
  const {output}=validateCase(1);
  assert.equal(output.uncertainty_level,'high');
  assert.equal(finish(1,output).test_pass,true);
});
test('TC3: auth+MFA+tokens => HIGH independent of an optimistic model',()=>{
  const {output}=validateCase(2);
  assert.equal(output.risk_level,'high');
  assert.ok(output.deterministic_risk_flags.includes('authentication'));
  assert.ok(output.deterministic_risk_flags.includes('secrets'));
  assert.equal(finish(2,output).test_pass,true);
});
test('TC4: hostile instructions in issue data are flagged as risk, never executed',()=>{
  const {output}=validateCase(3);
  assert.equal(output.risk_level,'high');
  assert.ok(output.deterministic_risk_flags.includes('prompt_injection'));
  assert.equal(finish(3,output).test_pass,true);
});
test('TC5: non-GitHub URL is denied before fetch or model invocation',()=>{
  const c=context(4);
  assert.equal(c.input_ok,false);
  assert.equal(c.processing_outcome,'failed_closed_invalid_input');
  const done=evaluate('fail-closed.js',{item:c}).json;
  assert.equal(evaluate('assert-expectations.js',{item:done}).json.test_pass,true);
});
test('github URLs cannot be used for SSRF or arbitrary network targets',()=>{
  for(const url of ['http://github.com/owner/repo/issues/3','https://github.com.evil.org/o/r/issues/7',
  'https://github.com/o/r/issues/1/../../private','https://github.com/o/r/pulls/1',
  'https://api.github.com/repos/o/r/issues/1', 'https://github.com/o/r/issues/0']) {
    assert.equal(evaluate('normalize-input.js',{item:{issue_url:url}}).json.input_ok,false,url);
  }
});
test('malformed JSON fails closed',()=>{
  const raw={output:'{oops'};
  const r=evaluate('validate-output.js',{item:raw,upstream:{'Issue Context':context(0)}}).json;
  assert.equal(r.is_valid,false);
  assert.equal(r.processing_outcome,'failed_closed_invalid_agent_output');
  assert.equal(r.report_markdown,'');
});
test('missing security_sensitive boolean fails strict schema validation',()=>{
  const model=JSON.parse(syntheticModel().output);
  delete model.risk_assessment.security_sensitive;
  const r=evaluate('validate-output.js',{item:{output:JSON.stringify(model)},upstream:{'Issue Context':context(2)}}).json;
  assert.equal(r.is_valid,false);
  assert.match(r.validation_errors,/invalid_risk_assessment/);
});
test('model extra top-level fields are rejected',()=>{
  const model=JSON.parse(syntheticModel().output);model.trust_me=true;
  const r=evaluate('validate-output.js',{item:{output:JSON.stringify(model)},upstream:{'Issue Context':context(0)}}).json;
  assert.equal(r.is_valid,false);
  assert.match(r.validation_errors,/unexpected_or_missing/);
});
test('approval only records a decision and never performs a write',()=>{
  const {output}=validateCase(2);
  const report=evaluate('build-report.js',{item:output}).json;
  const approved=evaluate('approval-decision.js',{
    item:{Decision:'Approve','Reviewer note':'Checked'},upstream:{'Build Review Report':report}
  }).json;
  assert.equal(approved.review_decision,'approved_by_human_dry_run');
  assert.equal(approved.write_action,'disabled_by_design');
  assert.equal(approved.external_write_performed,false);
});
test('audit has no raw issue body, secrets or full model transcript',()=>{
  const {output}=validateCase(0);
  const audit=finish(0,output);
  assert.equal(audit.test_pass,true);
  assert.ok(!('issue_body' in audit));
  assert.ok(!('triage' in audit));
  assert.equal(audit.external_write_performed,false);
});
test('read-only risk probe is side-effect free and returns deterministic signals',()=>{
  const output=evaluate('risk-probe-tool.js',{query:JSON.stringify({title:'Change MFA',body:'Store API tokens',labels:'security'})});
  const result=JSON.parse(output);
  assert.ok(result.risk_signals.includes('authentication'));
  assert.ok(result.risk_signals.includes('secrets'));
});
test('assertion node is not a rubber stamp: contradictory output fails the case',()=>{
  const {output}=validateCase(2);
  const report=evaluate('build-report.js',{item:output}).json;
  const tampered={...report,risk_level:'low',requires_human_review:false};
  const checked=evaluate('assert-expectations.js',{item:tampered}).json;
  assert.equal(checked.test_pass,false);
  assert.ok(checked.test_failures.length>=2);
});
test('GitHub issue normalization accepts empty body but rejects PR-like payloads',()=>{
  const upstream={'Validate URL + Demo Fixtures':context(0)};
  const good=evaluate('normalize-github.js',{item:{title:'A task',body:null,number:101,state:'open',labels:[],user:{login:'demo'}},upstream}).json;
  assert.equal(good.input_ok,true);
  assert.equal(good.issue_body,'');
  const bad=evaluate('normalize-github.js',{item:{title:'A task',body:'text',number:101,state:'open',pull_request:{}},upstream}).json;
  assert.equal(bad.input_ok,false);
});
test('human rejection and timeout remain a non-mutating dry run',()=>{
  const {output}=validateCase(2);
  const report=evaluate('build-report.js',{item:output}).json;
  for(const [input,decision] of [
    [{Decision:'Reject'},'rejected_by_human'],[{},'approval_timeout_or_invalid_response']
  ]) {
    const record=evaluate('approval-decision.js',{item:input,upstream:{'Build Review Report':report}}).json;
    assert.equal(record.review_decision,decision);
    assert.equal(record.external_write_performed,false);
    assert.equal(record.write_action,'disabled_by_design');
  }
});


test('exported AI tool uses the exact inspect_issue_risk name and agent connection',()=>{
  const wf=JSON.parse(fs.readFileSync(path.join(root,'workflows','safe-agentic-issue-triage.json'),'utf8'));
  const tool=wf.nodes.find(n=>n.type==='@n8n/n8n-nodes-langchain.toolCode');
  assert.ok(tool);
  assert.equal(tool.name,'inspect_issue_risk');
  assert.equal(wf.connections[tool.name].ai_tool[0][0].node,'AI Triage Agent');
  const agent=wf.nodes.find(n=>n.name==='AI Triage Agent');
  assert.match(agent.parameters.options.systemMessage,/Call inspect_issue_risk once/);
});
