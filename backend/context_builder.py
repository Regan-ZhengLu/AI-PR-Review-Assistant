"""Build compact context for PR review prompts.

This file is the PR-review-oriented successor of the original pico context
manager idea. It deliberately keeps the context small for MVP speed.
"""

from __future__ import annotations

from typing import Any


def build_review_context(pr_payload: dict[str, Any], parsed_files: list[dict[str, Any]], risk_report: dict[str, Any]) -> str:
    lines: list[str] = []
    ref = pr_payload.get("ref", {})
    lines.append(f"Repository: {ref.get('owner')}/{ref.get('repo')}")
    lines.append(f"PR: #{ref.get('number')} {pr_payload.get('title', '')}")
    lines.append(f"Author: {pr_payload.get('user', '')}")
    lines.append(f"Base -> Head: {pr_payload.get('base', '')} -> {pr_payload.get('head', '')}")
    lines.append(f"Stats: +{pr_payload.get('additions', 0)} -{pr_payload.get('deletions', 0)}, files={pr_payload.get('changed_files', 0)}")
    if pr_payload.get("body"):
        lines.append("\nPR description:")
        lines.append(str(pr_payload.get("body", ""))[:2000])
    lines.append("\nRisk pre-analysis:")
    lines.append(str(risk_report))
    lines.append("\nChanged files and patches:")
    for change in parsed_files:
        if change.get("is_noise"):
            continue
        lines.append(f"\n--- {change.get('filename')} ({change.get('status')}, +{change.get('additions')} -{change.get('deletions')}) ---")
        patch = change.get("patch", "") or ""
        lines.append(patch[:4000])
    return "\n".join(lines)
