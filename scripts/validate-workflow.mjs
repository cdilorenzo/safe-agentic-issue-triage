import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const filename=path.join(root,'workflows','safe-agentic-issue-triage.json');
const wf=JSON.parse(fs.readFileSync(filename,'utf8'));
assert.equal(wf.active,false,'public template must not be active');
assert.equal(wf.availableInMCP,false,'must not be remotely accessible via MCP');
assert.ok(Array.isArray(wf.nodes) && wf.nodes.length>=15);
const names=new Set(wf.nodes.map(n=>n.name));
assert.equal(names.size,wf.nodes.length,'duplicate node names');
const ids=new Set(wf.nodes.map(n=>n.id));
assert.equal(ids.size,wf.nodes.length,'duplicate node IDs');
for(const node of wf.nodes) {
  assert.equal(node.position.length,2);
  assert.ok(Number.isFinite(node.position[0]) && Number.isFinite(node.position[1]));
  const label=node.type.toLowerCase();
  assert.ok(!label.includes('datatab') && !label.includes('mcpserver') && !label.includes('formtrigger') && !label.includes('webhook'),'forbidden public trigger or table binding');
  assert.ok(node.type!=='n8n-nodes-base.executeCommand' && node.type!=='n8n-nodes-base.git' && node.type!=='n8n-nodes-base.github','no execution or GitHub writes');
  if (node.type==='n8n-nodes-base.httpRequest') {
    assert.equal(node.parameters.method,'GET','no external mutation');
    assert.match(node.parameters.url,/^=https:\/\/api\.github\.com\/repos\//,'HTTP target must be GitHub API');
  }
  if (node.credentials) throw new Error(`Credential reference in ${node.name} should not be published`);
}
for(const [from,channels] of Object.entries(wf.connections)) {
  assert.ok(names.has(from),`orphan source ${from}`);
  for(const outputs of Object.values(channels)) for(const arr of outputs) for(const edge of arr) assert.ok(names.has(edge.node),`orphan target ${edge.node}`);
}
const model=wf.nodes.find(n=>n.name==='Google Gemini Chat Model');
const tool=wf.nodes.find(n=>n.name==='inspect_issue_risk');
const agent=wf.nodes.find(n=>n.name==='AI Triage Agent');
assert.ok(model && tool && agent,'missing model/tool/agent');
assert.equal(tool.name,'inspect_issue_risk','tool name must exactly match instructions the agent receives');
assert.equal(tool.parameters.specifyInputSchema,false,'tool must accept the documented JSON string query');
assert.equal(wf.connections[model.name].ai_languageModel[0][0].node,agent.name);
assert.equal(wf.connections[tool.name].ai_tool[0][0].node,agent.name);
assert.ok(!('id' in wf) && !('versionId' in wf),'no source instance workflow identifier');
const serial=JSON.stringify(wf);
assert.ok(!/github_pat_[a-zA-Z0-9]{8,}|sk-[a-zA-Z0-9]{24,}/.test(serial),'looks like a secret');
assert.ok(!serial.includes('SXQrxtL45hitMhfg'),'previous instance-specific data table ID leaked');
const codeNodes=wf.nodes.filter(x=>x.type==='n8n-nodes-base.code'||x.type==='@n8n/n8n-nodes-langchain.toolCode');
for(const n of codeNodes) {
  const code=n.parameters.jsCode;
  assert.ok(code && code.length>20,`empty code node: ${n.name}`);
  try{new Function('$json','$input','$execution','$', 'query',code)}
  catch(e){throw new Error(`Code syntax error in ${n.name}: ${e.message}`)}
}
console.log(`OK: ${wf.nodes.length} valid unique nodes, safe connections, agent tool, code syntax and no credential bindings`);
