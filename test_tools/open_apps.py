# -*- coding: utf-8 -*-
"""
@File    : open_apps.py
@Time    : 2025/03/17
@Author  : Bruce.Si
@Desc    : 打开应用
"""

import psutil
import multiprocessing
import keyboard
import time
from datetime import datetime
from common.window_monitor import WindowMonitor
from common.logger import create_logger
from common.PFS_monitor import RefreshRateMonitor
from common.HWINFO_monitor import HWiNFOMonitor
from config.config import TARGET_LABELS


# 创建主程序日志器
logger = create_logger(
    name="test_restore_desktop",
    level="INFO",
    time_rotating=True,
    console_output=False,
    when='midnight'
)
# 目标
target = {
    "title": "",
    "size": (1829, 1143),
    "is_maximized": False
}


def process_window_monitor(stop_event, queue):
    """窗口监控进程"""
    monitor = WindowMonitor(logger=logger, target=None)
    while not stop_event.is_set():
        monitor.monitor_window_changes()
    # 添加响应时间和结束时间到管道
    response_time = monitor.window_history[1]
    end_time = monitor.window_history[-1]
    queue.put(response_time)
    queue.put(end_time)



def fps_monitor(stop_event):
    """FPS监控进程"""
    monitor = RefreshRateMonitor(show_plot=True, logger=logger)
    while not stop_event.is_set():
        monitor.record_frame()
    monitor.results_analysis()  # 结果分析



def process_performance_monitor(stop_event):
    """性能监控进程"""
    monitor = HWiNFOMonitor(TARGET_LABELS, interval=1.0)
    monitor.reader.open()  # 打开监听器
    monitor.init_label_indices()  # 初始化标签
    while not stop_event.is_set():
        # 开始监听
        monitor.read_target_sensors()
        time.sleep(monitor.interval)
    monitor.results_analysis()  # 结果分析
    monitor.stop()


def monitor_process(process_name):
    """
    监控指定名称的进程是否启动
    :param process_name: 要监控的进程名称
    """
    print(f"开始监控进程 {process_name}...")
    while True:
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == process_name:
                    print(f"进程 {process_name} 已启动，进程 ID 为 {proc.pid}。")
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        time.sleep(1)


if __name__ == "__main__":
    target_process = "Taskmgr.exe"
    monitor_process(target_process)
