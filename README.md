# WindowAnchor

一个 Windows 上的窗口置顶小工具。

## 能干什么

- **窗口置顶**：全局热键一键置顶/取消，支持同时置顶多个窗口
- **透明度调节**：置顶的窗口可以调成半透明，看视频或者对照资料的时候好用
- **点击穿透**：开了之后鼠标能直接穿过去点后面的窗口，适合把参考资料搁在最前面
- **开机自启**：设置里勾一下就行
- **自定义热键**：置顶快捷键可以自己改

## 怎么用

### 直接用

打包好的 exe 双击就能跑，右下角托盘会出现一个小图钉图标。

默认热键是 `Ctrl+Shift+Space`，切到想置顶的窗口按一下就置顶了，再按一下取消。

右键托盘图标能看到所有功能：置顶当前窗口、调透明度、开点击穿透、设置。

### 跑源码

```bash
pip install -r requirements.txt
pythonw windowanchor.pyw
```

想带控制台看报错就用 `python -m windowanchor`。

### 自己打包 exe

双击 `build.bat`，打完在 `dist/WindowAnchor.exe`。

## 几个要注意的地方

- 只支持 Windows 10 / 11
- 有些程序（比如游戏、加速器这类）是以管理员权限跑的，这种窗口要置顶的话，WindowAnchor 也得右键"以管理员身份运行"才行
- 点击穿透开了之后，那个窗口就收不到鼠标事件了，想取消得去托盘菜单里操作

## 项目结构

```
WindowAnchor/
├── windowanchor/
│   ├── app.py               # 主控制器，把各个模块串起来
│   ├── config.py            # 配置读写，存在 %APPDATA%/WindowAnchor/
│   ├── hotkey.py            # 全局热键，独立线程跑消息循环
│   ├── pin_manager.py       # 置顶、透明度、点击穿透的状态管理
│   ├── settings_dialog.py   # 设置界面
│   ├── tray.py              # 系统托盘菜单
│   └── winapi.py            # 一堆 Windows API 的封装
├── windowanchor.pyw         # 无控制台入口
├── requirements.txt
├── WindowAnchor.spec        # PyInstaller 打包配置
├── build.bat                # 一键打包脚本
└── README.md
```

## 技术栈

Python 3.10+，PySide6 做界面，pywin32 + ctypes 调 Windows API。

## License

MIT，随便用。
