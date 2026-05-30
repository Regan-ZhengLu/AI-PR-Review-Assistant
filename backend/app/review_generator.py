"""Generate PR summary and review suggestions."""

from __future__ import annotations

from typing import Any


SUMMARY_PROMPT = """你是一个严谨的 AI PR Review 助手。请基于以下 PR 上下文输出结构化代码评审报告。

要求：
1. 先总结 PR 变更目的和影响范围。
2. 标出高风险文件和原因。
3. 给出 Review 建议，分为：确定问题、潜在风险、需要人工确认。
4. 给出测试建议。
5. 生成一段可以复制到 GitHub PR 的 review 总评。
6. 不要编造上下文中不存在的事实；不确定时明确说“需要确认”。

PR 上下文：
{context}
"""


def generate_rule_based_review(pr_payload: dict[str, Any], parsed_files: list[dict[str, Any]], risk_report: dict[str, Any]) -> dict[str, Any]:
    """Fallback review used when no LLM key is configured."""
    active_files = [f for f in parsed_files if not f.get("is_noise")]
    high_files = [f for f in risk_report.get("files", []) if f.get("level") in {"High", "Medium"}]
    suggestions: list[str] = []
    for item in high_files:
        suggestions.append(f"请重点检查 {item['filename']}，风险等级 {item['level']}，原因：{', '.join(item.get('reasons', [])) or '变更较复杂'}。")
    if not suggestions:
        suggestions.append("当前规则层未发现明显高风险信号，建议仍结合业务语义进行人工确认。")
    return {
        "summary": f"该 PR 修改 {len(active_files)} 个有效文件，新增 {pr_payload.get('additions', 0)} 行，删除 {pr_payload.get('deletions', 0)} 行。",
        "risk": risk_report,
        "suggestions": suggestions,
        "test_suggestions": ["针对核心变更补充单元测试或回归测试。", "如涉及接口行为变化，请补充边界条件测试。"],
        "github_review_draft": "本次 PR 已完成自动预审。建议重点关注风险文件、测试覆盖和边界条件；AI 建议仅作为辅助，最终结论请以人工 Review 为准。",
    }


def generate_llm_review(model_client: Any, context: str, max_new_tokens: int = 1800) -> str:
    prompt = SUMMARY_PROMPT.format(context=context)
    return model_client.complete(prompt, max_new_tokens=max_new_tokens)
