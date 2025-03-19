# -*- coding: utf-8 -*-
"""
@File    : mouse_monitor.py
@Time    : 2025/01/03
@Author  : Bruce.Si
@Description : 鼠标监听工具
    - 监听鼠标左键按下和释放事件
    - 记录精确时间戳和位置信息
    - 记录点击窗口信息
    - 计算按压持续时间
@Version : 1.0
"""
import threading

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QObject
from datetime import datetime
import win32api
import win32gui
import win32con
import time
import sys
from common.logger import create_logger, Logger

class MouseMonitor:
    """
    鼠标监听工具
    """
    def __init__(self, logger: Logger):
        self.press_time = None
        self.release_time = None
        self.is_running = True
        self.last_pos = None  # 记录上一次的鼠标位置
        self.last_state = 0  # 记录上一次的鼠标状态
        self.is_monitoring = False  # 是否正在监听
        self.logger = logger
        self.logger.info("鼠标监听工具初始化完成")

    def monitor_mouse_changes(self):
        """监听鼠标变化"""
        # 获取上次鼠标状态
        self.last_state = win32api.GetKeyState(win32con.VK_LBUTTON)
        self.last_pos = win32api.GetCursorPos()
        while self.is_running:
            # 检查ESC键
            if win32api.GetAsyncKeyState(win32con.VK_ESCAPE):
                self.is_running = False
                break
                
            # 获取当前鼠标状态
            current_state = win32api.GetKeyState(win32con.VK_LBUTTON)
            current_pos = win32api.GetCursorPos()
            # 检测状态变化
            if current_state != self.last_state:
                # 负值表示按下，正值表示释放
                if current_state < 0:
                    self.on_mouse_press()
                else:
                    self.on_mouse_release()
            else:
                if current_pos != self.last_pos:
                    pos_info = (
                        f"\n鼠标移动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
                        f"鼠标移动位置: x={current_pos[0]}, y={current_pos[1]}"
                    )
                    self.logger.info(pos_info)
            self.last_pos = current_pos
            self.last_state = current_state
            time.sleep(0.00001)  # 降低CPU使用率，同时保持较高精度

    def on_mouse_press(self):
        self.press_time = datetime.now()
        x, y = win32api.GetCursorPos()
        press_info = (
            f"\n鼠标按下时间: {self.press_time.strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
            f"鼠标按下位置: x={x}, y={y}"
        )
        self.logger.info(press_info)
        
    def on_mouse_release(self):
        self.release_time = datetime.now()
        x, y = win32api.GetCursorPos()

        # 计算持续时间
        duration = (self.release_time - self.press_time).total_seconds()

        release_info = (
            f"\n鼠标释放位置: {self.release_time.strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
            f"鼠标释放位置: x={x}, y={y}\n"
            f"按住持续时间: {duration:.3f} 秒"
        )
        self.logger.info(release_info)

    def start_monitoring(self):
        """开始监听"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_mouse_changes)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.logger.info("鼠标监听工具已启动...")
            self.logger.info("按Ctrl+C退出程序")

    def stop_monitoring(self):
        """停止监听"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("鼠标监听已停止")


if __name__ == '__main__':
    logger = create_logger(
            name="mouse_monitor",
            level="INFO",
            time_rotating=True,
            when='midnight'
        )
    app = QApplication(sys.argv)
    window = QWidget()
    monitor = MouseMonitor(logger=logger)
    
    # 启动监听
    try:
        monitor.start_monitoring()
        while monitor.is_monitoring:
            time.sleep(0.00001)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
    sys.exit()