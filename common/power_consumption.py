# -*- coding: utf-8 -*-
"""
@File    : power_consumption.py
@Time    : 2025/02/07
@Author  : Bruce.Si
@Desc    : 功耗监控
"""

import subprocess
import threading
from common.logger import create_logger, Logger
import wmi
import psutil
from typing import Dict, Optional
import time
import re
from common.HWinfolog_monitor import HWINFOLOGMonitor


class PowerMonitor:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.wmi = wmi.WMI()
        self.is_monitoring = False
        self.monitor_thread = None
        self.power_data = {
            'timestamp': [],
            'cpu_power': [],         # CPU功耗
            'gpu_power': [],         # GPU功耗
        }

    def get_cpu_power(self, gpu_info) -> Optional[float]:
        """获取CPU功耗（需要管理员权限）"""
        if gpu_info:
            for gpu_name, info in gpu_info.items():
                return float(info['cpu_power'])

    def get_gpu_power(self, gpu_info) -> Optional[float]:
        """获取GPU功耗"""
        # NVIDIA GPU
        # try:
        #     cmd = "nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits"
        #     result = subprocess.check_output(cmd, shell=True)
        #     return float(result.decode().strip())
        # except Exception as e:
        #     self.logger.info(f"获取GPU功耗失败: {e}")
        # return None
        if gpu_info:
            for gpu_name, info in gpu_info.items():
                return float(info['gpu_power'])

    def start_monitoring(self):
        """开始监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.logger.info("功耗监听工具启动")

    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("功耗监听工具停止")

    def monitor(self):
        """监控循环"""
        while self.is_monitoring:
            monitor = HWINFOLOGMonitor()
            hw_info = monitor.read_gpu_info()

            current_time = time.time()
            
            # 收集数据
            cpu_power = self.get_cpu_power(hw_info)
            gpu_power = self.get_gpu_power(hw_info)

            # 存储数据
            self.power_data['timestamp'].append(current_time)
                
            self.power_data['cpu_power'].append(cpu_power)
            self.power_data['gpu_power'].append(gpu_power)

            time.sleep(0.1)  # 每100毫秒采样一次

    def get_power_summary(self) -> Dict:
        """获取功耗统计摘要"""
        summary = {}
        
        for metric in ['cpu_power', 'gpu_power']:
            data = [x for x in self.power_data[metric] if x is not None]
            if data:
                summary[metric] = {
                    'min': min(data),
                    'max': max(data),
                    'avg': sum(data) / len(data)
                }
            else:
                summary[metric] = {
                    'min': None,
                    'max': None,
                    'avg': None
                }
                
        return summary


if __name__ == "__main__":
    # 创建监控实例
    logger = create_logger("power_monitor")
    power_monitor = PowerMonitor(logger)
    
    try:
        # 开始监控
        power_monitor.start_monitoring()

        # 运行一段时间
        time.sleep(5)
        
        # 停止监控
        power_monitor.stop_monitoring()
        
        # 获取统计信息
        summary = power_monitor.get_power_summary()
        print(summary)

            
    except KeyboardInterrupt:
        power_monitor.stop_monitoring()
