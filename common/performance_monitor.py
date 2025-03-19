# -*- coding: utf-8 -*-
"""
@File    : performance_monitor.py
@Time    : 2025/01/22
@Author  : Bruce.Si
@Description : 性能监听工具
    - 监听CPU使用率
    - 监听内存使用率
    - 监听GPU使用率
@Version : 1.0
"""
import pynvml
import psutil
import time
from common.logger import create_logger, Logger
from common.HWinfolog_monitor import HWINFOLOGMonitor
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List
import pandas as pd
import threading


class PerformanceMonitor:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.is_monitoring = False
        self.last_state = 0
        self.monitor_thread = None
        # 添加数据存储
        self.performance_data = {
            'timestamp': [],
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'network_sent': [],
            'network_recv': [],
            'gpu_usage': []
        }
        self.start_time = None
        self.end_time = None

    @staticmethod
    def get_cpu_usage(gpu_info):
        if gpu_info:
            for gpu_name, info in gpu_info.items():
                return float(info['cpu_usage'])

    @staticmethod
    def get_memory_usage(gpu_info):
        return psutil.virtual_memory().percent

    @staticmethod
    def get_gpu_usage(gpu_info):
        # 英伟达显卡支持
        # pynvml.nvmlInit()
        # handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        # utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        # gpu_util = utilization.gpu
        # pynvml.nvmlShutdown()
        if gpu_info:
            for gpu_name, info in gpu_info.items():
                return float(info['gpu_usage'])

    def start_monitoring(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.logger.info("性能监听工具启动")

    def stop_monitoring(self):
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("性能监听工具停止")
        
    def _clear_data(self):
        """清空历史数据"""
        for key in self.performance_data:
            self.performance_data[key] = []

    # ... 保留原有的get_xxx_usage方法 ...

    def monitor(self):
        """监控并收集性能数据"""
        while self.is_monitoring:
            current_time = time.time()

            hw_monitor = HWINFOLOGMonitor()
            hw_info = hw_monitor.read_gpu_info()

            # 收集性能数据
            cpu_usage = self.get_cpu_usage(hw_info)
            memory_usage = self.get_memory_usage(hw_info)
            gpu_usage = self.get_gpu_usage(hw_info)

            # 存储数据
            self.performance_data['timestamp'].append(current_time)
            self.performance_data['cpu_usage'].append(cpu_usage)
            self.performance_data['memory_usage'].append(memory_usage)
            self.performance_data['gpu_usage'].append(gpu_usage)

            # 日志输出
            # self.logger.info(f"CPU使用率: {cpu_usage}%")
            # self.logger.info(f"内存使用率: {memory_usage}%")
            # self.logger.info(f"GPU使用率: {gpu_usage}%")
            time.sleep(1)

    def get_performance_summary(self) -> Dict:
        """获取性能统计摘要"""
        if not self.performance_data['timestamp']:
            return {}

        summary = {}
        for metric in ['cpu_usage', 'memory_usage', 'gpu_usage']:
            data = self.performance_data[metric]
            summary[metric] = {
                'min': min(data),
                'max': max(data),
                'avg': round(sum(data) / len(data), 4),
            }
        return summary

    def plot_performance_curves(self, save_path: str = None):
        """绘制性能曲线图"""
        # 加载中文字体，需要确保字体文件路径正确
        plt.rcParams['font.sans-serif'] = ['SimHei']  # SimHei是一种常见的支持中文的字体，也可以替换为其他支持中文的字体名
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题


        if not self.performance_data['timestamp']:
            self.logger.warning("没有可用的性能数据来绘制图表")
            return

        # 转换时间戳为相对时间（秒）
        relative_time = np.array(self.performance_data['timestamp']) - self.performance_data['timestamp'][0]

        # 创建子图
        fig, axs = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle('性能监控报告', fontsize=16)

        # CPU使用率
        axs[0, 0].plot(relative_time, self.performance_data['cpu_usage'])
        axs[0, 0].set_title('CPU使用率')
        axs[0, 0].set_ylabel('%')

        # 内存使用率
        axs[0, 1].plot(relative_time, self.performance_data['memory_usage'])
        axs[0, 1].set_title('内存使用率')
        axs[0, 1].set_ylabel('%')

        # GPU使用率
        axs[1, 1].plot(relative_time, self.performance_data['gpu_usage'])
        axs[1, 1].set_title('GPU使用率')
        axs[1, 1].set_ylabel('%')

        # 调整布局
        plt.tight_layout()

        # 保存或显示图表
        if save_path:
            plt.savefig(save_path)
            self.logger.info(f"性能曲线图已保存至: {save_path}")
        else:
            plt.show()

        plt.close()


if __name__ == '__main__':

    # 创建监控实例
    logger = create_logger("performance_monitor")
    monitor = PerformanceMonitor(logger)

    # 开始监控

    monitor.start_monitoring()
    time.sleep(3)
    monitor.stop_monitoring()

    # 获取性能摘要
    summary = monitor.get_performance_summary()
    print(summary)

    # 绘制性能曲线图
    # monitor.plot_performance_curves(save_path="performance_report.png")