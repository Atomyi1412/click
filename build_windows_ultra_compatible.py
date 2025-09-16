#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Ultra Compatible Build Script
解决Python DLL加载失败问题的超兼容构建脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_windows_ultra_compatible_exe():
    """构建Windows超兼容版本可执行文件"""
    
    # 设置Windows控制台编码为UTF-8
    if sys.platform == 'win32':
        os.system('chcp 65001')
    
    print("[INFO] Starting Windows ultra compatible build...")
    
    # 检查平台
    if sys.platform != 'win32':
        print(f"[ERROR] Current platform is {sys.platform}, not Windows. Please run this script on Windows 10/11 64-bit system to generate real Windows executable.")
        return False
    
    # 确保输出目录存在
    dist_dir = Path('dist')
    dist_dir.mkdir(exist_ok=True)
    
    # PyInstaller 命令参数 - 超兼容配置
    cmd = [
        'pyinstaller',
        '--onefile',  # 单文件模式，避免DLL路径问题
        '--windowed',  # 不显示控制台窗口
        '--name=MouseClicker_UltraCompat',  # 使用英文名避免路径编码问题
        '--distpath=dist',  # 输出目录
        '--workpath=build',  # 工作目录
        '--specpath=.',  # spec文件路径
        # 多位置版本使用用户目录下的配置文件，不需要打包配置文件
        
        # Python运行时包含
        '--collect-all=encodings',  # 包含所有编码
        '--collect-all=locale',     # 包含本地化支持
        '--collect-all=ctypes',     # 包含ctypes库
        '--collect-all=_ctypes',    # 包含底层ctypes
        
        # PyQt5 完整包含
        '--collect-all=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui', 
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.sip',
        '--hidden-import=PyQt5.QtPrintSupport',
        '--hidden-import=sip',
        
        # pynput 完整包含
        '--collect-all=pynput',
        '--hidden-import=pynput',
        '--hidden-import=pynput.mouse',
        '--hidden-import=pynput.keyboard',
        '--hidden-import=pynput._util',
        '--hidden-import=pynput._util.win32',
        '--hidden-import=pynput._util.win32_vks',
        
        # keyboard 库
        '--collect-all=keyboard',
        '--hidden-import=keyboard',
        
        # 标准库
        '--hidden-import=json',
        '--hidden-import=threading',
        '--hidden-import=time',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=configparser',
        '--hidden-import=pathlib',
        '--hidden-import=subprocess',
        '--hidden-import=shutil',
        
        # Windows特定库
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32gui',
        '--hidden-import=win32process',
        '--hidden-import=winsound',
        
        # 运行时库包含
        '--collect-all=pkg_resources',
        '--collect-all=setuptools',
        
        # 优化和兼容性设置
        '--optimize=0',  # 不优化，保持最大兼容性
        '--debug=all',   # 包含调试信息
        '--noupx',       # 不使用UPX压缩
        '--clean',       # 清理临时文件
        
        # 包含所有必要的DLL
        '--collect-all=_ssl',
        '--collect-all=_hashlib',
        '--collect-all=_socket',
        '--collect-all=select',
        
        'auto_clicker_multi_position.py'
    ]

    # 如果有图标文件，添加图标参数
    if os.path.exists('icon.ico'):
        cmd.insert(-1, '--icon=icon.ico')

    try:
        print(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("[SUCCESS] Build successful!")
        print(result.stdout)
        
        # 检查生成的文件
        exe_file = dist_dir / 'MouseClicker_UltraCompat.exe'
        
        if exe_file.exists():
            print(f"\n[SUCCESS] Windows ultra compatible version generated: {exe_file.absolute()}")
            print(f"File size: {exe_file.stat().st_size / 1024 / 1024:.1f} MB")
            return True
        else:
            print("[ERROR] Generated executable file not found")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("[ERROR] PyInstaller not found, please ensure it is properly installed")
        return False

def create_windows_ultra_compatible_package():
    """创建Windows超兼容发布包"""
    
    print("[INFO] Creating Windows ultra compatible package...")
    
    # 创建发布目录
    release_dir = Path('release/windows_ultra_compatible')
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制可执行文件
    exe_source = Path('dist/MouseClicker_UltraCompat.exe')
    if exe_source.exists():
        exe_dest = release_dir / 'MouseClicker_UltraCompat.exe'
        shutil.copy2(exe_source, exe_dest)
        print(f"[SUCCESS] Copied executable to: {exe_dest}")
    else:
        print("[ERROR] Executable file not found, cannot create release package")
        return False
    
    # 创建启动脚本
    launcher_script = release_dir / 'Start_MouseClicker_UltraCompat.bat'
    launcher_content = '''@echo off
echo Starting Mouse Clicker Ultra Compatible Version...
echo.
echo [INFO] This version is designed for maximum Windows compatibility
echo [INFO] If you encounter any issues, please run as administrator
echo.
pause
echo Starting application...
MouseClicker_UltraCompat.exe
pause
'''
    
    with open(launcher_script, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    print(f"[SUCCESS] Created launcher script: {launcher_script}")
    
    # 创建README文件
    readme_file = release_dir / 'README_UltraCompat.md'
    readme_content = '''# Mouse Clicker - Ultra Compatible Version

## [IMPORTANT] Ultra Compatibility Features

### Maximum Windows Compatibility
- [SINGLE-FILE] Single executable file, no DLL dependencies
- [RUNTIME-INCLUDED] All Python runtime libraries included
- [DEBUG-INFO] Debug information included for troubleshooting
- [NO-COMPRESSION] No compression to avoid compatibility issues

### Supported Systems
- Windows 11 64-bit (all editions)
- Windows 10 64-bit (all editions)
- Windows Server 2019/2022
- Intel and AMD processors

## [USAGE] How to Use

### First Run
1. **Extract** the zip file to any folder
2. **Right-click** on `Start_MouseClicker_UltraCompat.bat`
3. **Select** "Run as administrator" (recommended)
4. **Allow** Windows Defender if prompted

### Alternative Launch
- Double-click `MouseClicker_UltraCompat.exe` directly
- If issues occur, always try running as administrator

## [TROUBLESHOOTING] Problem Solving

### If the program still won't start:

1. **Install Visual C++ Redistributable**
   - Download from Microsoft official website
   - Install both x64 and x86 versions

2. **Check Windows Defender**
   - Add the folder to exclusion list
   - Temporarily disable real-time protection

3. **Run as Administrator**
   - Right-click the exe file
   - Select "Run as administrator"

4. **Check System Requirements**
   - Ensure Windows 10/11 64-bit
   - Ensure .NET Framework 4.7.2 or later

### If hotkeys don't work:
1. Run as administrator
2. Check Windows accessibility permissions
3. Disable other hotkey software temporarily

## [FEATURES] Function Description

### Core Features
- **Multi-Position Clicking**: Set multiple click positions and cycle through them
- **Position Management**: Add, remove, and reorder click positions
- **Click Modes**: Single click, double click, customizable frequency
- **Cycle Options**: Sequential clicking through all positions
- **Real-time Display**: Shows current position being clicked

### Advanced Features
- **Global Hotkeys**: Ctrl+Alt+S (start), Ctrl+Alt+D (stop)
- **Custom Hotkeys**: Fully customizable key combinations
- **Position Capture**: Click to capture mouse positions
- **Settings Persistence**: Automatically save all configurations
- **Emergency Stop**: Multiple ways to stop clicking immediately

### Multi-Position Setup
1. **Add Positions**: Click "Capture Position" and click where you want
2. **Manage List**: Remove or reorder positions as needed
3. **Set Parameters**: Configure click frequency and count
4. **Start Clicking**: Use hotkeys or interface buttons

### Hotkey Instructions
- Default: Ctrl+Alt+S (start), Ctrl+Alt+D (stop)
- Customizable in program interface
- Supports Ctrl, Alt, Shift, Win key combinations
- Emergency stop available through multiple methods

## [SUPPORT] Technical Support

If you continue to experience issues:
1. Check Windows Event Viewer for error details
2. Try running in Windows compatibility mode
3. Ensure no antivirus software is blocking the program
4. Contact support with specific error messages

---
Generated by Ultra Compatible Build Script
'''
    
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"[SUCCESS] Created README file: {readme_file}")
    
    # 复制配置文件
    config_files = ['requirements.txt']  # 多位置版本配置文件在用户目录
    for config_file in config_files:
        if os.path.exists(config_file):
            shutil.copy2(config_file, release_dir)
    
    print(f"\n[SUCCESS] Windows ultra compatible package created successfully: {release_dir.absolute()}")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("Windows Ultra Compatible Build Script")
    print("Solving Python DLL loading issues")
    print("=" * 60)
    
    if build_windows_ultra_compatible_exe():
        if create_windows_ultra_compatible_package():
            print("\n[SUCCESS] Windows ultra compatible build completed successfully!")
            print("\n[INFO] Usage Instructions:")
            print("1. Copy the release/windows_ultra_compatible folder to Windows system")
            print("2. Run 'Start_MouseClicker_UltraCompat.bat' as administrator")
            print("3. If issues persist, check the README_UltraCompat.md file")
        else:
            print("\n[ERROR] Failed to create release package!")
            sys.exit(1)
    else:
        print("\n[ERROR] Windows ultra compatible build failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()