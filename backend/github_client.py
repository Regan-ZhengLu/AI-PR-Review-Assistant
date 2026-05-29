"""GitHub Pull Request data fetcher.

MVP goal:
- parse a GitHub PR URL
- fetch PR metadata
- fetch changed files and patches

This module intentionally uses the standard library first, so the project can
run with fewer dependencies during the early assessment stage.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import os
import re
from typing import Any
from urllib import error, request


PR_URL_RE = re.compile(r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)(?:[/?#].*)?$")


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


def parse_pr_url(url: str) -> PullRequestRef:
    """Parse a GitHub PR URL into owner/repo/number."""
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError("Invalid GitHub PR URL. Expected https://github.com/{owner}/{repo}/pull/{number}")
    return PullRequestRef(
        owner=match.group("owner"),
        repo=match.group("repo"),
        number=int(match.group("number")),
    )


class GitHubClient:
    """Small GitHub REST API client for PR review analysis."""

    def __init__(self, token: str | None = None, api_base: str = "https://api.github.com", timeout: int = 30):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def _get_json(self, path: str) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "diffsense-ai/0.1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = request.Request(self.api_base + path, headers=headers, method="GET")
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API request failed: HTTP {exc.code}: {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Could not reach GitHub API: {exc}") from exc

    def get_pull_request(self, ref: PullRequestRef) -> dict[str, Any]:
        return self._get_json(f"/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}")

    def get_pull_request_files(self, ref: PullRequestRef) -> list[dict[str, Any]]:
        # MVP: fetch first page. Later PR can add pagination.
        return self._get_json(f"/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}/files?per_page=100")

    def fetch_pr_payload(self, url: str) -> dict[str, Any]:
        ref = parse_pr_url(url)
        pr = self.get_pull_request(ref)
        files = self.get_pull_request_files(ref)
        return {
            "ref": asdict(ref),
            "title": pr.get("title", ""),
            "body": pr.get("body", ""),
            "user": (pr.get("user") or {}).get("login", ""),
            "base": (pr.get("base") or {}).get("ref", ""),
            "head": (pr.get("head") or {}).get("ref", ""),
            "changed_files": pr.get("changed_files", len(files)),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "files": files,
        }
