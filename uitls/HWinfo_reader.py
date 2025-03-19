# -*- coding: utf-8 -*-
"""
@File    : hwinfo_reader.py
@Author  : Bruce.Si
@Desc    : HWiNFO共享内存读取器的Python实现，基于C#代码转换
"""

import mmap
import ctypes
from ctypes import *
from enum import IntEnum
from typing import List, Dict

# 常量定义
HWINFO_SENSORS_MAP_FILE_NAME2 = "Global\\HWiNFO_SENS_SM2"
HWINFO_SENSORS_SM2_MUTEX = "Global\\HWiNFO_SM2_MUTEX"
HWINFO_SENSORS_STRING_LEN2 = 128
HWINFO_UNIT_STRING_LEN = 16
SHARED_MEMORY_SIZE = 1024 * 1024  # 1MB 缓冲区


class SensorReadingType(IntEnum):
    """传感器读数类型"""
    NONE = 0
    TEMP = 1  # 温度
    VOLT = 2  # 电压
    FAN = 3  # 风扇
    CURRENT = 4  # 电流
    POWER = 5  # 功率
    CLOCK = 6  # 时钟频率
    USAGE = 7  # 使用率
    OTHER = 8  # 其他


class HWiNFOSensorsMem2(Structure):
    """共享内存头部结构"""
    _pack_ = 1
    _fields_ = [
        ("dwSignature", c_uint32),  # 签名
        ("dwVersion", c_uint32),  # 版本
        ("dwRevision", c_uint32),  # 修订版本
        ("poll_time", c_int64),  # 轮询时间
        ("dwOffsetOfSensorSection", c_uint32),  # 传感器区段偏移
        ("dwSizeOfSensorElement", c_uint32),  # 传感器元素大小
        ("dwNumSensorElements", c_uint32),  # 传感器元素数量
        ("dwOffsetOfReadingSection", c_uint32),  # 读数区段偏移
        ("dwSizeOfReadingElement", c_uint32),  # 读数元素大小
        ("dwNumReadingElements", c_uint32)  # 读数元素数量
    ]


class HWiNFOSensorElement(Structure):
    """传感器元素结构"""
    _pack_ = 1
    _fields_ = [
        ("dwSensorID", c_uint32),  # 传感器ID
        ("dwSensorInst", c_uint32),  # 传感器实例ID
        ("szSensorNameOrig", c_char * HWINFO_SENSORS_STRING_LEN2),  # 原始传感器名称
        ("szSensorNameUser", c_char * HWINFO_SENSORS_STRING_LEN2)  # 用户自定义传感器名称
    ]


class HWiNFOReadingElement(Structure):
    """读数元素结构"""
    _pack_ = 1
    _fields_ = [
        ("tReading", c_uint32),  # 读数类型
        ("dwSensorIndex", c_uint32),  # 传感器索引
        ("dwReadingID", c_uint32),  # 读数ID
        ("szLabelOrig", c_char * HWINFO_SENSORS_STRING_LEN2),  # 原始标签
        ("szLabelUser", c_char * HWINFO_SENSORS_STRING_LEN2),  # 用户标签
        ("szUnit", c_char * HWINFO_UNIT_STRING_LEN),  # 单位
        ("Value", c_double),  # 当前值
        ("ValueMin", c_double),  # 最小值
        ("ValueMax", c_double),  # 最大值
        ("ValueAvg", c_double)  # 平均值
    ]


