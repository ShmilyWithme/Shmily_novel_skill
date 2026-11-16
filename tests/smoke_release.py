"""Launch the actual Windows EXE with temporary settings and close its visible window."""

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from novel_writer_gui import APP_VERSION  # noqa: E402
from build_release import APP_NAME  # noqa: E402


def main():
    if sys.platform != "win32":
        raise SystemExit("Release smoke test requires Windows")
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

    def windows():
        found = {}

        @callback_type
        def callback(hwnd, _):
            length = user32.GetWindowTextLengthW(hwnd)
            if length and user32.IsWindowVisible(hwnd):
                title = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, title, length + 1)
                found[hwnd] = title.value
            return True

        user32.EnumWindows(callback, 0)
        return found

    executable = ROOT / "dist" / f"{APP_NAME}.exe"
    previous = set(windows())
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env["APPDATA"] = tmp
        proc = subprocess.Popen([str(executable)], env=env, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            deadline = time.monotonic() + 30
            hwnd = None
            while time.monotonic() < deadline:
                hwnd = next((handle for handle, title in windows().items()
                             if handle not in previous and title == f"{APP_NAME} {APP_VERSION}"), None)
                if hwnd:
                    break
                if proc.poll() is not None:
                    raise RuntimeError("EXE exited before showing its main window")
                time.sleep(0.1)
            if hwnd is None:
                raise RuntimeError("Visible EXE main window was not detected")
            user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
            code = proc.wait(timeout=15)
            if code:
                raise RuntimeError(f"EXE exited with code {code}")
            print(f"Packaged v{APP_VERSION} main window opened and exited cleanly.")
        finally:
            if proc.poll() is None:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                               capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)


if __name__ == "__main__":
    main()
