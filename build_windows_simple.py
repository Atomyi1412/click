#!/usr/bin/env python3
"""
Windows 简化版打包脚本
使用最基本的 PyInstaller 参数，避免兼容性问题
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_windows_simple_exe():
    """构建简化版 Windows exe 文件"""
    print("开始构建简化版 Windows exe 文件...")
    
    # 确保在正确的目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 清理之前的构建文件
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # 使用最简单的 PyInstaller 命令
    cmd = [
        'python3', '-m', 'PyInstaller',
        '--onedir',  # 使用目录模式
        '--windowed',  # 不显示控制台
        '--name=MouseClicker',  # 使用英文名避免编码问题
        '--add-data=config_native.json:.',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui', 
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=pynput',
        '--hidden-import=pynput.mouse',
        '--hidden-import=pynput.keyboard',
        '--collect-all=PyQt5',
        '--collect-all=pynput',
        '--noupx',  # 不使用压缩
        'auto_clicker_native.py'
    ]
    
    try:
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功！")
        
        # 检查输出文件
        exe_dir = Path('dist/MouseClicker')
        exe_file = exe_dir / 'MouseClicker.exe'
        
        if exe_file.exists():
            print(f"\n✅ Windows 简化版已生成: {exe_file.absolute()}")
            print(f"文件大小: {exe_file.stat().st_size / 1024 / 1024:.1f} MB")
            return True
        else:
            # 检查是否生成了无扩展名的文件
            exe_file_no_ext = exe_dir / 'MouseClicker'
            if exe_file_no_ext.exists():
                # 重命名为 .exe
                exe_file_no_ext.rename(exe_file)
                print(f"\n✅ Windows 简化版已生成: {exe_file.absolute()}")
                print(f"文件大小: {exe_file.stat().st_size / 1024 / 1024:.1f} MB")
                return True
            else:
                print("❌ 未找到生成的可执行文件")
                return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller 未找到，请确保已正确安装")
        return False

def create_windows_simple_package():
    """创建简化版发布包"""
    print("\n创建简化版发布包...")
    
    # 创建发布目录
    release_dir = Path('release/windows_simple')
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制应用目录
    app_source = Path('dist/MouseClicker')
    app_dest = release_dir / 'MouseClicker'
    
    if app_source.exists():
        if app_dest.exists():
            shutil.rmtree(app_dest)
        shutil.copytree(app_source, app_dest)
        print(f"✅ 已复制应用到: {app_dest}")
    else:
        print("❌ 未找到应用目录")
        return False
    
    # 创建启动脚本
    launcher_script = release_dir / 'Start_MouseClicker.bat'
    launcher_content = '''@echo off
chcp 65001 >nul
echo Starting Mouse Clicker...
cd /d "%~dp0"
cd "MouseClicker"
start "" "MouseClicker.exe"
'''
    
    with open(launcher_script, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    print(f"✅ 已创建启动脚本: {launcher_script}")
    
    # 创建说明文件
    readme_content = '''# Mouse Clicker - Windows Compatible Version

## How to Use

1. Double-click `Start_MouseClicker.bat` to run the program
2. Or go into `MouseClicker` folder and run `MouseClicker.exe`

## Important Notes

### Windows 11 Compatibility
- ✅ Compatible with Windows 10/11 64-bit
- ✅ Includes all necessary runtime libraries
- ✅ Uses directory mode for better compatibility

### First Run
1. **Windows Defender Warning**: May be blocked on first run
   - Click "More info" → "Run anyway"
   - Or add to Windows Defender exclusion list

2. **Antivirus False Positive**: Some antivirus may flag it
   - This is because the program monitors global keystrokes
   - Please add to trusted list

3. **Administrator Rights**: 
   - Program needs to monitor global hotkeys
   - Recommend running as administrator

## Features

- **Mouse Clicking**: Single/double click, 1-100 clicks per second
- **Global Hotkeys**: Ctrl+Alt+S (start), Ctrl+Alt+D (stop)
- **Custom Hotkeys**: Customizable modifier key combinations
- **Settings Save**: Automatically saves configuration

## Troubleshooting

### Program Won\'t Start
1. Ensure Windows 10/11 64-bit system
2. Try running as administrator
3. Check if antivirus is blocking
4. Re-download and extract to new location

### Hotkeys Not Working
1. Ensure program runs as administrator
2. Check if other programs use same hotkeys
3. Try different hotkey combinations

---

**Note**: Please comply with software usage agreements and do not use for unauthorized purposes.
'''
    
    readme_file = release_dir / 'README.md'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"✅ 已创建说明文件: {readme_file}")
    
    print(f"\n🎉 简化版发布包已创建: {release_dir.absolute()}")
    return True

def main():
    """主函数"""
    print("=== Mouse Clicker Windows Simple Build Tool ===")
    print("Building compatible version for Windows 11\n")
    
    if build_windows_simple_exe():
        if create_windows_simple_package():
            print("\n✅ Windows 简化版打包完成！")
            print("\n📋 使用说明:")
            print("1. 将 release/windows_simple 文件夹复制到 Windows 系统")
            print("2. 双击 'Start_MouseClicker.bat' 启动程序")
            print("3. 或以管理员权限运行获得最佳体验")
        else:
            print("\n❌ 创建发布包失败！")
            sys.exit(1)
    else:
        print("\n❌ 简化版打包失败！")
        sys.exit(1)

if __name__ == '__main__':
    main()