#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多位置鼠标连点器 - 支持设定多个位置并按编号依次点击
基于原生热键版本扩展
"""

import sys
import json
import threading
import time
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QSpinBox, QComboBox,
                             QGroupBox, QCheckBox, QSlider, QTextEdit, QShortcut,
                             QListWidget, QListWidgetItem, QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QCloseEvent, QKeySequence
from pynput.mouse import Controller, Button
from pynput import mouse

# 尝试导入原生macOS热键支持
try:
    from AppKit import NSApplication  # type: ignore
    import Quartz  # type: ignore
    NATIVE_HOTKEY_AVAILABLE = True
except Exception:
    NATIVE_HOTKEY_AVAILABLE = False
    class Quartz:  # type: ignore
        @staticmethod
        def CGEventTapCreate(*args): return None
        @staticmethod
        def CGEventTapEnable(*args): pass
        @staticmethod
        def CGEventGetIntegerValueField(*args): return 0
        @staticmethod
        def CGEventGetFlags(*args): return 0
        @staticmethod
        def CFMachPortCreateRunLoopSource(*args): return None
        @staticmethod
        def CFRunLoopAddSource(*args): pass
        @staticmethod
        def CFRunLoopGetCurrent(*args): return None
        @staticmethod
        def CFRunLoopRunInMode(*args): return None
        @staticmethod
        def CFMachPortInvalidate(*args): pass
        kCGEventKeyDown = 10
        kCGEventFlagsChanged = 12
        kCGKeyboardEventKeycode = 9
        kCGSessionEventTap = 0
        kCGHeadInsertEventTap = 0
        kCGEventTapOptionDefault = 0
        kCGHIDEventTap = 0
        kCGEventTapOptionListenOnly = 1
        kCGEventTapDisabledByTimeout = 0
        kCGEventTapDisabledByUserInput = 1
        kCFRunLoopCommonModes = 'kCFRunLoopCommonModes'
        kCFRunLoopDefaultMode = 'kCFRunLoopDefaultMode'
        kCGEventFlagMaskCommand = 1048576
        kCGEventFlagMaskAlternate = 524288
        kCGEventFlagMaskControl = 262144
        kCGEventFlagMaskShift = 131072


class MultiPositionClickWorker(QThread):
    """多位置点击工作线程"""
    finished = pyqtSignal()
    position_changed = pyqtSignal(int, str)  # 位置索引, 位置描述
    
    def __init__(self, positions, click_type, frequency, max_clicks, button_type, cycle_mode=True):
        super().__init__()
        self.positions = positions  # [(x, y, name), ...]
        self.click_type = click_type
        self.frequency = frequency
        self.max_clicks = max_clicks
        self.button_type = button_type
        self.cycle_mode = cycle_mode  # 是否循环点击所有位置
        self.running = False
        self.mouse = Controller()
        
    def run(self):
        """执行多位置点击"""
        self.running = True
        click_count = 0
        position_index = 0
        
        # 按钮映射
        button_map = {
            '左键': Button.left,
            '右键': Button.right,
            '中键': Button.middle
        }
        button = button_map.get(self.button_type, Button.left)
        
        # 计算点击间隔
        interval = 1.0 / self.frequency
        
        while self.running:
            if not self.positions:
                break
                
            # 检查最大点击次数
            if self.max_clicks > 0 and click_count >= self.max_clicks:
                break
                
            # 获取当前位置
            current_pos = self.positions[position_index]
            x, y, name = current_pos
            
            # 发送位置变更信号
            self.position_changed.emit(position_index + 1, name)
            
            # 移动鼠标到目标位置
            self.mouse.position = (x, y)
            time.sleep(0.01)  # 短暂延迟确保鼠标移动到位
            
            # 再次检查running状态
            if not self.running:
                break
            
            # 执行点击
            if self.click_type == '单击':
                self.mouse.click(button)
            elif self.click_type == '双击':
                self.mouse.click(button, 2)
                
            click_count += 1
            
            # 移动到下一个位置
            position_index = (position_index + 1) % len(self.positions)
            
            # 如果不是循环模式且已经点击完所有位置一轮，则停止
            if not self.cycle_mode and position_index == 0 and click_count >= len(self.positions):
                break
                
            # 等待下次点击 - 分解为小段sleep以便及时响应停止信号
            remaining_time = interval
            while remaining_time > 0 and self.running:
                sleep_time = min(0.05, remaining_time)  # 每次最多sleep 50ms
                time.sleep(sleep_time)
                remaining_time -= sleep_time
            
        self.finished.emit()
        
    def stop(self):
        """停止点击"""
        self.running = False


class NativeHotkeyManager:
    """原生热键管理器"""
    
    def __init__(self, callback_start, callback_stop):
        self.callback_start = callback_start
        self.callback_stop = callback_stop
        self.event_tap = None
        self.run_loop_source = None
        self.monitoring = False
        self.monitor_thread = None
        
        # 默认热键配置
        self.hotkey_config = {
            'start': {
                'ctrl': True, 'option': True, 'shift': False, 'command': False,
                'key': 'S'
            },
            'stop': {
                'ctrl': True, 'option': True, 'shift': False, 'command': False,
                'key': 'D'
            }
        }
        
    def update_hotkey_config(self, cfg: dict):
        """更新热键配置"""
        if 'start' in cfg:
            self.hotkey_config['start'].update(cfg['start'])
        if 'stop' in cfg:
            self.hotkey_config['stop'].update(cfg['stop'])
            
        # 重启监听
        if self.monitoring:
            self.stop_monitoring()
            self.start_monitoring()
            
    def start_monitoring(self):
        """开始监听热键"""
        if not NATIVE_HOTKEY_AVAILABLE or self.monitoring:
            return False
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._run_event_tap, daemon=True)
        self.monitor_thread.start()
        return True
        
    def stop_monitoring(self):
        """停止监听热键"""
        self.monitoring = False
        
        if self.event_tap:
            try:
                Quartz.CGEventTapEnable(self.event_tap, False)
                if self.run_loop_source:
                    Quartz.CFMachPortInvalidate(self.run_loop_source)  # type: ignore
                self.event_tap = None
                self.run_loop_source = None
            except Exception as e:
                print(f"停止热键监听时出错: {e}")
                
    def _run_event_tap(self):
        """运行事件监听"""
        try:
            def event_callback(proxy, event_type, event, refcon):
                try:
                    if event_type == Quartz.kCGEventKeyDown:
                        keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
                        flags = Quartz.CGEventGetFlags(event)
                        
                        # 检查开始热键
                        if self._check_hotkey_match(keycode, flags, 'start'):
                            self.callback_start()
                            
                        # 检查停止热键
                        elif self._check_hotkey_match(keycode, flags, 'stop'):
                            self.callback_stop()
                            
                except Exception as e:
                    print(f"热键回调错误: {e}")
                    
                return event
                
            # 创建事件监听
            self.event_tap = Quartz.CGEventTapCreate(
                Quartz.kCGSessionEventTap,
                Quartz.kCGHeadInsertEventTap,
                Quartz.kCGEventTapOptionDefault,
                1 << Quartz.kCGEventKeyDown,
                event_callback,
                None
            )
            
            if not self.event_tap:
                print("无法创建事件监听")
                return
                
            # 创建运行循环源
            self.run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, self.event_tap, 0)
            Quartz.CFRunLoopAddSource(Quartz.CFRunLoopGetCurrent(), self.run_loop_source, Quartz.kCFRunLoopCommonModes)
            
            # 启用事件监听
            Quartz.CGEventTapEnable(self.event_tap, True)
            
            # 运行事件循环
            while self.monitoring:
                Quartz.CFRunLoopRunInMode(Quartz.kCFRunLoopDefaultMode, 0.1, False)
                
        except Exception as e:
            print(f"热键监听错误: {e}")
            
    def _check_hotkey_match(self, keycode, flags, hotkey_type):
        """检查热键是否匹配"""
        config = self.hotkey_config[hotkey_type]
        
        # 键码映射
        key_map = {
            'S': 1, 'D': 2, 'F': 3, 'G': 5, 'H': 4, 'J': 38, 'K': 40, 'L': 37
        }
        
        expected_keycode = key_map.get(config['key'], 1)
        if keycode != expected_keycode:
            return False
            
        # 检查修饰键
        ctrl_pressed = bool(flags & Quartz.kCGEventFlagMaskControl)  # type: ignore
        option_pressed = bool(flags & Quartz.kCGEventFlagMaskAlternate)  # type: ignore
        shift_pressed = bool(flags & Quartz.kCGEventFlagMaskShift)  # type: ignore
        command_pressed = bool(flags & Quartz.kCGEventFlagMaskCommand)  # type: ignore
        
        return (ctrl_pressed == config['ctrl'] and
                option_pressed == config['option'] and
                shift_pressed == config['shift'] and
                command_pressed == config['command'])


class AutoClickerMultiPosition(QMainWindow):
    hotkey_start_signal = pyqtSignal()
    hotkey_stop_signal = pyqtSignal()
    emergency_stop_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.click_worker = None
        self.positions = []  # [(x, y, name), ...]
        self.capturing_position = False
        self.mouse_listener = None
        
        # 紧急停止相关
        self.emergency_mouse_listener = None
        self.emergency_keyboard_listener = None
        self.esc_press_count = 0
        self.last_esc_time = 0
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.expanduser('~'), '.auto_clicker_multi_config.json')
        
        # 热键配置
        self.hotkey_config = {
            'start': {
                'ctrl': True, 'option': True, 'shift': False, 'command': False,
                'key': 'S'
            },
            'stop': {
                'ctrl': True, 'option': True, 'shift': False, 'command': False,
                'key': 'D'
            }
        }
        

        
        self.init_ui()
        self.setup_hotkeys()
        
        # 初始化热键配置UI（在UI创建之后）
        self._refresh_hotkey_ui()
        self.load_config()
        
    def init_ui(self):
        self.setWindowTitle('多位置鼠标连点器 - 原生热键版')
        self.setGeometry(100, 100, 500, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel('多位置鼠标连点器')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 位置管理组
        position_group = QGroupBox("位置管理")
        position_layout = QVBoxLayout()
        
        # 位置列表
        self.position_list = QListWidget()
        self.position_list.setMaximumHeight(150)
        position_layout.addWidget(QLabel('点击位置列表:'))
        position_layout.addWidget(self.position_list)
        
        # 位置操作按钮
        pos_button_layout = QHBoxLayout()
        
        self.capture_position_btn = QPushButton('捕获位置')
        self.capture_position_btn.clicked.connect(self.start_position_capture)
        pos_button_layout.addWidget(self.capture_position_btn)
        
        self.remove_position_btn = QPushButton('删除选中')
        self.remove_position_btn.clicked.connect(self.remove_selected_position)
        pos_button_layout.addWidget(self.remove_position_btn)
        
        self.clear_positions_btn = QPushButton('清空所有')
        self.clear_positions_btn.clicked.connect(self.clear_all_positions)
        pos_button_layout.addWidget(self.clear_positions_btn)
        
        position_layout.addLayout(pos_button_layout)
        position_group.setLayout(position_layout)
        layout.addWidget(position_group)
        
        # 基本设置组
        basic_group = QGroupBox("基本设置")
        basic_layout = QVBoxLayout()
        
        # 点击类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel('点击类型:'))
        self.click_type_combo = QComboBox()
        self.click_type_combo.addItems(['单击', '双击'])
        type_layout.addWidget(self.click_type_combo)
        basic_layout.addLayout(type_layout)
        
        # 点击频率
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel('点击频率:'))
        self.frequency_spin = QSpinBox()
        self.frequency_spin.setRange(1, 100)
        self.frequency_spin.setValue(5)
        self.frequency_spin.setSuffix(' 次/秒')
        freq_layout.addWidget(self.frequency_spin)
        basic_layout.addLayout(freq_layout)
        
        # 最大点击次数
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel('最大次数:'))
        self.max_clicks_spin = QSpinBox()
        self.max_clicks_spin.setRange(0, 99999)
        self.max_clicks_spin.setValue(0)
        self.max_clicks_spin.setSpecialValueText('无限制')
        max_layout.addWidget(self.max_clicks_spin)
        basic_layout.addLayout(max_layout)
        
        # 鼠标按钮
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel('鼠标按钮:'))
        self.button_combo = QComboBox()
        self.button_combo.addItems(['左键', '右键', '中键'])
        button_layout.addWidget(self.button_combo)
        basic_layout.addLayout(button_layout)
        
        # 循环模式
        cycle_layout = QHBoxLayout()
        self.cycle_checkbox = QCheckBox('循环点击所有位置')
        self.cycle_checkbox.setChecked(True)
        cycle_layout.addWidget(self.cycle_checkbox)
        basic_layout.addLayout(cycle_layout)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # 控制按钮组
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout()
        
        # 开始/停止按钮
        button_layout = QHBoxLayout()
        self.start_button = QPushButton('开始多位置连点')
        self.start_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        self.start_button.clicked.connect(self.start_clicking)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton('停止连点')
        self.stop_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
        self.stop_button.clicked.connect(self.stop_clicking)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        control_layout.addLayout(button_layout)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 热键状态组
        hotkey_group = QGroupBox("热键状态")
        hotkey_layout = QVBoxLayout()
        
        if NATIVE_HOTKEY_AVAILABLE:
            self.hotkey_status = QLabel('✅ 原生热键支持可用')
            self.hotkey_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.hotkey_status = QLabel('❌ 原生热键不可用，请使用界面按钮')
            self.hotkey_status.setStyleSheet("color: orange; font-weight: bold;")
            
        hotkey_layout.addWidget(self.hotkey_status)
        
        hotkey_help = QLabel('Ctrl+Option+S: 开始连点\nCtrl+Option+D: 停止连点\n或使用上方按钮控制')
        hotkey_help.setStyleSheet("color: #666; font-size: 12px;")
        hotkey_layout.addWidget(hotkey_help)
        
        # 自定义热键设置
        hk_cfg_group = QGroupBox("自定义热键")
        hk_cfg_layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('开始组合:'))
        self.chk_start_ctrl = QCheckBox('Ctrl')
        self.chk_start_opt = QCheckBox('Option')
        self.chk_start_shift = QCheckBox('Shift')
        self.chk_start_cmd = QCheckBox('Command')
        for w in (self.chk_start_ctrl, self.chk_start_opt, self.chk_start_shift, self.chk_start_cmd):
            row1.addWidget(w)
        row1.addWidget(QLabel('键:'))
        self.cmb_start_key = QComboBox()
        self.cmb_start_key.addItems(['S','D','F','G','H','J','K','L'])
        row1.addWidget(self.cmb_start_key)
        hk_cfg_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel('停止组合:'))
        self.chk_stop_ctrl = QCheckBox('Ctrl')
        self.chk_stop_opt = QCheckBox('Option')
        self.chk_stop_shift = QCheckBox('Shift')
        self.chk_stop_cmd = QCheckBox('Command')
        for w in (self.chk_stop_ctrl, self.chk_stop_opt, self.chk_stop_shift, self.chk_stop_cmd):
            row2.addWidget(w)
        row2.addWidget(QLabel('键:'))
        self.cmb_stop_key = QComboBox()
        self.cmb_stop_key.addItems(['D','S','F','G','H','J','K','L'])
        row2.addWidget(self.cmb_stop_key)
        hk_cfg_layout.addLayout(row2)
        
        btn_row = QHBoxLayout()
        self.btn_apply_hotkey = QPushButton('应用热键')
        self.btn_apply_hotkey.clicked.connect(self.apply_hotkey_settings)
        btn_row.addWidget(self.btn_apply_hotkey)
        hk_cfg_layout.addLayout(btn_row)
        
        hk_cfg_group.setLayout(hk_cfg_layout)
        hotkey_layout.addWidget(hk_cfg_group)

        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # 状态信息
        self.status_label = QLabel('准备就绪')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e8; border-radius: 5px;")
        layout.addWidget(self.status_label)
        
        # 当前位置显示
        self.current_position_label = QLabel('当前位置: 无')
        self.current_position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_position_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        layout.addWidget(self.current_position_label)
        
        # 使用说明
        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout()
        
        help_text = QTextEdit()
        help_text.setMaximumHeight(120)
        help_text.setPlainText(
            "1. 添加多个点击位置（可以手动添加当前位置或捕获位置）\n"
            "2. 设置点击参数\n"
            "3. 选择是否循环点击所有位置\n"
            "4. 使用按钮或按 Ctrl+Option+S 开始连点\n"
            "5. 按 Ctrl+Option+D 或点击停止按钮结束\n"
            "6. 程序会按照编号依次点击各个位置"
        )
        help_text.setReadOnly(True)
        help_layout.addWidget(help_text)
        
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)
        
        central_widget.setLayout(layout)
        
    def setup_hotkeys(self):
        """设置热键"""
        native_ok = False
        if NATIVE_HOTKEY_AVAILABLE:
            self.hotkey_manager = NativeHotkeyManager(
                self.hotkey_start_signal.emit,
                self.hotkey_stop_signal.emit
            )
            self.hotkey_manager.update_hotkey_config(self.hotkey_config)
            native_ok = self.hotkey_manager.start_monitoring()
            
        if not native_ok:
            # 备用热键方案
            self.shortcut_start = QShortcut(QKeySequence('Ctrl+Alt+S'), self)
            self.shortcut_start.activated.connect(self.start_clicking)
            
            self.shortcut_stop = QShortcut(QKeySequence('Ctrl+Alt+D'), self)
            self.shortcut_stop.activated.connect(self.stop_clicking)
            
        # 连接热键信号
        self.hotkey_start_signal.connect(self.start_clicking)
        self.hotkey_stop_signal.connect(self.stop_clicking)
        self.emergency_stop_signal.connect(self.emergency_stop)
        
        # 启动紧急停止监听
        self.setup_emergency_stop()
        
    def start_position_capture(self):
        """开始捕获位置"""
        if self.capturing_position:
            return
            
        self.capturing_position = True
        self.capture_position_btn.setText('点击鼠标捕获位置...')
        self.capture_position_btn.setEnabled(False)
        
        def on_click(x, y, button, pressed):
            print(f"鼠标事件: x={x}, y={y}, button={button}, pressed={pressed}")  # 调试信息
            if pressed and button == Button.left:
                print(f"检测到左键点击: ({x}, {y})")  # 调试信息
                # 保存坐标并使用QTimer在主线程中执行UI操作
                self.captured_x = x
                self.captured_y = y
                print("调用QTimer.singleShot")  # 调试信息
                QTimer.singleShot(0, self.handle_position_capture)
                return False  # 停止监听
                
        try:
            self.mouse_listener = mouse.Listener(on_click=on_click)
            self.mouse_listener.start()
        except Exception as e:
            print(f"启动鼠标监听失败: {e}")
            self.capturing_position = False
            self.capture_position_btn.setText('捕获位置')
            self.capture_position_btn.setEnabled(True)
    
    def handle_position_capture(self):
        """处理位置捕获的UI操作"""
        print("handle_position_capture函数被调用")  # 调试信息
        try:
            x, y = self.captured_x, self.captured_y
            # 确保窗口在最前面
            self.raise_()
            self.activateWindow()
            
            # 弹出坐标确认对话框
            msg = QMessageBox(self)
            msg.setWindowTitle('确认添加位置')
            msg.setText(f'检测到鼠标点击位置:\n\n坐标: ({int(x)}, {int(y)})\n\n是否要添加此位置到点击列表？')
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.Yes)
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)  # type: ignore
            
            print("显示对话框")  # 调试信息
            reply = msg.exec_()
            print(f"对话框返回: {reply}")  # 调试信息
            
            if reply == QMessageBox.Yes:
                # 询问位置名称
                name, ok = QInputDialog.getText(self, '输入位置名称', '请输入此位置的名称:', text=f'位置{len(self.positions)+1}')
                if ok and name.strip():
                    self.positions.append((int(x), int(y), name.strip()))
                    self.update_position_list()
                    self.save_config()
                    print(f"位置已添加: {name.strip()} ({int(x)}, {int(y)})")
                else:
                    print("位置添加被取消")
            else:
                print("用户取消添加位置")
        except Exception as e:
            print(f"处理坐标确认时出错: {e}")
        finally:
            # 重置捕获状态
            self.capturing_position = False
            self.capture_position_btn.setText('捕获位置')
            self.capture_position_btn.setEnabled(True)
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            print("捕获状态已重置")
        
    def remove_selected_position(self):
        """删除选中的位置"""
        current_row = self.position_list.currentRow()
        if current_row >= 0:
            del self.positions[current_row]
            self.update_position_list()
            self.save_config()
            
    def clear_all_positions(self):
        """清空所有位置"""
        reply = QMessageBox.question(self, '确认', '确定要清空所有位置吗？', 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.positions.clear()
            self.update_position_list()
            self.save_config()
            
    def update_position_list(self):
        """更新位置列表显示"""
        self.position_list.clear()
        for i, (x, y, name) in enumerate(self.positions):
            item_text = f"{i+1}. {name} ({x}, {y})"
            self.position_list.addItem(item_text)
            
    def check_accessibility_permission(self):
        """检查辅助功能权限"""
        try:
            # 在打包的应用中，直接尝试执行鼠标操作来检测权限
            from pynput.mouse import Controller
            from pynput import mouse
            
            # 方法1: 尝试创建鼠标监听器
            try:
                test_listener = mouse.Listener(on_click=lambda x, y, button, pressed: None)
                test_listener.start()
                time.sleep(0.1)
                test_listener.stop()
                # 如果能成功创建监听器，说明有权限
                return True
            except Exception:
                pass
            
            # 方法2: 尝试鼠标控制
            mouse_controller = Controller()
            
            # 获取当前位置
            original_pos = mouse_controller.position
            
            # 尝试移动鼠标一个很小的距离
            test_pos = (original_pos[0] + 1, original_pos[1] + 1)
            mouse_controller.position = test_pos
            time.sleep(0.05)
            
            # 检查是否真的移动了
            new_pos = mouse_controller.position
            
            # 恢复原位置
            mouse_controller.position = original_pos
            
            # 如果位置变化很小，说明有权限
            if abs(new_pos[0] - test_pos[0]) <= 2 and abs(new_pos[1] - test_pos[1]) <= 2:
                return True
            
            return False
            
        except Exception:
            return False
    
    def show_permission_dialog(self):
        """显示权限设置对话框"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle('需要辅助功能权限')
        msg.setText('多位置连点功能需要辅助功能权限才能正常工作。')
        msg.setInformativeText(
            '请按照以下步骤设置权限：\n\n'
            '1. 打开 系统偏好设置\n'
            '2. 选择 安全性与隐私\n'
            '3. 点击 辅助功能 标签\n'
            '4. 点击左下角的锁图标解锁\n'
            '5. 添加此应用程序到允许列表\n'
            '6. 重启应用程序\n\n'
            '设置完成后，请重新尝试开始连点。'
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def start_clicking(self):
        """开始多位置连点"""
        if self.click_worker and self.click_worker.isRunning():
            return
            
        if not self.positions:
            QMessageBox.warning(self, '警告', '请先添加至少一个点击位置！')
            return
        
        # 检查辅助功能权限
        if not self.check_accessibility_permission():
            self.show_permission_dialog()
            return
            
        click_type = self.click_type_combo.currentText()
        frequency = self.frequency_spin.value()
        max_clicks = self.max_clicks_spin.value()
        button_type = self.button_combo.currentText()
        cycle_mode = self.cycle_checkbox.isChecked()
        
        self.click_worker = MultiPositionClickWorker(
            self.positions, click_type, frequency, max_clicks, button_type, cycle_mode
        )
        self.click_worker.finished.connect(self.on_clicking_finished)
        self.click_worker.position_changed.connect(self.on_position_changed)
        self.click_worker.start()
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText(f'多位置连点中... ({frequency}次/秒, {len(self.positions)}个位置)')
        self.status_label.setStyleSheet("padding: 10px; background-color: #fff3cd; border-radius: 5px;")
        
        self.save_config()
        
    def setup_emergency_stop(self):
        """设置紧急停止功能"""
        try:
            # 鼠标移动到屏幕角落紧急停止
            def on_mouse_move(x, y):
                if self.click_worker and self.click_worker.isRunning():
                    # 获取屏幕尺寸
                    screen = QApplication.primaryScreen()
                    if screen:
                        screen_rect = screen.geometry()
                        screen_width = screen_rect.width()
                        screen_height = screen_rect.height()
                    else:
                        screen_width = 1920  # 默认值
                        screen_height = 1080
                    
                    # 检查是否移动到屏幕四个角落（容差20像素）
                    corner_tolerance = 20
                    if ((x <= corner_tolerance and y <= corner_tolerance) or  # 左上角
                        (x >= screen_width - corner_tolerance and y <= corner_tolerance) or  # 右上角
                        (x <= corner_tolerance and y >= screen_height - corner_tolerance) or  # 左下角
                        (x >= screen_width - corner_tolerance and y >= screen_height - corner_tolerance)):  # 右下角
                        self.emergency_stop_signal.emit()
            
            # 连续按ESC键紧急停止
            def on_key_press(key):
                try:
                    from pynput.keyboard import Key
                    # 检查是否按下ESC键
                    if key == Key.esc:
                        current_time = time.time()
                        # 如果距离上次按ESC不超过1秒，计数增加
                        if current_time - self.last_esc_time <= 1.0:
                            self.esc_press_count += 1
                        else:
                            self.esc_press_count = 1
                        
                        self.last_esc_time = current_time
                        print(f"ESC按键检测: 第{self.esc_press_count}次")
                        
                        # 连续按3次ESC触发紧急停止
                        if self.esc_press_count >= 3:
                            print("触发紧急停止！")
                            self.esc_press_count = 0
                            if self.click_worker and self.click_worker.isRunning():
                                self.emergency_stop_signal.emit()
                except Exception as e:
                    print(f"ESC键检测错误: {e}")
                    pass
            
            # 启动监听器
            from pynput import mouse, keyboard
            self.emergency_mouse_listener = mouse.Listener(on_move=on_mouse_move)
            self.emergency_keyboard_listener = keyboard.Listener(on_press=on_key_press)
            
            self.emergency_mouse_listener.start()
            self.emergency_keyboard_listener.start()
            
        except Exception as e:
            print(f"紧急停止功能启动失败: {e}")
    
    def emergency_stop(self):
        """紧急停止"""
        if self.click_worker and self.click_worker.isRunning():
            self.click_worker.stop()
            self.status_label.setText('🚨 紧急停止！')
            self.status_label.setStyleSheet("padding: 10px; background-color: #ff6b6b; color: white; border-radius: 5px; font-weight: bold;")
            
            # 3秒后恢复状态
            def reset_status():
                self.status_label.setText('准备就绪')
                self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e8; border-radius: 5px;")
            QTimer.singleShot(3000, reset_status)
    
    def stop_clicking(self):
        """停止连点"""
        if self.click_worker:
            self.click_worker.stop()
            
    def on_clicking_finished(self):
        """连点完成"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText('已停止')
        self.status_label.setStyleSheet("padding: 10px; background-color: #f8d7da; border-radius: 5px;")
        self.current_position_label.setText('当前位置: 无')
        
        # 3秒后恢复准备状态
        def reset_status():
            self.status_label.setText('准备就绪')
            self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e8; border-radius: 5px;")
        QTimer.singleShot(3000, reset_status)
        
    def on_position_changed(self, position_index, position_name):
        """位置变更时更新显示"""
        self.current_position_label.setText(f'当前位置: {position_index}. {position_name}')
        
    def save_config(self):
        """保存配置"""
        config = {
            'positions': self.positions,
            'click_type': self.click_type_combo.currentText(),
            'frequency': self.frequency_spin.value(),
            'max_clicks': self.max_clicks_spin.value(),
            'button_type': self.button_combo.currentText(),
            'cycle_mode': self.cycle_checkbox.isChecked(),
            'hotkey_config': self.hotkey_config
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
            
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 加载位置
                if 'positions' in config:
                    # 加载位置列表，确保坐标为数字类型
                    loaded_positions = config['positions']
                    self.positions = []
                    for pos in loaded_positions:
                        if isinstance(pos, dict):
                            # 处理字典格式 {'x': x, 'y': y, 'name': name}
                            self.positions.append((int(pos['x']), int(pos['y']), pos['name']))
                        elif isinstance(pos, (list, tuple)) and len(pos) >= 3:
                            # 处理列表/元组格式 [x, y, name] 或 (x, y, name)
                            self.positions.append((int(pos[0]), int(pos[1]), pos[2]))
                        else:
                            print(f"跳过无效位置数据: {pos}")
                    self.update_position_list()
                    
                # 加载基本设置
                if 'click_type' in config and hasattr(self, 'click_type_combo'):
                    index = self.click_type_combo.findText(config['click_type'])
                    if index >= 0:
                        self.click_type_combo.setCurrentIndex(index)
                        
                if 'frequency' in config and hasattr(self, 'frequency_spin'):
                    self.frequency_spin.setValue(config['frequency'])
                    
                if 'max_clicks' in config and hasattr(self, 'max_clicks_spin'):
                    self.max_clicks_spin.setValue(config['max_clicks'])
                    
                if 'button_type' in config and hasattr(self, 'button_combo'):
                    index = self.button_combo.findText(config['button_type'])
                    if index >= 0:
                        self.button_combo.setCurrentIndex(index)
                        
                if 'cycle_mode' in config and hasattr(self, 'cycle_checkbox'):
                    self.cycle_checkbox.setChecked(config['cycle_mode'])
                    
                # 加载热键配置
                if 'hotkey_config' in config:
                    self.hotkey_config.update(config['hotkey_config'])
                    self._refresh_hotkey_ui()
                    
        except Exception as e:
            print(f"加载配置失败: {e}")
            
    def closeEvent(self, a0):
        """关闭事件"""
        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager.stop_monitoring()
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        # 停止紧急停止监听器
        if self.emergency_mouse_listener:
            self.emergency_mouse_listener.stop()
        if self.emergency_keyboard_listener:
            self.emergency_keyboard_listener.stop()
        
        self.save_config()
        if a0:
            a0.accept()
        super().closeEvent(a0)
        
    def _init_hotkey_config_ui(self):
         """初始化热键配置UI"""
         # 设置开始热键的默认值
         self.chk_start_ctrl.setChecked(self.hotkey_config['start']['ctrl'])
         self.chk_start_opt.setChecked(self.hotkey_config['start']['option'])
         self.chk_start_shift.setChecked(self.hotkey_config['start']['shift'])
         self.chk_start_cmd.setChecked(self.hotkey_config['start']['command'])
         self.cmb_start_key.setCurrentText(self.hotkey_config['start']['key'])
         
         # 设置停止热键的默认值
         self.chk_stop_ctrl.setChecked(self.hotkey_config['stop']['ctrl'])
         self.chk_stop_opt.setChecked(self.hotkey_config['stop']['option'])
         self.chk_stop_shift.setChecked(self.hotkey_config['stop']['shift'])
         self.chk_stop_cmd.setChecked(self.hotkey_config['stop']['command'])
         self.cmb_stop_key.setCurrentText(self.hotkey_config['stop']['key'])
        
    def _refresh_hotkey_ui(self):
        """刷新热键配置UI"""
        if hasattr(self, 'chk_start_ctrl'):
            self._init_hotkey_config_ui()
            
    def apply_hotkey_settings(self):
         """应用热键设置"""
         # 更新热键配置
         self.hotkey_config['start'] = {
             'ctrl': self.chk_start_ctrl.isChecked(),
             'option': self.chk_start_opt.isChecked(),
             'shift': self.chk_start_shift.isChecked(),
             'command': self.chk_start_cmd.isChecked(),
             'key': self.cmb_start_key.currentText()
         }
         
         self.hotkey_config['stop'] = {
             'ctrl': self.chk_stop_ctrl.isChecked(),
             'option': self.chk_stop_opt.isChecked(),
             'shift': self.chk_stop_shift.isChecked(),
             'command': self.chk_stop_cmd.isChecked(),
             'key': self.cmb_stop_key.currentText()
         }
         
         # 更新原生热键管理器
         if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
             # 先停止当前监听
             self.hotkey_manager.stop_monitoring()
             # 更新配置
             self.hotkey_manager.update_hotkey_config(self.hotkey_config)
             # 重新启动监听
             if not self.hotkey_manager.start_monitoring():
                 QMessageBox.warning(self, '热键设置', '热键更新失败，请检查权限设置')
                 return
             
         # 保存配置
         self.save_config()
         
         # 显示确认消息
         QMessageBox.information(self, '设置已应用', '热键设置已更新并保存！')


def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("多位置鼠标连点器")
    app.setApplicationVersion("2.0")
    
    window = AutoClickerMultiPosition()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()