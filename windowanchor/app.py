"""应用主控 v1.6：整合置顶恢复、点击穿透、层级排序、系统菜单、透明度调节。"""
import sys
import ctypes
import winerror
import win32con
from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from . import winapi
from .config import ConfigManager
from .hotkey import HotkeyThread, display_hotkey
from .pin_manager import PinManager
from .tray import TrayController
from .settings_dialog import SettingsDialog

MUTEX_NAME = "Global\\WindowAnchor_SingleInstance_v16"


class AppController(QObject):
    """应用总控制器 v1.6。"""

    def __init__(self, app: QApplication):
        super().__init__()
        self._app = app
        self._mutex = None
        self._last_foreground = 0

        # 核心组件
        self._config = ConfigManager(parent=self)
        self._pin_mgr = PinManager(parent=self)
        self._hotkey = HotkeyThread(parent=self)
        self._tray = TrayController(parent=self)
        self._settings_dialog = None

        # 连接托盘
        self._tray.set_pinned_provider(self._pin_mgr.list_pinned)
        self._tray.set_opacity_provider(self._pin_mgr.get_opacity)
        self._tray.set_click_through_provider(self._pin_mgr.is_click_through)
        self._tray.toggle_requested.connect(self._on_toggle_current)
        self._tray.unpin_requested.connect(self._on_unpin)
        self._tray.unpin_all_requested.connect(self._on_unpin_all)
        self._tray.settings_requested.connect(self._open_settings)
        self._tray.quit_requested.connect(self.quit)
        self._tray.menu_about_to_show.connect(self._on_menu_about_to_show)
        self._tray.opacity_changed.connect(self._on_opacity_changed)
        self._tray.click_through_toggled.connect(self._on_click_through_toggled)


        # 连接热键
        self._hotkey.triggered.connect(self._on_toggle_current)
        self._hotkey.error.connect(self._on_hotkey_error)

        # 应用配置中的热键
        mods = self._config.get("hotkey_modifiers")
        vk = self._config.get("hotkey_key")
        # 热键有效性检查：如果配置里的热键无效（如被错误保存为0），重置为默认
        if not mods or not vk:
            mods = win32con.MOD_CONTROL | win32con.MOD_SHIFT
            vk = win32con.VK_SPACE
            self._config.set("hotkey_modifiers", mods, save=False)
            self._config.set("hotkey_key", vk, save=False)
            self._config.set("hotkey_display", "Ctrl+Shift+Space", save=False)
        self._hotkey.set_hotkey(mods, vk)
        self._hotkey.start()

        # 设置系统菜单回调

        # 更新托盘提示
        self._update_tray_tooltip()

        # 启动提示
        if self._config.get("show_startup_message"):
            hotkey_text = display_hotkey(mods, vk)
            self._tray.show_message(
                "WindowAnchor v1.0 已启动",
                f"按 {hotkey_text} 切换当前窗口置顶\n"
                f"右键托盘图标查看更多功能",
                3000,
            )

        # 定时清理失效窗口（每30秒）
        self._cleanup_timer = QTimer(self)
        self._cleanup_timer.timeout.connect(self._pin_mgr.cleanup_invalid)
        self._cleanup_timer.start(30000)

        # v1.6 新增：置顶状态恢复定时器（修复"点击其他窗口失去置顶"的bug）
        self._restore_timer = QTimer(self)
        self._restore_timer.timeout.connect(self._restore_topmost)
        self._update_restore_timer()

        # v1.6.5 新增：高频层级保持定时器（200ms）
        # 确保用户点击窗口后，设定的层级顺序几乎瞬间恢复

        # 监听配置变化
        self._config.config_changed.connect(self._on_config_changed)

    # ----------------------------------------------------------
    # 置顶状态恢复（核心bug修复）
    # ----------------------------------------------------------

    def _restore_topmost(self):
        """定期检查并恢复丢失的置顶状态。"""
        if not self._config.get("auto_restore_topmost"):
            return
        restored = self._pin_mgr.restore_topmost()
        if restored > 0:
            # 静默恢复，不弹窗打扰用户
            pass

    def _update_restore_timer(self):
        """根据配置更新恢复定时器的间隔。"""
        if self._config.get("auto_restore_topmost"):
            interval = self._config.get("restore_interval", 5)
            self._restore_timer.start(interval * 1000)
        else:
            self._restore_timer.stop()



    # ----------------------------------------------------------
    # 托盘/热键回调
    # ----------------------------------------------------------

    def _on_menu_about_to_show(self):
        hwnd = winapi.get_foreground_window()
        if hwnd and winapi.is_window(hwnd):
            self._last_foreground = hwnd

    def _on_toggle_current(self):
        """热键/托盘：切换当前前台窗口的置顶状态。"""
        hwnd = winapi.get_foreground_window()
        if not hwnd or not winapi.is_window(hwnd):
            hwnd = self._last_foreground
        if not hwnd or not winapi.is_window(hwnd):
            return

        default_opacity = self._config.get("default_opacity")
        title = winapi.get_window_title(hwnd) or "该窗口"
        # 检查置顶前窗口是否能被操作（权限检测）
        was_topmost = winapi.is_topmost(hwnd)
        pinned = self._pin_mgr.toggle(hwnd, default_opacity)
        # 验证置顶是否真的生效
        if pinned and not winapi.is_topmost(hwnd):
            # 置顶失败，可能是权限问题
            self._tray.show_message(
                "WindowAnchor",
                f"无法置顶：{title[:20]}\n该程序可能以管理员权限运行，\n请以管理员权限重启 WindowAnchor 后重试。",
                5000,
            )
            return
        opacity = self._pin_mgr.get_opacity(hwnd)

        if pinned:
            opacity_text = f"（透明度 {opacity}%）" if opacity < 100 else ""
            self._tray.show_message("WindowAnchor", f"已置顶：{title[:30]}{opacity_text}")
        else:
            self._tray.show_message("WindowAnchor", f"已取消置顶：{title[:30]}")

        self._tray.rebuild()
        self._update_tray_tooltip()

    def _on_unpin(self, hwnd: int):
        self._pin_mgr.unpin(hwnd)
        self._tray.rebuild()
        self._update_tray_tooltip()

    def _on_unpin_all(self):
        count = self._pin_mgr.count()
        self._pin_mgr.unpin_all()
        if count > 0:
            self._tray.show_message("WindowAnchor", f"已取消全部 {count} 个窗口的置顶")
        self._tray.rebuild()
        self._update_tray_tooltip()

    def _on_opacity_changed(self, hwnd: int, opacity: int):
        self._pin_mgr.set_opacity(hwnd, opacity)
        self._tray.rebuild()

    def _on_click_through_toggled(self, hwnd: int):
        """切换点击穿透状态。"""
        new_state = self._pin_mgr.toggle_click_through(hwnd)
        title = winapi.get_window_title(hwnd) or "该窗口"
        if new_state:
            self._tray.show_message(
                "点击穿透已开启",
                f"{title[:25]}\n现在点击会穿透到后面的窗口\n"
                f"如需取消，请在托盘菜单中关闭",
                3000,
            )
        else:
            self._tray.show_message("点击穿透已关闭", f"{title[:25]}", 2000)
        self._tray.rebuild()






    def _on_hotkey_error(self, msg: str):
        self._tray.show_message("WindowAnchor 热键错误", msg, 5000)

    # ----------------------------------------------------------
    # 设置界面
    # ----------------------------------------------------------

    def _open_settings(self):
        if self._settings_dialog is None:
            self._settings_dialog = SettingsDialog(self._config)
            self._settings_dialog.settings_applied.connect(self._on_settings_applied)
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()

    def _on_settings_applied(self):
        mods = self._config.get("hotkey_modifiers")
        vk = self._config.get("hotkey_key")
        self._hotkey.set_hotkey(mods, vk)
        self._update_restore_timer()
        self._update_tray_tooltip()
        self._tray.show_message("WindowAnchor", "设置已生效", 1500)

    def _on_config_changed(self, key: str, value):
        """配置变化时的响应。"""
        if key == "auto_restore_topmost" or key == "restore_interval":
            self._update_restore_timer()
        elif key == "hotkey_modifiers" or key == "hotkey_key":
            # 热键变化时重新注册
            mods = self._config.get("hotkey_modifiers")
            vk = self._config.get("hotkey_key")
            if mods and vk:  # 只在热键有效时重新注册
                self._hotkey.set_hotkey(mods, vk)

    def _update_tray_tooltip(self):
        mods = self._config.get("hotkey_modifiers")
        vk = self._config.get("hotkey_key")
        hotkey_text = display_hotkey(mods, vk)
        count = self._pin_mgr.count()
        if count > 0:
            tip = f"WindowAnchor v1.0 - {count} 个置顶窗口\n热键：{hotkey_text}\n右键打开菜单"
        else:
            tip = f"WindowAnchor v1.0 - 窗口置顶工具\n热键：{hotkey_text}\n右键打开菜单"
        self._tray.set_tooltip(tip)

    # ----------------------------------------------------------
    # 生命周期
    # ----------------------------------------------------------

    def quit(self):
        if self._config.get("unpin_on_exit"):
            self._pin_mgr.unpin_all()
        self._hotkey.stop()
        self._cleanup_timer.stop()
        self._restore_timer.stop()


        if self._mutex:
            ctypes.windll.kernel32.CloseHandle(self._mutex)
            self._mutex = None
        self._app.quit()

    def run(self):
        return self._app.exec()


def _acquire_single_instance():
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        return None
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == winerror.ERROR_ALREADY_EXISTS:
        ctypes.windll.kernel32.CloseHandle(handle)
        return None
    return handle


def main():
    mutex_handle = _acquire_single_instance()
    if not mutex_handle:
        ctypes.windll.user32.MessageBoxW(
            0, "WindowAnchor 已经在运行中。", "WindowAnchor", 0x40,
        )
        return 1

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("WindowAnchor")
    app.setApplicationVersion("1.0.0")

    controller = AppController(app)
    controller._mutex = mutex_handle
    return controller.run()


if __name__ == "__main__":
    sys.exit(main())
