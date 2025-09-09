#!/usr/bin/env python3
"""
鼠标连点器 - 原生macOS热键版本
使用AppKit和Cocoa实现更好的macOS兼容性
"""

import sys
import json
import threading
import time
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLabel, QSpinBox, QComboBox,
                             QGroupBox, QCheckBox, QSlider, QTextEdit, QShortcut)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QCloseEvent, QKeySequence
from pynput.mouse import Controller, Button

try:
    # 尝试导入原生macOS热键支持
    from AppKit import NSApplication
    from Quartz import (
        CGEventTapCreate, CGEventTapEnable, CGEventGetIntegerValueField,
        kCGEventKeyDown, kCGEventFlagsChanged, kCGKeyboardEventKeycode,
        kCGSessionEventTap, kCGHeadInsertEventTap, kCGEventTapOptionDefault,
        kCGHIDEventTap, kCGEventTapOptionListenOnly,
        kCGEventTapDisabledByTimeout, kCGEventTapDisabledByUserInput,
        CFMachPortCreateRunLoopSource, CFMachPortInvalidate,
        CFRunLoopGetCurrent, CFRunLoopAddSource, CFRunLoopRunInMode,
        kCFRunLoopCommonModes, kCFRunLoopDefaultMode
    )
    from Quartz import CGEventGetFlags, kCGEventFlagMaskCommand, kCGEventFlagMaskAlternate, kCGEventFlagMaskControl, kCGEventFlagMaskShift

    NATIVE_HOTKEY_AVAILABLE = True
except Exception:
    NATIVE_HOTKEY_AVAILABLE = False


class ClickWorker(QThread):
    """连点工作线程"""
    finished = pyqtSignal()
    
    def __init__(self, click_type, frequency, max_clicks, button_type):
        super().__init__()
        self.click_type = click_type
        self.frequency = frequency
        self.max_clicks = max_clicks
        self.button_type = button_type
        self.running = False
        self.mouse = Controller()
        
    def run(self):
        self.running = True
        click_count = 0
        interval = 1.0 / self.frequency
        
        # 按钮映射
        button_map = {
            '左键': Button.left,
            '右键': Button.right,
            '中键': Button.middle
        }
        button = button_map.get(self.button_type, Button.left)
        
        while self.running and (self.max_clicks == 0 or click_count < self.max_clicks):
            try:
                if self.click_type == '单击':
                    self.mouse.click(button)
                elif self.click_type == '双击':
                    self.mouse.click(button, 2)
                    
                click_count += 1
                time.sleep(interval)
            except Exception as e:
                print(f"点击错误: {e}")
                break
                
        self.finished.emit()
        
    def stop(self):
        self.running = False


