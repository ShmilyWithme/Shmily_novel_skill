# 网文写作助手

基于 Claude Code Skill / OpenAI Codex Skill 的智能小说创作工具，专为网络文学作者打造。

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![AI](https://img.shields.io/badge/AI-Claude%20Code%20%7C%20Codex-orange)

## 界面预览

> 新版界面围绕“长篇工坊”重新组织，把工作台、章节写作、故事地图、资料库和 AI 编剧室拆成更清晰的创作流水线。

![工作台预览](images/screenshot_1.png)

![章节与写作预览](images/screenshot_2.png)

![AI 编剧室预览](images/screenshot_3.png)

## 最新更新：v2.2.0

- 新增 OpenAI Codex CLI 支持，可在 GUI 左侧切换 `Claude Code` / `Codex`。
- 新增 `.agents/skills/novel-write`，EXE 打包时会同时内置 Claude 与 Codex 两套 Skill。
- 重构主界面为工作台、章节工位、故事地图、资料库、AI 编剧室、日志、数据看板。
- 章节工位新增 `上一章` / `下一章` 快速切换按钮，并根据当前章节自动禁用不可用方向。
- 修复 Windows PowerShell 5.1 读取 UTF-8 中文时导致 AI 编剧室乱码的问题。
- 新增 `Codex 诊断`，用于检查 Codex CLI、登录配置、`.agents` Skill 和本地 provider 状态。
- 新增 `build_release.py`，一键清理运行残留并打包内置 Skill 的单文件 EXE。

完整更新说明见 [RELEASE_v2.2.0.md](RELEASE_v2.2.0.md)。

## 前置条件

### 必须安装

| 软件              | 版本要求 | 说明                                      |
| ----------------- | -------- | ----------------------------------------- |
| **Node.js**       | 18+      | Claude Code CLI / Codex CLI 的运行依赖    |
| **Claude Code CLI 或 Codex CLI** | 最新版 | AI 核心引擎，负责大纲生成、章节撰写等 |

### 安装步骤

**1. 安装 Node.js**

- 前往 [nodejs.org](https://nodejs.org/) 下载 LTS 版本
- 安装后验证：`node --version`

**2. 安装 AI CLI**

可以只安装其中一个，也可以两个都安装，然后在 GUI 左侧"AI 引擎"中切换。

安装 Claude Code CLI：

```bash
npm install -g @anthropic-ai/claude-code
```

安装 OpenAI Codex CLI：

```bash
npm install -g @openai/codex@latest
```

**3. 配置 AI CLI**

Claude Code：
- 首次运行 `claude` 命令，按提示登录 Anthropic 账号
- 需要有效的 Claude API 订阅（Pro 或 Max 计划）

OpenAI Codex：
- 首次运行 `codex login`，按提示登录 ChatGPT / OpenAI 账号
- 在 GUI 中选择 `Codex` 后，会通过 `codex exec` 在小说项目目录内执行写作任务
- Codex 不在 GUI 内单独配置 API，直接读取用户本机 Codex CLI 的现有配置（`~/.codex/config.toml` 和登录信息）
- 如需使用自定义 API / provider，请在 Codex CLI 自己的配置中设置；当前 Codex CLI 需要 provider 支持 OpenAI Responses 接口 `/v1/responses`

Claude 第三方 API 接入：
- 安装 ccswitch：`npm install -g ccswitch`
- 配置第三方 API 密钥（如 OpenRouter、API2D 等）
- 运行 `ccswitch` 切换到第三方 API
- 详细教程参考 [ccswitch 文档](https://github.com/nicepkg/ccswitch)

### 可选依赖（源码运行）

| 软件        | 版本要求 | 说明              |
| ----------- | -------- | ----------------- |
| Python      | 3.8+     | 从源码运行时需要  |
| PyInstaller | 最新版   | 打包成 EXE 时需要 |

---

## 下载安装

### 方式一：下载 EXE（推荐）

前往 [Releases](https://github.com/ShmilyWithme/Shmily_novel_skill/releases) 页面下载最新版本的 `网文写作助手.exe`。

**优点：**

- 单文件运行，无需安装 Python
- 自带 Skill 配置和示例项目
- 双击即可使用

**要求：**

- 已安装 Claude Code CLI 或 Codex CLI
- 已完成对应账号登录

### 方式二：从源码运行

```bash
git clone https://github.com/ShmilyWithme/Shmily_novel_skill.git
cd Shmily_novel_skill
pip install customtkinter
python novel_writer_gui.py
```

---

## 功能特性

### 核心功能

| 功能       | 说明                                 |
| ---------- | ------------------------------------ |
| 大纲生成   | 总大纲、卷大纲、章节梗概，三层细化   |
| 章节撰写   | 3000-5000 字/章，自动遵循文风设定    |
| 人物管理   | 角色设定卡、一致性检查、关系追踪     |
| 世界观设定 | 力量体系、地理环境、社会结构、时间线 |
| 风格控制   | 支持起点、番茄、晋江等平台风格       |
| 审稿润色   | 五维评分、文字打磨、查重             |
| 导出发布   | 合并章节、去除元数据、一键导出       |

### 界面功能

| 功能          | 说明                               |
| ------------- | ---------------------------------- |
| 创作工作台    | 汇总字数、章节、目标进度和资料完整度 |
| 长篇生产线    | 按立项、总纲、章纲、正文、打磨、发布组织操作 |
| 章节工位      | 集成正文编辑、章前检查、续写、审稿和润色 |
| 故事地图      | 集中管理总纲、卷纲和章节规划       |
| 资料库        | 集中管理角色、世界观、文风配方和伏笔笔记 |
| AI 编剧室     | 与 Claude Code / Codex 实时对话执行写作任务 |
| 数据看板      | 查看章节数、总字数、完成进度和导出报告 |
| AI 引擎选择    | 支持 Claude Code / Codex，自主切换 |
| 日志面板      | 独立日志标签页，记录所有操作       |
| 文件修改记录  | 命令执行后显示新增/修改/删除的文件 |
| 浅色/深色主题 | 支持三种主题切换                   |

### 支持的小说类型

| 类型      | 模板                     |
| --------- | ------------------------ |
| 玄幻/仙侠 | 修仙体系、升级流、爽文   |
| 都市/现实 | 商战职场、都市异能、重生 |
| 科幻/未来 | 星际、赛博朋克、末日     |
| 奇幻/魔幻 | 魔法体系、种族设定、冒险 |
| 末世/废土 | 丧尸、生存、废土重建     |

---

## 使用说明

### GUI 操作

1. **新建小说** — 填写项目名称、类型、平台等配置
2. **工作台总览** — 查看字数、章节、进度和资料完整度
3. **生成大纲** — 在"故事地图"或"长篇生产线"中生成故事框架
4. **维护资料库** — 补全角色、世界观、文风配方和伏笔笔记
5. **撰写章节** — 在"章节工位"选择章节，或进入"AI 编剧室"输入命令
6. **导出小说** — 点击"导出可发布全文"，合并所有章节为可发布文件

### 命令行操作

| 命令              | 功能           |
| ----------------- | -------------- |
| `生成大纲`      | 生成故事总大纲 |
| `生成第N卷大纲` | 生成卷级大纲   |
| `规划第N章`     | 生成章节梗概   |
| `写第N章`       | 撰写章节正文   |
| `继续写`        | 续写当前章节   |
| `改写第N章`     | 按指定方向重写 |
| `扩写第N章`     | 扩展章节内容   |
| `审稿`          | 审阅最近章节   |
| `润色`          | 文字打磨       |
| `导出`          | 合并导出全文   |

---

## 项目结构

```
novel_write/
├── novel_writer_gui.py              # GUI 主程序
├── build.bat                        # 打包脚本
├── README.md                        # 项目说明
├── RELEASE_v2.2.0.md                # 最新版本更新公告
├── RELEASE_v2.1.0.md                # 历史版本更新公告
├── .claude/                          # Claude Code Skill
│   └── skills/
│       └── novel-write/
│           ├── SKILL.md             # Skill 入口
│           ├── modules/             # 功能模块
│           │   ├── init-project.md
│           │   ├── outline-generator.md
│           │   ├── chapter-writer.md
│           │   ├── character-manager.md
│           │   ├── worldbuilding.md
│           │   ├── style-control.md
│           │   └── utils/
│           │       ├── consistency-checker.md
│           │       ├── review.md
│           │       ├── stats.md
│           │       └── export.md
│           └── templates/           # 模板文件
│               ├── chapter-template.md
│               ├── character-card-template.md
│               ├── worldbuilding-template.md
│               └── genre-templates/
│                   ├── xuanhuan.md
│                   ├── dushi.md
│                   ├── kehuan.md
│                   ├── qihuan.md
│                   └── moxi.md
├── .agents/                          # Codex Skill
│   └── skills/
│       └── novel-write/
└── dist/                            # 打包输出目录
```

---

## 打包成 EXE

```bash
# 推荐：自动清理残留并打包 Claude/Codex 两套 Skill
build.bat

# 或直接运行 Python 构建脚本
python build_release.py
```

打包完成后，exe 文件在 `dist/` 目录中。发布到 GitHub Release 时只需要上传 `dist/网文写作助手.exe`；EXE 内已包含 Claude 的 `.claude/skills/novel-write` 和 Codex 的 `.agents/skills/novel-write`，用户新建或打开小说项目时会自动释放到项目目录。

---

## 常见问题

### Q: 运行 EXE 提示找不到 Claude Code 或 Codex

A: 需要先安装对应 CLI 并完成登录。Claude 使用 `npm install -g @anthropic-ai/claude-code`，Codex 使用 `npm install -g @openai/codex@latest`。

### Q: 如何切换 Claude / Codex

A: 在左侧"AI 引擎"下拉框中选择 `Claude Code` 或 `Codex`。项目会记住上次选择的引擎。

### Q: GitHub Release 只上传 EXE，别人能直接用吗

A: 可以。EXE 已内置 `.claude/skills/novel-write` 和 `.agents/skills/novel-write` 两套写作 Skill。用户仍需要自行安装并登录 Claude Code CLI 或 Codex CLI，但不需要手动复制 Skill 文件。

### Q: Codex 报 503 Service Unavailable 或 127.0.0.1 连接失败

A: 这通常不是 EXE 缺少 `.agents` Skill，而是当前 Codex CLI 读取到的本机配置或代理不可用。请先在"AI 编剧室"点击 `Codex 诊断`，再检查 `~/.codex/config.toml`、`codex login` 状态和 `base_url` 对应服务是否可访问。

如果你用的是 `cc-switch`，要注意它可能只提供 Claude/Anthropic `Messages` 接口。当前 Codex CLI 需要 OpenAI `Responses` 接口；如果诊断显示 `/v1/messages` 可用但 `/v1/responses` 返回 503，这个代理就不能作为 Codex provider 使用。

### Q: 终端输出没有实时显示

A: 确保使用最新版本的 EXE。Claude Code 已使用 `--output-format stream-json --include-partial-messages --verbose` 输出实时增量；Codex 会显示 CLI 原始实时输出。

### Q: 如何切换深色/浅色主题

A: 在左侧面板底部的主题下拉菜单中选择。

### Q: 如何添加新的小说类型模板

A: 在 `.claude/skills/novel-write/templates/genre-templates/` 和 `.agents/skills/novel-write/templates/genre-templates/` 下同步创建新的 `.md` 文件。

---

## 反馈交流

- GitHub Issues: [提交问题](https://github.com/ShmilyWithme/Shmily_novel_skill/issues)
- QQ: 1943477162
- 邮箱: z2960775@gmail.com

## License

[MIT](LICENSE)
