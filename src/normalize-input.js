// URL allowlisting is the boundary for the optional public GitHub GET.
const f = $json;
const raw = String(f.issue_url || '').trim();
const cleaned = raw.split('#')[0].split('?')[0].replace(/\/+$/, '');
const match = /^https:\/\/github\.com\/([A-Za-z0-9][A-Za-z0-9_.-]{0,38})\/([A-Za-z0-9_.-]{1,100})\/issues\/([1-9]\d{0,9})$/.exec(cleaned);
const good = !!match && raw.length <= 400 && !cleaned.includes('..') && !cleaned.includes('%');
const context = {
  test_case: String(f.test_case || 'MANUAL_public_issue'), expected: f.expected || {},
  issue_url:good ? cleaned : '', owner:good ? match[1] : '',
  repo:good ? match[2] : '', issue_number:good ? match[3] : '',
  input_ok:good, data_source:good && f.issue ? 'sample' : good ? 'github' : 'invalid',
  issue_title:good && f.issue ? String(f.issue.title||'') : '',
  issue_body:good && f.issue ? String(f.issue.body||'') : '',
  issue_labels:good && f.issue ? String(f.issue.labels||'') : '',
  issue_author:good && f.issue ? String(f.issue.author||'') : '',
  issue_state:good && f.issue ? 'open' : '',
  validation_errors:good ? '' : 'Invalid or disallowed URL: expected https://github.com/owner/repo/issues/123',
  processing_outcome:good ? 'input_validated' : 'failed_closed_invalid_input',
  risk_level:'not_assessed',uncertainty_level:'not_assessed',
  review_decision:'not_applicable',write_action:'disabled_by_design',
  requires_human_review:false, interactive_approval_enabled:f.interactive_approval_enabled === true,
  external_write_performed:false,merge_deploy_or_execute_performed:false,
  report_markdown:'',risk_flags:'',test_pass:null,test_failures:[]
};
return {json:context};
