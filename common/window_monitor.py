# -*- coding: utf-8 -*-
"""
@File    : window_monitor.py
@Time    : 2025/01/06
@Author  : Bruce.Si
@Desc    : 窗口监听模块
"""

import win32gui
import win32con
import time
from datetime import datetime
from typing import Dict, Optional
from common.logger import create_logger, Logger


class WindowMonitor:
    def __init__(self, logger: Logger, target: Dict = None):
        self.window_history: list = []  # 窗口历史记录
        self.current_window: Optional[Dict] = None  # 当前活动窗口
        self.is_monitoring = False  # 是否正在监听
        self.monitor_thread = None  # 监听线程
        self.monitor_interval = 0.00001  # 监听间隔（秒）
        self.target = target  # 目标窗口
        self.target_num = 0  #目标窗口序号(实际是响应窗口序号，target_num+1)
        self.target_window_record = None  # 目标窗口记录
        self.last_window = None  # 上次记录窗口
        
        # 初始化日志器
        self.logger = logger

    def get_window_info(self, hwnd: int) -> Dict:
        """获取窗口详细信息"""

        try:
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            # 获取窗口状态
            placement = win32gui.GetWindowPlacement(hwnd)
            is_zoomed = placement[1] == win32con.SW_SHOWMAXIMIZED
            is_minimized = placement[1] == win32con.SW_SHOWMINIMIZED
            
            return {
                "timestamp": datetime.now(),
                "hwnd": hwnd,
                "title": win32gui.GetWindowText(hwnd),
                "class_name": win32gui.GetClassName(hwnd),
                "rect": rect,
                "size": (width, height),
                "position": (rect[0], rect[1]),
                "is_minimized": is_minimized,
                "is_maximized": is_zoomed
            }
        except Exception as e:
            self.logger.error(f"获取窗口信息失败: {e}")
            return {}

    def add_to_history(self, window_info: Dict):
        """添加窗口信息到历史记录"""
        timestamp = window_info["timestamp"]
        self.window_history.append(timestamp)

    def monitor_window_changes(self):
        """监听窗口变化"""
        current_hwnd = win32gui.GetForegroundWindow()
        if current_hwnd != 0:  # 非正常窗口处理
            window_info = self.get_window_info(current_hwnd)
            if current_hwnd != self.last_window:
                self.current_window = window_info
                self.add_to_history(window_info)
                self.log_window_info(window_info)
            else:
                if self.has_window_changed(self.current_window, window_info):
                    self.current_window = window_info
                    self.add_to_history(window_info)
                    self.log_window_info(window_info, changed_only=True)

            # 检查是否遇到目标窗口
            if not self.target_window_record and self.target:
                if not self.has_window_changed(self.current_window, self.target):
                    self.target_window_record = window_info
                    self.target_num = len(self.window_history)
        self.last_window = current_hwnd

    def has_window_changed(self, old_info: Dict, new_info: Dict) -> bool:
        """检查窗口信息是否发生变化"""
        keys_to_check = ['title', 'size', 'is_maximized']
        return any(old_info.get(key) != new_info.get(key) for key in keys_to_check)

    def log_window_info(self, info: Dict, changed_only: bool = False):
        """记录窗口信息到日志"""
        if not info:
            return
            
        event_type = "窗口状态变化" if changed_only else "新活动窗口"
        
        log_msg = (
            f"\n{event_type}:\n"
            f"时间: {info['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
            f"标题: 【-{info['title']}-】\n"
            f"句柄: {info['hwnd']}\n"
            f"类名: {info['class_name']}\n"
            f"位置: {info['position']}\n"
            f"大小: {info['size']}\n"
            f"最小化: {info['is_minimized']}\n"
            f"最大化: {info['is_maximized']}"
        )
        
        self.logger.info(log_msg)

    def start_monitoring(self):
        """开始监听"""
        try:
            print("窗口工具启动")
            self.is_monitoring = True
            while self.is_monitoring:
                try:
                    self.monitor_window_changes()
                    time.sleep(self.monitor_interval)
                except Exception as e:
                    print(f"读取数据时出错: {e}")
                    time.sleep(1)  # 出错时等待1秒再重试
        except KeyboardInterrupt:
            print("手动停止窗口监控进程")
        finally:
            self.stop_monitoring()


    def stop_monitoring(self):
        """停止监听"""
        self.is_monitoring = False
        self.logger.info("窗口监听已停止")

    def results_analysis(self, start, end):
        """结果分析"""
        # 计算最后一个窗口和响应窗口的时差
        last = self.window_history[end] - self.window_history[start]
        return last.total_seconds() * 1000


def main():
    logger = create_logger(
            name="window_monitor",
            level="INFO",
            time_rotating=True,
            when='midnight'
        )
    target = {
        "title": "auto_win [C:/Users/Bruce.Si/PycharmProjects/auto_win] – window_monitor.py",
        "size": (1842, 1109),
        "is_maximized": True
    }
    monitor = WindowMonitor(logger=logger, target=target)
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("手动停止")
    finally:
        a = monitor.results_analysis(1, -1)
        print(a)

if __name__ == "__main__":
    main()