"""
@File    : test_7_open_apps.py
@Time    : 2025/01/13
@Author  : Bruce.Si
@Desc    : 打开应用,运行代码后找到对于软件右键，按enter启动，等待运行结束
"""

import multiprocessing
import keyboard
import time
from datetime import datetime
from common.window_monitor import WindowMonitor
from common.desktop_focus_monitor import DesktopFocusMonitor
from common.logger import create_logger
from common.PFS_monitor import RefreshRateMonitor
from pywinauto import Application
from common.performance_monitor import PerformanceMonitor
from common.power_consumption import PowerMonitor


# 创建主程序日志器
logger = create_logger(
    name="test_open_apps",
    level="INFO",
    time_rotating=True,
    when='midnight'
)
# 目标app
target = {
    "title": "中望3D 2025 x64",
    "size": (2906, 1730),
    "is_maximized": True
    # "title": "MatePad Pro 全场景发布会-final.pptx - PowerPoint (未经授权产品)",
    # "size": (2160, 1241),
    # "is_maximized": False
}

# 目标app内元素
window_title = "中望3D 2025 x64"
element_title = "菜单栏"
# window_title = "MatePad Pro 全场景发布会-final.pptx - PowerPoint (未经授权产品)"
# element_title = "幻灯片 17 - "


def process_window_monitor():
    """窗口监控进程"""
    monitor = WindowMonitor(logger=logger, target=target)
    try:
        monitor.start_monitoring()
        while monitor.is_monitoring:
            time.sleep(0.00001)
    except KeyboardInterrupt:
        monitor.stop_monitoring()


def process_keyboard_monitor():
    """键盘监控进程, 打开应用"""
    # 等待检测 enter 组合键
    fps = RefreshRateMonitor(show_plot=True, logger=logger)
    keyboard.wait('enter')
    key_press_time = datetime.now()
    logger.info(f"检测到enter按键时间: {key_press_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    fps.start_monitoring()
    time.sleep(5)
    fps.stop_monitoring()
    fps.format_drop_results()


def process_performance_monitor():
    """性能监控进程"""
    monitor = PerformanceMonitor(logger=logger)
    keyboard.wait('enter')
    monitor.start_monitoring()
    time.sleep(5)
    monitor.stop_monitoring()
    summary = monitor.get_performance_summary()
    print(summary)


def process_power_monitor():
    """功耗监控进程"""
    power_monitor = PowerMonitor(logger=logger)
    keyboard.wait('enter')
    power_monitor.start_monitoring()
    time.sleep(5)
    power_monitor.stop_monitoring()
    summary = power_monitor.get_power_summary()
    print(summary)


def monitor_element():
    """
    持续监测窗口内目标元素，直到找到目标元素。

    参数:
    window_title (str): 窗口的标题。
    element_title (str): 元素的标题（可选）。
    """
    global window_title, element_title

    if not element_title:
        logger.error("请提供要监测的元素标题")
        return

    app = Application(backend="uia")
    start_time = datetime.now()
    logger.info(f"开始监测元素 - 窗口: {window_title}, 元素: {element_title}")

    # 性能统计变量
    iteration_count = 0

    while True:
        try:
            iteration_count += 1

            # 尝试连接窗口
            app.connect(title=window_title)
            window = app.window(title=window_title)

            try:
                # 尝试查找元素
                window.child_window(title=element_title)
                found_time = datetime.now()
                duration = (found_time - start_time).total_seconds() * 1000

                # 计算总体性能统计
                total_iterations = iteration_count
                total_time = (found_time - start_time).total_seconds()
                avg_iteration_time = total_time / total_iterations * 1000
                iterations_per_second = total_iterations / total_time

                logger.info(
                    f"\n找到目标元素:\n"
                    f"时间: {found_time.strftime('%Y-%m-%d %H:%M:%S.%f')}\n"
                    f"窗口: {window_title}\n"
                    f"元素: {element_title}\n"
                    f"总耗时: {duration:.2f}ms\n"
                    f"总检测次数: {total_iterations}\n"
                    f"平均每次检测耗时: {avg_iteration_time:.3f}ms\n"
                    f"平均检测频率: {iterations_per_second:.1f}次/秒"
                )
                break
            except Exception:
                # 元素未找到，继续监测
                time.sleep(0.00001)  # 添加小延迟，降低CPU使用率
                continue
        except Exception as e:
            # 窗口未找到或其他错误，继续监测
            time.sleep(0.00001)  # 添加小延迟，降低CPU使用率
            continue


def main():
    """主程序"""

    try:
        # 创建进程
        window_process = multiprocessing.Process(
            target=process_window_monitor,
            name="WindowMonitor"
        )

        keyboard_monitor = multiprocessing.Process(
            target=process_keyboard_monitor,
            name="KeyboardMonitor"
        )

        desktop_process = multiprocessing.Process(
            target=monitor_element,
            name="DesktopMonitor"
        )

        performance_process = multiprocessing.Process(
            target=process_performance_monitor,
            name="PerformanceMonitor"
        )

        power_process = multiprocessing.Process(
            target=process_power_monitor,
            name="PowerMonitor"
        )

        # 启动进程
        logger.info("正在启动所有监控进程...")
        window_process.start()
        keyboard_monitor.start()
        desktop_process.start()
        performance_process.start()
        power_process.start()

        # 等待进程结束
        desktop_process.join()
        window_process.join()
        keyboard_monitor.join()
        performance_process.join()
        power_process.join()

        logger.info("所有监控进程已结束")

    except Exception as e:
        logger.error(f"主程序异常: {e}")
    finally:
        # 确保进程正确退出
        if window_process.is_alive():
            window_process.terminate()
        if desktop_process.is_alive():
            desktop_process.terminate()
        if keyboard_monitor.is_alive():
            keyboard_monitor.terminate()
        if performance_process.is_alive():
            performance_process.terminate()
        if power_process.is_alive():
            power_process.terminate()

        logger.info("程序已退出")
        logger.info(f"\n{'-' * 100}")


if __name__ == "__main__":
    multiprocessing.freeze_support()  # Windows下打包支持
    main()
