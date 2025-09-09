#!/usr/bin/env python3
"""
热键调试版本 - 带详细日志输出
"""

import sys
import json
import threading
import time
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QSpinBox, QComboBox,
                             QGroupBox, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from pynput.mouse import Controller, Button
from pynput import keyboard


class DebugWorker(QThread):
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        
    def run(self):
        self.running = True
        while self.running:
            time.sleep(1)
            self.log_signal.emit(f"调试线程运行中... {time.strftime('%H:%M:%S')}")


class DebugHotkeyTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.hotkey_listener = None
        self.key_pressed = []
        self.init_ui()
        self.setup_debug_hotkeys()
        
    def init_ui(self):
        self.setWindowTitle('热键调试工具')
        self.setGeometry(100, 100, 500, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # 权限检查
        perm_group = QGroupBox("权限检查")
        perm_layout = QVBoxLayout()
        
        self.perm_label = QLabel("检查macOS权限设置...")
        self.perm_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        perm_layout.addWidget(self.perm_label)
        
        perm_help = QLabel("确保终端应用有：\n1. 辅助功能权限\n2. 输入监控权限")
        perm_help.setStyleSheet("color: #666;")
        perm_layout.addWidget(perm_help)
        
        perm_group.setLayout(perm_layout)
        layout.addWidget(perm_group)
        
        # 热键测试
        test_group = QGroupBox("热键测试")
        test_layout = QVBoxLayout()
        
        self.test_button = QPushButton("测试F6/F7")
        self.test_button.clicked.connect(self.test_hotkeys)
        test_layout.addWidget(self.test_button)
        
        self.status_label = QLabel("等待测试...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        test_layout.addWidget(self.status_label)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # 日志输出
        log_group = QGroupBox("调试日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # 权限帮助
        help_group = QGroupBox("权限设置步骤")
        help_layout = QVBoxLayout()
        
        help_text = """
1. 打开系统偏好设置 → 安全性与隐私 → 隐私
2. 选择"辅助功能"，添加并勾选终端应用
3. 选择"输入监控"，添加并勾选终端应用
4. 重启终端应用
        """
        help_label = QLabel(help_text)
        help_label.setWordWrap(True)
        help_layout.addWidget(help_label)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        central_widget.setLayout(layout)
        
        self.check_permissions()
        
    def check_permissions(self):
        try:
            # 测试pynput是否能监听键盘
            test_listener = keyboard.Listener(on_press=lambda x: None)
            test_listener.start()
            test_listener.stop()
            self.perm_label.setText("✅ 权限检查通过")
            self.perm_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
        except Exception as e:
            self.perm_label.setText("❌ 权限检查失败")
            self.perm_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
            self.log(f"权限错误: {str(e)}")
            
    def setup_debug_hotkeys(self):
        def on_key_press(key):
            try:
                # 获取按键名称
                if hasattr(key, 'char') and key.char:
                    key_name = key.char.lower()
                else:
                    key_name = str(key).split('.')[-1].lower()
                
                self.log(f"按键检测: {key_name}")
                
                if key_name == 'f6':
                    self.log("🟢 F6被按下 - 开始连点")
                    self.status_label.setText("F6已触发 - 开始")
                    self.status_label.setStyleSheet("color: green")
                elif key_name == 'f7':
                    self.log("🔴 F7被按下 - 停止连点")
                    self.status_label.setText("F7已触发 - 停止")
                    self.status_label.setStyleSheet("color: red")
                    
            except Exception as e:
                self.log(f"按键处理错误: {str(e)}")
        
        try:
            self.hotkey_listener = keyboard.Listener(on_press=on_key_press)
            self.hotkey_listener.start()
            self.log("热键监听器已启动")
        except Exception as e:
            self.log(f"监听器启动失败: {str(e)}")
            
    def test_hotkeys(self):
        self.log("请按F6或F7测试热键功能...")
        self.status_label.setText("等待按键...")
        
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def closeEvent(self, a0):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        a0.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = DebugHotkeyTester()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()