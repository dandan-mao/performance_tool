# -*- coding: utf-8 -*-
"""
@File    : lock_monitor.py
@Time    : 2025/01/22
@Author  : Bruce.Si
@Description : 锁屏监听工具
    - 监听锁屏状态
    - 记录锁屏状态变化时间
    - 记录锁屏状态持续时间
@Version : 1.0
"""

import ctypes
from ctypes import wintypes
import win32con
from datetime import datetime
import time
from typing import Optional
from common.logger import create_logger, Logger

class LockScreenMonitor:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.is_monitoring = False
        self.last_state = False
        
        # 定义Windows API常量
        self.DESKTOP_SWITCHDESKTOP = 0x0100
        self._initialize_win_api()


    def _initialize_win_api(self):
        """初始化Windows API"""
        # 定义OpenDesktop函数
        self.OpenDesktop = ctypes.windll.user32.OpenDesktopW
        self.OpenDesktop.argtypes = [wintypes.LPWSTR, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.OpenDesktop.restype = wintypes.HANDLE
        
        # 定义SwitchDesktop函数
        self.SwitchDesktop = ctypes.windll.user32.SwitchDesktop
        self.SwitchDesktop.argtypes = [wintypes.HANDLE]
        self.SwitchDesktop.restype = wintypes.BOOL
        
        # 定义CloseDesktop函数
        self.CloseDesktop = ctypes.windll.user32.CloseDesktop
        self.CloseDesktop.argtypes = [wintypes.HANDLE]
        self.CloseDesktop.restype = wintypes.BOOL

    def is_locked(self) -> bool:
        """
        检查系统是否处于锁屏状态
        通过尝试切换到默认桌面来判断是否锁屏
        """
        h_desktop = self.OpenDesktop("Default", 0, False, self.DESKTOP_SWITCHDESKTOP)
        if h_desktop:
            is_locked = not bool(self.SwitchDesktop(h_desktop))
            self.CloseDesktop(h_desktop)
            return is_locked
        return True

    def monitor_lock_state(self):
        """开始监控锁屏状态"""
        self.is_monitoring = True
        self.logger.info("开始监控锁屏状态...")
        last_change_time = datetime.now()
        
        try:
            while self.is_monitoring:
                current_state = self.is_locked()
                
                # 检测状态变化
                if current_state != self.last_state:
                    now = datetime.now()
                    duration = (now - last_change_time).total_seconds() * 1000  # 转换为毫秒
                    
                    self.logger.info(
                        f"\n锁屏状态变化 - "
                        f"时间: {now.strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
                        f"状态: {'已锁定' if current_state else '已解锁'}\n"
                        f"持续时间: {duration:.2f}ms"
                    )
                    
                    # 更新状态
                    self.last_state = current_state
                    last_change_time = now
                
                # 降低CPU使用率，但保持较快的响应速度
                time.sleep(0.001)  # 1ms延迟
                
        except KeyboardInterrupt:
            self.logger.info("监控被手动中断")
        except Exception as e:
            self.logger.error(f"监控过程出错: {e}")
        finally:
            self.stop_monitoring()

    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        self.logger.info("停止监控锁屏状态")

def main():
    # 创建日志记录器
    logger = create_logger(
        name="lock_monitor",
        level="INFO",
        time_rotating=True,
        when='midnight'
    )
    
    # 创建监控器实例
    monitor = LockScreenMonitor(logger=logger)
    
    try:
        # 开始监控
        monitor.monitor_lock_state()
    except KeyboardInterrupt:
        monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()