#!/usr/bin/env python3
"""
macOS 打包脚本
使用 PyInstaller 将鼠标连点器打包成 macOS app 文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import plistlib

def build_macos_app():
    """构建 macOS app 文件"""
    print("开始构建 macOS app 文件...")
    
    # 确保在正确的目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # 清理之前的构建文件
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # PyInstaller 命令参数
    cmd = [
        'python3', '-m', 'PyInstaller',
        '--onedir',  # 打包成目录（macOS app 需要）
        '--windowed',  # 不显示控制台窗口
        '--name=鼠标连点器',  # app 名称
        '--icon=icon.icns',  # macOS 图标文件（如果存在）
        '--add-data=config_native.json:.',  # 包含配置文件
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui', 
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=pynput',
        '--hidden-import=pynput.mouse',
        '--hidden-import=pynput.keyboard',
        '--hidden-import=keyboard',
        '--hidden-import=AppKit',
        '--hidden-import=Quartz',
        '--collect-all=PyQt5',
        '--collect-all=pynput',
        '--collect-all=AppKit',
        '--collect-all=Quartz',
        '--osx-bundle-identifier=com.autoclicker.native',
        'auto_clicker_native.py'
    ]
    
    # 如果没有图标文件，移除图标参数
    if not os.path.exists('icon.icns'):
        cmd = [arg for arg in cmd if not arg.startswith('--icon')]
    
    try:
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功！")
        print(result.stdout)
        
        # 检查输出文件
        app_path = Path('dist/鼠标连点器.app')
        if app_path.exists():
            print(f"\n✅ macOS app 文件已生成: {app_path.absolute()}")
            
            # 修改 Info.plist 添加权限请求
            modify_info_plist(app_path)
            
            # 计算 app 大小
            app_size = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file())
            print(f"App 大小: {app_size / 1024 / 1024:.1f} MB")
        else:
            print("❌ 未找到生成的 app 文件")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller 未找到，请确保已正确安装")
        return False
    
    return True

def modify_info_plist(app_path):
    """修改 Info.plist 添加权限请求"""
    print("\n修改 Info.plist 添加权限请求...")
    
    plist_path = app_path / 'Contents' / 'Info.plist'
    if not plist_path.exists():
        print("❌ 未找到 Info.plist 文件")
        return
    
    try:
        # 读取现有的 plist
        with open(plist_path, 'rb') as f:
            plist_data = plistlib.load(f)
        
        # 添加权限请求
        plist_data['NSAppleEventsUsageDescription'] = '此应用需要辅助功能权限来实现全局热键功能'
        plist_data['NSAccessibilityUsageDescription'] = '此应用需要辅助功能权限来监听全局按键事件'
        
        # 添加 LSUIElement 隐藏 Dock 图标（可选）
        # plist_data['LSUIElement'] = True
        
        # 写回 plist
        with open(plist_path, 'wb') as f:
            plistlib.dump(plist_data, f)
        
        print("✅ Info.plist 已更新，添加了权限请求")
        
    except Exception as e:
        print(f"❌ 修改 Info.plist 失败: {e}")

def create_macos_package():
    """创建 macOS 发布包"""
    print("\n创建 macOS 发布包...")
    
    # 创建发布目录
    release_dir = Path('release/macos')
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制 app 文件
    app_source = Path('dist/鼠标连点器.app')
    app_dest = release_dir / '鼠标连点器.app'
    
    if app_source.exists():
        if app_dest.exists():
            shutil.rmtree(app_dest)
        shutil.copytree(app_source, app_dest)
        print(f"✅ 已复制 app 文件到: {release_dir}")
    
    # 复制说明文件
    readme_files = ['README.md', 'README_macOS.md']
    for readme in readme_files:
        if os.path.exists(readme):
            shutil.copy2(readme, release_dir)
    
    # 创建权限设置说明
    create_permission_guide(release_dir)
    
    print(f"\n🎉 macOS 发布包已创建: {release_dir.absolute()}")

def create_permission_guide(release_dir):
    """创建权限设置说明文件"""
    guide_content = """# macOS 权限设置指南

## 重要提示

鼠标连点器需要辅助功能权限才能正常工作。请按照以下步骤设置：

### 1. 首次运行
- 双击 `鼠标连点器.app` 启动应用
- 系统会弹出权限请求对话框
- 点击 "打开系统偏好设置"

### 2. 手动设置权限
如果没有自动弹出权限请求，请手动设置：

1. 打开 "系统偏好设置" > "安全性与隐私" > "隐私"
2. 在左侧列表中选择 "辅助功能"
3. 点击左下角的锁图标，输入管理员密码
4. 点击 "+" 按钮，添加 "鼠标连点器.app"
5. 确保应用旁边的复选框已勾选

### 3. 重启应用
设置完权限后，重新启动鼠标连点器即可使用全局热键功能。

### 4. 默认热键
- Ctrl + Option + S：开始连点
- Ctrl + Option + D：停止连点
- 可在应用内自定义热键组合

### 故障排除

**如果热键不工作：**
1. 确认已正确设置辅助功能权限
2. 重启应用
3. 尝试使用窗口内的 F6/F7 热键（需要应用窗口在前台）

**如果应用无法启动：**
1. 右键点击应用，选择 "打开"
2. 在弹出的对话框中点击 "打开"
3. 如果仍有问题，请在终端中运行：`xattr -cr 鼠标连点器.app`

## 联系支持

如果遇到其他问题，请检查应用内的使用说明或联系开发者。
"""
    
    guide_path = release_dir / '权限设置指南.md'
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ 已创建权限设置指南")

if __name__ == '__main__':
    print("=== 鼠标连点器 macOS 打包工具 ===")
    
    if build_macos_app():
        create_macos_package()
        print("\n✅ macOS 打包完成！")
        print("\n📋 下一步：")
        print("1. 测试生成的 app 文件")
        print("2. 设置辅助功能权限")
        print("3. 验证全局热键功能")
    else:
        print("\n❌ macOS 打包失败！")
        sys.exit(1)