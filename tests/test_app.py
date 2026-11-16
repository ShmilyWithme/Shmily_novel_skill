import json
import os
from pathlib import Path
import queue
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import novel_writer_gui as gui


class Text:
    def __init__(self, value=""):
        self.value = value

    def get(self, *args):
        return self.value

    def set(self, value):
        self.value = value

    def delete(self, *args):
        self.value = ""

    def insert(self, _, value):
        self.value += value


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = gui.ModernNovelWriterApp.__new__(gui.ModernNovelWriterApp)
        a = self.app
        a.root = Mock()
        a.project_path = str(self.root)
        a.project_config = {"name": "测试", "target_words": 1000}
        a._cmd_running = False
        a._closing = False
        a._cancel_command = threading.Event()
        a._ui_events = queue.Queue()
        a._loaded_outline_path = None
        a._loaded_outline_choice = "总大纲"
        a._loaded_outline_content = ""
        a._loaded_chapter_num = None
        a._loaded_chapter_content = ""
        a._loaded_chapter_path = None
        a._chapter_scan_cache = {}
        a.outline_var = Text("总大纲")
        a.outline_text = Text()
        a.writing_text = Text()
        a.chapter_var = Text("暂无章节")
        a.chat_var = Text("test task")
        a.outline_menu = Mock()
        a.refresh_dashboard = Mock()
        a.update_status = Mock()
        a.update_word_count = Mock()
        a.update_chapter_nav_state = Mock()
        a._terminal_write = Mock()
        for method in ("showwarning", "showerror", "showinfo", "askyesno", "askyesnocancel"):
            patcher = patch.object(gui.messagebox, method)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write(self, path, content):
        target = self.root / path
        gui.atomic_write_text(target, content)
        return target

    def test_volume_save_never_overwrites_master(self):
        master = self.write("outline/master-outline.md", "总纲")
        for filename in ("vol2-outline.md", "volume-3-outline.md"):
            with self.subTest(filename=filename):
                path = self.write("outline/" + filename, "卷纲")
                number = "2" if filename.startswith("vol2") else "3"
                self.app._on_outline_selected(f"第{number}卷", confirm_switch=False)
                self.app.outline_text.value = "修改卷纲"
                self.assertTrue(self.app.save_outline())
                self.assertEqual(gui.read_text(path), "修改卷纲")
                self.assertEqual(gui.read_text(master), "总纲")

    def test_outline_refresh_cancel_preserves_unsaved_edit(self):
        self.write("outline/master-outline.md", "原稿")
        self.app.load_outline()
        self.app.outline_text.value = "未保存"
        gui.messagebox.askyesnocancel.return_value = None
        self.app.load_outline()
        self.assertEqual(self.app.outline_text.value, "未保存")

    def test_outline_switch_saves_original_selection(self):
        master = self.write("outline/master-outline.md", "总纲")
        volume = self.write("outline/vol1-outline.md", "卷纲")
        self.app.load_outline()
        self.app.outline_text.value = "修改总纲"
        self.app.outline_var.set("第1卷")
        gui.messagebox.askyesnocancel.return_value = True
        self.assertTrue(self.app._on_outline_selected("第1卷"))
        self.assertEqual(gui.read_text(master), "修改总纲")
        self.assertEqual(gui.read_text(volume), "卷纲")

    def test_outline_menu_numeric_sort_and_alias(self):
        for name in ("vol10", "vol2", "volume-1", "volume-2"):
            self.write(f"outline/{name}-outline.md", "outline")
        self.app.load_outline()
        self.app.outline_menu.configure.assert_called_with(values=["总大纲", "第1卷", "第2卷", "第10卷"])

    def test_external_change_refusal_preserves_disk_and_editor(self):
        path = self.write("outline/master-outline.md", "原稿")
        self.app.load_outline()
        self.app.outline_text.value = "编辑中"
        path.write_text("外部修改", encoding="utf-8")
        gui.messagebox.askyesno.return_value = False
        self.assertFalse(self.app.save_outline())
        self.assertEqual(gui.read_text(path), "外部修改")
        self.assertEqual(self.app.outline_text.value, "编辑中")

    def test_missing_outline_does_not_persist_placeholder(self):
        self.app.load_outline()
        self.assertEqual(self.app.outline_text.value, "")
        self.assertFalse(self.app._is_outline_dirty())
        self.app.outline_text.value = "新总纲"
        self.assertTrue(self.app.save_outline())
        self.assertEqual(gui.read_text(self.root / "outline/master-outline.md"), "新总纲")

    def test_invalid_chapter_encoding_keeps_current_document(self):
        path = self.write("chapters/ch002.md", "ok")
        path.write_bytes(b"\xff\xff")
        self.app._loaded_chapter_num = 1
        self.app._loaded_chapter_path = "old.md"
        self.app._loaded_chapter_content = "旧稿"
        self.app.writing_text.value = "旧稿"
        self.app.chapter_var.set("第2章")
        self.assertFalse(self.app._on_chapter_selected("第2章"))
        self.assertEqual(self.app.writing_text.value, "旧稿")
        self.assertEqual(self.app.chapter_var.get(), "第1章")

    def test_save_chapter_failure_keeps_dirty_state(self):
        self.write("chapters/ch001.md", "原稿")
        self.app.chapter_var.set("第1章")
        self.app._on_chapter_selected("第1章")
        self.app.writing_text.value = "新稿"
        with patch.object(gui, "atomic_write_text", side_effect=PermissionError("read only")):
            self.assertFalse(self.app.save_chapter())
        self.assertTrue(self.app._is_current_chapter_dirty())

    def test_scan_deduplicates_chapter_numbers_and_refreshes_counts(self):
        self.write("chapters/ch1.md", "甲")
        path = self.write("chapters/ch001.md", "甲乙<!-- 注释不计入字数 -->")
        self.write("chapters/ch010.md", "丙")
        chapters = self.app.scan_chapters()
        self.assertEqual([x["number"] for x in chapters], [1, 10])
        self.assertEqual(chapters[0]["words"], 2)
        path.write_text("甲乙丙丁", encoding="utf-8")
        self.assertEqual(self.app.scan_chapters()[0]["words"], 4)

    def test_export_saves_editor_and_strips_metadata(self):
        self.write("chapters/ch001.md", "旧稿<!-- 隐藏 -->")
        self.app.chapter_var.set("第1章")
        self.app._on_chapter_selected("第1章")
        self.app.writing_text.value = "新稿<!-- 隐藏 -->"
        self.app.export_novel()
        export = next((self.root / "export").glob("*.md"))
        self.assertIn("新稿", gui.read_text(export))
        self.assertNotIn("隐藏", gui.read_text(export))

    def test_export_failure_keeps_previous_export(self):
        path = self.write("chapters/ch001.md", "旧稿")
        export = self.write("export/测试_全文.md", "上次导出")
        path.write_bytes(b"\xff")
        self.app.export_novel()
        self.assertEqual(gui.read_text(export), "上次导出")
        gui.messagebox.showerror.assert_called_once()

    def test_invalid_project_open_keeps_old_project(self):
        self.write("broken/project.json", '{"target_words": "bad"}')
        with patch.object(gui.filedialog, "askdirectory", return_value=str(self.root / "broken")):
            self.app.open_project()
        self.assertEqual(self.app.project_path, str(self.root))
        gui.messagebox.showerror.assert_called_once()

    def test_close_cancel_keeps_window_alive(self):
        self.app._confirm_document_switch = Mock(return_value=False)
        self.app.on_closing()
        self.assertFalse(self.app._closing)
        self.app.root.destroy.assert_not_called()

    def test_stop_before_process_exists_sets_cancellation(self):
        self.app._cmd_running = True
        self.app.proc = None
        self.app.stop_command()
        self.assertTrue(self.app._cancel_command.is_set())

    def test_cancelled_preflight_never_launches_cli(self):
        class ImmediateThread:
            def __init__(self, target, **kwargs):
                self.target = target

            def start(self):
                self.target()

        self.app.proc = None
        self.app.set_document_editors_enabled = Mock()
        self.app._append_log = Mock()
        self.app._update_running_status = Mock()
        self.app.preflight_ai_command = lambda _cwd: self.app._cancel_command.set()
        with patch.object(gui, "ensure_skill_files", return_value=True), \
                patch.object(gui.threading, "Thread", ImmediateThread), \
                patch.object(gui.subprocess, "Popen") as popen:
            self.app.send_message()
        popen.assert_not_called()
        callback, args = self.app._ui_events.get_nowait()
        self.assertEqual(callback, self.app._command_done)
        self.assertEqual(args[0], -1)

    def test_utf8_split_across_output_chunks_is_decoded_once(self):
        self.app._last_command_output = ""
        proc = Mock()
        with patch.object(gui.os, "read", side_effect=[b"\xe4", b"\xb8\xad", b""]):
            self.app.read_raw_process_output(proc)
        self.assertEqual(self.app._last_command_output, "中")

    def test_empty_document_can_be_saved_and_cancel_does_not_create_file(self):
        path = self.write("notes.md", "原稿")
        with patch.object(gui, "EditDialog", return_value=Mock(result="")):
            self.assertTrue(gui.edit_document(Mock(), path, "notes"))
        self.assertEqual(gui.read_text(path), "")
        missing = self.root / "missing.md"
        with patch.object(gui, "EditDialog", return_value=Mock(result=None)):
            self.assertFalse(gui.edit_document(Mock(), missing, "notes", "default"))
        self.assertFalse(missing.exists())

    def test_edit_save_failure_keeps_input_for_retry(self):
        path = self.write("notes.md", "原稿")
        real_write = gui.atomic_write_text
        calls = []

        def fail_once(target, content):
            calls.append(content)
            if len(calls) == 1:
                raise PermissionError("locked")
            real_write(target, content)

        with patch.object(gui, "EditDialog", return_value=Mock(result="新稿")) as dialog, \
                patch.object(gui, "atomic_write_text", side_effect=fail_once):
            self.assertTrue(gui.edit_document(Mock(), path, "notes"))
        self.assertEqual(dialog.call_count, 2)
        self.assertEqual(dialog.call_args.args[-1], "新稿")
        self.assertEqual(gui.read_text(path), "新稿")

    def test_background_ui_events_execute_only_when_drained(self):
        callback = Mock()
        thread = threading.Thread(target=self.app._post_ui, args=(callback, "result"))
        thread.start()
        thread.join(timeout=2)
        callback.assert_not_called()
        self.app.root.after.assert_not_called()
        self.app._drain_ui_events()
        callback.assert_called_once_with("result")

    def test_prompt_is_stdin_not_shell_argument(self):
        message = 'write & echo secret > bad.txt $(test)'
        command, prompt = self.app.build_ai_command(message)
        self.assertNotIn(message, command)
        self.assertIn(message, prompt)
        self.assertIn("workspace-write", command)
        self.assertEqual(command[-1], "-")

    def test_review_targets_selected_chapter(self):
        self.app._loaded_chapter_num = 12
        self.app.send_message = Mock()
        self.app.tabview = Mock()
        self.app.review_chapter()
        self.assertIn("第12章", self.app.chat_var.get())

    def test_atomic_replace_failure_keeps_old_file_and_cleans_temp(self):
        path = self.write("data.md", "原文件")
        with patch.object(gui.os, "replace", side_effect=PermissionError("locked")):
            with self.assertRaises(PermissionError):
                gui.atomic_write_text(path, "新文件")
        self.assertEqual(gui.read_text(path), "原文件")
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_project_config_accepts_bom_and_normalizes_legacy_numbers(self):
        path = self.write("project.json", '\ufeff{"name":"测试","target_words":"1000"}')
        config = gui.load_project_config(path)
        self.assertEqual(config["target_words"], 1000)
        self.assertEqual(config["target_chapters"], 0)

    def test_project_config_rejects_malformed_types(self):
        for data in ([], {"target_words": True}, {"target_words": -1}, {"target_words": []},
                     {"target_chapters": "invalid"}, {"name": []}):
            with self.subTest(data=data):
                path = self.write("project.json", json.dumps(data))
                with self.assertRaises(ValueError):
                    gui.load_project_config(path)

    def test_skill_repair_preserves_customized_files(self):
        self.assertTrue(gui.ensure_skill_files(self.root))
        skill = self.root / ".agents/skills/novel-write"
        custom = skill / "SKILL.md"
        custom.write_text("custom instructions", encoding="utf-8")
        missing = skill / "modules/utils/review.md"
        missing.unlink()
        self.assertIn(str(missing), gui.get_missing_skill_paths(self.root))
        self.assertTrue(gui.ensure_skill_files(self.root))
        self.assertEqual(gui.read_text(custom), "custom instructions")
        self.assertTrue(missing.exists())

    def test_project_creation_failure_leaves_no_partial_project(self):
        target = self.root / "new-project"
        with patch.object(self.app, "create_initial_files", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.app.create_project_structure(target, "test", {})
        self.assertFalse(target.exists())
        self.assertEqual(list(self.root.glob(".novel-project-*")), [])

    def test_project_creation_produces_openable_project_without_cli(self):
        target = self.root / "new-project"
        self.app.create_project_structure(target, "test", {"target_words": 1000, "target_chapters": 10})
        config = gui.load_project_config(target / "project.json")
        self.assertEqual(config["target_words"], 1000)
        self.assertFalse(gui.get_missing_skill_paths(target))
        with self.assertRaises(FileExistsError):
            self.app.create_project_structure(target, "test", {})
        self.assertEqual(gui.load_project_config(target / "project.json"), config)

    def test_character_paths_stay_inside_project(self):
        manager = gui.CharacterManagerDialog.__new__(gui.CharacterManagerDialog)
        manager.project_path = str(self.root)
        manager.top = Mock()
        for name in ("../outside", "CON", "a/b", "a\\b", "NUL.txt", "index"):
            self.assertIsNone(manager._character_file(name, show_error=False))
        self.assertEqual(Path(manager._character_file("林墨")).resolve(),
                         (self.root / "characters/林墨.md").resolve())


if __name__ == "__main__":
    unittest.main()
