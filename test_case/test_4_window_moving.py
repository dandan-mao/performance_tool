# -*- coding: utf-8 -*-
"""
@File    : test_4_window_moving.py
@Time    : 2025/01/10
@Author  : Bruce.Si
@Desc    : 窗口移动
"""

import multiprocessing
import keyboard
import time
from datetime import datetime

from common.PFS_monitor import RefreshRateMonitor
from common.window_monitor import WindowMonitor
from common.logger import create_logger
from common.mouse_monitor import MouseMonitor
from common.performance_monitor import PerformanceMonitor
from common.power_consumption import PowerMonitor

# 创建主程序日志器
logger = create_logger(
    name="test_window_moving",
    level="INFO",
    time_rotating=True,
    when='midnight'
)

target = {
    "title": "媒体播放器",
    "size": (1842, 1109),
    "is_maximized": True
}

def process_mouse_monitor():
    """鼠标监控进程"""
    monitor = MouseMonitor(logger=logger)
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        monitor.stop_monitoring()

def process_window_monitor():
    """窗口监控进程"""
    monitor = WindowMonitor(logger=logger, target=target)
    try:
        monitor.start_monitoring()
        while monitor.is_monitoring:
            time.sleep(0.00001)
    except KeyboardInterrupt:
        monitor.stop_monitoring()


def process_keyboard_monitor():
    """键盘监控进程"""
    # 等待检测 win+UP 组合键
    fps = RefreshRateMonitor(show_plot=True, logger=logger)
    keyboard.wait('alt+tab')
    key_press_time = datetime.now()
    logger.info(f"检测到alt+tab按键时间: {key_press_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    fps.start_monitoring()
    time.sleep(5)
    fps.stop_monitoring()
    fps.format_drop_results()

def process_performance_monitor():
    """性能监控进程"""
    monitor = PerformanceMonitor(logger=logger)
    keyboard.wait('alt+tab')
    monitor.start_monitoring()
    time.sleep(3)
    monitor.stop_monitoring()
    summary = monitor.get_performance_summary()
    print(summary)


def process_power_monitor():
    """功耗监控进程"""
    power_monitor = PowerMonitor(logger=logger)
    keyboard.wait('alt+tab')
    power_monitor.start_monitoring()
    time.sleep(3)
    power_monitor.stop_monitoring()
    summary = power_monitor.get_power_summary()
    print(summary)

def main():
    """主程序"""

    try:
        # 创建进程
        window_process = multiprocessing.Process(
            target=process_window_monitor,
            name="WindowMonitor"
        )

        keyboard_process = multiprocessing.Process(
            target=process_keyboard_monitor,
            name="KeyboardMonitor"
        )

        mouse_process = multiprocessing.Process(
            target=process_mouse_monitor(),
            name="MouseMonitor"
        )

        performance_process = multiprocessing.Process(
            target=process_performance_monitor,
            name="PerformanceMonitor"
        )

        power_process = multiprocessing.Process(
            target=process_power_monitor,
            name="PowerMonitor"
        )

        # 启动进程
        logger.info("正在启动窗口监控进程...")
        window_process.start()
        keyboard_process.start()
        mouse_process.start()
        performance_process.start()
        power_process.start()

        # 等待进程结束
        window_process.join()
        keyboard_process.join()
        mouse_process.join()
        performance_process.join()
        power_process.join()

        logger.info("窗口监控进程已结束")

    except Exception as e:
        logger.error(f"主程序异常: {e}")
    finally:
        # 确保进程正确退出
        if window_process.is_alive():
            window_process.terminate()
        if keyboard_process.is_alive():
            keyboard_process.terminate()
        if mouse_process.is_alive():
            mouse_process.terminate()
        if performance_process.is_alive():
            performance_process.terminate()
        if power_process.is_alive():
            power_process.terminate()

        logger.info("程序已退出")
        logger.info(f"\n{'-' * 100}")


if __name__ == "__main__":
    multiprocessing.freeze_support()  # Windows下打包支持
    main()