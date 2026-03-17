#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程锁定模块 - 防止意外删除其他 py 程序
"""

import os
import sys
import json
import psutil
from pathlib import Path
from typing import List, Optional, Set


class ProcessLocker:
    """
    进程锁定器
    
    功能：
    - 锁定指定的 Python 进程
    - 防止锁定的进程被意外终止或删除
    - 提供进程状态监控
    """
    
    def __init__(self, lock_file: Optional[str] = None):
        """
        初始化进程锁定器
        
        Args:
            lock_file: 锁定文件路径，默认为 ~/.qwen_gui/process_lock.json
        """
        if lock_file:
            self.lock_file = Path(lock_file)
        else:
            self.lock_file = Path.home() / ".qwen_gui" / "process_lock.json"
        
        self._locked_pids: Set[int] = set()
        self._load()
    
    def _load(self) -> None:
        """加载锁定的进程列表"""
        try:
            if self.lock_file.exists():
                with open(self.lock_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._locked_pids = set(data.get('pids', []))
        except Exception as e:
            print(f"加载进程锁定文件失败：{e}")
            self._locked_pids = set()
    
    def _save(self) -> None:
        """保存锁定的进程列表"""
        try:
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.lock_file, 'w', encoding='utf-8') as f:
                json.dump({'pids': list(self._locked_pids)}, f, indent=2)
        except Exception as e:
            print(f"保存进程锁定文件失败：{e}")
    
    def lock_current_process(self) -> bool:
        """
        锁定当前进程
        
        Returns:
            是否成功锁定
        """
        current_pid = os.getpid()
        if current_pid not in self._locked_pids:
            self._locked_pids.add(current_pid)
            self._save()
            return True
        return False
    
    def unlock_current_process(self) -> bool:
        """
        解锁当前进程
        
        Returns:
            是否成功解锁
        """
        current_pid = os.getpid()
        if current_pid in self._locked_pids:
            self._locked_pids.discard(current_pid)
            self._save()
            return True
        return False
    
    def lock_process(self, pid: int) -> bool:
        """
        锁定指定进程
        
        Args:
            pid: 进程 ID
        
        Returns:
            是否成功锁定
        """
        if self._is_valid_pid(pid):
            self._locked_pids.add(pid)
            self._save()
            return True
        return False
    
    def unlock_process(self, pid: int) -> bool:
        """
        解锁指定进程
        
        Args:
            pid: 进程 ID
        
        Returns:
            是否成功解锁
        """
        if pid in self._locked_pids:
            self._locked_pids.discard(pid)
            self._save()
            return True
        return False
    
    def _is_valid_pid(self, pid: int) -> bool:
        """检查 PID 是否为有效的进程"""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
    
    def is_locked(self, pid: int) -> bool:
        """检查进程是否被锁定"""
        return pid in self._locked_pids
    
    def get_locked_processes(self) -> List[dict]:
        """
        获取所有锁定的进程信息

        Returns:
            进程信息列表
        """
        processes = []
        # 复制集合避免迭代时修改
        for pid in list(self._locked_pids):
            try:
                proc = psutil.Process(pid)
                processes.append({
                    'pid': pid,
                    'name': proc.name(),
                    'status': proc.status(),
                    'create_time': proc.create_time()
                })
            except psutil.NoSuchProcess:
                # 进程已不存在，从锁定列表中移除
                self.unlock_process(pid)
        return processes
    
    def cleanup_dead_processes(self) -> int:
        """
        清理已死亡的进程
        
        Returns:
            清理的进程数量
        """
        dead_pids = []
        for pid in self._locked_pids:
            if not self._is_valid_pid(pid):
                dead_pids.append(pid)
        
        for pid in dead_pids:
            self.unlock_process(pid)
        
        return len(dead_pids)
    
    def protect_file(self, file_path: str) -> None:
        """
        保护指定文件不被删除
        
        Args:
            file_path: 文件路径
        """
        # 在 Windows 上，可以通过设置文件属性来保护
        try:
            import ctypes
            FILE_ATTRIBUTE_READONLY = 0x00000001
            ctypes.windll.kernel32.SetFileAttributesW(file_path, FILE_ATTRIBUTE_READONLY)
        except Exception as e:
            print(f"保护文件失败：{e}")
    
    def unprotect_file(self, file_path: str) -> None:
        """
        解除文件保护
        
        Args:
            file_path: 文件路径
        """
        try:
            import ctypes
            FILE_ATTRIBUTE_NORMAL = 0x00000080
            ctypes.windll.kernel32.SetFileAttributesW(file_path, FILE_ATTRIBUTE_NORMAL)
        except Exception as e:
            print(f"解除文件保护失败：{e}")


# 全局进程锁定器实例
_locker: Optional[ProcessLocker] = None


def get_locker() -> ProcessLocker:
    """获取全局进程锁定器"""
    global _locker
    if _locker is None:
        _locker = ProcessLocker()
    return _locker


def init_locker(lock_file: Optional[str] = None) -> ProcessLocker:
    """初始化全局进程锁定器"""
    global _locker
    _locker = ProcessLocker(lock_file)
    return _locker


def lock_current() -> bool:
    """锁定当前进程"""
    return get_locker().lock_current_process()


def unlock_current() -> bool:
    """解锁当前进程"""
    return get_locker().unlock_current_process()
