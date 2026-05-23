@echo off
chcp 65001 >nul
echo ==============================
echo   网文写作助手 - 打包工具
echo ==============================
echo.

:: 检查 PyInstaller 是否安装
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装 PyInstaller...
    pip install pyinstaller
    echo.
)

:: 获取 customtkinter 路径
for /f "delims=" %%i in ('python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"') do set CTK_PATH=%%i

if "%CTK_PATH%"=="" (
    echo [错误] 未找到 customtkinter，请先运行: pip install customtkinter
    pause
    exit /b 1
)

echo [信息] customtkinter 路径: %CTK_PATH%
echo [开始打包] 请稍候（约1-3分钟）...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "网文写作助手" ^
    --icon=NONE ^
    --add-data "%CTK_PATH%;customtkinter\" ^
    --add-data ".claude;.claude\" ^
    --hidden-import customtkinter ^
    --hidden-import tkinter ^
    novel_writer_gui.py

echo.
if exist "dist\网文写作助手.exe" (
    echo ==============================
    echo   打包成功！
    echo   文件位置: dist\网文写作助手.exe
    echo ==============================
    echo.
    echo 是否打开输出目录？(Y/N)
    set /p choice=
    if /i "%choice%"=="Y" explorer dist
) else (
    echo [错误] 打包失败，请检查上方错误信息
)

pause
