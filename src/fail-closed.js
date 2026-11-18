// Failed input or GitHub read never reaches the AI model; no external writes.
return {json:{...$json,is_valid:false,report_markdown:'',
  risk_level:$json.risk_level==='high'?'high':'not_assessed',uncertainty_level:'not_assessed',
  review_decision:'not_applicable_failed_closed',requires_human_review:false,
  write_action:'disabled_by_design',external_write_performed:false,merge_deploy_or_execute_performed:false}};
