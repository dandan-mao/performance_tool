# -*- coding: utf-8 -*-
"""
@File    : HWinfolog_monitor.py
@Time    : 2025/02/11
@Author  : Bruce.Si
@Desc    : WH_INFO日志下获取功耗信息
"""

import os
from typing import Dict, Optional, Any
from datetime import datetime
from config.config import HWINFO_LOG_PATH, LOG_NAME
from collections import deque


class HWINFOLOGMonitor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_path: str = HWINFO_LOG_PATH):
        self.log_path = log_path
        self.last_read_time = 0
        self.title = {"cpu_usage": 0, "gpu_usage": 0, "cpu_power": 0, "gpu_power": 0}

    def get_latest_log(self) -> Optional[str]:
        """获取最新的日志文件"""
        try:
            # 确保日志目录存在
            if not os.path.exists(self.log_path):
                print(f"日志目录不存在: {self.log_path}")
                return None

            # 获取最新的日志文件
            log_files = [f for f in os.listdir(self.log_path) if f.endswith(LOG_NAME)]
            if not log_files:
                print("未找到日志文件")
                return None

            latest_log = max(log_files, key=lambda x: os.path.getmtime(os.path.join(self.log_path, x)))
            return os.path.join(self.log_path, latest_log)


        except Exception as e:
            print(f"获取日志文件失败: {str(e)}")
            return None

    def get_title_num(self, log_file=None):
        """获取title序号"""
        with open(log_file, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            first_line = first_line.strip()
            line_list = first_line.split(",")
            if '"CPU 封装功率 [W]"' in line_list:
                self.title["cpu_power"] = line_list.index('"CPU 封装功率 [W]"')
            if '"GT 核心功率 [W]"' in line_list:
                self.title["gpu_power"] = line_list.index('"GT 核心功率 [W]"')
            if '"GPU D3D 使用率 [%]"' in line_list:
                self.title["gpu_usage"] = line_list.index('"GPU D3D 使用率 [%]"')
            if '"CPU 总使用率 [%]"' in line_list:
                self.title["cpu_usage"] = line_list.index('"CPU 总使用率 [%]"')

    def read_gpu_info(self) -> Dict[str, Dict[str, float]]:
        """读取HWinfo信息"""
        try:
            log_file = self.get_latest_log()
            if not log_file:
                return {}

            # 检查文件是否有更新
            current_mtime = os.path.getmtime(log_file)
            if current_mtime <= self.last_read_time:
                return {}

            self.last_read_time = current_mtime
            # 获取title序号
            if self._instance:
                self.get_title_num(log_file)
            # 读取日志文件的最后几行
            with open(log_file, 'r', encoding='utf-8') as file:
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
    except Exception as e:
        print(f"程序错误: {str(e)}")


if __name__ == "__main__":
    main()