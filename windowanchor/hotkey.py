"""全局热键 v1.6：独立线程注册 RegisterHotKey，支持自定义热键，优化响应速度。"""
import threading
import ctypes
from ctypes import wintypes
import win32con
import win32gui
import win32api
from PySide6.QtCore import QObject, Signal

WM_HOTKEY = 0x0312
HOTKEY_ID = 1
WM_REREGISTER = WM_HOTKEY + 1  # 自定义消息：重新注册热键

MODIFIER_MAP = {
    "Ctrl": win32con.MOD_CONTROL,
    "Alt": win32con.MOD_ALT,
    "Shift": win32con.MOD_SHIFT,
    "Win": win32con.MOD_WIN,
}

VK_NAMES = {
    0x20: "Space", 0x09: "Tab", 0x0D: "Enter", 0x1B: "Esc",
    0x2E: "Delete", 0x2C: "PrintScreen",
    0xBC: ",", 0xBE: ".", 0xBA: ";", 0xDE: "'",
    0xDB: "[", 0xDD: "]", 0xDC: "\\", 0xBF: "/", 0xC0: "`",
    0xBD: "-", 0xBB: "=",
}
for i in range(1, 13):
    VK_NAMES[0x6F + i] = f"F{i}"
for i in range(10):
    VK_NAMES[0x30 + i] = str(i)
for i in range(26):
    VK_NAMES[0x41 + i] = chr(0x41 + i)


def vk_to_name(vk: int) -> str:
    return VK_NAMES.get(vk, f"VK({vk})")


def display_hotkey(modifiers: int, vk: int) -> str:
    parts = []
    if modifiers & win32con.MOD_CONTROL:
        parts.append("Ctrl")
    if modifiers & win32con.MOD_ALT:
        parts.append("Alt")
    if modifiers & win32con.MOD_SHIFT:
        parts.append("Shift")
    if modifiers & win32con.MOD_WIN:
        parts.append("Win")
    parts.append(vk_to_name(vk))
    return "+".join(parts)


class HotkeyThread(QObject):
    """在独立线程中注册并监听全局热键。v1.6 优化：更快的响应、更稳定的重注册。"""

    triggered = Signal()
    error = Signal(str)

    def __init__(self, parent=None, name="main"):
        super().__init__(parent)
        self._name = name
        self._thread = None
        self._running = threading.Event()
        self._msg_thread_id = None
        self._hwnd = None
        self._class_atom = None
        self._hinst = None
        self._modifiers = win32con.MOD_CONTROL | win32con.MOD_SHIFT
        self._vk = win32con.VK_SPACE
        self._need_reregister = threading.Event()
        self._started = False

    def set_hotkey(self, modifiers: int, vk: int):
        """设置新的热键，在线程中重新注册。"""
        self._modifiers = modifiers
        self._vk = vk
        if self._started and self._thread and self._thread.is_alive():
            self._need_reregister.set()
            if self._msg_thread_id:
                ctypes.windll.user32.PostThreadMessageW(
                    self._msg_thread_id, WM_REREGISTER, 0, 0,
                )

    def start(self):
        """启动热键监听线程。"""
        if self._thread and self._thread.is_alive():
            return
        self._running.set()
        self._started = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _register_hotkey(self) -> bool:
        """注册当前热键。"""
        if not self._hwnd:
            return False
        ctypes.windll.user32.UnregisterHotKey(self._hwnd, HOTKEY_ID)
        ok = ctypes.windll.user32.RegisterHotKey(
            self._hwnd, HOTKEY_ID, self._modifiers, self._vk,
        )
        if not ok:
            err = ctypes.get_last_error()
            self.error.emit(
                f"注册热键 {display_hotkey(self._modifiers, self._vk)} 失败"
                f"（错误码 {err}，可能被其他程序占用）。"
            )
            return False
        return True

    def _loop(self):
        """热键线程主循环。v1.6 优化：使用更轻量的消息循环。"""
        self._msg_thread_id = win32api.GetCurrentThreadId()
        self._hinst = win32api.GetModuleHandle(None)

        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc
        wc.lpszClassName = f"WindowAnchorHotkey_{self._name}_v16"
        wc.hInstance = self._hinst
        try:
            self._class_atom = win32gui.RegisterClass(wc)
        except Exception as e:
            self.error.emit(f"注册窗口类失败：{e}")
            self._running.clear()
            return

        self._hwnd = win32gui.CreateWindowEx(
            0, self._class_atom, f"WindowAnchorHotkey_{self._name}", 0, 0, 0, 0, 0, 0, 0,
            self._hinst, None,
        )
        self._register_hotkey()

        # 使用 GetMessage 循环，响应更快
        msg = wintypes.MSG()
        while self._running.is_set():
            # 阻塞等待消息（超时500ms，以便检查 running 状态）
            result = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
            if result == -1 or result == 0:
                break
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                self.triggered.emit()
            elif msg.message == WM_REREGISTER:
                if self._need_reregister.is_set():
                    self._need_reregister.clear()
                    self._register_hotkey()
            else:
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        # 清理
        ctypes.windll.user32.UnregisterHotKey(self._hwnd, HOTKEY_ID)
        if win32gui.IsWindow(self._hwnd):
            win32gui.DestroyWindow(self._hwnd)
        win32gui.UnregisterClass(self._class_atom, self._hinst)

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """窗口过程（备用，主要消息在循环中处理）。"""
        if msg == WM_HOTKEY and wparam == HOTKEY_ID:
            self.triggered.emit()
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def stop(self):
        """停止热键监听。"""
        self._running.clear()
        self._started = False
        if self._msg_thread_id:
            ctypes.windll.user32.PostThreadMessageW(
                self._msg_thread_id, win32con.WM_QUIT, 0, 0,
            )
        if self._thread:
            self._thread.join(timeout=2)
        self._thread = None
