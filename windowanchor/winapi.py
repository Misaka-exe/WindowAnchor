"""Windows API 封装 v1.7：窗口置顶、透明度、点击穿透、开机自启。"""
import ctypes
import os
import win32gui
import win32con
import win32api

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32


# 存储窗口子类化的原始窗口过程，用于恢复
_original_wndprocs = {}
# 存储哪些窗口已经添加了系统菜单项

# ============================================================
# 窗口置顶
# ============================================================

def get_foreground_window() -> int:
    """获取当前前台窗口句柄。"""
    try:
        return win32gui.GetForegroundWindow()
    except Exception:
        return 0


def is_window(hwnd: int) -> bool:
    """检查窗口句柄是否有效。"""
    try:
        return bool(win32gui.IsWindow(hwnd))
    except Exception:
        return False


def get_window_title(hwnd: int) -> str:
    """获取窗口标题。"""
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""


def get_window_class(hwnd: int) -> str:
    """获取窗口类名。"""
    try:
        return win32gui.GetClassName(hwnd)
    except Exception:
        return ""


def get_process_name(hwnd: int) -> str:
    """获取窗口所属进程名。"""
    try:
        import win32process
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        name = win32process.GetModuleFileNameEx(handle, 0)
        win32api.CloseHandle(handle)
        import os
        return os.path.basename(name)
    except Exception:
        return ""


def set_topmost(hwnd: int, topmost: bool) -> bool:
    """设置窗口是否置顶。成功返回 True。"""
    try:
        flag = win32con.HWND_TOPMOST if topmost else win32con.HWND_NOTOPMOST
        win32gui.SetWindowPos(
            hwnd, flag, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
        )
        return True
    except Exception:
        return False


def is_topmost(hwnd: int) -> bool:
    """判断窗口是否处于置顶状态。"""
    try:
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        return bool(ex_style & win32con.WS_EX_TOPMOST)
    except Exception:
        return False

# ============================================================
# 窗口透明度
# ============================================================

def set_opacity(hwnd: int, opacity: int) -> bool:
    """设置窗口透明度。opacity: 10-100。"""
    try:
        opacity = max(10, min(100, opacity))
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if not (ex_style & win32con.WS_EX_LAYERED):
            win32gui.SetWindowLong(
                hwnd, win32con.GWL_EXSTYLE,
                ex_style | win32con.WS_EX_LAYERED,
            )
        alpha = int(opacity * 255 / 100)
        _user32.SetLayeredWindowAttributes(hwnd, 0, alpha, 0x2)
        return True
    except Exception:
        return False


def get_opacity(hwnd: int) -> int:
    """获取窗口透明度，返回 10-100。"""
    try:
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if not (ex_style & win32con.WS_EX_LAYERED):
            return 100
        cr_key = ctypes.c_ulong()
        alpha = ctypes.c_byte()
        flags = ctypes.c_ulong()
        _user32.GetLayeredWindowAttributes(
            hwnd, ctypes.byref(cr_key), ctypes.byref(alpha), ctypes.byref(flags),
        )
        if flags.value & 0x2:
            return max(10, min(100, int(alpha.value * 100 / 255)))
        return 100
    except Exception:
        return 100


def reset_opacity(hwnd: int) -> bool:
    """恢复窗口不透明。"""
    try:
        set_opacity(hwnd, 100)
        return True
    except Exception:
        return False

# ============================================================
# 窗口层级排序（Z-Order）
# ============================================================

def bring_to_front(hwnd: int) -> bool:
    """将窗口移到 Z-order 最前面（在所有置顶窗口之上）。"""
    try:
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
        )
        return True
    except Exception:
        return False


def set_zorder_relative(hwnd: int, insert_after_hwnd: int) -> bool:
    """将窗口放到指定窗口之后（调整层级）。"""
    try:
        win32gui.SetWindowPos(
            hwnd, insert_after_hwnd, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
        )
        return True
    except Exception:
        return False


# ============================================================
# 点击穿透（Click-Through）
# ============================================================

def set_click_through(hwnd: int, enabled: bool, current_opacity: int = None) -> bool:
    """设置窗口点击穿透。
    enabled=True: 鼠标点击穿透窗口，操作后面的内容
    enabled=False: 恢复正常
    current_opacity: 当前透明度（10-100），用于穿透和透明度共存。如果为None则自动获取。
    """
    try:
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if enabled:
            # 获取当前透明度（如果没传）
            if current_opacity is None:
                current_opacity = get_opacity(hwnd)
            # 同时设置 WS_EX_LAYERED 和 WS_EX_TRANSPARENT
            if not (ex_style & win32con.WS_EX_LAYERED):
                win32gui.SetWindowLong(
                    hwnd, win32con.GWL_EXSTYLE,
                    ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT,
                )
            else:
                win32gui.SetWindowLong(
                    hwnd, win32con.GWL_EXSTYLE,
                    ex_style | win32con.WS_EX_TRANSPARENT,
                )
            # 关键：用 LWA_ALPHA 设置透明度，这样点击穿透和透明度可以共存
            # 不需要 LWA_COLORKEY，WS_EX_TRANSPARENT 本身就会让鼠标穿透
            alpha = int(max(10, min(100, current_opacity)) * 255 / 100)
            _user32.SetLayeredWindowAttributes(hwnd, 0, alpha, 0x2)  # LWA_ALPHA
        else:
            # 移除 WS_EX_TRANSPARENT，保留 WS_EX_LAYERED
            new_style = ex_style & ~win32con.WS_EX_TRANSPARENT
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_style)
            # 恢复透明度属性
            if current_opacity is None:
                current_opacity = get_opacity(hwnd)
            if current_opacity < 100:
                set_opacity(hwnd, current_opacity)
            else:
                # 完全不透明时，移除分层样式以避免渲染问题
                if new_style & win32con.WS_EX_LAYERED:
                    win32gui.SetWindowLong(
                        hwnd, win32con.GWL_EXSTYLE,
                        new_style & ~win32con.WS_EX_LAYERED,
                    )
        return True
    except Exception:
        return False


def is_click_through(hwnd: int) -> bool:
    """判断窗口是否处于点击穿透状态。"""
    try:
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        return bool(ex_style & win32con.WS_EX_TRANSPARENT)
    except Exception:
        return False

# ============================================================
# 开机自启（注册表）
# ============================================================

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_VALUE_NAME = "WindowAnchor"


def set_auto_start(enable: bool, exe_path: str = None) -> bool:
    try:
        import winreg
        if exe_path is None:
            import sys
            exe_path = sys.executable
            if getattr(sys, "frozen", False):
                pass
            else:
                script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                script_path = os.path.join(script_dir, "windowanchor.pyw")
                pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                if os.path.exists(pythonw):
                    exe_path = f'"{pythonw}" "{script_path}"'
                else:
                    exe_path = f'"{sys.executable}" "{script_path}"'

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, _APP_VALUE_NAME, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, _APP_VALUE_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_auto_start_enabled() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, _APP_VALUE_NAME)
            winreg.CloseKey(key)
            return bool(value)
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False
