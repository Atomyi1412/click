#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鼠标连点器 - Auto Clicker
功能：
- 基本连点功能
- 自定义点击类型（左键/右键）
- 设置点击频率和次数
- 热键控制
- 按住连点模式
- 鼠标录制与回放
"""

import sys
import time
import threading
import json
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QSpinBox, 
                              QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit,
                              QGroupBox, QRadioButton, QButtonGroup, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Listener as KeyboardListener
import keyboard as kb
import configparser
import os

class ClickThread(QThread):
    click_signal = pyqtSignal()
    
    def __init__(self, click_type, interval, max_clicks, hold_mode=False):
        super().__init__()
        self.click_type = click_type
        self.interval = interval
        self.max_clicks = max_clicks
        self.hold_mode = hold_mode
        self.running = False
        self.click_count = 0
        self.mouse = MouseController()
        
    def run(self):
        self.running = True
        self.click_count = 0
        
        button = Button.left if self.click_type == 'left' else Button.right
        
        while self.running and (self.max_clicks == 0 or self.click_count < self.max_clicks):
            if self.hold_mode and not kb.is_pressed('f6'):
                break
                
            self.mouse.click(button)
            self.click_count += 1
            self.click_signal.emit()
            
            if self.interval > 0:
                time.sleep(self.interval / 1000.0)
    
    def stop(self):
        self.running = False

class RecordThread(QThread):
    record_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.events = []
        self.mouse_listener = None
        self.keyboard_listener = None
        
    def on_click(self, x, y, button, pressed):
        if self.recording and pressed:
            event = {
                'type': 'click',
                'x': x,
                'y': y,
                'button': str(button),
                'timestamp': time.time()
            }
            self.events.append(event)
            self.record_signal.emit(f"点击: ({x}, {y}) {button}")
    
    def on_key_press(self, key):
        if self.recording:
            try:
                key_str = key.char if hasattr(key, 'char') else str(key)
                event = {
                    'type': 'key',
                    'key': key_str,
                    'timestamp': time.time()
                }
                self.events.append(event)
                self.record_signal.emit(f"按键: {key_str}")
            except:
                pass
    
    def run(self):
        self.recording = True
        self.events = []
        
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.keyboard_listener = KeyboardListener(on_press=self.on_key_press)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        while self.recording:
            time.sleep(0.1)
    
    def stop(self):
        self.recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

class PlaybackThread(QThread):
    playback_signal = pyqtSignal(str)
    
    def __init__(self, events):
        super().__init__()
        self.events = events
        self.running = False
        self.mouse = MouseController()
        
    def run(self):
        self.running = True
        if not self.events:
            return
            
        start_time = self.events[0]['timestamp']
        
        for event in self.events:
            if not self.running:
                break
                
            if event['type'] == 'click':
                delay = event['timestamp'] - start_time
                if delay > 0:
                    time.sleep(delay)
                
                x, y = event['x'], event['y']
                button = Button.left if 'left' in event['button'] else Button.right
                
                self.mouse.position = (x, y)
                self.mouse.click(button)
                
                self.playback_signal.emit(f"回放点击: ({x}, {y})")
                start_time = event['timestamp']
    
    def stop(self):
        self.running = False

class AutoClicker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.click_thread = None
        self.record_thread = None
        self.playback_thread = None
        self.config_file = 'config.ini'
        self.load_config()
        
        self.init_ui()
        self.setup_hotkeys()
        
    def load_config(self):
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.config['Settings'] = {
                'click_type': 'left',
                'interval': '100',
                'max_clicks': '0',
                'hotkey': 'f6',
                'hold_mode': 'false'
            }
            self.save_config()
    
    def save_config(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def init_ui(self):
        self.setWindowTitle('鼠标连点器')
        self.setGeometry(100, 100, 500, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 连点设置组
        click_group = QGroupBox("连点设置")
        click_layout = QVBoxLayout()
        
        # 点击类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("点击类型:"))
        self.click_type_combo = QComboBox()
        self.click_type_combo.addItems(["左键", "右键"])
        click_type = self.config['Settings'].get('click_type', 'left')
        self.click_type_combo.setCurrentText("左键" if click_type == 'left' else "右键")
        type_layout.addWidget(self.click_type_combo)
        click_layout.addLayout(type_layout)
        
        # 点击间隔
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("点击间隔 (毫秒):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 10000)
        self.interval_spin.setValue(int(self.config['Settings'].get('interval', '100')))
        interval_layout.addWidget(self.interval_spin)
        click_layout.addLayout(interval_layout)
        
        # 点击次数
        clicks_layout = QHBoxLayout()
        clicks_layout.addWidget(QLabel("点击次数 (0=无限):"))
        self.clicks_spin = QSpinBox()
        self.clicks_spin.setRange(0, 1000000)
        self.clicks_spin.setValue(int(self.config['Settings'].get('max_clicks', '0')))
        clicks_layout.addWidget(self.clicks_spin)
        click_layout.addLayout(clicks_layout)
        
        # 模式选择
        mode_layout = QHBoxLayout()
        self.hold_mode_check = QCheckBox("按住连点模式")
        self.hold_mode_check.setChecked(self.config['Settings'].getboolean('hold_mode', False))
        mode_layout.addWidget(self.hold_mode_check)
        click_layout.addLayout(mode_layout)
        
        click_group.setLayout(click_layout)
        layout.addWidget(click_group)
        
        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始连点")
        self.start_btn.clicked.connect(self.start_clicking)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止连点")
        self.stop_btn.clicked.connect(self.stop_clicking)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 录制控制
        record_group = QGroupBox("录制与回放")
        record_layout = QVBoxLayout()
        
        record_btn_layout = QHBoxLayout()
        self.record_start_btn = QPushButton("开始录制")
        self.record_start_btn.clicked.connect(self.start_recording)
        record_btn_layout.addWidget(self.record_start_btn)
        
        self.record_stop_btn = QPushButton("停止录制")
        self.record_stop_btn.clicked.connect(self.stop_recording)
        self.record_stop_btn.setEnabled(False)
        record_btn_layout.addWidget(self.record_stop_btn)
        
        self.playback_btn = QPushButton("回放录制")
        self.playback_btn.clicked.connect(self.playback_recording)
        record_btn_layout.addWidget(self.playback_btn)
        
        record_layout.addLayout(record_btn_layout)
        
        self.record_text = QTextEdit()
        self.record_text.setMaximumHeight(100)
        record_layout.addWidget(self.record_text)
        
        record_group.setLayout(record_layout)
        layout.addWidget(record_group)
        
        # 状态显示
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.status_label)
        
        # 热键提示
        hotkey_label = QLabel("热键: F6 - 开始/停止连点")
        hotkey_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hotkey_label)
        
        self.recorded_events = []
    
    def setup_hotkeys(self):
        kb.add_hotkey('f6', self.toggle_clicking)
    
    def toggle_clicking(self):
        if self.click_thread and self.click_thread.isRunning():
            self.stop_clicking()
        else:
            self.start_clicking()
    
    def start_clicking(self):
        click_type = 'left' if self.click_type_combo.currentText() == '左键' else 'right'
        interval = self.interval_spin.value()
        max_clicks = self.clicks_spin.value()
        hold_mode = self.hold_mode_check.isChecked()
        
        self.click_thread = ClickThread(click_type, interval, max_clicks, hold_mode)
        self.click_thread.click_signal.connect(self.update_click_count)
        self.click_thread.finished.connect(self.clicking_finished)
        
        self.click_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("连点中...")
        
        # 保存设置
        self.config['Settings']['click_type'] = click_type
        self.config['Settings']['interval'] = str(interval)
        self.config['Settings']['max_clicks'] = str(max_clicks)
        self.config['Settings']['hold_mode'] = str(hold_mode)
        self.save_config()
    
    def stop_clicking(self):
        if self.click_thread and self.click_thread.isRunning():
            self.click_thread.stop()
            self.click_thread.wait()
    
    def update_click_count(self):
        if self.click_thread:
            self.status_label.setText(f"已点击: {self.click_thread.click_count} 次")
    
    def clicking_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("连点完成")
    
    def start_recording(self):
        self.record_thread = RecordThread()
        self.record_thread.record_signal.connect(self.update_record_log)
        self.record_thread.finished.connect(self.recording_finished)
        
        self.record_thread.start()
        
        self.record_start_btn.setEnabled(False)
        self.record_stop_btn.setEnabled(True)
        self.status_label.setText("录制中...")
        self.record_text.clear()
    
    def stop_recording(self):
        if self.record_thread and self.record_thread.isRunning():
            self.recorded_events = self.record_thread.events
            self.record_thread.stop()
            self.record_thread.wait()
    
    def recording_finished(self):
        self.record_start_btn.setEnabled(True)
        self.record_stop_btn.setEnabled(False)
        self.status_label.setText(f"录制完成，共 {len(self.recorded_events)} 个事件")
    
    def update_record_log(self, text):
        self.record_text.append(text)
    
    def playback_recording(self):
        if not self.recorded_events:
            QMessageBox.warning(self, "警告", "没有录制的内容")
            return
        
        self.playback_thread = PlaybackThread(self.recorded_events)
        self.playback_thread.playback_signal.connect(self.update_record_log)
        self.playback_thread.finished.connect(self.playback_finished)
        
        self.playback_thread.start()
        self.status_label.setText("回放中...")
    
    def playback_finished(self):
        self.status_label.setText("回放完成")
    
    def closeEvent(self, a0):
        self.stop_clicking()
        if self.record_thread and self.record_thread.isRunning():
            self.record_thread.stop()
        if self.playback_thread and self.playback_thread.isRunning():
            self.playback_thread.stop()
        a0.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AutoClicker()
    window.show()
    sys.exit(app.exec_())