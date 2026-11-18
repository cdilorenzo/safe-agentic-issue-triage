// SOURCE OF TRUTH: The build script replaces __FIXTURES__ with public synthetic cases.
// To inspect ONE real public issue, set CUSTOM_PUBLIC_ISSUE_URL and run manually.
// No public form/webhook is enabled in this reference implementation.
const CUSTOM_PUBLIC_ISSUE_URL = '';
const fixtures = __FIXTURES__;
if (CUSTOM_PUBLIC_ISSUE_URL.trim()) {
  return [{json:{test_case:'MANUAL_public_issue',issue_url:CUSTOM_PUBLIC_ISSUE_URL.trim(),expected:{input_ok:true,processing_outcome:'report_generated',write_action:'disabled_by_design'}}}];
}
return fixtures.map((f,i) => ({json:{...f},pairedItem:{item:0}}));
