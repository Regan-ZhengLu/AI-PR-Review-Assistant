# DiffSense AI：AI PR Review 助手

DiffSense AI 是一个面向 GitHub Pull Request 的 AI 代码评审辅助工具。用户输入 GitHub PR 链接后，系统会自动获取 PR 标题、描述和代码变更内容，结合规则预分析与 AI 模型生成 PR 变更总结、风险代码识别、Review 建议和可复制到 GitHub PR 评论区的 Markdown Review。

本项目对应实训营题目三：**AI PR Review 助手**。

## 核心功能

- 支持输入 GitHub Pull Request 链接
- 自动解析 `owner`、`repo` 和 `pull number`
- 自动获取 GitHub PR 元信息和 changed files diff
- 过滤 lock/build/dist/coverage/node_modules 等低价值噪声文件
- 基于规则识别敏感路径、大 diff、异常吞没、疑似 SQL 拼接等风险信号
- 使用 OpenAI-compatible AI 模型生成结构化 Review 结果
- 展示 PR 变更总结、整体风险等级、风险代码列表和 Review 建议
- 支持 AI API Key 缺失时 fallback 到规则预分析结果
- 支持复制 Markdown 格式 Review，方便粘贴到 GitHub PR 评论区
- 提供 Web 页面、Web API 和 CLI 三种使用方式

## 技术栈

### Frontend

- React
- Vite
- TypeScript
- CSS

### Backend

- Python 3.10+
- FastAPI
- Pydantic
- Uvicorn
- Python 标准库 `urllib` 调用 GitHub API 与 OpenAI-compatible API

### External API

- GitHub REST API
- OpenAI-compatible Chat Completions API
  - 可接 OpenAI、DeepSeek、Moonshot、通义千问兼容网关等

### Dev / Test

- pytest
- ruff

## 项目结构

```text
AI-PR-Review-Assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── cli.py                   # CLI 入口
│   │   ├── analyzer.py              # PR 分析流程编排
│   │   ├── github_client.py         # GitHub PR 数据获取
│   │   ├── pr_parser.py             # changed files 解析与噪声过滤
│   │   ├── risk_analyzer.py         # 规则层风险评分
│   │   ├── context_builder.py       # AI Review 上下文构建
│   │   ├── ai_review_service.py     # AI Review 模型调用与结果归一化
│   │   ├── review_generator.py      # 规则 Review 报告生成
│   │   └── report_formatter.py      # CLI Markdown 报告格式化
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Review 页面
│   │   ├── api.ts                   # 前端 API 请求
│   │   ├── formatReviewMarkdown.ts  # Markdown Review 格式化
│   │   ├── RiskBadge.tsx            # 风险等级标签
│   │   ├── types.ts                 # 前端类型定义
│   │   └── styles.css               # 页面样式
│   └── package.json
├── docs/
├── prompt.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## 本地启动

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd AI-PR-Review-Assistant
```

### 2. 创建后端环境

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[web,dev]"
cp .env.example .env
```

### 3. 配置环境变量

编辑 `.env`：

```env
# GitHub token 可选，但推荐配置，避免 GitHub API 限流。
GITHUB_TOKEN=your_github_token

# AI Review 模型配置。
AI_API_KEY=your_ai_api_key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
```

如果使用 DeepSeek、Moonshot、通义千问等 OpenAI-compatible 网关，可将：

```env
AI_BASE_URL=
AI_MODEL=
```

替换为对应服务商提供的地址和模型名。

如果暂时不配置 `AI_API_KEY`，系统仍可运行，但 `/api/review` 会返回规则层 fallback 结果，页面会提示当前为规则预分析结果。

### 4. 一键启动前后端（推荐）

项目提供了一键启动脚本，会自动准备虚拟环境、安装前后端依赖、加载 `.env`、启动后端和前端：

```bash
./scripts/dev.sh
```

启动成功后打开：

```text
http://127.0.0.1:5173
```

按 `Ctrl+C` 可以同时关闭前端和后端。

### 5. 手动启动后端服务

如果你希望分别控制前后端，也可以手动启动：

```bash
uvicorn app.main:app --reload --app-dir backend
```

默认后端地址：

```text
http://127.0.0.1:8000
```

健康检查：

```text
GET http://127.0.0.1:8000/health
```

### 6. 手动启动前端页面

打开新的终端：

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

默认前端地址：

```text
http://127.0.0.1:5173
```

前端 Vite 开发服务器已配置 `/api` 代理到后端 `http://127.0.0.1:8000`。

## 使用方式

### Web 页面

1. 启动后端和前端
2. 打开前端页面
3. 输入公开 GitHub PR 链接，例如：

   ```text
   https://github.com/facebook/react/pull/30872
   ```

