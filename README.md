# 文件粉碎工具 (File Shredder)

Windows 下专治「文件被占用 / 拒绝访问 / 只读 / 被系统保护」等删不掉的场景。基于 PySide6 (Qt 6) 现代 GUI，L0-L6 递进式删除链，双进程提权模型，打包成单个 `.exe`。

## 功能特性

- **PySide6 (Qt 6) 现代界面**：Fluent 风格，高 DPI 适配，原生拖放支持
- **拖放 / 粘贴路径** 添加删除目标，支持文件与文件夹混合队列
- **递进式删除策略 L0-L6**，自动逐级升级
- **双进程模型**：主界面普通权限运行（拖放正常），删除时自动 UAC 提权
- **系统关键路径护栏**：自动拦截 `C:\Windows`、盘根目录等，防误删
- **实时进度与日志**
- **64 位**，目标系统 Windows 10 及以上

## 删除原理

每一级只在前一级失败后才会尝试，尽可能减少对系统的破坏：

| 级别 | 手段 | 解决的典型问题 |
| --- | --- | --- |
| **L0** | 清除只读/隐藏/系统属性 | 属性阻止删除 |
| **L1** | POSIX 语义删除 `FileDispositionInfoEx` | 文件仍被打开也能标记删除 |
| **L2** | 常规删除 `DeleteFileW` / `RemoveDirectoryW` | 普通删除 |
| **L3** | 夺取所有权 + 重写 DACL | 「拒绝访问」/ 权限不足 |
| **L4** | 强制关闭其他进程持有的文件句柄 | 「文件被占用」 |
| **L4.5** | `NtDeleteFile` 原生 NT API | 绕过 Win32 层检查 |
| **L4.6** | `FILE_FLAG_DELETE_ON_CLOSE` | 句柄关闭后自动删除 |
| **L4.7** | `NtUnmapViewOfSection` 卸载内存映射 | 被 LoadLibrary 加载的 DLL/EXE |
| **L5** | Restart Manager 定位并结束占用进程树 | 顽固占用 |
| **L6** | `MoveFileEx(MOVEFILE_DELAY_UNTIL_REBOOT)` | 重启时删除兜底 |

## 使用方法

1. **双击 `文件粉碎工具.exe`** 打开（不要右键「以管理员身份运行」，否则拖放会被 UIPI 拦截）
2. 把要删除的文件或文件夹**拖入窗口**，或点「添加文件/文件夹」
3. 按需勾选选项（默认配置即可）
4. 点「开始删除」，弹出 UAC 时点「是」
5. 日志区实时显示每个目标的删除状态和失败原因

## 从源码运行

```bash
# Python 3.13+
pip install PySide6

python main.py
```

## 打包

```bash
pip install pyinstaller PySide6

pyinstaller --onefile --noconsole --name "文件粉碎工具" --clean ^
    --add-binary "D:\anaconda\Library\bin\ffi.dll;." ^
    --add-binary "D:\anaconda\Library\bin\shiboken6.cp313-win_amd64.dll;." ^
    --hidden-import shiboken6 ^
    --paths "D:\anaconda\Library\bin" ^
    main.py
```

> 注意：`--add-binary` 中的路径需根据你的 Anaconda/Python 安装位置调整。

## 项目结构

```
file_shredder/
├── main.py      # 入口：GUI/worker 模式路由
├── winapi.py    # Win32/NT API ctypes 封装
├── engine.py    # L0-L6 递进删除引擎 + 安全护栏
├── worker.py    # 提权子进程（JSON 任务、JSONL 日志）
└── gui.py       # PySide6 Fluent 风格界面
```

## 免责声明

本工具用于清理自己机器上确属多余的顽固文件。**删除操作不可逆**，请确认目标无误。系统关键路径已被自动拦截，但仍请谨慎使用「结束占用进程」等高风险选项。

## 许可证

MIT
