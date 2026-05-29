"""End-to-end PR analysis pipeline."""

from __future__ import annotations

from typing import Any

from .ai_review_service import AIReviewClient, AIReviewConfigError, build_fallback_review
from .github_client import GitHubClient
from .pr_parser import parse_changed_files
from .risk_analyzer import analyze_pr_risk
from .context_builder import build_review_context
from .review_generator import generate_rule_based_review


def analyze_pr(url: str, github_client: GitHubClient | None = None) -> dict[str, Any]:
    client = github_client or GitHubClient()
    pr_payload = client.fetch_pr_payload(url)
    parsed_files = parse_changed_files(pr_payload.get("files", []))
    risk_report = analyze_pr_risk(parsed_files)
    # CLI keeps the deterministic report format for stable local output.
    _context = build_review_context(pr_payload, parsed_files, risk_report)
    return generate_rule_based_review(pr_payload, parsed_files, risk_report)


def review_pr(
    url: str,
    github_client: GitHubClient | None = None,
    ai_client: AIReviewClient | None = None,
    allow_fallback: bool = True,
) -> dict[str, Any]:
    """Analyze a PR and return the frontend-facing AI review contract."""

    client = github_client or GitHubClient()
    pr_payload = client.fetch_pr_payload(url)
    parsed_files = parse_changed_files(pr_payload.get("files", []))
    risk_report = analyze_pr_risk(parsed_files)
    context = build_review_context(pr_payload, parsed_files, risk_report)
    reviewer = ai_client or AIReviewClient()

    try:
        review = reviewer.review(context)
    except AIReviewConfigError as exc:
        if not allow_fallback:
            raise
        review = build_fallback_review(pr_payload, parsed_files, risk_report, reason=str(exc))

    review["pr"] = {
        "title": pr_payload.get("title", ""),
        "author": pr_payload.get("user", ""),
        "repository": _format_repository(pr_payload.get("ref", {})),
        "pullNumber": (pr_payload.get("ref", {}) or {}).get("number"),
        "changedFiles": pr_payload.get("changed_files", len(parsed_files)),
        "additions": pr_payload.get("additions", 0),
        "deletions": pr_payload.get("deletions", 0),
    }
    review["riskPreAnalysis"] = risk_report
    return review


def _format_repository(ref: dict[str, Any]) -> str:
    owner = ref.get("owner", "")
    repo = ref.get("repo", "")
    return f"{owner}/{repo}" if owner and repo else ""
