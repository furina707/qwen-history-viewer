#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen CLI 历史记录查看器 - CustomTkinter 增强版
基于会话 ID 启动 CLI 的标准实现
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

# 导入自定义模块
from config import get_config, init_config, Config
from logger import get_logger, init_logger, LogSystem
from process_lock import get_locker, init_locker, lock_current, unlock_current

# 设置 CustomTkinter 外观
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class QwenHistoryViewer(ctk.CTk):
    """Qwen CLI 历史记录查看器"""

    THEME_COLORS = {
        'dark': {
            'bg': '#1e1e1e', 'fg': '#d4d4d4', 'frame_bg': '#252526',
            'button_bg': '#0e639c', 'button_fg': '#ffffff',
            'user_color': '#569cd6', 'assistant_color': '#6a9955',
            'system_color': '#808080', 'highlight_color': '#f1c40f',
            'text_bg': '#1e1e1e', 'text_fg': '#d4d4d4'
        },
        'light': {
            'bg': '#f0f0f0', 'fg': '#000000', 'frame_bg': '#ffffff',
            'button_bg': '#0078d7', 'button_fg': '#ffffff',
            'user_color': '#0066cc', 'assistant_color': '#008000',
            'system_color': '#808080', 'highlight_color': '#ff6600',
            'text_bg': '#ffffff', 'text_fg': '#000000'
        },
        'blue': {
            'bg': '#1a1a2e', 'fg': '#eaeaea', 'frame_bg': '#16213e',
            'button_bg': '#0f3460', 'button_fg': '#ffffff',
            'user_color': '#4da8da', 'assistant_color': '#5dd175',
            'system_color': '#9a9a9a', 'highlight_color': '#f9ed69',
            'text_bg': '#1a1a2e', 'text_fg': '#eaeaea'
        },
        'green': {
            'bg': '#1a281a', 'fg': '#d4e4d4', 'frame_bg': '#2d3d2d',
            'button_bg': '#3d5c3d', 'button_fg': '#ffffff',
            'user_color': '#6ab0c3', 'assistant_color': '#89c989',
            'system_color': '#9a9a9a', 'highlight_color': '#f4d03f',
            'text_bg': '#1a281a', 'text_fg': '#d4e4d4'
        }
    }

    def __init__(self, session_id: Optional[str] = None):
        super().__init__()

        # 初始化
        self.app_config = init_config()
        self.app_logger = init_logger()
        self.app_locker = init_locker()

        if self.app_config.get("enable_process_lock", True):
            lock_current()

        self.app_logger.set_level(self.app_config.log_level)
        self.app_logger.info("=" * 50)
        self.app_logger.info("Qwen CLI 历史记录查看器启动")
        self.app_logger.info(f"会话 ID 参数：{session_id}")

        self.session_id_param = session_id
        self.geometry(f"{self.app_config.get('window_width', 1400)}x{self.app_config.get('window_height', 900)}")
        self.title("Qwen CLI 历史记录查看器")

        # 数据
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.current_session: Optional[str] = None
        self.favorites: set = set()
        self.projects: List[tuple] = []
        self.stats_labels: Dict[str, ctk.CTkLabel] = {}

        # qwen 目录
        self.qwen_dir = Path.home() / ".qwen"
        self.projects_dir = self.qwen_dir / "projects"
        self.favorites_file = self.qwen_dir / "favorites.json"

        self._load_favorites()
        self._create_ui()
        self._load_sessions()

        if session_id:
            self.after(500, lambda: self._open_qwen_cli(session_id))

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_ui(self):
        """创建界面"""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        self._create_menu()
        self._create_toolbar(main_frame)
        self._create_search_panel(main_frame)
        self._create_left_panel(main_frame)
        self._create_right_panel(main_frame)
        self._create_status_bar(main_frame)
        self._apply_theme(self.app_config.theme)

    def _create_menu(self):
        """创建菜单"""
        self.menu_bar = tk.Menu(self)
        self.configure(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="刷新", command=self._load_sessions, accelerator="F5")
        file_menu.add_command(label="打开 CLI", command=self._open_qwen_cli, accelerator="Ctrl+O")
        file_menu.add_command(label="导出", command=self._export_session, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="配置", command=self._show_config)
        file_menu.add_command(label="日志", command=self._show_logs)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing)

        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="复制", command=self._copy_message, accelerator="Ctrl+C")
        edit_menu.add_command(label="复制会话 ID", command=self._copy_session_id)
        edit_menu.add_command(label="搜索", command=self._focus_search, accelerator="Ctrl+F")

        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="切换主题", command=self._toggle_theme, accelerator="Ctrl+T")

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)

        self.bind('<F5>', lambda e: self._load_sessions())
        self.bind('<Control-e>', lambda e: self._export_session())
        self.bind('<Control-f>', lambda e: self._focus_search())
        self.bind('<Control-d>', lambda e: self._toggle_favorite())
        self.bind('<Control-t>', lambda e: self._toggle_theme())
        self.bind('<Control-c>', lambda e: self._copy_message())
        self.bind('<Control-o>', lambda e: self._open_qwen_cli())

    def _create_toolbar(self, parent):
        """工具栏"""
        toolbar = ctk.CTkFrame(parent, height=50)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        toolbar.pack_propagate(False)

        ctk.CTkLabel(toolbar, text="项目:").pack(side=tk.LEFT, padx=(10, 5))
        self.project_var = tk.StringVar()
        self.project_combo = ctk.CTkComboBox(toolbar, variable=self.project_var, state="readonly", width=200, command=self._on_project_selected)
        self.project_combo.pack(side=tk.LEFT, padx=(0, 10))

        ctk.CTkLabel(toolbar, text="筛选:").pack(side=tk.LEFT, padx=(10, 5))
        self.filter_var = tk.StringVar(value="全部")
        filter_combo = ctk.CTkComboBox(toolbar, variable=self.filter_var, state="readonly", width=100, values=["全部", "今天", "本周", "本月", "收藏"], command=self._apply_filter)
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))

        ctk.CTkButton(toolbar, text="🔄 刷新", command=self._load_sessions, width=80).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(toolbar, text="🌙 主题", command=self._toggle_theme, width=80).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(toolbar, text="💬 打开 CLI", command=self._open_qwen_cli, width=100).pack(side=tk.LEFT, padx=5)

        ctk.CTkLabel(toolbar, text="会话 ID:").pack(side=tk.LEFT, padx=(20, 5))
        self.session_id_var = tk.StringVar()
        self.session_id_entry = ctk.CTkEntry(toolbar, textvariable=self.session_id_var, width=200)
        self.session_id_entry.pack(side=tk.LEFT, padx=(0, 5))
        ctk.CTkButton(toolbar, text="打开指定会话", command=self._open_specified_session, width=120).pack(side=tk.LEFT)

    def _create_search_panel(self, parent):
        """搜索面板"""
        search_frame = ctk.CTkFrame(parent)
        search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(search_frame, text="关键词:").grid(row=0, column=0, padx=(10, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=300)
        self.search_entry.grid(row=0, column=1, padx=(0, 10))
        self.search_entry.bind('<Return>', lambda e: self._do_search())

        ctk.CTkLabel(search_frame, text="范围:").grid(row=0, column=2, padx=(10, 5))
        self.search_scope_var = tk.StringVar(value="当前会话")
        scope_combo = ctk.CTkComboBox(search_frame, variable=self.search_scope_var, state="readonly", width=120, values=["当前会话", "当前项目", "全部项目"])
        scope_combo.grid(row=0, column=3, padx=(0, 10))

        ctk.CTkButton(search_frame, text="🔍 搜索", command=self._do_search, width=80).grid(row=0, column=4, padx=5)
        ctk.CTkButton(search_frame, text="清空", command=self._clear_search, width=60).grid(row=0, column=5)

        self.search_result_label = ctk.CTkLabel(search_frame, text="", text_color="green")
        self.search_result_label.grid(row=1, column=0, columnspan=6, sticky="w", padx=10, pady=(5, 0))

    def _create_left_panel(self, parent):
        """左侧面板"""
        left_frame = ctk.CTkFrame(parent)
        left_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)

        theme = self.THEME_COLORS[self.app_config.theme]
        self.session_listbox = tk.Listbox(left_frame, width=50, font=("Consolas", 9), bg=theme['text_bg'], fg=theme['text_fg'], selectbackground=theme['highlight_color'], selectforeground='#000000', borderwidth=0, highlightthickness=0)
        self.session_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.session_listbox.bind("<<ListboxSelect>>", self._on_session_selected)
        self.session_listbox.bind("<Double-Button-1>", lambda e: self._open_qwen_cli())

        btn_frame = ctk.CTkFrame(left_frame)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        ctk.CTkButton(btn_frame, text="⭐ 收藏", command=self._toggle_favorite, width=100).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(btn_frame, text="🗑️ 删除", command=self._delete_session, width=100).pack(side=tk.LEFT, padx=2)

        self._create_stats_panel(left_frame)

    def _create_stats_panel(self, parent):
        """统计面板"""
        stats_frame = ctk.CTkFrame(parent)
        stats_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        stats_data = [("总会话", "total_sessions"), ("总消息", "total_messages"), ("用户", "user_messages"), ("助手", "assistant_messages"), ("项目", "projects_count"), ("收藏", "favorites_count")]
        for i, (label, key) in enumerate(stats_data):
            row = i // 3
            col = (i % 3) * 2
            ctk.CTkLabel(stats_frame, text=f"{label}:").grid(row=row, column=col, sticky="w", padx=5)
            lbl = ctk.CTkLabel(stats_frame, text="0", text_color="blue")
            lbl.grid(row=row, column=col+1, sticky="w", padx=5)
            self.stats_labels[key] = lbl

    def _create_right_panel(self, parent):
        """右侧面板"""
        right_frame = ctk.CTkFrame(parent)
        right_frame.grid(row=2, column=1, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

        info_frame = ctk.CTkFrame(right_frame)
        info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.info_label = ctk.CTkLabel(info_frame, text="", font=("Consolas", 9))
        self.info_label.pack(side=tk.LEFT)
        self.favorite_indicator = ctk.CTkLabel(info_frame, text="", font=("Arial", 12))
        self.favorite_indicator.pack(side=tk.RIGHT)

        # 使用 tkinter 的 ScrolledText 以支持 tag_configure
        from tkinter import scrolledtext
        theme = self.THEME_COLORS[self.app_config.theme]
        self.message_text = scrolledtext.ScrolledText(right_frame, font=("Consolas", 10), bg=theme['text_bg'], fg=theme['text_fg'], borderwidth=0)
        self.message_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self._configure_text_tags()

        btn_frame = ctk.CTkFrame(right_frame)
        btn_frame.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ctk.CTkButton(btn_frame, text="📋 复制", command=self._copy_message, width=100).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_frame, text="📤 导出", command=self._export_session, width=100).grid(row=0, column=1, padx=5)
        ctk.CTkButton(btn_frame, text="📈 统计", command=self._show_detailed_stats, width=100).grid(row=0, column=2, padx=5)

    def _configure_text_tags(self):
        """配置文本标签"""
        theme = self.THEME_COLORS[self.app_config.theme]
        self.message_text.tag_configure("user", foreground=theme['user_color'], font=("Consolas", 10, "bold"))
        self.message_text.tag_configure("assistant", foreground=theme['assistant_color'], font=("Consolas", 10, "bold"))
        self.message_text.tag_configure("system", foreground=theme['system_color'], font=("Consolas", 8, "italic"))
        self.message_text.tag_configure("highlight", background=theme['highlight_color'], foreground="#000000")
        self.message_text.tag_configure("timestamp", foreground=theme['system_color'], font=("Consolas", 8))

    def _create_status_bar(self, parent):
        """状态栏"""
        status_frame = ctk.CTkFrame(parent)
        status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self.status_var = tk.StringVar(value="就绪")
        ctk.CTkLabel(status_frame, textvariable=self.status_var, anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_label = ctk.CTkLabel(status_frame, text="")
        self.progress_label.pack(side=tk.RIGHT, padx=10)

    def _apply_theme(self, theme_name):
        """应用主题"""
        ctk.set_appearance_mode("dark" if theme_name in ['dark', 'blue', 'green'] else "light")
        if hasattr(self, 'session_listbox'):
            theme = self.THEME_COLORS[theme_name]
            self.session_listbox.config(bg=theme['text_bg'], fg=theme['text_fg'])

    def _set_theme(self, theme_name):
        """设置主题"""
        self.app_config.theme = theme_name
        self._apply_theme(theme_name)
        self.status_var.set(f"已切换到 {theme_name} 主题")

    def _toggle_theme(self):
        """切换主题"""
        themes = ['dark', 'light', 'blue', 'green']
        idx = themes.index(self.app_config.theme) if self.app_config.theme in themes else 0
        self._set_theme(themes[(idx + 1) % len(themes)])

    def _load_favorites(self):
        """加载收藏"""
        try:
            if self.favorites_file.exists():
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    self.favorites = set(json.load(f))
        except Exception as e:
            self.app_logger.error(f"加载收藏失败：{e}")
            self.favorites = set()

    def _save_favorites(self):
        """保存收藏"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.favorites), f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.app_logger.error(f"保存收藏失败：{e}")

    def _load_sessions(self):
        """加载会话"""
        self.status_var.set("正在加载...")
        self.update()
        self.app_logger.info("加载会话列表")

        self.project_combo.set("")
        self.session_listbox.delete(0, tk.END)
        self.sessions.clear()
        self.current_session = None

        if not self.projects_dir.exists():
            messagebox.showerror("错误", f"找不到 qwen 配置目录：{self.projects_dir}")
            return

        self.projects = []
        for item in self.projects_dir.iterdir():
            if item.is_dir():
                encoded_name = item.name
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
                        except:
                            pass
                if cwd_path:
                    project_name = cwd_path
                else:
                    project_name = encoded_name.replace("c-", "C:").replace("--", "/").replace("_user_", "_")
                self.projects.append((project_name, item))

        friendly_names = [name.replace("\\", "/") for name, _ in self.projects]
        self.project_combo.configure(values=friendly_names)
        self._update_stats_display()
        self.status_var.set(f"找到 {len(self.projects)} 个项目")

    def _find_project_dir(self, project_name):
        """查找项目目录"""
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
                        except:
                            continue
        encoded_name = project_name.replace("C:", "c-").replace("/", "--").replace("_", "_user_")
        return self.projects_dir / encoded_name

    def _on_project_selected(self, project_name):
        """选择项目"""
        if not project_name:
            return
        self.app_logger.info(f"选择项目：{project_name}")

        project_dir = self._find_project_dir(project_name)
        chats_dir = project_dir / "chats"

        self.session_listbox.delete(0, tk.END)
        self.sessions.clear()
        self.current_session = None
        self._clear_message_display()

        if not chats_dir.exists():
            self.status_var.set(f"项目 '{project_name}' 没有聊天记录")
            return

        session_files = list(chats_dir.glob("*.jsonl"))
        session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        filtered = self._filter_sessions(session_files)

        for session_file in filtered:
            self._add_session_to_list(session_file)
        self._update_stats_display()
        self.status_var.set(f"项目 '{project_name}' - 找到 {len(self.sessions)} 个会话")

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
                        if filter_type == "今天" and session_time.date() == now.date():
                            filtered.append(f)
                        elif filter_type == "本周" and (now - session_time.replace(tzinfo=None)).days <= 7:
                            filtered.append(f)
                        elif filter_type == "本月" and session_time.month == now.month and session_time.year == now.year:
                            filtered.append(f)
            except:
                continue
        return filtered

    def _apply_filter(self, event=None):
        """应用筛选"""
        if self.project_var.get():
            self._on_project_selected(self.project_var.get())

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
                    f.seek(0)
                    msg_count = sum(1 for _ in f)
                    if len(content) > 50:
                        content = content[:50] + "..."
                    fav_mark = "⭐ " if session_id in self.favorites else ""
                    display_text = f"{fav_mark}{timestamp[:19]} - {content}"
                    self.session_listbox.insert(tk.END, display_text)
                    self.sessions[session_id] = {'file': session_file, 'timestamp': timestamp, 'preview': content, 'msg_count': msg_count}
        except Exception as e:
            self.app_logger.error(f"读取会话失败：{e}")

    def _on_session_selected(self, event):
        """选择会话"""
        selection = self.session_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        session_id = list(self.sessions.keys())[index]
        self.current_session = session_id
        self._display_session(session_id)
        is_fav = session_id in self.favorites
        self.favorite_indicator.configure(text="⭐" if is_fav else "")

    def _display_session(self, session_id):
        """显示会话"""
        session_data = self.sessions[session_id]
        session_file = session_data['file']
        self.message_text.delete("1.0", tk.END)
        self.info_label.configure(text=f"会话 ID: {session_id} | 消息数：{session_data['msg_count']}")

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        self._display_message(data)
                    except:
                        continue
        except Exception as e:
            self.message_text.insert(tk.END, f"读取失败：{e}\n")

    def _display_message(self, data):
        """显示消息"""
        self.message_text.insert(tk.END, "\n")
        timestamp = data.get('timestamp', 'Unknown')
        msg_type = data.get('type', 'unknown')
        type_map = {'user': ('👤 用户', 'user'), 'assistant': ('🤖 助手', 'assistant'), 'system': ('⚙️ 系统', 'system')}
        role_text, tag = type_map.get(msg_type, (msg_type, 'system'))
        self.message_text.insert(tk.END, f"[{timestamp[:19]}] {role_text}\n", tag)
        message = data.get('message', {})
        parts = message.get('parts', [])
        for part in parts:
            part_type = part.get('type', 'text')
            if part_type == 'text':
                content = part.get('text', '')
                self.message_text.insert(tk.END, f"{content}\n")
            elif part_type == 'tool-call':
                tool_name = part.get('toolName', 'unknown')
                self.message_text.insert(tk.END, f"🔧 调用工具：{tool_name}\n", 'system')
            elif part_type == 'tool-result':
                tool_name = part.get('toolName', 'unknown')
                result = part.get('result', 'No result')
                self.message_text.insert(tk.END, f"🔧 工具 '{tool_name}' 结果：{result}\n", 'system')
        self.message_text.insert(tk.END, "-" * 80 + "\n", 'timestamp')

    def _clear_message_display(self):
        """清空消息"""
        self.message_text.delete("1.0", tk.END)
        self.info_label.configure(text="")
        self.favorite_indicator.configure(text="")

    def _update_stats_display(self):
        """更新统计"""
        stats = {
            'total_sessions': str(len(self.sessions)),
            'total_messages': str(sum(s['msg_count'] for s in self.sessions.values())),
            'projects_count': str(len(self.projects)),
            'favorites_count': str(len(self.favorites)),
            'user_messages': '0',
            'assistant_messages': '0'
        }
        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].configure(text=value)

    def _do_search(self):
        """搜索"""
        keyword = self.search_var.get().strip()
        if not keyword:
            self._clear_search()
            return
        scope = self.search_scope_var.get()
        results = []
        if scope == "当前会话" and self.current_session:
            session_file = self.sessions[self.current_session]['file']
            results = self._search_in_file(session_file, keyword)
        else:
            if scope == "当前项目":
                files = [s['file'] for s in self.sessions.values()]
            else:
                files = []
                for project_dir in self.projects_dir.iterdir():
                    if project_dir.is_dir():
                        chats_dir = project_dir / "chats"
                        if chats_dir.exists():
                            files.extend(chats_dir.glob("*.jsonl"))
            for f in files:
                results.extend(self._search_in_file(f, keyword))
        self.search_result_label.configure(text=f"找到 {len(results)} 条结果" if results else "未找到结果")

    def _search_in_file(self, file_path, keyword):
        """文件搜索"""
        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if keyword.lower() in line.lower():
                        results.append(line)
        except:
            pass
        return results

    def _clear_search(self):
        """清空搜索"""
        self.search_var.set("")
        self.search_result_label.configure(text="")

    def _focus_search(self):
        """聚焦搜索"""
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)

    def _toggle_favorite(self):
        """切换收藏"""
        if not self.current_session:
            messagebox.showwarning("警告", "请先选择会话")
            return
        if self.current_session in self.favorites:
            self.favorites.remove(self.current_session)
        else:
            self.favorites.add(self.current_session)
        self._save_favorites()
        self._on_project_selected(self.project_var.get())

    def _copy_message(self):
        """复制消息"""
        try:
            selected = self.message_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(selected)
        except:
            all_text = self.message_text.get("1.0", tk.END)
            self.clipboard_clear()
            self.clipboard_append(all_text)
        self.status_var.set("已复制")

    def _copy_session_id(self):
        """复制会话 ID"""
        if not self.current_session:
            messagebox.showwarning("警告", "请先选择会话")
            return
        self.clipboard_clear()
        self.clipboard_append(self.current_session)
        self.status_var.set(f"已复制：{self.current_session}")

    def _delete_session(self):
        """删除会话"""
        selection = self.session_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择会话")
            return
        if not self.app_config.get("confirm_delete", True) or messagebox.askyesno("确认", "确定删除？"):
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
                self._update_stats_display()
                self.status_var.set(f"已删除：{session_id}")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败：{e}")

    def _open_specified_session(self):
        """打开指定会话"""
        session_id = self.session_id_var.get().strip()
        if not session_id:
            messagebox.showwarning("警告", "请输入会话 ID")
            return
        self._open_qwen_cli(session_id)

    def _open_qwen_cli(self, session_id=None):
        """打开 CLI"""
        target = session_id if session_id else self.current_session
        if not target:
            project_name = self.project_var.get()
            if not project_name:
                messagebox.showwarning("警告", "请先选择项目或会话")
                return
            try:
                project_dir = self._find_project_dir(project_name)
                if not project_dir.exists():
                    messagebox.showerror("错误", f"项目不存在：{project_dir}")
                    return
                cmd = f'cmd.exe /k "cd /d {project_name} && {self.app_config.get("cli_command", "qwen")} -c"'
                subprocess.Popen(cmd)
                self.status_var.set(f"已打开项目 CLI")
            except Exception as e:
                self.app_logger.error(f"打开 CLI 失败：{e}")
                messagebox.showerror("错误", f"打开 CLI 失败：{e}")
            return

        try:
            session_file = None
            work_dir = None
            for item in self.projects_dir.iterdir():
                if item.is_dir():
                    chats_dir = item / "chats"
                    if chats_dir.exists():
                        target_file = chats_dir / f"{target}.jsonl"
                        if target_file.exists():
                            session_file = target_file
                            try:
                                with open(target_file, 'r', encoding='utf-8') as f:
                                    first_line = f.readline()
                                    if first_line:
                                        data = json.loads(first_line)
                                        work_dir = data.get('cwd', None)
                            except:
                                pass
                            if not work_dir:
                                work_dir = item.name.replace("c-", "C:").replace("--", "/").replace("_user_", "_")
                            break
            if not session_file:
                messagebox.showerror("错误", f"找不到会话：{target}")
                return
            cmd = f'cmd.exe /k "cd /d {work_dir} && {self.app_config.get("cli_command", "qwen")} -r {target}"'
            subprocess.Popen(cmd)
            self.status_var.set(f"已打开会话：{target[:8]}...")
            self.app_logger.info(f"打开 CLI - 会话：{target}")
        except Exception as e:
            self.app_logger.error(f"打开 CLI 失败：{e}")
            messagebox.showerror("错误", f"打开 CLI 失败：{e}")

    def _export_session(self):
        """导出会话"""
        if not self.current_session:
            return
        session_file = self.sessions[self.current_session]['file']
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文件", "*.txt")], initialfile=f"qwen_{self.current_session[:8]}.txt")
        if file_path:
            try:
                with open(session_file, 'r', encoding='utf-8') as src:
                    with open(file_path, 'w', encoding='utf-8') as dst:
                        dst.write(f"会话 ID: {self.current_session}\n导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*80}\n\n")
                        for line in src:
                            try:
                                data = json.loads(line.strip())
                                ts = data.get('timestamp', 'Unknown')
                                msg_type = data.get('type', 'unknown')
                                message = data.get('message', {})
                                parts = message.get('parts', [])
                                role = {'user': '用户', 'assistant': '助手', 'system': '系统'}.get(msg_type, msg_type)
                                dst.write(f"[{ts[:19]}] {role}:\n")
                                for part in parts:
                                    if part.get('type') == 'text':
                                        dst.write(f"{part.get('text', '')}\n")
                                dst.write("\n" + "-"*80 + "\n\n")
                            except:
                                continue
                self.status_var.set(f"已导出：{file_path}")
                messagebox.showinfo("成功", f"已导出到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{e}")

    def _show_detailed_stats(self):
        """详细统计"""
        if not self.current_session:
            messagebox.showwarning("警告", "请先选择会话")
            return
        session_file = self.sessions[self.current_session]['file']
        stats = {'total': 0, 'user': 0, 'assistant': 0, 'chars': 0}
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        stats['total'] += 1
                        stats[data.get('type', 'unknown')] = stats.get(data.get('type', 'unknown'), 0) + 1
                        for part in data.get('message', {}).get('parts', []):
                            if part.get('type') == 'text':
                                stats['chars'] += len(part.get('text', ''))
                    except:
                        continue
        except Exception as e:
            messagebox.showerror("错误", f"统计失败：{e}")
            return

        win = ctk.CTkToplevel(self)
        win.title(f"统计 - {self.current_session[:8]}")
        win.geometry("300x250")
        frame = ctk.CTkFrame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame, text="📊 会话统计", font_size=16, font_weight="bold").pack(pady=10)
        for label, value in [("总会话", stats['total']), ("用户", stats.get('user', 0)), ("助手", stats.get('assistant', 0)), ("字符", f"{stats['chars']:,}")]:
            ctk.CTkLabel(frame, text=f"{label}: {value}").pack(pady=2)
        ctk.CTkButton(frame, text="关闭", command=win.destroy).pack(pady=10)

    def _show_config(self):
        """配置窗口"""
        win = ctk.CTkToplevel(self)
        win.title("配置")
        win.geometry("400x300")
        frame = ctk.CTkFrame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame, text="⚙️ 配置", font_size=16, font_weight="bold").pack(pady=10)

        theme_frame = ctk.CTkFrame(frame)
        theme_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(theme_frame, text="主题:").pack(side=tk.LEFT, padx=10)
        theme_combo = ctk.CTkComboBox(theme_frame, values=['dark', 'light', 'blue', 'green'])
        theme_combo.set(self.app_config.theme)
        theme_combo.pack(side=tk.LEFT, padx=10)
        theme_combo.configure(command=lambda v: self._set_theme(v))

        log_frame = ctk.CTkFrame(frame)
        log_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(log_frame, text="日志级别:").pack(side=tk.LEFT, padx=10)
        log_combo = ctk.CTkComboBox(log_frame, values=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        log_combo.set(self.app_config.log_level)
        log_combo.pack(side=tk.LEFT, padx=10)
        log_combo.configure(command=lambda v: self.app_config.set("log_level", v))

        cli_frame = ctk.CTkFrame(frame)
        cli_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(cli_frame, text="CLI 命令:").pack(side=tk.LEFT, padx=10)
        cli_entry = ctk.CTkEntry(cli_frame)
        cli_entry.insert(0, self.app_config.get("cli_command", "qwen"))
        cli_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        def save_cli():
            self.app_config.set("cli_command", cli_entry.get())
        cli_entry.configure(command=lambda: save_cli())

        lock_frame = ctk.CTkFrame(frame)
        lock_frame.pack(fill=tk.X, pady=5)
        lock_switch = ctk.CTkSwitch(lock_frame, text="启用进程锁定", command=lambda: self.app_config.set("enable_process_lock", lock_switch.get()))
        lock_switch.pack(side=tk.LEFT, padx=10)
        lock_switch.select() if self.app_config.get("enable_process_lock", True) else lock_switch.deselect()

        ctk.CTkButton(frame, text="关闭", command=win.destroy).pack(pady=20)

    def _show_logs(self):
        """日志窗口"""
        win = ctk.CTkToplevel(self)
        win.title("日志")
        win.geometry("700x500")
        frame = ctk.CTkFrame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        type_frame = ctk.CTkFrame(frame)
        type_frame.pack(fill=tk.X, pady=5)
        ctk.CTkLabel(type_frame, text="类型:").pack(side=tk.LEFT, padx=10)
        log_type_var = tk.StringVar(value="runtime")
        ctk.CTkRadioButton(type_frame, text="Runtime", variable=log_type_var, value="runtime").pack(side=tk.LEFT, padx=5)
        ctk.CTkRadioButton(type_frame, text="Historical", variable=log_type_var, value="historical").pack(side=tk.LEFT, padx=5)

        def load_log():
            self.message_text.delete("1.0", tk.END)
            log_file = self.app_logger.get_log_file(log_type_var.get())
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        self.message_text.insert(tk.END, f.read())
                except Exception as e:
                    self.message_text.insert(tk.END, f"读取失败：{e}")
            else:
                self.message_text.insert(tk.END, "日志不存在")

        log_text = ctk.CTkTextbox(frame)
        log_text.pack(fill=tk.BOTH, expand=True, pady=10)
        # 替换 self.message_text 为 log_text
        self.message_text_backup = self.message_text
        self.message_text = log_text

        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ctk.CTkButton(btn_frame, text="刷新", command=load_log).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="打开", command=lambda: self.app_logger.open_log_file(log_type_var.get())).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="清空", command=lambda: [self.app_logger.clear_logs(), load_log()]).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="关闭", command=lambda: [setattr(self, 'message_text', self.message_text_backup), win.destroy()]).pack(side=tk.RIGHT, padx=5)
        load_log()

    def _show_help(self):
        """帮助"""
        help_text = """
Qwen CLI 历史记录查看器

📋 基本功能:
• 选择项目查看会话
• 双击会话打开 CLI
• 搜索历史记录

⌨️ 快捷键:
• F5: 刷新
• Ctrl+E: 导出
• Ctrl+F: 搜索
• Ctrl+D: 收藏
• Ctrl+T: 切换主题
• Ctrl+O: 打开 CLI
"""
        win = ctk.CTkToplevel(self)
        win.title("帮助")
        win.geometry("500x400")
        text = ctk.CTkTextbox(win, font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        text.insert(tk.END, help_text)
        text.configure(state=tk.DISABLED)

    def _show_about(self):
        """关于"""
        messagebox.showinfo("关于", f"""
Qwen CLI 历史记录查看器
版本：3.0 (CustomTkinter)

功能:
• 纯 Python 实现
• CustomTkinter GUI
• 日志系统
• 配置系统
• 进程锁定

配置：{self.app_config.config_file}
日志：{self.app_logger.log_dir}
""")

    def _on_closing(self):
        """关闭"""
        self.app_logger.info("程序关闭")
        if self.app_config.get("enable_process_lock", True):
            unlock_current()
        self.app_locker.cleanup_dead_processes()
        self.destroy()


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='Qwen CLI 历史记录查看器')
    parser.add_argument('-s', '--session', type=str, help='会话 ID')
    parser.add_argument('-o', '--open-cli', action='store_true', help='仅打开 CLI')
    args = parser.parse_args()

    if args.open_cli and args.session:
        qwen_dir = Path.home() / ".qwen"
        projects_dir = qwen_dir / "projects"
        work_dir = None
        for item in projects_dir.iterdir():
            if item.is_dir():
                chats_dir = item / "chats"
                if chats_dir.exists():
                    target_file = chats_dir / f"{args.session}.jsonl"
                    if target_file.exists():
                        try:
                            with open(target_file, 'r', encoding='utf-8') as f:
                                first_line = f.readline()
                                if first_line:
                                    data = json.loads(first_line)
                                    work_dir = data.get('cwd', None)
                        except:
                            pass
                        if not work_dir:
                            work_dir = item.name.replace("c-", "C:").replace("--", "/").replace("_user_", "_")
                        break
        if work_dir:
            cmd = f'cmd.exe /k "cd /d {work_dir} && qwen -r {args.session}"'
            subprocess.Popen(cmd)
            print(f"已打开：{args.session}")
        else:
            print(f"错误：找不到会话 {args.session}")
            sys.exit(1)
        return

    init_config()
    init_logger()
    app = QwenHistoryViewer(session_id=args.session)
    app.mainloop()


if __name__ == "__main__":
    main()
