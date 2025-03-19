# -*- coding: utf-8 -*-
"""
@File    : test_6_window_split_screen.py
@Time    : 2025/01/10
@Author  : Bruce.Si
@Desc    : 窗口分屏
"""

import multiprocessing
import keyboard
import time
from datetime import datetime

from common.PFS_monitor import RefreshRateMonitor
from common.keyboard_monitor import KeyboardMonitor
from common.window_monitor import WindowMonitor
from common.logger import create_logger
from common.performance_monitor import PerformanceMonitor
from common.power_consumption import PowerMonitor

# 创建主程序日志器
logger = create_logger(
    name="test_window_split_screen",
    level="INFO",
    time_rotating=True,
    when='midnight'
)

target = {
    "title": "媒体播放器",
    "size": (926, 1101),
    "is_maximized": False
}


def process_window_monitor():
    """窗口监控进程"""
    monitor = WindowMonitor(logger=logger)

    try:
        monitor.start_monitoring()
        while monitor.is_monitoring:
            time.sleep(0.00001)
    except KeyboardInterrupt:
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
            time.sleep(0.00001)
        logger.info("监控已结束")
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        logger.info("程序被手动中断")


def process_refreshrate_monitor():
    """FPS监控进程"""
    fps = RefreshRateMonitor(show_plot=True, logger=logger)
    fps.start_monitoring()
    time.sleep(3)
    fps.stop_monitoring()
    fps.format_drop_results()

def process_performance_monitor():
    """性能监控进程"""
    monitor = PerformanceMonitor(logger=logger)
    keyboard.wait('win+right')
    monitor.start_monitoring()
    time.sleep(3)
    monitor.stop_monitoring()
    summary = monitor.get_performance_summary()
    print(summary)


def process_power_monitor():
    """功耗监控进程"""
    power_monitor = PowerMonitor(logger=logger)
    keyboard.wait('win+right')
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

        keyboard_monitor = multiprocessing.Process(
            target=process_keyboard_monitor,
            name="KeyboardMonitor"
        )

        refreshrate_monitor = multiprocessing.Process(
            target=process_refreshrate_monitor,
            name="KeyboardMonitor"
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
        logger.info("正在启动监控进程...")
        window_process.start()
        keyboard_monitor.start()
        refreshrate_monitor.start()
        performance_process.start()
        power_process.start()

        # 等待进程结束
        window_process.join()
        keyboard_monitor.join()
        refreshrate_monitor.join()
        performance_process.join()
        power_process.join()

        logger.info("监控进程已结束")

    except Exception as e:
        logger.error(f"主程序异常: {e}")
    finally:
        # 确保进程正确退出
        if window_process.is_alive():
            window_process.terminate()
        if keyboard_monitor.is_alive():
            keyboard_monitor.terminate()
        if refreshrate_monitor.is_alive():
            refreshrate_monitor.terminate()
        if performance_process.is_alive():
            performance_process.terminate()
        if power_process.is_alive():
            power_process.terminate()
        logger.info("程序已退出")
        logger.info(f"\n{'-' * 100}")


if __name__ == "__main__":
    multiprocessing.freeze_support()  # Windows下打包支持
    main()