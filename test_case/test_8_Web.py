from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from pynput import mouse
from datetime import datetime
import time
from common.logger import create_logger
from common.PFS_monitor import RefreshRateMonitor
from common.performance_monitor import PerformanceMonitor
from common.power_consumption import PowerMonitor
import keyboard
import multiprocessing

logger = create_logger(
    name="test_restore_desktop",
    level="INFO",
    time_rotating=True,
    when='midnight')

def process_performance_monitor():
    """性能监控进程"""
    monitor = PerformanceMonitor(logger=logger)
    keyboard.wait('enter')
    monitor.start_monitoring()
    time.sleep(10)
    monitor.stop_monitoring()
    summary = monitor.get_performance_summary()
    print(summary)


def process_power_monitor():
    """功耗监控进程"""
    power_monitor = PowerMonitor(logger=logger)
    keyboard.wait('enter')
    power_monitor.start_monitoring()
    time.sleep(10)
    power_monitor.stop_monitoring()
    summary = power_monitor.get_power_summary()
    print(summary)


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


class ScrollMonitor:
    def __init__(self):
        # 指定Edge WebDriver的路径

        edge_driver_path = "../DLLs/msedgedriver.exe"
        # 创建Edge WebDriver的Service对象
        service = Service(executable_path=edge_driver_path)
        # 初始化Edge WebDriver并指定Service
        self.driver = webdriver.Edge(service=service)
        self.mouse_scroll_time = None
        self.mouse_scroll_time = None
        self.pixel_scroll_time = None
        self.monitoring = True

    def on_scroll(self, x, y, dx, dy):
        if self.mouse_scroll_time is None:
            self.mouse_scroll_time = datetime.now()
            print(f"\n检测到鼠标滚轮移动，时间: {self.mouse_scroll_time.strftime('%H:%M:%S.%f')}")

    def monitor_page_scroll(self):
        try:
            # 打开bilibili
            print(datetime.now().strftime('%H:%M:%S.%f'), "正在打开bilibili...")
            self.driver.get("https://www.bilibili.com/")
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print(datetime.now().strftime('%H:%M:%S.%f'), "页面加载完成，请使用鼠标滚轮滚动...")


            # 开始监听鼠标滚轮
            listener = mouse.Listener(on_scroll=self.on_scroll)
            listener.start()

            last_scroll = 0
            while self.monitoring:
                current_scroll = self.driver.execute_script("return window.pageYOffset;")
                
                if current_scroll > 1 and self.pixel_scroll_time is None and self.mouse_scroll_time is not None:
                    self.pixel_scroll_time = datetime.now()
                    print(f"检测到页面滚动，时间: {self.pixel_scroll_time.strftime('%H:%M:%S.%f')}")
                    
                    # 计算响应时间
                    response_time = (self.pixel_scroll_time - self.mouse_scroll_time).total_seconds()
                    print("\n响应时间总结:")
                    print(f"鼠标滚动时间: {self.mouse_scroll_time.strftime('%H:%M:%S.%f')}")
                    print(f"页面响应时间: {self.pixel_scroll_time.strftime('%H:%M:%S.%f')}")
                    print(f"响应延迟: {response_time * 1000:.2f} 毫秒")
                    
                    self.monitoring = False
                    break
                
                time.sleep(0.001)  # 降低CPU使用率

        finally:
            listener.stop()
            self.driver.quit()


def web():
    keyboard.wait('enter')
    monitor = ScrollMonitor()
    monitor.monitor_page_scroll()


if __name__ == "__main__":

    performance_process = multiprocessing.Process(
        target=process_performance_monitor,
        name="PerformanceMonitor"
    )

    power_process = multiprocessing.Process(
        target=process_power_monitor,
        name="PowerMonitor"
    )
    keyboard_monitor = multiprocessing.Process(
        target=process_keyboard_monitor,
        name="KeyboardMonitor"
    )

    keyboard_web = multiprocessing.Process(
        target=web,
        name="web"
    )
    # fps = RefreshRateMonitor(show_plot=True, logger=logger)
    # fps.start_monitoring()

    keyboard_web.start()
    performance_process.start()
    power_process.start()
    keyboard_monitor.start()


    keyboard_web.join()
    performance_process.join()
    power_process.join()
    keyboard_monitor.join()

    # fps.stop_monitoring()
    # fps.format_drop_results()