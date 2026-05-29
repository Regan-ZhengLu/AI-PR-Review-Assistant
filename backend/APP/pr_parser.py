"""Pull Request diff parser and noise filter."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import PurePosixPath
from typing import Any


IGNORED_FILENAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
}
IGNORED_DIR_PARTS = {"dist", "build", "coverage", ".next", ".nuxt", "node_modules"}
IGNORED_SUFFIXES = {".min.js", ".map"}


@dataclass
class ParsedFileChange:
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str
    is_noise: bool
    risk_hints: list[str]


def is_noise_file(filename: str) -> bool:
    path = PurePosixPath(filename)
    if path.name in IGNORED_FILENAMES:
        return True
    if any(part in IGNORED_DIR_PARTS for part in path.parts):
        return True
    return any(filename.endswith(suffix) for suffix in IGNORED_SUFFIXES)


def build_risk_hints(file_change: dict[str, Any]) -> list[str]:
    filename = file_change.get("filename", "")
    patch = file_change.get("patch", "") or ""
    hints: list[str] = []
    lowered = filename.lower()
    sensitive_words = ["auth", "login", "token", "permission", "payment", "billing", "database", "migration", "config", "secret"]
    if any(word in lowered for word in sensitive_words):
        hints.append("sensitive_path")
    if file_change.get("changes", 0) >= 200:
        hints.append("large_diff")
    if "TODO" in patch or "FIXME" in patch:
        hints.append("todo_or_fixme")
    if "except" in patch and "pass" in patch:
        hints.append("possible_swallowed_exception")
    if "SELECT " in patch.upper() and "+" in patch:
        hints.append("possible_sql_concatenation")
    return hints


def parse_changed_files(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for item in files:
        parsed_item = ParsedFileChange(
            filename=item.get("filename", ""),
            status=item.get("status", ""),
            additions=int(item.get("additions", 0)),
            deletions=int(item.get("deletions", 0)),
            changes=int(item.get("changes", 0)),
            patch=item.get("patch", "") or "",
            is_noise=is_noise_file(item.get("filename", "")),
            risk_hints=build_risk_hints(item),
        )
        parsed.append(asdict(parsed_item))
    return parsed
