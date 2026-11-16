# 网文写作助手 v2.2.0 更新公告

v2.2.0 面向长篇连续创作更新界面与项目流程，并集成 OpenAI Codex CLI，支持在小说项目工作区中运行写作任务。

## 主要功能

- 重构主界面，拆分工作台、章节工位、故事地图、资料库、Codex 编剧室、日志和数据看板。
- 在章节工位加入上一章/下一章导航。
- 新增 Codex CLI 诊断，可检查 CLI 安装、登录、本地配置和项目 Skill。
- 增加 `.agents/skills/novel-write`，并在创建或打开小说项目时释放 Codex Skill。
- 统一使用 UTF-8 环境变量处理中文输入输出，并修复常见乱码文本。
- 新增打包脚本，将 Codex Skill 内置到单文件 EXE。
- 增加原子写入，避免保存章节、大纲和项目配置时留下半个文件。
- 加强项目打开失败提示、Skill 释放检查和角色文件名校验，避免损坏配置或越界路径影响项目。

## 使用要求

- 安装并登录 OpenAI Codex CLI。
- 自定义 provider 需要兼容 OpenAI Responses 接口 `/v1/responses`。
- 长篇写作建议分批执行，并定期检查章节、大纲和人物资料的一致性。

## 下载

前往 [Releases](https://github.com/ShmilyWithme/Shmily_novel_skill/releases) 获取 Windows 版本。