class HWiNFOReader:
    """HWiNFO共享内存读取器"""

    def __init__(self):
        self.mm = None
        self.header = None
        self.sensor_names = []

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        """打开并初始化共享内存连接"""
        try:
            # 连接到共享内存
            self.mm = mmap.mmap(-1, SHARED_MEMORY_SIZE, HWINFO_SENSORS_MAP_FILE_NAME2)

            # 读取头部信息
            header_data = self.mm.read(sizeof(HWiNFOSensorsMem2))
            self.header = HWiNFOSensorsMem2.from_buffer_copy(header_data)

            # 打印头部信息
            # print("\n=== 共享内存头部信息 ===")
            # print(f"签名: 0x{self.header.dwSignature:08X}")
            # print(f"版本: {self.header.dwVersion}")
            # print(f"修订版本: {self.header.dwRevision}")
            # print(f"传感器数量: {self.header.dwNumSensorElements}")
            # print(f"读数数量: {self.header.dwNumReadingElements}")

            # 读取所有传感器名称
            self._read_sensor_names()

        except Exception as e:
            raise ConnectionError(f"无法连接到HWiNFO共享内存: {str(e)}\n"
                                  "请确保：\n"
                                  "1. HWiNFO已经启动并运行\n"
                                  "2. 在HWiNFO设置中启用了共享内存支持\n"
                                  "3. 以管理员权限运行程序")

    def _read_sensor_names(self):
        """读取所有传感器名称"""
        self.sensor_names = []
        for i in range(self.header.dwNumSensorElements):
            offset = self.header.dwOffsetOfSensorSection + (i * self.header.dwSizeOfSensorElement)
            self.mm.seek(offset)
            sensor_data = self.mm.read(self.header.dwSizeOfSensorElement)
            sensor = HWiNFOSensorElement.from_buffer_copy(sensor_data)

            name = (sensor.szSensorNameUser.decode('utf-8', errors='ignore').strip('\x00') or
                    sensor.szSensorNameOrig.decode('utf-8', errors='ignore').strip('\x00'))
            self.sensor_names.append(name)

            # print(f"\n=== 传感器 {i + 1} ===")
            # print(f"ID: {sensor.dwSensorID}")
            # print(f"实例ID: {sensor.dwSensorInst}")
            # print(f"名称: {name}")

    def read_all(self) -> List[Dict]:
        """读取所有传感器读数"""
        if not self.mm or not self.header:
            raise ConnectionError("未连接到HWiNFO")

        readings = []
        for i in range(self.header.dwNumReadingElements):
            offset = self.header.dwOffsetOfReadingSection + (i * self.header.dwSizeOfReadingElement)
            self.mm.seek(offset)
            reading_data = self.mm.read(self.header.dwSizeOfReadingElement)
            reading = HWiNFOReadingElement.from_buffer_copy(reading_data)

            reading_info = {
                'type': SensorReadingType(reading.tReading).name,
                'sensor_name': self.sensor_names[reading.dwSensorIndex],
                'sensor_index': reading.dwSensorIndex,
                'reading_id': reading.dwReadingID,
                'label': reading.szLabelOrig.decode('utf-8', errors='ignore').strip('\x00'),
                'user_label': reading.szLabelUser.decode('utf-8', errors='ignore').strip('\x00'),
                'unit': reading.szUnit.decode('utf-8', errors='ignore').strip('\x00'),
                'value': reading.Value,
                'min': reading.ValueMin,
                'max': reading.ValueMax,
                'avg': reading.ValueAvg
            }
            readings.append(reading_info)

            # 打印读数信息
            # print(f"\n=== 读数 {i + 1} ===")
            # print(reading_info)

        return readings

    def close(self):
        """关闭共享内存连接"""
        if self.mm:
            self.mm.close()
            self.mm = None
            self.header = None


def main():
    """主函数"""
    try:
        with HWiNFOReader() as reader:
            readings = reader.read_all()

            # 示例：筛选并显示所有CPU温度读数
            cpu_temps = [r for r in readings
                         if r['type'] == 'TEMP' and 'CPU' in r['label']]

            if cpu_temps:
                print("\n=== HWINFO数据 ===")
                for temp in cpu_temps:
                    print(f"{temp['label']}: {temp['value']:.1f}{temp['unit']}")

    except Exception as e:
        print(f"错误: {str(e)}")


if __name__ == "__main__":
    main()