"""窗口靠边自动收起管理器（类似QQ停靠）。

功能：
- 窗口拖到屏幕边缘并停止移动，自动收起为一条细线
- 鼠标移过去自动展开，移开自动收起
- 可设置收起宽度、触发阈值
- 防误触发：窗口必须停止移动 300ms 才会收起
- 每个窗口可单独设置收起方向（自动/左/右/上/下）
- 排除最大化窗口
"""
import time
from PySide6.QtCore import QObject, QTimer, Signal
from . import winapi


class DockManager(QObject):
    """管理窗口靠边自动收起功能。"""

    dock_state_changed = Signal(int, bool)  # hwnd, is_docked

    # 防误触发：窗口必须停止移动的时间（秒）
    DOCK_DELAY = 0.3

    # 有效的收起方向
    VALID_DIRECTIONS = ("auto", "left", "right", "top", "bottom")

    # 动画参数
    ANIMATION_DURATION = 200  # 动画时长（毫秒）
    ANIMATION_INTERVAL = 16    # 动画帧间隔（毫秒，约60fps）

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._docked_windows = {}  # hwnd -> state dict
        self._enabled_windows = set()  # 启用了停靠功能的窗口 hwnd
        self._window_directions = {}  # hwnd -> "auto"/"left"/"right"/"top"/"bottom"
        self._pending_dock = {}  # hwnd -> {rect, edge, time} 等待收起的窗口
        self._animating_windows = {}  # hwnd -> {from_rect, to_rect, start_time, duration} 正在动画的窗口
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_mouse_and_windows)
        self._timer.start(100)  # 100ms 轮询
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animation_tick)
        self._animation_timer.start(self.ANIMATION_INTERVAL)
        self._update_screen_size()

    def _update_screen_size(self):
        """更新屏幕尺寸。"""
        self._screen_width = winapi.get_screen_width()
        self._screen_height = winapi.get_screen_height()

    def set_dock_enabled(self, hwnd, enabled):
        """启用/禁用指定窗口的停靠功能。"""
        if enabled:
            self._enabled_windows.add(hwnd)
        else:
            self._enabled_windows.discard(hwnd)
            self._pending_dock.pop(hwnd, None)
            self._undock_window(hwnd)
            # 注意：不清理 _window_directions，重新启用后方向配置还在

    def is_dock_enabled(self, hwnd):
        return hwnd in self._enabled_windows

    def is_docked(self, hwnd):
        return hwnd in self._docked_windows

    def set_dock_direction(self, hwnd, direction):
        """设置指定窗口的收起方向。"""
        if direction not in self.VALID_DIRECTIONS:
            return
        self._window_directions[hwnd] = direction
        # 如果窗口已经收起，重新按新方向收起
        if hwnd in self._docked_windows:
            state = self._docked_windows[hwnd]
            original_rect = state["original_rect"]
            is_hidden = state["is_hidden"]
            new_edge = direction if direction != "auto" else self._detect_edge(original_rect)
            if new_edge:
                # 只有确定 new_edge 有效时才 pop，避免窗口意外失去收起状态
                self._docked_windows.pop(hwnd, None)
                self._dock_window(hwnd, new_edge, original_rect)
                if not is_hidden:
                    self._expand_window(hwnd)

    def get_dock_direction(self, hwnd):
        """获取指定窗口的收起方向，默认 auto。"""
        return self._window_directions.get(hwnd, "auto")

    def toggle_dock_current(self):
        """切换当前前台窗口的停靠功能。返回是否启用。"""
        hwnd = winapi.get_foreground_window()
        if not hwnd:
            return None
        enabled = not self.is_dock_enabled(hwnd)
        self.set_dock_enabled(hwnd, enabled)
        return enabled

    def _check_mouse_and_windows(self):
        """检查鼠标位置和窗口状态（核心循环）。"""
        if not self._config.get("dock_enabled", True):
            return

        try:
            mouse_x, mouse_y = winapi.get_cursor_pos()
        except Exception:
            return

        dock_width = self._config.get("dock_width", 3)

        # 1. 检查已收起的窗口（每个窗口单独异常保护）
        for hwnd, state in list(self._docked_windows.items()):
            try:
                if not winapi.is_window(hwnd):
                    self._docked_windows.pop(hwnd, None)
                    continue

                # 动画过程中跳过检测，避免干扰
                if self._is_animating(hwnd):
                    continue

                # 排除最大化窗口（已展开状态下也不触发收起）
                if self._is_maximized(hwnd):
                    continue

                if state["is_hidden"]:
                    # 检查鼠标是否在屏幕边缘（用屏幕边缘判断，不是窗口当前位置）
                    if self._is_mouse_on_screen_edge(mouse_x, mouse_y, state["edge"], state["original_rect"], dock_width):
                        self._expand_window(hwnd)
                else:
                    # 如果鼠标还在屏幕边缘，保持展开，不开始收起计时（防止闪烁）
                    if self._is_mouse_on_screen_edge(mouse_x, mouse_y, state["edge"], state["original_rect"], dock_width):
                        state.pop("hide_delay", None)
                        # 更新 last_rect
                        rect = winapi.get_window_rect(hwnd)
                        if rect:
                            state["last_rect"] = rect
                        continue

                    # 检查用户是否在拖动窗口
                    rect = winapi.get_window_rect(hwnd)
                    if rect:
                        # 初始化 last_rect
                        if "last_rect" not in state:
                            state["last_rect"] = rect
                        # 检测窗口位置是否变化（用户在拖动），加5像素容差
                        position_changed = not self._rect_almost_equal(state["last_rect"], rect, tolerance=5)
                        # 检测窗口是否还在对应方向的边缘附近
                        near_edge = self._is_window_near_edge(rect, state["edge"])

                        if position_changed and not near_edge:
                            # 用户拖动窗口离开了边缘，取消自动收起状态
                            # 从 _docked_windows 移除，但保留 _enabled_windows 和方向配置
                            # 这样窗口进入第二部分检测逻辑，等待下次靠近边缘时收起
                            self._docked_windows.pop(hwnd, None)
                            self._pending_dock.pop(hwnd, None)
                            continue

                        # 如果用户拖动了窗口但还在边缘附近，更新 original_rect 为当前位置
                        # 这样再次收起时会用新位置计算收起位置
                        if position_changed and near_edge:
                            state["original_rect"] = rect

                        # 更新 last_rect
                        state["last_rect"] = rect

                        # 检查鼠标是否离开了窗口（用户没拖动，只是鼠标移开了）
                        if not self._is_mouse_in_window(mouse_x, mouse_y, rect):
                            if "hide_delay" not in state:
                                state["hide_delay"] = time.time()
                            elif time.time() - state["hide_delay"] > 0.5:
                                self._hide_window(hwnd)
                        else:
                            state.pop("hide_delay", None)
            except Exception:
                # 单个窗口异常不影响其他窗口，也不会让定时器停止
                continue

        # 2. 检查启用了停靠但还未收起的窗口（带防误触发，每个窗口单独异常保护）
        for hwnd in list(self._enabled_windows):
            try:
                if not winapi.is_window(hwnd):
                    self._enabled_windows.discard(hwnd)
                    self._pending_dock.pop(hwnd, None)
                    continue
                if hwnd in self._docked_windows:
                    continue

                # 排除最大化窗口
                if self._is_maximized(hwnd):
                    self._pending_dock.pop(hwnd, None)
                    continue

                rect = winapi.get_window_rect(hwnd)
                if not rect:
                    continue

                # 获取收起方向：固定方向 or 自动检测
                direction = self.get_dock_direction(hwnd)
                if direction == "auto":
                    edge = self._detect_edge(rect)
                else:
                    # 固定方向：也要检查窗口是否真的靠近那个方向的边缘
                    # 否则不管窗口在屏幕哪里，只要停住就会收起
                    if self._is_window_near_edge(rect, direction):
                        edge = direction
                    else:
                        edge = None

                if edge:
                    # 窗口靠近边缘（或固定方向），检查是否停止移动足够长时间
                    if hwnd in self._pending_dock:
                        pending = self._pending_dock[hwnd]
                        # 检查窗口位置是否变化（加2像素容差，避免Windows微小波动导致永远不触发）
                        if self._rect_almost_equal(pending["rect"], rect):
                            # 位置没变，检查是否超时
                            if time.time() - pending["time"] >= self.DOCK_DELAY:
                                self._dock_window(hwnd, edge, rect)
                                self._pending_dock.pop(hwnd, None)
                        else:
                            # 位置变了，更新等待状态
                            pending["rect"] = rect
                            pending["edge"] = edge
                            pending["time"] = time.time()
                    else:
                        # 第一次检测到靠近边缘，开始计时
                        self._pending_dock[hwnd] = {
                            "rect": rect,
                            "edge": edge,
                            "time": time.time(),
                        }
                else:
                    # 窗口离开了边缘，取消等待
                    self._pending_dock.pop(hwnd, None)
            except Exception:
                # 单个窗口异常不影响其他窗口
                continue

    def _is_maximized(self, hwnd):
        """检查窗口是否最大化。"""
        try:
            import ctypes
            return bool(ctypes.windll.user32.IsZoomed(hwnd))
        except Exception:
            return False

    def _rect_almost_equal(self, r1, r2, tolerance=2):
        """比较两个窗口矩形是否近似相等（tolerance像素以内算没动）。"""
        return all(abs(a - b) <= tolerance for a, b in zip(r1, r2))

    def _detect_edge(self, rect):
        """自动检测窗口靠近哪个边缘（选择距离最近的边缘）。"""
        threshold = self._config.get("dock_threshold", 10)
        left, top, right, bottom = rect

        # 计算窗口每个边缘到屏幕对应边缘的距离
        distances = {
            "left": left,
            "right": self._screen_width - right,
            "top": top,
            "bottom": self._screen_height - bottom,
        }
        # 找到距离最小的边缘
        min_edge = min(distances, key=distances.get)
        if distances[min_edge] <= threshold:
            return min_edge
        return None

    def _is_window_near_edge(self, rect, edge):
        """检测窗口是否在指定方向的边缘附近。"""
        threshold = self._config.get("dock_threshold", 10)
        left, top, right, bottom = rect

        if edge == "left":
            return left <= threshold
        elif edge == "right":
            return right >= self._screen_width - threshold
        elif edge == "top":
            return top <= threshold
        elif edge == "bottom":
            return bottom >= self._screen_height - threshold
        return False

    def _ease_out(self, t):
        """缓动函数：开始快，结束慢（ease-out cubic）。"""
        return 1 - (1 - t) ** 3

    def _start_animation(self, hwnd, from_rect, to_rect):
        """启动窗口位置动画。"""
        self._animating_windows[hwnd] = {
            "from_rect": from_rect,
            "to_rect": to_rect,
            "start_time": time.time() * 1000,  # 毫秒
            "duration": self.ANIMATION_DURATION,
        }

    def _animation_tick(self):
        """动画帧更新：每帧更新所有正在动画的窗口位置。"""
        now = time.time() * 1000
        completed = []

        for hwnd, anim in list(self._animating_windows.items()):
            elapsed = now - anim["start_time"]
            t = min(elapsed / anim["duration"], 1.0)
            eased_t = self._ease_out(t)

            from_rect = anim["from_rect"]
            to_rect = anim["to_rect"]

            # 线性插值计算当前位置
            current_rect = tuple(
                int(from_rect[i] + (to_rect[i] - from_rect[i]) * eased_t)
                for i in range(4)
            )

            # 移动窗口
            left, top, right, bottom = current_rect
            width = right - left
            height = bottom - top
            try:
                winapi.move_window(hwnd, left, top, width, height)
            except Exception:
                pass

            if t >= 1.0:
                completed.append(hwnd)

        # 移除已完成的动画
        for hwnd in completed:
            self._animating_windows.pop(hwnd, None)

    def _is_animating(self, hwnd):
        """检查窗口是否正在动画。"""
        return hwnd in self._animating_windows

    def _stop_animation(self, hwnd):
        """停止窗口的动画。"""
        self._animating_windows.pop(hwnd, None)

    def _dock_window(self, hwnd, edge, original_rect):
        """收起窗口到屏幕边缘。"""
        self._docked_windows[hwnd] = {
            "original_rect": original_rect,
            "edge": edge,
            "is_hidden": True,
        }
        self._hide_window(hwnd)
        self.dock_state_changed.emit(hwnd, True)

    def _hide_window(self, hwnd):
        """把窗口平滑收起（动画移到屏幕外，只露出一条边）。"""
        state = self._docked_windows.get(hwnd)
        if not state:
            return

        # 如果正在动画，先停止
        self._stop_animation(hwnd)

        dock_width = self._config.get("dock_width", 3)
        left, top, right, bottom = state["original_rect"]
        width = right - left
        height = bottom - top
        edge = state["edge"]

        # 收起后的位置：窗口大部分在屏幕外，只露出 dock_width 像素
        if edge == "left":
            new_left = -width + dock_width
            new_top = top
        elif edge == "right":
            new_left = self._screen_width - dock_width
            new_top = top
        elif edge == "top":
            new_left = left
            new_top = -height + dock_width
        else:  # bottom
            new_left = left
            new_top = self._screen_height - dock_width

        to_rect = (new_left, new_top, new_left + width, new_top + height)

        # 获取当前位置作为动画起点
        current_rect = winapi.get_window_rect(hwnd)
        if not current_rect:
            current_rect = (0, top, width, top + height)

        # 启动动画
        self._start_animation(hwnd, current_rect, to_rect)
        state["is_hidden"] = True

    def _expand_window(self, hwnd):
        """展开窗口（平滑动画移到屏幕内的边缘位置，和收起位置严格对齐）。"""
        state = self._docked_windows.get(hwnd)
        if not state:
            return

        # 如果正在动画，先停止
        self._stop_animation(hwnd)

        dock_width = self._config.get("dock_width", 3)
        left, top, right, bottom = state["original_rect"]
        width = right - left
        height = bottom - top
        edge = state["edge"]

        # 展开到屏幕内的边缘位置，和收起位置严格对齐：
        # 左边收起：窗口右边在 dock_width，露出 0~dock_width → 展开：窗口左边在 0
        # 右边收起：窗口左边在 screen_width - dock_width → 展开：窗口右边在 screen_width
        # 上边收起：窗口下边在 dock_width → 展开：窗口上边在 0
        # 下边收起：窗口上边在 screen_height - dock_width → 展开：窗口下边在 screen_height
        if edge == "left":
            new_left = 0
            new_top = top
        elif edge == "right":
            new_left = self._screen_width - width
            new_top = top
        elif edge == "top":
            new_left = left
            new_top = 0
        else:  # bottom
            new_left = left
            new_top = self._screen_height - height

        to_rect = (new_left, new_top, new_left + width, new_top + height)

        # 获取当前位置作为动画起点
        current_rect = winapi.get_window_rect(hwnd)
        if not current_rect:
            current_rect = (0, top, width, top + height)

        # 启动动画
        self._start_animation(hwnd, current_rect, to_rect)
        state["is_hidden"] = False
        state.pop("hide_delay", None)

    def _undock_window(self, hwnd):
        """取消停靠，恢复窗口原始位置。"""
        # 停止动画
        self._stop_animation(hwnd)
        state = self._docked_windows.pop(hwnd, None)
        if state:
            # 恢复到原始位置（不是 _expand_window 的边缘位置）
            left, top, right, bottom = state["original_rect"]
            width = right - left
            height = bottom - top
            winapi.move_window(hwnd, left, top, width, height)
            self.dock_state_changed.emit(hwnd, False)

    def _is_mouse_on_screen_edge(self, mouse_x, mouse_y, edge, original_rect, dock_width):
        """检查鼠标是否在屏幕边缘（收起后展开的触发条件）。
        用屏幕边缘判断，不是窗口当前位置（窗口已经移到屏幕外了）。
        """
        left, top, right, bottom = original_rect
        margin = 5
        if edge == "left":
            return mouse_x <= dock_width + margin and top <= mouse_y <= bottom
        elif edge == "right":
            return mouse_x >= self._screen_width - dock_width - margin and top <= mouse_y <= bottom
        elif edge == "top":
            return mouse_y <= dock_width + margin and left <= mouse_x <= right
        else:  # bottom
            return mouse_y >= self._screen_height - dock_width - margin and left <= mouse_x <= right

    def _is_mouse_in_window(self, mouse_x, mouse_y, rect):
        """检查鼠标是否在窗口内。"""
        left, top, right, bottom = rect
        return left <= mouse_x <= right and top <= mouse_y <= bottom

    def undock_all(self):
        """取消所有窗口的停靠（程序退出时调用）。"""
        for hwnd in list(self._docked_windows.keys()):
            self._undock_window(hwnd)
        self._pending_dock.clear()

    def cleanup(self):
        """清理失效窗口。"""
        for hwnd in list(self._docked_windows.keys()):
            if not winapi.is_window(hwnd):
                self._docked_windows.pop(hwnd, None)
        for hwnd in list(self._pending_dock.keys()):
            if not winapi.is_window(hwnd):
                self._pending_dock.pop(hwnd, None)
        for hwnd in list(self._enabled_windows):
            if not winapi.is_window(hwnd):
                self._enabled_windows.discard(hwnd)
                self._window_directions.pop(hwnd, None)
