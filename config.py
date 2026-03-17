#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置系统 - 用于管理程序参数
"""

import json
import os
from pathlib import Path
from typing import Any, Optional


class Config:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        # 外观设置
        "theme": "dark",  # dark, light, blue, green
        "font_family": "Microsoft YaHei",
        "font_size": 12,
        
        # CLI 设置
        "cli_command": "qwen",
        "cli_auto_resume": True,
        "default_session_id": None,
        
        # 日志设置
        "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        "log_max_size_mb": 10,
        "log_backup_count": 5,
        
        # 窗口设置
        "window_width": 1400,
        "window_height": 900,
        "window_position": "center",
        
        # 进程锁定
        "enable_process_lock": True,
        "locked_processes": [],
        
        # 其他设置
        "auto_save": True,
        "confirm_delete": True,
        "show_statistics": True,
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为 ~/.qwen_gui/config.json
        """
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = Path.home() / ".qwen_gui" / "config.json"
        
        self._config: dict = {}
        self._load()
    
    def _load(self) -> None:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                # 合并默认配置（确保新添加的配置项存在）
                merged = self.DEFAULT_CONFIG.copy()
                merged.update(self._config)
                self._config = merged
            else:
                self._config = self.DEFAULT_CONFIG.copy()
                self._save()
        except Exception as e:
            print(f"加载配置文件失败：{e}，使用默认配置")
            self._config = self.DEFAULT_CONFIG.copy()
    
    def _save(self) -> None:
        """保存配置文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败：{e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._config[key] = value
        self._save()
    
    def reset(self, key: Optional[str] = None) -> None:
        """重置配置"""
        if key:
            self._config[key] = self.DEFAULT_CONFIG.get(key)
        else:
            self._config = self.DEFAULT_CONFIG.copy()
        self._save()
    
    def get_all(self) -> dict:
        """获取所有配置"""
        return self._config.copy()
    
    @property
    def theme(self) -> str:
        return self._config.get("theme", "dark")
    
    @theme.setter
    def theme(self, value: str) -> None:
        self.set("theme", value)
    
    @property
    def log_level(self) -> str:
        return self._config.get("log_level", "INFO")
    
    @log_level.setter
    def log_level(self, value: str) -> None:
        self.set("log_level", value)


# 全局配置实例
global_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global global_config
    if global_config is None:
        global_config = Config()
    return global_config


def init_config(config_file: Optional[str] = None) -> Config:
    """初始化全局配置"""
    global global_config
    global_config = Config(config_file)
    return global_config
