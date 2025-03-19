# -*- coding: utf-8 -*-
"""
@File    : taskmgr_monitor.py
@Time    : 2025/02/20
@Author  : Bruce.Si
@Desc    : 任务管理器DLL调用
"""

import ctypes
import os
import platform
from ctypes import Structure, c_double, c_char, c_bool

# 定义 PerfData 结构体
class PerfData(Structure):
    _fields_ = [
        ("power_state", ctypes.c_char * 50),  # 固定长度字符串
        ("foregroud_process", ctypes.c_char * 256),  # 固定长度字符串
        ("cpu_usage", c_double),
        ("cpu_perf", c_double),
        ("disk_io", c_double),
        ("mem_usage", c_double),
        ("gpu_0_usage", c_double),
        ("gpu_1_usage", c_double),
        ("gpu_0_3d", c_double),
        ("gpu_1_3d", c_double),
        ("gpu_0_copy", c_double),
        ("gpu_1_copy", c_double),
        ("gpu_0_gdi_render", c_double),
        ("gpu_1_gdi_render", c_double),
        ("gpu_0_legacy_overlay", c_double),
        ("gpu_1_legacy_overlay", c_double),
        ("gpu_0_video_decoding", c_double),
        ("gpu_1_video_decoding", c_double),
        ("gpu_0_video_encoding", c_double),
        ("gpu_1_video_encoding", c_double),
        ("gpu_0_video_processing", c_double),
        ("gpu_1_video_processing", c_double),
        ("gpu_0_security", c_double),
        ("gpu_1_security", c_double),
        ("gpu_0_compute", c_double),
        ("gpu_1_compute", c_double),
        ("gpu_0_other", c_double),
        ("gpu_1_other", c_double),
        ("gpu_dedicated_usage", c_double),
    ]


# 解码字符串字段
def decode_string_field(field):
    return field.decode("utf-8").strip("\x00")


# 根据平台加载DLL
def load_perfmon_dll():
    current_path = os.path.dirname(os.getcwd())
    print("当前文件夹路径：", current_path)
    arch = platform.architecture()[0]  # 获取当前Python解释器的架构
    if arch == "32bit":
        dll_path = "\DLLs\PerfMon.dll"  # 32位DLL路径
    else:
        dll_path = "\DLLs\PerfMon.dll"  # 64位DLL路径

    try:
        perfmon_dll = ctypes.CDLL(current_path+dll_path)  # 加载DLL
        return perfmon_dll
    except OSError as e:
        print(f"加载DLL失败: {e}")
        return None


# 定义 GetPerfData 函数
def setup_get_perf_data(perfmon_dll):
    GetPerfData = perfmon_dll.GetPerfData
    GetPerfData.argtypes = [ctypes.c_int, ctypes.POINTER(PerfData)]  # 参数类型
    GetPerfData.restype = c_bool  # 返回值类型
    return GetPerfData


# 更新性能数据
def update(calc_sleep):
    perfmon_dll = load_perfmon_dll()
    if not perfmon_dll:
        return None

    GetPerfData = setup_get_perf_data(perfmon_dll)
    data = PerfData()  # 创建结构体实例
    success = GetPerfData(calc_sleep, ctypes.byref(data))  # 调用DLL函数

    if success:
        return data
    else:
        print("获取性能数据失败")
        return None


# 示例：获取并打印性能数据
if __name__ == "__main__":
    data = update(1)  # 获取性能数据
    if data:
        print(f"CPU使用率: {data.cpu_usage}%")
        print(f"内存使用率: {data.mem_usage}%")
        print(f"GPU 0的3D使用率: {data.gpu_1_3d}%")
        print(f"电源状态: {decode_string_field(data.power_state)}")
        print(f"前台进程: {decode_string_field(data.foregroud_process)}")