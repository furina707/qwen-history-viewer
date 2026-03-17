#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""依赖测试脚本"""

import sys
sys.path.insert(0, '.')

def test_dependencies():
    """测试所有依赖"""
    print("=" * 50)
    print("依赖测试报告")
    print("=" * 50)
    
    # 1. 第三方依赖
    print("\n1. 第三方依赖:")
    try:
        import customtkinter
        print(f"   [OK] customtkinter == {customtkinter.__version__}")
    except ImportError as e:
        print(f"   [FAIL] customtkinter: {e}")
        return False
    
    try:
        import psutil
        print(f"   [OK] psutil == {psutil.__version__}")
    except ImportError as e:
        print(f"   [FAIL] psutil: {e}")
        return False
    
    # 2. 标准库
    print("\n2. Python 标准库:")
    std_libs = ['json', 'logging', 'subprocess', 'os', 'sys', 'datetime', 'pathlib', 'tkinter']
    for lib in std_libs:
        try:
            __import__(lib)
            print(f"   [OK] {lib}")
        except ImportError as e:
            print(f"   [FAIL] {lib}: {e}")
            return False
    
    # 3. 自定义模块
    print("\n3. 自定义模块:")
    try:
        from config import Config, get_config, init_config
        print("   [OK] config.py")
    except ImportError as e:
        print(f"   [FAIL] config.py: {e}")
        return False
    
    try:
        from logger import LogSystem, get_logger, init_logger
        print("   [OK] logger.py")
    except ImportError as e:
        print(f"   [FAIL] logger.py: {e}")
        return False
    
    try:
        from process_lock import ProcessLocker, get_locker, init_locker, lock_current
        print("   [OK] process_lock.py")
    except ImportError as e:
        print(f"   [FAIL] process_lock.py: {e}")
        return False
    
    # 4. 功能测试
    print("\n4. 功能测试:")
    try:
        config = Config()
        print(f"   [OK] 配置系统：{config.config_file}")
    except Exception as e:
        print(f"   [FAIL] 配置系统：{e}")
        return False
    
    try:
        logger = LogSystem()
        logger.info("测试日志消息")
        print(f"   [OK] 日志系统：{logger.log_dir}")
    except Exception as e:
        print(f"   [FAIL] 日志系统：{e}")
        return False
    
    try:
        locker = ProcessLocker()
        locker.lock_current_process()
        print(f"   [OK] 进程锁定：{locker.lock_file}")
        locker.unlock_current_process()
    except Exception as e:
        print(f"   [FAIL] 进程锁定：{e}")
        return False
    
    print("\n" + "=" * 50)
    print("所有测试通过!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = test_dependencies()
    sys.exit(0 if success else 1)
