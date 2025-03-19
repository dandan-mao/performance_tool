# -*- coding: utf-8 -*-
"""
@File    : test_1_restore_desktop.py
@Time    : 2025/01/08
@Author  : Bruce.Si
@Desc    : 一键恢复桌面
"""

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


def main():
    """主程序"""

    # 创建一个 Event 对象，用于通知子进程停止
    stop_event = multiprocessing.Event()

    # 创建队列，计算响应时延和完成时延
    queue = multiprocessing.Queue()

    # 创建进程
    processes = [
        multiprocessing.Process(target=process_window_monitor,name="WindowMonitor",args=(stop_event,queue)),
        multiprocessing.Process(target=fps_monitor,name="FPSMonitor",args=(stop_event,)),
        multiprocessing.Process(target=process_performance_monitor,name="PerformanceMonitor",args=(stop_event,))
    ]

    # 启动进程
    print("正在启动所有监控进程...")
    for process in processes:
        process.daemon = True
        process.start()

    print("所有监听器已启动...")
    time.sleep(1)
    print("请输入WIN+D...")

    # 等待检测 Win+D 组合键
    keyboard.wait('windows+d')
    # 开始时间：键入win+D时间
    start_time = datetime.now()
    print(f"检测到Win+D按键时间: {start_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print("-------------------------")
    time.sleep(1)
    # 设置 Event 对象，通知子进程停止
    stop_event.set()
    # 获取队列中的响应时间和结束时间--队列遵循先进先出
    response_time = queue.get()
    end_time = queue.get()
    response_delay = (response_time - start_time).total_seconds() * 1000
    complete_delay = (end_time - start_time).total_seconds() * 1000

    print(
        "=============时延统计=============\n"
        f"响应时延：{response_delay:3f}\n"
        f"完成时延：{complete_delay:3f}"
    )
    for process in processes:
        process.join()
    print("==============结束==============")



if __name__ == "__main__":
    multiprocessing.freeze_support()  # Windows下打包支持
    main()

