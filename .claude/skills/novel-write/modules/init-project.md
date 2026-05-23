# 项目初始化模块

## 功能说明

当用户首次使用本 skill 或说"新建小说项目"时，执行项目初始化流程。

## 触发词

- `新建小说`
- `初始化项目`
- `创建项目`

## 执行流程

### 第一步：收集信息

询问用户以下信息（如果用户未主动提供）：

1. **小说名称**：作品的标题
2. **类型/题材**：从五大类型中选择，或自定义
   - 玄幻/仙侠
   - 都市/现实
   - 科幻/未来
   - 历史/架空
   - 悬疑/推理
3. **目标平台**：起点、番茄、晋江等（影响风格和篇幅）
4. **预计总字数/章节数**：作品规模
5. **核心卖点/一句话简介**：作品的核心吸引力
6. **目标读者群体**：作品面向的读者

### 第二步：创建目录结构

在用户的项目目录下创建以下文件结构：

```
novel/
├── project.md              # 项目总览（元信息、进度追踪）
├── worldbuilding/
│   └── settings.md         # 世界观设定
├── characters/
│   ├── index.md            # 角色索引
│   └── MC.md               # 主角设定卡
├── outline/
│   ├── master-outline.md   # 总大纲
│   ├── volume-1.md         # 第一卷大纲
│   └── chapter-outs/
│       └── ch001.md        # 第1章梗概
├── chapters/
│   └── ch001.md            # 第1章正文
├── style/
│   └── style-config.md     # 当前文风配置
└── notes/
    └── misc.md             # 杂项笔记、伏笔追踪
```

### 第三步：生成项目文件

#### project.md 内容模板

```markdown
# [小说名称] 项目总览

## 基本信息
- 小说名称：
- 类型/题材：
- 目标平台：
- 预计总字数：XX万字
- 预计章节数：XX章
- 核心卖点：
- 目标读者：
- 创建日期：YYYY-MM-DD

## 进度追踪
| 章节 | 状态 | 字数 | 完成日期 |
|------|------|------|----------|
| ch001 | 待写 | - | - |
```

#### 其他文件初始化

- `worldbuilding/settings.md`：使用 `templates/worldbuilding-template.md` 模板
- `characters/MC.md`：使用 `templates/character-card-template.md` 模板
- `characters/index.md`：创建空的角色索引
- `outline/master-outline.md`：创建空的大纲文件
- `style/style-config.md`：使用 `templates/style-guide.md` 中的默认配置
- `notes/misc.md`：创建空的笔记文件，包含伏笔追踪表

## 注意事项

1. 如果用户未提供某些信息，使用默认值或留空
2. 所有文件使用 UTF-8 编码
3. 文件名使用英文或拼音，避免中文路径问题
4. 创建完成后向用户展示项目结构
