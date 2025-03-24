# -*- coding: utf-8 -*-
"""
@File    : HWinfolog_monitor.py
@Time    : 2025/02/11
@Author  : Bruce.Si
@Desc    : WH_INFO日志下获取功耗信息
"""

import time
from typing import Dict, Any
from config.config import HWINFO_LOG_PATH
from collections import deque
import csv


class HWINFOLOGMonitor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_path: str = HWINFO_LOG_PATH):
        self.log_path = log_path
        self.title = {"cpu_usage": 0, "gpu_usage": 0, "cpu_power": 0, "gpu_power": 0}


    def get_title_num(self, log_file=None):
        """获取title序号"""
        with open(log_file, 'r', encoding='GBK') as f:
            reader = csv.reader(f)
            rows = list(reader)
            first_row = rows[0]
            print(first_row)
            if 'CPU Package Power [W]' in first_row:
                self.title["cpu_power"] = first_row.index('CPU Package Power [W]')
            if 'GT Cores Power [W]' in first_row:
                self.title["gpu_power"] = first_row.index('GT Cores Power [W]')
            if 'GPU D3D Usage [%]' in first_row:
                self.title["gpu_usage"] = first_row.index('GPU D3D Usage [%]')
            if 'Total CPU Utility [%]' in first_row:
                self.title["cpu_usage"] = first_row.index('Total CPU Utility [%]')

    def read_gpu_info(self) -> Dict[str, Dict[str, float]]:
        """读取HWinfo信息"""
        try:
            # 获取title序号
            if self._instance:
                self.get_title_num(self.log_path)
            # 读取日志文件的最后几行
            with open(self.log_path, 'r', encoding='GBK') as file:
                # 创建一个最大长度为 2 的 deque
                last_two_lines = deque(file, maxlen=2)
                if len(last_two_lines) >= 2:
                    # 获取倒数第二行并去除行尾的换行符
                    second_last_line = last_two_lines[0].strip()
                else:
                    print("文件行数少于 2，没有倒数第二行。")
                return self.parse_log_line(second_last_line)

        except Exception as e:
            print(f"读取GPU信息失败: {str(e)}")

        return {}

    def parse_log_line(self, line: str) -> dict[str, dict[str, str]] | dict[Any, Any]:
        """解析日志行"""
        try:
            # 假设日志格式为: "时间戳,功耗"
            parts = line.split(',')
            if len(parts) >= 3:
                return {
                    'GPU 0': {
                        'time_date': parts[1],
                        'gpu_power': parts[self.title["gpu_power"]],
                        'gpu_usage': parts[self.title["gpu_usage"]],
                        'cpu_usage': parts[self.title["cpu_usage"]],
                        'cpu_power': parts[self.title["cpu_power"]],
                    }
                }
        except Exception as e:
            print(f"解析日志行失败: {line}")
            print(f"错误: {str(e)}")
        return {}


def main():
    try:
        monitor = HWINFOLOGMonitor()

        while True:
            gpu_info = monitor.read_gpu_info()
            if gpu_info:
                for gpu_name, info in gpu_info.items():
                    if 'gpu_power' in info:
                        print(monitor.title)
                        print(gpu_info)
            time.sleep(1)
    except Exception as e:
        print(f"程序错误: {str(e)}")


if __name__ == "__main__":
    main()