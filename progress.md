# ⚠️ 项目上下文记录文件 — 必读规则

> **新开对话必须先完整阅读本文件，不得跳过。**
>
> **标记【已确认】的内容不得擅自更改，如需变更必须先询问用户。**
>
> **每次交付后必须更新本文件（版本历史、待办状态、踩坑记录、最后更新日期）。**
>
> **删代码前必须先全局搜索引用，确认没有地方还在调用旧版本。**
>
> **每次交付前必须执行 6 项自验证：语法检查、导入检查、引用检查、逻辑检查、配置检查、文档检查，全部通过后才能打包交付。**

---

## 1. 项目基本信息

| 项目 | 内容 |
|------|------|
| 名称 | WindowAnchor |
| 当前版本 | 2.0 |
| 技术栈 | Python 3.10+ / PySide6 / pywin32 |
| 目标平台 | Windows 10 / 11 |
| 最后更新日期 | 2026-09-11 |
| 原项目 | https://github.com/feng-pip/PinToTop （MIT协议，仅1 commit，功能极简） |
| 用户GitHub | Misaka-exe |
| 仓库地址 | https://github.com/Misaka-exe/WindowAnchor |
| 用户本地路径 | `C:\Users\WJC\Desktop\WindowAnchor` |
| 项目工作目录 | `/home/user/.super_doubao/super-doubao-runtime/workspace/WindowAnchor-2.0/` |
| 打包文件 | `/home/user/.super_doubao/super-doubao-runtime/workspace/WindowAnchor-2.0.zip` |

---

## 2. 已完成功能

### 2.1 核心功能（1.0 就有）

| 功能 | 状态 | 验证情况 | 已知问题 |
|------|------|---------|---------|
| 窗口置顶/取消置顶 | ✅ 完成 | 已验证可用 | 以管理员权限运行的程序（游戏、加速器等）需要 WindowAnchor 也以管理员身份运行才能置顶 |
| 全局热键置顶 | ✅ 完成 | 已验证可用 | 默认 Ctrl+Shift+Space，可在设置里自定义 |
| 同时置顶多个窗口 | ✅ 完成 | 已验证可用 | 无 |
| 透明度调节 | ✅ 完成 | 已验证可用 | 在已置顶窗口子菜单里调节，0-100% |
| 点击穿透 | ✅ 完成 | 已验证可用 | 开启后窗口收不到鼠标事件，想取消得去托盘菜单操作 |
| 开机自启 | ✅ 完成 | 已验证可用 | 写入注册表，可在设置里开关 |
| 托盘菜单 | ✅ 完成 | 已验证可用 | 可撕下成独立窗口（2.0新增） |

### 2.2 2.0 新增功能

| 功能 | 状态 | 验证情况 | 已知问题 |
|------|------|---------|---------|
| 靠边收起（类似QQ停靠） | ✅ 完成 | 已验证可用 | 只支持主屏幕，多显示器暂不支持 |
| 每个窗口单独控制靠边收起 | ✅ 完成 | 已验证可用 | 在已置顶窗口子菜单里勾选 |
| 收起方向选择（自动/左/右/上/下） | ✅ 完成 | 已验证可用 | 自动方向选最近的边 |
| 靠边收起平滑动画 | ✅ 完成 | 已验证可用 | 200ms，ease-out 缓动，约60fps |
| 拖动离开边缘不再自动收起 | ✅ 完成 | 已验证可用 | 再次拖到同方向边缘会在新位置收起 |
| 老板键（一键隐藏所有置顶窗口） | ✅ 完成 | 已验证可用 | 默认 Ctrl+Shift+H，可自定义；隐藏时托盘图标变红 |
| 老板键静音功能 | ⚠️ 部分完成 | 代码已写，需额外装 pycaw + comtypes | 不装也能用，只是隐藏时不会自动静音 |
| 托盘菜单可撕下 | ✅ 完成 | 刚加，待用户验证 | 拖动菜单顶部小横条可撕成独立窗口，撕下后不自动关闭 |
| 托盘菜单操作不弹通知 | ✅ 完成 | 刚加，待用户验证 | 托盘菜单操作不弹通知，热键操作才弹，避免遮挡菜单 |

---

## 3. 关键决策【已确认】

