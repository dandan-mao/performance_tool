# **AUTO WIN**

​	auto_win是基于python实现的windows系统下性能和硬件监听工具包，本工具包提供了一系列通用的工具类和功能模块，用于简化开发过程。

关键特性：

- 纯python
- 基于windows基础API
- HWINFO性能监听

## 安装

Open a terminal and run (Requires Python 3.11+):

```python
# 运行 pip freeze > requirements.txt下载代码需要的第三方资源包
pip freeze > requirements.txt
```

## 介绍

### common

- desktop_focus_monitor.py: 桌面焦点监控工具
- HWINFO_monitor.py: WH_INFO共享内存下获取功耗信息
- HWinfolog_monitor.py: WH_INFO日志下获取功耗信息
- keyboard_monitor.py: 键盘按键监控工具
- lock_monitor.py: 系统锁屏状态监控工具（未完成）
- mouse_monitor.py: 鼠标移动和点击监控工具
- performance_monitor.py: 系统性能监控工具
- PFS_monitor.py: 显示器刷新率监控工具
- power_consumption.py: 系统整体功耗监控工具
- taskmgr_monitor.py: 任务管理器DLL调用工具
- wheel_monitor.py: 鼠标滚轮使用监控工具
- window_monitor.py: 窗口状态和大小监控工具

