# -*- coding: utf-8 -*-
"""
@File    : PFS_test.py
@Time    : 2025/01/06   
@Author  : Bruce.Si
@Desc    : 滚轮响应时间监控模块
"""

from pynput import mouse
import time
import numpy as np
from datetime import datetime
import win32gui
import win32api

class WheelMonitor:
    def __init__(self):
        self.is_running = True
        self.last_time = time.perf_counter()
        self.response_times = []
        self.listener = None

    def on_scroll(self, x, y, dx, dy):
        """
        滚轮事件回调函数
        dx, dy: 滚动方向和距离
        """
        current_time = time.perf_counter()
        
        # 计算响应时间（毫秒）
        if self.last_time:
            response_time = (current_time - self.last_time) * 1000
            self.response_times.append(response_time)
            self.print_event_info(response_time, dy)
        
        self.last_time = current_time

    def start_monitor(self):
        """开始监测"""
        print("滚轮响应监测已启动...")
        print("请滚动鼠标滚轮进行测试")
        print("按Ctrl+C退出程序")
        print("-" * 30)

        try:
            # 创建并启动监听器
            with mouse.Listener(on_scroll=self.on_scroll) as self.listener:
                self.listener.join()
        except KeyboardInterrupt:
            print("\n监测已停止")
        finally:
            self.print_statistics()

    def print_event_info(self, response_time, direction):
        """打印事件信息"""
        try:
            current_time = datetime.now()
            x, y = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint((x, y))
            window_text = win32gui.GetWindowText(hwnd)
            
            scroll_direction = "向上" if direction > 0 else "向下"
            print(f"时间: {current_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
            print(f"滚动方向: {scroll_direction}")
            print(f"位置: x={x}, y={y}")
            print(f"窗口: {window_text}")
            print(f"响应时间: {response_time:.2f}ms")
            print("-" * 30)
        except Exception as e:
            print(f"打印信息错误: {e}")

    def print_statistics(self):
        """打印统计信息"""
        if not self.response_times:
            print("\n没有检测到滚轮事件")
            return
            
        response_times = np.array(self.response_times)
        
        print("\n统计结果:")
        print(f"样本数量: {len(response_times)}")
        print(f"平均响应时间: {np.mean(response_times):.2f}ms")
        print(f"最小响应时间: {np.min(response_times):.2f}ms")
        print(f"最大响应时间: {np.max(response_times):.2f}ms")
        print(f"标准差: {np.std(response_times):.2f}ms")
        print(f"中位数: {np.median(response_times):.2f}ms")

def main():
    monitor = WheelMonitor()
    monitor.start_monitor()

if __name__ == '__main__':
    main()