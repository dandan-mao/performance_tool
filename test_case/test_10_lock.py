"""
@File    : test_10_lock.py
@Time    : 2025/01/15
@Author  : Bruce.Si
@Desc    : 锁屏
"""

import multiprocessing
import keyboard
import time
from datetime import datetime

from common.keyboard_monitor import KeyboardMonitor
from common.window_monitor import WindowMonitor
from common.desktop_focus_monitor import DesktopFocusMonitor
from common.logger import create_logger
from common.PFS_monitor import RefreshRateMonitor
from pywinauto import Application
from common.lock_monitor import LockScreenMonitor
import pyautogui


# 创建主程序日志器
logger = create_logger(
    name="test_open_apps",
    level="INFO",
    time_rotating=True,
    when='midnight'
)
# 目标app
target = {
    "title": "攀研训练营-OS introduction and install.pptx - PowerPoint",
    "size": (2400, 1399),
    "is_maximized": False
}
pyautogui.FAILSAFE = True  # 启用自动防故障功能

def press_enter_auto():
    """
    使用 pyautogui 模拟 Enter 键
    """
    pyautogui.press('enter')

def press_enter_auto_with_duration(duration: float = 0.001):
    """
    使用 pyautogui 模拟按住 Enter 键指定时间
    :param duration: 按键持续时间（秒）
    """
    pyautogui.keyDown('enter')
    time.sleep(duration)
    pyautogui.keyUp('enter')

def process_lock_screen_monitor():
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

def process_keyboard_monitor():
    """键盘监控进程"""
    # 等待检测 win+right 组合键
    monitor = KeyboardMonitor(logger=logger, target='q')
    try:
        # 开始监控
        monitor.start_monitoring()
        logger.info("等待目标组合键 (win+right) 或按 Ctrl+C 退出...")
        # 等待监控停止
        while monitor.is_monitoring:
            process_lock_screen_monitor()
            time.sleep(0.00001)

        logger.info("监控已结束")
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        logger.info("程序被手动中断")

def process_refreshrate_monitor():
    """FPS监控进程"""
    fps = RefreshRateMonitor(show_plot=True, logger=logger)
    fps.start_monitoring()
    time.sleep(8)
    fps.stop_monitoring()
    fps.format_drop_results()

def main():
    """主程序"""

    try:
        # 创建进程
        lock_screen_process = multiprocessing.Process(
            target=process_lock_screen_monitor,
            name="WindowMonitor"
        )

        keyboard_monitor = multiprocessing.Process(
            target=process_keyboard_monitor,
            name="KeyboardMonitor"
        )

        refreshrate_monitor = multiprocessing.Process(
            target=process_refreshrate_monitor,
            name="KeyboardMonitor"
        )
        # 启动进程
        logger.info("正在启动监控进程...")
        lock_screen_process.start()
        keyboard_monitor.start()
        refreshrate_monitor.start()

        # 等待进程结束
        lock_screen_process.join()
        keyboard_monitor.join()
        refreshrate_monitor.join()
        logger.info("监控进程已结束")

    except Exception as e:
        logger.error(f"主程序异常: {e}")
    finally:
        # 确保进程正确退出
        if lock_screen_process.is_alive():

            lock_screen_process.terminate()
        if keyboard_monitor.is_alive():
            keyboard_monitor.terminate()
        if refreshrate_monitor.is_alive():
            refreshrate_monitor.terminate()
        logger.info("程序已退出")
        logger.info(f"\n{'-' * 100}")


if __name__ == "__main__":
    multiprocessing.freeze_support()  # Windows下打包支持
    main()