### 3.1 已删除的功能【已确认，不得恢复】

| 决策 | 原因 | 不能改的点 |
|------|------|-----------|
| 彻底删除上下移/层级排序功能 | 用户明确要求删除，该功能体验不好 | 不得在任何地方恢复层级排序相关代码 |
| 彻底删除标题栏右键菜单功能 | 在 Chrome/Edge/VS Code/微信等自绘标题栏的现代应用上无法工作（应用本身限制） | 不得恢复系统菜单集成相关代码 |
| 删除 Ctrl+Shift+滚轮调节透明度功能 | 用户明确要求删除 | 不得恢复滚轮调节透明度 |
| 设置界面只保留靠边收起勾选框 | 用户明确要求删除"收起后露出宽度"和"触发收起的边缘距离"两个数值设置项 | 不得在设置界面恢复这两个设置项（后端配置项保留，使用默认值） |
| 删除托盘菜单"窗口靠边收起（当前窗口）"菜单项 | 用户明确要求删除 | 不得在托盘菜单根目录恢复这个菜单项（已置顶窗口子菜单里的靠边收起保留） |

### 3.2 行为决策【已确认】

| 决策 | 原因 | 不能改的点 |
|------|------|-----------|
| 靠边收起展开后在边缘位置展开，不是恢复到原始位置 | 符合 QQ 停靠行为，避免展开后鼠标不在窗口内导致闪烁 | 展开位置必须在屏幕内的边缘位置（左展开 left=0，右展开 left=screen_width-width） |
| 拖动窗口离开边缘后不再自动收起 | 用户需求，展开后拖到别的地方用不应该又收回去 | 检测到位置变化且不在边缘附近时，从 _docked_windows 移除但保留启用状态 |
| 托盘菜单操作不弹通知，热键操作才弹 | 避免通知遮挡托盘菜单；托盘菜单里的勾选状态就是反馈 | 所有托盘菜单信号连接必须传 show_notification=False，热键用默认 True |
| 靠边收起防误触发用 2 像素容差 | Windows 的 GetWindowRect 每次返回有 1-2 像素微小波动，完全相等判断会导致永远不相等 | _rect_almost_equal 的 tolerance 默认 2 像素 |
| 靠边收起方向检测选最近的边 | 按 left→right→top→bottom 顺序判断会导致大窗口同时靠近多个边时优先返回 left | _detect_edge 必须计算四边距离返回最近的 |
| set_dock_enabled 禁用时不清理方向配置 | 禁用再启用后方向配置应该还在，否则用户选好的方向会丢失变回 auto | 禁用时不得调用 _window_directions.pop |
| set_dock_direction 先判断 new_edge 有效再 pop | 先 pop 后判断会导致 direction=auto 且 original_rect 不在边缘附近时窗口意外失去收起状态 | 必须先确定 new_edge 有效，再操作 _docked_windows |
| 打包用保守 excludes + strip=False | 排除 QtXml 等 Qt 内部依赖 + strip=True 会导致 exe 运行时报"无法定位序数 380"错误 | spec 文件只排除 QtWebEngine/QtMultimedia/Qt3D 等确定不需要的模块，strip=False |
| build.bat 全部用英文 | 中文注释在 cmd 里会乱码被当成命令执行 | build.bat 里不得出现中文 |

---

## 4. 待办事项

| 优先级 | 事项 | 状态 | 备注 |
|--------|------|------|------|
| P0 | 2.0 版本基本功能稳定 | ✅ 完成 | |
| P1 | 靠边收起功能 | ✅ 完成 | 含方向选择、平滑动画、拖动离开不收起 |
| P1 | 老板键功能 | ✅ 完成 | 含自定义热键 |
| P1 | 托盘菜单可撕下 | ✅ 完成 | 刚加，待用户验证 |
| P1 | 托盘菜单操作不弹通知 | ✅ 完成 | 刚加，待用户验证 |
| P1 | 设置对话框非模态化 | ⏸️ 暂缓 | 用户说"先不做，我再看看效果"，改完设置不关闭，方便多次更改 |
| P1 | 2.0 版本推送到 GitHub | ⏳ 待做 | 当前 GitHub 上还是 1.0 版本的代码和 Release |
| P1 | 创建 2.0 GitHub Release | ⏳ 待做 | |
| P2 | 窗口贴靠分屏（snap_manager） | 💡 待审核 | 代码已从项目移除，待用户审核决定是否做 |
| P2 | 特定程序启动自动置顶规则 | 💡 待审核 | |
| P2 | 置顶窗口分组管理 | 💡 待审核 | |
| P2 | 多显示器支持 | 💡 待审核 | 当前靠边收起只支持主屏幕 |
| P2 | 老板键静音功能完善 | ⚠️ 部分完成 | 需用户确认是否需要（要额外装 pycaw + comtypes） |
| P2 | exe 体积优化 | ⏸️ 暂缓 | 用户之前说"忽略压缩的问题"，当前 44.9MB，装 UPX 可降到 20-25MB |

