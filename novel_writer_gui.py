#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网文写作助手 GUI 界面 - 现代风格
基于 customtkinter 的图形化界面
"""

import os
import sys
import json
import re
import codecs
import subprocess
import threading
import time
import shutil
import tempfile
import queue
from datetime import datetime
from tkinter import messagebox, filedialog

import customtkinter as ctk
from customtkinter import (
    CTk,
    CTkFrame,
    CTkLabel,
    CTkButton,
    CTkEntry,
    CTkTextbox,
    CTkTabview,
    CTkOptionMenu,
    CTkToplevel,
    CTkFont,
    CTkScrollableFrame
)


# 设置主题
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# ═══════════════════════════════════════════════════════════
#  UI 色彩系统
# ═══════════════════════════════════════════════════════════

COLORS = {
    # ── 背景色 ──
    "bg_main":        ("#F3F4F6", "#0F172A"),
    "bg_sidebar":     ("#FFFFFF", "#111827"),
    "bg_card":        ("#FFFFFF", "#1F2937"),
    "bg_input":       ("#FFFFFF", "#111827"),
    "bg_dialog":      ("#F9FAFB", "#111827"),
    "bg_band":        ("#FFF7ED", "#1E293B"),

    # ── 强调色 ──
    "accent":         ("#9A3412", "#FB923C"),
    "accent_hover":   ("#7C2D12", "#FDBA74"),
    "accent_alt":     ("#0F766E", "#2DD4BF"),
    "accent_alt_hover": ("#134E4A", "#5EEAD4"),
    "danger":         ("#B91C1C", "#EF4444"),
    "danger_hover":   ("#991B1B", "#F87171"),
    "success":        ("#166534", "#22C55E"),
    "success_hover":  ("#14532D", "#4ADE80"),
    "info":           ("#1D4ED8", "#60A5FA"),
    "info_hover":     ("#1E40AF", "#93C5FD"),
    "warning":        ("#92400E", "#FBBF24"),
    "tab_selected":   ("#FED7AA", "#92400E"),
    "tab_selected_hover": ("#FDBA74", "#B45309"),

    # ── 文本色 ──
    "text_primary":   ("#111827", "#F9FAFB"),
    "text_secondary": ("#374151", "#D1D5DB"),
    "text_terminal":  ("#064E3B", "#D1FAE5"),
    "text_btn_dark":  ("#111827", "#F9FAFB"),
    "text_btn_light": ("#FFFFFF", "#111827"),
    "text_btn_alt":   ("#FFFFFF", "#042F2E"),
    "text_on_status": ("#111827", "#F9FAFB"),

    # ── 边框/分隔线 ──
    "border":         ("#9CA3AF", "#4B5563"),
    "border_focus":   ("#0F766E", "#5EEAD4"),
    "divider":        ("#D1D5DB", "#374151"),
    "border_btn":     ("#6B7280", "#9CA3AF"),

    # ── 状态色 ──
    "status_ready":   ("#E5E7EB", "#1F2937"),
    "status_running": ("#CCFBF1", "#134E4A"),
    "status_success": ("#DCFCE7", "#14532D"),
    "status_error":   ("#FEE2E2", "#7F1D1D"),

    # ── hover ──
    "hover_outline":  ("#E5E7EB", "#374151"),
}

# ── 尺寸常量 ──
CORNER_RADIUS_SM = 6
CORNER_RADIUS_MD = 8
CORNER_RADIUS_LG = 10
CORNER_RADIUS_XL = 12

BTN_HEIGHT_SM = 30
BTN_HEIGHT_MD = 36
BTN_HEIGHT_LG = 40

# ── 字体 ──
FONT_MONO = ("Consolas", 12)
FONT_TITLE = ("Microsoft YaHei UI", 25, "bold")
FONT_SECTION = ("Microsoft YaHei UI", 12, "bold")
FONT_BODY = ("Microsoft YaHei UI", 13)
FONT_SMALL = ("Microsoft YaHei UI", 11)
FONT_DISPLAY = ("Microsoft YaHei UI", 18, "bold")
FONT_CARD_TITLE = ("Microsoft YaHei UI", 14, "bold")

APP_SETTINGS_FILE = ".novel_writer_settings.json"
APP_VERSION = "2.3.1"
REQUIRED_SKILL_FILES = (
    "SKILL.md",
    os.path.join("agents", "openai.yaml"),
    os.path.join("modules", "chapter-writer.md"),
    os.path.join("modules", "character-manager.md"),
    os.path.join("modules", "init-project.md"),
    os.path.join("modules", "outline-generator.md"),
    os.path.join("modules", "style-control.md"),
    os.path.join("modules", "worldbuilding.md"),
    os.path.join("modules", "utils", "consistency-checker.md"),
    os.path.join("modules", "utils", "export.md"),
    os.path.join("modules", "utils", "review.md"),
    os.path.join("modules", "utils", "stats.md"),
    os.path.join("templates", "chapter-template.md"),
    os.path.join("templates", "character-card-template.md"),
    os.path.join("templates", "worldbuilding-template.md"),
    *(os.path.join("templates", "genre-templates", f"{genre}.md")
      for genre in ("dushi", "kehuan", "moxi", "qihuan", "xuanhuan")),
)
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def resolve_codex_path(environment=None):
    """查找 Windows 上的 Codex CLI，兼容 npm shim 和 Codex Desktop 安装。"""
    environment = environment or os.environ
    candidates = []

    configured = environment.get("CODEX_PATH", "").strip().strip('"')
    if configured:
        candidates.append(configured)

    for command in ("codex", "codex.exe", "codex.cmd", "codex.bat"):
        found = shutil.which(command)
        if found:
            candidates.append(found)

    appdata = environment.get("APPDATA", "")
    local_appdata = environment.get("LOCALAPPDATA", "")
    candidates.extend([
        os.path.join(appdata, "npm", "codex.cmd"),
        os.path.join(appdata, "npm", "codex.exe"),
        os.path.join(local_appdata, "npm", "codex.cmd"),
        os.path.join(local_appdata, "npm", "codex.exe"),
    ])

    # Codex Desktop puts the bundled CLI in a versioned subdirectory.
    codex_bin = os.path.join(local_appdata, "OpenAI", "Codex", "bin")
    if os.path.isdir(codex_bin):
        try:
            versioned = [
                os.path.join(codex_bin, name, "codex.exe")
                for name in os.listdir(codex_bin)
            ]
            versioned.sort(key=lambda path: os.path.getmtime(path) if os.path.isfile(path) else 0,
                           reverse=True)
            candidates.extend(versioned)
        except OSError:
            pass

    seen = set()
    for candidate in candidates:
        if not candidate:
            continue
        normalized = os.path.abspath(os.path.expandvars(os.path.expanduser(candidate)))
        key = os.path.normcase(normalized)
        if key in seen:
            continue
        seen.add(key)
        if os.path.isfile(normalized):
            return normalized
    return None


def build_codex_cli_command(arguments=()):
    """构造可执行的 Codex 命令，避免依赖启动 GUI 时继承的 PATH。"""
    codex_path = resolve_codex_path()
    arguments = list(arguments)
    if codex_path:
        extension = os.path.splitext(codex_path)[1].lower()
        if extension in (".exe", ".com"):
            return [codex_path, *arguments]
        return ["cmd.exe", "/d", "/c", codex_path, *arguments]
    return ["cmd.exe", "/d", "/c", "codex", *arguments]

MOJIBAKE_MARKERS = (
    "锟斤拷", "鐨", "涓", "鍦", "鍙", "鏄", "绛", "杩", "瀹", "灏",
    "浣", "犲", "鎵", "瑕", "璇", "殑", "鈥", "鈹", "忋", "勩",
    "缃", "戞", "枃", "鍐", "欎", "綔", "鍔", "墜", "鏋", "勯",
    "€", "棩", "潰", "弬", "鍩", "櫙", "鑹", "闂"
)


def _count_cjk(text):
    return sum(1 for char in text if '\u4e00' <= char <= '\u9fff')


def _mojibake_marker_count(text):
    return sum(text.count(marker) for marker in MOJIBAKE_MARKERS)


def repair_mojibake_text(text):
    """修复 Windows PowerShell 5.1 把 UTF-8 中文按 GBK/ANSI 读出的常见乱码。"""
    if not text or _mojibake_marker_count(text) < 2:
        return text

    def score(candidate):
        markers = _mojibake_marker_count(candidate)
        replacements = candidate.count("�")
        return _count_cjk(candidate) - markers * 8 - replacements * 12

    original_markers = _mojibake_marker_count(text)
    original_cjk = _count_cjk(text)
    original_replacements = text.count("�")
    original_score = score(text)
    best_text = text
    best_score = original_score
    for encoding in ("gbk", "cp936"):
        try:
            candidate = text.encode(encoding).decode("utf-8")
        except UnicodeError:
            candidate = None
        if candidate is not None:
            candidate_markers = _mojibake_marker_count(candidate)
            candidate_cjk = _count_cjk(candidate)
            candidate_replacements = candidate.count("�")
            if (
                candidate_markers < original_markers
                and candidate_replacements <= original_replacements
                and (
                    original_cjk < 2
                    or candidate_cjk >= max(1, int(original_cjk * 0.3))
                )
            ):
                candidate_score = score(candidate)
                if candidate_score > best_score:
                    best_text = candidate
                    best_score = candidate_score

        if "�" not in text:
            continue
        try:
            candidate = text.encode(encoding, errors="ignore").decode("utf-8", errors="replace")
        except UnicodeError:
            continue
        candidate_markers = _mojibake_marker_count(candidate)
        candidate_cjk = _count_cjk(candidate)
        candidate_replacements = candidate.count("�")
        if candidate_markers >= original_markers:
            continue
        if candidate_replacements > original_replacements:
            continue
        if original_cjk >= 2 and candidate_cjk < max(1, int(original_cjk * 0.3)):
            continue
        candidate_score = score(candidate)
        if candidate_score > best_score:
            best_text = candidate
            best_score = candidate_score

    return best_text if best_score >= original_score + 5 else text
AI_ENGINE_NAME = "Codex"
AI_ENGINE_DEFAULT_PROMPT = "$novel-write "
TAB_DASHBOARD = "工作台"
TAB_WRITING = "章节工位"
TAB_OUTLINE = "故事地图"
TAB_LIBRARY = "资料库"
TAB_STUDIO = "AI 编剧室"
TAB_LOG = "日志"
TAB_STATS = "数据看板"


def btn_primary(**kwargs):
    defaults = dict(height=BTN_HEIGHT_LG, corner_radius=CORNER_RADIUS_MD,
                    fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                    text_color=COLORS["text_btn_light"])
    defaults.update(kwargs)
    return defaults

def btn_outline(**kwargs):
    defaults = dict(height=BTN_HEIGHT_MD, corner_radius=CORNER_RADIUS_MD,
                    fg_color="transparent", border_width=1,
                    border_color=COLORS["border_btn"],
                    text_color=COLORS["text_btn_dark"],
                    hover_color=COLORS["hover_outline"])
    defaults.update(kwargs)
    return defaults

def btn_danger(**kwargs):
    defaults = dict(height=BTN_HEIGHT_MD, corner_radius=CORNER_RADIUS_MD,
                    fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                    text_color=COLORS["text_btn_light"])
    defaults.update(kwargs)
    return defaults

def btn_success(**kwargs):
    defaults = dict(height=BTN_HEIGHT_MD, corner_radius=CORNER_RADIUS_MD,
                    fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                    text_color=COLORS["text_btn_light"])
    defaults.update(kwargs)
    return defaults

def btn_info(**kwargs):
    defaults = dict(height=BTN_HEIGHT_MD, corner_radius=CORNER_RADIUS_MD,
                    fg_color=COLORS["info"], hover_color=COLORS["info_hover"],
                    text_color=COLORS["text_btn_light"])
    defaults.update(kwargs)
    return defaults

def btn_teal(**kwargs):
    defaults = dict(height=BTN_HEIGHT_MD, corner_radius=CORNER_RADIUS_MD,
                    fg_color=COLORS["accent_alt"], hover_color=COLORS["accent_alt_hover"],
                    text_color=COLORS["text_btn_alt"])
    defaults.update(kwargs)
    return defaults

def btn_ghost(**kwargs):
    defaults = dict(height=BTN_HEIGHT_SM, corner_radius=CORNER_RADIUS_SM,
                    fg_color="transparent", border_width=1,
                    border_color=COLORS["border_btn"],
                    text_color=COLORS["text_secondary"],
                    hover_color=COLORS["hover_outline"])
    defaults.update(kwargs)
    return defaults

def menu_style(**kwargs):
    defaults = dict(
        fg_color=COLORS["bg_input"],
        button_color=COLORS["accent"],
        button_hover_color=COLORS["accent_hover"],
        dropdown_fg_color=COLORS["bg_card"],
        dropdown_hover_color=COLORS["hover_outline"],
        text_color=COLORS["text_primary"],
        dropdown_text_color=COLORS["text_primary"],
    )
    defaults.update(kwargs)
    return defaults

def get_color(key):
    mode = ctk.get_appearance_mode()
    pair = COLORS[key]
    return pair[1] if mode == "Dark" else pair[0]


def get_app_data_dir():
    """获取稳定的用户级配置目录，避免 EXE 旁边生成运行配置"""
    base_dir = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    app_dir = os.path.join(base_dir, "NovelWriterAssistant")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_app_settings_path():
    """获取全局应用设置文件路径"""
    return os.path.join(get_app_data_dir(), APP_SETTINGS_FILE)


def get_default_project_root():
    """获取新建小说项目默认保存目录"""
    documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
    if os.path.isdir(documents_dir):
        root = os.path.join(documents_dir, "网文写作助手项目")
    else:
        root = os.path.join(get_app_data_dir(), "projects")
    os.makedirs(root, exist_ok=True)
    return root


def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        base_path = sys._MEIPASS
    else:
        # 开发时的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def ensure_skill_files(target_dir=None):
    """确保 Codex 所需的 Skill 文件存在于目标目录"""
    target_dir = target_dir or os.getcwd()
    skill_path = os.path.join('.agents', 'skills', 'novel-write')
    dest_skill_dir = os.path.join(target_dir, skill_path)
    if all(os.path.isfile(os.path.join(dest_skill_dir, relative_path)) for relative_path in REQUIRED_SKILL_FILES):
        return True

    resource_skill_dir = get_resource_path(skill_path)
    if not os.path.isdir(resource_skill_dir):
        return False

    try:
        os.makedirs(target_dir, exist_ok=True)
        os.makedirs(os.path.dirname(dest_skill_dir), exist_ok=True)
        # 补齐缺失文件时保留项目已有的自定义 Skill。
        for source_root, _, filenames in os.walk(resource_skill_dir):
            relative_root = os.path.relpath(source_root, resource_skill_dir)
            destination_root = os.path.join(dest_skill_dir, relative_root)
            os.makedirs(destination_root, exist_ok=True)
            for filename in filenames:
                destination = os.path.join(destination_root, filename)
                if not os.path.exists(destination):
                    shutil.copy2(os.path.join(source_root, filename), destination)
        return all(
            os.path.isfile(os.path.join(dest_skill_dir, relative_path))
            for relative_path in REQUIRED_SKILL_FILES
        )
    except OSError as e:
        print(f"释放 Codex Skill 文件失败: {e}")
        return False


def get_missing_skill_paths(target_dir):
    """返回项目目录中缺失的 Codex Skill 路径"""
    skill_dir = os.path.join(target_dir, '.agents', 'skills', 'novel-write')
    return [
        os.path.join(skill_dir, relative_path)
        for relative_path in REQUIRED_SKILL_FILES
        if not os.path.isfile(os.path.join(skill_dir, relative_path))
    ]


def has_bundled_skill_resources():
    """检查发布包中是否包含 Codex Skill 资源"""
    return all(
        os.path.isfile(get_resource_path(os.path.join('.agents', 'skills', 'novel-write', relative_path)))
        for relative_path in REQUIRED_SKILL_FILES
    )


def validate_project_name(name):
    """Validate a novel project name before using it as a directory name."""
    name = (name or "").strip()
    if not name:
        return "请输入项目名称。"
    if name in (".", "..") or any(ord(char) < 32 or char in '<>:"/\\|?*' for char in name):
        return "项目名称包含 Windows 文件名不允许的字符。"
    if name.endswith((" ", ".")):
        return "项目名称不能以空格或句点结尾。"
    if name.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
        return "项目名称与 Windows 保留设备名冲突。"
    return None


def atomic_write_text(path, content):
    """以同目录临时文件原子替换文本，避免编辑过程中留下半个文件。"""
    path = os.path.abspath(path)
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, temporary_file = tempfile.mkstemp(
        prefix=f".{os.path.basename(path)}.",
        suffix=".tmp",
        dir=directory,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_file, path)
    except Exception:
        try:
            os.unlink(temporary_file)
        except OSError:
            pass
        raise


def validate_child_filename(name, label="名称"):
    """校验会被转换为项目内文件名的用户输入。"""
    error = validate_project_name(name)
    if error:
        return f"{label}无效：{error}"
    return None


def read_text(path):
    """兼容带 BOM 的 UTF-8 文件，读取失败时保留调用方原有编辑内容。"""
    with open(path, encoding="utf-8-sig") as stream:
        return stream.read()


def load_project_config(path):
    config = json.loads(read_text(path))
    if not isinstance(config, dict):
        raise ValueError("project.json 顶层必须是对象")
    for key in ("target_words", "target_chapters"):
        value = config.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise ValueError(f"{key} 必须是非负整数")
        try:
            number = int(value)
        except ValueError:
            raise ValueError(f"{key} 必须是非负整数") from None
        if number < 0:
            raise ValueError(f"{key} 不能小于零")
        config[key] = number
    for key in ("name", "type", "platform", "pov", "audience", "hook", "created"):
        if key in config and not isinstance(config[key], str):
            raise ValueError(f"{key} 必须是文本")
    return config


def document_body(content):
    return re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL).strip()


def edit_document(parent, path, title, default=""):
    """保存失败时保留输入供重试；读取失败时不打开空白编辑器。"""
    try:
        original = read_text(path) if os.path.exists(path) else None
    except (OSError, UnicodeError) as e:
        messagebox.showerror("读取失败", str(e), parent=parent)
        return False
    content = original if original is not None else default
    while True:
        dialog = EditDialog(parent, title, content)
        parent.wait_window(dialog.top)
        if dialog.result is None:
            return False
        content = dialog.result
        try:
            disk = read_text(path) if os.path.exists(path) else None
            if disk != original and not messagebox.askyesno(
                    "文件已被外部修改", "确定用编辑内容覆盖磁盘中的修改吗？", parent=parent):
                continue
            atomic_write_text(path, content)
            return True
        except (OSError, UnicodeError) as e:
            messagebox.showerror("保存失败", f"编辑内容已保留，可重试保存。\n{e}", parent=parent)


class ModernNovelWriterApp:
    """现代风格网文写作助手"""

    def __init__(self):
        self.root = CTk()
        self.root.title(f"网文写作助手 {APP_VERSION}")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)

        # 项目状态
        self.project_path = None
        self.project_config = {}
        self.app_settings = self.load_app_settings()
        appearance = self.app_settings.get("appearance", "浅色")
        ctk.set_appearance_mode({"浅色": "light", "深色": "dark", "系统": "system"}.get(appearance, "light"))
        if 'ai_engine' in self.app_settings:
            self.app_settings.pop('ai_engine', None)
            self.save_app_settings()
        self._cmd_running = False
        self.proc = None
        self._last_command_output = ""
        self._diagnostic_running = False
        self._closing = False
        self._loaded_chapter_num = None
        self._loaded_chapter_content = ""
        self._loaded_chapter_path = None
        self._chapter_scan_cache = {}
        self._loaded_outline_path = None
        self._loaded_outline_content = ""
        self._loaded_outline_choice = "总大纲"
        self._ui_events = queue.Queue(maxsize=256)
        self._cancel_command = threading.Event()

        # 创建界面
        self.create_ui()
        self.root.after(50, self._drain_ui_events)
        self.root.bind("<Control-s>", self._save_shortcut)

        # 窗口关闭时清理进程
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_app_settings(self):
        """读取全局应用设置"""
        settings_path = get_app_settings_path()
        if not os.path.exists(settings_path):
            return {}
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings if isinstance(settings, dict) else {}
        except Exception:
            return {}

    def save_app_settings(self):
        """保存全局应用设置"""
        settings_path = get_app_settings_path()
        try:
            atomic_write_text(settings_path, json.dumps(self.app_settings, ensure_ascii=False, indent=2))
        except Exception as e:
            if hasattr(self, 'log_text'):
                self._append_log(f"保存应用设置失败: {e}", "ERROR")
            else:
                print(f"保存应用设置失败: {e}")

    def get_ai_engine_label(self):
        """获取当前 AI 引擎显示名"""
        return AI_ENGINE_NAME

    def _post_ui(self, callback, *args):
        """后台线程只入队，不直接调用 Tk（包括 after）。"""
        while not self._closing:
            try:
                self._ui_events.put((callback, args), timeout=0.1)
                return
            except queue.Full:
                continue

    def _drain_ui_events(self):
        if self._closing:
            return
        try:
            for _ in range(64):
                try:
                    callback, args = self._ui_events.get_nowait()
                except queue.Empty:
                    break
                try:
                    callback(*args)
                except Exception:
                    self.root.report_callback_exception(*sys.exc_info())
        finally:
            if not self._closing:
                self.root.after(50, self._drain_ui_events)

    def _save_shortcut(self, _event=None):
        if self.tabview.get() == TAB_OUTLINE:
            self.save_outline()
        else:
            self.save_project()
        return "break"

    def get_default_prompt(self):
        """获取当前引擎的默认输入前缀"""
        return AI_ENGINE_DEFAULT_PROMPT

    def format_skill_command(self, command):
        """根据当前引擎格式化 novel-write 命令"""
        return f"{self.get_default_prompt()}{command}".strip()

    def create_ui(self):
        """创建主界面"""
        # 主容器
        self.main_container = CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # 左侧面板
        self.create_left_panel()

        # 右侧面板
        self.create_right_panel()

        # 底部状态栏
        self.create_status_bar()

    def create_left_panel(self):
        """创建左侧面板"""
        self.left_panel = CTkFrame(self.main_container, width=280, corner_radius=CORNER_RADIUS_XL,
                                    fg_color=COLORS["bg_sidebar"])
        self.left_panel.pack(side="left", fill="y", padx=(0, 15))
        self.left_panel.pack_propagate(False)

        # 创建可滚动的容器
        self.left_scroll = CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.left_scroll.pack(fill="both", expand=True)

        # Logo 和标题
        header_frame = CTkFrame(self.left_scroll, fg_color="transparent")
        header_frame.pack(fill="x", padx=18, pady=(22, 12))

        CTkLabel(header_frame, text="长篇工坊",
                 font=FONT_TITLE, text_color=COLORS["text_primary"]).pack(anchor="w")
        CTkLabel(header_frame, text="大纲 · 章节 · 人设 · 发布",
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(2, 0))

        # 项目信息卡片
        self.create_project_card()

        # 快捷操作按钮
        self.create_action_buttons()

    def create_project_card(self):
        """创建项目信息卡片"""
        card = CTkFrame(self.left_scroll, corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_card"])
        card.pack(fill="x", padx=15, pady=(8, 12))

        # 项目名称
        self.project_name_var = ctk.StringVar(value="未打开项目")
        CTkLabel(card, text="当前书稿",
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(anchor="w", padx=15, pady=(15, 0))
        CTkLabel(card, textvariable=self.project_name_var,
                 font=CTkFont(size=16, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(0, 5))

        # 项目类型
        self.project_type_var = ctk.StringVar(value="")
        CTkLabel(card, textvariable=self.project_type_var,
                 font=FONT_SMALL, text_color=COLORS["text_secondary"], wraplength=230,
                 justify="left").pack(anchor="w", padx=15, pady=(0, 8))

        self.project_snapshot_var = ctk.StringVar(value="先建立一本书，再让 AI 帮你推进大纲和章节。")
        CTkLabel(card, textvariable=self.project_snapshot_var,
                 font=FONT_SMALL, text_color=COLORS["text_secondary"], wraplength=230,
                 justify="left").pack(anchor="w", padx=15, pady=(0, 15))

    def create_action_buttons(self):
        """创建快捷操作按钮"""
        self.create_sidebar_section("书稿", [
            ("新建长篇项目", self.new_project, "primary"),
            ("打开已有项目", self.open_project, "outline"),
            ("保存当前书稿", self.save_project, "outline"),
        ])

        self.create_sidebar_section("创作流水线", [
            ("1 生成总纲", self.generate_outline, "teal"),
            ("2 规划章节", self.plan_chapter, "outline"),
            ("3 写出正文", self.write_chapter, "primary"),
            ("4 续写当前章", self.continue_writing, "outline"),
            ("5 审稿体检", self.review_chapter, "outline"),
            ("6 润色打磨", self.polish_chapter, "outline"),
        ])

        self.create_sidebar_section("资料库", [
            ("打开资料库", self.open_library, "teal"),
            ("角色档案", self.view_characters, "outline"),
            ("世界观设定", self.edit_worldbuilding, "outline"),
            ("文风配方", self.style_settings, "outline"),
            ("数据看板", self.word_stats, "outline"),
        ])

        self.create_sidebar_section("发布", [
            ("导出可发布全文", self.export_novel, "primary"),
        ])

        # 主题切换
        theme_frame = CTkFrame(self.left_scroll, fg_color="transparent")
        theme_frame.pack(fill="x", padx=15, pady=(20, 15))

        CTkLabel(theme_frame, text="外观模式:", text_color=COLORS["text_primary"]).pack(side="left", padx=(0, 10))

        self.theme_var = ctk.StringVar(value=self.app_settings.get("appearance", "浅色"))
        theme_menu = CTkOptionMenu(theme_frame, values=["浅色", "深色", "系统"],
                                    variable=self.theme_var, command=self.change_theme,
                                    width=120, **menu_style())
        theme_menu.pack(side="right")

    def create_sidebar_section(self, title, buttons):
        """创建侧边栏分组"""
        CTkFrame(self.left_scroll, height=1, fg_color=COLORS["divider"]).pack(fill="x", padx=20, pady=(10, 0))
        CTkLabel(self.left_scroll, text=title,
                 font=FONT_SECTION, text_color=COLORS["text_primary"]).pack(anchor="w", padx=20, pady=(10, 5))

        for text, command, style in buttons:
            if style == "primary":
                kwargs = btn_primary()
            elif style == "teal":
                kwargs = btn_teal()
            else:
                kwargs = btn_outline()
            btn = CTkButton(self.left_scroll, text=text, command=command, anchor="w", **kwargs)
            btn.pack(fill="x", padx=15, pady=2)

    def create_right_panel(self):
        """创建右侧面板"""
        self.right_panel = CTkFrame(self.main_container, corner_radius=CORNER_RADIUS_XL,
                                     fg_color=COLORS["bg_main"])
        self.right_panel.pack(side="right", fill="both", expand=True)

        # 标签页视图
        self.tabview = CTkTabview(self.right_panel, corner_radius=CORNER_RADIUS_LG,
                                   segmented_button_fg_color=COLORS["bg_sidebar"],
                                   segmented_button_selected_color=COLORS["tab_selected"],
                                   segmented_button_selected_hover_color=COLORS["tab_selected_hover"],
                                   segmented_button_unselected_color=COLORS["bg_sidebar"],
                                   segmented_button_unselected_hover_color=COLORS["hover_outline"],
                                   text_color=COLORS["text_primary"],
                                   text_color_disabled=COLORS["text_secondary"])
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # 创建标签页
        self.create_dashboard_tab()
        self.create_writing_tab()
        self.create_outline_tab()
        self.create_library_tab()
        self.create_terminal_tab()
        self.create_log_tab()
        self.create_stats_tab()

    def create_dashboard_tab(self):
        """创建创作工作台"""
        self.tabview.add(TAB_DASHBOARD)

        page = CTkFrame(self.tabview.tab(TAB_DASHBOARD), fg_color="transparent")
        page.pack(fill="both", expand=True, padx=12, pady=12)

        hero = CTkFrame(page, corner_radius=CORNER_RADIUS_XL, fg_color=COLORS["bg_band"])
        hero.pack(fill="x", pady=(0, 12))

        hero_left = CTkFrame(hero, fg_color="transparent")
        hero_left.pack(side="left", fill="both", expand=True, padx=18, pady=16)

        CTkLabel(hero_left, text="今日创作台",
                 font=FONT_DISPLAY, text_color=COLORS["text_primary"]).pack(anchor="w")
        self.dashboard_subtitle_var = ctk.StringVar(value="打开一本书，开始推进大纲、章节和伏笔。")
        CTkLabel(hero_left, textvariable=self.dashboard_subtitle_var,
                 font=FONT_BODY, text_color=COLORS["text_secondary"],
                 wraplength=620, justify="left").pack(anchor="w", pady=(4, 0))

        hero_actions = CTkFrame(hero, fg_color="transparent")
        hero_actions.pack(side="right", padx=18, pady=16)
        CTkButton(hero_actions, text="规划下一章", command=self.plan_chapter,
                  width=120, **btn_teal()).pack(pady=3)
        CTkButton(hero_actions, text="开始写章", command=self.write_chapter,
                  width=120, **btn_primary()).pack(pady=3)

        cards = CTkFrame(page, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 12))
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="dash")

        self.dashboard_word_var = ctk.StringVar(value="0")
        self.dashboard_chapter_var = ctk.StringVar(value="0")
        self.dashboard_target_var = ctk.StringVar(value="0%")
        self.dashboard_engine_var = ctk.StringVar(value=self.get_ai_engine_label())

        self.create_metric_card(cards, 0, "总字数", self.dashboard_word_var, "正文累计中文字符")
        self.create_metric_card(cards, 1, "章节数", self.dashboard_chapter_var, "已生成章节文件")
        self.create_metric_card(cards, 2, "进度", self.dashboard_target_var, "距离目标字数")
        self.create_metric_card(cards, 3, "引擎", self.dashboard_engine_var, "当前 AI 执行器")

        lower = CTkFrame(page, fg_color="transparent")
        lower.pack(fill="both", expand=True)
        lower.grid_columnconfigure(0, weight=2)
        lower.grid_columnconfigure(1, weight=1)
        lower.grid_rowconfigure(0, weight=1)

        pipeline = CTkFrame(lower, corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_card"])
        pipeline.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        CTkLabel(pipeline, text="长篇生产线",
                 font=FONT_CARD_TITLE, text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 8))

        steps = [
            ("立项", "项目骨架、平台、读者和卖点", self.new_project),
            ("总纲", "主线、卷结构、核心爽点", self.generate_outline),
            ("章纲", "把剧情拆到可写场景", self.plan_chapter),
            ("正文", "按文风和设定生成章节", self.write_chapter),
            ("打磨", "审稿、润色、查漏补缺", self.review_chapter),
            ("发布", "合并章节并清理元信息", self.export_novel),
        ]
        for index, (name, desc, command) in enumerate(steps, 1):
            self.create_pipeline_row(pipeline, index, name, desc, command)

        side = CTkFrame(lower, corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_card"])
        side.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        CTkLabel(side, text="资料完整度",
                 font=FONT_CARD_TITLE, text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 8))

        self.dashboard_world_var = ctk.StringVar(value="世界观: 未打开项目")
        self.dashboard_role_var = ctk.StringVar(value="角色: 未打开项目")
        self.dashboard_outline_var = ctk.StringVar(value="大纲: 未打开项目")
        self.dashboard_note_var = ctk.StringVar(value="伏笔: 未打开项目")

        for var in (self.dashboard_world_var, self.dashboard_role_var,
                    self.dashboard_outline_var, self.dashboard_note_var):
            CTkLabel(side, textvariable=var, font=FONT_BODY,
                     text_color=COLORS["text_secondary"], wraplength=260,
                     justify="left").pack(anchor="w", padx=16, pady=5)

        CTkFrame(side, height=1, fg_color=COLORS["divider"]).pack(fill="x", padx=16, pady=10)
        CTkButton(side, text="进入资料库", command=self.open_library,
                  **btn_outline()).pack(fill="x", padx=16, pady=3)
        CTkButton(side, text="编辑世界观", command=self.edit_worldbuilding,
                  **btn_outline()).pack(fill="x", padx=16, pady=3)
        CTkButton(side, text="查看统计", command=self.word_stats,
                  **btn_teal()).pack(fill="x", padx=16, pady=(3, 14))


    def create_metric_card(self, parent, column, title, value_var, caption):
        """创建工作台指标卡"""
        card = CTkFrame(parent, corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_card"])
        card.grid(row=0, column=column, sticky="ew", padx=4)
        CTkLabel(card, text=title, font=FONT_SMALL,
                 text_color=COLORS["text_secondary"]).pack(anchor="w", padx=14, pady=(12, 0))
        CTkLabel(card, textvariable=value_var, font=CTkFont(size=22, weight="bold"),
                 text_color=COLORS["text_primary"]).pack(anchor="w", padx=14, pady=(0, 2))
        CTkLabel(card, text=caption, font=FONT_SMALL,
                 text_color=COLORS["text_secondary"]).pack(anchor="w", padx=14, pady=(0, 12))

    def create_pipeline_row(self, parent, index, name, desc, command):
        """创建生产线步骤行"""
        row = CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=4)

        badge = CTkLabel(row, text=f"{index}", width=28, height=28,
                         corner_radius=14, fg_color=COLORS["accent_alt"],
                         text_color=COLORS["text_btn_light"],
                         font=CTkFont(size=12, weight="bold"))
        badge.pack(side="left", padx=(0, 10))

        text_box = CTkFrame(row, fg_color="transparent")
        text_box.pack(side="left", fill="x", expand=True)
        CTkLabel(text_box, text=name, font=FONT_CARD_TITLE,
                 text_color=COLORS["text_primary"]).pack(anchor="w")
        CTkLabel(text_box, text=desc, font=FONT_SMALL,
                 text_color=COLORS["text_secondary"]).pack(anchor="w")

        CTkButton(row, text="执行", width=58, command=command,
                  **btn_ghost(height=28)).pack(side="right")

    def refresh_dashboard(self):
        """刷新创作工作台"""
        if not hasattr(self, 'dashboard_word_var'):
            return

        self.dashboard_engine_var.set(self.get_ai_engine_label())
        if not self.project_path:
            self.dashboard_subtitle_var.set("打开一本书，开始推进大纲、章节和伏笔。")
            self.dashboard_word_var.set("0")
            self.dashboard_chapter_var.set("0")
            self.dashboard_target_var.set("0%")
            self.dashboard_world_var.set("世界观: 未打开项目")
            self.dashboard_role_var.set("角色: 未打开项目")
            self.dashboard_outline_var.set("大纲: 未打开项目")
            self.dashboard_note_var.set("伏笔: 未打开项目")
            self.refresh_library()
            return

        project_name = self.project_config.get('name', '未命名')
        project_type = self.project_config.get('type', '未知题材')
        platform = self.project_config.get('platform', '未知平台')
        chapters = self.scan_chapters()
        total_words = sum(item["words"] for item in chapters)
        chapter_count = len({item["number"] for item in chapters})
        target_words = max(int(self.project_config.get('target_words', 0) or 0), 1)
        progress = min(total_words / target_words * 100, 999)

        self.dashboard_subtitle_var.set(f"《{project_name}》 · {project_type} · {platform}，继续把故事推进到下一处钩子。")
        self.dashboard_word_var.set(str(total_words))
        self.dashboard_chapter_var.set(str(chapter_count))
        self.dashboard_target_var.set(f"{progress:.1f}%")

        self.dashboard_world_var.set(self.get_material_status("世界观", os.path.join(self.project_path, 'worldbuilding', 'settings.md')))
        self.dashboard_role_var.set(self.get_character_status())
        self.dashboard_outline_var.set(self.get_material_status("大纲", os.path.join(self.project_path, 'outline', 'master-outline.md')))
        self.dashboard_note_var.set(self.get_material_status("伏笔", os.path.join(self.project_path, 'notes', 'misc.md')))

        if hasattr(self, 'project_snapshot_var'):
            self.project_snapshot_var.set(f"{chapter_count} 章 · {total_words} 字 · 进度 {progress:.1f}%")
        self.refresh_library()

    def get_material_status(self, label, path):
        """获取资料文件状态"""
        if not os.path.exists(path):
            return f"{label}: 未建立"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception:
            return f"{label}: 无法读取"
        meaningful_lines = [
            line for line in content.splitlines()
            if line.strip() and not line.strip().startswith('#') and '：' in line and not line.rstrip().endswith('：')
        ]
        if meaningful_lines:
            return f"{label}: 已填 {len(meaningful_lines)} 项"
        return f"{label}: 有模板，待补完"

    def get_character_status(self):
        """获取角色资料状态"""
        if not self.project_path:
            return "角色: 未打开项目"
        characters_dir = os.path.join(self.project_path, 'characters')
        if not os.path.exists(characters_dir):
            return "角色: 未建立"
        files = [f for f in os.listdir(characters_dir) if f.endswith('.md') and f != 'index.md']
        if not files:
            return "角色: 暂无角色卡"
        return f"角色: {len(files)} 张角色卡"

    def create_writing_tab(self):
        """创建写作标签页"""
        self.tabview.add(TAB_WRITING)

        # 工具栏
        toolbar = CTkFrame(self.tabview.tab(TAB_WRITING), fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        CTkLabel(toolbar, text="章节工位", font=FONT_DISPLAY,
                 text_color=COLORS["text_primary"]).pack(side="left", padx=5)
        CTkButton(toolbar, text="保存章节", command=self.save_chapter,
                  width=110, **btn_primary()).pack(side="right", padx=5)
        CTkButton(toolbar, text="续写", command=self.continue_writing,
                  width=90, **btn_outline()).pack(side="right", padx=5)
        CTkButton(toolbar, text="润色", command=self.polish_chapter,
                  width=90, **btn_outline()).pack(side="right", padx=5)

        # 章节选择
        chapter_frame = CTkFrame(self.tabview.tab(TAB_WRITING), fg_color="transparent")
        chapter_frame.pack(fill="x", padx=10, pady=5)

        CTkLabel(chapter_frame, text="当前章节:", text_color=COLORS["text_secondary"]).pack(side="left", padx=(0, 10))
        self.chapter_var = ctk.StringVar(value="暂无章节")
        self.chapter_menu = CTkOptionMenu(chapter_frame, values=["暂无章节"],
                                          variable=self.chapter_var, width=150,
                                          command=self._on_chapter_selected,
                                          **menu_style())
        self.chapter_menu.pack(side="left")
        self.prev_chapter_button = CTkButton(chapter_frame, text="上一章",
                                             command=self.previous_chapter,
                                             width=86, state="disabled",
                                             **btn_outline())
        self.prev_chapter_button.pack(side="left", padx=(8, 0))
        self.next_chapter_button = CTkButton(chapter_frame, text="下一章",
                                             command=self.next_chapter,
                                             width=86, state="disabled",
                                             **btn_outline())
        self.next_chapter_button.pack(side="left", padx=(8, 0))

        self.word_count_var = ctk.StringVar(value="字数: 0")
        CTkLabel(chapter_frame, textvariable=self.word_count_var,
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(side="right")

        workspace = CTkFrame(self.tabview.tab(TAB_WRITING), fg_color="transparent")
        workspace.pack(fill="both", expand=True, padx=10, pady=10)
        workspace.grid_columnconfigure(0, weight=3)
        workspace.grid_columnconfigure(1, weight=1)
        workspace.grid_rowconfigure(0, weight=1)

        # 写作区域
        self.writing_text = CTkTextbox(workspace,
                                        font=FONT_BODY,
                                        corner_radius=CORNER_RADIUS_LG,
                                        fg_color=COLORS["bg_input"],
                                        border_width=1,
                                        border_color=COLORS["border"])
        self.writing_text.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        aide = CTkFrame(workspace, corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_card"])
        aide.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        CTkLabel(aide, text="章前检查", font=FONT_CARD_TITLE,
                 text_color=COLORS["text_primary"]).pack(anchor="w", padx=14, pady=(14, 8))
        tips = [
            "读取上一章结尾，确认衔接点",
            "核对本章梗概和章末钩子",
            "确认登场角色的口吻和动机",
            "检查需要埋设或回收的伏笔",
            "写完后更新 project.md 和 notes/misc.md",
        ]
        for tip in tips:
            CTkLabel(aide, text=f"- {tip}", font=FONT_SMALL,
                     text_color=COLORS["text_secondary"], wraplength=250,
                     justify="left").pack(anchor="w", padx=14, pady=3)

        CTkFrame(aide, height=1, fg_color=COLORS["divider"]).pack(fill="x", padx=14, pady=10)
        CTkButton(aide, text="规划本章", command=self.plan_chapter,
                  **btn_teal()).pack(fill="x", padx=14, pady=3)
        CTkButton(aide, text="写新章节", command=self.write_chapter,
                  **btn_primary()).pack(fill="x", padx=14, pady=3)
        CTkButton(aide, text="审稿体检", command=self.review_chapter,
                  **btn_outline()).pack(fill="x", padx=14, pady=3)

        # 绑定字数统计
        self.writing_text.bind("<KeyRelease>", lambda _: self.update_word_count())

    def create_outline_tab(self):
        """创建大纲标签页"""
        self.tabview.add(TAB_OUTLINE)

        # 工具栏
        toolbar = CTkFrame(self.tabview.tab(TAB_OUTLINE), fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        CTkLabel(toolbar, text="故事地图", font=FONT_DISPLAY,
                 text_color=COLORS["text_primary"]).pack(side="left", padx=5)
        CTkButton(toolbar, text="生成总大纲", command=self.generate_outline,
                  width=130, **btn_primary()).pack(side="right", padx=5)
        CTkButton(toolbar, text="生成卷大纲", command=self.generate_volume_outline,
                  width=130, **btn_teal()).pack(side="right", padx=5)
        CTkButton(toolbar, text="保存大纲", command=self.save_outline,
                  width=110, **btn_outline()).pack(side="right", padx=5)

        # 大纲选择区域
        outline_selector = CTkFrame(self.tabview.tab(TAB_OUTLINE), fg_color="transparent")
        outline_selector.pack(fill="x", padx=10, pady=5)

        CTkLabel(outline_selector, text="查看大纲:", text_color=COLORS["text_secondary"]).pack(side="left", padx=(0, 10))

        self.outline_var = ctk.StringVar(value="总大纲")
        self.outline_menu = CTkOptionMenu(outline_selector, values=["总大纲"],
                                          variable=self.outline_var, width=150,
                                          command=self._on_outline_selected,
                                          **menu_style())
        self.outline_menu.pack(side="left")

        CTkButton(outline_selector, text="刷新", command=self.load_outline,
                  width=90, **btn_ghost()).pack(side="left", padx=10)

        outline_workspace = CTkFrame(self.tabview.tab(TAB_OUTLINE), fg_color="transparent")
        outline_workspace.pack(fill="both", expand=True, padx=10, pady=10)
        outline_workspace.grid_columnconfigure(0, weight=3)
        outline_workspace.grid_columnconfigure(1, weight=1)
        outline_workspace.grid_rowconfigure(0, weight=1)

        # 大纲显示区域
        self.outline_text = CTkTextbox(outline_workspace,
                                        font=FONT_BODY,
                                        corner_radius=CORNER_RADIUS_LG,
                                        fg_color=COLORS["bg_input"],
                                        border_width=1,
                                        border_color=COLORS["border"])
        self.outline_text.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        outline_guide = CTkFrame(outline_workspace, corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_card"])
        outline_guide.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        CTkLabel(outline_guide, text="规划节奏", font=FONT_CARD_TITLE,
                 text_color=COLORS["text_primary"]).pack(anchor="w", padx=14, pady=(14, 8))
        guide_lines = [
            "总纲先定主线、卖点和多卷结构",
            "卷纲负责阶段目标、反派和升级节点",
            "章纲要落到场景、冲突和章末钩子",
            "偏离大纲时同步更新 chapter-outs",
        ]
        for line in guide_lines:
            CTkLabel(outline_guide, text=f"- {line}", font=FONT_SMALL,
                     text_color=COLORS["text_secondary"], wraplength=250,
                     justify="left").pack(anchor="w", padx=14, pady=4)
        CTkFrame(outline_guide, height=1, fg_color=COLORS["divider"]).pack(fill="x", padx=14, pady=10)
        CTkButton(outline_guide, text="规划章节", command=self.plan_chapter,
                  **btn_teal()).pack(fill="x", padx=14, pady=3)
        CTkButton(outline_guide, text="开始写章", command=self.write_chapter,
                  **btn_primary()).pack(fill="x", padx=14, pady=3)

    def create_library_tab(self):
        """创建资料库标签页"""
        self.tabview.add(TAB_LIBRARY)

        page = CTkFrame(self.tabview.tab(TAB_LIBRARY), fg_color="transparent")
        page.pack(fill="both", expand=True, padx=12, pady=12)
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=1)
        page.grid_rowconfigure(1, weight=1)

        header = CTkFrame(page, corner_radius=CORNER_RADIUS_XL, fg_color=COLORS["bg_band"])
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        CTkLabel(header, text="资料库",
                 font=FONT_DISPLAY, text_color=COLORS["text_primary"]).pack(anchor="w", padx=18, pady=(16, 4))
        CTkLabel(header, text="把角色、世界观、文风和伏笔集中管理，避免长篇写到后面设定漂移。",
                 font=FONT_BODY, text_color=COLORS["text_secondary"],
                 wraplength=760, justify="left").pack(anchor="w", padx=18, pady=(0, 16))

        status_card = CTkFrame(page, corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_card"])
        status_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        CTkLabel(status_card, text="资料体检",
                 font=FONT_CARD_TITLE, text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 8))

        self.library_world_var = ctk.StringVar(value="世界观: 未打开项目")
        self.library_role_var = ctk.StringVar(value="角色: 未打开项目")
        self.library_style_var = ctk.StringVar(value="文风: 未打开项目")
        self.library_note_var = ctk.StringVar(value="伏笔: 未打开项目")

        for var in (self.library_world_var, self.library_role_var,
                    self.library_style_var, self.library_note_var):
            CTkLabel(status_card, textvariable=var, font=FONT_BODY,
                     text_color=COLORS["text_secondary"], wraplength=330,
                     justify="left").pack(anchor="w", padx=16, pady=5)

        CTkLabel(status_card, text="建议顺序: 先补世界规则，再补角色动机，最后校准文风和伏笔回收。",
                 font=FONT_SMALL, text_color=COLORS["text_secondary"],
                 wraplength=330, justify="left").pack(anchor="w", padx=16, pady=(14, 16))

        actions = CTkFrame(page, corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_card"])
        actions.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        CTkLabel(actions, text="资料动作",
                 font=FONT_CARD_TITLE, text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 8))

        cards = [
            ("角色档案", "新增、编辑角色卡，追踪口吻、关系和角色弧线。", self.view_characters, "primary"),
            ("世界观设定", "维护力量体系、地图、阵营、规则和禁忌。", self.edit_worldbuilding, "teal"),
            ("文风配方", "校准平台风格、叙事节奏、对话口味和禁用表达。", self.style_settings, "outline"),
            ("伏笔笔记", "记录埋设章节、计划回收和实际回收状态。", self.edit_notes, "outline"),
        ]
        for title, desc, command, style in cards:
            self.create_library_action(actions, title, desc, command, style)

        self.refresh_library()

    def create_library_action(self, parent, title, desc, command, style):
        """创建资料库动作卡"""
        card = CTkFrame(parent, corner_radius=CORNER_RADIUS_MD, fg_color=COLORS["bg_input"],
                        border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", padx=14, pady=5)

        text_box = CTkFrame(card, fg_color="transparent")
        text_box.pack(side="left", fill="x", expand=True, padx=12, pady=10)
        CTkLabel(text_box, text=title, font=FONT_CARD_TITLE,
                 text_color=COLORS["text_primary"]).pack(anchor="w")
        CTkLabel(text_box, text=desc, font=FONT_SMALL,
                 text_color=COLORS["text_secondary"], wraplength=300,
                 justify="left").pack(anchor="w", pady=(2, 0))

        if style == "primary":
            button_kwargs = btn_primary(width=76)
        elif style == "teal":
            button_kwargs = btn_teal(width=76)
        else:
            button_kwargs = btn_outline(width=76)
        CTkButton(card, text="打开", command=command,
                  **button_kwargs).pack(side="right", padx=12, pady=10)

    def refresh_library(self):
        """刷新资料库状态"""
        if not hasattr(self, 'library_world_var'):
            return

        if not self.project_path:
            self.library_world_var.set("世界观: 未打开项目")
            self.library_role_var.set("角色: 未打开项目")
            self.library_style_var.set("文风: 未打开项目")
            self.library_note_var.set("伏笔: 未打开项目")
            return

        self.library_world_var.set(self.get_material_status("世界观", os.path.join(self.project_path, 'worldbuilding', 'settings.md')))
        self.library_role_var.set(self.get_character_status())
        self.library_style_var.set(self.get_material_status("文风", os.path.join(self.project_path, 'style', 'style-config.md')))
        self.library_note_var.set(self.get_material_status("伏笔", os.path.join(self.project_path, 'notes', 'misc.md')))

    def open_library(self):
        """打开资料库标签页"""
        self.refresh_library()
        self.tabview.set(TAB_LIBRARY)

    def create_terminal_tab(self):
        """创建终端标签页"""
        self.tabview.add(TAB_STUDIO)

        # 进度提示区域
        self.progress_frame = CTkFrame(self.tabview.tab(TAB_STUDIO), height=44,
                                        corner_radius=CORNER_RADIUS_MD,
                                        fg_color=COLORS["status_ready"])
        self.progress_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.progress_frame.pack_propagate(False)

        self.progress_label = CTkLabel(self.progress_frame, text="就绪",
                                        font=CTkFont(size=13, weight="bold"),
                                        text_color=COLORS["text_on_status"])
        self.progress_label.pack(expand=True)

        # 工具栏
        toolbar = CTkFrame(self.tabview.tab(TAB_STUDIO), fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=5)

        CTkLabel(toolbar, text="AI 编剧室", font=FONT_DISPLAY,
                 text_color=COLORS["text_primary"]).pack(side="left", padx=5)
        CTkButton(toolbar, text="清空对话", command=self.clear_terminal,
                  width=100, **btn_ghost()).pack(side="right", padx=5)
        CTkButton(toolbar, text="Codex 诊断", command=self.run_codex_diagnostics,
                  width=110, **btn_info()).pack(side="right", padx=5)

        # 终端输出区域（聊天式界面）
        self.terminal_text = CTkTextbox(self.tabview.tab(TAB_STUDIO),
                                         font=FONT_MONO,
                                         corner_radius=CORNER_RADIUS_LG,
                                         fg_color=COLORS["bg_input"],
                                         border_width=1,
                                         border_color=COLORS["border"],
                                         state="disabled")
        self.terminal_text.pack(fill="both", expand=True, padx=10, pady=5)

        # 聊天输入区域（合并命令和回复）
        chat_frame = CTkFrame(self.tabview.tab(TAB_STUDIO), fg_color="transparent")
        chat_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.chat_var = ctk.StringVar(value=self.get_default_prompt())
        self.chat_entry = CTkEntry(chat_frame, textvariable=self.chat_var,
                                    height=BTN_HEIGHT_LG, corner_radius=CORNER_RADIUS_LG,
                                    fg_color=COLORS["bg_input"],
                                    border_width=1, border_color=COLORS["border"])
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.chat_entry.bind("<Return>", lambda _: self.send_message())

        CTkButton(chat_frame, text="发送", command=self.send_message,
                  width=90, **btn_primary()).pack(side="left", padx=5)
        CTkButton(chat_frame, text="停止", command=self.stop_command,
                  width=90, **btn_danger()).pack(side="left", padx=5)

        # 绑定输入框聚焦高亮
        self._bind_focus_highlight(self.chat_entry)

    def create_log_tab(self):
        """创建日志标签页"""
        self.tabview.add(TAB_LOG)

        # 工具栏
        toolbar = CTkFrame(self.tabview.tab(TAB_LOG), fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        CTkButton(toolbar, text="清空日志", command=self.clear_log,
                  width=100, **btn_ghost()).pack(side="right", padx=5)
        CTkButton(toolbar, text="导出日志", command=self.export_log,
                  width=100, **btn_ghost()).pack(side="right", padx=5)

        # 日志显示区域
        self.log_text = CTkTextbox(self.tabview.tab(TAB_LOG),
                                    font=FONT_MONO,
                                    corner_radius=CORNER_RADIUS_LG,
                                    fg_color=COLORS["bg_input"],
                                    border_width=1,
                                    border_color=COLORS["border"],
                                    state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(5, 10))

    def _append_log(self, text, level="INFO"):
        """追加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {text}\n"

        self.log_text.configure(state="normal")
        self.log_text.insert("end", log_entry)
        self._trim_output(self.log_text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        """清空日志"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def export_log(self):
        """导出日志"""
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt")]
        )
        if filepath:
            content = self.log_text.get("1.0", "end")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self._append_log(f"日志已导出到: {filepath}")

    def _bind_focus_highlight(self, entry):
        """为输入框绑定聚焦高亮效果"""
        def on_focus_in(_):
            entry.configure(border_color=get_color("border_focus"), border_width=2)
        def on_focus_out(_):
            entry.configure(border_color=get_color("border"), border_width=1)
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def create_stats_tab(self):
        """创建统计标签页"""
        self.tabview.add(TAB_STATS)

        # 工具栏
        toolbar = CTkFrame(self.tabview.tab(TAB_STATS), fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        CTkLabel(toolbar, text="数据看板", font=FONT_DISPLAY,
                 text_color=COLORS["text_primary"]).pack(side="left", padx=5)
        CTkButton(toolbar, text="刷新统计", command=self.refresh_stats,
                  width=110, **btn_primary()).pack(side="right", padx=5)
        CTkButton(toolbar, text="导出报告", command=self.export_stats,
                  width=110, **btn_outline()).pack(side="right", padx=5)

        # 统计信息显示
        self.stats_text = CTkTextbox(self.tabview.tab(TAB_STATS),
                                      font=FONT_BODY,
                                      corner_radius=CORNER_RADIUS_LG,
                                      fg_color=COLORS["bg_input"],
                                      border_width=1,
                                      border_color=COLORS["border"])
        self.stats_text.pack(fill="both", expand=True, padx=10, pady=10)

    def create_status_bar(self):
        """创建状态栏"""
        status_frame = CTkFrame(self.root, height=35, corner_radius=0,
                                 fg_color=COLORS["bg_sidebar"])
        status_frame.pack(fill="x", side="bottom")

        self.status_var = ctk.StringVar(value="就绪")
        CTkLabel(status_frame, textvariable=self.status_var,
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(side="left", padx=15)

        # 右侧信息
        self.status_project_var = ctk.StringVar(value="")
        CTkLabel(status_frame, textvariable=self.status_project_var,
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(side="left", padx=10)

        self.status_words_var = ctk.StringVar(value="")
        CTkLabel(status_frame, textvariable=self.status_words_var,
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(side="left", padx=10)

        self.status_time_var = ctk.StringVar(value="")
        CTkLabel(status_frame, textvariable=self.status_time_var,
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(side="right", padx=15)

        # 启动时间更新
        self._update_status_time()

    def _update_status_time(self):
        """更新状态栏时间"""
        self.status_time_var.set(datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._update_status_time)

    def update_status_project(self):
        """更新状态栏项目信息"""
        if self.project_path:
            path = self.project_path
            if len(path) > 40:
                path = "..." + path[-37:]
            self.status_project_var.set(f"📁 {path}")
        else:
            self.status_project_var.set("")

    def update_status_words(self):
        """更新状态栏字数信息"""
        if hasattr(self, 'writing_text'):
            content = self.writing_text.get("1.0", "end")
            words = self.count_cjk_characters(content)
            self.status_words_var.set(f"📝 {words} 字")

    def change_theme(self, mode):
        """切换主题"""
        if mode == "浅色":
            ctk.set_appearance_mode("light")
        elif mode == "深色":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("system")
        self.app_settings["appearance"] = mode
        self.save_app_settings()

    def normalize_user_message(self, message):
        """去掉 Codex Skill 前缀，得到实际写作指令"""
        normalized = message.strip()
        prefix = "$novel-write"
        if normalized == prefix:
            return ""
        if normalized.startswith(prefix + " "):
            return normalized[len(prefix):].strip()
        return normalized

    def build_codex_prompt(self, message):
        """构造 Codex 非交互提示"""
        task = self.normalize_user_message(message)
        if not task:
            task = "查看当前小说项目状态，并给出下一步建议"

        project_hint = "当前目录就是小说项目根目录。"
        if self.project_path:
            project_hint = f"当前小说项目根目录: {self.project_path}"

        return f"""$novel-write

请使用工作区内的 novel-write skill 处理下面的网文写作任务。
{project_hint}

用户任务:
{task}

执行要求:
- 优先读取项目中的 project.md、outline、chapters、characters、worldbuilding、style、notes 等上下文；若存在 notes/canon.md，先把它作为已确认事实清单。
- 在 Windows 上读取中文 Markdown/Skill 文件时必须指定 UTF-8，例如 PowerShell 使用 `Get-Content -Encoding UTF8`；不要使用默认编码读取。
- 需要生成或修改内容时，直接写入当前小说项目对应文件。
- 保持章节、大纲、人物、世界观、正典和伏笔记录一致。
- 每章明确记录一次主动选择、选择代价和结束时的状态变化；远期伏笔要在近期产生可验证的回报、误导或代价。
- 最后简要说明完成了什么，以及修改了哪些文件。
"""

    def build_ai_command(self, message):
        """构造 Codex 命令；任务文本只经 stdin 传入，不经过命令壳解析。"""
        prompt = self.build_codex_prompt(message)
        cmd = build_codex_cli_command([
            "--ask-for-approval", "never",
            "exec",
            "--skip-git-repo-check",
            "--sandbox", "workspace-write",
            "--color", "never",
            "-",
        ])
        return cmd, prompt

    def build_ai_environment(self):
        """构造 AI 子进程环境变量。"""
        env = os.environ.copy()
        codex_path = resolve_codex_path(env)
        if codex_path:
            codex_directory = os.path.dirname(codex_path)
            env["PATH"] = codex_directory + os.pathsep + env.get("PATH", "")
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("LANG", "C.UTF-8")
        env.setdefault("LC_ALL", "C.UTF-8")
        return env

    def get_failure_hint(self):
        """根据当前引擎和最近输出生成失败提示"""
        output = getattr(self, '_last_command_output', '')
        if 'Missing optional dependency' in output:
            return "[Codex 提示] Codex CLI 安装不完整，请运行：npm install -g @openai/codex@latest\n"
        if 'not logged in' in output.lower() or 'login' in output.lower():
            return "[Codex 提示] 请先运行 codex login 完成登录。\n"
        if '503 Service Unavailable' in output or '127.0.0.1' in output:
            return (
                "[Codex 提示] 检测到本地服务或代理连接失败。请确认 Codex Desktop/本地代理正在运行，"
                "codex login 有效，或点击“Codex 诊断”查看详情。\n"
            )
        if 'unrecognized option' in output.lower() or 'unexpected argument' in output.lower():
            return "[Codex 提示] 当前 Codex CLI 参数可能不兼容，请运行：codex update 或 npm install -g @openai/codex@latest\n"
        return "[Codex 提示] 请确认已安装并登录 Codex CLI：npm install -g @openai/codex@latest，然后运行 codex login。\n"

    def preflight_ai_command(self, cwd):
        """执行前做快速检查，避免明显不可用的 CLI 配置长时间卡住。"""
        codex_path = resolve_codex_path()
        if not codex_path:
            return ("未找到 Codex CLI。请安装并登录 Codex，或把 codex.exe 放入 PATH；"
                    "npm 安装命令：npm install -g @openai/codex@latest")
        return None

    def check_codex_login_status(self, cwd):
        """快速确认 Codex CLI 是否有可用登录凭据。"""
        returncode, output, timed_out = self.run_command_with_timeout(
            build_codex_cli_command(["login", "status"]),
            cwd,
            timeout=8,
        )
        if timed_out:
            return False, "codex login status 超时"
        if returncode == 0 and ("Logged in" in output or "登录" in output):
            return True, output.strip()
        return False, output.strip() or f"returncode={returncode}"

    def run_command_with_timeout(self, cmd, cwd, timeout=10):
        """运行短命令；超时时杀掉完整进程树，避免残留 codex/node。"""
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=cwd,
                env=self.build_ai_environment(),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            try:
                output_bytes, _ = proc.communicate(timeout=timeout)
                output = output_bytes.decode("utf-8", errors="replace") if output_bytes else ""
                return proc.returncode, output, False
            except subprocess.TimeoutExpired:
                self.kill_process_tree(proc.pid)
                try:
                    output_bytes, _ = proc.communicate(timeout=2)
                except Exception:
                    output_bytes = b""
                output = output_bytes.decode("utf-8", errors="replace") if output_bytes else ""
                return -1, output, True
        except Exception as e:
            return -1, str(e), False

    def kill_process_tree(self, pid):
        """终止 Windows 进程树。"""
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                timeout=5,
            )
        except Exception:
            pass

    def get_codex_local_provider_info(self):
        """解析 ~/.codex/config.toml 中当前 provider 的安全摘要。"""
        codex_home = os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex")
        config_path = os.path.join(codex_home, "config.toml")
        info = {"config_path": config_path, "model_provider": "", "base_url": ""}
        if not os.path.exists(config_path):
            return info

        current_section = ""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("[") and line.endswith("]"):
                        current_section = line[1:-1].strip()
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if not current_section and key == "model_provider":
                        info["model_provider"] = value
                    elif key == "base_url":
                        provider = info.get("model_provider")
                        if not provider or current_section == f"model_providers.{provider}":
                            info["base_url"] = value
        except Exception as e:
            info["error"] = str(e)
        return info

    def probe_codex_base_url(self, base_url):
        """快速探测 OpenAI 兼容 provider 是否有可用的基础路由。"""
        if not base_url:
            return False, "未配置 base_url"
        try:
            from urllib import request, error
            root_url = base_url.rstrip("/")

            def probe(url, method="GET", body=None):
                data = body.encode("utf-8") if body else None
                headers = {"Content-Type": "application/json"} if body else {}
                req = request.Request(url, data=data, headers=headers, method=method)
                try:
                    with request.urlopen(req, timeout=5) as response:
                        content = response.read(500).decode("utf-8", errors="replace")
                        return getattr(response, "status", 0), content
                except error.HTTPError as e:
                    content = e.read(500).decode("utf-8", errors="replace")
                    return e.code, content

            models_url = root_url + "/models"
            models_status, _ = probe(models_url)
            if models_status in (200, 401, 403):
                return True, f"{models_url} HTTP {models_status}"

            responses_url = root_url + "/responses"
            responses_status, responses_content = probe(responses_url)
            if responses_status in (200, 401, 403, 405):
                return True, f"{responses_url} HTTP {responses_status}"

            detail = f"{models_url} HTTP {models_status}; {responses_url} HTTP {responses_status}"
            if responses_content:
                detail += f"; responses: {responses_content[:180]}"
            return False, detail
        except Exception as e:
            return False, str(e)

    def find_local_port_owner(self, base_url):
        """返回本地 base_url 端口对应的进程，辅助定位 cc-switch 等代理。"""
        match = re.search(r":(\d+)", base_url)
        if not match:
            return "未识别端口"
        port = match.group(1)
        try:
            completed = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"$c=Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; "
                 "$p=if($c){Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue}; "
                 "if($p){\"$($p.ProcessName) PID=$($p.Id)\"}else{\"未找到监听进程\"}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                timeout=5,
                env=self.build_ai_environment(),
                encoding="utf-8",
                errors="replace",
            )
            return (completed.stdout or "").strip() or "未找到监听进程"
        except Exception as e:
            return f"查询失败: {e}"

    def read_process_output(self, proc=None):
        """读取 Codex 子进程的实时输出。"""
        self.read_raw_process_output(proc)

    def read_raw_process_output(self, proc=None):
        """按块读取原始终端输出。"""
        proc = proc or self.proc
        if not proc or not proc.stdout:
            return
        fd = proc.stdout.fileno()
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        while True:
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            text = decoder.decode(chunk)
            text = repair_mojibake_text(text)
            self.record_command_output(text)
            if not self._closing:
                self._post_ui(self._append_terminal, text)
        remaining = decoder.decode(b"", final=True)
        if remaining:
            self.record_command_output(remaining)
            if not self._closing:
                self._post_ui(self._append_terminal, remaining)

    def record_command_output(self, text):
        """保存最近输出用于失败提示。"""
        self._last_command_output += text
        if len(self._last_command_output) > 6000:
            self._last_command_output = self._last_command_output[-6000:]

    # ==================== AI 命令执行 ====================

    def send_message(self):
        """发送消息（统一命令和回复）"""
        if self._cmd_running:
            self._terminal_write("\n[请稍候] 当前 Codex 任务尚未完成。\n")
            return
        message = self.chat_var.get().strip()
        if not message:
            return
        if not self.project_path:
            messagebox.showwarning("提示", "请先新建或打开小说项目，再执行 AI 写作任务。")
            return

        project_path = os.path.abspath(self.project_path)
        if not os.path.isdir(project_path):
            messagebox.showwarning("项目不可用", "当前小说项目目录不存在，请重新打开项目。")
            return
        if not self._save_current_chapter_if_dirty():
            return
        if self._is_outline_dirty() and not self.save_outline():
            return
        # 所有命令构建与界面状态读取均在主线程完成。
        cmd, stdin_text = self.build_ai_command(message)

        # 清空输入框
        self.chat_var.set("")

        # 显示用户消息
        engine_name = self.get_ai_engine_label()
        self._terminal_write(f"\n[{engine_name}] >>> {message}\n\n")

        # 记录日志
        self._append_log(f"{engine_name} 执行命令: {message}", "CMD")

        self._cmd_start_time = time.time()
        self._cmd_running = True
        self._cancel_command.clear()
        self.set_document_editors_enabled(False)
        self._last_command_output = ""
        self._update_running_status(f"{engine_name} 正在处理")

        def _run():
            proc = None
            try:
                cwd = project_path
                if not ensure_skill_files(cwd):
                    if not self._closing:
                        self._post_ui(
                            self._command_preflight_failed,
                            "无法释放项目所需的 Codex Skill 文件，请检查安装目录权限。",
                        )
                    return

                preflight_error = self.preflight_ai_command(cwd)
                if preflight_error:
                    if not self._closing:
                        self._post_ui(self._command_preflight_failed, preflight_error)
                    return

                if self._closing or self._cancel_command.is_set():
                    self._post_ui(self._command_done, -1, project_path)
                    return

                # 记录命令执行前的文件状态
                old_state = self._get_file_state(cwd)

                stdin_arg = subprocess.PIPE if stdin_text else subprocess.DEVNULL

                proc = subprocess.Popen(
                    cmd,
                    stdin=stdin_arg,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=cwd,
                    env=self.build_ai_environment(),
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    bufsize=0  # 禁用缓冲，实时输出
                )

                self.proc = proc
                if self._closing or self._cancel_command.is_set():
                    self.kill_process_tree(proc.pid)
                    proc.wait(timeout=5)
                    self._post_ui(self._command_done, -1, project_path)
                    return
                if stdin_text and proc.stdin:
                    proc.stdin.write(stdin_text.encode("utf-8"))
                    proc.stdin.close()

                self.read_process_output(proc)
                proc.wait()

                if self._closing:
                    return

                # 记录命令执行后的文件状态，显示变化
                new_state = self._get_file_state(cwd)
                changes = self._get_file_changes(old_state, new_state)
                if changes:
                    self._post_ui(self._append_terminal, "\n--- 文件修改记录 ---\n")
                    for change in changes:
                        self._post_ui(self._append_terminal, change + "\n")
                        # 记录到日志面板
                        self._post_ui(self._append_log, change, "FILE")

                if not self._closing:
                    self._post_ui(self._command_done, proc.returncode, project_path)
            except Exception as e:
                if proc is not None and proc.poll() is None:
                    self.kill_process_tree(proc.pid)
                if not self._closing:
                    self._post_ui(self._command_error, str(e))
            finally:
                if proc is not None:
                    for stream in (proc.stdin, proc.stdout):
                        if stream is not None:
                            stream.close()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _command_preflight_failed(self, message):
        """执行前检查失败时显示可操作原因。"""
        self._cmd_running = False
        self.set_document_editors_enabled(True)
        self.proc = None
        self._terminal_write(f"\n[执行前检查失败]\n{message}\n")
        self._terminal_write(f"{'='*60}\n\n")
        self.update_status("执行前检查失败")
        self._append_log(f"执行前检查失败: {message}", "ERROR")
        self.progress_label.configure(text="检查失败")
        self.progress_frame.configure(fg_color=COLORS["status_error"])
        self.root.after(3000, self._reset_progress)

    def stop_command(self):
        """终止正在运行的命令"""
        if not self._cmd_running:
            self._terminal_write("\n[没有正在运行的命令]\n")
            return
        self._cancel_command.set()
        self.update_status("正在停止命令")
        self._terminal_write("\n[正在停止 Codex 任务]\n")
        proc = self.proc
        if proc is not None and proc.poll() is None:
            threading.Thread(target=self.kill_process_tree, args=(proc.pid,), daemon=True).start()

    def _terminal_write(self, text):
        """向只读终端写入文本"""
        text = repair_mojibake_text(str(text))
        self.terminal_text.configure(state="normal")
        self.terminal_text.insert("end", text)
        self._trim_output(self.terminal_text)
        self.terminal_text.see("end")
        self.terminal_text.configure(state="disabled")

    def _append_terminal(self, text):
        """追加文本到终端"""
        self._terminal_write(text)

    @staticmethod
    def _trim_output(widget, max_characters=300000):
        """限制长任务的显示缓存，避免终端持续增长拖慢界面。"""
        count = widget._textbox.count("1.0", "end-1c", "chars")
        length = int(count[0]) if count else 0
        if length > max_characters:
            widget.delete("1.0", f"1.0+{length - max_characters}c")

    def _command_done(self, returncode, project_path=None):
        """命令执行完成"""
        self._cmd_running = False
        self.set_document_editors_enabled(True)
        self.proc = None
        elapsed = time.time() - getattr(self, '_cmd_start_time', time.time())
        elapsed_str = f"{elapsed:.1f}秒" if elapsed < 60 else f"{elapsed/60:.1f}分钟"
        if self._cancel_command.is_set():
            self._terminal_write(f"\n[任务已停止，耗时 {elapsed_str}]\n")
            self.update_status("任务已停止；已写入的文件保留")
            self.progress_label.configure(text="已停止")
            self.progress_frame.configure(fg_color=COLORS["status_ready"])
        elif returncode == 0:
            self._terminal_write(f"\n[命令执行完成，耗时 {elapsed_str}]\n")
            self.update_status(f"命令执行完成，耗时 {elapsed_str}")
            self.progress_label.configure(text=f"✅ 完成 ({elapsed_str})")
            self.progress_frame.configure(fg_color=COLORS["status_success"])
            self._append_log(f"命令执行完成，耗时 {elapsed_str}", "OK")
        else:
            self._terminal_write(f"\n[命令执行失败，返回码: {returncode}，耗时 {elapsed_str}]\n")
            self._terminal_write(self.get_failure_hint())
            self.update_status(f"命令执行失败，耗时 {elapsed_str}")
            self.progress_label.configure(text=f"❌ 失败 ({elapsed_str})")
            self.progress_frame.configure(fg_color=COLORS["status_error"])
        self._terminal_write(f"{'='*60}\n\n")
        if self.project_path and (project_path is None or os.path.abspath(self.project_path) == project_path):
            self.refresh_stats()
            self._load_chapter_list(preserve_current=True, reload_current=not self._is_current_chapter_dirty())
            self.load_outline(confirm_switch=False)

        # 3秒后恢复就绪状态
        self.root.after(3000, self._reset_progress)

    def _reset_progress(self):
        """重置进度提示区域"""
        if not getattr(self, '_cmd_running', False):
            self.progress_label.configure(text="就绪")
            self.progress_frame.configure(fg_color=COLORS["status_ready"])

    def _command_error(self, error):
        """命令执行出错"""
        if self._cancel_command.is_set():
            self._command_done(-1, self.project_path)
            return
        self._cmd_running = False
        self.set_document_editors_enabled(True)
        self.proc = None
        self._terminal_write(f"\n[错误] {error}\n")
        self._terminal_write(f"{'='*60}\n\n")
        self.update_status("命令执行出错")
        self._append_log(f"命令执行出错: {error}", "ERROR")
        self.progress_label.configure(text="出错")
        self.progress_frame.configure(fg_color=COLORS["status_error"])
        if self.project_path:
            self.load_project_content(preserve_editors=True)
            self.load_outline(confirm_switch=False)

        # 3秒后恢复就绪状态
        self.root.after(3000, self._reset_progress)

    def set_document_editors_enabled(self, enabled):
        """任务执行期间锁定正文和大纲编辑器，避免与 CLI 写入冲突。"""
        state = "normal" if enabled else "disabled"
        for widget_name in ("writing_text", "outline_text"):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                widget.configure(state=state)
        if hasattr(self, "chapter_menu"):
            self.chapter_menu.configure(state=state)
        if hasattr(self, "outline_menu"):
            self.outline_menu.configure(state=state)
        if enabled:
            self.update_chapter_nav_state()
        else:
            for widget_name in ("prev_chapter_button", "next_chapter_button"):
                widget = getattr(self, widget_name, None)
                if widget is not None:
                    widget.configure(state="disabled")

    def _update_running_status(self, prefix):
        """更新运行中的状态栏显示（带动态点和耗时）"""
        if not getattr(self, '_cmd_running', False):
            return
        elapsed = time.time() - self._cmd_start_time
        dots = "." * (int(elapsed) % 4)
        elapsed_str = f"{elapsed:.0f}秒" if elapsed < 60 else f"{elapsed/60:.1f}分钟"
        status_text = f"{prefix}{dots} ({elapsed_str})"
        self.update_status(status_text)

        # 更新进度提示区域
        self.progress_label.configure(text=f"⏳ {status_text}")
        self.progress_frame.configure(fg_color=COLORS["status_running"])

        self.root.after(1000, lambda: self._update_running_status(prefix))

    def run_quick_command(self, command):
        """运行快捷命令"""
        if self._prevent_project_edit_during_command():
            return
        self.chat_var.set(command)
        self.send_message()

    def clear_terminal(self):
        """清空终端"""
        self.terminal_text.configure(state="normal")
        self.terminal_text.delete("1.0", "end")
        self.terminal_text.configure(state="disabled")

    def run_codex_diagnostics(self):
        """在终端面板输出 Codex CLI、配置和 skill 释放状态。"""
        if getattr(self, '_diagnostic_running', False):
            self._terminal_write("\n[Codex 诊断] 诊断正在运行，请稍候。\n")
            return

        self._diagnostic_running = True
        self.update_status("Codex 诊断中")
        self._terminal_write("\n[Codex 诊断] 正在检查 CLI、配置和 .agents Skill...\n")

        def _run():
            try:
                report = self.build_codex_diagnostics_report()
            except Exception as e:
                report = f"诊断失败：{e}\n"
            self._post_ui(self._finish_codex_diagnostics, report)

        threading.Thread(target=_run, daemon=True).start()

    def _finish_codex_diagnostics(self, report):
        """回到 UI 线程输出诊断结果。"""
        self._diagnostic_running = False
        self._terminal_write(report)
        self._terminal_write(f"{'='*60}\n\n")
        self.update_status("Codex 诊断完成")

    def build_codex_diagnostics_report(self):
        """生成 Codex 诊断报告，避免输出密钥类敏感字段。"""
        lines = [
            "\n--- Codex 诊断报告 ---",
            f"当前项目: {self.project_path or '未打开项目'}",
            "Codex 配置来源: 本机 Codex CLI 现有配置（~/.codex/config.toml 和登录信息）",
            f"EXE/源码内置 Skill: {'完整' if has_bundled_skill_resources() else '不完整'}",
        ]

        codex_path = resolve_codex_path()
        lines.append(f"PATH 中的 codex: {codex_path or '未找到'}")

        if self.project_path:
            codex_skill = os.path.join(self.project_path, '.agents', 'skills', 'novel-write', 'SKILL.md')
            lines.append(f"项目 Codex Skill: {'存在' if os.path.exists(codex_skill) else '缺失'} ({codex_skill})")

        lines.extend(self.get_codex_config_summary())
        local_info = self.get_codex_local_provider_info()
        local_base_url = local_info.get("base_url", "")
        if local_base_url:
            ok, detail = self.probe_codex_base_url(local_base_url)
            lines.append(f"本机 provider 探测: {'通过' if ok else '失败'} - {detail}")
            lines.append(f"本机 provider 端口进程: {self.find_local_port_owner(local_base_url)}")
        lines.append("")
        lines.append(self.capture_command("where codex", ["where.exe", "codex"], timeout=8))
        lines.append(self.capture_command("codex --version", build_codex_cli_command(["--version"]), timeout=8))
        lines.append("[Codex 诊断] 执行任务时直接调用 codex exec，并读取本机 Codex CLI 的现有配置。")
        lines.append(self.capture_command(
            "codex login status", build_codex_cli_command(["login", "status"]), timeout=8))

        joined = "\n".join(lines)
        if "127.0.0.1" in joined or "503 Service Unavailable" in joined:
            lines.append("")
            lines.append("结论: 当前 Codex 配置/输出指向本地服务或代理。若出现 503，这通常不是 EXE 缺 .agents Skill，而是 Codex Desktop/本地代理没有启动、崩溃、未登录或上游不可用。")
            lines.append("建议: 先打开或重启 Codex Desktop，确认 codex login 成功；如果使用自定义 base_url，请确认 127.0.0.1 对应服务正在运行。")

        return "\n".join(lines) + "\n"

    def get_codex_config_summary(self):
        """读取 Codex 配置摘要，只展示非密钥字段。"""
        codex_home = os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex")
        config_path = os.path.join(codex_home, "config.toml")
        lines = [f"Codex 配置文件: {config_path}"]
        if not os.path.exists(config_path):
            lines.append("Codex 配置摘要: 未找到 config.toml")
            return lines

        safe_keys = (
            "model_provider",
            "model",
            "base_url",
            "wire_api",
            "requires_openai_auth",
            "approval_policy",
            "sandbox_mode",
        )
        try:
            summary = []
            with open(config_path, 'r', encoding='utf-8') as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key = line.split("=", 1)[0].strip()
                    lower = key.lower()
                    if lower in safe_keys:
                        summary.append(line)
            if summary:
                lines.append("Codex 配置摘要:")
                lines.extend(f"  {item}" for item in summary)
            else:
                lines.append("Codex 配置摘要: 未发现可安全展示的关键字段")
        except Exception as e:
            lines.append(f"Codex 配置读取失败: {e}")
        return lines

    def capture_command(self, title, cmd, timeout=10):
        """执行短诊断命令并返回文本。"""
        code, output, timed_out = self.run_command_with_timeout(
            cmd, self.project_path or os.getcwd(), timeout)
        if timed_out:
            return f"[{title}] 超时（超过 {timeout} 秒未返回）"
        return f"[{title}] returncode={code}\n{output.strip()[-3000:] or '(无输出)'}"

    def _get_file_state(self, directory):
        """获取目录下所有文件的状态"""
        state = {}
        if not directory or not os.path.exists(directory):
            return state
        for root, dirs, files in os.walk(directory):
            # 跳过隐藏目录和构建目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('build', 'dist', '__pycache__', 'node_modules')]
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    file_stat = os.stat(filepath)
                    state[filepath] = (file_stat.st_mtime_ns, file_stat.st_size)
                except OSError:
                    pass
        return state

    def _get_file_changes(self, old_state, new_state):
        """比较文件状态，返回变化列表"""
        changes = []
        all_files = set(old_state.keys()) | set(new_state.keys())

        for filepath in sorted(all_files):
            old = old_state.get(filepath)
            new = new_state.get(filepath)

            if old is None:
                # 使用相对路径
                try:
                    rel_path = os.path.relpath(filepath, self.project_path) if self.project_path else filepath
                except:
                    rel_path = filepath
                changes.append(f"[新增] {rel_path}")
            elif new is None:
                try:
                    rel_path = os.path.relpath(filepath, self.project_path) if self.project_path else filepath
                except:
                    rel_path = filepath
                changes.append(f"[删除] {rel_path}")
            elif old != new:
                try:
                    rel_path = os.path.relpath(filepath, self.project_path) if self.project_path else filepath
                except:
                    rel_path = filepath
                changes.append(f"[修改] {rel_path}")

        return changes

    # ==================== 项目管理功能 ====================

    def new_project(self):
        """新建项目"""
        if self._cmd_running:
            messagebox.showinfo("请稍候", "Codex 任务完成后再新建项目。")
            return
        if not self._confirm_document_switch():
            return
        dialog = NewProjectDialog(self.root, self.app_settings.get('project_root', get_default_project_root()))
        self.root.wait_window(dialog.top)

        if dialog.result:
            project_name = dialog.result['name']
            project_type = dialog.result['type']
            project_path = dialog.result['path']
            self.app_settings['project_root'] = project_path
            self.save_app_settings()

            full_path = os.path.abspath(os.path.join(project_path, project_name))
            try:
                self.create_project_structure(full_path, project_name, dialog.result)
            except OSError as e:
                messagebox.showerror("创建项目失败", f"无法创建项目目录或初始文件：\n{e}")
                return
            if not self.prepare_project_skills(full_path):
                messagebox.showerror(
                    "项目创建未完成",
                    "项目目录已经创建，但 Codex Skill 未能释放。请检查应用目录权限后重试。",
                )
                return

            self.project_path = full_path
            self._reset_editors()
            self.project_config = {
                'name': project_name,
                'type': project_type,
                'platform': dialog.result.get('platform', '番茄小说'),
                'pov': dialog.result.get('pov', '第三人称限制'),
                'audience': dialog.result.get('audience', '男频'),
                'hook': dialog.result.get('hook', ''),
                'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'target_words': dialog.result.get('target_words', 2000000),
                'target_chapters': dialog.result.get('target_chapters', 500),
            }
            self.save_project_config()
            self.load_project_content()

            self.project_name_var.set(project_name)
            self.project_type_var.set(f"类型: {project_type} | {dialog.result.get('platform', '')}")
            self.update_status(f"项目 '{project_name}' 创建成功")
            self.chat_var.set(self.format_skill_command(f"新建小说 --name {project_name} --type {project_type}"))

    def open_project(self):
        """打开项目"""
        if self._cmd_running:
            messagebox.showinfo("请稍候", "Codex 任务完成后再打开其他项目。")
            return
        if not self._confirm_document_switch():
            return
        from tkinter import filedialog
        path = filedialog.askdirectory(title="选择项目目录")
        if path:
            config_file = os.path.join(path, 'project.json')
            if not os.path.isfile(config_file):
                messagebox.showwarning("无法打开项目", "所选目录不是网文写作助手项目，缺少 project.json。")
                return
            try:
                project_config = load_project_config(config_file)
            except (OSError, ValueError) as e:
                messagebox.showerror("项目配置损坏", f"无法读取 project.json：\n{e}")
                return

            if not self.prepare_project_skills(path):
                return
            self.project_config = project_config
            self.project_path = path
            self._reset_editors()
            self.project_config.pop('ai_engine', None)
            try:
                self.save_project_config()
            except OSError as e:
                messagebox.showwarning("项目配置只读", f"项目已打开，但无法保存配置：\n{e}")
            if hasattr(self, 'chat_var') and not self.chat_var.get().strip():
                self.chat_var.set(self.get_default_prompt())
            self.project_name_var.set(self.project_config.get('name', '未命名'))
            self.project_type_var.set(f"类型: {self.project_config.get('type', '未知')}")
            self.update_status(f"已打开项目: {self.project_config.get('name')}")
            self.load_project_content()

    def save_project(self):
        """保存项目"""
        if self._cmd_running:
            messagebox.showinfo("请稍候", "Codex 任务完成后再保存项目。")
            return
        if not self._check_project():
            return

        if self._loaded_chapter_num is not None:
            if not self.save_chapter():
                return
        if self._is_outline_dirty() and not self.save_outline():
            return
        try:
            self.save_project_config()
        except OSError as e:
            messagebox.showerror("保存失败", f"无法保存项目配置：\n{e}")
            return
        self.refresh_dashboard()
        self.update_status("项目已保存")

    def save_project_config(self):
        """保存项目配置"""
        if self.project_path:
            self.project_config.pop('ai_engine', None)
            config_file = os.path.join(self.project_path, 'project.json')
            content = json.dumps(self.project_config, ensure_ascii=False, indent=2) + "\n"
            atomic_write_text(config_file, content)

    def prepare_project_skills(self, path):
        """为项目准备 Codex novel-write skill"""
        ensure_skill_files(path)
        missing = get_missing_skill_paths(path)
        if missing:
            message = "项目缺少内置写作 Skill，Codex 可能无法识别 novel-write。\n\n缺失:\n" + "\n".join(missing)
            self.update_status("写作 Skill 释放不完整")
            if hasattr(self, 'log_text'):
                self._append_log(message, "ERROR")
            messagebox.showwarning("Skill 资源缺失", message)
            return False
        return True

    def create_project_structure(self, path, name, config):
        """在相邻临时目录准备完整项目，成功后再交付最终目录。"""
        path = os.path.abspath(path)
        if os.path.exists(path):
            raise FileExistsError(path)
        directories = [
            'worldbuilding',
            'characters',
            'outline/chapter-outs',
            'chapters',
            'style',
            'notes',
            'export',
        ]

        parent = os.path.dirname(path)
        staging = tempfile.mkdtemp(prefix=".novel-project-", dir=parent)
        try:
            for dir_name in directories:
                os.makedirs(os.path.join(staging, dir_name), exist_ok=True)
            self.create_initial_files(staging, name, config)
            initial_config = {key: config[key] for key in (
                "type", "platform", "pov", "audience", "hook", "target_words", "target_chapters"
            ) if key in config}
            initial_config.update(name=name, created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            atomic_write_text(os.path.join(staging, "project.json"),
                              json.dumps(initial_config, ensure_ascii=False, indent=2))
            if not ensure_skill_files(staging):
                raise OSError("无法准备 Codex Skill，请检查安装目录和磁盘权限。")
            os.rename(staging, path)
        finally:
            if os.path.isdir(staging) and os.path.dirname(os.path.abspath(staging)) == parent:
                shutil.rmtree(staging)

    def create_initial_files(self, path, name, config):
        """创建初始文件"""
        project_type = config.get('type', '玄幻/仙侠')
        platform = config.get('platform', '番茄小说')
        pov = config.get('pov', '第三人称限制')
        audience = config.get('audience', '男频')
        hook = config.get('hook', '')
        target_words = config.get('target_words', 2000000)
        target_chapters = config.get('target_chapters', 500)
        created = datetime.now().strftime('%Y-%m-%d')

        # project.md
        project_md = f"""# {name} 项目总览

## 基本信息
- 小说名称：{name}
- 类型/题材：{project_type}
- 目标平台：{platform}
- 叙事视角：{pov}
- 目标读者：{audience}
- 预计总字数：{target_words // 10000}万字
- 预计章节数：{target_chapters}章
- 核心卖点：{hook if hook else '（待填写）'}
- 创建日期：{created}

## 进度追踪
| 章节 | 状态 | 字数 | 完成日期 |
|------|------|------|----------|
| ch001 | 待写 | - | - |
"""
        with open(os.path.join(path, 'project.md'), 'w', encoding='utf-8') as f:
            f.write(project_md)

        # worldbuilding/settings.md
        settings_md = """# 世界观设定

## 基础框架
- 世界名称：
- 时代背景：
- 科技/文明水平：
- 整体氛围/基调：

## 地理与环境
- 主要地域：
- 重要地点：
- 特殊环境：

## 力量体系（如有）
- 体系名称：
- 等级划分：
- 突破条件：
- 特殊规则/限制：

## 社会结构
- 政治体系：
- 主要势力/组织：
- 经济体系：
- 社会阶层：

## 历史与文化
- 重大历史事件：
- 文化习俗：
- 信仰/宗教：

## 特殊设定
- 独特规则：
- 禁忌/禁区：
"""
        with open(os.path.join(path, 'worldbuilding', 'settings.md'), 'w', encoding='utf-8') as f:
            f.write(settings_md)

        # characters/index.md
        index_md = """# 角色索引

| 角色名 | 文件名 | 类型 | 首次出场 | 状态 |
|--------|--------|------|----------|------|
"""
        with open(os.path.join(path, 'characters', 'index.md'), 'w', encoding='utf-8') as f:
            f.write(index_md)

        # style/style-config.md
        style_md = f"""# 文风配置

## 当前风格
- 平台风格：{platform}
- 叙事视角：{pov}
- 时态：过去时
- 目标读者：{audience}

## 文风参数
| 参数 | 设置 | 说明 |
|------|------|------|
| 句式偏好 | 短句为主 | 影响阅读节奏 |
| 描写密度 | 适中 | 环境和心理描写的详细程度 |
| 对话风格 | 口语化 | 角色对话的用词风格 |
| 幽默程度 | 轻度 | 是否加入轻松元素 |
| 虐心程度 | 微虐 | 情感上的虐心程度 |
| 节奏偏好 | 快节奏 | 情节推进速度 |
| 信息密度 | 中 | 每段包含的新信息量 |

## 参考风格
- 模仿作者：
- 样章参考：

## 禁忌项
- 不使用的词汇/表达：
- 避免的情节模式：
"""
        with open(os.path.join(path, 'style', 'style-config.md'), 'w', encoding='utf-8') as f:
            f.write(style_md)

        # notes/misc.md
        notes_md = """# 杂项笔记

## 伏笔追踪
| ID | 伏笔内容 | 埋设章节 | 计划回收 | 实际回收 | 状态 |
|----|----------|----------|----------|----------|------|

## 待办事项

## 灵感记录
"""
        with open(os.path.join(path, 'notes', 'misc.md'), 'w', encoding='utf-8') as f:
            f.write(notes_md)

        canon_md = """# 内容正典

> 只记录正文已经确认的事实。计划中的设定放在大纲，不要直接写入正典。

## 不可变事实

| ID | 事实 | 首次确认 | 最近验证 | 状态 | 备注 |
|----|------|----------|----------|------|------|

## 当前时间线

| 章节 | 故事内时间 | 地点 | 关键变化 |
|------|------------|------|----------|

## 当前资源与伤势

| 对象 | 当前状态 | 最近变化章节 | 约束 |
|------|----------|--------------|------|

## 活跃冲突

| 冲突 | 主动方 | 目标 | 当前压力 | 下一次升级 |
|------|--------|------|----------|------------|

## 待核对事项

- [ ]
"""
        with open(os.path.join(path, 'notes', 'canon.md'), 'w', encoding='utf-8') as f:
            f.write(canon_md)

    def load_project_content(self, preserve_editors=False):
        """加载项目内容"""
        if not self._check_project():
            return

        if not preserve_editors:
            self.load_outline()
        self.refresh_stats()
        self._load_chapter_list(
            preserve_current=preserve_editors,
            reload_current=not preserve_editors,
        )

    @staticmethod
    def count_cjk_characters(content):
        return sum(
            1 for char in document_body(content)
            if ('\u3400' <= char <= '\u4dbf'
                or '\u4e00' <= char <= '\u9fff'
                or '\uf900' <= char <= '\ufaff'
                or '\U00020000' <= char <= '\U0002fa1f')
        )

    def scan_chapters(self):
        """扫描章节目录并缓存字数；仅在文件元数据变化后重新读取正文。"""
        if not self.project_path:
            return []
        chapters_dir = os.path.join(self.project_path, 'chapters')
        if not os.path.isdir(chapters_dir):
            return []

        entries = []
        try:
            with os.scandir(chapters_dir) as iterator:
                for entry in iterator:
                    match = re.fullmatch(r"ch(\d+)\.md", entry.name, flags=re.IGNORECASE)
                    if not match or not entry.is_file():
                        continue
                    try:
                        stat = entry.stat()
                    except OSError:
                        continue
                    entries.append({
                        "number": int(match.group(1)),
                        "name": entry.name,
                        "path": entry.path,
                        "signature": (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size),
                    })
        except OSError:
            return []

        entries.sort(key=lambda item: (item["number"], len(item["name"]), item["name"].lower()))
        unique_entries = {}
        for item in entries:
            number = item["number"]
            current = unique_entries.get(number)
            canonical_name = f'ch{number:03d}.md'
            if current is None or item["name"].lower() == canonical_name.lower():
                unique_entries[number] = item
        entries = [unique_entries[number] for number in sorted(unique_entries)]
        signature = tuple((item["name"].lower(), *item["signature"]) for item in entries)
        cache_key = os.path.normcase(os.path.abspath(chapters_dir))
        cached = self._chapter_scan_cache.get(cache_key)
        if cached and cached[0] == signature:
            return cached[1]

        cached_counts = cached[2] if cached else {}
        new_counts = {}
        for item in entries:
            count_key = (item["name"].lower(), *item["signature"])
            word_count = cached_counts.get(count_key)
            if word_count is None:
                try:
                    with open(item["path"], 'r', encoding='utf-8', errors='replace') as chapter_file:
                        word_count = self.count_cjk_characters(chapter_file.read())
                except OSError:
                    word_count = 0
            new_counts[count_key] = word_count
            item["words"] = word_count

        self._chapter_scan_cache[cache_key] = (signature, entries, new_counts)
        return entries

    def get_chapter_path(self, chapter_num):
        """查找已有章节文件；新文件统一使用三位数编号。"""
        if not self.project_path:
            return None
        chapter_num = int(chapter_num)
        chapters_dir = os.path.join(self.project_path, 'chapters')
        canonical = os.path.join(chapters_dir, f'ch{chapter_num:03d}.md')
        if os.path.isfile(canonical):
            return canonical
        try:
            with os.scandir(chapters_dir) as iterator:
                matches = []
                for entry in iterator:
                    match = re.fullmatch(r"ch(\d+)\.md", entry.name, flags=re.IGNORECASE)
                    if match and int(match.group(1)) == chapter_num and entry.is_file():
                        matches.append(entry.path)
                if matches:
                    matches.sort(key=lambda path: (len(os.path.basename(path)), os.path.basename(path).lower()))
                    return matches[0]
        except OSError:
            pass
        return canonical

    def _current_chapter_number(self):
        match = re.fullmatch(r"第(\d+)章", self.chapter_var.get().strip())
        return int(match.group(1)) if match else None

    def _is_current_chapter_dirty(self):
        if self._loaded_chapter_num is None or not hasattr(self, 'writing_text'):
            return False
        return self.writing_text.get("1.0", "end-1c") != self._loaded_chapter_content

    def _save_current_chapter_if_dirty(self):
        if not self._is_current_chapter_dirty():
            return True
        if self._current_chapter_number() is None:
            messagebox.showwarning("无法保存", "当前没有选中的章节，先选择或创建章节再继续。")
            return False
        return self.save_chapter()

    def _confirm_chapter_switch(self):
        if not self._is_current_chapter_dirty():
            return True
        answer = messagebox.askyesnocancel("章节尚未保存", "当前章节有未保存的修改，要先保存吗？")
        if answer is None:
            return False
        if answer:
            return bool(self.save_chapter())
        return True

    def _is_outline_dirty(self):
        return (self._loaded_outline_path is not None
                and self.outline_text.get("1.0", "end-1c") != self._loaded_outline_content)

    def _confirm_outline_switch(self):
        if not self._is_outline_dirty():
            return True
        answer = messagebox.askyesnocancel("大纲尚未保存", "当前大纲有未保存的修改，要先保存吗？")
        return answer is not None and (not answer or bool(self.save_outline()))

    def _confirm_document_switch(self):
        return self._confirm_chapter_switch() and self._confirm_outline_switch()

    def _reset_editors(self):
        self._loaded_chapter_num = None
        self._loaded_chapter_path = None
        self._loaded_chapter_content = ""
        self._loaded_outline_path = None
        self._loaded_outline_content = ""
        self._loaded_outline_choice = "总大纲"
        self.outline_var.set("总大纲")
        self._chapter_scan_cache.clear()

    def _check_external_change(self, path, original):
        try:
            disk = read_text(path) if os.path.exists(path) else None
        except (OSError, UnicodeError) as e:
            messagebox.showerror("无法核对文件", str(e))
            return False
        if disk != original:
            return messagebox.askyesno(
                "文件已被外部修改", "磁盘中的文件已经改变。确定用编辑器中的内容覆盖吗？")
        return True

    def _load_chapter_list(self, preserve_current=False, reload_current=True):
        """扫描 chapters 目录，动态更新章节选择器"""
        chapters = self.get_chapter_choices()
        if chapters:
            self.chapter_menu.configure(values=chapters)
            current = self.chapter_var.get() if preserve_current else ""
            choice = current if current in chapters else chapters[0]
            self.chapter_var.set(choice)
            if reload_current:
                self._on_chapter_selected(choice, confirm_switch=False, force=True)
            else:
                self.update_chapter_nav_state()
        else:
            self.chapter_menu.configure(values=["暂无章节"])
            self.chapter_var.set("暂无章节")
            if reload_current:
                self.writing_text.delete("1.0", "end")
                self._loaded_chapter_num = None
                self._loaded_chapter_content = ""
                self._loaded_chapter_path = None
                self.update_word_count()
            self.update_chapter_nav_state()

    def get_chapter_choices(self):
        """返回按章节号排序的章节显示名。"""
        by_number = {}
        for item in self.scan_chapters():
            number = item["number"]
            current = by_number.get(number)
            canonical_name = f'ch{number:03d}.md'
            if current is None or item["name"].lower() == canonical_name.lower():
                by_number[number] = item
        return [f"第{number}章" for number in sorted(by_number)]

    def get_current_chapter_index(self, chapters=None):
        """获取当前章节在章节列表中的位置。"""
        chapters = chapters or self.get_chapter_choices()
        current = self.chapter_var.get() if hasattr(self, 'chapter_var') else ""
        try:
            return chapters.index(current)
        except ValueError:
            return -1

    def update_chapter_nav_state(self):
        """刷新章节导航按钮状态。"""
        if not hasattr(self, 'prev_chapter_button') or not hasattr(self, 'next_chapter_button'):
            return
        chapters = self.get_chapter_choices()
        current_index = self.get_current_chapter_index(chapters)
        has_prev = current_index > 0
        has_next = current_index >= 0 and current_index < len(chapters) - 1
        self.prev_chapter_button.configure(state="normal" if has_prev else "disabled")
        self.next_chapter_button.configure(state="normal" if has_next else "disabled")

    def previous_chapter(self):
        """切换到上一章。"""
        if self._cmd_running:
            return
        if not self._check_project():
            return
        chapters = self.get_chapter_choices()
        current_index = self.get_current_chapter_index(chapters)
        if current_index < 0:
            self.update_status("当前章节不在章节列表中")
            self.update_chapter_nav_state()
            return
        if current_index == 0:
            self.update_status("已经是第一章")
            self.update_chapter_nav_state()
            return

        prev_choice = chapters[current_index - 1]
        self.chapter_var.set(prev_choice)
        if self._on_chapter_selected(prev_choice):
            self.update_status(f"已切换到 {prev_choice}")

    def next_chapter(self):
        """切换到下一章。"""
        if self._cmd_running:
            return
        if not self._check_project():
            return
        chapters = self.get_chapter_choices()
        current_index = self.get_current_chapter_index(chapters)
        if current_index < 0:
            self.update_status("当前章节不在章节列表中")
            self.update_chapter_nav_state()
            return
        if current_index >= len(chapters) - 1:
            self.update_status("已经是最后一章")
            self.update_chapter_nav_state()
            return

        next_choice = chapters[current_index + 1]
        self.chapter_var.set(next_choice)
        if self._on_chapter_selected(next_choice):
            self.update_status(f"已切换到 {next_choice}")

    def _on_chapter_selected(self, choice, confirm_switch=True, force=False):
        """切换章节时自动加载内容"""
        if self._cmd_running:
            return False
        if not self.project_path or choice == "暂无章节":
            self.update_chapter_nav_state()
            return True
        target_path = self.get_chapter_path(self._current_chapter_number()) if self._current_chapter_number() is not None else None
        if (not force and self._current_chapter_number() == self._loaded_chapter_num
                and target_path == self._loaded_chapter_path):
            self.update_chapter_nav_state()
            return True
        if confirm_switch and not self._confirm_chapter_switch():
            if self._loaded_chapter_num is not None:
                self.chapter_var.set(f"第{self._loaded_chapter_num}章")
            return False
        number = self._current_chapter_number()
        if number is None:
            self.update_chapter_nav_state()
            return False
        path = self.get_chapter_path(number)
        try:
            content = read_text(path)
        except (OSError, UnicodeError) as e:
            if self._loaded_chapter_num is not None:
                self.chapter_var.set(f"第{self._loaded_chapter_num}章")
            messagebox.showerror("读取章节失败", str(e))
            return False
        self.writing_text.delete("1.0", "end")
        self.writing_text.insert("1.0", content)
        self._loaded_chapter_num = number
        self._loaded_chapter_content = content
        self._loaded_chapter_path = path
        self.update_word_count()
        self.update_chapter_nav_state()
        return True

    def load_outline(self, confirm_switch=True):
        """加载大纲"""
        if not self.project_path or self._cmd_running:
            return
        if confirm_switch and not self._confirm_outline_switch():
            return
        outline_dir = os.path.join(self.project_path, 'outline')
        outlines = ["总大纲"]
        try:
            filenames = os.listdir(outline_dir) if os.path.isdir(outline_dir) else []
        except OSError as e:
            messagebox.showerror("读取大纲失败", str(e))
            return
        volumes = set()
        for filename in filenames:
            match = re.fullmatch(r"(?:vol|volume-)(\d+)-outline\.md", filename)
            if match:
                volumes.add(int(match.group(1)))
        outlines.extend(f"第{number}卷" for number in sorted(volumes))
        self.outline_menu.configure(values=outlines)
        choice = self.outline_var.get()
        self._on_outline_selected(choice if choice in outlines else "总大纲", confirm_switch=False)

    def _on_outline_selected(self, choice, confirm_switch=True):
        """切换大纲时自动加载内容"""
        if not self.project_path or self._cmd_running:
            return False
        if confirm_switch and not self._confirm_outline_switch():
            self.outline_var.set(self._loaded_outline_choice)
            return False
        outline_dir = os.path.join(self.project_path, 'outline')
        if choice == "总大纲":
            outline_file = os.path.join(outline_dir, 'master-outline.md')
        else:
            match = re.fullmatch(r"第(\d+)卷", choice)
            if not match:
                return False
            volume_num = match.group(1)
            outline_file = os.path.join(outline_dir, f'vol{volume_num}-outline.md')
            if not os.path.exists(outline_file) and os.path.exists(
                    os.path.join(outline_dir, f'volume-{volume_num}-outline.md')):
                outline_file = os.path.join(outline_dir, f'volume-{volume_num}-outline.md')
        try:
            disk_content = read_text(outline_file) if os.path.exists(outline_file) else None
        except (OSError, UnicodeError) as e:
            self.outline_var.set(self._loaded_outline_choice)
            messagebox.showerror("读取大纲失败", str(e))
            return False
        content = disk_content or ""
        self.outline_text.delete("1.0", "end")
        self.outline_text.insert("1.0", content)
        self._loaded_outline_path = outline_file
        self._loaded_outline_content = content
        self._loaded_outline_disk_content = disk_content
        self._loaded_outline_choice = choice
        self.outline_var.set(choice)
        return True

    # ==================== 项目检查 ====================

    def _check_project(self):
        """检查是否已打开项目，未打开时弹窗提示"""
        if not self.project_path:
            messagebox.showwarning("提示", "请先打开或新建项目")
            return False
        return True

    def _prevent_project_edit_during_command(self):
        if not self._cmd_running:
            return False
        messagebox.showinfo("请稍候", "Codex 正在处理当前项目，任务完成后再执行其他操作。")
        return True

    # ==================== 大纲功能 ====================

    def generate_outline(self):
        """生成总大纲"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        self.chat_var.set(self.format_skill_command("生成总大纲"))
        self.send_message()
        self.tabview.set(TAB_STUDIO)

    def generate_volume_outline(self):
        """生成卷大纲"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        dialog = CTkInputDialog(text="请输入卷数:", title="生成卷大纲")
        volume = dialog.get_input()
        if volume and volume.isdigit():
            self.chat_var.set(self.format_skill_command(f"生成第{volume}卷大纲"))
            self.send_message()
            self.tabview.set(TAB_STUDIO)

    def save_outline(self):
        """保存大纲"""
        if self._prevent_project_edit_during_command():
            return False
        if not self._check_project():
            return False
        outline_file = self._loaded_outline_path
        if not outline_file:
            return False
        if not self._check_external_change(outline_file, self._loaded_outline_disk_content):
            return False
        content = self.outline_text.get("1.0", "end-1c")
        try:
            atomic_write_text(outline_file, content)
        except OSError as e:
            messagebox.showerror("保存失败", f"无法保存大纲：\n{e}")
            return False
        self._loaded_outline_content = content
        self._loaded_outline_disk_content = content
        self.update_status("大纲已保存")
        return True

    # ==================== 章节功能 ====================

    def write_chapter(self):
        """写章节"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        dialog = CTkInputDialog(text="请输入章节号:", title="写章节")
        chapter = dialog.get_input()
        if chapter and chapter.isdigit():
            self.chat_var.set(self.format_skill_command(f"写第{chapter}章"))
            self.send_message()
            self.tabview.set(TAB_STUDIO)

    def continue_writing(self):
        """续写"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        self.chat_var.set(self.format_skill_command("继续写"))
        self.send_message()
        self.tabview.set(TAB_STUDIO)

    def plan_chapter(self):
        """规划章节"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        dialog = CTkInputDialog(text="请输入章节号:", title="规划章节")
        chapter = dialog.get_input()
        if chapter and chapter.isdigit():
            self.chat_var.set(self.format_skill_command(f"规划第{chapter}章"))
            self.send_message()
            self.tabview.set(TAB_STUDIO)

    def save_chapter(self):
        """保存章节"""
        if self._prevent_project_edit_during_command():
            return False
        if not self._check_project():
            return False
        chapter_num = self._loaded_chapter_num
        if chapter_num is None:
            messagebox.showinfo("暂无章节", "请先选择或生成章节，再保存正文。")
            return False
        chapter_name = f"第{chapter_num}章"
        chapter_file = self.get_chapter_path(chapter_num)
        if not self._check_external_change(chapter_file, self._loaded_chapter_content):
            return False
        content = self.writing_text.get("1.0", "end-1c")
        try:
            atomic_write_text(chapter_file, content)
        except OSError as e:
            messagebox.showerror("保存失败", f"无法保存章节：\n{e}")
            return False
        self._loaded_chapter_content = content
        self._loaded_chapter_path = chapter_file
        self.refresh_dashboard()
        self.update_status(f"章节 {chapter_name} 已保存")
        return True

    # ==================== 人物功能 ====================

    def view_characters(self):
        """查看人物管理"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        dialog = CharacterManagerDialog(self.root, self.project_path)
        self.root.wait_window(dialog.top)
        self.refresh_dashboard()

    # ==================== 世界观功能 ====================

    def get_default_worldbuilding_template(self):
        """默认世界观模板"""
        return """# 世界观设定

## 基础设定
- 世界名称：
- 时代背景：
- 地理环境：
- 社会结构：

## 力量体系
- 能力来源：
- 等级划分：
- 修炼/成长方式：
- 限制与代价：

## 阵营与势力
| 势力 | 立场 | 资源 | 主要人物 |
|------|------|------|----------|

## 时间线
- 故事开始前：
- 第一卷关键节点：

## 禁忌与规则
- 不能违反的世界规则：
- 容易造成漏洞的设定：
"""

    def edit_worldbuilding(self):
        """编辑世界观"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        settings_file = os.path.join(self.project_path, 'worldbuilding', 'settings.md')
        if edit_document(self.root, settings_file, "世界观设定", self.get_default_worldbuilding_template()):
            self.update_status("世界观设定已更新")
            self.refresh_dashboard()

    # ==================== 风格配置 ====================

    def get_default_style_template(self):
        """默认文风模板"""
        project_type = self.project_config.get('type', '未分类')
        platform = self.project_config.get('platform', '未指定平台')
        return f"""# 文风配置

## 基础风格
- 小说类型：{project_type}
- 目标平台：{platform}
- 叙事视角：
- 语言气质：
- 节奏关键词：

## 文风参数
| 参数 | 当前设定 | 说明 |
|------|----------|------|
| 叙事节奏 | 快节奏 | 每章保持明确冲突和推进 |
| 情绪密度 | 中高 | 保持期待感、危机感或爽点 |
| 对话风格 | 口语化 | 角色对话贴合身份和关系 |
| 描写比例 | 适中 | 避免大段静态说明 |

## 参考风格
- 模仿作者：
- 样章参考：

## 禁忌项
- 不使用的词汇/表达：
- 避免的情节模式：
"""

    def style_settings(self):
        """风格配置"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        style_file = os.path.join(self.project_path, 'style', 'style-config.md')
        if edit_document(self.root, style_file, "风格配置", self.get_default_style_template()):
            self.update_status("风格配置已更新")
            self.refresh_dashboard()

    def edit_notes(self):
        """编辑伏笔和杂项笔记"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        notes_file = os.path.join(self.project_path, 'notes', 'misc.md')
        default = "# 杂项笔记\n\n## 伏笔追踪\n| ID | 伏笔内容 | 埋设章节 | 计划回收 | 实际回收 | 状态 |\n|----|----------|----------|----------|----------|------|\n\n## 待办事项\n\n## 灵感记录\n"
        if edit_document(self.root, notes_file, "伏笔笔记", default):
            self.update_status("伏笔笔记已更新")
            self.refresh_dashboard()

    # ==================== 统计功能 ====================

    def word_count(self):
        """字数统计"""
        if not self._check_project():
            return 0
        return sum(item["words"] for item in self.scan_chapters())

    def count_words(self):
        """统计当前章节字数"""
        content = self.writing_text.get("1.0", "end")
        chinese_chars = self.count_cjk_characters(content)
        self.word_count_var.set(f"字数: {chinese_chars}")

    def update_word_count(self, _=None):
        """更新字数统计"""
        self.count_words()
        self.update_status_words()

    def refresh_stats(self):
        """刷新统计信息"""
        if self._cmd_running:
            return
        if not self._check_project():
            return

        self.stats_text.delete("1.0", "end")

        chapters = self.scan_chapters()
        chapters_count = len({item["number"] for item in chapters})
        total_words = sum(item["words"] for item in chapters)
        chapter_list = [f'ch{number:03d}' for number in sorted({item["number"] for item in chapters})]
        target_words = max(int(self.project_config.get('target_words', 0) or 0), 1)

        stats = f"""# 写作统计报告

## 项目信息
- 项目名称：{self.project_config.get('name', '未命名')}
- 项目类型：{self.project_config.get('type', '未知')}
- 创建时间：{self.project_config.get('created', '未知')}

## 字数统计
- 总字数：{total_words} 字
- 章节数：{chapters_count} 章
- 平均每章：{total_words // chapters_count if chapters_count else 0} 字

## 进度追踪
- 已完成章节：{chapters_count} 章
- 目标字数：{self.project_config.get('target_words', 0)} 字
- 完成进度：{total_words / target_words * 100:.1f}%

## 章节列表
{chr(10).join(f'- {name}' for name in chapter_list) if chapter_list else '暂无章节'}

## 最近更新
- 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.stats_text.insert("1.0", stats)
        self.refresh_dashboard()

    def export_stats(self):
        """导出统计报告"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title="导出统计报告",
            defaultextension=".md",
            filetypes=[("Markdown文件", "*.md"), ("所有文件", "*.*")]
        )
        if file_path:
            content = self.stats_text.get("1.0", "end")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.update_status(f"统计报告已导出")

    def word_stats(self):
        """字数统计"""
        if self._prevent_project_edit_during_command():
            return
        self.refresh_stats()
        self.tabview.set(TAB_STATS)

    # ==================== 导出功能 ====================

    def export_novel(self):
        """导出合并所有章节为可发布文件"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        if not self._save_current_chapter_if_dirty():
            return

        chapters_dir = os.path.join(self.project_path, 'chapters')
        if not os.path.exists(chapters_dir):
            messagebox.showwarning("提示", "没有找到章节目录")
            return

        chapters = self.scan_chapters()
        if not chapters:
            messagebox.showwarning("提示", "没有找到章节文件")
            return

        export_dir = os.path.join(self.project_path, 'export')
        os.makedirs(export_dir, exist_ok=True)

        project_name = self.project_config.get('name', '未命名')
        export_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', project_name).strip(' .') or '未命名'
        export_file = os.path.join(export_dir, f'{export_name}_全文.md')

        total_chars = 0
        parts = [f"# {project_name}\n\n"]
        try:
            for chapter in chapters:
                content = document_body(read_text(chapter["path"]))
                if content:
                    parts.append(content + "\n\n---\n\n")
                    chinese_chars = self.count_cjk_characters(content)
                    total_chars += chinese_chars
            atomic_write_text(export_file, "".join(parts))
        except (OSError, UnicodeError) as e:
            messagebox.showerror("导出失败", f"原导出文件保持完整：\n{e}")
            return

        self._terminal_write(f"\n[导出完成] {export_file}\n")
        chapter_count = len({chapter["number"] for chapter in chapters})
        self._terminal_write(f"[共 {chapter_count} 章，{total_chars} 字]\n")
        self.update_status(f"导出完成：{chapter_count} 章，{total_chars} 字")
        messagebox.showinfo("导出成功",
                            f"已导出 {chapter_count} 章，共 {total_chars} 字\n\n"
                            f"文件位置：{export_file}")

    # ==================== 辅助功能 ====================

    def review_chapter(self):
        """审稿"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        if self._loaded_chapter_num is None:
            messagebox.showinfo("暂无章节", "请先选择章节。")
            return
        self.chat_var.set(self.format_skill_command(f"审稿第{self._loaded_chapter_num}章"))
        self.send_message()
        self.tabview.set(TAB_STUDIO)

    def polish_chapter(self):
        """润色"""
        if self._prevent_project_edit_during_command():
            return
        if not self._check_project():
            return
        if self._loaded_chapter_num is None:
            messagebox.showinfo("暂无章节", "请先选择章节。")
            return
        self.chat_var.set(self.format_skill_command(f"润色第{self._loaded_chapter_num}章"))
        self.send_message()
        self.tabview.set(TAB_STUDIO)

    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
        self.root.update_idletasks()

    def on_closing(self):
        """窗口关闭时终止子进程（含子进程树）"""
        if not self._cmd_running and not self._confirm_document_switch():
            return
        if self._cmd_running and not messagebox.askyesno("任务仍在运行", "关闭窗口并停止当前 Codex 任务吗？"):
            return
        self._cancel_command.set()
        self._closing = True
        if self.proc and self.proc.poll() is None:
            try:
                # 杀掉整个 Codex CLI 进程树。
                self.kill_process_tree(self.proc.pid)
            except:
                pass
        self.root.destroy()

    def run(self):
        """运行应用"""
        self.root.mainloop()


class CTkInputDialog:
    """现代风格输入对话框"""

    def __init__(self, parent=None, text="输入:", title="输入"):
        self.top = CTkToplevel(parent)
        self.top.title(title)
        self.top.geometry("350x180")
        self.top.transient(parent)
        self.top.grab_set()

        self.result = None

        CTkLabel(self.top, text=text, font=FONT_BODY, text_color=COLORS["text_primary"]).pack(pady=(20, 10))

        self.entry = CTkEntry(self.top, width=280, height=BTN_HEIGHT_LG, corner_radius=CORNER_RADIUS_LG,
                               fg_color=COLORS["bg_input"], border_width=1, border_color=COLORS["border"])
        self.entry.pack(pady=10)
        self.entry.focus_set()

        button_frame = CTkFrame(self.top, fg_color="transparent")
        button_frame.pack(pady=10)

        CTkButton(button_frame, text="确定", command=self.ok,
                  width=100, **btn_primary()).pack(side="left", padx=10)
        CTkButton(button_frame, text="取消", command=self.cancel,
                  width=100, **btn_ghost(height=BTN_HEIGHT_MD)).pack(side="left", padx=10)

        self.entry.bind("<Return>", lambda _: self.ok())

    def ok(self):
        self.result = self.entry.get()
        self.top.destroy()

    def cancel(self):
        self.top.destroy()

    def get_input(self):
        self.top.wait_window()
        return self.result


class NewProjectDialog:
    """新建项目对话框"""

    def __init__(self, parent, default_project_root=None):
        self.top = CTkToplevel(parent)
        self.top.title("新建项目")
        self.top.geometry("520x720")
        self.top.transient(parent)
        self.top.grab_set()

        self.result = None
        self.default_project_root = default_project_root or get_default_project_root()

        # 可滚动容器
        scroll = CTkScrollableFrame(self.top, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        CTkLabel(scroll, text="新建小说项目",
                 font=("Microsoft YaHei UI", 20, "bold"), text_color=COLORS["text_primary"]).pack(pady=(10, 15))

        # 项目名称
        CTkLabel(scroll, text="项目名称:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.name_var = ctk.StringVar()
        CTkEntry(scroll, textvariable=self.name_var, width=400, height=BTN_HEIGHT_MD,
                 corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_input"],
                 border_width=1, border_color=COLORS["border"]).pack(padx=20, pady=(0, 8))

        # 保存目录
        CTkLabel(scroll, text="保存目录:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        path_frame = CTkFrame(scroll, fg_color="transparent")
        path_frame.pack(fill="x", padx=20, pady=(0, 8))
        self.path_var = ctk.StringVar(value=self.default_project_root)
        CTkEntry(path_frame, textvariable=self.path_var, width=300, height=BTN_HEIGHT_MD,
                 corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_input"],
                 border_width=1, border_color=COLORS["border"]).pack(side="left", fill="x", expand=True, padx=(0, 8))
        CTkButton(path_frame, text="选择...", command=self.choose_path,
                  width=86, **btn_outline()).pack(side="right")

        # 项目类型
        CTkLabel(scroll, text="项目类型:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.type_var = ctk.StringVar(value="玄幻/仙侠")
        CTkOptionMenu(scroll, values=["玄幻/仙侠", "都市/现实", "科幻/未来", "历史/架空", "悬疑/推理", "言情/耽美"],
                      variable=self.type_var, width=400, height=BTN_HEIGHT_MD,
                      **menu_style()).pack(padx=20, pady=(0, 8))

        # 目标平台
        CTkLabel(scroll, text="目标平台:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.platform_var = ctk.StringVar(value="番茄小说")
        CTkOptionMenu(scroll, values=["番茄小说", "起点中文网", "晋江文学城", "纵横中文网", "飞卢小说", "其他"],
                      variable=self.platform_var, width=400, height=BTN_HEIGHT_MD,
                      **menu_style()).pack(padx=20, pady=(0, 8))

        # 叙事视角
        CTkLabel(scroll, text="叙事视角:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.pov_var = ctk.StringVar(value="第三人称限制")
        CTkOptionMenu(scroll, values=["第三人称限制", "第三人称全知", "第一人称", "多视角切换"],
                      variable=self.pov_var, width=400, height=BTN_HEIGHT_MD,
                      **menu_style()).pack(padx=20, pady=(0, 8))

        # 目标字数
        CTkLabel(scroll, text="目标字数（万字）:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.words_var = ctk.StringVar(value="200")
        CTkEntry(scroll, textvariable=self.words_var, width=400, height=BTN_HEIGHT_MD,
                 corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_input"],
                 border_width=1, border_color=COLORS["border"]).pack(padx=20, pady=(0, 8))

        # 预计章节数
        CTkLabel(scroll, text="预计章节数:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.chapters_var = ctk.StringVar(value="500")
        CTkEntry(scroll, textvariable=self.chapters_var, width=400, height=BTN_HEIGHT_MD,
                 corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_input"],
                 border_width=1, border_color=COLORS["border"]).pack(padx=20, pady=(0, 8))

        # 目标读者
        CTkLabel(scroll, text="目标读者:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.audience_var = ctk.StringVar(value="男频")
        CTkOptionMenu(scroll, values=["男频", "女频", "全年龄"],
                      variable=self.audience_var, width=400, height=BTN_HEIGHT_MD,
                      **menu_style()).pack(padx=20, pady=(0, 8))

        # 核心卖点
        CTkLabel(scroll, text="核心卖点（一句话简介）:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.hook_var = ctk.StringVar()
        CTkEntry(scroll, textvariable=self.hook_var, width=400, height=BTN_HEIGHT_MD,
                 corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_input"],
                 border_width=1, border_color=COLORS["border"]).pack(padx=20, pady=(0, 8))

        # 按钮
        button_frame = CTkFrame(self.top, fg_color="transparent")
        button_frame.pack(pady=15)

        CTkButton(button_frame, text="创建项目", command=self.ok,
                  width=130, **btn_primary()).pack(side="left", padx=10)
        CTkButton(button_frame, text="取消", command=self.cancel,
                  width=100, **btn_ghost(height=BTN_HEIGHT_LG)).pack(side="left", padx=10)

    def ok(self):
        name = self.name_var.get().strip()
        error = validate_project_name(name)
        if error:
            messagebox.showwarning("项目名称无效", error, parent=self.top)
            return

        project_root = self.path_var.get().strip() or self.default_project_root
        if not os.path.isdir(project_root):
            messagebox.showwarning("保存目录无效", "请选择一个已存在的保存目录。", parent=self.top)
            return
        if os.path.exists(os.path.join(project_root, name)):
            messagebox.showwarning(
                "项目已存在",
                "该目录已经存在。为避免覆盖现有小说，请更换项目名称或选择其他保存目录。",
                parent=self.top,
            )
            return

        try:
            target_words = int(self.words_var.get()) * 10000
            target_chapters = int(self.chapters_var.get())
            if target_words <= 0 or target_chapters <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("目标无效", "目标字数和章节数必须是大于零的整数。", parent=self.top)
            return

        self.result = {
            'name': name,
            'type': self.type_var.get(),
            'platform': self.platform_var.get(),
            'pov': self.pov_var.get(),
            'target_words': target_words,
            'target_chapters': target_chapters,
            'audience': self.audience_var.get(),
            'hook': self.hook_var.get(),
            'path': project_root,
        }
        self.top.destroy()

    def choose_path(self):
        path = filedialog.askdirectory(title="选择小说项目保存目录", initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)

    def cancel(self):
        self.top.destroy()


class CharacterManagerDialog:
    """人物管理对话框"""

    def __init__(self, parent, project_path):
        self.top = CTkToplevel(parent)
        self.top.title("人物管理")
        self.top.geometry("700x500")
        self.top.transient(parent)
        self.top.grab_set()

        self.project_path = project_path

        # 工具栏
        toolbar = CTkFrame(self.top, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=(15, 10))

        CTkButton(toolbar, text="➕ 新建角色", command=self.new_character,
                  width=110, **btn_primary()).pack(side="left", padx=5)
        CTkButton(toolbar, text="✏️ 编辑角色", command=self.edit_character,
                  width=110, **btn_outline()).pack(side="left", padx=5)
        CTkButton(toolbar, text="删除角色", command=self.delete_character,
                  width=110, **btn_danger()).pack(side="left", padx=5)

        # 角色列表
        self.character_list = CTkTextbox(self.top, font=FONT_BODY, corner_radius=CORNER_RADIUS_LG,
                                          fg_color=COLORS["bg_input"], border_width=1, border_color=COLORS["border"])
        self.character_list.pack(fill="both", expand=True, padx=15, pady=10)

        # 加载角色列表
        self.load_characters()

    def load_characters(self):
        """加载角色列表"""
        self.character_list.delete("1.0", "end")

        characters_dir = os.path.join(self.project_path, 'characters')
        if os.path.exists(characters_dir):
            files = sorted(
                f for f in os.listdir(characters_dir)
                if f.endswith('.md') and f != 'index.md'
            )

            if files:
                self.character_list.insert("end", "角色列表:\n\n")
                for i, file_name in enumerate(files, 1):
                    char_name = file_name.replace('.md', '')
                    self.character_list.insert("end", f"{i}. {char_name}\n")
            else:
                self.character_list.insert("end", "暂无角色，点击'新建角色'创建。")

    def _character_file(self, name, show_error=True):
        """把角色名安全地解析为 characters 目录内的 Markdown 文件。"""
        name = (name or "").strip()
        error = validate_child_filename(name, "角色名")
        if name.casefold() == "index":
            error = "index 是角色索引文件，请使用其他角色名。"
        project_root = os.path.realpath(self.project_path)
        characters_dir = os.path.realpath(os.path.join(self.project_path, 'characters'))
        candidate = os.path.realpath(os.path.join(characters_dir, f"{name}.md"))
        try:
            inside_project = os.path.commonpath([project_root, characters_dir]) == project_root
            inside_directory = os.path.commonpath([characters_dir, candidate]) == characters_dir
        except ValueError:
            inside_project = False
            inside_directory = False
        if error or not inside_project or not inside_directory:
            if show_error:
                messagebox.showwarning(
                    "角色名无效",
                    error or "角色文件必须位于当前项目的 characters 目录内。",
                    parent=self.top,
                )
            return None
        return candidate

    def new_character(self):
        """新建角色"""
        dialog = CTkInputDialog(parent=self.top, text="请输入角色名称:", title="新建角色")
        name = dialog.get_input()
        if name:
            name = name.strip()
            char_file = self._character_file(name)
            if not char_file:
                return
            if os.path.exists(char_file):
                messagebox.showwarning("角色已存在", "同名角色已经存在，请使用编辑功能。", parent=self.top)
                return
            char_md = f"""# {name} 设定卡

## 基本信息
- 姓名：{name}
- 别名/称号：
- 年龄：
- 性别：
- 外貌特征：

## 性格画像
- 核心性格：
- 说话特点：
- 行为习惯：

## 背景故事
- 出身：
- 经历：
- 当前状态：

## 能力体系
- 战斗能力：
- 特殊能力/技能：
- 弱点/短板：

## 人物关系
| 角色名 | 关系 | 当前状态 | 发展方向 |
|--------|------|----------|----------|

## 角色弧线
- 起点状态：
- 转折事件：
- 终点状态：
"""
            try:
                atomic_write_text(char_file, char_md)
            except OSError as e:
                messagebox.showerror("创建角色失败", str(e), parent=self.top)
                return

            self.load_characters()

    def edit_character(self):
        """编辑角色"""
        dialog = CTkInputDialog(parent=self.top, text="请输入要编辑的角色名称:", title="编辑角色")
        name = dialog.get_input()
        if name:
            name = name.strip()
            char_file = self._character_file(name)
            if not char_file:
                return
            if os.path.exists(char_file):
                if edit_document(self.top, char_file, f"编辑角色: {name}"):
                    self.load_characters()
            else:
                messagebox.showinfo("未找到角色", f"没有找到角色：{name}", parent=self.top)

    def delete_character(self):
        """删除角色"""
        dialog = CTkInputDialog(parent=self.top, text="请输入要删除的角色名称:", title="删除角色")
        name = dialog.get_input()
        if name:
            name = name.strip()
            char_file = self._character_file(name)
            if not char_file:
                return
            if os.path.exists(char_file):
                if messagebox.askyesno("确认删除", f"确定删除角色“{name}”吗？", parent=self.top):
                    try:
                        os.remove(char_file)
                    except OSError as e:
                        messagebox.showerror("删除失败", str(e), parent=self.top)
                        return
                    self.load_characters()
            else:
                messagebox.showinfo("未找到角色", f"没有找到角色：{name}", parent=self.top)


class EditDialog:
    """编辑对话框"""

    def __init__(self, parent, title, content):
        self.top = CTkToplevel(parent)
        self.top.title(title)
        self.top.geometry("700x550")
        self.top.transient(parent)
        self.top.grab_set()

        self.result = None

        # 文本编辑区域
        self.text = CTkTextbox(self.top, font=FONT_BODY, corner_radius=CORNER_RADIUS_LG,
                                fg_color=COLORS["bg_input"], border_width=1, border_color=COLORS["border"])
        self.text.pack(fill="both", expand=True, padx=15, pady=15)
        self.text.insert("1.0", content)

        # 按钮
        button_frame = CTkFrame(self.top, fg_color="transparent")
        button_frame.pack(pady=10)

        CTkButton(button_frame, text="保存", command=self.ok,
                  width=100, **btn_primary()).pack(side="left", padx=10)
        CTkButton(button_frame, text="取消", command=self.cancel,
                  width=100, **btn_ghost(height=BTN_HEIGHT_LG)).pack(side="left", padx=10)

    def ok(self):
        self.result = self.text.get("1.0", "end-1c")
        self.top.destroy()

    def cancel(self):
        self.top.destroy()


def main():
    """主函数"""
    app = ModernNovelWriterApp()
    app.run()


if __name__ == '__main__':
    main()
