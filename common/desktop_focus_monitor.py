# -*- coding: utf-8 -*-
"""
@File    : desktop_focus_monitor.py
@Time    : 2025/01/06
@Author  : Bruce.Si
@Desc    : 桌面焦点监听类
"""

import win32gui
import win32con
import win32process
import win32api
import threading
import time
from datetime import datetime
from typing import Optional
from common.logger import create_logger, Logger

class DesktopFocusMonitor:
    def __init__(self, logger: Logger):
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_interval = 0.00001  # 1毫秒的监听间隔
        self.last_focus_time: Optional[datetime] = None
        
        # 初始化日志器
        self.logger = logger

    def is_desktop_window(self, hwnd: int) -> bool:
        """
        判断窗口是否为桌面窗口
        """
        try:
            # 基本检查 判断句柄id           
            if not hwnd == 134638:
                return False
            return True
        except Exception as e:
            if not hwnd == 0:
                self.logger.error(f"桌面窗口检查失败: {e}")
            return False

    def check_desktop_focus(self) -> bool:
        """
        检查当前焦点是否在桌面
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            return self.is_desktop_window(hwnd)
        except Exception as e:
            self.logger.error(f"焦点检查失败: {e}")
            return False

    def monitor_desktop_focus(self):
        """
        监控桌面焦点状态
        """
        was_desktop_focused = False
        
        while self.is_monitoring:
            try:
                is_desktop_focused = self.check_desktop_focus()
                self.last_focus_time = datetime.now()
                # 状态变化：非桌面 -> 桌面
                if is_desktop_focused and not was_desktop_focused:
                    self.logger.info((
                        f"\n标题: 桌面焦点\n"
                        f"时间: {self.last_focus_time.strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
                        f"句柄: {win32gui.GetForegroundWindow()}"
                    ))
                    self.is_monitoring = False
                    break
                
                # 状态变化：桌面 -> 非桌面
                elif not is_desktop_focused and was_desktop_focused:
                    if self.last_focus_time:
                        self.logger.info((
                            f"\n标题: 非桌面焦点\n"
                            f"时间: {self.last_focus_time.strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
                            f"句柄: {win32gui.GetForegroundWindow()}"
                        ))
                
                was_desktop_focused = is_desktop_focused
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"监控过程出错: {e}")
                time.sleep(1)  # 错误发生时稍微暂停

    def start_monitoring(self):
        """
        启动监控
        """
        if not self.is_monitoring:
            try:
                self.is_monitoring = True
                self.monitor_thread = threading.Thread(target=self.monitor_desktop_focus)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()
                self.logger.info("桌面焦点监控已启动")
            except Exception as e:
                print(f"监听器启动失败: {e}")


    def stop_monitoring(self):
        """
        停止监控
        """
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("桌面焦点监控已停止")

def main():
    """
    独立运行时的入口函数
    """
    logger = create_logger(
        name="desktop_focus",
        level="INFO",
        time_rotating=True,
        when='midnight'
    )
    monitor = DesktopFocusMonitor(logger=logger)
    try:
        monitor.start_monitoring()
        while monitor.is_monitoring:
            time.sleep(0.00001)
    except KeyboardInterrupt:
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()