# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件
用于自定义打包参数和依赖处理
"""

import sys
from pathlib import Path

# 获取当前目录
project_dir = Path.cwd()

# 分析主脚本
a = Analysis(
    ['auto_clicker_native.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        # 包含配置文件
        ('config_native.json', '.'),
        # 如果有其他资源文件，在这里添加
    ],
    hiddenimports=[
        # PyQt5 相关
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        
        # 鼠标和键盘控制
        'pynput',
        'pynput.mouse',
        'pynput.keyboard',
        'pynput._util',
        'pynput._util.darwin',
        'keyboard',
        
        # macOS 特定模块
        'AppKit',
        'Quartz',
        'CoreFoundation',
        'objc',
        
        # 其他可能需要的模块
        'json',
        'threading',
        'time',
        'os',
        'sys',
        'configparser',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小文件大小
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 处理收集的文件
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 根据平台选择不同的打包方式
if sys.platform == 'win32':
    # Windows 打包为单个 exe 文件
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='鼠标连点器',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # 不显示控制台窗口
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='icon.ico' if Path('icon.ico').exists() else None,
    )
else:
    # macOS/Linux 打包为目录结构
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='鼠标连点器',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='鼠标连点器',
    )
    
    # macOS 特定：创建 app bundle
    if sys.platform == 'darwin':
        app = BUNDLE(
            coll,
            name='鼠标连点器.app',
            icon='icon.icns' if Path('icon.icns').exists() else None,
            bundle_identifier='com.autoclicker.native',
            info_plist={
                'CFBundleName': '鼠标连点器',
                'CFBundleDisplayName': '鼠标连点器',
                'CFBundleVersion': '1.0.0',
                'CFBundleShortVersionString': '1.0.0',
                'NSHighResolutionCapable': True,
                'NSAppleEventsUsageDescription': '此应用需要辅助功能权限来实现全局热键功能',
                'NSAccessibilityUsageDescription': '此应用需要辅助功能权限来监听全局按键事件',
                'LSMinimumSystemVersion': '10.13.0',
            },
        )