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
import subprocess
import threading
import time
import shutil
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
AI_ENGINE_LABELS = ["Claude Code", "Codex"]
AI_ENGINE_KEYS = {
    "Claude Code": "claude",
    "Codex": "codex",
}
AI_ENGINE_NAMES = {
    "claude": "Claude Code",
    "codex": "Codex",
}
AI_ENGINE_DEFAULT_PROMPTS = {
    "claude": "/novel-write ",
    "codex": "$novel-write ",
}
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


def ensure_skill_files(target_dir=None, engine=None):
    """确保 Claude/Codex 所需的 Skill 文件存在于目标目录"""
    target_dir = target_dir or os.getcwd()
    os.makedirs(target_dir, exist_ok=True)
    copied_any = False
    all_skill_roots = [
        ('.claude', os.path.join('.claude', 'skills', 'novel-write')),
        ('.agents', os.path.join('.agents', 'skills', 'novel-write')),
    ]
    if engine == 'claude':
        skill_roots = all_skill_roots[:1]
    elif engine == 'codex':
        skill_roots = all_skill_roots[1:]
    else:
        skill_roots = all_skill_roots

    for root_name, skill_path in skill_roots:
        dest_skill_dir = os.path.join(target_dir, skill_path)
        if os.path.exists(dest_skill_dir):
            copied_any = True
            continue

        resource_skill_dir = get_resource_path(skill_path)
        if not os.path.exists(resource_skill_dir):
            continue

        try:
            shutil.copytree(resource_skill_dir, dest_skill_dir, dirs_exist_ok=True)
            copied_any = True
        except Exception as e:
            print(f"释放 {root_name} Skill 文件失败: {e}")

    return copied_any


def get_missing_skill_paths(target_dir):
    """返回项目目录中缺失的 skill 路径"""
    required = [
        os.path.join(target_dir, '.claude', 'skills', 'novel-write', 'SKILL.md'),
        os.path.join(target_dir, '.agents', 'skills', 'novel-write', 'SKILL.md'),
    ]
    return [path for path in required if not os.path.exists(path)]


def has_bundled_skill_resources():
    """检查发布包中是否包含 Claude/Codex 两套 skill 资源"""
    required = [
        os.path.join('.claude', 'skills', 'novel-write', 'SKILL.md'),
        os.path.join('.agents', 'skills', 'novel-write', 'SKILL.md'),
    ]
    return all(os.path.exists(get_resource_path(path)) for path in required)


