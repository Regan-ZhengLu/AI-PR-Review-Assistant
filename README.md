# DiffSense AI：AI PR Review 助手

DiffSense AI 是一个面向 GitHub Pull Request 的 AI 代码评审辅助工具。用户输入 PR 链接后，系统会自动获取 PR 信息和文件变更，进行规则预分析与风险评分，并生成 PR 变更摘要、风险文件列表、Review 建议、测试建议和可复制到 GitHub 的 Review 草稿。

## 1. 项目目标

本项目用于实训营题目三「AI PR Review 助手」。目标是帮助开发者提升 Pull Request Review 的效率与质量，重点覆盖：

- PR 变更总结
- 风险代码识别
- Review 建议生成
- 误报与漏报控制
- 上下文获取与压缩
- 响应速度与使用体验

## 2. 当前 MVP 能力

- 解析 GitHub PR URL
- 获取 PR 基本信息与 changed files
- 解析文件变更并过滤 lock/build/dist 等噪声文件
- 基于规则生成风险评分与 PR Health Score
- 生成 Markdown Review 报告
- 提供 CLI 入口
- 预留 FastAPI Web API 入口

## 3. 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

分析公开 PR：

```bash
diffsense https://github.com/OWNER/REPO/pull/NUMBER
```

运行测试：

```bash
pip install -e ".[dev]"
pytest
```

启动 Web API（可选）：

```bash
pip install -e ".[web]"
uvicorn app.main:app --reload --app-dir backend
```

## 4. 系统架构

```text
GitHub PR URL
  ↓
github_client.py：获取 PR 元数据和文件 patch
  ↓
pr_parser.py：解析变更、过滤噪声文件、提取风险信号
  ↓
risk_analyzer.py：规则层风险评分与 PR Health Score
  ↓
context_builder.py：构建紧凑上下文，供后续 LLM 使用
  ↓
review_generator.py：生成摘要、建议、测试建议、评论草稿
  ↓
report_formatter.py：输出 Markdown / JSON / API 响应
```

## 5. 模型选择设计

当前 MVP 先使用确定性的规则层完成风险预分析，避免模型不稳定导致误报。后续将接入项目已有的模型调用适配层，采用「规则预分析 + LLM 深度 Review」的混合方案：

- 规则层：识别敏感路径、大 diff、异常吞没、疑似 SQL 拼接、噪声文件等稳定信号。
- LLM 层：结合 PR 描述、diff、风险预分析和相关上下文生成语义级 Review 建议。
- 输出层：将建议分为「确定问题」「潜在风险」「需要人工确认」，降低误报影响。

## 6. 上下文获取方式

MVP 上下文包括：

- PR 标题与描述
- base/head 分支
- 文件变更统计
- changed files patch
- 规则层风险预分析结果

后续计划扩展：

- 获取完整变更文件内容
- 提取被修改函数上下文
- 查找相关测试文件
- 分析 import / 调用关系
- 接入仓库历史提交和已有 review comments

## 7. 历史代码复用说明

本项目部分基础能力复用了本人此前开发的 `pico` 本地 coding agent 项目，主要包括：

- `backend/app/model_client.py`：由原 `pico/models.py` 迁移，用于后续接入 Ollama、OpenAI-compatible、Anthropic-compatible、DeepSeek 等模型后端。
- `backend/app/config.py`：由原 `pico/config.py` 迁移，用于加载本地 `.env` 配置。
- `backend/app/run_store.py`：由原 `pico/run_store.py` 迁移，用于后续保存分析运行记录。

本次实训作品新增原创部分包括：

- GitHub PR URL 解析与 PR 数据获取
- PR changed files 解析与噪声过滤
- 风险信号提取与 PR Health Score
- PR Review 报告格式化
- AI PR Review 助手的模块化架构设计
- 后续 Web/API 交互与 Demo 展示

## 8. 依赖说明

当前核心 MVP 使用 Python 标准库实现 GitHub API 请求和规则分析。可选依赖：

- `pytest`：测试
- `ruff`：代码规范检查
- `fastapi` / `uvicorn` / `pydantic`：Web API 服务

如后续接入具体大模型 SDK 或前端框架，将在此处继续补充依赖与原创功能说明。

## 9. PR 开发计划

建议按照以下 Pull Request 持续开发，避免临尾突击提交：

1. 初始化项目结构与基础文档
2. 迁移模型调用层和配置管理
3. 实现 GitHub PR URL 解析
4. 接入 GitHub PR 基础信息与 changed files 获取
5. 实现 diff 解析和噪声文件过滤
6. 实现规则层风险评分
7. 实现 Review 报告格式化
8. 接入 LLM 生成 PR 摘要与建议
9. 增加 Web API 或前端页面
10. 增加 Demo 样例、测试与 README 截图

## 10. 未来扩展方向

- 支持 GitHub App / Webhook 自动触发
- 支持 inline review comments
- 支持安全专项、测试专项、性能专项 Review 模式
- 支持上下文检索和调用链分析
- 支持团队级 Review 规则配置
- 支持多模型对比和 Review 质量评估

## 11. Demo 视频

待录制后将视频链接放在这里。
