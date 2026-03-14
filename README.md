# Qwen CLI 历史记录查看器

一个功能丰富的 GUI 工具，用于查看和管理 Qwen CLI 的聊天历史记录。

## ✨ 功能特性

- 📂 **多项目管理** - 自动扫描所有项目的聊天记录
- 📋 **会话列表** - 按时间排序，显示预览和时间戳
- 💬 **彩色消息** - 区分用户/助手/系统消息
- 🔍 **全局搜索** - 支持关键词搜索，可指定范围
- 📊 **统计信息** - 实时显示会话数、消息数等
- 🌙 **主题切换** - 深色/浅色主题一键切换
- ⭐ **收藏功能** - 收藏重要会话，支持筛选查看
- 📤 **导出功能** - 导出单个或全部会话为文本
- 📋 **复制消息** - 一键复制选中消息
- 🎯 **筛选器** - 按今天/本周/本月/收藏筛选
- 🗑️ **删除功能** - 删除历史会话或整个项目（二次确认）
- 💬 **打开 CLI** - 一键打开对应项目的 qwen CLI 终端

## 🚀 使用方法

### 启动方式

**Windows:**
```bash
# 隐藏终端启动（推荐）
pythonw qwen_history_gui.pyw

# 或显示终端
python qwen_history_gui.py
```

**Linux/Mac:**
```bash
python3 qwen_history_gui.py
```

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F5` | 刷新会话列表 |
| `Ctrl+E` | 导出当前会话 |
| `Ctrl+F` | 聚焦搜索框 |
| `Ctrl+D` | 添加/移除收藏 |
| `Ctrl+T` | 切换主题 |
| `Ctrl+C` | 复制消息 |
| `Ctrl+O` | 打开 qwen CLI |
| `Ctrl+Delete` | 删除当前项目 |

## 📁 数据存储

聊天记录存储在：
- **Windows:** `%USERPROFILE%\.qwen\projects\<项目>\chats\*.jsonl`
- **Linux/Mac:** `~/.qwen/projects/<项目>/chats/*.jsonl`

收藏列表存储在：
- **Windows:** `%USERPROFILE%\.qwen\favorites.json`
- **Linux/Mac:** `~/.qwen/favorites.json`

## 📸 界面预览

- 主界面显示项目列表和历史会话
- 左侧统计面板实时显示数据
- 右侧彩色显示对话内容
- 支持深色/浅色主题切换

## 🛠️ 技术栈

- Python 3.x
- Tkinter (标准库，无需额外安装)

## 📄 许可证

MIT License