class NativeHotkeyManager:
    """原生macOS热键管理器（使用Quartz Event Tap实现全局热键F6/F7）"""
    
    def __init__(self, callback_start, callback_stop):
        self.callback_start = callback_start
        self.callback_stop = callback_stop
        self.monitoring = False
        self.tap = None
        self.run_loop_source = None
        self.thread = None
        # macOS 虚拟键码：F6=0x3E(62), F7=0x3F(63)
        self.VK_F6 = 0x3E
        self.VK_F7 = 0x3F
        # Apple 硬件键码与兼容映射
        self.VK_F6_SET = {97, 62}
        self.VK_F7_SET = {98, 63}
        # 组合键配置（动态更新）: 修饰键集合与主键的硬件码集合
        self.combo_start_modmask = (kCGEventFlagMaskControl | kCGEventFlagMaskAlternate)  # 默认 Ctrl+Option
        self.combo_stop_modmask = (kCGEventFlagMaskControl | kCGEventFlagMaskAlternate)
        self.combo_start_keycodes = {1}  # 默认 S
        self.combo_stop_keycodes = {2}  # 默认 D
    
    def update_hotkey_config(self, cfg: dict):
        """从窗口配置计算出需要的标志位与主键硬件码集合"""
        def mods_to_mask(mods):
            mask = 0
            for m in mods:
                if m == 'Ctrl':
                    mask |= int(kCGEventFlagMaskControl)
                elif m == 'Option':
                    mask |= int(kCGEventFlagMaskAlternate)
                elif m == 'Shift':
                    mask |= int(kCGEventFlagMaskShift)
                elif m == 'Command':
                    mask |= int(kCGEventFlagMaskCommand)
            return mask
        def key_to_codes(k):
            # 仅支持主键 S/D/F/G/H/J/K/L，使用常见 ANSI 美式布局硬件键码
            mapping = {
                'S': 1, 'D': 2, 'F': 3, 'G': 5, 'H': 4, 'J': 38, 'K': 40, 'L': 37
            }
            c = mapping.get(k.upper())
            return {c} if c is not None else set()
        self.combo_start_modmask = mods_to_mask(cfg.get('start_mods', []))
        self.combo_stop_modmask = mods_to_mask(cfg.get('stop_mods', []))
        self.combo_start_keycodes = key_to_codes(cfg.get('start_key', 'S')) or {1}
        self.combo_stop_keycodes = key_to_codes(cfg.get('stop_key', 'D')) or {2}

    def start_monitoring(self):
        """开始监听全局热键"""
        if not NATIVE_HOTKEY_AVAILABLE:
            return False
        if self.monitoring:
            return True
        try:
            self.monitoring = True
            self.thread = threading.Thread(target=self._run_event_tap, daemon=True)
            self.thread.start()
            return True
        except Exception as e:
            print(f"热键监听启动失败: {e}")
            self.monitoring = False
            return False
    
    def stop_monitoring(self):
        """停止监听全局热键"""
        self.monitoring = False
        try:
            if self.tap is not None:
                CFMachPortInvalidate(self.tap)  # type: ignore[name-defined]
                self.tap = None
            if self.run_loop_source is not None:
                self.run_loop_source = None
        except Exception:
            pass
    
    def _run_event_tap(self):
        # noinspection PyUnresolvedReferences
        def event_callback(proxy, event_type, event, refcon):
            # 处理tap被系统禁用（超时或用户输入）
            if event_type in (kCGEventTapDisabledByTimeout, kCGEventTapDisabledByUserInput):  # type: ignore[name-defined]
                try:
                    print("[NativeHotkey] 事件Tap被禁用，尝试重新启用...")
                except Exception:
                    pass
                CGEventTapEnable(self.tap, True)  # type: ignore[name-defined]
                return event
            if event_type == kCGEventKeyDown:  # type: ignore[name-defined]
                keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)  # type: ignore[name-defined]
                flags = CGEventGetFlags(event)  # type: ignore[name-defined]
                try:
                    print(f"[NativeHotkey] keyDown keycode={keycode} flags=0x{int(flags):x}")
                except Exception:
                    pass
                # 组合键判定优先，其次保留 F6/F7 兜底
                if (int(flags) & int(self.combo_start_modmask)) == int(self.combo_start_modmask) and int(keycode) in self.combo_start_keycodes:
                    self.callback_start()
                elif (int(flags) & int(self.combo_stop_modmask)) == int(self.combo_stop_modmask) and int(keycode) in self.combo_stop_keycodes:
                    self.callback_stop()
                elif int(keycode) in self.VK_F6_SET:
                    self.callback_start()
                elif int(keycode) in self.VK_F7_SET:
                    self.callback_stop()

                # 调试输出：看到任意按键就打印键码与修饰键
                try:
                    print(f"[NativeHotkey] keyDown keycode={keycode} flags=0x{int(flags):x}")
                except Exception:
                    pass
                # 组合键方案：Ctrl + Option + S 开始；Ctrl + Option + D 停止
                want_mod = (kCGEventFlagMaskControl | kCGEventFlagMaskAlternate)  # type: ignore[name-defined]
                if (int(flags) & want_mod) == want_mod:
                    # 键位：S=1, D=2 在硬件键码上（美式布局）。为了兼容，保留 F6/F7 触发。
                    if int(keycode) in (1,) or int(keycode) in self.VK_F6_SET:
                        self.callback_start()
                    elif int(keycode) in (2,) or int(keycode) in self.VK_F7_SET:
                        self.callback_stop()
            return event

        mask = (
            (1 << kCGEventKeyDown) |  # type: ignore[name-defined]
            (1 << kCGEventFlagsChanged)  # type: ignore[name-defined]
        )
        # 持有回调引用，避免被GC
        self._event_callback = event_callback
        self.tap = CGEventTapCreate(  # type: ignore[name-defined]
            kCGHIDEventTap,  # type: ignore[name-defined]
            kCGHeadInsertEventTap,  # type: ignore[name-defined]
            kCGEventTapOptionListenOnly,  # type: ignore[name-defined]
            mask,
            self._event_callback,
            None
        )
        if not self.tap:
            # HID层失败时回退到Session层
            try:
                print("[NativeHotkey] HID层EventTap创建失败，回退到Session层...")
            except Exception:
                pass
            self.tap = CGEventTapCreate(  # type: ignore[name-defined]
                kCGSessionEventTap,  # type: ignore[name-defined]
                kCGHeadInsertEventTap,  # type: ignore[name-defined]
                kCGEventTapOptionListenOnly,  # type: ignore[name-defined]
                mask,
                self._event_callback,
                None
            )
        if not self.tap:
            print("[NativeHotkey] EventTap创建失败，请检查输入监控权限")
            self.monitoring = False
            return

        self.run_loop_source = CFMachPortCreateRunLoopSource(None, self.tap, 0)  # type: ignore[name-defined]
        loop = CFRunLoopGetCurrent()  # type: ignore[name-defined]
        CFRunLoopAddSource(loop, self.run_loop_source, kCFRunLoopCommonModes)  # type: ignore[name-defined]
        CGEventTapEnable(self.tap, True)  # type: ignore[name-defined]
        print("[NativeHotkey] 全局热键监听已启动 (Quartz Event Tap)")

        while self.monitoring:
            CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0.2, True)  # type: ignore[name-defined]

        try:
            if self.tap:
                CGEventTapEnable(self.tap, False)  # type: ignore[name-defined]
                CFMachPortInvalidate(self.tap)  # type: ignore[name-defined]
                self.tap = None
        except Exception:
            pass


