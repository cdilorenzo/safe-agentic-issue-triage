#!/usr/bin/env python3
"""Deterministic, read-only GitHub issue triage gate.

Single-file, Python standard-library-only runner suitable for Agensi's
isolated temporary-script execution model. It does not access the network,
read environment variables, invoke programs, or write files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

VERSION = "1.0.0"
MAX_BYTES = 64_000
RISK_RANK = {"low": 0, "medium": 1, "high": 2}
VALID_TEST_KINDS = {
    "positive", "negative", "security", "regression", "integration",
    "documentation", "manual",
}
ISSUE_KEYS = {"title", "body", "url", "number", "labels"}
ANALYSIS_KEYS = {
    "summary", "proposed_change", "acceptance_criteria", "tests",
    "questions", "claimed_risk", "reasoning",
}
TEST_KEYS = {"kind", "scenario", "expected"}
GH_PATH = re.compile(
    r"^/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38})?)/([A-Za-z0-9_.-]{1,100})/issues/([1-9][0-9]{0,9})$"
)

# Rules inspect untrusted issue text and the agent's proposed change.
# They are conservative indicators, not proof of a vulnerability.
RULES = (
    ("prompt_injection", "high", r"\bignore\s+(?:all\s+)?(?:previous|prior|system|developer)\s+instructions\b|\b(?:reveal|print|dump)\s+(?:the\s+)?(?:system\s+prompt|secrets?|credentials?|env(?:ironment)?\s+variables?)\b|\byou\s+are\s+now\s+(?:a|the)\b|\bbypass\s+(?:your\s+)?(?:safety|guardrails|instructions)\b", "Possible untrusted instructions embedded in issue text"),
    ("auth_identity", "high", r"\b(?:mfa|2fa|oauth|sso|authentication|authorization|authorisation|rbac|jwt|login|logins|sign[ -]?in|passwords?|permissions?|access[ -]?tokens?|refresh[ -]?tokens?|role[ -]?based access)\b", "Authentication, access control or identity affected"),
    ("secret_handling", "high", r"\b(?:api[ -]?keys?|private[ -]?keys?|secrets?|credentials?|credential[ -]?store|token[ -]?rotation|key[ -]?management|encryption[ -]?keys?)\b", "Secrets or credential handling affected"),
    ("bypass_control", "high", r"\b(?:disable|bypass|skip|remove|turn off|circumvent)\b.{0,50}\b(?:mfa|2fa|authentication|authorization|authorisation|access control|security|approval|audit|verification|rate limiting)\b", "Request may weaken a protective control"),
    ("destructive_change", "high", r"\b(?:drop\s+table|truncate\s+table|purge\s+(?:all\s+)?data|hard[ -]?delete|irreversible\s+deletion|delete\s+(?:all\s+)?(?:users?|accounts?|records?|customer\s+data)|wipe\s+(?:the\s+)?database)\b", "Potentially destructive operation"),
    ("sensitive_data", "high", r"\b(?:personally\s+identifiable|personal\s+data|patient\s+data|health\s+records?|medical\s+records?|pii|gdpr|hipaa|credit\s+card\s+data)\b", "Personal or regulated data affected"),
    ("money_flow", "high", r"\b(?:payments?|payouts?|billing|chargebacks?|credit\s+cards?|invoic(?:e|ing)|bank\s+transfers?)\b", "Financial transaction logic affected"),
    ("live_system", "high", r"\b(?:production\s+database|live\s+customer\s+traffic|deploy\s+to\s+production|production\s+credentials?|prod[ -]?only\s+data)\b", "Live or production system change"),
    ("data_migration", "medium", r"\b(?:database\s+migration|schema\s+migration|data\s+migration|backfill|schema\s+change|transaction\s+isolation)\b", "Persistent data or migration impact"),
    ("distributed_reliability", "medium", r"\b(?:race\s+conditions?|concurren(?:cy|t)|dead[ -]?letter|message\s+queue|idempotenc[ey]|retry\s+polic(?:y|ies)|cache\s+invalidation|webhooks?)\b", "Distributed systems or reliability impact"),
    ("api_contract", "medium", r"\b(?:public\s+api|breaking\s+api|api\s+endpoint|rate[ -]?limit(?:ing|s)?|backward[ -]?compatib(?:le|ility))\b", "External API contract or compatibility impact"),
)
AMBIGUITY = re.compile(
    r"\b(?:tbd|not\s+sure|figure\s+it\s+out|somehow|make\s+it\s+better|make\s+it\s+faster|asap|details\s+later)\b",
    re.IGNORECASE,
)


class ContractError(Exception):
    """Input contract violation; do not include user-provided text in errors."""


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _dict(value: object, path: str, keys: set[str]) -> dict:
    _assert(isinstance(value, dict), f"{path} must be a JSON object")
    unexpected = set(value) - keys
    _assert(not unexpected, f"{path} contains unsupported fields")
    return value


def _str(value: object, path: str, max_len: int, *, empty_ok: bool = False) -> str:
    _assert(isinstance(value, str), f"{path} must be a string")
    value = value.strip()
    _assert(len(value) <= max_len, f"{path} exceeds its size limit")
    _assert(empty_ok or bool(value), f"{path} must not be empty")
    return value


def _strings(value: object, path: str, cap: int, max_len: int) -> list[str]:
    _assert(isinstance(value, list), f"{path} must be an array")
    _assert(len(value) <= cap, f"{path} contains too many entries")
    return [_str(entry, f"{path}[{index}]", max_len) for index, entry in enumerate(value)]


def _validate_github_url(value: str) -> str:
    _assert(all(ord(char) >= 33 for char in value), "issue.url contains unsafe whitespace or control characters")
    try:
        parts = urlsplit(value)
        _assert(parts.scheme == "https" and parts.netloc == "github.com", "issue.url must use https://github.com")
        _assert(not parts.query and not parts.fragment and not parts.username and not parts.password,
                "issue.url cannot include credentials, query parameters or fragments")
        _assert(bool(GH_PATH.fullmatch(parts.path)), "issue.url must target /owner/repo/issues/NUMBER")
    except ValueError as exc:
        raise ContractError("issue.url is malformed") from exc
    return value


def validate(payload: object) -> tuple[dict, dict]:
    top = _dict(payload, "input", {"issue", "analysis"})
    _assert("issue" in top and "analysis" in top, "input needs issue and analysis")
    issue = _dict(top["issue"], "issue", ISSUE_KEYS)
    analysis = _dict(top["analysis"], "analysis", ANALYSIS_KEYS)
    _assert(ANALYSIS_KEYS.issubset(analysis), "analysis is missing required fields")
    _assert("title" in issue and "body" in issue, "issue needs title and body")
    normalized_issue = {
        "title": _str(issue["title"], "issue.title", 300),
        "body": _str(issue["body"], "issue.body", 20_000, empty_ok=True),
        "labels": _strings(issue.get("labels", []), "issue.labels", 20, 80),
    }
    if "url" in issue:
        _assert(isinstance(issue["url"], str) and issue["url"] == issue["url"].strip(),
                "issue.url must not contain surrounding whitespace")
        normalized_issue["url"] = _validate_github_url(_str(issue["url"], "issue.url", 240))
    if "number" in issue:
        _assert(type(issue["number"]) is int and 0 < issue["number"] <= 9_999_999_999,
                "issue.number must be a positive integer")
        normalized_issue["number"] = issue["number"]
        if "url" in issue:
            match = GH_PATH.fullmatch(urlsplit(issue["url"]).path)
            _assert(match is not None and int(match.group(3)) == issue["number"],
                    "issue.number must match issue.url")
    normalized_analysis = {
        "summary": _str(analysis["summary"], "analysis.summary", 1200),
        "proposed_change": _str(analysis["proposed_change"], "analysis.proposed_change", 1200),
        "reasoning": _str(analysis["reasoning"], "analysis.reasoning", 1200),
        "acceptance_criteria": _strings(analysis["acceptance_criteria"], "analysis.acceptance_criteria", 12, 280),
        "questions": _strings(analysis["questions"], "analysis.questions", 10, 280),
    }
    claimed = _str(analysis["claimed_risk"], "analysis.claimed_risk", 10)
    _assert(claimed in RISK_RANK, "analysis.claimed_risk must be low, medium or high")
    normalized_analysis["claimed_risk"] = claimed
    _assert(isinstance(analysis["tests"], list) and len(analysis["tests"]) <= 16,
            "analysis.tests must be an array of up to 16 tests")
    tests = []
    for index, item in enumerate(analysis["tests"]):
        test = _dict(item, f"analysis.tests[{index}]", TEST_KEYS)
        _assert(TEST_KEYS.issubset(test), "each test needs kind, scenario and expected")
        kind = _str(test["kind"], "test.kind", 20)
        _assert(kind in VALID_TEST_KINDS, "test.kind is not recognized")
        tests.append({
            "kind": kind,
            "scenario": _str(test["scenario"], "test.scenario", 300),
            "expected": _str(test["expected"], "test.expected", 300),
        })
    normalized_analysis["tests"] = tests
    return normalized_issue, normalized_analysis


def _docs_only(issue: dict) -> bool:
    title = issue["title"].lower()
    labels = {label.lower() for label in issue["labels"]}
    return (
        title.startswith(("docs:", "doc:", "documentation:", "readme:", "document ", "update docs", "fix docs"))
        or bool(labels & {"docs", "documentation", "docs-only"})
    )


def classify(issue: dict, analysis: dict) -> dict:
    """Classify independent of agent's risk claim; require manual signoff."""
    doc_only = _docs_only(issue)
    risk_texts = (
        ("issue.title", issue["title"]),
        ("issue.body", issue["body"]),
        ("analysis.proposed_change", analysis["proposed_change"]),
    )
    signals: list[dict] = []
    observed: set[str] = set()
    for rule_id, severity, pattern, description in RULES:
        for location, content in risk_texts:
            if re.search(pattern, content, re.IGNORECASE):
                if doc_only and severity == "medium":
                    continue  # Documentation-only API mentions are not runtime changes.
                if rule_id not in observed:
                    signals.append({
                        "id": rule_id,
                        "severity": severity,
                        "location": location,
                        "description": description,
                    })
                    observed.add(rule_id)
                break

    floor = max((RISK_RANK[s["severity"]] for s in signals), default=0)
    claim = RISK_RANK[analysis["claimed_risk"]]
    computed_risk = next(name for name, rank in RISK_RANK.items() if rank == max(floor, claim))
    escalated = floor > claim
    quality_gaps: list[str] = []
    if not analysis["acceptance_criteria"]:
        quality_gaps.append("Missing explicit acceptance criteria")
    if not analysis["tests"]:
        quality_gaps.append("Missing proposed tests")
    kinds = {test["kind"] for test in analysis["tests"]}
    if not doc_only:
        if "positive" not in kinds and "integration" not in kinds:
            quality_gaps.append("Missing a positive or integration test")
        if "negative" not in kinds:
            quality_gaps.append("Missing a negative or failure-path test")
    elif "documentation" not in kinds and "manual" not in kinds:
        quality_gaps.append("Missing documentation verification test")
    if computed_risk == "high" and "security" not in kinds:
        quality_gaps.append("Security-sensitive change lacks a security test")
    if len(issue["body"].strip()) < 35 and not doc_only:
        quality_gaps.append("Issue description is too short to establish scope")
    if AMBIGUITY.search(issue["title"] + " " + issue["body"]):
        quality_gaps.append("Issue contains unresolved or vague requirements")
    if escalated:
        quality_gaps.append("Agent understated a risk detected by independent rules")

    # Human review is requested, never granted, by this script.
    if any(s["id"] == "prompt_injection" for s in signals):
        status = "requires_human_review"
        reason = "Untrusted prompt-like instructions detected in issue content"
    elif computed_risk == "high":
        status = "requires_human_review"
        reason = "Sensitive change requires specialist review"
    elif computed_risk == "medium":
        status = "requires_human_review"
        reason = "Medium-risk change requires manual signoff"
    elif analysis["questions"] or quality_gaps:
        status = "needs_clarification"
        reason = "Open questions or missing verification evidence"
    else:
        status = "ready_for_review"
        reason = "No rule-based blockers found; independent human review still applies"

    return {
        "version": VERSION,
        "issue_ref": issue.get("url") or (f"#{issue['number']}" if "number" in issue else "pasted-issue"),
        "gate": {
            "status": status,
            "computed_risk": computed_risk,
            "agent_claimed_risk": analysis["claimed_risk"],
            "risk_escalated": escalated,
            "human_signoff_required": True,
            "authorized_to_execute": False,
            "reason": reason,
        },
        "signals": signals,
        "quality_gaps": quality_gaps,
        "open_questions": analysis["questions"],
        "proposal": {
            "summary": analysis["summary"],
            "change": analysis["proposed_change"],
            "acceptance_criteria": analysis["acceptance_criteria"],
            "tests": analysis["tests"],
            "reasoning": analysis["reasoning"],
        },
        "limitations": [
            "Risk patterns are heuristic; absence of a match is not evidence of safety.",
            "No code, runtime behavior or repository architecture was inspected by this gate.",
            "The gate does not verify the issue content against GitHub or authorize changes.",
        ],
    }


