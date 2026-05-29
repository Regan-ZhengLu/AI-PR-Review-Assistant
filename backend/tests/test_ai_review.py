from app.ai_review_service import AIReviewClient, AIReviewConfigError, build_fallback_review, normalize_ai_review
from app.analyzer import review_pr


class FakeGitHubClient:
    def fetch_pr_payload(self, url):
        return {
            "ref": {"owner": "example", "repo": "repo", "number": 123},
            "title": "fix login error",
            "body": "Handle empty token",
            "user": "octocat",
            "base": "main",
            "head": "fix-login",
            "changed_files": 1,
            "additions": 8,
            "deletions": 2,
            "files": [
                {
                    "filename": "src/auth/login.py",
                    "status": "modified",
                    "additions": 8,
                    "deletions": 2,
                    "changes": 10,
                    "patch": "+ if token is None:\n+     return None",
                }
            ],
        }


class FakeAIClient:
    def review(self, context):
        assert "fix login error" in context
        return normalize_ai_review(
            {
                "summary": "本 PR 修复登录 token 为空时的处理。",
                "riskLevel": "medium",
                "risks": [
                    {
                        "file": "src/auth/login.py",
                        "line": 12,
                        "severity": "medium",
                        "type": "bug",
                        "description": "需要确认空 token 调用方是否能处理 None。",
                        "suggestion": "补充调用方兼容性测试。",
                        "confidence": "medium",
                    }
                ],
                "suggestions": ["补充 token 为空的单元测试"],
                "mergeRecommendation": "建议补充测试后合并。",
                "confidence": "medium",
            },
            model="fake-model",
            used_ai=True,
        )


class MissingAIClient:
    def review(self, context):
        raise AIReviewConfigError("AI_API_KEY/OPENAI_API_KEY is not configured")


def test_review_pr_returns_ai_contract():
    result = review_pr("https://github.com/example/repo/pull/123", github_client=FakeGitHubClient(), ai_client=FakeAIClient())

    assert result["summary"] == "本 PR 修复登录 token 为空时的处理。"
    assert result["riskLevel"] == "medium"
    assert result["risks"][0]["file"] == "src/auth/login.py"
    assert result["suggestions"] == ["补充 token 为空的单元测试"]
    assert result["mergeRecommendation"] == "建议补充测试后合并。"
    assert result["usedAi"] is True
    assert result["model"] == "fake-model"
    assert result["pr"]["repository"] == "example/repo"
    assert result["riskPreAnalysis"]["overall_level"] in {"Info", "Low", "Medium", "High"}


def test_review_pr_falls_back_when_ai_key_missing():
    result = review_pr("https://github.com/example/repo/pull/123", github_client=FakeGitHubClient(), ai_client=MissingAIClient())

    assert result["usedAi"] is False
    assert result["fallbackReason"] == "AI_API_KEY/OPENAI_API_KEY is not configured"
    assert result["riskLevel"] in {"low", "medium", "high"}
    assert result["mergeRecommendation"]


def test_ai_client_reports_missing_key(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = AIReviewClient(api_key="", model="test-model")

    assert client.is_configured is False


def test_normalize_ai_review_keeps_expected_fields():
    result = normalize_ai_review(
        {
            "summary": "summary",
            "risk_level": "HIGH",
            "risks": [{"filename": "a.py", "severity": "unknown", "confidence": "HIGH"}],
            "suggestions": ["one", 2],
            "merge_recommendation": "do not merge yet",
            "confidence": "LOW",
        },
        model="test-model",
    )

    assert result["riskLevel"] == "high"
    assert result["risks"][0]["file"] == "a.py"
    assert result["risks"][0]["severity"] == "low"
    assert result["risks"][0]["confidence"] == "high"
    assert result["suggestions"] == ["one", "2"]
    assert result["mergeRecommendation"] == "do not merge yet"
    assert result["confidence"] == "low"
    assert result["model"] == "test-model"


def test_build_fallback_review_matches_frontend_contract():
    result = build_fallback_review(
        {"additions": 1, "deletions": 1},
        [{"filename": "a.py", "is_noise": False}],
        {"overall_level": "High", "files": [{"filename": "a.py", "level": "High", "reasons": ["sensitive_path"]}]},
        reason="missing key",
    )

    assert result["riskLevel"] == "high"
    assert result["risks"][0]["severity"] == "high"
    assert result["usedAi"] is False
    assert result["fallbackReason"] == "missing key"
