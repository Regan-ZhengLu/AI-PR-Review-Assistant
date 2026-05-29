# DiffSense AI 持续 PR 计划

| PR | 标题 | 内容 | 验证方式 |
|---|---|---|---|
| 1 | 初始化项目结构与基础文档 | 创建 backend、README、pyproject、PR 模板 | pytest 通过，README 可读 |
| 2 | 迁移模型调用层和配置管理 | 迁移本人 pico 项目的 model/config/run_store | import 正常 |
| 3 | 实现 GitHub PR URL 解析 | 支持解析 owner/repo/pr number | 单元测试 |
| 4 | 接入 GitHub PR 数据获取 | 获取 PR metadata 和 changed files | 使用公开 PR 手测 |
| 5 | 实现 diff 解析和过滤 | 过滤 lock/build/dist 文件 | 单元测试 |
| 6 | 实现风险评分 | High/Medium/Low 和 Health Score | 单元测试 |
| 7 | 实现 Review 报告输出 | Markdown/JSON 输出 | CLI 手测 |
| 8 | 接入 LLM Review | 生成自然语言 Review 建议 | mock + 手测 |
| 9 | 增加 Web API/前端 | 输入 PR URL 展示报告 | demo 手测 |
| 10 | 完善测试和 Demo 文档 | README、截图、视频链接 | 仓库完整复现 |
