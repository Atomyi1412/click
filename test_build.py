#!/usr/bin/env python3
"""
打包测试脚本
验证生成的可执行文件是否正常工作
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def test_macos_app():
    """测试 macOS app 文件"""
    print("\n=== 测试 macOS App ===")
    
    app_path = Path('dist/鼠标连点器.app')
    if not app_path.exists():
        print("❌ 未找到 macOS app 文件")
        return False
    
    print(f"✅ 找到 app 文件: {app_path}")
    
    # 检查 app 结构
    contents_path = app_path / 'Contents'
    if not contents_path.exists():
        print("❌ app 结构不完整")
        return False
    
    # 检查可执行文件
    executable_path = contents_path / 'MacOS' / '鼠标连点器'
    if not executable_path.exists():
        print("❌ 未找到可执行文件")
        return False
    
    print(f"✅ 可执行文件存在: {executable_path}")
    
    # 检查权限
    if not os.access(executable_path, os.X_OK):
        print("❌ 可执行文件没有执行权限")
        return False
    
    print("✅ 可执行文件有执行权限")
    
    # 检查 Info.plist
    plist_path = contents_path / 'Info.plist'
    if plist_path.exists():
        print("✅ Info.plist 存在")
        try:
            with open(plist_path, 'r') as f:
                content = f.read()
                if 'NSAccessibilityUsageDescription' in content:
                    print("✅ 包含辅助功能权限描述")
                else:
                    print("⚠️  缺少辅助功能权限描述")
        except Exception as e:
            print(f"⚠️  读取 Info.plist 失败: {e}")
    
    # 计算 app 大小
    try:
        result = subprocess.run(['du', '-sh', str(app_path)], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            size = result.stdout.split()[0]
            print(f"📦 App 大小: {size}")
    except Exception as e:
        print(f"⚠️  无法获取 app 大小: {e}")
    
    return True

def test_app_launch():
    """测试应用启动（非阻塞）"""
    print("\n=== 测试应用启动 ===")
    
    app_path = Path('dist/鼠标连点器.app')
    if not app_path.exists():
        print("❌ 未找到 app 文件")
        return False
    
    try:
        # 使用 open 命令启动应用（非阻塞）
        print("🚀 尝试启动应用...")
        result = subprocess.run(['open', str(app_path)], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 应用启动命令执行成功")
            print("📋 请手动检查应用是否正常显示界面")
            print("📋 如果需要权限，请按照说明文档设置")
            return True
        else:
            print(f"❌ 应用启动失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  启动超时，但这可能是正常的")
        return True
    except Exception as e:
        print(f"❌ 启动测试失败: {e}")
        return False

def test_dependencies():
    """测试依赖是否正确打包"""
    print("\n=== 测试依赖打包 ===")
    
    app_path = Path('dist/鼠标连点器.app')
    if not app_path.exists():
        return False
    
    # 检查关键依赖
    frameworks_path = app_path / 'Contents' / 'Frameworks'
    resources_path = app_path / 'Contents' / 'Resources'
    
    dependencies_found = 0
    total_dependencies = 0
    
    # 检查 PyQt5
    total_dependencies += 1
    if any(f.name.startswith('Qt') for f in frameworks_path.glob('*') if f.is_dir()):
        print("✅ PyQt5 框架已打包")
        dependencies_found += 1
    else:
        print("❌ PyQt5 框架未找到")
    
    # 检查 Python 库
    total_dependencies += 1
    if (resources_path / 'lib').exists():
        print("✅ Python 库已打包")
        dependencies_found += 1
    else:
        print("❌ Python 库未找到")
    
    print(f"📊 依赖检查: {dependencies_found}/{total_dependencies} 通过")
    return dependencies_found == total_dependencies

def create_release_package():
    """创建发布包"""
    print("\n=== 创建发布包 ===")
    
    app_path = Path('dist/鼠标连点器.app')
    if not app_path.exists():
        print("❌ 未找到 app 文件")
        return False
    
    # 创建发布目录
    release_dir = Path('release/macos')
    release_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 复制 app 文件
        import shutil
        dest_app = release_dir / '鼠标连点器.app'
        if dest_app.exists():
            shutil.rmtree(dest_app)
        shutil.copytree(app_path, dest_app)
        print(f"✅ 已复制 app 到: {dest_app}")
        
        # 复制说明文件
        readme_files = ['README_macOS.md', 'README_Build.md']
        for readme in readme_files:
            if Path(readme).exists():
                shutil.copy2(readme, release_dir)
                print(f"✅ 已复制: {readme}")
        
        print(f"\n🎉 发布包已创建: {release_dir.absolute()}")
        return True
        
    except Exception as e:
        print(f"❌ 创建发布包失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 鼠标连点器打包测试工具 ===")
    
    # 检查当前目录
    if not Path('auto_clicker_native.py').exists():
        print("❌ 请在项目根目录运行此脚本")
        sys.exit(1)
    
    success_count = 0
    total_tests = 4
    
    # 运行测试
    if test_macos_app():
        success_count += 1
    
    if test_dependencies():
        success_count += 1
    
    if test_app_launch():
        success_count += 1
    
    if create_release_package():
        success_count += 1
    
    # 显示结果
    print(f"\n=== 测试结果 ===")
    print(f"通过测试: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！")
        print("\n📋 下一步：")
        print("1. 手动测试应用功能")
        print("2. 设置辅助功能权限")
        print("3. 测试热键功能")
        print("4. 在不同 macOS 版本上测试")
    else:
        print("❌ 部分测试失败，请检查问题")
        sys.exit(1)

if __name__ == '__main__':
    main()