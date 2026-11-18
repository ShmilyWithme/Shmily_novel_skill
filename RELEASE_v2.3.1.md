# 网文写作助手 v2.3.1

## Codex CLI 自动发现

- 修复从 Windows 快捷方式启动时因环境变量不完整而误报“未找到 Codex CLI”的问题。
- 自动查找系统 PATH、`%APPDATA%\npm`、`%LOCALAPPDATA%\npm` 和 Codex Desktop 的版本化安装目录。
- 支持通过 `CODEX_PATH` 指定自定义 `codex.exe`、`codex.cmd` 或 `codex.bat`。
- Codex 版本检查、登录状态检查和实际写作任务统一使用同一条已发现的 CLI 路径。

## 验证

- 31 项本地测试通过。
- Windows GitHub Actions 测试和打包会继续验证真实 EXE 启动。

下载 `NovelWriter-v2.3.1-Windows.exe`，安装并登录 Codex CLI 后运行。源码版需 Python 3.10+：

```powershell
python -m pip install -r requirements.txt
python novel_writer_gui.py
```
