#!/usr/bin/env python3
"""
通用打包脚本
自动检测平台并执行相应的打包流程
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def detect_platform():
    """检测当前平台"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    elif system == 'linux':
        return 'linux'
    else:
        return 'unknown'

def check_dependencies():
    """检查依赖是否已安装"""
    print("检查依赖...")
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} 已安装")
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("请运行: python3 -m pip install pyinstaller")
        return False
    
    # 检查主要依赖
    dependencies = ['PyQt5', 'pynput', 'keyboard']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} 已安装")
        except ImportError:
            print(f"❌ {dep} 未安装")
            print(f"请运行: python3 -m pip install {dep}")
            return False
    
    return True

def build_with_spec():
    """使用 spec 文件打包"""
    print("\n使用 spec 文件打包...")
    
    spec_file = 'auto_clicker.spec'
    if not os.path.exists(spec_file):
        print(f"❌ 未找到 {spec_file} 文件")
        return False
    
    cmd = ['python3', '-m', 'PyInstaller', spec_file]
    
    try:
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 打包成功！")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False

def build_platform_specific():
    """根据平台执行特定的打包脚本"""
    current_platform = detect_platform()
    print(f"\n检测到平台: {current_platform}")
    
    if current_platform == 'windows':
        script = 'build_windows.py'
    elif current_platform == 'macos':
        script = 'build_macos.py'
    else:
        print(f"❌ 不支持的平台: {current_platform}")
        return False
    
    if not os.path.exists(script):
        print(f"❌ 未找到平台特定的打包脚本: {script}")
        return False
    
    try:
        print(f"\n执行平台特定打包脚本: {script}")
        result = subprocess.run([sys.executable, script], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 平台特定打包失败: {e}")
        return False

def show_results():
    """显示打包结果"""
    print("\n=== 打包结果 ===")
    
    # 检查 dist 目录
    dist_dir = Path('dist')
    if dist_dir.exists():
        print(f"\n📁 输出目录: {dist_dir.absolute()}")
        
        for item in dist_dir.iterdir():
            if item.is_file():
                size = item.stat().st_size / 1024 / 1024
                print(f"  📄 {item.name} ({size:.1f} MB)")
            elif item.is_dir():
                # 计算目录大小
                total_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                size = total_size / 1024 / 1024
                print(f"  📁 {item.name}/ ({size:.1f} MB)")
    
    # 检查 release 目录
    release_dir = Path('release')
    if release_dir.exists():
        print(f"\n📦 发布目录: {release_dir.absolute()}")
        for platform_dir in release_dir.iterdir():
            if platform_dir.is_dir():
                print(f"  📁 {platform_dir.name}/")
                for item in platform_dir.iterdir():
                    print(f"    - {item.name}")

def main():
    """主函数"""
    print("=== 鼠标连点器通用打包工具 ===")
    print(f"Python 版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    
    # 检查主文件是否存在
    main_file = 'auto_clicker_native.py'
    if not os.path.exists(main_file):
        print(f"❌ 未找到主文件: {main_file}")
        sys.exit(1)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装缺失的依赖后重试")
        sys.exit(1)
    
    # 选择打包方式
    print("\n选择打包方式:")
    print("1. 使用 spec 文件打包（推荐）")
    print("2. 使用平台特定脚本打包")
    
    try:
        choice = input("\n请选择 (1 或 2，默认为 1): ").strip() or '1'
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(0)
    
    success = False
    
    if choice == '1':
        success = build_with_spec()
    elif choice == '2':
        success = build_platform_specific()
    else:
        print("❌ 无效选择")
        sys.exit(1)
    
    if success:
        show_results()
        print("\n🎉 打包完成！")
        
        current_platform = detect_platform()
        if current_platform == 'macos':
            print("\n📋 macOS 用户请注意:")
            print("1. 首次运行需要设置辅助功能权限")
            print("2. 查看 '权限设置指南.md' 了解详细步骤")
        elif current_platform == 'windows':
            print("\n📋 Windows 用户请注意:")
            print("1. 可能需要安装 Visual C++ 运行库")
            print("2. 某些杀毒软件可能误报，请添加信任")
    else:
        print("\n❌ 打包失败！")
        sys.exit(1)

if __name__ == '__main__':
    main()