def markdown(result: dict) -> str:
    if "error" in result:
        return "# Issue Risk Gate — blocked\n\n" + result["error"] + "\n"
    gate = result["gate"]
    lines = [
        "# GitHub Issue Risk Gate — review draft", "",
        f"**Reference:** `{result['issue_ref']}`",
        f"**Status:** `{gate['status']}`",
        f"**Independent risk level:** `{gate['computed_risk']}`",
        f"**Agent's claim:** `{gate['agent_claimed_risk']}`",
        f"**Escalated:** {'yes' if gate['risk_escalated'] else 'no'}",
        "**Execution permission:** none — human signoff required", "",
        f"**Why:** {gate['reason']}", "", "## AI proposal (untrusted draft)",
        "", result["proposal"]["summary"], "",
        f"**Proposed change:** {result['proposal']['change']}", "",
        "### Acceptance criteria",
    ]
    lines += [f"- {value}" for value in result["proposal"]["acceptance_criteria"]] or ["- Not provided"]
    lines += ["", "### Proposed tests"]
    for test in result["proposal"]["tests"]:
        lines.append(f"- **{test['kind']}:** {test['scenario']} — expected: {test['expected']}")
    if not result["proposal"]["tests"]:
        lines.append("- Not provided")
    lines += ["", "## Independent risk signals"]
    for signal in result["signals"]:
        lines.append(f"- **{signal['severity']} / {signal['id']}:** {signal['description']} ({signal['location']})")
    if not result["signals"]:
        lines.append("- No heuristic pattern matched; this does not prove safety")
    lines += ["", "## Quality gaps and clarification"]
    lines += [f"- {item}" for item in result["quality_gaps"]] or ["- None detected by rules"]
    lines += [f"- Open question: {item}" for item in result["open_questions"]]
    lines += ["", "## Boundaries"]
    lines += [f"- {item}" for item in result["limitations"]]
    return "\n".join(lines) + "\n"


def _load_input(path: str) -> object:
    if path == "-":
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    else:
        # The caller explicitly identifies the input file; no directory traversal
        # or hidden discovery is performed by the script.
        file = Path(path)
        if not file.is_file():
            raise ContractError("input file not found")
        if file.stat().st_size > MAX_BYTES:
            raise ContractError("input exceeds maximum size")
        raw = file.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ContractError("input exceeds maximum size")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("input must be valid UTF-8 JSON") from exc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only independent risk gate for AI GitHub issue triage")
    parser.add_argument("--input", default="-", help="JSON input path or '-' for stdin (default)")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--strict", action="store_true", help="Return nonzero unless status is ready_for_review")
    args = parser.parse_args(argv)
    try:
        issue, analysis = validate(_load_input(args.input))
        result = classify(issue, analysis)
    except (ContractError, OSError) as exc:
        result = {
            "version": VERSION,
            "error": str(exc) if isinstance(exc, ContractError) else "Cannot read input file",
            "gate": {"status": "blocked", "authorized_to_execute": False},
        }
        print(json.dumps(result, indent=2) if args.format == "json" else markdown(result))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.format == "json" else markdown(result))
    return 0 if not args.strict or result["gate"]["status"] == "ready_for_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
