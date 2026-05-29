"""Rule-based PR risk scoring.

This is the deterministic layer used before LLM review. It gives the reviewer
stable signals and helps reduce hallucinated or overly broad suggestions.
"""

from __future__ import annotations

from typing import Any


HINT_WEIGHTS = {
    "sensitive_path": 25,
    "large_diff": 20,
    "todo_or_fixme": 8,
    "possible_swallowed_exception": 18,
    "possible_sql_concatenation": 30,
}


def score_file(change: dict[str, Any]) -> dict[str, Any]:
    score = 0
    if change.get("is_noise"):
        return {"filename": change.get("filename", ""), "score": 0, "level": "Ignored", "reasons": ["noise_file"]}

    changes = int(change.get("changes", 0))
    if changes > 50:
        score += min(20, changes // 20)

    reasons = list(change.get("risk_hints", []))
    for hint in reasons:
        score += HINT_WEIGHTS.get(hint, 0)

    if score >= 45:
        level = "High"
    elif score >= 20:
        level = "Medium"
    elif score > 0:
        level = "Low"
    else:
        level = "Info"
    return {"filename": change.get("filename", ""), "score": min(score, 100), "level": level, "reasons": reasons}


def analyze_pr_risk(parsed_files: list[dict[str, Any]]) -> dict[str, Any]:
    files = [score_file(change) for change in parsed_files]
    active = [item for item in files if item["level"] != "Ignored"]
    max_score = max((item["score"] for item in active), default=0)
    if max_score >= 45:
        overall = "High"
    elif max_score >= 20:
        overall = "Medium"
    elif max_score > 0:
        overall = "Low"
    else:
        overall = "Info"
    health_score = max(0, 100 - max_score)
    return {"overall_level": overall, "health_score": health_score, "files": files}
