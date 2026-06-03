# 网文写作助手

基于 Claude Code Skill 的智能小说创作工具，专为网络文学作者打造。

## 前置条件

### 必须安装

| 软件                      | 版本要求 | 说明                                  |
| ------------------------- | -------- | ------------------------------------- |
| **Claude Code CLI** | 无       | AI 核心引擎，负责大纲生成、章节撰写等 |
| **Node.js**         | 18+      | Claude Code CLI 的运行依赖            |

### 安装步骤

**1. 安装 Node.js**

- 前往 [nodejs.org](https://nodejs.org/) 下载 LTS 版本
- 安装后验证：`node --version`

**2. 安装 Claude Code CLI**

```bash
npm install -g @anthropic-ai/claude-code
```

**3. 配置 Claude Code**

**方式 A：官方账号（推荐）**
- 首次运行 `claude` 命令，按提示登录 Anthropic 账号
- 需要有效的 Claude API 订阅（Pro 或 Max 计划）

**方式 B：使用 ccswitch 接入第三方 API**
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

- 已安装 Claude Code CLI
- 已配置 Anthropic 账号

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
| 聊天式终端    | 合并命令和回复，像聊天一样操作     |
| 实时输出      | AI 响应实时显示，无缓冲延迟        |
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
2. **生成大纲** — 点击"生成总大纲"，AI 自动生成故事框架
3. **撰写章节** — 选择章节，点击"写章节"或在终端输入命令
4. **导出小说** — 点击"导出小说"，合并所有章节为可发布文件

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
├── RELEASE_v2.0.md                  # 版本更新公告
├── .claude/
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
└── dist/                            # 打包输出目录
```

---

## 打包成 EXE

```bash
# 安装依赖
pip install pyinstaller customtkinter

# 打包
pyinstaller --onefile --windowed \
    --add-data ".claude/skills;.claude/skills" \
    --name "网文写作助手" \
    novel_writer_gui.py
```

打包完成后，exe 文件在 `dist/` 目录中。

---

## 常见问题

### Q: 运行 EXE 提示找不到 Claude Code

A: 需要先安装 Claude Code CLI 并配置好 Anthropic 账号。

### Q: 终端输出没有实时显示

A: 确保使用最新版本的 EXE，旧版本可能存在缓冲延迟问题。

### Q: 如何切换深色/浅色主题

A: 在左侧面板底部的主题下拉菜单中选择。

### Q: 如何添加新的小说类型模板

A: 在 `.claude/skills/novel-write/templates/genre-templates/` 下创建新的 `.md` 文件。

---

## 反馈交流

- GitHub Issues: [提交问题](https://github.com/ShmilyWithme/Shmily_novel_skill/issues)
- QQ: 1943477162
- 邮箱: z2960775@gmail.com

## License

[MIT](LICENSE)
