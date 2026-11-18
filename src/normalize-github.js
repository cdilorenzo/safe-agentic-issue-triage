// Keep original parsed URL and deterministic safety settings, never trust API response fields.
const input = $('Validate URL + Demo Fixtures').item.json;
const issue = $json;
const valid = issue && typeof issue.title === 'string' && (typeof issue.body === 'string' || issue.body === null) &&
  !issue.pull_request && issue.number === Number(input.issue_number) && issue.state === 'open';
if (!valid) {
  return {json:{...input,input_ok:false,processing_outcome:'failed_closed_unexpected_github_response',
    validation_errors:'GitHub response absent, malformed, not an open issue, or represents a pull request'}};
}
return {json:{...input,input_ok:true,data_source:'github',issue_title:issue.title.slice(0,500),
  issue_body:String(issue.body||'').slice(0,16000),issue_labels:Array.isArray(issue.labels) ? issue.labels.map(x=>typeof x==='string'?x:x.name||'').join(', ').slice(0,1000):'',
  issue_author:String(issue.user?.login||'').slice(0,100),issue_state:issue.state}};