---

## 5. 踩坑记录（最重要！防止重复犯）

### 5.1 语法/导入类

| 坑 | 现象 | 解决方案 |
|----|------|---------|
| 中文引号语法错误 | pyw 文件无法打开，报 SyntaxError | 代码里必须用英文引号，不得用中文引号 |
| ctypes.wintypes 未导入 | 报 AttributeError: module 'ctypes' has no attribute 'wintypes' | 使用 ctypes.wintypes 前必须先 import ctypes.wintypes |
| ConfigManager.get() 不支持默认值参数 | 报 TypeError: ConfigManager.get() takes 2 positional arguments but 3 were given | 必须先给 ConfigManager.get() 方法添加默认值参数支持 |
| spec 排除 QtXml + strip=True | exe 运行时报"无法定位序数 380 于动态链接库" | 只排除 QtWebEngine/QtMultimedia/Qt3D 等确定不需要的模块，strip=False |
| build.bat 中文注释 | cmd 里中文乱码被当成命令执行，报一堆错误 | build.bat 全部用英文，不得出现中文 |

### 5.2 功能逻辑类

| 坑 | 现象 | 解决方案 |
|----|------|---------|
| 托盘菜单同一窗口重复显示多次 | 已置顶窗口列表里同一个窗口出现多次 | 重建菜单前必须清空动态项列表，去重已置顶窗口列表 |
| 热键录制失效 | 录制热键后不生效 | HotkeyRecorder 默认值 (0,0) 会覆盖配置，必须正确处理默认值 |
| 系统菜单命令 ID 处理错误 | 标题栏右键菜单点击后无反应 | 命令 ID 不能用 `cmd = wparam & 0xFFF0`，会把 0x8003/0x8004/0x8005 全部变成 0x8000；必须直接比较完整 ID |
| 穿透与透明度无法共存 | 调节透明度后点击穿透被取消 | set_opacity 旧代码会先取消穿透，必须修改为调节透明度时保留穿透状态 |
| 删除系统菜单代码时误删工具函数 | 删除标题栏右键菜单功能后，其他功能报错 | 删代码前必须全局搜索引用，确认工具函数没有被其他地方调用 |
| 两个 HotkeyThread 实例冲突 | 置顶热键和老板键热键同时注册时其中一个不生效 | 两个 HotkeyThread 实例不能使用相同窗口类名，必须通过 name 参数区分 |
| 老板键隐藏 0 个窗口 | 按老板键后弹窗显示"隐藏 0 个窗口"，实际已置顶的窗口没被隐藏 | pin_manager.list_pinned() 返回 [(hwnd, title), ...] 元组列表，boss_key.hide() 里写成 `for hwnd in pinned` 把元组当句柄传入 is_window() 导致全部失败；必须改为 `for hwnd, title in pinned` |
| 靠边收起无法收起 | 窗口拖到边缘后永远不收起 | 防误触发逻辑用 `pending["rect"] == rect` 完全相等判断，Windows 的 GetWindowRect 每次返回有 1-2 像素微小波动导致永远不相等、计时永远不超时；必须用 _rect_almost_equal() 加 2 像素容差 |
| 固定方向不生效，始终左侧 | 选了右/上/下方向，实际收起方向始终是左侧 | 三个原因：①set_dock_enabled 禁用时调用 _window_directions.pop 清理方向配置，导致用户选好方向后如果不小心取消再启用，方向丢失变回 auto；②_detect_edge 按 left→right→top→bottom 顺序判断，大窗口同时靠近多个边时优先返回 left，而不是实际最近的边；③set_dock_direction 里先 _docked_windows.pop 再判断 new_edge，当 direction=auto 且 original_rect 不在边缘附近时 _detect_edge 返回 None，导致窗口意外失去收起状态。修复：禁用时不清理方向配置；_detect_edge 改为计算四边距离返回最近的；set_dock_direction 改为先判断 new_edge 有效再 pop |
| 展开位置错误+闪烁 | 选固定方向后鼠标在右边缘触发展开，但窗口实际在左边展开；鼠标一直放边缘页面会反复展开/收起闪烁 | _expand_window 恢复到 original_rect（窗口收起前的位置，可能在屏幕中间），而不是在边缘附近展开，不符合 QQ 停靠行为；且展开后鼠标不在窗口内（鼠标在边缘 x=5，窗口 left=500），0.5 秒后又收起，然后鼠标还在边缘又展开，反复循环。修复：_expand_window 改为移到屏幕内的边缘位置（左展开 left=0，右展开 left=screen_width-width）；_undock_window（取消停靠）才恢复到 original_rect；展开后额外加保护：鼠标还在触发展开的屏幕边缘时保持展开不开始收起计时 |
| 靠边收起动画闪烁/卡顿 | 动画过程中窗口位置跳动 | 动画过程中必须跳过鼠标/窗口检测逻辑，避免检测逻辑干扰动画；用 _is_animating(hwnd) 判断，正在动画时 continue |

