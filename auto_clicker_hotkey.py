#!/usr/bin/env python3
"""
带热键功能的鼠标连点器 - 使用pynput实现
尝试避免keyboard库的权限问题
"""

import sys
import json
import threading
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QSpinBox, QComboBox,
                             QGroupBox, QTextEdit, QShortcut)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QKeySequence
from pynput.mouse import Controller, Button
from pynput import keyboard


class ClickWorker(QThread):
    click_signal = pyqtSignal(int)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = False
        self.mouse = Controller()
        self.click_count = 0
        
    def run(self):
        self.running = True
        self.click_count = 0
        
        button_map = {
            '左键': Button.left,
            '右键': Button.right,
            '中键': Button.middle
        }
        button = button_map[self.config['button']]
        
        interval = 1.0 / self.config['frequency']
        
        while self.running and self.click_count < self.config['max_clicks']:
            if self.config['click_type'] == '单击':
                self.mouse.click(button)
            else:  # 双击
                self.mouse.click(button)
                time.sleep(0.01)
                self.mouse.click(button)
            
            self.click_count += 1
            self.click_signal.emit(self.click_count)
            
            if not self.running:
                break
                
            time.sleep(interval)
    
    def stop(self):
        self.running = False


class MouseClicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.config = {
            'frequency': 10,
            'max_clicks': 1000,
            'button': '左键',
            'click_type': '单击',
            'hotkey_start': 'f6',
            'hotkey_stop': 'f7'
        }
        self.load_config()
        self.hotkey_listener = None
        self.init_ui()
        self.setup_hotkeys()
        
    def init_ui(self):
        self.setWindowTitle('鼠标连点器 (带热键)')
        self.setGeometry(100, 100, 450, 550)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # 设置组
        settings_group = QGroupBox("点击设置")
        settings_layout = QVBoxLayout()
        
        # 频率设置
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("点击频率 (次/秒):"))
        self.freq_spinbox = QSpinBox()
        self.freq_spinbox.setRange(1, 100)
        self.freq_spinbox.setValue(self.config['frequency'])
        self.freq_spinbox.valueChanged.connect(self.update_config)
        freq_layout.addWidget(self.freq_spinbox)
        settings_layout.addLayout(freq_layout)
        
        # 最大点击次数
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("最大点击次数:"))
        self.max_spinbox = QSpinBox()
        self.max_spinbox.setRange(1, 10000)
        self.max_spinbox.setValue(self.config['max_clicks'])
        self.max_spinbox.valueChanged.connect(self.update_config)
        max_layout.addWidget(self.max_spinbox)
        settings_layout.addLayout(max_layout)
        
        # 鼠标按钮选择
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel("鼠标按钮:"))
        self.button_combo = QComboBox()
        self.button_combo.addItems(['左键', '右键', '中键'])
        self.button_combo.setCurrentText(self.config['button'])
        self.button_combo.currentTextChanged.connect(self.update_config)
        button_layout.addWidget(self.button_combo)
        settings_layout.addLayout(button_layout)
        
        # 点击类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("点击类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(['单击', '双击'])
        self.type_combo.setCurrentText(self.config['click_type'])
        self.type_combo.currentTextChanged.connect(self.update_config)
        type_layout.addWidget(self.type_combo)
        settings_layout.addLayout(type_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 热键设置
        hotkey_group = QGroupBox("热键设置")
        hotkey_layout = QVBoxLayout()
        
        start_key_layout = QHBoxLayout()
        start_key_layout.addWidget(QLabel("开始热键:"))
        self.start_key_label = QLabel(self.config['hotkey_start'].upper())
        start_key_layout.addWidget(self.start_key_label)
        hotkey_layout.addLayout(start_key_layout)
        
        stop_key_layout = QHBoxLayout()
        stop_key_layout.addWidget(QLabel("停止热键:"))
        self.stop_key_label = QLabel(self.config['hotkey_stop'].upper())
        stop_key_layout.addWidget(self.stop_key_label)
        hotkey_layout.addLayout(stop_key_layout)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout()
        
        self.start_button = QPushButton("开始连点")
        self.start_button.clicked.connect(self.start_clicking)
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;")
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止连点")
        self.stop_button.clicked.connect(self.stop_clicking)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #f44336; color: white; font-size: 16px; padding: 10px;")
        control_layout.addWidget(self.stop_button)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 状态显示
        status_group = QGroupBox("状态")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        self.count_label = QLabel("点击次数: 0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.count_label)
        
        hotkey_status_layout = QHBoxLayout()
        hotkey_status_layout.addWidget(QLabel("热键状态:"))
        self.hotkey_status_label = QLabel("监听中")
        self.hotkey_status_label.setStyleSheet("color: green")
        hotkey_status_layout.addWidget(self.hotkey_status_label)
        status_layout.addLayout(hotkey_status_layout)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 提示信息
        tip_label = QLabel("提示：\n1. 将鼠标移动到需要点击的位置\n2. 按F6开始连点，按F7停止\n3. 或使用界面按钮控制")
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(tip_label)
        
        central_widget.setLayout(layout)
        
    def setup_hotkeys(self):
        def on_key_press(key):
            try:
                key_name = key.char.lower() if hasattr(key, 'char') else str(key).split('.')[1].lower()
                
                if key_name == self.config['hotkey_start']:
                    self.start_clicking()
                elif key_name == self.config['hotkey_stop']:
                    self.stop_clicking()
            except:
                pass
        
        def listen_for_hotkeys():
            with keyboard.Listener(on_press=on_key_press) as listener:
                self.hotkey_listener = listener
                listener.join()
        
        self.hotkey_thread = threading.Thread(target=listen_for_hotkeys, daemon=True)
        self.hotkey_thread.start()
        
    def update_config(self):
        self.config['frequency'] = self.freq_spinbox.value()
        self.config['max_clicks'] = self.max_spinbox.value()
        self.config['button'] = self.button_combo.currentText()
        self.config['click_type'] = self.type_combo.currentText()
        self.save_config()
        
    def start_clicking(self):
        if self.worker and self.worker.isRunning():
            return
            
        self.worker = ClickWorker(self.config)
        self.worker.click_signal.connect(self.update_count)
        self.worker.finished.connect(self.clicking_finished)
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("连点中...")
        
        self.worker.start()
        
    def stop_clicking(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            
    def clicking_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("就绪")
        
    def update_count(self, count):
        self.count_label.setText(f"点击次数: {count}")
        
    def load_config(self):
        try:
            with open('config_hotkey.json', 'r') as f:
                self.config.update(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
            
    def save_config(self):
        try:
            with open('config_hotkey.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass
            
    def closeEvent(self, a0):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.save_config()
        if a0:
            a0.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MouseClicker()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()