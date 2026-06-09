# 网文写作助手 v2.2.0 更新公告

## 版本亮点

v2.2.0 是一次面向“长篇连续创作”的大版本更新：新增 OpenAI Codex CLI 支持，重构 GUI 创作流，并强化 Windows 中文编码兼容性。现在可以在同一套小说项目里自由选择 Claude Code 或 Codex 作为 AI 引擎。

---

## 新增功能

**Claude Code / Codex 双引擎**
- 左侧新增 AI 引擎选择器，支持在 `Claude Code` 与 `Codex` 间切换。
- Codex 模式通过 `codex exec` 在当前小说项目目录内执行写作任务。
- Codex 使用本机 Codex CLI 的现有登录和配置，不在 GUI 中额外保存 API Key。
- 新增 `.agents/skills/novel-write`，为 Codex 提供与 Claude Skill 对齐的写作能力。

**新版长篇工坊界面**
- 新增“工作台”，集中展示总字数、章节数、目标进度、资料完整度和当前 AI 引擎。
- 新增“章节工位”，整合正文编辑、章前检查、规划本章、写新章节、审稿体检、续写和润色。
- 新增“故事地图”，集中查看总纲、卷纲和章节规划。
- 新增“资料库”，集中管理角色、世界观、文风配方和伏笔笔记。
- 新增“数据看板”，展示章节数、总字数、平均章节字数和导出统计。

**章节导航优化**
- 章节工位新增 `上一章` / `下一章` 按钮。
- 第一章自动禁用上一章，最后一章自动禁用下一章。
- 点击后直接加载对应章节正文，减少长篇项目切章成本。

**Codex 诊断**
- AI 编剧室新增 `Codex 诊断` 按钮。
- 可检查 Codex CLI 是否安装、配置文件摘要、项目 `.agents` Skill 是否存在。
- 可辅助定位 `503 Service Unavailable`、`127.0.0.1` 本地 provider 和 Responses API 不兼容问题。

**发布打包**
- 新增 `build_release.py`，统一打包入口。
- `build.bat` 简化为调用构建脚本。
- 打包时同时内置 `.claude/skills` 与 `.agents/skills`。
- 自动清理 `dist/.claude`、`dist/.agents` 和运行设置残留，避免把运行时文件混进发布包。

---

## 问题修复

- 修复 Windows PowerShell 5.1 默认编码读取 UTF-8 中文文件时，AI 编剧室出现乱码的问题。
- Codex 执行环境增加 UTF-8 相关环境变量，降低中文输出乱码概率。
- AI 编剧室显示层加入常见 mojibake 文本修复，尽量恢复已被错误解码的中文输出。
- 修复旧版打包脚本只内置 Claude Skill、Codex 无法识别 `novel-write` 的问题。
- 改进项目打开流程，打开已有项目时自动补齐 Claude/Codex 两套 Skill。

---

## 使用建议

- 如果主要使用 Claude Code：安装并登录 `@anthropic-ai/claude-code` 后，在 GUI 左侧选择 `Claude Code`。
- 如果主要使用 Codex：安装并登录 `@openai/codex@latest` 后，在 GUI 左侧选择 `Codex`。
- 如果使用自定义本地 provider，Codex 需要兼容 OpenAI Responses 接口 `/v1/responses`。
- 长篇自动写作建议按 3-5 章分批执行，例如“从 ch041 写到 ch045，按规划一章 -> 写正文 -> 规划下一章循环”。

---

## 下载方式

前往 [Releases](https://github.com/ShmilyWithme/Shmily_novel_skill/releases) 下载最新版 `网文写作助手.exe`。

---

## 截图

![工作台预览](images/screenshot_1.png)

![章节与写作预览](images/screenshot_2.png)

![AI 编剧室预览](images/screenshot_3.png)

---

**反馈交流**
- GitHub Issues: [提交问题](https://github.com/ShmilyWithme/Shmily_novel_skill/issues)
- QQ: 1943477162
