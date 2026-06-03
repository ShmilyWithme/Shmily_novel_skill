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
from tkinter import messagebox

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
    "bg_main":        ("#F5F5F5", "#1E1E1E"),
    "bg_sidebar":     ("#EBEBEB", "#1A1A1A"),
    "bg_card":        ("#E8E8E8", "#252525"),
    "bg_input":       ("#E0E0E0", "#2A2A2A"),
    "bg_dialog":      ("#F0F0F0", "#1E1E1E"),

    # ── 强调色 ──
    "accent":         ("#2563EB", "#3B82F6"),
    "accent_hover":   ("#1D4ED8", "#2563EB"),
    "danger":         ("#DC2626", "#DC2626"),
    "danger_hover":   ("#B91C1C", "#B91C1C"),
    "success":        ("#16A34A", "#16A34A"),
    "success_hover":  ("#15803D", "#15803D"),
    "info":           ("#2563EB", "#3B82F6"),
    "info_hover":     ("#1D4ED8", "#2563EB"),

    # ── 文本色 ──
    "text_primary":   ("#1F2937", "#E5E7EB"),
    "text_secondary": ("#6B7280", "#9CA3AF"),
    "text_terminal":  ("#065F46", "#A7F3D0"),
    "text_btn_dark":  ("#1F2937", "#E5E7EB"),
    "text_btn_light": ("#F9FAFB", "#F9FAFB"),

    # ── 边框/分隔线 ──
    "border":         ("#D1D5DB", "#374151"),
    "border_focus":   ("#3B82F6", "#3B82F6"),
    "divider":        ("#E5E7EB", "#2D2D2D"),
    "border_btn":     ("#D1D5DB", "#4B5563"),

    # ── 状态色 ──
    "status_ready":   ("#E5E7EB", "#2D2D2D"),
    "status_running": ("#DBEAFE", "#1E3A5F"),
    "status_success": ("#DCFCE7", "#14532D"),
    "status_error":   ("#FEE2E2", "#450A0A"),

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
FONT_TITLE = ("Microsoft YaHei UI", 24, "bold")
FONT_SECTION = ("Microsoft YaHei UI", 12, "bold")
FONT_BODY = ("Microsoft YaHei UI", 13)
FONT_SMALL = ("Microsoft YaHei UI", 11)


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

def btn_ghost(**kwargs):
    defaults = dict(height=BTN_HEIGHT_SM, corner_radius=CORNER_RADIUS_SM,
                    fg_color="transparent", border_width=1,
                    border_color=COLORS["border_btn"],
                    text_color=COLORS["text_secondary"],
                    hover_color=COLORS["hover_outline"])
    defaults.update(kwargs)
    return defaults

def get_color(key):
    mode = ctk.get_appearance_mode()
    pair = COLORS[key]
    return pair[1] if mode == "Dark" else pair[0]


