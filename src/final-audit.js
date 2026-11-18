// Portable audit as execution output. No instance-specific Data Table IDs and no live writes.
const d=$json;
return {json:{
  test_case:d.test_case,issue_url:d.issue_url,source:d.data_source,
  execution_id:String($execution.id||'manual'),processed_at:new Date().toISOString(),
  input_ok:d.input_ok,processing_outcome:d.processing_outcome,
  is_valid:d.is_valid===true,risk_level:d.risk_level,uncertainty_level:d.uncertainty_level,
  risk_flags:d.risk_flags||'',review_decision:d.review_decision,
  requires_human_review:d.requires_human_review===true,
  write_action:d.write_action,external_write_performed:false,
  merge_deploy_or_execute_performed:false,
  expected:d.expected||{},test_pass:d.test_pass===true,test_failures:d.test_failures||[],
  validation_errors:d.validation_errors||'',report_markdown:d.report_markdown||''
}};
