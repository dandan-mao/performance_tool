# -*- coding: utf-8 -*-
"""
@File    : HWINFO_monitor.py
@Time    : 2025/03/06
@Author  : Bruce.Si
@Desc    : WH_INFO共享内存下获取功耗信息
"""

import time
from typing import List, Dict, Callable
from dataclasses import dataclass

from matplotlib import rcParams

from uitls.HWinfo_reader import HWiNFOReader, SensorReadingType, HWiNFOReadingElement

# 常量定义
HWINFO_SENSORS_MAP_FILE_NAME2 = "Global\\HWiNFO_SENS_SM2"
HWINFO_SENSORS_SM2_MUTEX = "Global\\HWiNFO_SM2_MUTEX"
HWINFO_SENSORS_STRING_LEN2 = 128
HWINFO_UNIT_STRING_LEN = 16
SHARED_MEMORY_SIZE = 1024 * 1024  # 1MB 缓冲区

@dataclass
class SensorReading:
    """传感器读数数据类"""
    label: str
    value: float
    unit: str
    type: str
    min_value: float
    max_value: float
    avg_value: float
    timestamp: float

class HWiNFOMonitor:
    """HWiNFO传感器监听器"""
    def __init__(self, target_labels: List[str], interval: float = 1.0):
        """
        初始化监听器

        Args:
            target_labels: 要监听的标签列表
            interval: 监听间隔（秒），默认1秒
        """
        self.target_labels = [label.lower() for label in target_labels]  # 转换为小写
        self.interval = interval
        self.reader = HWiNFOReader()
        self._label_indices = {}  # 标签到索引的映射
        # self._callbacks = []  # 回调函数列表
        self.data_record = {}  # 标签数据记录
        self._running = False

    def init_label_indices(self):
        """初始化标签索引映射"""
        # 读取一次数据来构建索引映射
        readings = self.reader.read_all()
        for i, reading in enumerate(readings):
            label = reading['label'].lower()
            user_label = reading['user_label'].lower()

            if label in self.target_labels:
                self._label_indices[label] = i
                self.data_record[label] = []
            if user_label and user_label in self.target_labels:
                self._label_indices[user_label] = i
                self.data_record[user_label] = []

    # def add_callback(self, callback: Callable[[Dict[str, SensorReading]], None]):
    #     """
    #     添加数据回调函数
    #     Args:
    #         callback: 回调函数，接收一个字典参数，键为标签，值为传感器读数
    #     """
    #     self._callbacks.append(callback)

    def read_target_sensors_to_result(self):
        """返回标传感器的数据"""
        performance_data = {}
        for label, idx in self._label_indices.items():
            offset = (self.reader.header.dwOffsetOfReadingSection +
                      idx * self.reader.header.dwSizeOfReadingElement)

            self.reader.mm.seek(offset)
            reading_data = self.reader.mm.read(self.reader.header.dwSizeOfReadingElement)
            reading = HWiNFOReadingElement.from_buffer_copy(reading_data)
            performance_data[label] = reading.Value

        return performance_data

    def read_target_sensors(self):
        """读取目标传感器的数据"""
        readings = {}
        current_time = time.time()

        # 只读取我们关心的索引位置的数据
        for label, idx in self._label_indices.items():
            offset = (self.reader.header.dwOffsetOfReadingSection +
                      idx * self.reader.header.dwSizeOfReadingElement)

            self.reader.mm.seek(offset)
            reading_data = self.reader.mm.read(self.reader.header.dwSizeOfReadingElement)
            reading = HWiNFOReadingElement.from_buffer_copy(reading_data)
            self.data_record[label].append(reading.Value)
        #     readings[label] = SensorReading(
        #         label=reading.szLabelOrig.decode('utf-8', errors='ignore').strip('\x00'),
        #         value=reading.Value,
        #         unit=reading.szUnit.decode('utf-8', errors='ignore').strip('\x00'),
        #         type=SensorReadingType(reading.tReading).name,
        #         min_value=reading.ValueMin,
        #         max_value=reading.ValueMax,
        #         avg_value=reading.ValueAvg,
        #         timestamp=current_time
        #     )
        #
        # return readings

    def start(self):
        """开始监听"""
        try:
            print("HWINFO性能监听工具启动")
            self.reader.open()
            self.init_label_indices()

            if not self._label_indices:
                raise ValueError("未找到指定的标签")

            self._running = True

            while self._running:
                try:
                    # readings = self._read_target_sensors()
                    self.read_target_sensors()
                    # # 调用所有回调函数
                    # for callback in self._callbacks:
                    #     callback(readings)

                    time.sleep(self.interval)

                except Exception as e:
                    print(f"读取数据时出错: {e}")
                    time.sleep(1)  # 出错时等待1秒再重试

        except Exception as e:
            print(f"监听器启动失败: {e}")
        finally:
            self.stop()

    def stop(self):
        """停止监听"""
        self._running = False
        if self.reader:
            self.reader.close()

    def results_analysis(self):
        """统计结果"""
        print("========HWINFO性能统计结果========")
        for k, v in self.data_record.items():
            unit = "W" if "power" in k else "%"  # 单位处理，先简单这么处理
            print(
                f"【{k}】: "
                f"最大值: {round(max(v), 2)} {unit}, "
                f"最小值: {round(min(v), 2)} {unit}, "
                f"平均值: {round(sum(v) / len(v), 2)} {unit}"
            )


# # 使用示例
# def example_callback(readings: Dict[str, SensorReading]):
#     """回调函数"""
#     print("\n当前读数:")
#     for label, reading in readings.items():
#         print(f"{reading.label}: {reading.value:.2f}{reading.unit}")


def main():
    # 指定要监听的标签
    target_labels = [
        'Total CPU Utility',
        'CPU Package Power',
        'GT Cores Power',
        'GPU D3D Usage',
        'Physical Memory Load'
    ]

    # 创建监听器实例
    monitor = HWiNFOMonitor(target_labels, interval=1.0)

    # # 添加回调函数
    # monitor.add_callback(example_callback)
    monitor.reader.open()
    monitor.init_label_indices()
    data = monitor.read_target_sensors_to_result()
    print(data)
    # try:
    #     # 开始监听
    #     monitor.start()
    # except KeyboardInterrupt:
    #     print("\n停止监听")
    #     monitor.results_analysis()


if __name__ == "__main__":
    main()
