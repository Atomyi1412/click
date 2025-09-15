#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试多位置连点功能
"""

import sys
import time
from pynput.mouse import Controller, Button
from pynput import mouse

def test_mouse_control():
    """测试鼠标控制功能"""
    print("=== 鼠标控制测试 ===")
    
    try:
        mouse_controller = Controller()
        print(f"当前鼠标位置: {mouse_controller.position}")
        
        # 测试移动鼠标
        print("测试移动鼠标到 (100, 100)...")
        mouse_controller.position = (100, 100)
        time.sleep(0.5)
        print(f"移动后位置: {mouse_controller.position}")
        
        # 测试点击
        print("测试左键点击...")
        mouse_controller.click(Button.left)
        print("点击完成")
        
        return True
        
    except Exception as e:
        print(f"鼠标控制测试失败: {e}")
        return False

def test_multi_position_click():
    """测试多位置点击逻辑"""
    print("\n=== 多位置点击测试 ===")
    
    # 模拟位置数据
    positions = [(200, 200, "位置1"), (300, 300, "位置2"), (400, 400, "位置3")]
    
    try:
        mouse_controller = Controller()
        
        for i, (x, y, name) in enumerate(positions):
            print(f"点击 {name} ({x}, {y})...")
            
            # 移动鼠标
            mouse_controller.position = (x, y)
            time.sleep(0.1)
            
            # 验证位置
            actual_pos = mouse_controller.position
            print(f"实际位置: {actual_pos}")
            
            # 点击
            mouse_controller.click(Button.left)
            print(f"完成点击 {name}")
            
            time.sleep(1)  # 等待1秒
            
        return True
        
    except Exception as e:
        print(f"多位置点击测试失败: {e}")
        return False

def check_permissions():
    """检查权限"""
    print("\n=== 权限检查 ===")
    
    try:
        # 尝试获取当前鼠标位置
        mouse_controller = Controller()
        pos = mouse_controller.position
        print(f"✅ 可以获取鼠标位置: {pos}")
        
        # 尝试移动鼠标
        original_pos = pos
        test_pos = (pos[0] + 10, pos[1] + 10)
        mouse_controller.position = test_pos
        time.sleep(0.1)
        new_pos = mouse_controller.position
        
        if abs(new_pos[0] - test_pos[0]) < 5 and abs(new_pos[1] - test_pos[1]) < 5:
            print("✅ 可以移动鼠标")
            # 恢复原位置
            mouse_controller.position = original_pos
        else:
            print("❌ 无法移动鼠标 - 可能缺少辅助功能权限")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 权限检查失败: {e}")
        print("可能需要在系统偏好设置 > 安全性与隐私 > 辅助功能中添加此应用")
        return False

def main():
    print("多位置连点功能调试工具")
    print("=" * 40)
    
    # 检查权限
    if not check_permissions():
        print("\n❌ 权限检查失败，请检查系统权限设置")
        return
    
    # 测试基本鼠标控制
    if not test_mouse_control():
        print("\n❌ 基本鼠标控制测试失败")
        return
    
    # 测试多位置点击
    if test_multi_position_click():
        print("\n✅ 多位置点击测试成功")
    else:
        print("\n❌ 多位置点击测试失败")
    
    print("\n调试完成")

if __name__ == '__main__':
    main()