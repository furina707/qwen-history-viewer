# Qwen CLI 历史记录查看器 - CustomTkinter 版

一个功能丰富的 GUI 工具，用于查看和管理 Qwen CLI 的聊天历史记录。

## ✨ 功能特性

### 核心功能
- 📂 **多项目管理** - 自动扫描所有项目的聊天记录
- 📋 **会话列表** - 按时间排序，显示预览和时间戳
- 💬 **彩色消息** - 区分用户/助手/系统消息
- 🔍 **全局搜索** - 支持关键词搜索，可指定范围

### 增强功能
- 🎨 **多主题切换** - 深色/浅色/蓝色/绿色四种主题
- ⭐ **收藏功能** - 收藏重要会话，支持筛选查看
- 📤 **导出功能** - 导出单个或全部会话为文本
- 📊 **统计信息** - 实时显示会话数、消息数等

### 系统功能
- 📝 **日志系统** - 分 Runtime Log 和 Historical Log
- ⚙️ **配置系统** - 方便修改程序参数
- 🔒 **进程锁定** - 避免删除其他 py 程序
- 💬 **会话 ID 启动** - 基于会话 ID 标准启动 CLI

## 🚀 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动方式

**Windows:**
```bash
# 隐藏终端启动（推荐）
pythonw main.pyw

# 或显示终端
python main.py
```

**Linux/Mac:**
```bash
python3 main.py
```

## 📋 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-s, --session` | 直接打开指定会话 ID | `python main.py -s abc123` |
| `-o, --open-cli` | 打开指定会话到 CLI 后退出 GUI | `python main.py -s abc123 -o` |

**使用示例：**

```bash
# 打开 GUI 并自动加载指定会话到 CLI
python main.py -s abc123def456

# 直接打开指定会话的 CLI（不启动 GUI）
python main.py -s abc123def456 -o

# 仅打开 GUI
python main.py
```

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F5` | 刷新会话列表 |
| `Ctrl+E` | 导出当前会话 |
| `Ctrl+F` | 聚焦搜索框 |
| `Ctrl+D` | 添加/移除收藏 |
| `Ctrl+T` | 切换主题 |
| `Ctrl+C` | 复制消息 |
| `Ctrl+O` | 打开 qwen CLI |

## 📁 目录结构

```
qwen_history_gui/
├── main.py              # 主程序入口
├── config.py            # 配置系统
├── logger.py            # 日志系统
├── process_lock.py      # 进程锁定模块
├── requirements.txt     # 依赖列表
└── README.md           # 说明文档
```

## 📁 数据存储

聊天记录存储在：
- **Windows:** `%USERPROFILE%\.qwen\projects\<项目>\chats\*.jsonl`
- **Linux/Mac:** `~/.qwen/projects/<项目>/chats/*.jsonl`

程序配置存储在：
- **Windows:** `%USERPROFILE%\.qwen_gui\config.json`
- **Linux/Mac:** `~/.qwen_gui/config.json`

日志文件存储在：
- **Runtime Log:** `~/.qwen_gui/logs/runtime.log`
- **Historical Log:** `~/.qwen_gui/logs/history_YYYY-MM-DD.log`

## 🎨 主题设置

程序支持四种主题：
- **dark** - 深色主题（默认）
- **light** - 浅色主题
- **blue** - 蓝色主题
- **green** - 绿色主题

可通过菜单 `视图 -> 选择主题` 或配置文件修改。

## ⚙️ 配置系统

配置文件位于 `~/.qwen_gui/config.json`，支持以下配置项：

```json
{
    "theme": "dark",
    "font_family": "Microsoft YaHei",
    "font_size": 12,
    "cli_command": "qwen",
    "cli_auto_resume": true,
    "log_level": "INFO",
    "log_max_size_mb": 10,
    "window_width": 1400,
    "window_height": 900,
    "enable_process_lock": true,
    "auto_save": true,
    "confirm_delete": true
}
```

## 📝 日志系统

### Runtime Log
- 记录当前运行期间的所有日志
- 日志级别：DEBUG
- 文件大小限制：10MB
- 备份数量：3 个

### Historical Log
- 按天轮转保存历史日志
- 日志级别：INFO
- 保留天数：30 天
- 文件格式：history_YYYY-MM-DD.log

### 查看日志
1. 菜单 `文件 -> 查看日志`
2. 选择日志类型（Runtime/Historical）
3. 可刷新、打开文件或清空日志

## 🔒 进程锁定

进程锁定功能可防止意外终止程序：

- 启动时自动锁定当前进程
- 关闭时自动解锁
- 定期清理已死亡的进程
- 可通过配置关闭此功能

## 🛠️ 技术栈

- **Python 3.x**
- **CustomTkinter** - 现代化 GUI 框架
- **psutil** - 进程管理
- **logging** - 标准日志库

## 📄 许可证

MIT License