### 5.3 打包/发布类

| 坑 | 现象 | 解决方案 |
|----|------|---------|
| PyInstaller 打包找不到图标 | 报 FileNotFoundError: Icon input file ... assets\tray.ico not found | spec 文件里的图标路径必须用相对路径，且打包时工作目录要正确 |
| exe 体积 44.9MB | 用户觉得太大 | 装 UPX 可降到 20-25MB，但用户说"忽略压缩的问题" |
| GitHub 仓库上传了 build/dist 临时文件 | 仓库里有不该上传的文件夹 | 添加 .gitignore，排除 build/、dist/、__pycache__/、*.pyc、*.spec（保留 WindowAnchor.spec） |

---

## 6. 未解决的问题

| 问题 | 复现步骤 | 疑似原因 | 状态 |
|------|---------|---------|------|
| 特定软件（如雷神加速器）置顶/靠边收起无效 | 1. 以管理员身份运行雷神加速器 2. 用 WindowAnchor 置顶该窗口 3. 置顶不生效 | 以管理员权限运行的程序，需要 WindowAnchor 也以管理员身份运行才能操作其窗口（Windows UAC 权限隔离） | 已知限制，非 bug，README 已说明 |
| 靠边收起只支持主屏幕 | 1. 把窗口拖到副屏幕边缘 2. 不会触发靠边收起 | 当前代码只获取主屏幕尺寸，没有处理多显示器 | 待做（P2） |
| 老板键静音功能需额外依赖 | 1. 在设置里开启老板键静音 2. 按老板键 3. 不会静音 | 需要额外安装 pycaw + comtypes 库，默认不装 | 待用户确认是否需要 |

---

## 7. 明确不做的事【已确认】

1. **联网功能、AI API 接入** — 用户明确要求不做
2. **上下移/层级排序功能** — 用户明确要求彻底删除
3. **标题栏右键菜单功能** — 在自绘标题栏应用上无法工作，用户明确要求彻底删除
4. **Ctrl+Shift+滚轮调节透明度** — 用户明确要求删除
5. **时间追踪工具（TimeTracker）** — 用户暂时搁置
6. **截图/剪贴板管理/图片压缩/待办清单** — 已有成熟竞品，用户排除
7. **设置界面里的靠边收起数值设置项** — 用户明确要求只保留勾选框

---

## 8. 技术上下文

### 8.1 项目结构

