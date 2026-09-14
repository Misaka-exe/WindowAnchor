"""配置管理：JSON 持久化，支持热键、透明度、开机自启等设置。"""
import json
import os
from pathlib import Path
from PySide6.QtCore import QObject, Signal


class ConfigManager(QObject):
    """配置管理器，所有设置通过此对象读写，自动持久化到本地 JSON。"""

    config_changed = Signal(str, object)

    _DEFAULTS = {
        # 热键
        "hotkey_modifiers": 0x0002 | 0x0004,
        "hotkey_key": 0x20,
        "hotkey_display": "Ctrl+Shift+Space",

        # 透明度
        "default_opacity": 100,
        "remember_opacity": True,

        # 常规
        "auto_start": False,
        "show_startup_message": True,
        "unpin_on_exit": True,
        "language": "zh_CN",

        # v1.6 新增
        "auto_restore_topmost": True,   # 自动恢复丢失的置顶状态
        "restore_interval": 1,           # 置顶状态检查间隔（秒），1秒确保层级快速恢复
        # 2.0 新增：窗口靠边自动收起
        "dock_enabled": True,            # 启用窗口靠边收起功能
        "dock_width": 3,                 # 收起后露出的边宽度（像素）
        "dock_threshold": 10,            # 触发收起的边缘阈值（像素）
        # 2.0 新增：老板键
        "boss_key_enabled": True,         # 启用老板键
        "boss_key_modifiers": 0x0002 | 0x0004,  # Ctrl+Shift
        "boss_key_key": 0x48,             # H 键
        "boss_key_display": "Ctrl+Shift+H",
        "boss_key_mute": False,           # 隐藏时同时静音
        # 2.0 新增：窗口贴靠分屏
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = dict(self._DEFAULTS)
        self._config_path = self._get_config_path()
        self._load()

    def _get_config_path(self) -> Path:
        appdata = os.environ.get("APPDATA", str(Path.home()))
        config_dir = Path(appdata) / "WindowAnchor"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def _load(self):
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                for key, value in saved.items():
                    if key in self._DEFAULTS:
                        self._data[key] = value
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self):
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def get(self, key: str, default=None):
        """读取配置项。如果key不存在且提供了default，返回default。"""
        if key in self._data:
            return self._data[key]
        if key in self._DEFAULTS:
            return self._DEFAULTS[key]
        return default

    def set(self, key: str, value, save: bool = True):
        if key in self._DEFAULTS:
            self._data[key] = value
            if save:
                self._save()
            self.config_changed.emit(key, value)

    def get_all(self) -> dict:
        return dict(self._data)

    def reset(self, key: str = None):
        if key is None:
            self._data = dict(self._DEFAULTS)
            self._save()
            for k, v in self._data.items():
                self.config_changed.emit(k, v)
        elif key in self._DEFAULTS:
            self.set(key, self._DEFAULTS[key])

    @property
    def config_path(self) -> str:
        return str(self._config_path)
