import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import novel_writer_gui as gui


@unittest.skipUnless(sys.platform == "win32" or os.environ.get("DISPLAY"), "Tk requires a display")
class GuiSmokeTests(unittest.TestCase):
    def test_window_project_navigation_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            with patch.object(gui, "get_app_settings_path", return_value=str(path / "settings.json")):
                app = gui.ModernNovelWriterApp()
            try:
                app.root.withdraw()
                app.root.update()
                gui.atomic_write_text(path / "chapters/ch001.md", "# 第1章\n正文")
                gui.atomic_write_text(path / "outline/vol1-outline.md", "第一卷")
                app.project_path = tmp
                app.project_config = {"name": "软件测试", "target_words": 10000}
                app.load_project_content()
                self.assertEqual(app._loaded_chapter_num, 1)
                self.assertTrue(app._on_outline_selected("第1卷"))
                self.assertEqual(Path(app._loaded_outline_path).name, "vol1-outline.md")
                app._terminal_write("测试输出" * 100000)
                self.assertLessEqual(len(app.terminal_text.get("1.0", "end-1c")), 300000)
                app._append_log("smoke")
                app._post_ui(app.update_status, "队列已处理")
                app._drain_ui_events()
                self.assertEqual(app.status_var.get(), "队列已处理")
                app.root.update()
            finally:
                app._closing = True
                app.root.destroy()


if __name__ == "__main__":
    unittest.main()
