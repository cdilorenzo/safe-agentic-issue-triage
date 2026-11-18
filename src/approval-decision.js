// Optional manual approval is evidence only: it NEVER authorizes external changes.
const base=$('Build Review Report').item.json;
const answer=String($json.Decision||'').trim();
const decision=answer==='Approve'?'approved_by_human_dry_run':answer==='Reject'?'rejected_by_human':'approval_timeout_or_invalid_response';
return {json:{...base,review_decision:decision,approval_note:String($json['Reviewer note']||'').slice(0,300),
  write_action:'disabled_by_design',external_write_performed:false,merge_deploy_or_execute_performed:false}};
