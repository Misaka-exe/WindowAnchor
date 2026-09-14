"""老板键 / 一键隐藏管理器。

功能：
- 按全局热键，瞬间隐藏所有置顶窗口
- 再按一次恢复
- 可设置隐藏时同时静音
- 隐藏期间托盘图标特殊标记
"""
from PySide6.QtCore import QObject, Signal
from . import winapi


class BossKeyManager(QObject):
    """管理老板键功能。"""

    boss_key_toggled = Signal(bool)  # is_hidden

    def __init__(self, config, pin_manager, parent=None):
        super().__init__(parent)
        self._config = config
        self._pin_manager = pin_manager
        self._is_hidden = False
        self._hidden_windows = {}  # hwnd -> state dict

    def toggle(self):
        """切换老板键状态。"""
        if self._is_hidden:
            self.restore()
        else:
            self.hide()
        return self._is_hidden

    def hide(self):
        """隐藏所有置顶窗口。"""
        if self._is_hidden:
            return

        pinned = self._pin_manager.list_pinned()
        muted_pids = []
        for hwnd, title in pinned:
            if not winapi.is_window(hwnd):
                continue

            # 获取窗口对应的进程 ID
            pid = winapi.get_window_pid(hwnd)

            # 保存窗口状态
            state = {
                "rect": winapi.get_window_rect(hwnd),
                "is_topmost": self._pin_manager.is_pinned(hwnd),
                "opacity": self._pin_manager.get_opacity(hwnd),
                "is_click_through": self._pin_manager.is_click_through(hwnd),
                "is_visible": winapi.is_window_visible(hwnd),
                "pid": pid,
            }
            self._hidden_windows[hwnd] = state

            # 隐藏窗口
            winapi.hide_window(hwnd)

            # 可选：静音该窗口对应的应用
            if self._config.get("boss_key_mute", False):
                if pid and pid not in muted_pids:
                    try:
                        winapi.mute_process_audio(pid, True)
                        muted_pids.append(pid)
                    except Exception:
                        pass

        self._is_hidden = True
        self.boss_key_toggled.emit(True)

    def restore(self):
        """恢复所有隐藏的窗口。"""
        if not self._is_hidden:
            return

        for hwnd, state in self._hidden_windows.items():
            if not winapi.is_window(hwnd):
                continue

            # 恢复窗口可见性
            if state.get("is_visible", True):
                winapi.show_window(hwnd)

            # 恢复位置
            rect = state.get("rect")
            if rect:
                left, top, right, bottom = rect
                winapi.move_window(hwnd, left, top, right - left, bottom - top)

            # 恢复置顶状态
            if state.get("is_topmost"):
                self._pin_manager.pin(hwnd)

            # 恢复透明度
            opacity = state.get("opacity", 100)
            if opacity and opacity != 100:
                self._pin_manager.set_opacity(hwnd, opacity)

            # 恢复点击穿透
            if state.get("is_click_through"):
                self._pin_manager.set_click_through(hwnd, True)

        # 取消静音（恢复每个被隐藏窗口对应的应用音频）
        if self._config.get("boss_key_mute", False):
            muted_pids = set()
            for hwnd, state in self._hidden_windows.items():
                pid = state.get("pid", 0)
                if pid and pid not in muted_pids:
                    try:
                        winapi.mute_process_audio(pid, False)
                        muted_pids.add(pid)
                    except Exception:
                        pass

        self._hidden_windows.clear()

        self._is_hidden = False
        self.boss_key_toggled.emit(False)

    @property
    def is_hidden(self):
        return self._is_hidden

    def get_hidden_count(self):
        """获取当前隐藏的窗口数量。"""
        return len(self._hidden_windows)