class AutoClickerNative(QMainWindow):
    hotkey_start_signal = pyqtSignal()
    hotkey_stop_signal = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.click_worker = None
        self.hotkey_manager = None
        self.config_file = 'config_native.json'
        # 默认热键配置（界面与原生监听共用）
        self.hotkey_defaults = {
            'start_mods': ['Ctrl', 'Option'],
            'start_key': 'S',
            'stop_mods': ['Ctrl', 'Option'],
            'stop_key': 'D'
        }
        self.hotkey_config = dict(self.hotkey_defaults)
        # 连接跨线程信号
        self.hotkey_start_signal.connect(self.start_clicking)
        self.hotkey_stop_signal.connect(self.stop_clicking)
        self.init_ui()
        self.load_config()
        self.setup_hotkeys()
        # 初始化热键设置控件显示
        self._refresh_hotkey_ui()
        
    def init_ui(self):
        self.setWindowTitle('鼠标连点器 - 原生热键版')
        self.setGeometry(100, 100, 400, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel('鼠标连点器')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
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
        self.frequency_spin.setValue(10)
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
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # 控制按钮组
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout()
        
        # 开始/停止按钮
        button_layout = QHBoxLayout()
        self.start_button = QPushButton('开始连点')
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
        
        # 使用说明
        help_group = QGroupBox("使用说明")
        help_layout = QVBoxLayout()
        
        help_text = QTextEdit()
        help_text.setMaximumHeight(100)
        help_text.setPlainText(
            "1. 设置点击参数\n"
            "2. 将鼠标移动到目标位置\n"
            "3. 使用按钮或按 Ctrl+Option+S 开始连点\n"
            "4. 按 Ctrl+Option+D 或点击停止按钮结束"
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
            # 应用当前（或加载后的）热键配置到原生监听器
            self.hotkey_manager.update_hotkey_config(self.hotkey_config)
            if self.hotkey_manager.start_monitoring():
                self.hotkey_status.setText('✅ 原生热键监听中 (全局)')
                native_ok = True
            else:
                self.hotkey_status.setText('❌ 原生热键启动失败，已启用窗口内热键')
                self.hotkey_status.setStyleSheet("color: orange; font-weight: bold;")
        
        # 始终启用窗口内热键作为兜底：窗口聚焦时F6/F7可用
        self.shortcut_start = QShortcut(QKeySequence('F6'), self)
        self.shortcut_start.setContext(Qt.ShortcutContext.WindowShortcut)
        self.shortcut_start.activated.connect(self.start_clicking)
        
        self.shortcut_stop = QShortcut(QKeySequence('F7'), self)
        self.shortcut_stop.setContext(Qt.ShortcutContext.WindowShortcut)
        self.shortcut_stop.activated.connect(self.stop_clicking)
        
        if not native_ok:
            # 显示兜底提示
            self.hotkey_status.setText('ℹ️ 已启用窗口内热键：F6开始，F7停止（需窗口在前台）')
            self.hotkey_status.setStyleSheet("color: #666; font-weight: bold;")

    def start_clicking(self):
        """开始连点"""
        if self.click_worker and self.click_worker.isRunning():
            return
            
        click_type = self.click_type_combo.currentText()
        frequency = self.frequency_spin.value()
        max_clicks = self.max_clicks_spin.value()
        button_type = self.button_combo.currentText()
        
        self.click_worker = ClickWorker(click_type, frequency, max_clicks, button_type)
        self.click_worker.finished.connect(self.on_clicking_finished)
        self.click_worker.start()
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText(f'连点中... ({frequency}次/秒)')
        self.status_label.setStyleSheet("padding: 10px; background-color: #fff3cd; border-radius: 5px;")
        
        self.save_config()
        
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
        
        # 3秒后恢复准备状态
        def reset_status():
            self.status_label.setText('准备就绪')
            self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e8; border-radius: 5px;")
        QTimer.singleShot(3000, reset_status)
        
    def save_config(self):
        """保存配置"""
        config = {
            'click_type': self.click_type_combo.currentText(),
            'frequency': self.frequency_spin.value(),
            'max_clicks': self.max_clicks_spin.value(),
            'button_type': self.button_combo.currentText(),
            # 持久化热键配置
            'hotkey_config': self.hotkey_config
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
            
    def load_config(self):
        """加载配置"""
        if not os.path.exists(self.config_file):
            return
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.click_type_combo.setCurrentText(config.get('click_type', '单击'))
            self.frequency_spin.setValue(config.get('frequency', 10))
            self.max_clicks_spin.setValue(config.get('max_clicks', 0))
            self.button_combo.setCurrentText(config.get('button_type', '左键'))
            # 读取热键配置
            hk = config.get('hotkey_config')
            if isinstance(hk, dict):
                # 合并到默认值，避免缺项
                merged = dict(self.hotkey_defaults)
                merged.update(hk)
                self.hotkey_config = merged
        
        except Exception as e:
            print(f"加载配置失败: {e}")
            
    def apply_hotkey_settings(self):
        """从UI读取并应用新的热键设置，同时保存到配置"""
        def collect_mods(chk_ctrl, chk_opt, chk_shift, chk_cmd):
            mods = []
            if chk_ctrl.isChecked():
                mods.append('Ctrl')
            if chk_opt.isChecked():
                mods.append('Option')
            if chk_shift.isChecked():
                mods.append('Shift')
            if chk_cmd.isChecked():
                mods.append('Command')
            return mods
        self.hotkey_config['start_mods'] = collect_mods(self.chk_start_ctrl, self.chk_start_opt, self.chk_start_shift, self.chk_start_cmd)
        self.hotkey_config['stop_mods'] = collect_mods(self.chk_stop_ctrl, self.chk_stop_opt, self.chk_stop_shift, self.chk_stop_cmd)
        self.hotkey_config['start_key'] = self.cmb_start_key.currentText()
        self.hotkey_config['stop_key'] = self.cmb_stop_key.currentText()
        # 持久化到文件
        self.save_config()
        # 应用到原生监听（无需重启）
        if self.hotkey_manager and self.hotkey_manager.monitoring:
            self.hotkey_manager.update_hotkey_config(self.hotkey_config)
        # 更新状态提示
        self.status_label.setText('已应用新的热键设置')
        self.status_label.setStyleSheet("padding: 10px; background-color: #fff3cd; border-radius: 5px;")

    def _refresh_hotkey_ui(self):
        cfg = self.hotkey_config
        # start
        self.chk_start_ctrl.setChecked('Ctrl' in cfg.get('start_mods', []))
        self.chk_start_opt.setChecked('Option' in cfg.get('start_mods', []))
        self.chk_start_shift.setChecked('Shift' in cfg.get('start_mods', []))
        self.chk_start_cmd.setChecked('Command' in cfg.get('start_mods', []))
        idx = self.cmb_start_key.findText(cfg.get('start_key','S'))
        if idx >= 0:
            self.cmb_start_key.setCurrentIndex(idx)
        # stop
        self.chk_stop_ctrl.setChecked('Ctrl' in cfg.get('stop_mods', []))
        self.chk_stop_opt.setChecked('Option' in cfg.get('stop_mods', []))
        self.chk_stop_shift.setChecked('Shift' in cfg.get('stop_mods', []))
        self.chk_stop_cmd.setChecked('Command' in cfg.get('stop_mods', []))
        idx2 = self.cmb_stop_key.findText(cfg.get('stop_key','D'))
        if idx2 >= 0:
            self.cmb_stop_key.setCurrentIndex(idx2)
        
    def closeEvent(self, a0):
        """窗口关闭事件"""
        if self.click_worker:
            self.click_worker.stop()
        if self.hotkey_manager:
            self.hotkey_manager.stop_monitoring()
        if a0:
            a0.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 检查权限提示
    if not NATIVE_HOTKEY_AVAILABLE:
        print("注意: 原生热键库不可用，将使用界面按钮控制")
    
    window = AutoClickerNative()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()