def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        base_path = sys._MEIPASS
    else:
        # 开发时的路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def ensure_skill_files():
    """确保 Skill 文件存在于当前目录"""
    skill_dir = os.path.join(os.getcwd(), '.claude', 'skills', 'novel-write')
    if os.path.exists(skill_dir):
        return True

    # 从打包资源中释放
    resource_skill_dir = get_resource_path('.claude')
    if os.path.exists(resource_skill_dir):
        try:
            dest_dir = os.path.join(os.getcwd(), '.claude')
            shutil.copytree(resource_skill_dir, dest_dir, dirs_exist_ok=True)
            return True
        except Exception as e:
            print(f"释放 Skill 文件失败: {e}")
            return False

    return False


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
        self._cmd_running = False
        self.proc = None

        # 创建界面
        self.create_ui()

        # 窗口关闭时清理进程
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        header_frame.pack(fill="x", padx=15, pady=(20, 10))

        CTkLabel(header_frame, text="网文写作助手",
                 font=FONT_TITLE, text_color=COLORS["text_primary"]).pack(anchor="w")
        CTkLabel(header_frame, text="Claude Code 集成版",
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(anchor="w")

        # 项目信息卡片
        self.create_project_card()

        # 快捷操作按钮
        self.create_action_buttons()

    def create_project_card(self):
        """创建项目信息卡片"""
        card = CTkFrame(self.left_scroll, corner_radius=CORNER_RADIUS_LG, fg_color=COLORS["bg_card"])
        card.pack(fill="x", padx=15, pady=10)

        # 项目名称
        self.project_name_var = ctk.StringVar(value="未打开项目")
        CTkLabel(card, text="当前项目",
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(anchor="w", padx=15, pady=(15, 0))
        CTkLabel(card, textvariable=self.project_name_var,
                 font=CTkFont(size=16, weight="bold"), text_color=COLORS["text_primary"]).pack(anchor="w", padx=15, pady=(0, 5))

        # 项目类型
        self.project_type_var = ctk.StringVar(value="")
        CTkLabel(card, textvariable=self.project_type_var,
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(anchor="w", padx=15, pady=(0, 15))

    def create_action_buttons(self):
        """创建快捷操作按钮"""
        # 项目操作
        CTkFrame(self.left_scroll, height=1, fg_color=COLORS["divider"]).pack(fill="x", padx=20, pady=(10, 0))
        CTkLabel(self.left_scroll, text="项目操作",
                 font=FONT_SECTION, text_color=COLORS["text_primary"]).pack(anchor="w", padx=20, pady=(10, 5))

        project_buttons = [
            ("新建小说", self.new_project),
            ("打开项目", self.open_project),
            ("保存项目", self.save_project),
        ]

        for text, command in project_buttons:
            btn = CTkButton(self.left_scroll, text=text, command=command, anchor="w",
                           **btn_primary())
            btn.pack(fill="x", padx=15, pady=3)

        # AI 功能
        CTkFrame(self.left_scroll, height=1, fg_color=COLORS["divider"]).pack(fill="x", padx=20, pady=(10, 0))
        CTkLabel(self.left_scroll, text="AI 功能",
                 font=FONT_SECTION, text_color=COLORS["text_primary"]).pack(anchor="w", padx=20, pady=(10, 5))

        ai_buttons = [
            ("生成总大纲", self.generate_outline),
            ("规划章节", self.plan_chapter),
            ("写章节", self.write_chapter),
            ("续写", self.continue_writing),
            ("审稿", self.review_chapter),
            ("润色", self.polish_chapter),
        ]

        for text, command in ai_buttons:
            btn = CTkButton(self.left_scroll, text=text, command=command, anchor="w",
                           **btn_outline())
            btn.pack(fill="x", padx=15, pady=2)

        # 管理功能
        CTkFrame(self.left_scroll, height=1, fg_color=COLORS["divider"]).pack(fill="x", padx=20, pady=(10, 0))
        CTkLabel(self.left_scroll, text="管理功能",
                 font=FONT_SECTION, text_color=COLORS["text_primary"]).pack(anchor="w", padx=20, pady=(10, 5))

        manage_buttons = [
            ("人物管理", self.view_characters),
            ("世界观设定", self.edit_worldbuilding),
            ("风格配置", self.style_settings),
            ("统计分析", self.word_stats),
            ("导出小说", self.export_novel),
        ]

        for text, command in manage_buttons:
            btn = CTkButton(self.left_scroll, text=text, command=command, anchor="w",
                           **btn_outline())
            btn.pack(fill="x", padx=15, pady=2)

        # 主题切换
        theme_frame = CTkFrame(self.left_scroll, fg_color="transparent")
        theme_frame.pack(fill="x", padx=15, pady=(20, 15))

        CTkLabel(theme_frame, text="外观模式:", text_color=COLORS["text_primary"]).pack(side="left", padx=(0, 10))

        self.theme_var = ctk.StringVar(value="浅色")
        theme_menu = CTkOptionMenu(theme_frame, values=["浅色", "深色", "系统"],
                                    variable=self.theme_var, command=self.change_theme,
                                    width=120)
        theme_menu.pack(side="right")

    def create_right_panel(self):
        """创建右侧面板"""
        self.right_panel = CTkFrame(self.main_container, corner_radius=CORNER_RADIUS_XL,
                                     fg_color=COLORS["bg_main"])
        self.right_panel.pack(side="right", fill="both", expand=True)

        # 标签页视图
        self.tabview = CTkTabview(self.right_panel, corner_radius=CORNER_RADIUS_LG,
                                   segmented_button_fg_color=COLORS["bg_sidebar"],
                                   segmented_button_selected_color=COLORS["accent"],
                                   segmented_button_selected_hover_color=COLORS["accent_hover"],
                                   segmented_button_unselected_color=COLORS["bg_sidebar"])
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # 创建标签页
        self.create_writing_tab()
        self.create_outline_tab()
        self.create_terminal_tab()
        self.create_log_tab()
        self.create_stats_tab()

    def create_writing_tab(self):
        """创建写作标签页"""
        self.tabview.add("写作")

        # 工具栏
        toolbar = CTkFrame(self.tabview.tab("写作"), fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        CTkButton(toolbar, text="保存章节", command=self.save_chapter,
                  width=110, **btn_primary()).pack(side="left", padx=5)
        CTkButton(toolbar, text="字数统计", command=self.count_words,
                  width=110, **btn_primary()).pack(side="left", padx=5)

        # 章节选择
        chapter_frame = CTkFrame(self.tabview.tab("写作"), fg_color="transparent")
        chapter_frame.pack(fill="x", padx=10, pady=5)

        CTkLabel(chapter_frame, text="当前章节:", text_color=COLORS["text_secondary"]).pack(side="left", padx=(0, 10))
        self.chapter_var = ctk.StringVar(value="暂无章节")
        self.chapter_menu = CTkOptionMenu(chapter_frame, values=["暂无章节"],
                                          variable=self.chapter_var, width=150,
                                          command=self._on_chapter_selected)
        self.chapter_menu.pack(side="left")

        self.word_count_var = ctk.StringVar(value="字数: 0")
        CTkLabel(chapter_frame, textvariable=self.word_count_var,
                 font=FONT_SMALL, text_color=COLORS["text_secondary"]).pack(side="right")

        # 写作区域
        self.writing_text = CTkTextbox(self.tabview.tab("写作"),
                                        font=FONT_BODY,
                                        corner_radius=CORNER_RADIUS_LG,
                                        fg_color=COLORS["bg_input"],
                                        border_width=1,
                                        border_color=COLORS["border"])
        self.writing_text.pack(fill="both", expand=True, padx=10, pady=10)

        # 绑定字数统计
        self.writing_text.bind("<KeyRelease>", lambda _: self.update_word_count())

    def create_outline_tab(self):
        """创建大纲标签页"""
        self.tabview.add("大纲")

        # 工具栏
        toolbar = CTkFrame(self.tabview.tab("大纲"), fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        CTkButton(toolbar, text="生成总大纲", command=self.generate_outline,
                  width=130, **btn_primary()).pack(side="left", padx=5)
        CTkButton(toolbar, text="生成卷大纲", command=self.generate_volume_outline,
                  width=130, **btn_primary()).pack(side="left", padx=5)
        CTkButton(toolbar, text="保存大纲", command=self.save_outline,
                  width=110, **btn_primary()).pack(side="left", padx=5)

        # 大纲选择区域
        outline_selector = CTkFrame(self.tabview.tab("大纲"), fg_color="transparent")
        outline_selector.pack(fill="x", padx=10, pady=5)

        CTkLabel(outline_selector, text="查看大纲:", text_color=COLORS["text_secondary"]).pack(side="left", padx=(0, 10))

        self.outline_var = ctk.StringVar(value="总大纲")
        self.outline_menu = CTkOptionMenu(outline_selector, values=["总大纲"],
                                          variable=self.outline_var, width=150,
                                          command=self._on_outline_selected)
        self.outline_menu.pack(side="left")

        CTkButton(outline_selector, text="🔄 刷新", command=self.load_outline,
                  width=90, **btn_ghost()).pack(side="left", padx=10)

        # 大纲显示区域
        self.outline_text = CTkTextbox(self.tabview.tab("大纲"),
                                        font=FONT_BODY,
                                        corner_radius=CORNER_RADIUS_LG,
                                        fg_color=COLORS["bg_input"],
                                        border_width=1,
                                        border_color=COLORS["border"])
        self.outline_text.pack(fill="both", expand=True, padx=10, pady=10)

    def create_terminal_tab(self):
        """创建终端标签页"""
        self.tabview.add("终端")

        # 进度提示区域
        self.progress_frame = CTkFrame(self.tabview.tab("终端"), height=40,
                                        corner_radius=CORNER_RADIUS_MD,
                                        fg_color=COLORS["status_ready"])
        self.progress_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.progress_frame.pack_propagate(False)

        self.progress_label = CTkLabel(self.progress_frame, text="就绪",
                                        font=CTkFont(size=13, weight="bold"))
        self.progress_label.pack(expand=True)

        # 工具栏
        toolbar = CTkFrame(self.tabview.tab("终端"), fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=5)

        CTkButton(toolbar, text="清空对话", command=self.clear_terminal,
                  width=100, **btn_ghost()).pack(side="right", padx=5)

        # 终端输出区域（聊天式界面）
        self.terminal_text = CTkTextbox(self.tabview.tab("终端"),
                                         font=FONT_MONO,
                                         corner_radius=CORNER_RADIUS_LG,
                                         fg_color=COLORS["bg_input"],
                                         border_width=1,
                                         border_color=COLORS["border"],
                                         state="disabled")
        self.terminal_text.pack(fill="both", expand=True, padx=10, pady=5)

        # 聊天输入区域（合并命令和回复）
        chat_frame = CTkFrame(self.tabview.tab("终端"), fg_color="transparent")
        chat_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.chat_var = ctk.StringVar(value="/novel-write ")
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
        self.tabview.add("日志")

        # 工具栏
        toolbar = CTkFrame(self.tabview.tab("日志"), fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        CTkButton(toolbar, text="清空日志", command=self.clear_log,
                  width=100, **btn_ghost()).pack(side="right", padx=5)
        CTkButton(toolbar, text="导出日志", command=self.export_log,
                  width=100, **btn_ghost()).pack(side="right", padx=5)

        # 日志显示区域
        self.log_text = CTkTextbox(self.tabview.tab("日志"),
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
        self.tabview.add("统计")

        # 工具栏
        toolbar = CTkFrame(self.tabview.tab("统计"), fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(10, 5))

        CTkButton(toolbar, text="🔄 刷新统计", command=self.refresh_stats,
                  width=110, **btn_primary()).pack(side="left", padx=5)
        CTkButton(toolbar, text="导出报告", command=self.export_stats,
                  width=110, **btn_primary()).pack(side="left", padx=5)

        # 统计信息显示
        self.stats_text = CTkTextbox(self.tabview.tab("统计"),
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

    # ==================== Claude Code 命令执行 ====================

    def send_message(self):
        """发送消息（统一命令和回复）"""
        message = self.chat_var.get().strip()
        if not message:
            return

        # 清空输入框
        self.chat_var.set("")

        # 显示用户消息
        self._terminal_write(f"\n>>> {message}\n\n")

        # 记录日志
        self._append_log(f"执行命令: {message}", "CMD")

        self._cmd_start_time = time.time()
        self._cmd_running = True
        self._update_running_status("正在处理")

        def _run():
            try:
                cwd = self.project_path if self.project_path else os.getcwd()

                # 记录命令执行前的文件状态
                old_state = self._get_file_state(cwd)

                # 使用 -c 继续最近的对话，添加 < NUL 避免 stdin 警告
                cmd = ["cmd.exe", "/c", "claude", "-p", message, "-c",
                       "--allowedTools", "Write", "Edit", "<", "NUL"]

                self.proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=cwd,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    bufsize=0  # 禁用缓冲，实时输出
                )
                # 使用 os.read 实现实时输出（按块读取，平衡响应性和效率）
                import os
                fd = self.proc.stdout.fileno()
                while True:
                    chunk = os.read(fd, 4096)
                    if not chunk:
                        break
                    try:
                        text = chunk.decode("utf-8", errors="replace")
                    except:
                        text = str(chunk)
                    self.root.after(0, lambda t=text: self._append_terminal(t))
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

    def stop_command(self):
        """终止正在运行的命令"""
        if self.proc and self.proc.poll() is None:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                self._terminal_write("\n[已终止命令]\n")
                self._cmd_running = False
                self.update_status("命令已终止")
            except Exception as e:
                self._terminal_write(f"\n[终止失败: {e}]\n")
        else:
            self._terminal_write("\n[没有正在运行的命令]\n")

    def _terminal_write(self, text):
        """向只读终端写入文本"""
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
        dialog = NewProjectDialog(self.root)
        self.root.wait_window(dialog.top)

        if dialog.result:
            project_name = dialog.result['name']
            project_type = dialog.result['type']
            project_path = dialog.result['path']

            full_path = os.path.join(project_path, project_name)
            self.create_project_structure(full_path, project_name, dialog.result)

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
            }
            self.save_project_config()

            self.project_name_var.set(project_name)
            self.project_type_var.set(f"类型: {project_type} | {dialog.result.get('platform', '')}")
            self.update_status(f"项目 '{project_name}' 创建成功")

            self.chat_var.set(f"/novel-write 新建小说 --name {project_name} --type {project_type}")
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
                self.project_name_var.set(self.project_config.get('name', '未命名'))
                self.project_type_var.set(f"类型: {self.project_config.get('type', '未知')}")
                self.update_status(f"已打开项目: {self.project_config.get('name')}")
                self.load_project_content()

    def save_project(self):
        """保存项目"""
        if not self._check_project():
            return

        self.save_chapter()
        self.save_project_config()
        self.update_status("项目已保存")

    def save_project_config(self):
        """保存项目配置"""
        if self.project_path:
            config_file = os.path.join(self.project_path, 'project.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.project_config, f, ensure_ascii=False, indent=2)

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

    def _load_chapter_list(self):
        """扫描 chapters 目录，动态更新章节选择器"""
        chapters_dir = os.path.join(self.project_path, 'chapters')
        if not os.path.exists(chapters_dir):
            return
        files = sorted([f for f in os.listdir(chapters_dir)
                        if f.startswith('ch') and f.endswith('.md')])
        chapters = [f"第{f[2:5]}章" for f in files]
        if chapters:
            self.chapter_menu.configure(values=chapters)
            self.chapter_var.set(chapters[0])
            self._on_chapter_selected(chapters[0])
        else:
            self.chapter_menu.configure(values=["暂无章节"])
            self.chapter_var.set("暂无章节")

    def _on_chapter_selected(self, choice):
        """切换章节时自动加载内容"""
        if not self.project_path or choice == "暂无章节":
            return
        num = choice.replace('第', '').replace('章', '')
        path = os.path.join(self.project_path, 'chapters', f'ch{num}.md')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.writing_text.delete("1.0", "end")
            self.writing_text.insert("1.0", content)
            self.update_word_count()

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
        self.chat_var.set("/novel-write 生成总大纲")
        self.send_message()
        self.tabview.set("终端")

    def generate_volume_outline(self):
        """生成卷大纲"""
        if not self._check_project():
            return
        dialog = CTkInputDialog(text="请输入卷数:", title="生成卷大纲")
        volume = dialog.get_input()
        if volume and volume.isdigit():
            self.chat_var.set(f"/novel-write 生成第{volume}卷大纲")
            self.send_message()
            self.tabview.set("终端")

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
            self.chat_var.set(f"/novel-write 写第{chapter}章")
            self.send_message()
            self.tabview.set("终端")

    def continue_writing(self):
        """续写"""
        if not self._check_project():
            return
        self.chat_var.set("/novel-write 继续写")
        self.send_message()
        self.tabview.set("终端")

    def plan_chapter(self):
        """规划章节"""
        if not self._check_project():
            return
        dialog = CTkInputDialog(text="请输入章节号:", title="规划章节")
        chapter = dialog.get_input()
        if chapter and chapter.isdigit():
            self.chat_var.set(f"/novel-write 规划第{chapter}章")
            self.send_message()
            self.tabview.set("终端")

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
        self.update_status(f"章节 {chapter_name} 已保存")

    # ==================== 人物功能 ====================

    def view_characters(self):
        """查看人物管理"""
        if not self._check_project():
            return
        dialog = CharacterManagerDialog(self.root, self.project_path)
        self.root.wait_window(dialog.top)

    # ==================== 世界观功能 ====================

    def edit_worldbuilding(self):
        """编辑世界观"""
        if not self._check_project():
            return
        settings_file = os.path.join(self.project_path, 'worldbuilding', 'settings.md')
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
            dialog = EditDialog(self.root, "世界观设定", content)
            self.root.wait_window(dialog.top)
            if dialog.result:
                with open(settings_file, 'w', encoding='utf-8') as f:
                    f.write(dialog.result)
                self.update_status("世界观设定已更新")

    # ==================== 风格配置 ====================

    def style_settings(self):
        """风格配置"""
        if not self._check_project():
            return
        style_file = os.path.join(self.project_path, 'style', 'style-config.md')
        if os.path.exists(style_file):
            with open(style_file, 'r', encoding='utf-8') as f:
                content = f.read()
            dialog = EditDialog(self.root, "风格配置", content)
            self.root.wait_window(dialog.top)
            if dialog.result:
                with open(style_file, 'w', encoding='utf-8') as f:
                    f.write(dialog.result)
                self.update_status("风格配置已更新")

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
        self.tabview.set("统计")

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
        self.chat_var.set("/novel-write 审稿")
        self.send_message()
        self.tabview.set("终端")

    def polish_chapter(self):
        """润色"""
        if not self._check_project():
            return
        self.chat_var.set("/novel-write 润色")
        self.send_message()
        self.tabview.set("终端")

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

    def __init__(self, parent):
        self.top = CTkToplevel(parent)
        self.top.title("新建项目")
        self.top.geometry("480x650")
        self.top.transient(parent)
        self.top.grab_set()

        self.result = None

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

        # 项目类型
        CTkLabel(scroll, text="项目类型:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.type_var = ctk.StringVar(value="玄幻/仙侠")
        CTkOptionMenu(scroll, values=["玄幻/仙侠", "都市/现实", "科幻/未来", "历史/架空", "悬疑/推理", "言情/耽美"],
                      variable=self.type_var, width=400, height=BTN_HEIGHT_MD).pack(padx=20, pady=(0, 8))

        # 目标平台
        CTkLabel(scroll, text="目标平台:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.platform_var = ctk.StringVar(value="番茄小说")
        CTkOptionMenu(scroll, values=["番茄小说", "起点中文网", "晋江文学城", "纵横中文网", "飞卢小说", "其他"],
                      variable=self.platform_var, width=400, height=BTN_HEIGHT_MD).pack(padx=20, pady=(0, 8))

        # 叙事视角
        CTkLabel(scroll, text="叙事视角:", text_color=COLORS["text_primary"]).pack(anchor="w", padx=20)
        self.pov_var = ctk.StringVar(value="第三人称限制")
        CTkOptionMenu(scroll, values=["第三人称限制", "第三人称全知", "第一人称", "多视角切换"],
                      variable=self.pov_var, width=400, height=BTN_HEIGHT_MD).pack(padx=20, pady=(0, 8))

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
                      variable=self.audience_var, width=400, height=BTN_HEIGHT_MD).pack(padx=20, pady=(0, 8))

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
            'path': os.getcwd(),
        }
        self.top.destroy()

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
    # 确保 Skill 文件存在
    ensure_skill_files()

    app = ModernNovelWriterApp()
    app.run()


if __name__ == '__main__':
    main()
