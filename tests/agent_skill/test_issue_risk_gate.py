"""Black-box CLI tests: exact shipped Python script, no mocked gate outcomes."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "github-issue-risk-gate" / "scripts" / "issue_risk_gate.py"
EXAMPLES = ROOT / "skills" / "github-issue-risk-gate" / "examples"


def fixture(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def run_gate(payload=None, *, args=(), raw=None, script=SCRIPT):
    data = raw if raw is not None else json.dumps(payload, ensure_ascii=False)

    result = subprocess.run(
        [sys.executable, "-I", "-B", "-X", "utf8",
         str(script), "--input", "-", *args],
        input=data,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=8,
        check=False,
    )

    if result.stdout is None:
        raise AssertionError(
            f"subprocess stdout not captured: stderr={result.stderr!r}"
        )

    if "--format" in args and args[args.index("--format") + 1] == "markdown":
        return result, result.stdout

    return result, json.loads(result.stdout)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.good = fixture("docs-low-risk.json")

    def test_docs_ready_for_review(self):
        proc, result = run_gate(self.good)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(result["gate"]["status"], "ready_for_review")
        self.assertEqual(result["gate"]["computed_risk"], "low")
        self.assertEqual(result["signals"], [])

    def test_even_ready_case_never_authorizes_work(self):
        _, result = run_gate(self.good)
        self.assertFalse(result["gate"]["authorized_to_execute"])
        self.assertTrue(result["gate"]["human_signoff_required"])

    def test_high_risk_auth_is_escalated_from_model_low(self):
        _, result = run_gate(fixture("auth-high-risk.json"))
        self.assertEqual(result["gate"]["status"], "requires_human_review")
        self.assertEqual(result["gate"]["computed_risk"], "high")
        self.assertTrue(result["gate"]["risk_escalated"])
        self.assertIn("auth_identity", {item["id"] for item in result["signals"]})

    def test_ambiguous_issue_needs_clarification(self):
        _, result = run_gate(fixture("ambiguous.json"))
        self.assertEqual(result["gate"]["status"], "needs_clarification")
        self.assertGreaterEqual(len(result["quality_gaps"]), 2)
        self.assertEqual(len(result["open_questions"]), 2)

    def test_prompt_injection_high_and_untrusted(self):
        _, result = run_gate(fixture("prompt-injection.json"))
        self.assertEqual(result["gate"]["status"], "requires_human_review")
        self.assertIn("prompt_injection", {item["id"] for item in result["signals"]})
        self.assertFalse(result["gate"]["authorized_to_execute"])

    def test_prompt_injection_body_not_repeated_in_report(self):
        _, result = run_gate(fixture("prompt-injection.json"))
        self.assertNotIn("Ignore previous instructions", json.dumps(result))

    def test_invalid_domain_blocked(self):
        proc, result = run_gate(fixture("invalid-url.json"))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(result["gate"]["status"], "blocked")

    def test_medium_reliability_escalation(self):
        _, result = run_gate(fixture("medium-webhooks.json"))
        self.assertEqual(result["gate"]["status"], "requires_human_review")
        self.assertEqual(result["gate"]["computed_risk"], "medium")
        self.assertTrue(result["gate"]["risk_escalated"])
        self.assertIn("distributed_reliability", {x["id"] for x in result["signals"]})

    def test_valid_high_non_strict_returns_zero_for_successful_report(self):
        proc, _ = run_gate(fixture("auth-high-risk.json"))
        self.assertEqual(proc.returncode, 0)

    def test_valid_high_strict_returns_one(self):
        proc, result = run_gate(fixture("auth-high-risk.json"), args=("--strict",))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(result["gate"]["status"], "requires_human_review")

    def test_valid_docs_strict_returns_zero(self):
        proc, _ = run_gate(self.good, args=("--strict",))
        self.assertEqual(proc.returncode, 0)

    def test_markdown_report(self):
        proc, text = run_gate(self.good, args=("--format", "markdown"))
        self.assertEqual(proc.returncode, 0)
        self.assertIn("# GitHub Issue Risk Gate", text)
        self.assertIn("ready_for_review", text)
        self.assertIn("Execution permission", text)

    def test_malformed_json_blocked_without_traceback(self):
        proc, result = run_gate(raw='{"issue":')
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(result["gate"]["status"], "blocked")
        self.assertNotIn("Traceback", proc.stderr + proc.stdout)

    def test_oversized_input_fails_closed(self):
        proc, result = run_gate(raw="X" * 65_000)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("maximum size", result["error"])

    def test_missing_analysis_rejected(self):
        invalid = {"issue": self.good["issue"]}
        proc, result = run_gate(invalid)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("needs issue and analysis", result["error"])

    def test_missing_claimed_risk_rejected(self):
        payload = copy.deepcopy(self.good)
        del payload["analysis"]["claimed_risk"]
        proc, _ = run_gate(payload)
        self.assertEqual(proc.returncode, 2)

    def test_unknown_top_level_field_rejected(self):
        payload = copy.deepcopy(self.good)
        payload["do_not_validate"] = True
        proc, _ = run_gate(payload)
        self.assertEqual(proc.returncode, 2)

    def test_unknown_analysis_field_rejected(self):
        payload = copy.deepcopy(self.good)
        payload["analysis"]["approved"] = True
        proc, _ = run_gate(payload)
        self.assertEqual(proc.returncode, 2)

    def test_unknown_test_kind_rejected(self):
        payload = copy.deepcopy(self.good)
        payload["analysis"]["tests"][0]["kind"] = "unsafe"
        proc, _ = run_gate(payload)
        self.assertEqual(proc.returncode, 2)

    def test_unknown_test_field_rejected(self):
        payload = copy.deepcopy(self.good)
        payload["analysis"]["tests"][0]["command"] = "run"
        proc, _ = run_gate(payload)
        self.assertEqual(proc.returncode, 2)

    def test_boolean_issue_number_rejected(self):
        payload = copy.deepcopy(self.good)
        payload["issue"]["number"] = True
        proc, _ = run_gate(payload)
        self.assertEqual(proc.returncode, 2)

    def test_issue_number_url_mismatch_rejected(self):
        payload = copy.deepcopy(self.good)
        payload["issue"]["number"] = 43
        proc, _ = run_gate(payload)
        self.assertEqual(proc.returncode, 2)

    def test_urls_must_use_https_and_no_fragments(self):
        for url in (
            "http://github.com/example-org/sample-service/issues/42",
            "https://github.com/example-org/sample-service/issues/42?foo=bar",
            "https://github.com/example-org/sample-service/issues/42#comments",
            "https://github.com/example-org/sample-service/pull/42",
            "https://github.com:443/example-org/sample-service/issues/42",
            "https://github.com@attacker.example/example-org/sample-service/issues/42",
            "https://127.0.0.1/example-org/sample-service/issues/42",
            "https://github.com/example-org/sample-service/issues/42/../41",
            "https://github.com/example-org/sample-service/issues/42\n",
        ):
            with self.subTest(url=url):
                payload = copy.deepcopy(self.good)
                payload["issue"]["url"] = url
                proc, result = run_gate(payload)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(result["gate"]["status"], "blocked")

    def test_invalid_label_type_rejected(self):
        payload = copy.deepcopy(self.good)
        payload["issue"]["labels"] = [{"name": "docs"}]
        proc, _ = run_gate(payload)
        self.assertEqual(proc.returncode, 2)

    def test_docs_high_risk_not_downgraded(self):
        payload = copy.deepcopy(self.good)
        payload["issue"]["body"] += " Document how to disable MFA for user logins."
        _, result = run_gate(payload)
        self.assertEqual(result["gate"]["computed_risk"], "high")
        self.assertEqual(result["gate"]["status"], "requires_human_review")

    def test_model_cannot_lower_high_floor(self):
        payload = copy.deepcopy(self.good)
        payload["analysis"]["proposed_change"] = "Remove authentication checks for endpoints."
        _, result = run_gate(payload)
        self.assertEqual(result["gate"]["computed_risk"], "high")
        self.assertTrue(result["gate"]["risk_escalated"])

    def test_model_can_raise_conservative_risk(self):
        payload = copy.deepcopy(self.good)
        payload["analysis"]["claimed_risk"] = "high"
        _, result = run_gate(payload)
        self.assertEqual(result["gate"]["computed_risk"], "high")
        self.assertFalse(result["gate"]["risk_escalated"])

    def test_code_change_requires_negative_test(self):
        payload = copy.deepcopy(self.good)
        payload["issue"]["title"] = "Implement a faster list renderer"
        payload["issue"]["labels"] = ["enhancement"]
        payload["analysis"]["tests"] = [{"kind": "positive", "scenario": "Fast render", "expected": "Frame time improves"}]
        _, result = run_gate(payload)
        self.assertEqual(result["gate"]["status"], "needs_clarification")
        self.assertIn("Missing a negative or failure-path test", result["quality_gaps"])

    def test_analysis_questions_prevent_ready(self):
        payload = copy.deepcopy(self.good)
        payload["analysis"]["questions"].append("Has the owner approved the wording?")
        _, result = run_gate(payload)
        self.assertEqual(result["gate"]["status"], "needs_clarification")

    def test_agent_with_no_acceptance_criteria_not_ready(self):
        payload = copy.deepcopy(self.good)
        payload["analysis"]["acceptance_criteria"] = []
        _, result = run_gate(payload)
        self.assertEqual(result["gate"]["status"], "needs_clarification")

    def test_whitespace_only_summary_invalid(self):
        payload = copy.deepcopy(self.good)
        payload["analysis"]["summary"] = "  "
        proc, _ = run_gate(payload)
        self.assertEqual(proc.returncode, 2)

    def test_unicode_input_does_not_crash(self):
        payload = copy.deepcopy(self.good)
        payload["issue"]["body"] += " Einfache Erklärung für Nutzerinnen."
        _, result = run_gate(payload)
        self.assertEqual(result["gate"]["status"], "ready_for_review")

    def test_isolated_temp_script_no_sibling_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            isolated = Path(tmp) / "isolated_gate.py"
            shutil.copyfile(SCRIPT, isolated)
            proc, result = run_gate(self.good, script=isolated)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(result["gate"]["status"], "ready_for_review")
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["isolated_gate.py"])

    def test_invalid_json_null_rejected(self):
        proc, result = run_gate(raw="null")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(result["gate"]["status"], "blocked")

    def test_no_secrets_or_issue_body_in_output(self):
        payload = copy.deepcopy(self.good)
        payload["issue"]["body"] += " SAMPLE-PRIVATE-TEXT-DO-NOT-REPEAT"
        _, result = run_gate(payload)
        self.assertNotIn("SAMPLE-PRIVATE-TEXT-DO-NOT-REPEAT", json.dumps(result))


if __name__ == "__main__":
    unittest.main(verbosity=2)
