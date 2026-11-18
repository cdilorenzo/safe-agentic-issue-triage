// Agent-callable tool. Deterministic, no network, no filesystem, no credentials, no side effects.
// Its output is advisory ONLY. Independent downstream Code node enforces risk policy.
let text = '';
try {
  const value = typeof query === 'string' ? query : JSON.stringify(query);
  const data = JSON.parse(value);
  text = [data.title||'',data.body||'',data.labels||''].join('\n').slice(0,8000);
} catch {
  text = String(query||'').slice(0,8000);
}
const checks = [
  ['authentication',/\b(auth|authentication|login|mfa|2fa|sso|oauth|jwt|session|password)\b/i],
  ['authorization',/\b(authz|authori[sz]ation|rbac|permission|privilege|admin|roles?)\b/i],
  ['secrets',/\b(secrets?|tokens?|api[ _-]?keys?|credentials?|private key|vault)\b/i],
  ['sensitive_data',/\b(personal data|pii|gdpr|payment|bank account|encrypt|decrypt)\b/i],
  ['prompt_injection',/ignore (all )?(previous|prior)|system prompt|override (the )?(rules|instructions)|developer message|force[- ]push/i]
];
return JSON.stringify({risk_signals:checks.filter(([_,re])=>re.test(text)).map(([name])=>name),
  note:'Advisory read-only probe. Downstream independently recomputes risk from source issue.'});
