#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the release EXE with bundled Claude and Codex novel-write skills."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_NAME = "网文写作助手"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
SPEC_FILE = ROOT / f"{APP_NAME}.spec"


def ensure_pyinstaller():
    try:
        import PyInstaller.__main__  # noqa: F401
    except ImportError:
        print("[INFO] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def remove_path(path):
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def clean_runtime_residue():
    for path in (
        DIST_DIR / ".claude",
        DIST_DIR / ".agents",
        DIST_DIR / ".novel_writer_settings.json",
    ):
        remove_path(path)


def main():
    ensure_pyinstaller()

    import customtkinter
    import PyInstaller.__main__

    ctk_path = Path(customtkinter.__file__).resolve().parent
    print(f"[INFO] customtkinter: {ctk_path}")
    print("[INFO] Bundling skills:")
    print("       Claude: .claude/skills -> .claude/skills")
    print("       Codex : .agents/skills -> .agents/skills")

    clean_runtime_residue()
    remove_path(BUILD_DIR)
    remove_path(SPEC_FILE)

    args = [
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        APP_NAME,
        "--icon=NONE",
        "--add-data",
        f"{ctk_path}:customtkinter",
        "--add-data",
        ".claude/skills:.claude/skills",
        "--add-data",
        ".agents/skills:.agents/skills",
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

    clean_runtime_residue()

    exe = DIST_DIR / f"{APP_NAME}.exe"
    if not exe.exists():
        raise SystemExit(f"[ERROR] Expected EXE was not found: {exe}")

    print("[OK] Build succeeded")
    print(f"[OK] Output: {exe}")
    print(f"[OK] Size: {exe.stat().st_size} bytes")


if __name__ == "__main__":
    main()