class ModernNovelWriterApp:
    """现代风格网文写作助手"""

    def __init__(self):
        self.root = CTk()
        self.root.title("网文写作助手")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)

        # 项目状态
        self.project_path = None
        self.project_config = {}
        self.app_settings = self.load_app_settings()
        self.ai_engine = self.app_settings.get('ai_engine', 'claude')
        self._cmd_running = False
        self.proc = None
        self._last_command_output = ""
        self._diagnostic_running = False

        # 创建界面
        self.create_ui()

        # 窗口关闭时清理进程
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_app_settings(self):
        """读取全局应用设置"""
        settings_path = get_app_settings_path()
        if not os.path.exists(settings_path):
            return {}
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_app_settings(self):
        """保存全局应用设置"""
        settings_path = get_app_settings_path()
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.app_settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if hasattr(self, 'log_text'):
                self._append_log(f"保存应用设置失败: {e}", "ERROR")
            else:
                print(f"保存应用设置失败: {e}")

    def get_ai_engine_label(self):
        """获取当前 AI 引擎显示名"""
        return AI_ENGINE_NAMES.get(self.ai_engine, "Claude Code")

    def get_default_prompt(self):
        """获取当前引擎的默认输入前缀"""
        return AI_ENGINE_DEFAULT_PROMPTS.get(self.ai_engine, "/novel-write ")

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

        # AI 引擎选择
        self.create_engine_selector()

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

    def create_engine_selector(self):
        """创建 AI 引擎选择器"""
        CTkFrame(self.left_scroll, height=1, fg_color=COLORS["divider"]).pack(fill="x", padx=20, pady=(10, 0))
        CTkLabel(self.left_scroll, text="AI 引擎",
                 font=FONT_SECTION, text_color=COLORS["text_primary"]).pack(anchor="w", padx=20, pady=(10, 5))

        engine_frame = CTkFrame(self.left_scroll, corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_card"])
        engine_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.engine_var = ctk.StringVar(value=self.get_ai_engine_label())
        engine_menu = CTkOptionMenu(
            engine_frame,
            values=AI_ENGINE_LABELS,
            variable=self.engine_var,
            command=self.change_ai_engine,
            width=230,
            height=BTN_HEIGHT_MD,
            **menu_style(),
        )
        engine_menu.pack(fill="x", padx=12, pady=(12, 6))

        self.engine_hint_var = ctk.StringVar()
        CTkLabel(engine_frame, textvariable=self.engine_hint_var,
                 font=FONT_SMALL, text_color=COLORS["text_secondary"],
                 wraplength=230, justify="left").pack(anchor="w", padx=12, pady=(0, 12))
        self.update_engine_hint()

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

        self.theme_var = ctk.StringVar(value="浅色")
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

        self.refresh_dashboard()

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
        total_words = self.word_count()
        chapters_dir = os.path.join(self.project_path, 'chapters')
        chapter_files = []
        if os.path.exists(chapters_dir):
            chapter_files = sorted([f for f in os.listdir(chapters_dir) if f.endswith('.md')])
        target_words = max(int(self.project_config.get('target_words', 0) or 0), 1)
        progress = min(total_words / target_words * 100, 999)

        self.dashboard_subtitle_var.set(f"《{project_name}》 · {project_type} · {platform}，继续把故事推进到下一处钩子。")
        self.dashboard_word_var.set(str(total_words))
        self.dashboard_chapter_var.set(str(len(chapter_files)))
        self.dashboard_target_var.set(f"{progress:.1f}%")

        self.dashboard_world_var.set(self.get_material_status("世界观", os.path.join(self.project_path, 'worldbuilding', 'settings.md')))
        self.dashboard_role_var.set(self.get_character_status())
        self.dashboard_outline_var.set(self.get_material_status("大纲", os.path.join(self.project_path, 'outline', 'master-outline.md')))
        self.dashboard_note_var.set(self.get_material_status("伏笔", os.path.join(self.project_path, 'notes', 'misc.md')))

        if hasattr(self, 'project_snapshot_var'):
            self.project_snapshot_var.set(f"{len(chapter_files)} 章 · {total_words} 字 · 进度 {progress:.1f}%")
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
            words = len(content.replace(" ", "").replace("\n", ""))
            self.status_words_var.set(f"📝 {words} 字")

    def change_theme(self, mode):
        """切换主题"""
        if mode == "浅色":
            ctk.set_appearance_mode("light")
        elif mode == "深色":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("system")

    def change_ai_engine(self, label):
        """切换 AI 引擎"""
        self.ai_engine = AI_ENGINE_KEYS.get(label, 'claude')
        self.app_settings['ai_engine'] = self.ai_engine
        self.save_app_settings()

        if self.project_config is not None:
            self.project_config['ai_engine'] = self.ai_engine
            if self.project_path:
                self.save_project_config()

        self.update_engine_hint()
        self.refresh_dashboard()
        if hasattr(self, 'chat_var'):
            current = self.chat_var.get()
            default_prompts = list(AI_ENGINE_DEFAULT_PROMPTS.values())
            stripped_defaults = [prompt.strip() for prompt in default_prompts]
            if not current.strip() or current in default_prompts or current.strip() in stripped_defaults:
                self.chat_var.set(self.get_default_prompt())
        self.update_status(f"已切换 AI 引擎: {self.get_ai_engine_label()}")
        self._append_log(f"AI 引擎切换为: {self.get_ai_engine_label()}", "INFO")

    def update_engine_hint(self):
        """刷新引擎说明"""
        if not hasattr(self, 'engine_hint_var'):
            return
        if self.ai_engine == 'codex':
            mode_hint = "当前直接使用本机 Codex CLI 的现有配置（~/.codex/config.toml 和登录信息）。"
            text = f"使用 OpenAI Codex CLI。项目会自动释放 .agents/skills/novel-write；{mode_hint}"
        else:
            text = "使用 Claude Code CLI。需要已登录 Claude，支持 /novel-write Skill。"
        self.engine_hint_var.set(text)

    def normalize_user_message(self, message):
        """去掉不同引擎的显式 Skill 前缀，得到实际写作指令"""
        normalized = message.strip()
        for prefix in ("/novel-write", "$novel-write"):
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
- 优先读取项目中的 project.md、outline、chapters、characters、worldbuilding、style、notes 等上下文。
- 在 Windows 上读取中文 Markdown/Skill 文件时必须指定 UTF-8，例如 PowerShell 使用 `Get-Content -Encoding UTF8`；不要使用默认编码读取。
- 需要生成或修改内容时，直接写入当前小说项目对应文件。
- 保持章节、大纲、人物、世界观和伏笔记录一致。
- 最后简要说明完成了什么，以及修改了哪些文件。
"""

    def build_ai_command(self, message, cwd):
        """根据当前引擎构造 CLI 命令和 stdin"""
        if self.ai_engine == 'codex':
            prompt = self.build_codex_prompt(message)
            cmd = [
                "cmd.exe", "/d", "/c",
                "codex",
                "--ask-for-approval", "never",
                "exec",
            ]
            cmd.extend([
                "--skip-git-repo-check",
                "--sandbox", "workspace-write",
                "-C", cwd,
                "-",
            ])
            return cmd, prompt

        cmd = [
            "cmd.exe", "/d", "/c",
            "claude", "-p", message, "-c",
            "--output-format", "stream-json",
            "--include-partial-messages",
            "--verbose",
            "--allowedTools", "Write", "Edit",
        ]
        return cmd, ""

    def build_ai_environment(self):
        """构造 AI 子进程环境变量。"""
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("LANG", "C.UTF-8")
        env.setdefault("LC_ALL", "C.UTF-8")
        return env

    def get_failure_hint(self):
        """根据当前引擎和最近输出生成失败提示"""
        output = getattr(self, '_last_command_output', '')
        if self.ai_engine == 'codex':
            if 'Missing optional dependency' in output:
                return "[Codex 提示] Codex CLI 安装不完整，请运行：npm install -g @openai/codex@latest\n"
            if 'not logged in' in output.lower() or 'login' in output.lower():
                return "[Codex 提示] 请先运行 codex login 完成登录。\n"
            if '503 Service Unavailable' in output or '127.0.0.1' in output:
                return (
                    "[Codex 提示] 这不是 EXE 缺少 .agents Skill，而是当前 Codex CLI 连接的本地服务/代理不可用。\n"
                    "[Codex 提示] 检测到 127.0.0.1 或 503 Service Unavailable。请打开/重启 Codex Desktop 或本地代理，确认 codex login 有效；也可以点击“Codex 诊断”查看详情。\n"
                )
            if 'unrecognized option' in output.lower() or 'unexpected argument' in output.lower():
                return "[Codex 提示] 当前 Codex CLI 版本可能过旧或参数不兼容，请运行：codex update 或 npm install -g @openai/codex@latest\n"
            return "[Codex 提示] 请确认已安装并登录 Codex CLI：npm install -g @openai/codex@latest，然后运行 codex login。\n"

        if 'not found' in output.lower() or '不是内部或外部命令' in output:
            return "[Claude 提示] 未找到 Claude Code CLI，请运行：npm install -g @anthropic-ai/claude-code\n"
        return "[Claude 提示] 请确认已安装并登录 Claude Code CLI：npm install -g @anthropic-ai/claude-code，然后运行 claude。\n"

    def preflight_ai_command(self, cwd):
        """执行前做快速检查，避免明显不可用的 CLI 配置长时间卡住。"""
        if self.ai_engine != 'codex':
            return None

        if not shutil.which("codex"):
            return "未找到 Codex CLI，请先安装：npm install -g @openai/codex@latest"
        return None

    def check_codex_login_status(self, cwd):
        """快速确认 Codex CLI 是否有可用登录凭据。"""
        returncode, output, timed_out = self.run_command_with_timeout(
            ["cmd.exe", "/d", "/c", "codex", "login", "status"],
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

    def probe_codex_base_url(self, base_url, model="codex-health-check"):
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

            responses_body = json.dumps({
                "model": model,
                "input": "只回复 OK",
                "stream": False,
            }, ensure_ascii=False)
            responses_url = root_url + "/responses"
            responses_status, responses_content = probe(responses_url, "POST", responses_body)
            if responses_status in (200, 400, 401, 403):
                return True, f"{responses_url} HTTP {responses_status}"

            messages_body = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": "只回复 OK"}],
                "stream": False,
            }, ensure_ascii=False)
            messages_url = root_url + "/messages"
            messages_status, _ = probe(messages_url, "POST", messages_body)
            if messages_status == 200 and responses_status in (404, 405, 500, 503):
                return (
                    False,
                    f"{messages_url} HTTP 200，但 {responses_url} HTTP {responses_status}。"
                    "该本机代理像是 Claude/Anthropic Messages 接口，不是 Codex 需要的 OpenAI Responses 接口。"
                )

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

    def read_process_output(self):
        """读取 AI 子进程输出。Claude JSONL 流做友好展示，其它引擎显示原始输出。"""
        if self.ai_engine == 'claude':
            self.read_claude_stream_output()
        else:
            self.read_raw_process_output()

    def read_raw_process_output(self):
        """按块读取原始终端输出。"""
        fd = self.proc.stdout.fileno()
        while True:
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            try:
                text = chunk.decode("utf-8", errors="replace")
            except Exception:
                text = str(chunk)
            text = repair_mojibake_text(text)
            self.record_command_output(text)
            self.root.after(0, lambda t=text: self._append_terminal(t))

    def read_claude_stream_output(self):
        """解析 Claude stream-json 输出，只展示实时文本和关键状态。"""
        pending = ""
        fd = self.proc.stdout.fileno()
        while True:
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            try:
                text = chunk.decode("utf-8", errors="replace")
            except Exception:
                text = str(chunk)
            self.record_command_output(text)
            pending += text
            while "\n" in pending:
                line, pending = pending.split("\n", 1)
                rendered = self.render_claude_stream_line(line)
                if rendered:
                    self.root.after(0, lambda t=rendered: self._append_terminal(t))
        if pending.strip():
            rendered = self.render_claude_stream_line(pending)
            if rendered:
                self.root.after(0, lambda t=rendered: self._append_terminal(t))

    def record_command_output(self, text):
        """保存最近输出用于失败提示。"""
        self._last_command_output += text
        if len(self._last_command_output) > 6000:
            self._last_command_output = self._last_command_output[-6000:]

    def render_claude_stream_line(self, line):
        """把 Claude JSONL 事件转成人能读的终端文本。"""
        stripped = line.strip()
        if not stripped:
            return ""
        try:
            event = json.loads(stripped)
        except Exception:
            return line + "\n"

        event_type = event.get("type")
        if event_type == "system":
            subtype = event.get("subtype")
            if subtype == "init":
                model = event.get("model", "unknown")
                return f"[Claude] 会话已启动，模型: {model}\n"
            if subtype == "status":
                status = event.get("status")
                if status:
                    return f"[Claude] {status}...\n"
            return ""

        if event_type == "stream_event":
            stream_event = event.get("event", {})
            stream_type = stream_event.get("type")
            if stream_type == "content_block_delta":
                delta = stream_event.get("delta", {})
                if delta.get("type") == "text_delta":
                    return delta.get("text", "")
                if delta.get("type") == "input_json_delta":
                    return delta.get("partial_json", "")
            if stream_type == "content_block_start":
                block = stream_event.get("content_block", {})
                block_type = block.get("type")
                if block_type == "tool_use":
                    name = block.get("name", "tool")
                    return f"\n[Claude 工具] {name}\n"
            if stream_type == "message_stop":
                return "\n"
            return ""

        if event_type == "result":
            if event.get("is_error"):
                return f"\n[Claude 错误] {event.get('result') or event.get('subtype') or '执行失败'}\n"
            return ""

        if event_type == "assistant":
            return ""

        return ""

    # ==================== AI 命令执行 ====================

    def send_message(self):
        """发送消息（统一命令和回复）"""
        message = self.chat_var.get().strip()
        if not message:
            return
        if not self.project_path:
            messagebox.showwarning("提示", "请先新建或打开小说项目，再执行 AI 写作任务。")
            return

        # 清空输入框
        self.chat_var.set("")

        # 显示用户消息
        engine_name = self.get_ai_engine_label()
        self._terminal_write(f"\n[{engine_name}] >>> {message}\n\n")

        # 记录日志
        self._append_log(f"{engine_name} 执行命令: {message}", "CMD")

        self._cmd_start_time = time.time()
        self._cmd_running = True
        self._last_command_output = ""
        self._update_running_status(f"{engine_name} 正在处理")

        def _run():
            try:
                cwd = self.project_path
                ensure_skill_files(cwd, self.ai_engine)

                preflight_error = self.preflight_ai_command(cwd)
                if preflight_error:
                    self.root.after(0, lambda e=preflight_error: self._command_preflight_failed(e))
                    return

                # 记录命令执行前的文件状态
                old_state = self._get_file_state(cwd)

                cmd, stdin_text = self.build_ai_command(message, cwd)
                stdin_arg = subprocess.PIPE if stdin_text else subprocess.DEVNULL

                self.proc = subprocess.Popen(
                    cmd,
                    stdin=stdin_arg,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=cwd,
                    env=self.build_ai_environment(),
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    bufsize=0  # 禁用缓冲，实时输出
                )

                if stdin_text and self.proc.stdin:
                    self.proc.stdin.write(stdin_text.encode("utf-8"))
                    self.proc.stdin.close()

                self.read_process_output()
                self.proc.wait()

                # 记录命令执行后的文件状态，显示变化
                new_state = self._get_file_state(cwd)
                changes = self._get_file_changes(old_state, new_state)
                if changes:
                    self.root.after(0, lambda: self._append_terminal("\n--- 文件修改记录 ---\n"))
                    for change in changes:
                        self.root.after(0, lambda c=change: self._append_terminal(c + "\n"))
                        # 记录到日志面板
                        self.root.after(0, lambda c=change: self._append_log(c, "FILE"))

                self.root.after(0, self._command_done, self.proc.returncode)
            except Exception as e:
                self.root.after(0, self._command_error, str(e))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _command_preflight_failed(self, message):
        """执行前检查失败时显示可操作原因。"""
        self._cmd_running = False
        self._terminal_write(f"\n[执行前检查失败]\n{message}\n")
        self._terminal_write(f"{'='*60}\n\n")
        self.update_status("执行前检查失败")
        self._append_log(f"执行前检查失败: {message}", "ERROR")
        self.progress_label.configure(text="检查失败")
        self.progress_frame.configure(fg_color=COLORS["status_error"])
        self.root.after(3000, self._reset_progress)

    def stop_command(self):
        """终止正在运行的命令"""
        if self.proc and self.proc.poll() is None:
            try:
                self.kill_process_tree(self.proc.pid)
                self._terminal_write("\n[已终止命令]\n")
                self._cmd_running = False
                self.update_status("命令已终止")
            except Exception as e:
                self._terminal_write(f"\n[终止失败: {e}]\n")
        else:
            self._terminal_write("\n[没有正在运行的命令]\n")

    def _terminal_write(self, text):
        """向只读终端写入文本"""
        text = repair_mojibake_text(str(text))
        self.terminal_text.configure(state="normal")
        self.terminal_text.insert("end", text)
        self.terminal_text.see("end")
        self.terminal_text.configure(state="disabled")

    def _append_terminal(self, text):
        """追加文本到终端"""
        self._terminal_write(text)

    def _command_done(self, returncode):
        """命令执行完成"""
        self._cmd_running = False
        elapsed = time.time() - getattr(self, '_cmd_start_time', time.time())
        elapsed_str = f"{elapsed:.1f}秒" if elapsed < 60 else f"{elapsed/60:.1f}分钟"
        if returncode == 0:
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
        if self.project_path:
            self.load_project_content()

        # 3秒后恢复就绪状态
        self.root.after(3000, self._reset_progress)

    def _reset_progress(self):
        """重置进度提示区域"""
        if not getattr(self, '_cmd_running', False):
            self.progress_label.configure(text="就绪")
            self.progress_frame.configure(fg_color=COLORS["status_ready"])

    def _command_error(self, error):
        """命令执行出错"""
        self._cmd_running = False
        self._terminal_write(f"\n[错误] {error}\n")
        self._terminal_write(f"{'='*60}\n\n")
        self.update_status("命令执行出错")
        self._append_log(f"命令执行出错: {error}", "ERROR")
        self.progress_label.configure(text="出错")
        self.progress_frame.configure(fg_color=COLORS["status_error"])

        # 3秒后恢复就绪状态
        self.root.after(3000, self._reset_progress)

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
            report = self.build_codex_diagnostics_report()
            self.root.after(0, lambda: self._finish_codex_diagnostics(report))

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

        codex_path = shutil.which("codex")
        lines.append(f"PATH 中的 codex: {codex_path or '未找到'}")

        if self.project_path:
            ensure_skill_files(self.project_path, 'codex')
            codex_skill = os.path.join(self.project_path, '.agents', 'skills', 'novel-write', 'SKILL.md')
            claude_skill = os.path.join(self.project_path, '.claude', 'skills', 'novel-write', 'SKILL.md')
            lines.append(f"项目 Codex Skill: {'存在' if os.path.exists(codex_skill) else '缺失'} ({codex_skill})")
            lines.append(f"项目 Claude Skill: {'存在' if os.path.exists(claude_skill) else '缺失'} ({claude_skill})")

        lines.extend(self.get_codex_config_summary())
        local_info = self.get_codex_local_provider_info()
        local_base_url = local_info.get("base_url", "")
        if local_base_url:
            ok, detail = self.probe_codex_base_url(local_base_url)
            lines.append(f"本机 provider 探测: {'通过' if ok else '失败'} - {detail}")
            lines.append(f"本机 provider 端口进程: {self.find_local_port_owner(local_base_url)}")
        lines.append("")
        lines.append(self.capture_command("where codex", ["where.exe", "codex"], timeout=8))
        lines.append(self.capture_command("codex --version", ["cmd.exe", "/d", "/c", "codex", "--version"], timeout=8))
        doctor_cmd = ["cmd.exe", "/d", "/c", "codex", "doctor"]
        lines.append("[Codex 诊断] 执行任务时直接调用 codex exec，并读取本机 Codex CLI 的现有配置。")
        lines.append(self.capture_command("codex doctor", doctor_cmd, timeout=25))

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
        try:
            completed = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.project_path or os.getcwd(),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                timeout=timeout,
                env=self.build_ai_environment(),
                encoding="utf-8",
                errors="replace",
            )
            output = completed.stdout.strip() or "(无输出)"
            if len(output) > 3000:
                output = output[-3000:]
            return f"[{title}] returncode={completed.returncode}\n{output}"
        except subprocess.TimeoutExpired:
            return f"[{title}] 超时（超过 {timeout} 秒未返回）"
        except FileNotFoundError:
            return f"[{title}] 未找到命令"
        except Exception as e:
            return f"[{title}] 执行失败: {e}"

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
                    mtime = os.path.getmtime(filepath)
                    size = os.path.getsize(filepath)
                    state[filepath] = (mtime, size)
                except:
                    pass
        return state

    def _get_file_changes(self, old_state, new_state):
        """比较文件状态，返回变化列表"""
        changes = []
        all_files = set(old_state.keys()) | set(new_state.keys())

        for filepath in all_files:
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
        dialog = NewProjectDialog(self.root, self.app_settings.get('project_root', get_default_project_root()))
        self.root.wait_window(dialog.top)

        if dialog.result:
            project_name = dialog.result['name']
            project_type = dialog.result['type']
            project_path = dialog.result['path']
            self.app_settings['project_root'] = project_path
            self.save_app_settings()

            full_path = os.path.join(project_path, project_name)
            self.create_project_structure(full_path, project_name, dialog.result)
            self.prepare_project_skills(full_path)

            self.project_path = full_path
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
                'ai_engine': self.ai_engine,
            }
            self.save_project_config()

            self.project_name_var.set(project_name)
            self.project_type_var.set(f"类型: {project_type} | {dialog.result.get('platform', '')}")
            self.update_status(f"项目 '{project_name}' 创建成功")
            self.refresh_dashboard()

            self.chat_var.set(self.format_skill_command(f"新建小说 --name {project_name} --type {project_type}"))
            self.send_message()

    def open_project(self):
        """打开项目"""
        from tkinter import filedialog
        path = filedialog.askdirectory(title="选择项目目录")
        if path:
            config_file = os.path.join(path, 'project.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.project_config = json.load(f)
                self.project_path = path
                self.prepare_project_skills(path)
                saved_engine = self.project_config.get('ai_engine')
                if saved_engine in AI_ENGINE_NAMES:
                    self.ai_engine = saved_engine
                    self.app_settings['ai_engine'] = saved_engine
                    self.save_app_settings()
                    if hasattr(self, 'engine_var'):
                        self.engine_var.set(self.get_ai_engine_label())
                    self.update_engine_hint()
                    if hasattr(self, 'chat_var'):
                        self.chat_var.set(self.get_default_prompt())
                self.project_name_var.set(self.project_config.get('name', '未命名'))
                self.project_type_var.set(f"类型: {self.project_config.get('type', '未知')}")
                self.update_status(f"已打开项目: {self.project_config.get('name')}")
                self.load_project_content()
                self.refresh_dashboard()

    def save_project(self):
        """保存项目"""
        if not self._check_project():
            return

        self.save_chapter()
        self.save_project_config()
        self.refresh_dashboard()
        self.update_status("项目已保存")

    def save_project_config(self):
        """保存项目配置"""
        if self.project_path:
            config_file = os.path.join(self.project_path, 'project.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.project_config, f, ensure_ascii=False, indent=2)

    def prepare_project_skills(self, path):
        """为项目准备 Claude/Codex 两套 novel-write skill"""
        ensure_skill_files(path)
        missing = get_missing_skill_paths(path)
        if missing:
            message = "项目缺少内置写作 Skill，Claude/Codex 可能无法识别 novel-write。\n\n缺失:\n" + "\n".join(missing)
            self.update_status("写作 Skill 释放不完整")
            if hasattr(self, 'log_text'):
                self._append_log(message, "ERROR")
            messagebox.showwarning("Skill 资源缺失", message)
            return False
        return True

    def create_project_structure(self, path, name, config):
        """创建项目目录结构"""
        directories = [
            'worldbuilding',
            'characters',
            'outline/chapter-outs',
            'chapters',
            'style',
            'notes',
            'export',
        ]

        for dir_name in directories:
            os.makedirs(os.path.join(path, dir_name), exist_ok=True)

        self.create_initial_files(path, name, config)

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

    def load_project_content(self):
        """加载项目内容"""
        if not self._check_project():
            return

        self.load_outline()
        self.refresh_stats()
        self._load_chapter_list()
        self.refresh_dashboard()

    def _load_chapter_list(self):
        """扫描 chapters 目录，动态更新章节选择器"""
        chapters = self.get_chapter_choices()
        if chapters:
            self.chapter_menu.configure(values=chapters)
            self.chapter_var.set(chapters[0])
            self._on_chapter_selected(chapters[0])
        else:
            self.chapter_menu.configure(values=["暂无章节"])
            self.chapter_var.set("暂无章节")
            self.update_chapter_nav_state()

    def get_chapter_choices(self):
        """返回按章节号排序的章节显示名。"""
        if not self.project_path:
            return []
        chapters_dir = os.path.join(self.project_path, 'chapters')
        if not os.path.exists(chapters_dir):
            return []

        chapters = []
        for file_name in os.listdir(chapters_dir):
            match = re.fullmatch(r"ch(\d+)\.md", file_name)
            if match:
                raw_num = match.group(1)
                chapters.append((int(raw_num), raw_num))
        chapters.sort()
        return [f"第{raw_num}章" for _, raw_num in chapters]

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
        self._on_chapter_selected(prev_choice)
        self.update_status(f"已切换到 {prev_choice}")

    def next_chapter(self):
        """切换到下一章。"""
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
        self._on_chapter_selected(next_choice)
        self.update_status(f"已切换到 {next_choice}")

    def _on_chapter_selected(self, choice):
        """切换章节时自动加载内容"""
        if not self.project_path or choice == "暂无章节":
            self.update_chapter_nav_state()
            return
        num = choice.replace('第', '').replace('章', '')
        path = os.path.join(self.project_path, 'chapters', f'ch{num}.md')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.writing_text.delete("1.0", "end")
            self.writing_text.insert("1.0", content)
            self.update_word_count()
        self.update_chapter_nav_state()

    def load_outline(self):
        """加载大纲"""
        if not self.project_path:
            return

        outline_dir = os.path.join(self.project_path, 'outline')
        if not os.path.exists(outline_dir):
            return

        # 更新大纲选择菜单
        outlines = ["总大纲"]
        for f in sorted(os.listdir(outline_dir)):
            # 匹配 vol1-outline.md 或 volume-1-outline.md 格式
            if f.endswith('-outline.md') and not f.startswith('master'):
                name = f.replace('-outline.md', '')
                if name.startswith('vol'):
                    # vol1 -> 第1卷
                    num = name.replace('vol', '')
                    outlines.append(f"第{num}卷")
                elif name.startswith('volume-'):
                    # volume-1 -> 第1卷
                    num = name.replace('volume-', '')
                    outlines.append(f"第{num}卷")

        self.outline_menu.configure(values=outlines)

        # 加载当前选择的大纲
        self._on_outline_selected(self.outline_var.get())

    def _on_outline_selected(self, choice):
        """切换大纲时自动加载内容"""
        if not self.project_path:
            return

        outline_dir = os.path.join(self.project_path, 'outline')

        if choice == "总大纲":
            outline_file = os.path.join(outline_dir, 'master-outline.md')
        else:
            # 提取卷号
            volume_num = choice.replace('第', '').replace('卷', '')
            # 尝试两种文件名格式
            outline_file = os.path.join(outline_dir, f'vol{volume_num}-outline.md')
            if not os.path.exists(outline_file):
                outline_file = os.path.join(outline_dir, f'volume-{volume_num}-outline.md')

        if os.path.exists(outline_file):
            with open(outline_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.outline_text.delete("1.0", "end")
            self.outline_text.insert("1.0", content)
        else:
            self.outline_text.delete("1.0", "end")
            self.outline_text.insert("1.0", f"【{choice}】尚未生成")

    # ==================== 项目检查 ====================

    def _check_project(self):
        """检查是否已打开项目，未打开时弹窗提示"""
        if not self.project_path:
            messagebox.showwarning("提示", "请先打开或新建项目")
            return False
        return True

    # ==================== 大纲功能 ====================

    def generate_outline(self):
        """生成总大纲"""
        if not self._check_project():
            return
        self.chat_var.set(self.format_skill_command("生成总大纲"))
        self.send_message()
        self.tabview.set(TAB_STUDIO)

    def generate_volume_outline(self):
        """生成卷大纲"""
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
        if not self._check_project():
            return
        outline_file = os.path.join(self.project_path, 'outline', 'master-outline.md')
        content = self.outline_text.get("1.0", "end")
        with open(outline_file, 'w', encoding='utf-8') as f:
            f.write(content)
        self.update_status("大纲已保存")

    # ==================== 章节功能 ====================

    def write_chapter(self):
        """写章节"""
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
        if not self._check_project():
            return
        self.chat_var.set(self.format_skill_command("继续写"))
        self.send_message()
        self.tabview.set(TAB_STUDIO)

    def plan_chapter(self):
        """规划章节"""
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
        if not self._check_project():
            return
        chapter_name = self.chapter_var.get()
        chapter_num = chapter_name.replace('第', '').replace('章', '')
        chapter_file = os.path.join(self.project_path, 'chapters', f'ch{chapter_num.zfill(3)}.md')
        content = self.writing_text.get("1.0", "end")
        with open(chapter_file, 'w', encoding='utf-8') as f:
            f.write(content)
        self.refresh_dashboard()
        self.update_status(f"章节 {chapter_name} 已保存")

    # ==================== 人物功能 ====================

    def view_characters(self):
        """查看人物管理"""
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
        if not self._check_project():
            return
        settings_file = os.path.join(self.project_path, 'worldbuilding', 'settings.md')
        if not os.path.exists(settings_file):
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(self.get_default_worldbuilding_template())
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        dialog = EditDialog(self.root, "世界观设定", content)
        self.root.wait_window(dialog.top)
        if dialog.result:
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(dialog.result)
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
        if not self._check_project():
            return
        style_file = os.path.join(self.project_path, 'style', 'style-config.md')
        if not os.path.exists(style_file):
            os.makedirs(os.path.dirname(style_file), exist_ok=True)
            with open(style_file, 'w', encoding='utf-8') as f:
                f.write(self.get_default_style_template())
        with open(style_file, 'r', encoding='utf-8') as f:
            content = f.read()
        dialog = EditDialog(self.root, "风格配置", content)
        self.root.wait_window(dialog.top)
        if dialog.result:
            with open(style_file, 'w', encoding='utf-8') as f:
                f.write(dialog.result)
            self.update_status("风格配置已更新")
            self.refresh_dashboard()

    def edit_notes(self):
        """编辑伏笔和杂项笔记"""
        if not self._check_project():
            return
        notes_file = os.path.join(self.project_path, 'notes', 'misc.md')
        if not os.path.exists(notes_file):
            os.makedirs(os.path.dirname(notes_file), exist_ok=True)
            with open(notes_file, 'w', encoding='utf-8') as f:
                f.write("# 杂项笔记\n\n## 伏笔追踪\n| ID | 伏笔内容 | 埋设章节 | 计划回收 | 实际回收 | 状态 |\n|----|----------|----------|----------|----------|------|\n\n## 待办事项\n\n## 灵感记录\n")
        with open(notes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        dialog = EditDialog(self.root, "伏笔笔记", content)
        self.root.wait_window(dialog.top)
        if dialog.result:
            with open(notes_file, 'w', encoding='utf-8') as f:
                f.write(dialog.result)
            self.update_status("伏笔笔记已更新")
            self.refresh_dashboard()

    # ==================== 统计功能 ====================

    def word_count(self):
        """字数统计"""
        if not self._check_project():
            return 0
        total_words = 0
        chapters_dir = os.path.join(self.project_path, 'chapters')
        if os.path.exists(chapters_dir):
            for file_name in os.listdir(chapters_dir):
                if file_name.endswith('.md'):
                    with open(os.path.join(chapters_dir, file_name), 'r', encoding='utf-8') as f:
                        content = f.read()
                        chinese_chars = len([c for c in content if '一' <= c <= '鿿'])
                        total_words += chinese_chars
        return total_words

    def count_words(self):
        """统计当前章节字数"""
        content = self.writing_text.get("1.0", "end")
        chinese_chars = len([c for c in content if '一' <= c <= '鿿'])
        self.word_count_var.set(f"字数: {chinese_chars}")

    def update_word_count(self, _=None):
        """更新字数统计"""
        self.count_words()

    def refresh_stats(self):
        """刷新统计信息"""
        if not self._check_project():
            return

        self.stats_text.delete("1.0", "end")

        chapters_count = 0
        chapters_dir = os.path.join(self.project_path, 'chapters')
        chapter_files = []
        if os.path.exists(chapters_dir):
            chapter_files = sorted([f for f in os.listdir(chapters_dir) if f.endswith('.md')])
            chapters_count = len(chapter_files)

        total_words = self.word_count()

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
- 完成进度：{total_words / self.project_config.get('target_words', 1) * 100:.1f}%

## 章节列表
{chr(10).join(f'- {f.replace(".md", "")}' for f in chapter_files) if chapter_files else '暂无章节'}

## 最近更新
- 最后保存时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.stats_text.insert("1.0", stats)
        self.refresh_dashboard()

    def export_stats(self):
        """导出统计报告"""
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
        self.refresh_stats()
        self.tabview.set(TAB_STATS)

    # ==================== 导出功能 ====================

    def export_novel(self):
        """导出合并所有章节为可发布文件"""
        if not self._check_project():
            return

        chapters_dir = os.path.join(self.project_path, 'chapters')
        if not os.path.exists(chapters_dir):
            messagebox.showwarning("提示", "没有找到章节目录")
            return

        files = sorted([f for f in os.listdir(chapters_dir)
                        if f.startswith('ch') and f.endswith('.md')])
        if not files:
            messagebox.showwarning("提示", "没有找到章节文件")
            return

        export_dir = os.path.join(self.project_path, 'export')
        os.makedirs(export_dir, exist_ok=True)

        project_name = self.project_config.get('name', '未命名')
        export_file = os.path.join(export_dir, f'{project_name}_全文.md')

        total_chars = 0
        with open(export_file, 'w', encoding='utf-8') as out:
            out.write(f"# {project_name}\n\n")
            for f in files:
                filepath = os.path.join(chapters_dir, f)
                with open(filepath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                # 去除 HTML 元数据注释
                content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
                content = content.strip()
                if content:
                    out.write(content + "\n\n---\n\n")
                    chinese_chars = len([c for c in content if '一' <= c <= '鿿'])
                    total_chars += chinese_chars

        self._terminal_write(f"\n[导出完成] {export_file}\n")
        self._terminal_write(f"[共 {len(files)} 章，{total_chars} 字]\n")
        self.update_status(f"导出完成：{len(files)} 章，{total_chars} 字")
        messagebox.showinfo("导出成功",
                            f"已导出 {len(files)} 章，共 {total_chars} 字\n\n"
                            f"文件位置：{export_file}")

    # ==================== 辅助功能 ====================

    def review_chapter(self):
        """审稿"""
        if not self._check_project():
            return
        self.chat_var.set(self.format_skill_command("审稿"))
        self.send_message()
        self.tabview.set(TAB_STUDIO)

    def polish_chapter(self):
        """润色"""
        if not self._check_project():
            return
        self.chat_var.set(self.format_skill_command("润色"))
        self.send_message()
        self.tabview.set(TAB_STUDIO)

    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
        self.root.update_idletasks()

    def on_closing(self):
        """窗口关闭时终止子进程（含子进程树）"""
        self._cmd_running = False
        if self.proc and self.proc.poll() is None:
            try:
                # 杀掉整个进程树（cmd.exe → claude → node）
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
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
        if not self.name_var.get():
            return

        self.result = {
            'name': self.name_var.get(),
            'type': self.type_var.get(),
            'platform': self.platform_var.get(),
            'pov': self.pov_var.get(),
            'target_words': int(self.words_var.get()) * 10000,
            'target_chapters': int(self.chapters_var.get()),
            'audience': self.audience_var.get(),
            'hook': self.hook_var.get(),
            'path': self.path_var.get().strip() or self.default_project_root,
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
            files = [f for f in os.listdir(characters_dir) if f.endswith('.md') and f != 'index.md']

            if files:
                self.character_list.insert("end", "角色列表:\n\n")
                for i, file_name in enumerate(files, 1):
                    char_name = file_name.replace('.md', '')
                    self.character_list.insert("end", f"{i}. {char_name}\n")
            else:
                self.character_list.insert("end", "暂无角色，点击'新建角色'创建。")

    def new_character(self):
        """新建角色"""
        dialog = CTkInputDialog(parent=self.top, text="请输入角色名称:", title="新建角色")
        name = dialog.get_input()
        if name:
            char_file = os.path.join(self.project_path, 'characters', f'{name}.md')
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
            with open(char_file, 'w', encoding='utf-8') as f:
                f.write(char_md)

            self.load_characters()

    def edit_character(self):
        """编辑角色"""
        dialog = CTkInputDialog(parent=self.top, text="请输入要编辑的角色名称:", title="编辑角色")
        name = dialog.get_input()
        if name:
            char_file = os.path.join(self.project_path, 'characters', f'{name}.md')
            if os.path.exists(char_file):
                with open(char_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                edit_dialog = EditDialog(self.top, f"编辑角色: {name}", content)
                self.top.wait_window(edit_dialog.top)

                if edit_dialog.result:
                    with open(char_file, 'w', encoding='utf-8') as f:
                        f.write(edit_dialog.result)
                    self.load_characters()

    def delete_character(self):
        """删除角色"""
        dialog = CTkInputDialog(parent=self.top, text="请输入要删除的角色名称:", title="删除角色")
        name = dialog.get_input()
        if name:
            char_file = os.path.join(self.project_path, 'characters', f'{name}.md')
            if os.path.exists(char_file):
                os.remove(char_file)
                self.load_characters()


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
        self.result = self.text.get("1.0", "end")
        self.top.destroy()

    def cancel(self):
        self.top.destroy()


def main():
    """主函数"""
    app = ModernNovelWriterApp()
    app.run()


if __name__ == '__main__':
    main()
