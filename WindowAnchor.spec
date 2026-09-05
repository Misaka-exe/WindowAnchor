# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build config - safe and stable."""
block_cipher = None

# Conservative excludes - only modules we definitely don't need
# Keep QtNetwork/QtXml/QtSvg/QtPrintSupport - they are Qt internal dependencies
excludes = [
    # Heavy PySide6 modules we definitely don't use
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineQuick', 'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets', 'PySide6.Qt3DCore',
    'PySide6.Qt3DRender', 'PySide6.Qt3DInput', 'PySide6.Qt3DLogic',
    'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras', 'PySide6.QtBluetooth',
    'PySide6.QtNfc', 'PySide6.QtPositioning', 'PySide6.QtLocation',
    'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtCharts',
    'PySide6.QtDataVisualization', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
    'PySide6.QtQuick3D', 'PySide6.QtQuickWidgets', 'PySide6.QtTest',
    'PySide6.QtSql', 'PySide6.QtQml', 'PySide6.QtQuick',
    'PySide6.QtQuickControls2', 'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets',
    'PySide6.QtXmlPatterns',
    'PySide6.QtHelp', 'PySide6.QtDesigner', 'PySide6.QtUiTools',
    'PySide6.QtScript', 'PySide6.QtScriptTools',
    # Standard library modules we don't need
    'tkinter', 'unittest', 'pydoc', 'doctest',
    'test', 'pydoc_data', 'lib2to3', 'ensurepip',
    'distutils', 'setuptools', 'pkg_resources',
    'pip', 'wheel',
]

a = Analysis(
    ['windowanchor.pyw'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='WindowAnchor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/tray.ico',
)
