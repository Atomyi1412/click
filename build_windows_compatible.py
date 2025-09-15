#!/usr/bin/env python3
"""
Windows 11 兼容版打包脚本
使用 PyInstaller 将鼠标连点器打包成兼容 Windows 11 的 exe 文件
解决架构不匹配和运行时库缺失问题
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_windows_compatible_exe():
    """构建 Windows 11 兼容的 exe 文件"""
    print("Building Windows 11 compatible exe file...")

    # 仅允许在 Windows 上打包，避免生成 Mac Mach-O 假 exe
    if sys.platform != 'win32':
        print(f"❌ Current platform is {sys.platform}, not Windows. Please run this script on Windows 10/11 64-bit system to generate real Windows executable.")
        return False

    # 确保在正确的目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # 清理之前的构建文件
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    # 使用当前解释器，确保 64 位 Python 环境
    py_exe = sys.executable or 'python'

    # PyInstaller 命令参数 - 使用 onedir 模式提高兼容性
    cmd = [
        py_exe, '-m', 'PyInstaller',
        '--onedir',  # 使用目录模式而不是单文件，提高兼容性
        '--windowed',  # 不显示控制台窗口
        '--name=MouseClicker_Win11_Compat',  # 使用英文名避免路径编码问题
        '--distpath=dist',  # 输出目录
        '--workpath=build',  # 工作目录
        '--specpath=.',  # spec文件路径
        '--add-data=config_native.json:.',  # 包含配置文件
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui', 
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.sip',
        '--hidden-import=PyQt5.QtPrintSupport',
        '--hidden-import=pynput',
        '--hidden-import=pynput.mouse',
        '--hidden-import=pynput.keyboard',
        '--hidden-import=pynput._util',
        '--hidden-import=pynput._util.win32',
        '--hidden-import=keyboard',
        '--hidden-import=json',
        '--hidden-import=threading',
        '--hidden-import=time',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=configparser',
        '--collect-all=PyQt5',
        '--collect-all=pynput',
        '--collect-all=keyboard',
        '--optimize=2',  # Python 字节码优化
        '--strip',  # 去除调试信息
        '--noupx',  # 不使用 UPX 压缩，避免兼容性问题
        'auto_clicker_native.py'
    ]

    # 如果有图标文件，添加图标参数
    if os.path.exists('icon.ico'):
        cmd.insert(-1, '--icon=icon.ico')

    try:
        print(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(result.stdout)

        # 检查输出文件
        exe_dir = Path('dist/MouseClicker_Win11_Compat')
        exe_file = exe_dir / 'MouseClicker_Win11_Compat.exe'

        if exe_file.exists():
            print(f"\n✅ Windows compatible version generated: {exe_file.absolute()}")
            print(f"File size: {exe_file.stat().st_size / 1024 / 1024:.1f} MB")

            # 显示目录内容
            print(f"\n📁 Release directory contents:")
            for item in exe_dir.iterdir():
                if item.is_file():
                    size = item.stat().st_size / 1024 / 1024
                    print(f"  {item.name} ({size:.1f} MB)")
                else:
                    print(f"  {item.name}/ (directory)")
        else:
            print("❌ Generated executable file not found")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller not found, please ensure it is properly installed")
        return False

    return True

def create_windows_compatible_package():
    """创建 Windows 11 兼容发布包"""
    print("\nCreating Windows 11 compatible release package...")

    # 创建发布目录
    release_dir = Path('release/windows_compatible')
    release_dir.mkdir(parents=True, exist_ok=True)

    # 复制整个应用目录（与上面的构建输出名称保持一致）
    app_source = Path('dist/MouseClicker_Win11_Compat')
    app_dest = release_dir / 'MouseClicker_Win11_Compat'

    if app_source.exists():
        if app_dest.exists():
            shutil.rmtree(app_dest)
        shutil.copytree(app_source, app_dest)
        print(f"✅ Copied application directory to: {app_dest}")
    else:
        print("❌ Application directory not found, cannot create release package")
        return False

    # 创建启动脚本（英文名称，避免编码问题）
    launcher_script = release_dir / 'Start_MouseClicker_Win11_Compat.bat'
    launcher_content = '''@echo off
chcp 65001 >nul
cd /d "%~dp0"
cd "MouseClicker_Win11_Compat"
start "" "MouseClicker_Win11_Compat.exe"
'''

    with open(launcher_script, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    print(f"✅ Created launcher script: {launcher_script}")

    # 保留原有 README 生成逻辑（内容不影响运行）
    readme_content = '''# 鼠标连点器 - Windows 11 兼容版

## 🚀 使用方法

### 方法一：直接运行
1. 双击 `启动鼠标连点器.bat` 启动程序
2. 或者进入 `鼠标连点器` 文件夹，双击 `鼠标连点器.exe`

### 方法二：管理员权限运行（推荐）
1. 右键点击 `启动鼠标连点器.bat`
2. 选择 "以管理员身份运行"
3. 这样可以确保全局热键功能正常工作

## ⚠️ 重要说明

### Windows 11 兼容性
- ✅ 支持 Windows 11 64位系统
- ✅ 包含所有必要的运行时库
- ✅ 使用目录模式，避免单文件兼容性问题
- ✅ 针对 Intel/AMD 64位处理器优化

### 首次运行
1. **Windows Defender 警告**：首次运行时可能被 Windows Defender 拦截
   - 点击 "更多信息" → "仍要运行"
   - 或将程序添加到 Windows Defender 排除列表

2. **杀毒软件误报**：某些杀毒软件可能误报
   - 这是因为程序需要监听全局按键
   - 请将程序添加到信任列表

3. **权限设置**：
   - 程序需要监听全局热键，建议以管理员权限运行
   - 某些功能可能需要在 Windows 设置中允许应用访问

## 🎮 功能说明

### 基本功能
- **鼠标连点**：支持单击/双击，频率 1-100 次/秒
- **全局热键**：Ctrl+Option+S（开始）、Ctrl+Option+D（停止）
- **自定义热键**：可自定义修饰键组合和主键
- **配置保存**：自动保存设置

### 热键说明
- 默认热键：Ctrl+Alt+S（开始）、Ctrl+Alt+D（停止）
- 可在程序界面中自定义热键组合
- 支持 Ctrl、Alt、Shift、Win 键组合

## 🔧 故障排除

### 程序无法启动
1. 确保系统是 Windows 10/11 64位
2. 尝试以管理员权限运行
3. 检查杀毒软件是否拦截
4. 重新下载并解压到新位置

### 热键无效
1. 确保程序以管理员权限运行
2. 检查是否有其他程序占用相同热键
3. 尝试更换热键组合

### 连点功能异常
1. 确保鼠标指针在目标位置
2. 检查点击频率设置是否合理
3. 某些游戏可能有反作弊检测

## 📞 技术支持

如果遇到问题，请提供以下信息：
- Windows 版本和架构
- 错误信息截图
- 使用场景描述

---

**注意**：请遵守相关软件的使用协议，不要用于违规用途。
'''
    
    readme_file = release_dir / 'README_Windows_Compatible.md'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"✅ Created README file: {readme_file}")
    
    # 复制其他说明文件
    other_files = ['README.md', 'README_Windows.md']
    for file_name in other_files:
        if os.path.exists(file_name):
            shutil.copy2(file_name, release_dir)
    
    print(f"\n🎉 Windows 11 compatible package created successfully: {release_dir.absolute()}")
    return True

def main():
    """主函数"""
    # 设置控制台编码为UTF-8以支持中文显示
    import sys
    if sys.platform == 'win32':
        import os
        os.system('chcp 65001 > nul')
    
    print("=== Mouse Clicker Windows 11 Compatible Build Tool ===")
    print("Solving architecture mismatch and runtime library issues\n")
    
    if build_windows_compatible_exe():
        if create_windows_compatible_package():
            print("\n🎉 Windows 11 compatible build completed successfully!")
            print("\n📋 Usage Instructions:")
            print("1. Copy the release/windows_compatible folder to Windows 11 system")
            print("2. Double-click 'Start_MouseClicker_Win11_Compat.bat' or run as administrator")
            print("3. First run may require allowing Windows Defender warnings")
        else:
            print("\n❌ Failed to create release package!")
            sys.exit(1)
    else:
        print("\n❌ Windows 11 compatible build failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()