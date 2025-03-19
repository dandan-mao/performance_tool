# -*- coding: utf-8 -*-
"""
@File    : logger.py
@Time    : 2025/01/06
@Author  : Bruce.Si
@Desc    : 通用日志类
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Union, Dict
import json

class Logger:
    """
    通用日志类，支持控制台和文件输出，支持日志轮转
    """
    
    def __init__(
        self,
        name: str,
        level: str = "INFO",
        log_dir: str = "logs",
        log_file: Optional[str] = None,
        console_output: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        encoding: str = 'utf-8',
        time_rotating: bool = False,
        when: str = 'midnight',
        format_string: Optional[str] = None
    ):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: 日志文件目录
            log_file: 日志文件名（如果为None，则使用name_YYYYMMDD.log）
            console_output: 是否输出到控制台
            max_bytes: 单个日志文件最大字节数
            backup_count: 备份文件数量
            encoding: 文件编码
            time_rotating: 是否按时间轮转
            when: 时间轮转周期 ('S', 'M', 'H', 'D', 'midnight')
            format_string: 自定义日志格式
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        self.log_dir = log_dir
        self.console_output = console_output
        self.encoding = encoding
        
        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 设置日志文件名
        if log_file is None:
            log_file = f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        self.log_file = os.path.join(log_dir, log_file)
        
        # 创建日志器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # 自定义格式化器，支持完整的微秒显示
        class MicrosecondFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                created = datetime.fromtimestamp(record.created)
                if datefmt:
                    return created.strftime(datefmt)
                return f"{created.strftime('%Y-%m-%d %H:%M:%S')}.{created.microsecond:06d}"
        
        # 设置日志格式
        if format_string is None:
            format_string = (
                '%(asctime)s - %(levelname)s - '
                '%(filename)s:%(lineno)d - %(funcName)s - %(message)s'
            )
        
        # 使用自定义格式化器
        self.formatter = MicrosecondFormatter(format_string)
        
        # 添加处理器
        self.add_handlers(
            max_bytes=max_bytes,
            backup_count=backup_count,
            time_rotating=time_rotating,
            when=when
        )

    def add_handlers(
        self,
        max_bytes: int,
        backup_count: int,
        time_rotating: bool,
        when: str
    ):
        """添加日志处理器"""
        # 清除现有处理器
        self.logger.handlers = []
        
        # 添加文件处理器
        if time_rotating:
            file_handler = TimedRotatingFileHandler(
                filename=self.log_file,
                when=when,
                backupCount=backup_count,
                encoding=self.encoding
            )
        else:
            file_handler = RotatingFileHandler(
                filename=self.log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=self.encoding
            )
        
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
        
        # 添加控制台处理器
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(self.formatter)
            self.logger.addHandler(console_handler)

    def debug(self, message: Union[str, Dict], *args, **kwargs):
        """记录调试级别日志"""
        self._log(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: Union[str, Dict], *args, **kwargs):
        """记录信息级别日志"""
        self._log(logging.INFO, message, *args, **kwargs)

    def warning(self, message: Union[str, Dict], *args, **kwargs):
        """记录警告级别日志"""
        self._log(logging.WARNING, message, *args, **kwargs)

    def error(self, message: Union[str, Dict], *args, **kwargs):
        """记录错误级别日志"""
        self._log(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: Union[str, Dict], *args, **kwargs):
        """记录严重错误级别日志"""
        self._log(logging.CRITICAL, message, *args, **kwargs)

    def _log(self, level: int, message: Union[str, Dict], *args, **kwargs):
        """
        统一的日志记录方法
        支持字符串和字典类型的消息
        """
        if isinstance(message, dict):
            message = json.dumps(message, ensure_ascii=False, indent=2)
        self.logger.log(level, message, *args, **kwargs)

    def set_level(self, level: str):
        """动态设置日志级别"""
        self.logger.setLevel(getattr(logging, level.upper()))

def create_logger(name: str, **kwargs) -> Logger:
    """
    创建日志器的工厂方法
    """
    return Logger(name, **kwargs)

def main():
    """使用示例"""
    # 创建日志器
    logger = create_logger(
        name="test",
        level="DEBUG",
        console_output=True,
        time_rotating=True,
        when='midnight'
    )
    
    # 记录不同级别的日志
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.critical("这是一条严重错误日志")
    
    # 记录结构化数据
    data = {
        "user": "test_user",
        "action": "login",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    }
    logger.info(data)

if __name__ == "__main__":
    main()