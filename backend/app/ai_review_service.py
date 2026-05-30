"""AI-powered PR review service.

The service uses an OpenAI-compatible chat completions API so the project can
work with OpenAI, DeepSeek, Moonshot, Qwen-compatible gateways, or any provider
that exposes the same request shape.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib import error, request


AI_REVIEW_SYSTEM_PROMPT = """你是一个资深代码评审工程师。请根据 GitHub Pull Request 的标题、描述和 diff 内容进行代码评审。

请重点关注：
1. 本 PR 的主要变更内容
2. 可能引入 bug 的代码
3. 安全风险
4. 性能风险
5. 可维护性问题
6. 测试覆盖是否不足

请遵守以下约束：
- 只基于提供的 PR 上下文和 diff 判断，不要编造不存在的业务背景。
- 如果风险不确定，请将 confidence 标记为 low，并在描述中说明需要人工确认。
- 风险等级只能使用 high、medium、low。
- mergeRecommendation 用一句话说明是否建议合并。
- 请严格输出 JSON，不要输出 Markdown、解释文字或代码块。
"""


AI_REVIEW_JSON_SCHEMA = """请输出如下 JSON 结构：
{
  "summary": "本 PR 主要修改了...",
  "riskLevel": "high | medium | low",
  "risks": [
    {
      "file": "src/example.ts",
      "line": 42,
      "severity": "high | medium | low",
      "type": "bug | security | performance | maintainability | test",
      "description": "问题说明",
      "suggestion": "修改建议",
      "confidence": "high | medium | low"
    }
  ],
  "suggestions": ["建议补充..."],
  "mergeRecommendation": "建议修改后再合并",
  "confidence": "high | medium | low"
}
"""


class AIReviewConfigError(RuntimeError):
    """Raised when AI review is requested without required configuration."""


class AIReviewClient:
    """Minimal OpenAI-compatible chat completions client."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.environ.get("AI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("AI_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.environ.get("AI_MODEL") or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.model)

    def review(self, context: str) -> dict[str, Any]:
        if not self.is_configured:
            raise AIReviewConfigError("AI_API_KEY/OPENAI_API_KEY is not configured")

        payload = {
            "model": self.model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": AI_REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": f"{AI_REVIEW_JSON_SCHEMA}\n\nPR 上下文如下：\n{context}"},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "diffsense-ai/0.1",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                response_payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"AI API request failed: HTTP {exc.code}: {body_text}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Could not reach AI API: {exc}") from exc

        content = _extract_message_content(response_payload)
        return normalize_ai_review(_parse_json_content(content), model=self.model, used_ai=True)


def _extract_message_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError("AI API returned no choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("AI API returned an empty message")
    return content


def _parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"AI API returned invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("AI API returned JSON that is not an object")
    return parsed


def normalize_ai_review(review: dict[str, Any], model: str | None = None, used_ai: bool = True) -> dict[str, Any]:
    """Coerce provider output into the API contract used by the frontend."""

    risks = review.get("risks") if isinstance(review.get("risks"), list) else []
    normalized_risks: list[dict[str, Any]] = []
    for item in risks:
        if not isinstance(item, dict):
            continue
        normalized_risks.append(
            {
                "file": str(item.get("file") or item.get("filename") or ""),
                "line": item.get("line"),
                "severity": _normalize_level(item.get("severity"), default="low"),
                "type": str(item.get("type") or "maintainability"),
                "description": str(item.get("description") or ""),
                "suggestion": str(item.get("suggestion") or ""),
                "confidence": _normalize_confidence(item.get("confidence")),
            }
        )

    suggestions = review.get("suggestions") if isinstance(review.get("suggestions"), list) else []
    normalized = {
        "summary": str(review.get("summary") or "未生成 PR 总结。"),
        "riskLevel": _normalize_level(review.get("riskLevel") or review.get("risk_level"), default="low"),
        "risks": normalized_risks,
        "suggestions": [str(item) for item in suggestions if str(item).strip()],
        "mergeRecommendation": str(review.get("mergeRecommendation") or review.get("merge_recommendation") or "建议人工确认后再合并。"),
        "confidence": _normalize_confidence(review.get("confidence")),
        "usedAi": used_ai,
    }
    if model:
        normalized["model"] = model
    return normalized


def build_fallback_review(pr_payload: dict[str, Any], parsed_files: list[dict[str, Any]], risk_report: dict[str, Any], reason: str) -> dict[str, Any]:
    """Return a deterministic API-shaped review when no AI key is available."""

    files = [item for item in risk_report.get("files", []) if item.get("level") in {"High", "Medium", "Low"}]
    risks = [
        {
            "file": item.get("filename", ""),
            "line": None,
            "severity": _rule_level_to_api(item.get("level")),
            "type": "maintainability",
            "description": f"规则预分析发现风险信号：{', '.join(item.get('reasons', [])) or '变更较复杂'}。",
            "suggestion": "建议人工重点检查该文件的业务逻辑、边界条件和测试覆盖。",
            "confidence": "medium",
        }
        for item in files
    ]
    if not risks:
        risks = []

    active_files = [item for item in parsed_files if not item.get("is_noise")]
    return {
        "summary": f"该 PR 修改 {len(active_files)} 个有效文件，新增 {pr_payload.get('additions', 0)} 行，删除 {pr_payload.get('deletions', 0)} 行。当前返回规则预分析结果。",
        "riskLevel": _rule_level_to_api(risk_report.get("overall_level")),
        "risks": risks,
        "suggestions": [
            "针对核心变更补充单元测试或回归测试。",
            "如涉及接口行为变化，请补充边界条件测试。",
            "AI 模型未启用时，请将本结果作为预审辅助，并进行人工 Review。",
        ],
        "mergeRecommendation": "建议人工确认风险文件和测试覆盖后再合并。",
        "confidence": "medium",
        "usedAi": False,
        "fallbackReason": reason,
    }


def _normalize_level(value: Any, default: str) -> str:
    level = str(value or default).strip().lower()
    return level if level in {"high", "medium", "low"} else default


def _normalize_confidence(value: Any) -> str:
    confidence = str(value or "medium").strip().lower()
    return confidence if confidence in {"high", "medium", "low"} else "medium"


def _rule_level_to_api(level: Any) -> str:
    mapping = {"High": "high", "Medium": "medium", "Low": "low", "Info": "low", "Ignored": "low"}
    return mapping.get(str(level), "low")
