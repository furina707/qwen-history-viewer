#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen CLI 历史记录查看器 - 增强版
用于查看和管理 qwen-cli 的聊天历史记录
功能：搜索、统计、深色主题、复制、收藏、图表
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import webbrowser


class QwenHistoryViewer:
    """Qwen CLI 历史记录查看器 - 增强版"""
    
    # 深色主题配色
    DARK_THEME = {
        'bg': '#1e1e1e',
        'fg': '#d4d4d4',
        'frame_bg': '#252526',
        'label_bg': '#2d2d30',
        'text_bg': '#1e1e1e',
        'text_fg': '#d4d4d4',
        'select_bg': '#37373d',
        'button_bg': '#0e639c',
        'button_fg': '#ffffff',
        'user_color': '#569cd6',
        'assistant_color': '#6a9955',
        'system_color': '#808080',
        'highlight_color': '#f1c40f',
        'border_color': '#3e3e42'
    }
    
    # 浅色主题配色
    LIGHT_THEME = {
        'bg': '#f0f0f0',
        'fg': '#000000',
        'frame_bg': '#ffffff',
        'label_bg': '#e8e8e8',
        'text_bg': '#ffffff',
        'text_fg': '#000000',
        'select_bg': '#cce4ff',
        'button_bg': '#0078d7',
        'button_fg': '#ffffff',
        'user_color': '#0066cc',
        'assistant_color': '#008000',
        'system_color': '#808080',
        'highlight_color': '#ff6600',
        'border_color': '#d0d0d0'
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("Qwen CLI 历史记录查看器 - 增强版")
        self.root.geometry("1400x900")
        
        # 获取 qwen 配置目录
        self.qwen_dir = Path.home() / ".qwen"
        self.projects_dir = self.qwen_dir / "projects"
        self.favorites_file = self.qwen_dir / "favorites.json"
        
        # 数据存储
        self.sessions = {}  # session_id -> session_data
        self.current_session = None
        self.favorites = set()  # 收藏的会话 ID
        self.is_dark_theme = False  # 当前主题
        
        # 统计数据
        self.stats = {
            'total_sessions': 0,
            'total_messages': 0,
            'user_messages': 0,
            'assistant_messages': 0,
            'projects_count': 0
        }
        
        # 加载收藏
        self._load_favorites()
        
        # 创建界面
        self._create_ui()
        
        # 加载会话列表
        self._load_sessions()
    
    def _load_favorites(self):
        """加载收藏列表"""
        try:
            if self.favorites_file.exists():
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    self.favorites = set(json.load(f))
        except Exception as e:
            print(f"加载收藏失败：{e}")
            self.favorites = set()
    
    def _save_favorites(self):
        """保存收藏列表"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.favorites), f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存收藏失败：{e}")
    
    def _create_ui(self):
        """创建用户界面"""
        # 菜单栏
        self._create_menu()
        
        # 主容器
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 顶部工具栏
        self._create_toolbar(main_frame)
        
        # 搜索面板
        self._create_search_panel(main_frame)
        
        # 左侧面板 - 会话列表
        self._create_left_panel(main_frame)
        
        # 右侧面板 - 消息显示
        self._create_right_panel(main_frame)
        
        # 底部状态栏和统计
        self._create_status_bar(main_frame)
        
        # 应用默认主题
        self._apply_theme(self.LIGHT_THEME)
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="刷新会话列表", command=self._load_sessions, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="打开 qwen CLI", command=self._open_qwen_cli, accelerator="Ctrl+O")
        file_menu.add_command(label="导出当前会话", command=self._export_session, accelerator="Ctrl+E")
        file_menu.add_command(label="导出所有会话", command=self._export_all_sessions)
        file_menu.add_separator()
        file_menu.add_command(label="删除当前项目", command=self._delete_project, accelerator="Ctrl+Delete")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit, accelerator="Alt+F4")
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="复制选中消息", command=self._copy_message, accelerator="Ctrl+C")
        edit_menu.add_command(label="复制会话 ID", command=self._copy_session_id)
        edit_menu.add_separator()
        edit_menu.add_command(label="查找", command=self._focus_search, accelerator="Ctrl+F")
        
        # 收藏菜单
        fav_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="收藏", menu=fav_menu)
        fav_menu.add_command(label="添加/移除收藏", command=self._toggle_favorite, accelerator="Ctrl+D")
        fav_menu.add_command(label="仅显示收藏", command=self._toggle_show_favorites)
        fav_menu.add_separator()
        fav_menu.add_command(label="管理收藏", command=self._manage_favorites)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="切换深色主题", command=self._toggle_theme, accelerator="Ctrl+T")
        view_menu.add_command(label="显示统计面板", command=self._toggle_stats)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
        
        # 键盘快捷键绑定
        self.root.bind('<F5>', lambda e: self._load_sessions())
        self.root.bind('<Control-e>', lambda e: self._export_session())
        self.root.bind('<Control-f>', lambda e: self._focus_search())
        self.root.bind('<Control-d>', lambda e: self._toggle_favorite())
        self.root.bind('<Control-t>', lambda e: self._toggle_theme())
        self.root.bind('<Control-c>', lambda e: self._copy_message())
        self.root.bind('<Control-Delete>', lambda e: self._delete_project())
        self.root.bind('<Control-o>', lambda e: self._open_qwen_cli())
    
    def _create_toolbar(self, parent):
        """创建顶部工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        # 项目选择
        ttk.Label(toolbar, text="项目:").pack(side=tk.LEFT, padx=(0, 5))
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(
            toolbar, 
            textvariable=self.project_var,
            state="readonly",
            width=30
        )
        self.project_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.project_combo.bind("<<ComboboxSelected>>", self._on_project_selected)
        
        # 分隔线
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 筛选选项
        ttk.Label(toolbar, text="筛选:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=["全部", "今天", "本周", "本月", "收藏"],
            state="readonly",
            width=10
        )
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        filter_combo.bind("<<ComboboxSelected>>", self._apply_filter)
        
        # 工具按钮
        self.refresh_btn = ttk.Button(toolbar, text="🔄 刷新", command=self._load_sessions)
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.theme_btn = ttk.Button(toolbar, text="🌙 深色", command=self._toggle_theme)
        self.theme_btn.pack(side=tk.LEFT)

        # 打开 CLI 按钮
        self.open_cli_btn = ttk.Button(
            toolbar,
            text="💬 打开 CLI",
            command=self._open_qwen_cli
        )
        self.open_cli_btn.pack(side=tk.LEFT, padx=(10, 5))
        self.open_cli_btn.config(state=tk.DISABLED)

        # 删除项目按钮
        self.delete_project_btn = ttk.Button(
            toolbar,
            text="🗑️ 删除项目",
            command=self._delete_project
        )
        self.delete_project_btn.pack(side=tk.LEFT, padx=(10, 5))
        self.delete_project_btn.config(state=tk.DISABLED)
        
        # 统计信息快速查看
        self.quick_stats_label = ttk.Label(toolbar, text="", foreground="gray")
        self.quick_stats_label.pack(side=tk.RIGHT, padx=10)
    
    def _create_search_panel(self, parent):
        """创建搜索面板"""
        search_frame = ttk.LabelFrame(parent, text="搜索", padding="5")
        search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        # 搜索框
        ttk.Label(search_frame, text="关键词:").grid(row=0, column=0, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        self.search_entry.grid(row=0, column=1, padx=(0, 10))
        self.search_entry.bind('<Return>', self._do_search)
        
        # 搜索范围
        ttk.Label(search_frame, text="范围:").grid(row=0, column=2, padx=(0, 5))
        self.search_scope_var = tk.StringVar(value="当前会话")
        scope_combo = ttk.Combobox(
            search_frame,
            textvariable=self.search_scope_var,
            values=["当前会话", "当前项目", "全部项目"],
            state="readonly",
            width=12
        )
        scope_combo.grid(row=0, column=3, padx=(0, 10))
        
        # 搜索按钮
        search_btn = ttk.Button(search_frame, text="🔍 搜索", command=self._do_search)
        search_btn.grid(row=0, column=4, padx=(0, 5))
        
        clear_btn = ttk.Button(search_frame, text="清空", command=self._clear_search)
        clear_btn.grid(row=0, column=5)
        
        # 搜索结果显示
        self.search_result_label = ttk.Label(search_frame, text="", foreground="green")
        self.search_result_label.grid(row=1, column=0, columnspan=6, sticky="w", pady=(5, 0))
    
    def _create_left_panel(self, parent):
        """创建左侧面板"""
        left_frame = ttk.LabelFrame(parent, text="会话列表", padding="5")
        left_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(2, weight=1)
        
        # 会话列表框
        list_frame = ttk.Frame(left_frame)
        list_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.session_listbox = tk.Listbox(
            list_frame,
            width=50,
            height=25,
            selectmode=tk.BROWSE,
            font=("Consolas", 9)
        )
        self.session_listbox.grid(row=0, column=0, sticky="nsew")
        self.session_listbox.bind("<<ListboxSelect>>", self._on_session_selected)
        self.session_listbox.bind("<Double-Button-1>", self._on_session_double_click)
        
        # 滚动条
        list_scrollbar = ttk.Scrollbar(
            list_frame, 
            orient=tk.VERTICAL, 
            command=self.session_listbox.yview
        )
        list_scrollbar.grid(row=0, column=1, sticky="ns")
        self.session_listbox.config(yscrollcommand=list_scrollbar.set)
        
        # 操作按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        self.favorite_btn = ttk.Button(
            btn_frame,
            text="⭐ 收藏",
            command=self._toggle_favorite
        )
        self.favorite_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_btn = ttk.Button(
            btn_frame,
            text="🗑️ 删除",
            command=self._delete_session
        )
        self.delete_btn.pack(side=tk.LEFT)
        
        # 统计面板
        self._create_stats_panel(left_frame)
    
    def _create_stats_panel(self, parent):
        """创建统计面板"""
        stats_frame = ttk.LabelFrame(parent, text="📊 统计信息", padding="5")
        stats_frame.grid(row=3, column=0, sticky="ew", pady=(5, 0))
        
        # 统计网格
        self.stats_labels = {}
        stats_data = [
            ("总会话数", "total_sessions"),
            ("总消息数", "total_messages"),
            ("用户消息", "user_messages"),
            ("助手消息", "assistant_messages"),
            ("项目数", "projects_count"),
            ("收藏数", "favorites_count")
        ]
        
        for i, (label, key) in enumerate(stats_data):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(stats_frame, text=f"{label}:").grid(row=row, column=col, sticky="w", padx=(0, 5))
            lbl = ttk.Label(stats_frame, text="0", foreground="blue")
            lbl.grid(row=row, column=col+1, sticky="w")
            self.stats_labels[key] = lbl
    
    def _create_right_panel(self, parent):
        """创建右侧面板"""
        right_frame = ttk.LabelFrame(parent, text="对话内容", padding="5")
        right_frame.grid(row=2, column=1, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # 会话信息栏
        info_frame = ttk.Frame(right_frame)
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.info_label = ttk.Label(info_frame, text="", font=("Consolas", 9))
        self.info_label.pack(side=tk.LEFT)
        
        self.favorite_indicator = ttk.Label(info_frame, text="", foreground="gold", font=("Arial", 12))
        self.favorite_indicator.pack(side=tk.RIGHT)
        
        # 消息显示区域
        self.message_text = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            state=tk.DISABLED
        )
        self.message_text.grid(row=1, column=0, sticky="nsew")
        
        # 配置文本标签
        self._configure_text_tags()
        
        # 右键菜单
        self._create_context_menu()
        
        # 底部按钮
        btn_frame = ttk.Frame(right_frame)
        btn_frame.grid(row=2, column=0, sticky="e", pady=(5, 0))
        
        self.copy_btn = ttk.Button(
            btn_frame,
            text="📋 复制消息",
            command=self._copy_message
        )
        self.copy_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.export_btn = ttk.Button(
            btn_frame,
            text="📤 导出",
            command=self._export_session
        )
        self.export_btn.grid(row=0, column=1, padx=(0, 5))
        
        self.stats_detail_btn = ttk.Button(
            btn_frame,
            text="📈 详细统计",
            command=self._show_detailed_stats
        )
        self.stats_detail_btn.grid(row=0, column=2)
    
    def _configure_text_tags(self):
        """配置文本标签样式"""
        theme = self.DARK_THEME if self.is_dark_theme else self.LIGHT_THEME
        
        self.message_text.tag_configure("user", foreground=theme['user_color'], font=("Consolas", 10, "bold"))
        self.message_text.tag_configure("assistant", foreground=theme['assistant_color'], font=("Consolas", 10, "bold"))
        self.message_text.tag_configure("system", foreground=theme['system_color'], font=("Consolas", 10, "italic"))
        self.message_text.tag_configure("timestamp", foreground=theme['system_color'], font=("Consolas", 8))
        self.message_text.tag_configure("highlight", background=theme['highlight_color'], foreground="#000000")
    
    def _create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="复制此消息", command=self._copy_message)
        self.context_menu.add_command(label="复制会话 ID", command=self._copy_session_id)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="添加/移除收藏", command=self._toggle_favorite)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="导出此会话", command=self._export_session)
        
        # 绑定右键事件
        self.message_text.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def _create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            status_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 进度指示
        self.progress_label = ttk.Label(status_frame, text="")
        self.progress_label.pack(side=tk.RIGHT, padx=10)
    
    def _apply_theme(self, theme):
        """应用主题"""
        self.root.configure(bg=theme['bg'])
        
        # 更新文本标签配置
        if hasattr(self, 'message_text'):
            self._configure_text_tags()
    
    def _toggle_theme(self):
        """切换主题"""
        self.is_dark_theme = not self.is_dark_theme
        theme = self.DARK_THEME if self.is_dark_theme else self.LIGHT_THEME
        self._apply_theme(theme)
        
        # 更新按钮文本
        self.theme_btn.config(text="☀️ 浅色" if self.is_dark_theme else "🌙 深色")
        
        self.status_var.set(f"已切换到{'深色' if self.is_dark_theme else '浅色'}主题")
    
    def _load_sessions(self):
        """加载所有会话"""
        self.status_var.set("正在加载会话列表...")
        self.root.update()
        
        # 清空现有数据
        self.project_combo.set("")
        self.session_listbox.delete(0, tk.END)
        self.sessions.clear()
        self.stats = {
            'total_sessions': 0,
            'total_messages': 0,
            'user_messages': 0,
            'assistant_messages': 0,
            'projects_count': 0
        }
        
        if not self.projects_dir.exists():
            messagebox.showerror("错误", f"找不到 qwen 配置目录：{self.qwen_dir}")
            self.status_var.set("错误：找不到配置目录")
            return
        
        # 获取所有项目目录
        projects = []
        project_cwd_map = {}  # 编码名 -> 原始 cwd 路径
        
        for item in self.projects_dir.iterdir():
            if item.is_dir():
                encoded_name = item.name
                # 尝试从会话文件中读取原始的 cwd 路径
                cwd_path = None
                chats_dir = item / "chats"
                if chats_dir.exists():
                    session_files = list(chats_dir.glob("*.jsonl"))
                    if session_files:
                        try:
                            with open(session_files[0], 'r', encoding='utf-8') as f:
                                first_line = f.readline()
                                if first_line:
                                    data = json.loads(first_line)
                                    cwd_path = data.get('cwd', None)
                        except Exception:
                            pass
                
                # 如果没有找到 cwd，使用解码后的路径
                if cwd_path:
                    project_name = cwd_path
                else:
                    # 解码项目名称（注意顺序：先替换 c- 为 C:，再替换 -- 为 /）
                    project_name = encoded_name.replace("c-", "C:").replace("--", "/").replace("_user_", "_")
                
                projects.append((project_name, item))
                project_cwd_map[project_name] = cwd_path
                self.stats['projects_count'] += 1

        if not projects:
            self.status_var.set("未找到任何项目")
            self._update_stats_display()
            return

        # 填充项目下拉框（显示友好路径）
        friendly_names = []
        for name, _ in projects:
            # 将路径转换为更友好的显示格式
            friendly_name = name.replace("\\", "/")
            friendly_names.append(friendly_name)

        self.project_combo["values"] = friendly_names
        self.stats['total_projects'] = len(projects)

        self.status_var.set(f"找到 {len(projects)} 个项目")
        self._update_stats_display()

    def _find_project_dir(self, project_name):
        """根据项目名称查找实际的项目目录"""
        # 尝试从会话文件中查找匹配的 cwd
        for item in self.projects_dir.iterdir():
            if item.is_dir():
                chats_dir = item / "chats"
                if chats_dir.exists():
                    session_files = list(chats_dir.glob("*.jsonl"))
                    if session_files:
                        try:
                            with open(session_files[0], 'r', encoding='utf-8') as f:
                                first_line = f.readline()
                                if first_line:
                                    data = json.loads(first_line)
                                    cwd = data.get('cwd', '')
                                    if cwd and (cwd == project_name or cwd.replace("\\", "/") == project_name):
                                        return item
                        except Exception:
                            continue
        
        # 如果没有找到，使用编码方式
        encoded_name = project_name.replace("C:", "c-").replace("/", "--").replace("_", "_user_")
        return self.projects_dir / encoded_name

    def _on_project_selected(self, event):
        """当选择项目时加载会话"""
        project_name = self.project_var.get()
        if not project_name:
            self.delete_project_btn.config(state=tk.DISABLED)
            self.open_cli_btn.config(state=tk.DISABLED)
            return

        # 启用按钮
        self.delete_project_btn.config(state=tk.NORMAL)
        self.open_cli_btn.config(state=tk.NORMAL)

        # 查找项目目录
        project_dir = self._find_project_dir(project_name)
        chats_dir = project_dir / "chats"
        
        # 清空会话列表
        self.session_listbox.delete(0, tk.END)
        self.sessions.clear()
        self.current_session = None
        self._clear_message_display()
        
        if not chats_dir.exists():
            self.status_var.set(f"项目 '{project_name}' 没有聊天记录")
            return
        
        # 加载所有聊天会话
        session_files = list(chats_dir.glob("*.jsonl"))
        session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 应用筛选
        filtered_sessions = self._filter_sessions(session_files)
        
        for session_file in filtered_sessions:
            self._add_session_to_list(session_file)
        
        # 更新统计
        self.stats['total_sessions'] = len(self.sessions)
        self._update_stats_display()
        
        filter_text = f" ({self.filter_var.get()})" if self.filter_var.get() != "全部" else ""
        self.status_var.set(f"项目 '{project_name}'{filter_text} - 找到 {len(self.sessions)} 个会话")
    
    def _filter_sessions(self, session_files):
        """筛选会话"""
        filter_type = self.filter_var.get()
        now = datetime.now()
        
        if filter_type == "全部":
            return session_files
        elif filter_type == "收藏":
            return [f for f in session_files if f.stem in self.favorites]
        
        filtered = []
        for f in session_files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    first_line = file.readline()
                    if first_line:
                        data = json.loads(first_line)
                        timestamp = data.get('timestamp', '')
                        session_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        
                        if filter_type == "今天":
                            if session_time.date() == now.date():
                                filtered.append(f)
                        elif filter_type == "本周":
                            days_diff = (now - session_time.replace(tzinfo=None)).days
                            if days_diff <= 7:
                                filtered.append(f)
                        elif filter_type == "本月":
                            if session_time.month == now.month and session_time.year == now.year:
                                filtered.append(f)
            except Exception:
                continue
        
        return filtered
    
    def _apply_filter(self, event=None):
        """应用筛选"""
        self._on_project_selected(None)
    
    def _add_session_to_list(self, session_file):
        """添加会话到列表"""
        session_id = session_file.stem
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if first_line:
                    data = json.loads(first_line)
                    timestamp = data.get('timestamp', 'Unknown')
                    message = data.get('message', {})
                    parts = message.get('parts', [])
                    content = ""
                    for part in parts:
                        if part.get('type') == 'text':
                            content = part.get('text', '')
                            break
                    
                    # 统计消息数
                    f.seek(0)
                    msg_count = sum(1 for _ in f)
                    self.stats['total_messages'] += msg_count
                    
                    # 截断过长的内容
                    if len(content) > 50:
                        content = content[:50] + "..."
                    
                    # 收藏标记
                    fav_mark = "⭐ " if session_id in self.favorites else ""
                    
                    # 格式化显示
                    display_text = f"{fav_mark}{timestamp[:19]} - {content}"
                    self.session_listbox.insert(tk.END, display_text)
                    self.sessions[session_id] = {
                        'file': session_file,
                        'timestamp': timestamp,
                        'preview': content,
                        'msg_count': msg_count
                    }
        except Exception as e:
            print(f"读取会话 {session_id} 失败：{e}")
    
    def _on_session_selected(self, event):
        """当选择会话时显示内容"""
        selection = self.session_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        session_id = list(self.sessions.keys())[index]
        self.current_session = session_id
        
        # 显示消息
        self._display_session(session_id)
        self.export_btn.config(state=tk.NORMAL)
        
        # 更新收藏标记
        is_fav = session_id in self.favorites
        self.favorite_indicator.config(text="⭐" if is_fav else "")
        self.favorite_btn.config(text="⭐ 已收藏" if is_fav else "☆ 收藏")
    
    def _on_session_double_click(self, event):
        """双击会话导出"""
        self._export_session()
    
    def _display_session(self, session_id):
        """显示会话内容"""
        session_data = self.sessions[session_id]
        session_file = session_data['file']
        
        self._clear_message_display()
        self.message_text.config(state=tk.NORMAL)
        
        # 显示会话信息
        self.info_label.config(text=f"会话 ID: {session_id} | 消息数：{session_data['msg_count']}")
        
        # 统计当前会话
        session_stats = {'user': 0, 'assistant': 0, 'system': 0}
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        self._display_message(data)
                        msg_type = data.get('type', 'unknown')
                        if msg_type in session_stats:
                            session_stats[msg_type] += 1
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.message_text.insert(tk.END, f"读取会话失败：{e}\n")
        
        self.message_text.config(state=tk.DISABLED)
        self.status_var.set(f"已加载会话：{session_id} | 用户：{session_stats['user']} | 助手：{session_stats['assistant']}")
    
    def _display_message(self, data):
        """显示单条消息"""
        self.message_text.insert(tk.END, "\n")
        
        # 时间戳
        timestamp = data.get('timestamp', 'Unknown')
        msg_type = data.get('type', 'unknown')
        
        # 角色映射
        type_map = {
            'user': ('👤 用户', 'user'),
            'assistant': ('🤖 助手', 'assistant'),
            'system': ('⚙️ 系统', 'system')
        }
        
        role_text, tag = type_map.get(msg_type, (msg_type, 'system'))
        
        # 显示角色和时间
        self.message_text.insert(tk.END, f"[{timestamp[:19]}] {role_text}\n", tag)
        
        # 显示消息内容
        message = data.get('message', {})
        parts = message.get('parts', [])
        
        for part in parts:
            part_type = part.get('type', 'text')
            if part_type == 'text':
                content = part.get('text', '')
                self.message_text.insert(tk.END, f"{content}\n")
            elif part_type == 'tool-result':
                tool_name = part.get('toolName', 'unknown')
                result = part.get('result', 'No result')
                self.message_text.insert(tk.END, f"🔧 工具 '{tool_name}' 结果:\n{result}\n", 'system')
            elif part_type == 'tool-call':
                tool_name = part.get('toolName', 'unknown')
                args = part.get('args', {})
                self.message_text.insert(tk.END, f"🔧 调用工具 '{tool_name}'\n", 'system')
        
        # 分隔线
        self.message_text.insert(tk.END, "-" * 80 + "\n", 'timestamp')
    
    def _clear_message_display(self):
        """清空消息显示"""
        self.message_text.config(state=tk.NORMAL)
        self.message_text.delete(1.0, tk.END)
        self.message_text.config(state=tk.DISABLED)
        self.info_label.config(text="")
        self.favorite_indicator.config(text="")
    
    def _update_stats_display(self):
        """更新统计显示"""
        stats_map = {
            'total_sessions': str(self.stats.get('total_sessions', 0)),
            'total_messages': str(self.stats.get('total_messages', 0)),
            'user_messages': str(self.stats.get('user_messages', 0)),
            'assistant_messages': str(self.stats.get('assistant_messages', 0)),
            'projects_count': str(self.stats.get('projects_count', 0)),
            'favorites_count': str(len(self.favorites))
        }
        
        for key, value in stats_map.items():
            if key in self.stats_labels:
                self.stats_labels[key].config(text=value)
        
        # 快速统计
        self.quick_stats_label.config(
            text=f"会话：{self.stats.get('total_sessions', 0)} | 消息：{self.stats.get('total_messages', 0)}"
        )
    
    def _do_search(self, event=None):
        """执行搜索"""
        keyword = self.search_var.get().strip()
        if not keyword:
            self._clear_search()
            return
        
        scope = self.search_scope_var.get()
        results = []
        result_count = 0
        
        if scope == "当前会话" and self.current_session:
            # 在当前会话中搜索
            session_file = self.sessions[self.current_session]['file']
            results = self._search_in_file(session_file, keyword)
            result_count = len(results)
        else:
            # 在多个会话中搜索
            if scope == "当前项目":
                files_to_search = [s['file'] for s in self.sessions.values()]
            else:  # 全部项目
                files_to_search = []
                for project_dir in self.projects_dir.iterdir():
                    if project_dir.is_dir():
                        chats_dir = project_dir / "chats"
                        if chats_dir.exists():
                            files_to_search.extend(chats_dir.glob("*.jsonl"))
            
            for file in files_to_search:
                file_results = self._search_in_file(file, keyword)
                results.extend(file_results)
            result_count = len(results)
        
        if results:
            self.search_result_label.config(text=f"找到 {result_count} 条匹配结果")
            # 高亮显示第一个结果
            if self.current_session and results:
                self._highlight_search(keyword)
        else:
            self.search_result_label.config(text="未找到匹配结果")
        
        self.status_var.set(f"搜索完成：{keyword}")
    
    def _search_in_file(self, file_path, keyword):
        """在文件中搜索关键词"""
        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if keyword.lower() in line.lower():
                        results.append(line)
        except Exception:
            pass
        return results
    
    def _highlight_search(self, keyword):
        """高亮显示搜索结果"""
        self.message_text.tag_remove("highlight", "1.0", tk.END)
        
        start_pos = "1.0"
        while True:
            pos = self.message_text.search(keyword, start_pos, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end_pos = f"{pos}+{len(keyword)}c"
            self.message_text.tag_add("highlight", pos, end_pos)
            start_pos = end_pos
    
    def _clear_search(self):
        """清空搜索"""
        self.search_var.set("")
        self.search_result_label.config(text="")
        self.message_text.tag_remove("highlight", "1.0", tk.END)
    
    def _focus_search(self):
        """聚焦搜索框"""
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)
    
    def _toggle_favorite(self):
        """切换收藏状态"""
        if not self.current_session:
            messagebox.showwarning("警告", "请先选择一个会话")
            return
        
        session_id = self.current_session
        if session_id in self.favorites:
            self.favorites.remove(session_id)
            self.status_var.set(f"已移除收藏：{session_id}")
        else:
            self.favorites.add(session_id)
            self.status_var.set(f"已添加收藏：{session_id}")
        
        self._save_favorites()
        
        # 刷新列表显示
        self._on_project_selected(None)
    
    def _toggle_show_favorites(self):
        """切换仅显示收藏"""
        self.filter_var.set("收藏")
        self._apply_filter()
    
    def _manage_favorites(self):
        """管理收藏"""
        if not self.favorites:
            messagebox.showinfo("收藏管理", "暂无收藏的会话")
            return
        
        # 创建管理窗口
        fav_window = tk.Toplevel(self.root)
        fav_window.title("收藏管理")
        fav_window.geometry("600x400")
        
        frame = ttk.Frame(fav_window, padding="10")
        frame.grid(row=0, column=0, sticky="nsew")
        
        ttk.Label(frame, text="已收藏的会话:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
        
        listbox = tk.Listbox(frame, width=70, height=15)
        listbox.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        
        for session_id in self.favorites:
            listbox.insert(tk.END, f"{session_id}")
        
        def remove_selected():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                session_id = list(listbox.get(0, tk.END))[index]
                self.favorites.discard(session_id)
                self._save_favorites()
                listbox.delete(index)
                self._update_stats_display()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, sticky="e", pady=(10, 0))
        
        ttk.Button(btn_frame, text="移除选中", command=remove_selected).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(btn_frame, text="关闭", command=fav_window.destroy).grid(row=0, column=1)
    
    def _copy_message(self):
        """复制选中的消息"""
        try:
            selected = self.message_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
            self.status_var.set("已复制选中的消息")
        except tk.TclError:
            # 没有选中内容，复制全部内容
            if self.current_session:
                all_text = self.message_text.get("1.0", tk.END)
                self.root.clipboard_clear()
                self.root.clipboard_append(all_text)
                self.status_var.set("已复制全部消息")
    
    def _copy_session_id(self):
        """复制会话 ID"""
        if not self.current_session:
            messagebox.showwarning("警告", "请先选择一个会话")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_session)
        self.status_var.set(f"已复制会话 ID: {self.current_session}")
    
    def _delete_session(self):
        """删除选中的会话"""
        selection = self.session_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个会话")
            return

        if not messagebox.askyesno("确认", "确定要删除选中的会话吗？\n此操作不可恢复！"):
            return

        index = selection[0]
        session_id = list(self.sessions.keys())[index]
        session_file = self.sessions[session_id]['file']

        try:
            session_file.unlink()
            self.favorites.discard(session_id)
            self._save_favorites()
            del self.sessions[session_id]
            self.session_listbox.delete(index)
            self._clear_message_display()
            self.export_btn.config(state=tk.DISABLED)
            self.stats['total_sessions'] -= 1
            self._update_stats_display()
            self.status_var.set(f"已删除会话：{session_id}")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败：{e}")

    def _delete_project(self):
        """删除当前项目"""
        project_name = self.project_var.get()
        if not project_name:
            messagebox.showwarning("警告", "请先选择一个项目")
            return

        # 查找项目目录
        project_dir = self._find_project_dir(project_name)

        if not project_dir.exists():
            messagebox.showerror("错误", f"项目目录不存在：{project_dir}")
            return

        # 统计项目中的会话数量
        chats_dir = project_dir / "chats"
        session_count = 0
        if chats_dir.exists():
            session_count = len(list(chats_dir.glob("*.jsonl")))

        # 获取编码后的目录名用于显示
        encoded_name = project_dir.name

        # 确认对话框
        confirm_msg = f"""确定要删除项目 "{project_name}" 吗？

此操作将删除：
• 项目目录：{encoded_name}
• 会话文件：{session_count} 个
• 所有聊天记录和上下文

⚠️ 此操作不可恢复！"""

        if not messagebox.askyesno("确认删除项目", confirm_msg, icon='warning'):
            return

        # 二次确认
        if not messagebox.askyesno("最终确认", "这是最后确认！\n\n删除后所有聊天记录将永久丢失！\n\n确定要继续吗？", icon='warning'):
            return

        try:
            import shutil
            # 删除项目目录
            shutil.rmtree(project_dir)

            # 清理收藏中属于该项目的会话
            if chats_dir.exists():
                for session_file in chats_dir.glob("*.jsonl"):
                    self.favorites.discard(session_file.stem)
            self._save_favorites()

            # 从下拉框中移除已删除的项目
            current_values = list(self.project_combo["values"])
            if project_name in current_values:
                current_values.remove(project_name)
            self.project_combo["values"] = current_values
            self.project_combo.set("")

            # 清空界面
            self.session_listbox.delete(0, tk.END)
            self.sessions.clear()
            self.current_session = None
            self._clear_message_display()
            self.export_btn.config(state=tk.DISABLED)
            self.delete_project_btn.config(state=tk.DISABLED)
            self.open_cli_btn.config(state=tk.DISABLED)

            # 更新统计
            self.stats['projects_count'] = len(current_values)
            self.stats['total_sessions'] = 0
            self._update_stats_display()

            self.status_var.set(f"已删除项目：{project_name}")
            messagebox.showinfo("成功", f"项目 '{project_name}' 已成功删除！")
        except Exception as e:
            messagebox.showerror("错误", f"删除项目失败：{e}")

    def _open_qwen_cli(self):
        """打开当前项目的 qwen CLI，并加载历史上下文"""
        project_name = self.project_var.get()
        if not project_name:
            messagebox.showwarning("警告", "请先选择一个项目")
            return

        try:
            import subprocess
            # 查找项目目录
            project_dir = self._find_project_dir(project_name)

            if not project_dir.exists():
                messagebox.showerror("错误", f"项目目录不存在：{project_dir}")
                return

            # 构建 qwen 命令参数
            # 如果有选中的会话，使用 --resume 加载该会话
            # 否则使用 --continue 加载最近的会话
            if self.current_session and self.current_session in self.sessions:
                # 使用选中的会话 ID
                context_arg = f'-r {self.current_session}'
                tip = f'已选择会话：{self.current_session[:8]}...'
            else:
                # 默认使用 --continue 加载最近的会话
                context_arg = '-c'
                tip = '正在加载最近的会话'

            # qwen CLI 基于当前工作目录来查找会话
            # 需要在项目对应的实际工作目录下运行 qwen
            # 使用 project_name 作为工作目录（它是原始的 cwd 路径）
            work_dir = project_name if self.current_session else Path.home() / "Desktop"

            # 使用 cmd.exe 新建窗口
            cmd_command = f'cmd.exe /k "cd /d {work_dir} && qwen {context_arg}"'
            subprocess.Popen(cmd_command)

            self.status_var.set(f"已打开项目 '{project_name}' 的 qwen CLI ({tip})")
        except Exception as e:
            messagebox.showerror("错误", f"打开 qwen CLI 失败：{e}")

    def _export_session(self):
        """导出当前会话"""
        if not self.current_session:
            return
        
        session_data = self.sessions[self.current_session]
        session_file = session_data['file']
        
        # 选择保存位置
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=f"qwen_chat_{self.current_session[:8]}.txt"
        )
        
        if not file_path:
            return
        
        try:
            with open(session_file, 'r', encoding='utf-8') as src:
                with open(file_path, 'w', encoding='utf-8') as dst:
                    dst.write(f"Qwen CLI 聊天记录导出\n")
                    dst.write(f"会话 ID: {self.current_session}\n")
                    dst.write(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    dst.write("=" * 80 + "\n\n")
                    
                    for line in src:
                        try:
                            data = json.loads(line.strip())
                            timestamp = data.get('timestamp', 'Unknown')
                            msg_type = data.get('type', 'unknown')
                            message = data.get('message', {})
                            parts = message.get('parts', [])
                            
                            role_map = {'user': '用户', 'assistant': '助手', 'system': '系统'}
                            role = role_map.get(msg_type, msg_type)
                            
                            dst.write(f"[{timestamp[:19]}] {role}:\n")
                            
                            for part in parts:
                                if part.get('type') == 'text':
                                    dst.write(f"{part.get('text', '')}\n")
                            
                            dst.write("\n" + "-" * 80 + "\n\n")
                        except json.JSONDecodeError:
                            continue
            
            self.status_var.set(f"已导出到：{file_path}")
            messagebox.showinfo("成功", f"会话已导出到:\n{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{e}")
    
    def _export_all_sessions(self):
        """导出所有会话"""
        if not self.sessions:
            messagebox.showwarning("警告", "没有可导出的会话")
            return
        
        dir_path = filedialog.askdirectory(title="选择导出目录")
        if not dir_path:
            return
        
        count = 0
        for session_id, session_data in self.sessions.items():
            try:
                session_file = session_data['file']
                output_path = Path(dir_path) / f"qwen_chat_{session_id[:8]}.txt"
                
                with open(session_file, 'r', encoding='utf-8') as src:
                    with open(output_path, 'w', encoding='utf-8') as dst:
                        dst.write(f"Qwen CLI 聊天记录导出\n")
                        dst.write(f"会话 ID: {session_id}\n")
                        dst.write(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        dst.write("=" * 80 + "\n\n")
                        
                        for line in src:
                            try:
                                data = json.loads(line.strip())
                                timestamp = data.get('timestamp', 'Unknown')
                                msg_type = data.get('type', 'unknown')
                                message = data.get('message', {})
                                parts = message.get('parts', [])
                                
                                role_map = {'user': '用户', 'assistant': '助手', 'system': '系统'}
                                role = role_map.get(msg_type, msg_type)
                                
                                dst.write(f"[{timestamp[:19]}] {role}:\n")
                                
                                for part in parts:
                                    if part.get('type') == 'text':
                                        dst.write(f"{part.get('text', '')}\n")
                                
                                dst.write("\n" + "-" * 80 + "\n\n")
                            except json.JSONDecodeError:
                                continue
                count += 1
            except Exception as e:
                print(f"导出 {session_id} 失败：{e}")
        
        messagebox.showinfo("完成", f"已导出 {count}/{len(self.sessions)} 个会话到:\n{dir_path}")
    
    def _show_detailed_stats(self):
        """显示详细统计"""
        if not self.current_session:
            messagebox.showwarning("警告", "请先选择一个会话")
            return
        
        session_data = self.sessions[self.current_session]
        session_file = session_data['file']
        
        # 统计详细信息
        stats = {
            'total': 0,
            'user': 0,
            'assistant': 0,
            'system': 0,
            'tool_calls': 0,
            'tool_results': 0,
            'total_chars': 0
        }
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        stats['total'] += 1
                        msg_type = data.get('type', 'unknown')
                        if msg_type in stats:
                            stats[msg_type] += 1
                        
                        message = data.get('message', {})
                        parts = message.get('parts', [])
                        for part in parts:
                            if part.get('type') == 'text':
                                stats['total_chars'] += len(part.get('text', ''))
                            elif part.get('type') == 'tool-call':
                                stats['tool_calls'] += 1
                            elif part.get('type') == 'tool-result':
                                stats['tool_results'] += 1
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            messagebox.showerror("错误", f"统计失败：{e}")
            return
        
        # 创建统计窗口
        stats_window = tk.Toplevel(self.root)
        stats_window.title(f"会话统计 - {self.current_session[:8]}")
        stats_window.geometry("400x350")
        
        frame = ttk.Frame(stats_window, padding="20")
        frame.grid(row=0, column=0, sticky="nsew")
        
        title = ttk.Label(frame, text="📊 会话详细统计", font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, pady=(0, 20))
        
        details = [
            ("总会话数", stats['total']),
            ("用户消息", stats['user']),
            ("助手消息", stats['assistant']),
            ("系统消息", stats['system']),
            ("工具调用", stats['tool_calls']),
            ("工具结果", stats['tool_results']),
            ("总字符数", f"{stats['total_chars']:,}")
        ]
        
        for i, (label, value) in enumerate(details):
            ttk.Label(frame, text=f"{label}:").grid(row=i+1, column=0, sticky="w", pady=5)
            ttk.Label(frame, text=str(value), font=("Consolas", 10)).grid(row=i+1, column=1, sticky="w", padx=20, pady=5)
        
        ttk.Button(frame, text="关闭", command=stats_window.destroy).grid(row=len(details)+2, column=0, columnspan=2, pady=20)
    
    def _toggle_stats(self):
        """切换统计面板显示"""
        # 简单实现：刷新显示
        self._update_stats_display()
        self.status_var.set("统计信息已更新")
    
    def _show_help(self):
        """显示帮助"""
        help_text = """
Qwen CLI 历史记录查看器 - 使用说明

📋 基本功能:
• 选择项目后查看历史会话
• 点击会话查看对话内容
• 双击会话快速导出

🔍 搜索功能:
• 输入关键词后按回车搜索
• 可选择搜索范围：当前会话/当前项目/全部项目

⭐ 收藏功能:
• 选中会话后点击收藏按钮
• 使用筛选器快速查看收藏

📤 导出功能:
• 点击导出按钮保存当前会话
• 文件菜单可导出所有会话

🗑️ 删除功能:
• 删除会话：选中会话后点击删除按钮
• 删除项目：选择项目后点击"删除项目"按钮
• 快捷键：Ctrl+Delete 删除当前项目
• ⚠️ 删除项目需要二次确认，请谨慎操作！

💬 打开 CLI:
• 选择项目后点击"打开 CLI"按钮
• 或快捷键 Ctrl+O
• 会在新窗口中打开该项目的 qwen CLI

🌙 主题切换:
• 点击深色/浅色按钮切换主题
• 快捷键：Ctrl+T

⌨️ 快捷键:
• F5: 刷新
• Ctrl+E: 导出
• Ctrl+F: 搜索
• Ctrl+D: 收藏
• Ctrl+T: 切换主题
• Ctrl+C: 复制
• Ctrl+O: 打开 qwen CLI
• Ctrl+Delete: 删除当前项目
"""
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("500x450")
        
        text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)
    
    def _show_about(self):
        """显示关于"""
        about_text = """
Qwen CLI 历史记录查看器 - 增强版

版本：2.2
作者：AI Assistant

功能特性:
• 查看所有项目的聊天记录
• 搜索历史消息
• 收藏重要会话
• 导出为文本文件
• 深色/浅色主题切换
• 实时统计信息
• 右键菜单操作
• 删除会话和项目
• 快速打开 qwen CLI

感谢使用！
"""
        messagebox.showinfo("关于", about_text)


def main():
    """主函数"""
    root = tk.Tk()

    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')

    app = QwenHistoryViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