```
WindowAnchor-2.0/
├── windowanchor/              # 主包
│   ├── __init__.py            # 版本号定义（当前 2.0.0）
│   ├── __main__.py            # python -m windowanchor 入口
│   ├── app.py                 # 主控制器，连接所有模块
│   ├── config.py              # JSON 配置持久化（%APPDATA%/WindowAnchor/config.json）
│   ├── hotkey.py              # 全局热键线程（支持自定义 name 参数避免多实例冲突）
│   ├── pin_manager.py         # 置顶/透明度/点击穿透管理
│   ├── dock_manager.py        # 靠边收起（含平滑动画）
│   ├── boss_key.py            # 老板键（一键隐藏所有置顶窗口）
│   ├── settings_dialog.py     # 设置界面（含热键录制器）
│   ├── tray.py                # 系统托盘菜单（可撕下）
│   └── winapi.py              # Windows API 封装
├── assets/
│   └── tray.ico               # 蓝色图钉图标
├── windowanchor.pyw           # 无控制台入口（日常使用）
├── requirements.txt           # 依赖列表
├── WindowAnchor.spec          # PyInstaller 配置（保守 excludes + strip=False）
├── build.bat                  # 一键打包（全英文）
├── README.md                  # 使用说明（去 AI 化风格）
└── progress.md                # 本文件，项目上下文记录
```

### 8.2 关键文件作用

| 文件 | 作用 | 关键类/函数 |
|------|------|------------|
| `app.py` | 主控制器，初始化所有模块，连接信号 | AppController，_on_toggle_current(show_notification=True)，_on_boss_key_pressed(show_notification=True) |
| `config.py` | 配置持久化，JSON 格式 | ConfigManager，get(key, default=None)，set(key, value) |
| `hotkey.py` | 全局热键，独立线程 | HotkeyThread(name="...")，必须传不同 name 避免多实例冲突 |
| `pin_manager.py` | 置顶/透明度/点击穿透 | PinManager，pin(hwnd)，unpin(hwnd)，set_opacity(hwnd, value)，toggle_click_through(hwnd) |
| `dock_manager.py` | 靠边收起，含平滑动画 | DockManager，set_dock_enabled(hwnd, enabled)，set_dock_direction(hwnd, direction)，_expand_window(hwnd)（在边缘位置展开），_hide_window(hwnd)（动画收起），_start_animation(hwnd, from_rect, to_rect)，_ease_out(t) |
| `boss_key.py` | 老板键 | BossKeyManager，toggle()，hide()，restore()，注意 list_pinned() 返回元组列表必须解包 |
| `settings_dialog.py` | 设置界面 | SettingsDialog，HotkeyRecorder，靠边收起只保留勾选框 |
| `tray.py` | 系统托盘菜单 | TrayManager，setTearOffEnabled(True)，show_message(title, msg, duration) |
| `winapi.py` | Windows API 封装 | get_window_rect(hwnd)，move_window(hwnd, x, y, w, h)，is_window(hwnd)，get_screen_width/height() |

### 8.3 关键配置项（config.json）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| hotkey_modifiers | 0x0006 (Ctrl+Shift) | 置顶热键修饰键 |
| hotkey_key | 0x20 (Space) | 置顶热键 |
| hotkey_display | "Ctrl+Shift+Space" | 热键显示文本 |
| default_opacity | 100 | 默认透明度 |
| remember_opacity | True | 记住每个窗口的透明度 |
| auto_start | False | 开机自启 |
| show_startup_message | True | 显示启动提示 |
| unpin_on_exit | True | 退出时自动取消所有置顶 |
| auto_restore_topmost | True | 自动恢复丢失的置顶状态 |
| restore_interval | 1 | 置顶状态检查间隔（秒） |
| dock_enabled | True | 启用靠边收起功能（全局开关） |
| dock_width | 3 | 收起后露出的边宽度（像素），设置界面已删除此项，使用默认值 |
| dock_threshold | 10 | 触发收起的边缘阈值（像素），设置界面已删除此项，使用默认值 |
| boss_key_enabled | True | 启用老板键 |
| boss_key_modifiers | 0x0006 (Ctrl+Shift) | 老板键修饰键 |
| boss_key_key | 0x48 (H) | 老板键 |
| boss_key_display | "Ctrl+Shift+H" | 老板键显示文本 |
| boss_key_mute | False | 老板键隐藏时同时静音（需 pycaw + comtypes） |

### 8.4 靠边收起关键参数（类常量，不可配置）

