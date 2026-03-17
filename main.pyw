#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen CLI 历史记录查看器 - Windows 无控制台启动入口
"""

import sys
from pathlib import Path

# 将当前目录添加到路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入并运行主程序
from main import main

if __name__ == "__main__":
    main()
