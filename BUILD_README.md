# Python 程序打包成 EXE 详细指南

## 概述

使用 PyInstaller 将 Python 程序打包成独立的 exe 文件，用户无需安装 Python 环境即可运行。

## 环境准备

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 确认依赖已安装

打包前确保程序的所有依赖都已安装：

```bash
pip install -r requirements.txt
# 或手动安装
pip install customtkinter cryptography
```

## 基础打包命令

### 最简单的打包

```bash
pyinstaller your_script.py
```

生成的文件在 `dist/your_script/` 目录中（文件夹形式）。

### 生成单个 exe 文件

```bash
pyinstaller --onefile your_script.py
```

生成单个 `dist/your_script.exe`，运行时会自动解压到临时目录。

### 无控制台窗口（GUI 程序必备）

```bash
pyinstaller --onefile --windowed your_script.py
```

`--windowed` 或 `-w` 参数去掉黑色控制台窗口。

### 指定输出名称

```bash
pyinstaller --onefile --windowed --name "我的程序" your_script.py
```

## 完整打包命令示例

### customtkinter 程序

```bash
pyinstaller --noconfirm --onefile --windowed \
    --name "程序名称" \
    --add-data "path/to/customtkinter;customtkinter/" \
    --hidden-import customtkinter \
    --hidden-import tkinter \
    your_script.py
```

### 带 cryptography 库的程序

```bash
pyinstaller --noconfirm --onefile --windowed \
    --name "程序名称" \
    --hidden-import cryptography \
    --hidden-import cryptography.hazmat.primitives \
    --hidden-import cryptography.hazmat.primitives.asymmetric \
    --hidden-import cryptography.hazmat.backends \
    your_script.py
```

### 完整示例（本项目）

```bash
pyinstaller --noconfirm --onefile --windowed \
    --name "网文写作助手" \
    --add-data "E:\Users\Shmily\AppData\Local\Programs\Python\Python312\Lib\site-packages\customtkinter;customtkinter\" \
    --hidden-import customtkinter \
    --hidden-import tkinter \
    --hidden-import cryptography \
    --hidden-import cryptography.hazmat.primitives \
    --hidden-import cryptography.hazmat.primitives.asymmetric \
    novel_writer_gui.py
```

## 常用参数说明

| 参数 | 说明 |
|------|------|
| `--onefile, -F` | 打包成单个 exe 文件 |
| `--windowed, -w` | 不显示控制台窗口（GUI 程序用） |
| `--noconfirm` | 不询问确认，直接覆盖旧文件 |
| `--name NAME` | 指定输出文件名 |
| `--icon FILE.ico` | 指定 exe 图标 |
| `--add-data SRC;DEST` | 添加数据文件（Windows 用分号分隔） |
| `--hidden-import MODULE` | 添加隐式导入的模块 |
| `--exclude-module MODULE` | 排除不需要的模块 |
| `--distpath DIR` | 指定输出目录 |
| `--workpath DIR` | 指定工作目录 |
| `--specpath DIR` | 指定 spec 文件目录 |

## 获取 customtkinter 路径

打包 customtkinter 程序需要添加其资源文件，先获取路径：

```bash
# 方法 1：Python 命令
python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"

# 方法 2：PowerShell
$ctkPath = python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"
Write-Host $ctkPath
```

然后在打包时使用：

```bash
--add-data "$ctkPath;customtkinter/"
```

## 添加图标

```bash
pyinstaller --onefile --windowed --icon=app.ico your_script.py
```

图标格式必须是 `.ico`，可以用在线工具转换：https://convertico.com

## 打包脚本模板

### Windows 批处理 (build.bat)

```bat
@echo off
chcp 65001 >nul
echo ==============================
echo   程序打包工具
echo ==============================
echo.

:: 检查 PyInstaller
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装 PyInstaller...
    pip install pyinstaller
    echo.
)

:: 获取 customtkinter 路径
for /f "delims=" %%i in ('python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"') do set CTK_PATH=%%i

echo [信息] customtkinter 路径: %CTK_PATH%
echo [开始打包] 请稍候...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "程序名称" ^
    --icon=app.ico ^
    --add-data "%CTK_PATH%;customtkinter\" ^
    --hidden-import customtkinter ^
    --hidden-import tkinter ^
    your_script.py

echo.
if exist "dist\程序名称.exe" (
    echo 打包成功！
    echo 文件位置: dist\程序名称.exe
    explorer dist
) else (
    echo 打包失败，请检查错误信息
)

pause
```

### PowerShell 脚本 (build.ps1)

```powershell
Write-Host "==============================" -ForegroundColor Cyan
Write-Host "  程序打包工具" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

# 获取 customtkinter 路径
$ctkPath = python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"
Write-Host "customtkinter 路径: $ctkPath"

# 打包
Write-Host "开始打包..." -ForegroundColor Yellow

pyinstaller --noconfirm --onefile --windowed `
    --name "程序名称" `
    --add-data "$ctkPath;customtkinter/" `
    --hidden-import customtkinter `
    --hidden-import tkinter `
    your_script.py

