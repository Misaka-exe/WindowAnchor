"""系统托盘 v1.6.1：修复菜单重复显示bug，优化交互。"""
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from . import winapi


def _create_tray_icon(active: bool = False) -> QIcon:
    pm = QPixmap(32, 32)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    if active:
        p.setBrush(QBrush(QColor(232, 132, 36, 255)))
        p.setPen(QPen(QColor(180, 90, 0, 255), 1.5))
    else:
        p.setBrush(QBrush(QColor(150, 150, 150, 255)))
        p.setPen(QPen(QColor(100, 100, 100, 255), 1.5))
    p.drawEllipse(8, 4, 16, 16)
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QPolygonF
    p.setBrush(QBrush(QColor(120, 120, 120, 255)))
    p.setPen(QPen(QColor(0, 0, 0, 0)))
    p.drawPolygon(QPolygonF([QPointF(16, 20), QPointF(13, 28), QPointF(19, 28)]))
    p.end()
    return QIcon(pm)


class TrayController(QObject):
    """托盘控制器 v1.6.1：每次完全重建菜单，避免重复显示。"""

    toggle_requested = Signal()
    unpin_requested = Signal(int)
    unpin_all_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()
    menu_about_to_show = Signal()
    opacity_changed = Signal(int, int)
    click_through_toggled = Signal(int)
    bring_front_requested = Signal(int)
    send_back_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray = QSystemTrayIcon(_create_tray_icon(False), parent)
        self._tray.setToolTip("WindowAnchor - 窗口置顶工具")
        self._pinned_provider = None
        self._opacity_provider = None
        self._click_through_provider = None

        self._menu = QMenu()
        self._menu.aboutToShow.connect(self._on_menu_about_to_show)
        self._tray.setContextMenu(self._menu)
        self._tray.show()

        # 存储动态创建的 QAction 和 QMenu，防止被 GC
        self._dynamic_items = []

    def set_pinned_provider(self, callback):
        self._pinned_provider = callback

    def set_opacity_provider(self, callback):
        self._opacity_provider = callback

    def set_click_through_provider(self, callback):
        self._click_through_provider = callback


    def _on_menu_about_to_show(self):
        self.menu_about_to_show.emit()
        self._rebuild_menu()

    def _rebuild_menu(self):
        """完全清空菜单并重建，避免重复显示。"""
        # 清空所有现有项
        self._menu.clear()
        self._dynamic_items.clear()

        pinned = self._get_pinned()
        count = len(pinned)

        # 1. 状态显示
        if count > 0:
            status_text = f"📌 当前有 {count} 个置顶窗口"
            self._tray.setIcon(_create_tray_icon(True))
        else:
            status_text = "当前无置顶窗口"
            self._tray.setIcon(_create_tray_icon(False))
        status_action = QAction(status_text, self._menu)
        status_action.setEnabled(False)
        status_action.setFont(QFont("", 9, QFont.Bold))
        self._menu.addAction(status_action)
        self._dynamic_items.append(status_action)

        self._menu.addSeparator()

        # 2. 置顶当前窗口
        toggle_action = QAction("📌 置顶/取消当前窗口", self._menu)
        toggle_action.triggered.connect(self.toggle_requested.emit)
        self._menu.addAction(toggle_action)
        self._dynamic_items.append(toggle_action)

        self._menu.addSeparator()

        # 4. 已置顶窗口列表
        section_label = QAction("── 已置顶窗口 ──", self._menu)
        section_label.setEnabled(False)
        self._menu.addAction(section_label)
        self._dynamic_items.append(section_label)

        if count == 0:
            placeholder = QAction("（暂无已置顶窗口）", self._menu)
            placeholder.setEnabled(False)
            self._menu.addAction(placeholder)
            self._dynamic_items.append(placeholder)
        else:
            # 用集合去重，避免同一个hwnd显示多次
            seen_hwnds = set()
            for hwnd, title in pinned:
                if hwnd in seen_hwnds:
                    continue
                seen_hwnds.add(hwnd)

                short_title = title[:30] + "..." if len(title) > 30 else title
                opacity = self._get_opacity(hwnd)
                click_through = self._is_click_through(hwnd)

                opacity_text = f" ({opacity}%)" if opacity < 100 else ""
                ct_text = " [穿透]" if click_through else ""

                # 创建子菜单
                item_menu = QMenu(f"📌 {short_title}{opacity_text}{ct_text}", self._menu)
                self._dynamic_items.append(item_menu)

                # 取消置顶
                unpin_action = QAction("❌ 取消置顶", item_menu)
                unpin_action.triggered.connect(lambda checked, h=hwnd: self.unpin_requested.emit(h))
                item_menu.addAction(unpin_action)
                self._dynamic_items.append(unpin_action)

                item_menu.addSeparator()

                # 透明度子菜单
                opacity_menu = QMenu("🎚 调节透明度", item_menu)
                self._dynamic_items.append(opacity_menu)
                for op in [100, 90, 80, 70, 60, 50, 40, 30, 20]:
                    act = QAction(f"{op}%", opacity_menu)
                    act.setCheckable(True)
                    act.setChecked(op == opacity)
                    act.triggered.connect(lambda checked, h=hwnd, o=op: self.opacity_changed.emit(h, o))
                    opacity_menu.addAction(act)
                    self._dynamic_items.append(act)
                item_menu.addMenu(opacity_menu)

                # 点击穿透
                ct_action = QAction("🖱 点击穿透（开启后点击穿透窗口）", item_menu)
                ct_action.setCheckable(True)
                ct_action.setChecked(click_through)
                ct_action.triggered.connect(lambda checked, h=hwnd: self.click_through_toggled.emit(h))
                item_menu.addAction(ct_action)
                self._dynamic_items.append(ct_action)

                item_menu.addSeparator()

                # 关闭窗口
                close_action = QAction("关闭此窗口", item_menu)
                close_action.triggered.connect(lambda checked, h=hwnd: self._close_window(h))
                item_menu.addAction(close_action)
                self._dynamic_items.append(close_action)

                # 把子菜单添加到主菜单
                menu_action = self._menu.addMenu(item_menu)
                self._dynamic_items.append(menu_action)

                # 添加一个"点击取消置顶"的快捷项
                quick_unpin = QAction("    点击取消置顶", self._menu)
                quick_unpin.triggered.connect(lambda checked, h=hwnd: self.unpin_requested.emit(h))
                self._menu.addAction(quick_unpin)
                self._dynamic_items.append(quick_unpin)

        self._menu.addSeparator()

        # 5. 全部取消
        unpin_all_action = QAction("取消所有置顶", self._menu)
        unpin_all_action.triggered.connect(self.unpin_all_requested.emit)
        self._menu.addAction(unpin_all_action)
        self._dynamic_items.append(unpin_all_action)

        # 6. 设置
        settings_action = QAction("⚙ 设置", self._menu)
        settings_action.triggered.connect(self.settings_requested.emit)
        self._menu.addAction(settings_action)
        self._dynamic_items.append(settings_action)

        self._menu.addSeparator()

        # 7. 退出
        quit_action = QAction("退出", self._menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        self._menu.addAction(quit_action)
        self._dynamic_items.append(quit_action)

    def _close_window(self, hwnd: int):
        try:
            import win32con
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        except Exception:
            pass

    def _get_pinned(self):
        if not self._pinned_provider:
            return []
        return self._pinned_provider()

    def _get_opacity(self, hwnd: int) -> int:
        if not self._opacity_provider:
            return 100
        return self._opacity_provider(hwnd)

    def _is_click_through(self, hwnd: int) -> bool:
        if not self._click_through_provider:
            return False
        return self._click_through_provider(hwnd)

    def rebuild(self):
        self._rebuild_menu()

    def show_message(self, title: str, message: str, duration: int = 2000):
        self._tray.showMessage(
            title, message, QSystemTrayIcon.MessageIcon.Information, duration,
        )

    def set_tooltip(self, text: str):
        self._tray.setToolTip(text)
