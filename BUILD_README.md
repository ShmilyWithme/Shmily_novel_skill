# Windows 构建与发布

使用 Windows、Python 3.10+ 和隔离的虚拟环境构建。PyInstaller 不支持从其他操作系统交叉生成 Windows EXE。

## 准备

在仓库根目录执行：

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-build.txt
```

使用虚拟环境可以避免把本机无关包带入发布文件。构建脚本会自动定位 CustomTkinter 和本仓库 Skill，无需填写本机绝对路径。

## 检查

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python -m py_compile novel_writer_gui.py build_release.py
git diff --check
```

测试覆盖卷纲保存、未保存编辑保护、外部冲突、导出失败、配置校验、Skill 补齐和后台事件等场景。Windows 测试会创建临时 Tk 窗口，不会调用 Codex 模型服务。

## 构建

```powershell
.venv\Scripts\python build_release.py
.venv\Scripts\python tests/smoke_release.py
```

也可以在已安装依赖的 Python 环境中运行 `build.bat`。

输出：

- `dist/网文写作助手.exe`：单文件桌面程序（GitHub Release 上传时命名为 `NovelWriter-v2.3.1-Windows.exe`）。
- `dist/SHA256SUMS.txt`：发布文件的 SHA-256 校验值。

脚本仅清理 `build/release/` 构建缓存，保留 `dist` 中的用户项目和配置。打包后会逐文件比较内置 Skill 与源码；校验失败会使构建失败。发布包只包含程序、依赖和通用 Skill，不包含用户小说、登录凭据或应用设置。

发布测试会实际启动 EXE，等待可见主窗口并关闭它，使用临时配置目录。

## 发布

1. 更新 `APP_VERSION`、README、界面预览图和对应版本的更新记录。
2. 通过检查并重新构建。
3. 将软件源码提交并推送到 GitHub。
4. 创建指向同一提交的版本标签及 GitHub Release，附上 EXE、`SHA256SUMS.txt` 和更新记录。
5. 下载发布附件并核对 SHA-256。

GitHub Actions 在每次推送和 PR 上运行 Python 3.10、3.12 的 Windows 测试，并构建可下载附件。

运行发布版仍需要用户安装并登录 Codex CLI。构建检查验证桌面程序与内置资源；实际 AI 服务连接由用户本机 CLI 配置决定。
