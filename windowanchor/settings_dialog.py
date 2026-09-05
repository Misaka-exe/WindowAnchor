"""设置对话框 v1.6.1：修复热键录制器，用自定义控件直接捕获按键。"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QFocusEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QCheckBox, QSlider, QSpinBox, QGroupBox,
    QLineEdit, QMessageBox,
)
import win32con
from .config import ConfigManager
from .hotkey import display_hotkey


class HotkeyLineEdit(QLineEdit):
    """自定义热键输入框：点击后进入录制模式，直接捕获按键组合。
    重写 keyPressEvent 而不是用 eventFilter，更可靠。
    """

    hotkey_captured = Signal(int, int)  # modifiers, vk

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recording = False
        self._current_modifiers = 0
        self._current_vk = 0
        self.setReadOnly(True)
        self.setPlaceholderText("点击此处录制热键")
        self.setMinimumWidth(180)

    def set_hotkey(self, modifiers: int, vk: int):
        self._current_modifiers = modifiers
        self._current_vk = vk
        self.setText(display_hotkey(modifiers, vk))

    def get_hotkey(self):
        return self._current_modifiers, self._current_vk

    def start_recording(self):
        """开始录制热键。"""
        self._recording = True
        self.setText("请按下组合键...")
        self.setFocus()
        self.selectAll()

    def stop_recording(self):
        """停止录制。"""
        self._recording = False
        if self._current_vk:
            self.setText(display_hotkey(self._current_modifiers, self._current_vk))
        else:
            self.setText("")
            self.setPlaceholderText("点击此处录制热键")

    def keyPressEvent(self, event: QKeyEvent):
        """捕获按键事件。这是最可靠的方式。"""
        if not self._recording:
            # 非录制模式下，按任意键开始录制
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Space:
                self.start_recording()
                event.accept()
                return
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()

        # 转换 Qt 修饰键到 Windows 位掩码
        win_mods = 0
        if modifiers & Qt.ControlModifier:
            win_mods |= win32con.MOD_CONTROL
        if modifiers & Qt.AltModifier:
            win_mods |= win32con.MOD_ALT
        if modifiers & Qt.ShiftModifier:
            win_mods |= win32con.MOD_SHIFT
        if modifiers & Qt.MetaModifier:
            win_mods |= win32con.MOD_WIN

        # 判断是否是修饰键本身
        is_modifier_key = key in (
            Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta,
        )

        if is_modifier_key:
            # 只按了修饰键，继续等待主键
            event.accept()
            return

        if key == Qt.Key_Escape:
            # Esc 取消录制
            self.stop_recording()
            event.accept()
            return

        # 有修饰键的组合键
        if win_mods:
            vk = self._qt_key_to_vk(key)
            if vk:
                self._current_modifiers = win_mods
                self._current_vk = vk
                self.setText(display_hotkey(win_mods, vk))
                self.hotkey_captured.emit(win_mods, vk)
                self._recording = False
                event.accept()
                return
        else:
            # 单键（F1-F12、特殊功能键等）也支持
            vk = self._qt_key_to_vk(key)
            if vk:
                self._current_modifiers = 0
                self._current_vk = vk
                self.setText(display_hotkey(0, vk))
                self.hotkey_captured.emit(0, vk)
                self._recording = False
                event.accept()
                return

        # 不支持的键，忽略
        event.accept()

    def focusOutEvent(self, event: QFocusEvent):
        """失去焦点时停止录制。"""
        if self._recording:
            self.stop_recording()
        super().focusOutEvent(event)

    @staticmethod
    def _qt_key_to_vk(qt_key: int) -> int:
        """Qt 键码转 Windows 虚拟键码。完整映射表。"""
        # 字母 A-Z
        if Qt.Key_A <= qt_key <= Qt.Key_Z:
            return 0x41 + (qt_key - Qt.Key_A)
        # 数字 0-9
        if Qt.Key_0 <= qt_key <= Qt.Key_9:
            return 0x30 + (qt_key - Qt.Key_0)
        # F1-F24
        if Qt.Key_F1 <= qt_key <= Qt.Key_F24:
            return 0x70 + (qt_key - Qt.Key_F1)
        # 特殊键
        mapping = {
            Qt.Key_Space: 0x20,
            Qt.Key_Tab: 0x09,
            Qt.Key_Return: 0x0D,
            Qt.Key_Enter: 0x0D,
            Qt.Key_Escape: 0x1B,
            Qt.Key_Delete: 0x2E,
            Qt.Key_Backspace: 0x08,
            Qt.Key_Insert: 0x2D,
            Qt.Key_Home: 0x24,
            Qt.Key_End: 0x23,
            Qt.Key_PageUp: 0x21,
            Qt.Key_PageDown: 0x22,
            Qt.Key_Up: 0x26,
            Qt.Key_Down: 0x28,
            Qt.Key_Left: 0x25,
            Qt.Key_Right: 0x27,
            Qt.Key_Comma: 0xBC,
            Qt.Key_Period: 0xBE,
            Qt.Key_Semicolon: 0xBA,
            Qt.Key_Apostrophe: 0xDE,
            Qt.Key_BracketLeft: 0xDB,
            Qt.Key_BracketRight: 0xDD,
            Qt.Key_Backslash: 0xDC,
            Qt.Key_Slash: 0xBF,
            Qt.Key_QuoteLeft: 0xC0,
            Qt.Key_Minus: 0xBD,
            Qt.Key_Equal: 0xBB,
            Qt.Key_Plus: 0xBB,
            Qt.Key_Underscore: 0xBD,
            Qt.Key_NumLock: 0x90,
            Qt.Key_CapsLock: 0x14,
            Qt.Key_ScrollLock: 0x91,
            Qt.Key_Print: 0x2C,
            Qt.Key_Pause: 0x13,
            Qt.Key_Menu: 0x5D,
        }
        return mapping.get(qt_key, 0)


class HotkeyRecorder(QWidget):
    """热键录制器容器：包含输入框、录制按钮、重置按钮。"""

    hotkey_changed = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending_hotkey = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._edit = HotkeyLineEdit()
        self._edit.hotkey_captured.connect(self._on_hotkey_captured)
        layout.addWidget(self._edit)

        self._record_btn = QPushButton("录制")
        self._record_btn.setCheckable(True)
        self._record_btn.clicked.connect(self._toggle_record)
        self._record_btn.setFixedWidth(70)
        layout.addWidget(self._record_btn)

        self._reset_btn = QPushButton("重置")
        self._reset_btn.clicked.connect(self._reset)
        self._reset_btn.setFixedWidth(60)
        layout.addWidget(self._reset_btn)

    def set_hotkey(self, modifiers: int, vk: int):
        self._edit.set_hotkey(modifiers, vk)
        self._pending_hotkey = None

    def get_hotkey(self):
        if self._pending_hotkey:
            return self._pending_hotkey
        return self._edit.get_hotkey()

    def _toggle_record(self):
        if self._record_btn.isChecked():
            self._record_btn.setText("按组合键")
            self._record_btn.setStyleSheet("background-color: #e67e22; color: white;")
            self._edit.start_recording()
        else:
            self._stop_recording()

    def _stop_recording(self):
        self._record_btn.setChecked(False)
        self._record_btn.setText("录制")
        self._record_btn.setStyleSheet("")
        self._edit.stop_recording()

    def _on_hotkey_captured(self, modifiers: int, vk: int):
        self._pending_hotkey = (modifiers, vk)
        self._stop_recording()
        self.hotkey_changed.emit(modifiers, vk)

    def _reset(self):
        mods = win32con.MOD_CONTROL | win32con.MOD_SHIFT
        vk = win32con.VK_SPACE
        self._edit.set_hotkey(mods, vk)
        self._pending_hotkey = (mods, vk)
        self.hotkey_changed.emit(mods, vk)


class SettingsDialog(QDialog):
    """设置主对话框 v1.6.1。"""

    settings_applied = Signal()

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self._config = config
        self._pending_hotkey = None

        self.setWindowTitle("WindowAnchor 设置")
        self.setMinimumSize(500, 480)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_general_tab(), "常规")
        self._tabs.addTab(self._build_hotkey_tab(), "热键")
        self._tabs.addTab(self._build_opacity_tab(), "透明度")
        self._tabs.addTab(self._build_advanced_tab(), "高级")
        layout.addWidget(self._tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._ok_btn = QPushButton("确定")
        self._ok_btn.clicked.connect(self._on_ok)
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        self._apply_btn = QPushButton("应用")
        self._apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self._ok_btn)
        btn_layout.addWidget(self._cancel_btn)
        btn_layout.addWidget(self._apply_btn)
        layout.addLayout(btn_layout)

        self._load_from_config()

    def _build_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        startup_group = QGroupBox("启动")
        startup_layout = QVBoxLayout(startup_group)
        self._auto_start_cb = QCheckBox("开机自动启动")
        self._startup_msg_cb = QCheckBox("启动时显示托盘提示")
        startup_layout.addWidget(self._auto_start_cb)
        startup_layout.addWidget(self._startup_msg_cb)
        layout.addWidget(startup_group)

        behavior_group = QGroupBox("行为")
        behavior_layout = QVBoxLayout(behavior_group)
        self._unpin_on_exit_cb = QCheckBox("退出程序时自动取消所有置顶")
        self._remember_opacity_cb = QCheckBox("记住每个程序的透明度偏好")
        behavior_layout.addWidget(self._unpin_on_exit_cb)
        behavior_layout.addWidget(self._remember_opacity_cb)
        layout.addWidget(behavior_group)

        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)
        about_label = QLabel(
            "WindowAnchor v1.0\n"
            "轻量级 Windows 窗口置顶工具\n"
            "支持自定义热键、透明度、点击穿透、层级排序"
        )
        about_label.setStyleSheet("color: #666; font-size: 12px;")
        about_layout.addWidget(about_label)
        layout.addWidget(about_group)

        layout.addStretch()
        return widget

    def _build_hotkey_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("置顶切换热键")
        group_layout = QVBoxLayout(group)
        desc = QLabel(
            "点击「录制」按钮或直接点击输入框，然后按下组合键。\n"
            "支持 Ctrl/Alt/Shift/Win + 字母/数字/功能键。\n"
            "录制时按 Esc 取消。"
        )
        desc.setStyleSheet("color: #666; font-size: 12px;")
        desc.setWordWrap(True)
        group_layout.addWidget(desc)

        self._hotkey_recorder = HotkeyRecorder()
        self._hotkey_recorder.hotkey_changed.connect(self._on_hotkey_recorded)
        # 用当前配置的热键初始化，避免默认值(0,0)覆盖配置
        _init_mods = self._config.get("hotkey_modifiers")
        _init_vk = self._config.get("hotkey_key")
        self._hotkey_recorder.set_hotkey(_init_mods, _init_vk)
        group_layout.addWidget(self._hotkey_recorder)

        self._hotkey_hint = QLabel("")
        self._hotkey_hint.setStyleSheet("color: #e67e22; font-size: 12px;")
        self._hotkey_hint.setWordWrap(True)
        group_layout.addWidget(self._hotkey_hint)
        layout.addWidget(group)

        layout.addStretch()
        return widget

    def _build_opacity_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        default_group = QGroupBox("新置顶窗口默认透明度")
        default_layout = QVBoxLayout(default_group)
        slider_row = QHBoxLayout()
        self._opacity_slider = QSlider(Qt.Horizontal)
        self._opacity_slider.setRange(10, 100)
        self._opacity_slider.setTickPosition(QSlider.TicksBelow)
        self._opacity_slider.setTickInterval(10)
        self._opacity_value = QLabel("100%")
        self._opacity_value.setMinimumWidth(50)
        self._opacity_value.setAlignment(Qt.AlignCenter)
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_value.setText(f"{v}%")
        )
        slider_row.addWidget(self._opacity_slider)
        slider_row.addWidget(self._opacity_value)
        default_layout.addLayout(slider_row)
        hint = QLabel("透明度 100% = 完全不透明，10% = 几乎透明。")
        hint.setStyleSheet("color: #666; font-size: 12px;")
        hint.setWordWrap(True)
        default_layout.addWidget(hint)
        layout.addWidget(default_group)

        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)
        self._preview_label = QLabel("这是透明度预览区域\n拖动上方滑块查看效果")
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setStyleSheet(
            "background-color: #3498db; color: white; padding: 20px; border-radius: 6px;"
        )
        self._preview_label.setMinimumHeight(80)
        self._opacity_slider.valueChanged.connect(self._update_preview)
        preview_layout.addWidget(self._preview_label)
        layout.addWidget(preview_group)

        layout.addStretch()
        return widget

    def _build_advanced_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        restore_group = QGroupBox("置顶状态保护")
        restore_layout = QVBoxLayout(restore_group)
        self._auto_restore_cb = QCheckBox("自动恢复丢失的置顶状态")
        self._auto_restore_cb.setToolTip(
            "某些窗口在获得/失去焦点时会丢失置顶样式，\n开启后程序会定期检查并恢复。"
        )
        restore_layout.addWidget(self._auto_restore_cb)

        interval_row = QHBoxLayout()
        interval_label = QLabel("检查间隔：")
        self._restore_interval = QSpinBox()
        self._restore_interval.setRange(1, 60)
        self._restore_interval.setSuffix(" 秒")
        interval_row.addWidget(interval_label)
        interval_row.addWidget(self._restore_interval)
        interval_row.addStretch()
        restore_layout.addLayout(interval_row)

        restore_hint = QLabel("修复「点击其他窗口后置顶失效」的问题。建议保持开启。")
        restore_hint.setStyleSheet("color: #666; font-size: 12px;")
        restore_hint.setWordWrap(True)
        restore_layout.addWidget(restore_hint)
        layout.addWidget(restore_group)


        layout.addStretch()
        return widget

    def _load_from_config(self):
        self._auto_start_cb.setChecked(self._config.get("auto_start"))
        self._startup_msg_cb.setChecked(self._config.get("show_startup_message"))
        self._unpin_on_exit_cb.setChecked(self._config.get("unpin_on_exit"))
        self._remember_opacity_cb.setChecked(self._config.get("remember_opacity"))

        mods = self._config.get("hotkey_modifiers")
        vk = self._config.get("hotkey_key")
        self._hotkey_recorder.set_hotkey(mods, vk)
        self._pending_hotkey = None

        self._opacity_slider.setValue(self._config.get("default_opacity"))

        self._auto_restore_cb.setChecked(self._config.get("auto_restore_topmost"))
        self._restore_interval.setValue(self._config.get("restore_interval", 5))

    def _apply_settings(self):
        from . import winapi

        self._config.set("show_startup_message", self._startup_msg_cb.isChecked())
        self._config.set("unpin_on_exit", self._unpin_on_exit_cb.isChecked())
        self._config.set("remember_opacity", self._remember_opacity_cb.isChecked())

        want_auto = self._auto_start_cb.isChecked()
        if want_auto != self._config.get("auto_start"):
            ok = winapi.set_auto_start(want_auto)
            if ok:
                self._config.set("auto_start", want_auto)
            else:
                QMessageBox.warning(self, "设置失败", "无法修改开机自启设置。")
                self._auto_start_cb.setChecked(self._config.get("auto_start"))

        # 应用热键
        mods, vk = self._hotkey_recorder.get_hotkey()
        if mods != self._config.get("hotkey_modifiers") or vk != self._config.get("hotkey_key"):
            self._config.set("hotkey_modifiers", mods)
            self._config.set("hotkey_key", vk)
            self._config.set("hotkey_display", display_hotkey(mods, vk))

        self._config.set("default_opacity", self._opacity_slider.value())

        self._config.set("auto_restore_topmost", self._auto_restore_cb.isChecked())
        self._config.set("restore_interval", self._restore_interval.value())

        self.settings_applied.emit()

    def _on_ok(self):
        self._apply_settings()
        self.accept()

    def _on_apply(self):
        self._apply_settings()

    def _on_hotkey_recorded(self, modifiers: int, vk: int):
        self._pending_hotkey = (modifiers, vk)
        self._hotkey_hint.setText(
            f"已录制：{display_hotkey(modifiers, vk)}\n点击「确定」或「应用」后生效。"
        )

    def _update_preview(self, value: int):
        alpha = value / 100.0
        self._preview_label.setStyleSheet(
            f"background-color: rgba(52, 152, 219, {alpha}); "
            f"color: white; padding: 20px; border-radius: 6px;"
        )