| 参数 | 值 | 说明 |
|------|-----|------|
| DOCK_DELAY | 0.3 秒 | 防误触发：窗口必须停止移动 300ms 才会收起 |
| ANIMATION_DURATION | 200ms | 靠边收起/展开动画时长 |
| ANIMATION_INTERVAL | 16ms | 动画帧间隔（约 60fps） |
| 展开后收起延迟 | 0.5 秒 | 鼠标离开窗口后 500ms 自动收起 |

### 8.5 常用命令

```bash
# 运行（带控制台调试）
python -m windowanchor

# 运行（无控制台，日常使用）
pythonw windowanchor.pyw

# 打包
pyinstaller --clean WindowAnchor.spec
# 或双击 build.bat
# 输出：dist/WindowAnchor.exe

# 打包 zip（序号和文件名保持一致）
cd /home/user/.super_doubao/super-doubao-runtime/workspace
rm -f WindowAnchor-2.0.zip
zip -r WindowAnchor-2.0.zip WindowAnchor-2.0 -x "*/__pycache__/*" "*.pyc"
```

### 8.6 信号连接速查（app.py）

| 信号 | 连接 | show_notification |
|------|------|-------------------|
| tray.toggle_requested | _on_toggle_current | False（托盘操作） |
| tray.unpin_requested | _on_unpin | False（托盘操作） |
| tray.unpin_all_requested | _on_unpin_all | False（托盘操作） |
| tray.click_through_toggled | _on_click_through_toggled | False（托盘操作） |
| tray.dock_toggle_requested | _on_dock_toggle | False（托盘操作） |
| tray.dock_toggle_window_requested | _on_dock_toggle_window | False（托盘操作） |
| tray.dock_direction_requested | _on_dock_direction | False（托盘操作） |
| tray.boss_key_requested | _on_boss_key_pressed | False（托盘操作） |
| hotkey.triggered | _on_toggle_current | True（默认，热键操作） |
| boss_key_hotkey.triggered | _on_boss_key_pressed | True（默认，热键操作） |

---

## 9. 版本历史

### v2.0（当前版本）

**最后更新：2026-09-12**

#### 2026-09-12 更新
- 修改：托盘菜单 tear-off 虚线横条改成右上角图钉图标（自定义 PinMenu 类，重写 paintEvent）
- 修改：确认收起和展开位置严格对齐（左收起右展开、右收起左展开）

#### 2026-09-11 更新
- 新增：托盘菜单可撕下功能（setTearOffEnabled(True)），拖动菜单顶部小横条可撕成独立窗口，撕下后不自动关闭
- 新增：托盘菜单操作不弹通知，热键操作才弹通知（所有托盘菜单信号连接传 show_notification=False）
- 修改：README 添加托盘菜单可撕下说明

#### 2026-09-10 更新
- 新增：靠边收起平滑动画（200ms，ease-out 缓动，约60fps）
- 新增：拖动窗口离开边缘后不再自动收起，再次拖到同方向边缘时在新位置收起
- 修改：_expand_window 改为在屏幕内边缘位置展开（不是恢复到 original_rect）
- 修改：展开后鼠标还在边缘时保持展开，不开始收起计时（防止闪烁）
- 修改：设置界面靠边收起部分只保留勾选框，删除"收起后露出宽度"和"触发收起的边缘距离"两个数值设置项
- 修改：删除托盘菜单"窗口靠边收起（当前窗口）"菜单项
- 修改：所有版本号从 v1.0 改为 v2.0
- 修复：固定方向不生效，始终左侧（三个根因：禁用时清理方向配置、_detect_edge 按顺序判断、set_dock_direction 先 pop 后判断）
- 修复：展开位置错误+闪烁（_expand_window 恢复到 original_rect 而非边缘位置）
- 修复：老板键隐藏 0 个窗口（list_pinned 返回元组未解包）
- 修复：靠边收起无法收起（防误触发位置完全相等判断+Windows微小波动，改用 2 像素容差）

### v1.0（已发布到 GitHub）

**发布日期：2026-09-09**

- 基础功能：窗口置顶/取消置顶、全局热键、同时置顶多个窗口
- 透明度调节、点击穿透、开机自启
- 托盘菜单、设置界面
- GitHub 仓库创建：https://github.com/Misaka-exe/WindowAnchor
- GitHub Release v1.0 发布，含 WindowAnchor.exe（44.9MB）

---

*本文件每次交付后必须更新。新开对话必须先完整阅读本文件。*
