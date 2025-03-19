# -*- coding: utf-8 -*-
"""
@File    : keyboard_monitor.py
@Time    : 2025/01/06
@Author  : Bruce.Si
@Desc    : 键盘监控模块
"""

from pynput import keyboard
import threading
from typing import Dict, Set, Optional, Callable
import time
from datetime import datetime
from common.logger import Logger
import keyboard as key


class KeyboardMonitor:
    def __init__(self, logger: Logger, target: Optional[str] = None):
        """
        初始化键盘监控器
        
        Args:
            logger: 外部传入的日志对象
            target: 目标组合键，触发后停止监控（例如：'windows+d'）
        """
        self.current_keys: Set[str] = set()  # 当前按下的键
        self.key_press_times: Dict[str, float] = {}  # 按键时间记录
        self.callbacks: Dict[str, Callable] = {}  # 回调函数字典
        self.listener: Optional[keyboard.Listener] = None
        self.is_monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 0.001  # 1毫秒的监听间隔
        
        # 目标组合键
        self.target = target.lower() if target else None
        self.target_keys = set(target.lower().split('+')) if target else set()
        
        # 使用外部传入的日志器
        self.logger = logger

    def _normalize_key(self, key) -> str:
        """统一按键名称格式"""
        try:
            if isinstance(key, keyboard.Key):
                return str(key).replace('Key.', '')
            return key.char.lower()
        except AttributeError:
            return str(key)

    def on_press(self, key):
        """按键按下事件处理"""
        try:
            key_name = self._normalize_key(key)
            current_time = time.time()
            
            # 记录按键和时间
            self.current_keys.add(key_name)
            self.key_press_times[key_name] = current_time
            
            # 检查是否是目标组合键
            if self.target and self.target_keys.issubset(self.current_keys):
                self.logger.info({
                    "事件": "target_hotkey_triggered",
                    "combination": self.target,
                    "时间": datetime.now().strftime('%H:%M:%S.%f')
                })
                # 停止监控
                self.is_monitoring = False
                return False  # 停止监听
            
            # 检查其他组合键
            self._check_combinations()

            # 记录日志
            self.logger.info({
                "事件": "按键按下",
                "键": key_name,
                "当前按下的键": list(self.current_keys),
                "时间": datetime.now().strftime('%H:%M:%S.%f')
            })
            
        except Exception as e:
            self.logger.error(f"按键处理错误: {e}")

    def on_release(self, key):
        """按键释放事件处理"""
        try:
            key_name = self._normalize_key(key)
            
            # 计算按键持续时间
            if key_name in self.key_press_times:
                duration = time.time() - self.key_press_times[key_name]
                self.logger.info({
                    "事件": "按键释放",
                    "键": key_name,
                    "间隔": f"{duration:.6f}s",
                    "时间": datetime.now().strftime('%H:%M:%S.%f')
                })
            
            # 清理按键记录
            self.current_keys.discard(key_name)
            self.key_press_times.pop(key_name, None)
            
        except Exception as e:
            self.logger.error(f"按键释放处理错误: {e}")

    def _check_combinations(self):
        """检查组合键"""
        try:
            for combo, callback in self.callbacks.items():
                required_keys = set(combo.lower().split('+'))
                if required_keys.issubset(self.current_keys):
                    self.logger.info({
                        "event": "hotkey_triggered",
                        "combination": combo,
                        "timestamp": datetime.now().strftime('%H:%M:%S.%f')
                    })
                    callback()
        except Exception as e:
            self.logger.error(f"组合键检查错误: {e}")

    def register_hotkey(self, key_combination: str, callback: Callable):
        """
        注册热键组合及其回调函数
        
        Args:
            key_combination: 按键组合，格式如 'ctrl+shift+a'
            callback: 触发时调用的函数
        """
        self.callbacks[key_combination.lower()] = callback
        self.logger.info({
            "event": "hotkey_registered",
            "combination": key_combination
        })

    def start_monitoring(self):
        """开始监控键盘输入"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            self.listener.start()

            if self.target:
                self.logger.info({
                    "event": "monitoring_started",
                    "target_hotkey": self.target,
                    "timestamp": datetime.now().strftime('%H:%M:%S.%f')
                })
            else:
                self.logger.info("键盘监控已启动")

    def stop_monitoring(self):
        """停止键盘监控"""
        if self.is_monitoring and self.listener:
            self.is_monitoring = False
            self.listener.stop()
            self.listener = None
            self.current_keys.clear()
            self.key_press_times.clear()
            self.logger.info("键盘监控已停止")

    def get_pressed_keys(self) -> Set[str]:
        """获取当前按下的所有键"""
        return self.current_keys.copy()

    def is_key_pressed(self, key: str) -> bool:
        """检查指定键是否被按下"""
        return key.lower() in self.current_keys

    def get_key_hold_duration(self, key: str) -> Optional[float]:
        """获取指定键的按住时长（秒）"""
        key = key.lower()
        if key in self.key_press_times and key in self.current_keys:
            return time.time() - self.key_press_times[key]
        return None

def main():
    """
    独立运行时的入口函数
    """
    from common.logger import create_logger
    
    # 创建日志器
    logger = create_logger(
        name="keyboard_monitor",
        level="DEBUG",
        time_rotating=True,
        when='midnight'
    )
    
    # 创建监控实例，设置目标组合键为 Win+D
    monitor = KeyboardMonitor(logger=logger, target='cmd+122')
    
    try:
        # 开始监控
        monitor.start_monitoring()
        logger.info("等待目标组合键 (Win+right) 或按 Ctrl+C 退出...")
        time.sleep(2)
        key.press("win")
        time.sleep(0.5)
        key.press("right")
        time.sleep(0.5)
        key.release("right")
        time.sleep(0.5)
        key.release("win")
        time.sleep(0.5)
        logger.info("监控已结束")

    except KeyboardInterrupt:
        monitor.stop_monitoring()
        logger.info("程序被手动中断")

if __name__ == "__main__":
    main()