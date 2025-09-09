#!/usr/bin/env python3
"""
Windows Build Script
Use PyInstaller to package mouse clicker into Windows exe file
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_windows_exe():
    """Build Windows exe file"""
    print("Starting Windows exe build...")

    # Platform validation: must build on Windows
    if sys.platform != 'win32':
        print(f"[ERROR] Current platform is {sys.platform}, not Windows. PyInstaller cannot cross-compile Windows executables.\nPlease run this script on Windows 10/11 64-bit system.")
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
        print(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(result.stdout)

        # Check output files (executable without extension on macOS)
        exe_path = Path('dist/MouseClicker_Win11.exe')
        exec_path = Path('dist/MouseClicker_Win11')

        if exe_path.exists():
            print(f"\n[SUCCESS] Windows 11 compatible version generated: {exe_path.absolute()}")
            print(f"File size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        elif exec_path.exists():
            print(f"\n[SUCCESS] Executable file generated: {exec_path.absolute()}")
            print(f"File size: {exec_path.stat().st_size / 1024 / 1024:.1f} MB")
            # Rename to .exe if generated without extension
            exe_renamed = exec_path.with_suffix('.exe')
            exec_path.rename(exe_renamed)
            print(f"Renamed to: {exe_renamed.absolute()}")
        else:
            print("[ERROR] Generated executable file not found")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("[ERROR] PyInstaller not found, please ensure it is properly installed")
        return False

    return True

def create_windows_package():
    """Create Windows release package"""
    print("\nCreating Windows release package...")
    
    # Create release directory
    release_dir = Path('release/windows')
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy exe file
    exe_source = Path('dist/MouseClicker_Win11.exe')
    if exe_source.exists():
        shutil.copy2(exe_source, release_dir / 'MouseClicker_Win11.exe')
        print(f"[SUCCESS] Copied exe file to: {release_dir}")
        
        # Create launcher script
        launcher_script = release_dir / 'Start_MouseClicker.bat'
        launcher_content = '''@echo off
chcp 65001 >nul
echo Starting Mouse Clicker for Windows 11...
cd /d "%~dp0"
start "" "MouseClicker_Win11.exe"
'''
        
        with open(launcher_script, 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        print(f"[SUCCESS] Created launcher script: {launcher_script}")
    else:
        print("[ERROR] Exe file not found, cannot create release package")
    
    # Copy documentation files
    readme_files = ['README.md', 'README_Windows.md']
    for readme in readme_files:
        if os.path.exists(readme):
            shutil.copy2(readme, release_dir)
    
    print(f"\n[INFO] Windows release package created: {release_dir.absolute()}")

if __name__ == '__main__':
    print("=== Mouse Clicker Windows Build Tool ===")
    
    if build_windows_exe():
        create_windows_package()
        print("\n[SUCCESS] Windows build completed!")
    else:
        print("\n[ERROR] Windows build failed!")
        sys.exit(1)