4. 点击“开始分析”
5. 查看 PR Summary、Risks、Suggestions 和 Merge Recommendation
6. 点击“复制 Review”或“复制 Markdown”
7. 将 Markdown Review 粘贴到 GitHub PR 评论区

### Web API

#### AI Review 分析接口

```http
POST /api/review
Content-Type: application/json
```

请求：

```json
{
  "prUrl": "https://github.com/owner/repo/pull/123"
}
```

响应示例：

```json
{
  "summary": "本 PR 主要修改了登录错误处理逻辑。",
  "riskLevel": "medium",
  "risks": [
    {
      "file": "src/auth.ts",
      "line": 42,
      "severity": "high",
      "type": "bug",
      "description": "token 为空时仍继续访问 user.id，可能导致运行时报错。",
      "suggestion": "建议在访问 user.id 前增加空值判断。",
      "confidence": "high"
    }
  ],
  "suggestions": [
    "建议补充 token 为空场景的单元测试。"
  ],
  "mergeRecommendation": "建议修改后再合并。",
  "confidence": "medium",
  "usedAi": true,
  "model": "gpt-4o-mini"
}
```

#### 规则分析接口

项目仍保留早期 MVP 的规则分析接口：

```http
POST /api/analyze
Content-Type: application/json
```

请求：

```json
{
  "pr_url": "https://github.com/owner/repo/pull/123"
}
```

### CLI

安装后可以使用 CLI 输出 Markdown 规则预审报告：

```bash
diffsense https://github.com/OWNER/REPO/pull/NUMBER
```

CLI 主要用于本地快速验证和调试；完整 Demo 推荐使用 Web 页面。

## 测试与构建

### 后端测试

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

如果只想做语法检查：

```bash
python3 -m compileall backend/app backend/tests
```

### 前端构建

```bash
npm --prefix frontend install
npm --prefix frontend run build
```

## 模型选择说明

本项目采用 **OpenAI-compatible Chat Completions API** 作为 AI Review 接入方式。

选择原因：

1. **接入成本低**：OpenAI、DeepSeek、Moonshot、通义千问兼容网关等都可以通过类似接口接入。
2. **代码理解能力强**：通用大语言模型具备代码 diff 理解、自然语言总结和结构化输出能力。
3. **便于替换模型**：通过 `AI_BASE_URL` 和 `AI_MODEL` 即可切换不同模型或服务商。
4. **适合两天 MVP**：无需引入复杂 Agent、数据库或 GitHub App，即可完成可演示闭环。

当前 Prompt 要求模型重点关注：

- PR 的主要变更内容
- 可能引入 bug 的代码
- 安全风险
- 性能风险
- 可维护性问题
- 测试覆盖是否不足

同时要求模型：

- 只基于 PR diff 和上下文判断
- 不编造不存在的业务背景
- 不确定时标记低置信度
- 按固定 JSON 格式输出
- 将风险等级限制为 `high`、`medium`、`low`

## 上下文获取方式

系统通过 GitHub REST API 获取 PR 上下文：

```text
GET /repos/{owner}/{repo}/pulls/{pull_number}
GET /repos/{owner}/{repo}/pulls/{pull_number}/files
```

当前传给 AI 的上下文包括：

- 仓库名
- PR 编号
- PR 标题
- PR 描述
- PR 作者
- base/head 分支
- 新增/删除行数
- changed files 列表
- 每个文件的 patch 内容
- 规则层风险预分析结果

为了控制响应速度和 token 成本，当前 MVP 会：

- 过滤 lock/build/dist/coverage/node_modules 等噪声文件
- 每个 patch 截断到合理长度
- 将规则预分析结果作为 AI 的先验提示
- 优先分析有效业务文件，而不是构建产物

## 误报与漏报控制设计

### 降低误报

- Prompt 明确要求模型只基于提供的 diff 和 PR 上下文判断
- 对不确定问题标记 `low confidence`
- 风险项必须包含文件、问题描述、修改建议和置信度
- 规则层先过滤噪声文件，避免 lock file、构建产物干扰 AI 判断
- 页面展示 AI / fallback 状态，提醒用户 AI Review 仅作为辅助

### 降低漏报

- 分析维度覆盖 bug、安全、性能、可维护性和测试覆盖
- 对每个 changed file 提供 patch 上下文
- 规则层提前识别敏感路径、大 diff、异常吞没、疑似 SQL 拼接等稳定信号
- 将规则层风险预分析结果注入 AI 上下文，提示模型重点关注高风险文件
- 输出整体建议和文件级风险点，便于人工 Review 继续追查

## 响应速度和使用体验

当前 MVP 的体验设计重点是：

