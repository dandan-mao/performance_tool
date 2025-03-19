# -*- coding: utf-8 -*-
"""
@File    : HWINFO_monitor.py
@Time    : 2025/03/017
@Author  : Bruce.Si
@Desc    : WH_INFO监听器UI版
"""


import tkinter as tk
from tkinter import messagebox, simpledialog
import time
import threading

from common.HWINFO_monitor import HWiNFOMonitor


class PerformanceMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("性能监听器")
        self.is_listening = False
        self.thread = None
        self.data_record = []

        # 初始化默认监听项目
        self.monitor_items = [
            'Total CPU Utility',
            'CPU Package Power',
        ]

        # 创建框架用于布局
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=10)

        self.item_listbox = tk.Listbox(self.input_frame, selectmode=tk.SINGLE, width=30)
        self.item_listbox.pack(side=tk.LEFT, padx=10)
        for item in self.monitor_items:
            self.item_listbox.insert(tk.END, item)

        self.add_button = tk.Button(self.input_frame, text="添加", command=self.add_item)
        self.add_button.pack(side=tk.TOP, padx=5)

        self.delete_button = tk.Button(self.input_frame, text="删除", command=self.delete_item)
        self.delete_button.pack(side=tk.BOTTOM, padx=5)

        # 创建开始和停止按钮
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=10)

        self.start_button = tk.Button(self.control_frame, text="开始监听", command=self.start_listening)
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(self.control_frame, text="停止监听", command=self.stop_listening,
                                     state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # 创建显示标签的框架
        self.display_frame = tk.Frame(root)
        self.display_frame.pack(pady=10)

        self.labels = {}
        for item in self.monitor_items:
            label = tk.Label(self.display_frame, text=f"{item}: 0%")
            label.pack(pady=5)
            self.labels[item] = label

        # 单个标签大致高度（可根据实际调整）
        self.label_height = 25
        # 窗口居中显示
        self.center_window()

    def add_item(self):
        if not self.is_listening:
            new_item = simpledialog.askstring("添加监听项目", "请输入新的监听项目:")
            if new_item:
                if new_item not in self.monitor_items:
                    self.monitor_items.append(new_item)
                    self.item_listbox.insert(tk.END, new_item)
                    label = tk.Label(self.display_frame, text=f"{new_item}: 0%")
                    label.pack(pady=5)
                    self.labels[new_item] = label
                    # 增加窗口高度
                    self.adjust_window_height(self.label_height)
                else:
                    messagebox.showwarning("警告", "该项目已存在！")

    def delete_item(self):
        if not self.is_listening:
            selected_index = self.item_listbox.curselection()
            if selected_index:
                index = selected_index[0]
                item = self.item_listbox.get(index)
                self.monitor_items.remove(item)
                self.item_listbox.delete(index)
                self.labels[item].destroy()
                del self.labels[item]
                # 减少窗口高度
                self.adjust_window_height(-self.label_height)

    def start_listening(self):
        self.is_listening = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.add_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        self.data_record.clear()
        self.thread = threading.Thread(target=self.monitor_performance)
        self.thread.start()

    def stop_listening(self):
        self.is_listening = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.add_button.config(state=tk.NORMAL)
        self.delete_button.config(state=tk.NORMAL)
        for item in self.monitor_items:
            data = [i[item.lower()] for i in self.data_record]
            self.labels[item].config(text=f"{item}: {round(sum(data) / len(data), 2)}%")
            print(round(sum(data) / len(data), 2))
        if self.thread:
            self.thread.join()

    def monitor_performance(self):
        # 调用HWinfo
        HWiNFO_monitor = HWiNFOMonitor(self.monitor_items, interval=1.0)
        HWiNFO_monitor.reader.open()
        HWiNFO_monitor.init_label_indices()
        while self.is_listening:
            # 读取标签数据
            performance_data = HWiNFO_monitor.read_target_sensors_to_result()
            for item in self.monitor_items:
                self.labels[item].config(text=f"{item}: {round(performance_data[item.lower()], 2)}%")
                # 可以根据需要添加更多的监听项目处理逻辑
            self.data_record.append(performance_data)
            print(performance_data)
            time.sleep(1)

    def center_window(self):
        # 更新窗口信息
        self.root.update_idletasks()
        # 获取窗口宽度和高度
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        # 获取屏幕宽度和高度
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # 计算窗口起始位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        # 设置窗口位置
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def adjust_window_height(self, delta_height):
        # 更新窗口信息
        self.root.update_idletasks()
        # 获取当前窗口宽度和高度
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        new_height = height + delta_height
        # 获取屏幕宽度和高度
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # 计算窗口起始位置
        x = (screen_width - width) // 2
        y = (screen_height - new_height) // 2
        # 设置窗口位置和大小
        self.root.geometry(f"{width}x{new_height}+{x}+{y}")


if __name__ == "__main__":
    root = tk.Tk()
    monitor = PerformanceMonitor(root)
    root.mainloop()
