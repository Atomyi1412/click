#!/usr/bin/env python3
"""
Windows 打包脚本
使用 PyInstaller 将鼠标连点器打包成 Windows exe 文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_windows_exe():
    """构建 Windows exe 文件"""
    print("开始构建 Windows exe 文件...")

    # 平台校验：必须在 Windows 上打包
    if sys.platform != 'win32':
        print(f"❌ 当前平台为 {sys.platform}，不是 Windows。PyInstaller 无法跨平台生成 Windows 可执行文件。\n请在 Windows 10/11 64 位系统上运行本脚本后再分发 exe。")
        return False

    # 确保在正确的目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # 清理之前的构建文件
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    # 使用当前解释器调用 PyInstaller，避免因环境不同调用到错误的解释器
    py_exe = sys.executable or 'python'

    # PyInstaller 命令参数 - Windows 11 兼容版
    cmd = [
        py_exe, '-m', 'PyInstaller',
        '--onefile',  # 打包成单个文件
        '--windowed',  # 不显示控制台窗口
        '--name=MouseClicker_Win11',  # 使用英文名避免编码问题
        '--add-data=config_native.json:.',  # 包含配置文件
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui', 
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=pynput',
        '--hidden-import=pynput.mouse',
        '--hidden-import=pynput.keyboard',
        '--hidden-import=keyboard',
        '--noupx',  # 不使用 UPX 压缩，提高兼容性
        '--exclude-module=tkinter',  # 排除不需要的模块
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        'auto_clicker_native.py'
    ]

    # 如果没有图标文件，移除图标参数
    if not os.path.exists('icon.ico'):
        cmd = [arg for arg in cmd if not arg.startswith('--icon')]

    try:
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功！")
        print(result.stdout)

        # 检查输出文件（在 macOS 上生成的是无扩展名的可执行文件）
        exe_path = Path('dist/MouseClicker_Win11.exe')
        exec_path = Path('dist/MouseClicker_Win11')

        if exe_path.exists():
            print(f"\n✅ Windows 11 兼容版已生成: {exe_path.absolute()}")
            print(f"文件大小: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        elif exec_path.exists():
            print(f"\n✅ 可执行文件已生成: {exec_path.absolute()}")
            print(f"文件大小: {exec_path.stat().st_size / 1024 / 1024:.1f} MB")
            # 在某些环境可能生成无扩展名文件，重命名为 .exe
            exe_renamed = exec_path.with_suffix('.exe')
            exec_path.rename(exe_renamed)
            print(f"已重命名为: {exe_renamed.absolute()}")
        else:
            print("❌ 未找到生成的可执行文件")

    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller 未找到，请确保已正确安装")
        return False

    return True

def create_windows_package():
    """创建 Windows 发布包"""
    print("\n创建 Windows 发布包...")
    
    # 创建发布目录
    release_dir = Path('release/windows')
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制 exe 文件
    exe_source = Path('dist/MouseClicker_Win11.exe')
    if exe_source.exists():
        shutil.copy2(exe_source, release_dir / 'MouseClicker_Win11.exe')
        print(f"✅ 已复制 exe 文件到: {release_dir}")
        
        # 创建启动脚本
        launcher_script = release_dir / 'Start_MouseClicker.bat'
        launcher_content = '''@echo off
chcp 65001 >nul
echo Starting Mouse Clicker for Windows 11...
cd /d "%~dp0"
start "" "MouseClicker_Win11.exe"
'''
        
        with open(launcher_script, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        print(f"✅ 已创建启动脚本: {launcher_script}")
    else:
        print("❌ 未找到 exe 文件，无法创建发布包")
    
    # 复制说明文件
    readme_files = ['README.md', 'README_Windows.md']
    for readme in readme_files:
        if os.path.exists(readme):
            shutil.copy2(readme, release_dir)
    
    print(f"\n🎉 Windows 发布包已创建: {release_dir.absolute()}")

if __name__ == '__main__':
    print("=== 鼠标连点器 Windows 打包工具 ===")
    
    if build_windows_exe():
        create_windows_package()
        print("\n✅ Windows 打包完成！")
    else:
        print("\n❌ Windows 打包失败！")
        sys.exit(1)