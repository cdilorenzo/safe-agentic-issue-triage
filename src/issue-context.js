// Bound prompt size and keep attribution (the source issue is untrusted content).
return {json:{...$json,issue_title:String($json.issue_title||'').slice(0,500),
  issue_body:String($json.issue_body||'').slice(0,6000),
  issue_labels:String($json.issue_labels||'').slice(0,1000)}};