if (Test-Path "dist/程序名称.exe") {
    Write-Host "打包成功！" -ForegroundColor Green
    Write-Host "文件位置: dist/程序名称.exe"
    Invoke-Item "dist"
} else {
    Write-Host "打包失败！" -ForegroundColor Red
}
```

## 常见问题解决

### 1. ModuleNotFoundError

**问题：** 打包后运行提示找不到模块

**解决：** 添加 `--hidden-import`

```bash
# 方法 1：添加参数
--hidden-import 模块名

# 方法 2：编辑 spec 文件
# 先生成 spec
pyinstaller your_script.py
# 编辑 your_script.spec，找到 hiddenimports=[]
# 改为 hiddenimports=['模块名']
# 然后用 spec 打包
pyinstaller your_script.spec
```

### 2. 找不到数据文件

**问题：** 程序运行时找不到配置文件、图片等

**解决：** 使用 `--add-data` 或修改代码

```bash
# 添加数据文件
--add-data "data;data"  # 格式: 源路径;目标路径
```

代码中访问打包后的数据文件：

```python
import sys
import os

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        base_path = sys._MEIPASS
    else:
        # 开发时的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# 使用
config_path = get_resource_path("config/settings.json")
```

### 3. customtkinter 主题缺失

**问题：** 打包后界面显示异常

**解决：** 必须添加 customtkinter 的资源文件

```bash
# 先获取路径
python -c "import customtkinter; print(customtkinter.__file__)"

# 添加到打包
--add-data "path/to/customtkinter;customtkinter/"
```

### 4. 杀毒软件误报

**问题：** exe 被杀毒软件拦截

**解决：**
- 添加信任/白名单
- 使用代码签名证书（付费）
- 用 `--uac-admin` 请求管理员权限

### 5. exe 文件太大

**问题：** 生成的 exe 文件过大

**解决：**

```bash
# 排除不需要的模块
--exclude-module matplotlib
--exclude-module numpy
--exclude-module pandas

# 使用 UPX 压缩（需先安装 UPX）
--upx-dir=/path/to/upx
```

### 6. 启动速度慢

**问题：** `--onefile` 模式启动慢

**原因：** 每次运行都要解压到临时目录

**解决：** 改用 `--onedir` 模式（文件夹形式）

```bash
pyinstaller --windowed --name "程序名称" your_script.py
```

生成 `dist/程序名称/` 文件夹，里面包含 exe 和依赖文件，整体分发。

### 7. 权限问题

**问题：** 打包过程中权限被拒绝

**解决：**

```bash
# 关闭正在运行的旧 exe
taskkill /F /IM "程序名称.exe"

# 删除旧文件
Remove-Item "dist/程序名称.exe" -Force

# 重新打包
pyinstaller ...
```

## spec 文件高级配置

生成 spec 文件：

```bash
pyinstaller your_script.py
```

编辑 `your_script.spec`：

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['your_script.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('customtkinter', 'customtkinter'),  # 添加数据文件
        ('config', 'config'),
    ],
    hiddenimports=[
        'customtkinter',
        'tkinter',
        'cryptography',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy'],  # 排除不需要的模块
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='程序名称',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # 启用 UPX 压缩
    console=False,       # 无控制台
    icon='app.ico',      # 图标
)
```

使用 spec 打包：

```bash
pyinstaller your_script.spec
```

## 完整打包流程

```bash
# 1. 确保依赖已安装
pip install pyinstaller customtkinter cryptography

# 2. 获取 customtkinter 路径
python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"

# 3. 执行打包
pyinstaller --noconfirm --onefile --windowed \
    --name "你的程序" \
    --add-data "customtkinter的路径;customtkinter/" \
    --hidden-import customtkinter \
    --hidden-import tkinter \
    --hidden-import cryptography \
    your_script.py

# 4. 检查输出
ls dist/

# 5. 测试运行
./dist/你的程序.exe
```

## 打包检查清单

打包前确认：

- [ ] 所有依赖已安装 (`pip list`)
- [ ] 程序能正常运行 (`python your_script.py`)
- [ ] 获取了 customtkinter 路径（如使用）
- [ ] 确定了程序名称和图标
- [ ] 关闭了正在运行的旧版本

打包后检查：

- [ ] exe 文件生成成功
- [ ] 双击能正常启动
- [ ] 功能正常（特别是 GUI 和文件操作）
- [ ] 在没有 Python 的电脑上测试

## 快速参考

```bash
# 最常用：单文件 + 无控制台
pyinstaller -F -w --name "程序名" script.py

# 完整版：单文件 + 无控制台 + 图标 + 自定义名称
pyinstaller -F -w --name "程序名" --icon=app.ico script.py

# customtkinter 完整版
pyinstaller -F -w --name "程序名" --add-data "ctk路径;customtkinter/" --hidden-import customtkinter script.py

# 打包 spec 文件（高级）
pyinstaller script.spec
```
