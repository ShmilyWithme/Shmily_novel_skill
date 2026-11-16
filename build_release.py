#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the release EXE with the bundled Codex novel-write skill."""

import os
import shutil
import subprocess
import sys
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_NAME = "网文写作助手"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build" / "release"
SPEC_FILE = BUILD_DIR / f"{APP_NAME}.spec"


def ensure_pyinstaller():
    try:
        import PyInstaller.__main__  # noqa: F401
    except ImportError:
        print("[INFO] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0,<7"])


def remove_path(path):
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def verify_archive(exe):
    """验证实际打包内容与源码资源一致，而不只检查 EXE 是否存在。"""
    from PyInstaller.archive.readers import CArchiveReader

    archive = CArchiveReader(str(exe))
    names = {name.replace("\\", "/"): name for name in archive.toc}
    resources = ROOT / ".agents" / "skills" / "novel-write"
    for source in resources.rglob("*"):
        if source.is_file():
            relative = source.relative_to(ROOT).as_posix()
            if relative not in names or archive.extract(names[relative]) != source.read_bytes():
                raise RuntimeError(f"Bundled Skill differs from source: {relative}")
    if any(".claude/" in name.lower() for name in names):
        raise RuntimeError("Unexpected legacy engine resources in release")


def main():
    ensure_pyinstaller()

    import customtkinter
    import PyInstaller.__main__

    ctk_path = Path(customtkinter.__file__).resolve().parent
    print(f"[INFO] customtkinter: {ctk_path}")
    print("[INFO] Bundling the Codex novel-write skill from .agents/skills")

    # 只清理本脚本的构建缓存，保留 dist 中的用户项目与运行配置。
    if BUILD_DIR.resolve().parent != (ROOT / "build").resolve():
        raise RuntimeError("Invalid build directory")
    remove_path(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    args = [
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        APP_NAME,
        "--icon=NONE",
        "--workpath", str(BUILD_DIR / "work"),
        "--specpath", str(BUILD_DIR),
        "--distpath", str(DIST_DIR),
        "--exclude-module", "numpy",
        "--add-data",
        f"{ctk_path}:customtkinter",
        "--add-data",
        f"{ROOT / '.agents' / 'skills'}:.agents/skills",
        "--hidden-import",
        "customtkinter",
        "--hidden-import",
        "tkinter",
        "novel_writer_gui.py",
    ]

    old_cwd = Path.cwd()
    try:
        os.chdir(ROOT)
        PyInstaller.__main__.run(args)
    finally:
        os.chdir(old_cwd)
        remove_path(SPEC_FILE)

    exe = DIST_DIR / f"{APP_NAME}.exe"
    if not exe.exists():
        raise SystemExit(f"[ERROR] Expected EXE was not found: {exe}")

    verify_archive(exe)
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    (DIST_DIR / "SHA256SUMS.txt").write_text(f"{digest}  {exe.name}\n", encoding="utf-8")

    print("[OK] Build succeeded")
    print(f"[OK] Output: {exe}")
    print(f"[OK] Size: {exe.stat().st_size} bytes")
    print(f"[OK] Archive verified; SHA256: {digest}")


if __name__ == "__main__":
    main()
