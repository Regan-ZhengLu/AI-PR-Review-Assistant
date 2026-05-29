"""Format review results for CLI, API and README demo screenshots."""

from __future__ import annotations

from typing import Any


def format_markdown_report(review: dict[str, Any]) -> str:
    risk = review.get("risk", {})
    lines = [
        "# AI PR Review Report",
        "",
        f"**Overall Risk:** {risk.get('overall_level', 'Unknown')}",
        f"**PR Health Score:** {risk.get('health_score', 'N/A')} / 100",
        "",
        "## PR Summary",
        review.get("summary", ""),
        "",
        "## Risk Files",
    ]
    for file_item in risk.get("files", []):
        lines.append(f"- `{file_item.get('filename')}`: {file_item.get('level')} ({file_item.get('score')}) - {', '.join(file_item.get('reasons', []))}")
    lines.extend(["", "## Review Suggestions"])
    for item in review.get("suggestions", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Test Suggestions"])
    for item in review.get("test_suggestions", []):
        lines.append(f"- {item}")
    lines.extend(["", "## GitHub Review Draft", review.get("github_review_draft", "")])
    return "\n".join(lines) + "\n"
