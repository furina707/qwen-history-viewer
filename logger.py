#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统 - 分 Runtime Log 和 Historical Log
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional


class LogSystem:
    """
    日志系统管理器
    
    - Runtime Log: 当前运行期间的日志，程序启动时创建
    - Historical Log: 历史日志，按天轮转保存
    """
    
    def __init__(self, log_dir: Optional[str] = None, name: str = "qwen_history_gui"):
        """
        初始化日志系统
        
        Args:
            log_dir: 日志目录，默认为 ~/.qwen_gui/logs
            name: 日志名称
        """
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / ".qwen_gui" / "logs"
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # 根级别设为 DEBUG，让 handler 控制过滤
        
        # 清除现有的 handler
        self.logger.handlers.clear()
        
        # 创建 formatter
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        self.simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 设置日志级别映射
        self.level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        # 初始化日志处理器
        self._setup_runtime_log()
        self._setup_historical_log()
        self._setup_console_handler()
    
    def _setup_runtime_log(self) -> None:
        """
        设置 Runtime Log
        记录当前运行期间的所有日志（DEBUG 级别及以上）
        """
        runtime_log_file = self.log_dir / "runtime.log"
        
        # 使用轮转文件处理器，避免日志文件过大
        runtime_handler = RotatingFileHandler(
            runtime_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        runtime_handler.setLevel(logging.DEBUG)
        runtime_handler.setFormatter(self.detailed_formatter)
        
        self.logger.addHandler(runtime_handler)
    
    def _setup_historical_log(self) -> None:
        """
        设置 Historical Log
        按天轮转保存历史日志（INFO 级别及以上）
        """
        historical_log_file = self.log_dir / "history"
        
        # 按天轮转，保留最近 30 天
        history_handler = TimedRotatingFileHandler(
            historical_log_file,
            when='D',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        history_handler.setLevel(logging.INFO)
        history_handler.setFormatter(self.detailed_formatter)
        history_handler.suffix = "%Y-%m-%d.log"
        
        self.logger.addHandler(history_handler)
    
    def _setup_console_handler(self, level: str = "INFO") -> None:
        """
        设置控制台日志输出
        
        Args:
            level: 日志级别
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level_map.get(level, logging.INFO))
        console_handler.setFormatter(self.simple_formatter)
        
        self.logger.addHandler(console_handler)
    
    def set_level(self, level: str) -> None:
        """
        设置控制台日志级别
        
        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                handler.setLevel(self.level_map.get(level, logging.INFO))
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs) -> None:
        self.logger.exception(msg, *args, **kwargs)
    
    def get_log_file(self, log_type: str = "runtime") -> Path:
        """
        获取日志文件路径
        
        Args:
            log_type: 日志类型 (runtime, historical)
        
        Returns:
            日志文件路径
        """
        if log_type == "runtime":
            return self.log_dir / "runtime.log"
        elif log_type == "historical":
            return self.log_dir / "history"
        else:
            return self.log_dir / f"{log_type}.log"
    
    def open_log_file(self, log_type: str = "runtime") -> None:
        """
        使用默认程序打开日志文件
        
        Args:
            log_type: 日志类型 (runtime, historical)
        """
        import subprocess
        log_file = self.get_log_file(log_type)
        if log_file.exists():
            subprocess.Popen(['notepad.exe', str(log_file)])
        else:
            self.warning(f"日志文件不存在：{log_file}")
    
    def clear_logs(self) -> None:
        """清空所有日志文件"""
        try:
            for log_file in self.log_dir.glob("*.log"):
                log_file.unlink()
            self.info("日志已清空")
        except Exception as e:
            self.error(f"清空日志失败：{e}")


# 全局日志实例
_global_logger: Optional[LogSystem] = None


def get_logger() -> LogSystem:
    """获取全局日志实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = LogSystem()
    return _global_logger


def init_logger(log_dir: Optional[str] = None, name: str = "qwen_history_gui") -> LogSystem:
    """初始化全局日志"""
    global _global_logger
    _global_logger = LogSystem(log_dir, name)
    return _global_logger
