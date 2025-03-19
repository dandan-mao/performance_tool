# -*- coding: utf-8 -*-
"""
@File    : PFS_test.py
@Time    : 2025/01/03
@Author  : Bruce.Si
@Desc    : 显示器刷新率监控模块
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from ctypes import windll
from typing import Dict
from datetime import datetime
from common.logger import create_logger,Logger


class RefreshRateMonitor:
    def __init__(self, logger: Logger, show_plot=True):
        """
        初始化刷新率监控器
        :param show_plot: 是否显示图表
        """
        self.show_plot = show_plot
        self.timestamps = []
        self.intervals = []
        self.dwm = windll.dwmapi
        self.is_monitoring = False

        # 初始化日志器
        self.logger = logger

        # 设置matplotlib中文字体
        if show_plot:
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
    
    def record_frame(self):
        """记录一帧"""
        self.dwm.DwmFlush()  # 等待垂直同步
        self.timestamps.append(time.perf_counter_ns())

    def analyze_frame_drops(self, target_fps: float = None) -> Dict:
        """
        分析丢帧情况
        :param target_fps: 目标帧率，如果不指定则使用平均刷新率
        :return: 分析结果字典
        """
        if len(self.timestamps) < 2:
            return {
                'max_drops': 0,
                'max_drop_time': 0,
                'max_drop_index': 0,
                'total_drops': 0,
                'drop_points': []
            }
        
        # 如果没有指定目标帧率，使用平均刷新率
        if target_fps is None:
            intervals = np.diff(self.timestamps) / 1_000_000  # 转换为毫秒
            avg_interval = np.mean(intervals)
            target_fps = 1000 / avg_interval
        
        target_frame_time = 1000.0 / target_fps  # 目标帧时间(ms)
        
        # 计算帧间隔（毫秒）
        intervals = np.diff(self.timestamps) / 1_000_000
        
        # 计算每个间隔丢失的帧数
        dropped_frames = np.floor(intervals / target_frame_time) - 1
        dropped_frames = np.maximum(dropped_frames, 0)  # 小于0的设为0
        
        # 找出最大丢帧数及其位置
        max_drops = int(np.max(dropped_frames))
        max_drop_index = int(np.argmax(dropped_frames))
        max_drop_time = intervals[max_drop_index]
        
        # 统计丢帧点（丢帧数大于0的位置）
        drop_points = []
        for i, drops in enumerate(dropped_frames):
            if drops > 0:
                drop_points.append({
                    'index': i,
                    'timestamp': self.timestamps[i] / 1_000_000,  # 转换为毫秒
                    'interval': intervals[i],
                    'dropped_frames': int(drops)
                })
        
        # 计算总丢帧数
        total_drops = int(np.sum(dropped_frames))

        return {
            'max_drops': max_drops,
            'max_drop_time': max_drop_time,
            'max_drop_index': max_drop_index,
            'total_drops': total_drops,
            'drop_points': drop_points,
            'target_fps': target_fps,
            'target_frame_time': target_frame_time
        }

    def results_analysis(self, target_fps: float = None):
        """
        格式化丢帧分析结果
        :return: dict 包含分析结果的字典
        """
        if len(self.timestamps) < 2:
            return None
            
        # 计算时间间隔（转换为毫秒）
        self.intervals = np.diff(self.timestamps) / 1_000_000
        
        # 基本统计
        avg_interval = np.mean(self.intervals)  # 平均帧时间
        refresh_rate = 1000 / avg_interval  # 平均刷新率
        std_dev = np.std(self.intervals)  # 标准差
        total_time = (self.timestamps[-1] - self.timestamps[0]) / 1_000_000
        actual_duration = total_time / 1000  # 转换为秒
        
        results = {
            'refresh_rate': refresh_rate,  # 平均刷新率
            'frame_time': avg_interval,  # 平均帧时间
            'std_dev': std_dev,  # 标准差
            'min_frame_time': np.min(self.intervals),  # 最大帧间隔
            'max_frame_time': np.max(self.intervals),  # 最小帧间隔
            'sample_count': len(self.intervals),  # 采样数量
            'duration': actual_duration,  # 操作持续时间
            'actual_fps': len(self.intervals) / actual_duration  # 实际帧率
        }

        # 添加丢帧分析结果
        drop_results = self.analyze_frame_drops(target_fps=target_fps)
        results['frame_drops'] = drop_results

        output = [
            f"\n目标帧率: {results['frame_drops']['target_fps']:.2f} FPS",
            f"目标帧时间: {results['frame_drops']['target_frame_time']:.2f} ms",
            f"最大丢帧数: {results['frame_drops']['max_drops']} 帧",
            f"最大丢帧时间: {results['frame_drops']['max_drop_time']:.2f} ms",
            f"总丢帧数: {results['frame_drops']['total_drops']} 帧",
            f"\n丢帧点详情:"
        ]

        for point in results['frame_drops']['drop_points']:
            output.append(
                f"  位置: {point['index']}, "
                f"时间戳: {point['timestamp']:.2f} ms, "
                f"间隔: {point['interval']:.2f} ms, "
                f"丢帧: {point['dropped_frames']} 帧"
            )
        # 打印结果
        info = (
            f"\n===========FPS统计结果============="
            f"\n操作持续时间: {results['duration']:.3f} 秒"
            f"\n平均刷新率: {results['refresh_rate']:.2f} Hz"
            f"\n平均帧时间: {results['frame_time']:.3f} ms"
            f"\n标准差: {results['std_dev']:.3f} ms"
            f"\n采样数量: {results['sample_count']}"
            f"\n实际帧率: {results['actual_fps']:.2f} FPS"
        )
        self.logger.info(info)
        self.logger.info("\n".join(output))
        print(info)
        print("\n".join(output))
        
    def plot_results(self):
        """绘制分析图表"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 帧时间分布直方图
        ax1.hist(self.intervals, bins=50, alpha=0.75, color='blue')
        ax1.set_title('帧时间分布', fontsize=12)
        ax1.set_xlabel('帧时间 (ms)', fontsize=10)
        ax1.set_ylabel('频次', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # 帧时间随时间变化图
        time_points = np.cumsum(self.intervals)
        ax2.plot(time_points, self.intervals, 'g-', alpha=0.5)
        ax2.set_title('帧时间随时间变化', fontsize=12)
        ax2.set_xlabel('累计时间 (ms)', fontsize=10)
        ax2.set_ylabel('帧时间 (ms)', fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()

    def start_monitoring(self):
        """开始监控"""
        try:
            print("FPS监听已启动")
            self.is_monitoring = True
            while self.is_monitoring:
                try:
                    self.record_frame()
                except Exception as e:
                    print(f"读取数据时出错: {e}")
        except Exception as e:
            print(f"监听器启动失败: {e}")
        finally:
            self.stop_monitoring()

    def stop_monitoring(self):
        """停止监听"""
        self.is_monitoring = False
        self.is_monitoring = False
        self.logger.info("FPS监听已停止")


# 监控Win+D操作的示例
def monitor_win_d_operation():
    """监控Win+D操作的示例"""
    import keyboard
    logger = create_logger(
            name="FPS_monitor",
            level="INFO",
            time_rotating=True,
            when='midnight'
        )
    
    monitor = RefreshRateMonitor(show_plot=True, logger=logger)
    print("等待Win+D操作...")
    
    # 等待Win+D
    keyboard.wait('windows+d')
    print(f"检测到Win+D - 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}")
    
    # 开始监控
    monitor.start_monitoring()
    
    # 监控一段时间（例如200ms）
    time.sleep(2)
    # 停止监控并获取结果
    monitor.stop_monitoring()

    # 打印丢帧分析结果
    monitor.results_analysis()
    monitor.plot_results()


if __name__ == "__main__":
    # 运行示例
    monitor_win_d_operation()