- 前端只需要输入一个 GitHub PR 链接
- 页面提供 loading 状态，避免用户误以为卡住
- 错误信息直接展示在页面上，便于定位无效链接、GitHub API 错误或 AI API 错误
- 结果按 Summary、Risks、Suggestions、Merge Recommendation 分区展示
- 风险等级使用颜色标签区分，便于快速扫描
- 提供 Markdown 预览和一键复制，方便粘贴到 GitHub PR 评论区
- AI Key 缺失时使用规则 fallback，保证本地 Demo 不会完全不可用

## Demo 视频

视频链接：TODO

Demo 视频建议覆盖：

1. 项目背景：为什么需要 AI PR Review Assistant
2. 页面输入 GitHub PR 链接
3. 系统自动获取 PR 变更内容
4. AI 生成 PR 变更总结
5. AI 识别风险代码
6. AI 生成 Review 建议和合并建议
7. 复制 Markdown Review，并展示可粘贴到 GitHub PR 评论区
8. 简述技术架构、模型选择和误报漏报控制
9. 简述未来扩展方向

## 开发过程说明

本项目按照小步 PR 的方式推进，主要阶段包括：

1. 初始化项目结构与基础 README
2. 实现 GitHub PR URL 解析
3. 获取 GitHub PR 元信息和 changed files
4. 实现规则层 diff 解析、噪声过滤和风险评分
5. 实现 AI Review 分析接口 `/api/review`
6. 实现 React + Vite 前端 Review 页面
7. 支持复制 Markdown 格式 Review 结果
8. 完善 README、Demo 视频和最终提交说明

每个 PR 尽量只做一件事，保证主分支在合并后仍可运行。

## 依赖说明

### 后端依赖

核心逻辑优先使用 Python 标准库实现，降低两天 MVP 的安装复杂度。

可选依赖：

- `fastapi`：Web API 服务
- `uvicorn`：ASGI 开发服务器
- `pydantic`：请求模型校验
- `pytest`：单元测试
- `ruff`：代码规范检查

### 前端依赖

- `react`：页面渲染
- `react-dom`：DOM 挂载
- `vite`：前端开发服务器和构建工具
- `typescript`：类型检查
- `@vitejs/plugin-react`：Vite React 插件
- `@types/react` / `@types/react-dom`：React 类型定义

### 外部服务

- GitHub REST API：获取 PR 元信息和 diff
- OpenAI-compatible AI API：生成 PR Review 结果

## 原创与复用说明

本项目中的以下能力为本次实训作品原创实现：

- GitHub PR URL 解析
- GitHub PR 元信息与 changed files 获取
- PR changed files 解析与噪声过滤
- 风险信号提取与 PR Health Score
- AI Review Prompt 设计
- AI Review 结构化 JSON 输出约束
- `/api/review` 分析接口
- React Review 页面
- Markdown Review 格式化与复制功能
- README 中的产品设计、模型选择、上下文设计和误报漏报控制说明

项目中部分基础能力来自本人此前代码片段，并已在项目中注明用途：

- `backend/app/model_client.py`：由本人此前本地 coding agent 项目的模型适配层迁移，用于后续扩展 Ollama、OpenAI-compatible、Anthropic-compatible 等模型后端。
- `backend/app/config.py`：由本人此前配置加载代码迁移，用于本地 `.env` 配置读取。
- `backend/app/run_store.py`：由本人此前运行记录存储代码迁移，用于后续保存分析运行记录。

本项目未复制他人业务代码，第三方框架和 API 均为公开依赖或公开服务。

## 未来扩展方向

- 支持 GitHub App / Webhook 自动监听 PR 创建事件
- 支持将 Review 结果自动评论到 GitHub PR
- 支持 GitHub inline review comments 行级评论
- 支持安全专项、测试专项、性能专项 Review 模式
- 支持多模型交叉评审，降低单模型误判
- 支持获取完整文件内容、相关测试文件和调用链上下文
- 支持团队自定义 Review 规则
- 支持 Review 历史记录、统计报表和质量评估
- 支持私有仓库和组织级权限配置

## 最终提交检查清单

- [ ] 仓库公开可访问
- [ ] README 包含项目介绍、技术栈、启动方式和环境变量说明
- [ ] README 包含模型选择说明
- [ ] README 包含上下文获取方式
- [ ] README 包含误报与漏报控制设计
- [ ] README 包含依赖与原创说明
- [ ] Demo 视频链接已填写
- [ ] 后端服务可启动
- [ ] 前端服务可启动
- [ ] 输入公开 GitHub PR 链接可以完成分析
- [ ] Markdown Review 可以复制
- [ ] 测试或构建命令已执行并记录结果
