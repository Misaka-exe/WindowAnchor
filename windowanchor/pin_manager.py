"""置顶管理器 v1.6：维护已置顶窗口集合，支持透明度、点击穿透、层级排序、自动恢复。"""
from PySide6.QtCore import QObject
from . import winapi


class PinManager(QObject):
    """管理所有已置顶窗口。v1.6 新增：点击穿透、层级排序、置顶状态恢复。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # {hwnd: {"title": str, "opacity": int, "process": str, "click_through": bool}}
        self._pinned = {}
        # 透明度记忆：{process_name: opacity}
        self._opacity_memory = {}
        # 层级顺序列表（按Z-order从底到顶排序）

    def toggle(self, hwnd: int, default_opacity: int = 100) -> bool:
        """切换窗口置顶状态。返回切换后是否置顶。"""
        if not winapi.is_window(hwnd):
            return False
        if hwnd in self._pinned:
            self.unpin(hwnd)
            return False
        else:
            self.pin(hwnd, default_opacity)
            return True

    def pin(self, hwnd: int, opacity: int = 100):
        """置顶窗口，可指定透明度。"""
        if not winapi.is_window(hwnd):
            return
        process = winapi.get_process_name(hwnd)
        if process and process in self._opacity_memory:
            opacity = self._opacity_memory[process]
        winapi.set_topmost(hwnd, True)
        if opacity < 100:
            winapi.set_opacity(hwnd, opacity)
        self._pinned[hwnd] = {
            "title": winapi.get_window_title(hwnd) or "未命名窗口",
            "opacity": opacity,
            "process": process,
            "click_through": False,
        }

    def unpin(self, hwnd: int):
        """取消窗口置顶，恢复透明度和点击穿透。"""
        if winapi.is_window(hwnd):
            # 先取消点击穿透
            if hwnd in self._pinned and self._pinned[hwnd].get("click_through"):
                winapi.set_click_through(hwnd, False)
            winapi.set_topmost(hwnd, False)
            winapi.reset_opacity(hwnd)
        self._pinned.pop(hwnd, None)

    def unpin_all(self):
        """取消所有窗口的置顶。"""
        for hwnd in list(self._pinned.keys()):
            self.unpin(hwnd)

    # ----------------------------------------------------------
    # 透明度
    # ----------------------------------------------------------

    def set_opacity(self, hwnd: int, opacity: int):
        """设置已置顶窗口的透明度，保持点击穿透状态。"""
        if not winapi.is_window(hwnd):
            return
        opacity = max(10, min(100, opacity))
        # 检查当前是否处于点击穿透状态
        was_click_through = (hwnd in self._pinned and self._pinned[hwnd].get("click_through"))
        current_opacity = self.get_opacity(hwnd)
        # 设置透明度（不会影响 WS_EX_TRANSPARENT 标志）
        winapi.set_opacity(hwnd, opacity)
        # 如果之前处于点击穿透状态，重新应用穿透（确保共存）
        if was_click_through:
            winapi.set_click_through(hwnd, True, opacity)
        if hwnd in self._pinned:
            self._pinned[hwnd]["opacity"] = opacity
            process = self._pinned[hwnd].get("process")
            if process:
                self._opacity_memory[process] = opacity

    def get_opacity(self, hwnd: int) -> int:
        """获取已置顶窗口的透明度。"""
        if hwnd in self._pinned:
            return self._pinned[hwnd]["opacity"]
        return winapi.get_opacity(hwnd)

    # ----------------------------------------------------------
    # 点击穿透
    # ----------------------------------------------------------

    def set_click_through(self, hwnd: int, enabled: bool):
        """设置窗口点击穿透，同时保持透明度。
        开启穿透时自动置于最顶层（最高优先级）。"""
        if not winapi.is_window(hwnd):
            return
        # 获取当前透明度，传入 set_click_through 确保两者共存
        current_opacity = self.get_opacity(hwnd)
        winapi.set_click_through(hwnd, enabled, current_opacity)
        if hwnd in self._pinned:
            self._pinned[hwnd]["click_through"] = enabled
        if enabled:
            # 开启穿透时自动置于最顶层
            try:
                winapi.bring_to_front(hwnd)
            except Exception:
                pass

    def is_click_through(self, hwnd: int) -> bool:
        """判断窗口是否处于点击穿透状态。"""
        if hwnd in self._pinned:
            return self._pinned[hwnd].get("click_through", False)
        return False

    def toggle_click_through(self, hwnd: int) -> bool:
        """切换点击穿透状态，返回切换后的状态。"""
        current = self.is_click_through(hwnd)
        self.set_click_through(hwnd, not current)
        return not current


    # ----------------------------------------------------------
    # 状态恢复（修复"点击其他页面失去置顶"的bug）
    # ----------------------------------------------------------

    def restore_topmost(self) -> int:
        """检查所有已置顶窗口，恢复丢失的 TOPMOST 状态，并强制保持用户设定的层级顺序。
        返回恢复的窗口数量。
        """
        # 先清理失效窗口
        for hwnd in list(self._pinned.keys()):
            if not winapi.is_window(hwnd):
                self._pinned.pop(hwnd, None)

        # 收集需要恢复的窗口
        need_restore = []
        for hwnd in list(self._pinned.keys()):
            if not winapi.is_topmost(hwnd):
                need_restore.append(hwnd)

        # 恢复失去 TOPMOST 状态的窗口
        restored = 0
        for hwnd in need_restore:
            try:
                winapi.set_topmost(hwnd, True)
                # 恢复透明度
                opacity = self._pinned[hwnd].get("opacity", 100)
                if opacity < 100:
                    winapi.set_opacity(hwnd, opacity)
                # 恢复点击穿透
                if self._pinned[hwnd].get("click_through"):
                    winapi.set_click_through(hwnd, True, opacity)
                restored += 1
            except Exception:
                pass

        # 确保点击穿透窗口优先级最高（置于最顶层）
        click_through_windows = []
        normal_windows = []
        for hwnd in list(self._pinned.keys()):
            if winapi.is_window(hwnd) and winapi.is_topmost(hwnd):
                if self._pinned[hwnd].get("click_through"):
                    click_through_windows.append(hwnd)
                else:
                    normal_windows.append(hwnd)
        
        # 先放普通窗口，再放穿透窗口（穿透窗口最后放，在最上面）
        for hwnd in normal_windows + click_through_windows:
            try:
                win32gui.SetWindowPos(
                    hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
                )
            except Exception:
                pass

        return restored

    # ----------------------------------------------------------
    # 查询
    # ----------------------------------------------------------

    def is_pinned(self, hwnd: int) -> bool:
        return hwnd in self._pinned

    def list_pinned(self) -> list:
        """返回已置顶窗口列表 [(hwnd, title), ...]，自动清理失效窗口。"""
        valid = []
        for hwnd in list(self._pinned.keys()):
            if winapi.is_window(hwnd):
                title = winapi.get_window_title(hwnd) or self._pinned[hwnd]["title"]
                self._pinned[hwnd]["title"] = title
                valid.append((hwnd, title))
            else:
                self._pinned.pop(hwnd, None)
        return valid

    def count(self) -> int:
        return len(self.list_pinned())

    def cleanup_invalid(self):
        self.list_pinned()
