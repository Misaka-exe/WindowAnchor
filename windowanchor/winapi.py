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
    """设置开机自启。enable=True 开启，False 关闭。"""
    try:
        import winreg
        import sys
        if exe_path is None:
            if getattr(sys, "frozen", False):
                # 打包后的 exe，确保路径加引号（处理含空格的路径）
                exe_path = f'"{sys.executable}"'
            else:
                # 源码运行，用 pythonw + 脚本路径
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
    except Exception as e:
        print(f"[set_auto_start] Error: {e}")
        return False


def get_auto_start_path() -> str:
    """获取注册表中当前的自启路径，不存在返回空字符串。"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, _APP_VALUE_NAME)
            winreg.CloseKey(key)
            return value or ""
        except FileNotFoundError:
            winreg.CloseKey(key)
            return ""
    except Exception:
        return ""


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


# ============================================================
# 屏幕与鼠标
# ============================================================

def get_screen_width() -> int:
    """获取主屏幕宽度。"""
    try:
        import ctypes
        return ctypes.windll.user32.GetSystemMetrics(0)
    except Exception:
        return 1920


def get_screen_height() -> int:
    """获取主屏幕高度。"""
    try:
        import ctypes
        return ctypes.windll.user32.GetSystemMetrics(1)
    except Exception:
        return 1080


def get_cursor_pos():
    """获取鼠标当前位置，返回 (x, y)。"""
    try:
        import ctypes
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return (pt.x, pt.y)
    except Exception:
        return (0, 0)


def get_work_area():
    """获取工作区矩形（排除任务栏），返回 (left, top, right, bottom) 或 None。"""
    try:
        import ctypes
        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
        rect = RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
        return (rect.left, rect.top, rect.right, rect.bottom)
    except Exception:
        return None


# ============================================================
# 窗口移动与显示
# ============================================================

def move_window(hwnd: int, x: int, y: int, width: int, height: int) -> bool:
    """移动并调整窗口大小。"""
    try:
        import ctypes
        ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, width, height, 0x0004 | 0x0010)
        return True
    except Exception:
        return False


def get_window_rect(hwnd: int):
    """获取窗口矩形，返回 (left, top, right, bottom) 或 None。"""
    try:
        import ctypes
        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
        rect = RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.left, rect.top, rect.right, rect.bottom)
    except Exception:
        return None


def hide_window(hwnd: int) -> bool:
    """隐藏窗口。"""
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        return True
    except Exception:
        return False


def show_window(hwnd: int) -> bool:
    """显示窗口。"""
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(hwnd, 9)
        ctypes.windll.user32.ShowWindow(hwnd, 5)
        return True
    except Exception:
        return False


def is_window_visible(hwnd: int) -> bool:
    """检查窗口是否可见。"""
    try:
        import ctypes
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
        return bool(style & 0x10000000)
    except Exception:
        return True


# ============================================================
# 系统音频（静音）
# ============================================================

def mute_system_audio(mute: bool) -> bool:
    """系统静音/取消静音。需要 pycaw + comtypes 库。"""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1 if mute else 0, None)
        return True
    except Exception:
        return False


def mute_process_audio(pid: int, mute: bool) -> bool:
    """对指定进程及其所有子进程的音频会话进行静音/取消静音。"""
    if not pid:
        return False
    try:
        import ctypes
        from ctypes import POINTER, cast
        from comtypes import CLSCTX_ALL
        
        # COM 线程初始化：每个使用 COM 的线程必须先初始化
        # 热键线程是新建的，没有初始化 COM，这里必须手动初始化
        COINIT_MULTITHREADED = 0x0
        COINIT_APARTMENTTHREADED = 0x2
        hr = ctypes.windll.ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
        # S_OK = 0, S_FALSE = 1, RPC_E_CHANGED_MODE = 0x80010106
        # 只要不是致命错误就继续
        if hr < 0 and hr != 0x80010106:
            return False
        
        try:
            from pycaw.pycaw import AudioUtilities
            import psutil
            
            # 获取目标进程及其所有子进程的 PID
            target_pids = set()
            target_pids.add(pid)
            try:
                parent = psutil.Process(pid)
                for child in parent.children(recursive=True):
                    target_pids.add(child.pid)
            except Exception:
                pass
            
            # 遍历所有音频会话，对目标进程的会话进行静音
            sessions = AudioUtilities.GetAllSessions()
            found = False
            for session in sessions:
                try:
                    # 有些会话的 Process 是 None（系统会话等）
                    if not session.Process:
                        continue
                    session_pid = session.Process.pid
                    if session_pid in target_pids:
                        session.SimpleAudioVolume.SetMute(1 if mute else 0, None)
                        found = True
                except Exception:
                    continue
            return found
        finally:
            ctypes.windll.ole32.CoUninitialize()
    except Exception:
        return False


def get_window_pid(hwnd: int) -> int:
    """获取窗口对应的进程 ID。"""
    try:
        import ctypes
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value
    except Exception:
        return 0
