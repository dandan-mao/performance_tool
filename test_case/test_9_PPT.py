import win32com.client
import time
import win32gui
import win32con
from datetime import datetime
import win32ui
from ctypes import windll
import numpy as np
from common.PFS_monitor import RefreshRateMonitor
from common.logger import create_logger
from common.PFS_monitor import RefreshRateMonitor
from common.performance_monitor import PerformanceMonitor
from common.power_consumption import PowerMonitor
import keyboard
import multiprocessing


logger = create_logger(
            name="test",
            level="DEBUG",
            console_output=True,
            time_rotating=True,
            when='midnight'
        )

def process_performance_monitor():
    """性能监控进程"""
    monitor = PerformanceMonitor(logger=logger)
    keyboard.wait('enter')
    monitor.start_monitoring()
    time.sleep(15)
    monitor.stop_monitoring()
    summary = monitor.get_performance_summary()
    print(summary)


def process_power_monitor():
    """功耗监控进程"""
    power_monitor = PowerMonitor(logger=logger)
    keyboard.wait('enter')
    power_monitor.start_monitoring()
    time.sleep(15)
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
    time.sleep(15)
    fps.stop_monitoring()
    fps.format_drop_results()

def capture_window(hwnd):
    """捕获窗口内容"""
    # 获取窗口尺寸
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    # 创建设备上下文
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    
    # 创建位图对象
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitMap)
    
    # 复制窗口内容
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
    
    # 获取位图信息
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    
    # 清理资源
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    
    return np.frombuffer(bmpstr, dtype='uint8')

def is_window_content_changed(prev_content, curr_content):
    """检查窗口内容是否发生变化"""
    if prev_content is None or curr_content is None:
        return False
    if len(prev_content) != len(curr_content):
        return False
    return not np.array_equal(prev_content, curr_content)

def find_slideshow_window():
    """查找PPT放映窗口"""
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            className = win32gui.GetClassName(hwnd)
            if className == "screenClass":
                hwnds.append(hwnd)
        return True
    
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None

def get_time_ms(start_time):
    """计算从开始时间到现在的毫秒数"""
    delta = datetime.now() - start_time
    return int(delta.total_seconds() * 1000)

def monitor_ppt_performance():
    try:


        # fps = RefreshRateMonitor(show_plot=True, logger=logger)
        #
        # fps.start_monitoring()

        # 创建PPT应用实例
        ppt = win32com.client.Dispatch("PowerPoint.Application")
        
        # 打开PPT文件
        presentation = ppt.Presentations.Open(r"C:\Users\yu\Desktop\MatePad Pro 全场景发布会-final.pptx")
        
        # 记录开始时间
        start_time = datetime.now()
        print(f"开始时间: {start_time.strftime('%H:%M:%S.%f')[:-3]}")
        
        # 开始放映
        presentation.SlideShowSettings.Run()
        
        # 等待放映窗口出现
        slideshow_hwnd = None
        while not slideshow_hwnd:
            slideshow_hwnd = find_slideshow_window()
            if slideshow_hwnd:
                print("PPT放映窗口出现",slideshow_hwnd)
                response_time = get_time_ms(start_time)
                print(f"响应时间: {response_time}ms")
            time.sleep(0.01)
        
        # 监控窗口内容变化
        prev_content = None
        content_stable_start = None
        content_stable_duration = 100  # 内容稳定100ms认为完成
        
        while True:
            if not win32gui.IsWindow(slideshow_hwnd):
                break
                
            current_content = capture_window(slideshow_hwnd)
            
            if is_window_content_changed(prev_content, current_content):
                content_stable_start = None
            elif prev_content is not None and content_stable_start is None:
                content_stable_start = datetime.now()
                print("内容稳定开始", get_time_ms(start_time), 'ms')
            
            if content_stable_start and get_time_ms(content_stable_start) >= content_stable_duration:
                complete_time = get_time_ms(start_time)
                print(f"完成时间: {complete_time}ms")
                break
                
            prev_content = current_content
            time.sleep(0.001)

        time.sleep(2)
        # fps.stop_monitoring()
        # fps.format_drop_results()
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        # 关闭演示
        try:
            if presentation:
                presentation.SlideShowWindow.View.Exit()
                presentation.Close()
            if ppt:
                ppt.Quit()
        except:
            pass

def test_multiple_times(times=1):

    keyboard.wait('enter')
    """多次测试取平均值"""
    response_times = []
    complete_times = []
    
    for i in range(times):
        print(f"\n第 {i+1} 次测试:")
        time.sleep(2)  # 测试间隔
        monitor_ppt_performance()
    
    # 如果需要计算平均值，可以取消下面的注释
    # if response_times:
    #     avg_response = sum(response_times) / len(response_times)
    #     print(f"\n平均响应时间: {avg_response:.0f}ms")
    # if complete_times:
    #     avg_complete = sum(complete_times) / len(complete_times)
    #     print(f"平均完成时间: {avg_complete:.0f}ms")

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

    keyboard_ppt = multiprocessing.Process(
        target=test_multiple_times,
        name="ppt"
    )

    keyboard_ppt.start()
    performance_process.start()
    power_process.start()
    keyboard_monitor.start()


    keyboard_ppt.join()
    performance_process.join()
    power_process.join()
    keyboard_monitor.join()

