from app.github_client import parse_pr_url
from app.pr_parser import parse_changed_files
from app.risk_analyzer import analyze_pr_risk


def test_parse_pr_url():
    ref = parse_pr_url("https://github.com/example/repo/pull/123")
    assert ref.owner == "example"
    assert ref.repo == "repo"
    assert ref.number == 123


def test_noise_filter_and_risk():
    parsed = parse_changed_files([
        {"filename": "package-lock.json", "status": "modified", "additions": 1, "deletions": 1, "changes": 2, "patch": ""},
        {"filename": "src/auth/login.py", "status": "modified", "additions": 80, "deletions": 10, "changes": 90, "patch": "+ except Exception:\n+     pass"},
    ])
    report = analyze_pr_risk(parsed)
    assert parsed[0]["is_noise"] is True
    assert report["overall_level"] in {"Medium", "High"}
