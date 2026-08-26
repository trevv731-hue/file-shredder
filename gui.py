# -*- coding: utf-8 -*-
"""PySide6 Fluent 风格 GUI"""

import os
import sys
import json
import time
import ctypes
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QCheckBox,
    QProgressBar, QTextEdit, QFileDialog, QMessageBox, QFrame,
    QAbstractItemView, QSizePolicy
)

import winapi
import engine
import worker

# Fluent 配色
COLOR_BG = "#FFFFFF"
COLOR_CARD = "#FFFFFF"
COLOR_ACCENT = "#0078D4"
COLOR_ACCENT_HOVER = "#106EBE"
COLOR_ACCENT_PRESSED = "#005A9E"
COLOR_TEXT = "#1F1F1F"
COLOR_TEXT_SECONDARY = "#616161"
COLOR_BORDER = "#E5E5E5"
COLOR_DANGER = "#D13438"
COLOR_SUCCESS = "#107C10"
COLOR_WARN = "#FF8C00"
COLOR_HOVER = "#F5F5F5"


def is_frozen():
    return getattr(sys, 'frozen', False)


def get_app_dir():
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class DropListWidget(QListWidget):
    """支持拖放的列表控件"""
    paths_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        paths = []
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            if p and os.path.exists(p):
                paths.append(os.path.normpath(p))
        if paths:
            self.paths_dropped.emit(paths)
        event.acceptProposedAction()


class FluentButton(QPushButton):
    """Fluent 风格按钮"""
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setMinimumHeight(34)
        self.setCursor(Qt.PointingHandCursor)
        if primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_ACCENT};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 20px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{ background-color: {COLOR_ACCENT_HOVER}; }}
                QPushButton:pressed {{ background-color: {COLOR_ACCENT_PRESSED}; }}
                QPushButton:disabled {{ background-color: #B0B0B0; color: #E0E0E0; }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_CARD};
                    color: {COLOR_TEXT};
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 4px;
                    padding: 6px 16px;
                    font-size: 13px;
                }}
                QPushButton:hover {{ background-color: {COLOR_HOVER}; border-color: #C0C0C0; }}
                QPushButton:pressed {{ background-color: #EBEBEB; }}
                QPushButton:disabled {{ color: #B0B0B0; }}
            """)


class FluentCheckBox(QCheckBox):
    """Fluent 风格复选框"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QCheckBox {{
                spacing: 8px;
                font-size: 13px;
                color: {COLOR_TEXT};
                padding: 4px 0;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid #A0A0A0;
                border-radius: 3px;
                background: white;
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLOR_ACCENT};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLOR_ACCENT};
                border-color: {COLOR_ACCENT};
                image: none;
            }}
        """)


class CardFrame(QFrame):
    """卡片容器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
            }}
        """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件粉碎工具")
        self.setMinimumSize(720, 600)
        self.resize(780, 680)

        self.targets = []  # 待删除路径列表
        self.worker_process = None
        self.worker_out = None
        self.worker_poll_timer = QTimer(self)
        self.worker_poll_timer.timeout.connect(self._poll_worker)
        self.worker_log_pos = 0
        self.cancel_file = None

        self._build_ui()
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: #F8F8F8; }}
            QLabel {{ color: {COLOR_TEXT}; }}
            QListWidget {{
                background-color: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
                font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 10px;
                border-radius: 3px;
                border-bottom: 1px solid #F0F0F0;
            }}
            QListWidget::item:hover {{ background-color: {COLOR_HOVER}; }}
            QListWidget::item:selected {{ background-color: #E3F0FC; color: {COLOR_TEXT}; }}
            QTextEdit {{
                background-color: #FAFAFA;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
                color: #333;
            }}
            QProgressBar {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 3px;
                text-align: center;
                height: 20px;
                font-size: 12px;
                background-color: #F0F0F0;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT};
                border-radius: 2px;
            }}
        """)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 标题
        title = QLabel("文件粉碎工具")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #1F1F1F;")
        main_layout.addWidget(title)

        subtitle = QLabel("L0-L6 递进删除链：清属性 → POSIX删除 → 夺权限 → 关句柄 → NtDeleteFile → 卸载内存映射 → 杀进程 → 重启删")
        subtitle.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_SECONDARY};")
        subtitle.setWordWrap(True)
        main_layout.addWidget(subtitle)

        # === 文件列表卡片 ===
        list_card = CardFrame()
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(12, 10, 12, 12)
        list_layout.setSpacing(8)

        list_header = QHBoxLayout()
        list_label = QLabel("待删除文件/文件夹")
        list_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        list_header.addWidget(list_label)
        list_header.addStretch()

        self.count_label = QLabel("0 项")
        self.count_label.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_SECONDARY};")
        list_header.addWidget(self.count_label)
        list_layout.addLayout(list_header)

        self.list_widget = DropListWidget()
        self.list_widget.paths_dropped.connect(self._add_paths)
        self.list_widget.setMinimumHeight(180)
        list_layout.addWidget(self.list_widget)

        # 列表操作按钮
        list_btn_row = QHBoxLayout()
        btn_add_file = FluentButton("添加文件")
        btn_add_file.clicked.connect(self._add_files)
        list_btn_row.addWidget(btn_add_file)

        btn_add_folder = FluentButton("添加文件夹")
        btn_add_folder.clicked.connect(self._add_folder)
        list_btn_row.addWidget(btn_add_folder)

        btn_paste = FluentButton("粘贴路径")
        btn_paste.clicked.connect(self._paste_paths)
        list_btn_row.addWidget(btn_paste)

        list_btn_row.addStretch()

        btn_remove = FluentButton("移除选中")
        btn_remove.clicked.connect(self._remove_selected)
        list_btn_row.addWidget(btn_remove)

        btn_clear = FluentButton("清空")
        btn_clear.clicked.connect(self._clear_list)
        list_btn_row.addWidget(btn_clear)

        list_layout.addLayout(list_btn_row)
        main_layout.addWidget(list_card)

        # === 选项卡片 ===
        opt_card = CardFrame()
        opt_layout = QVBoxLayout(opt_card)
        opt_layout.setContentsMargins(12, 10, 12, 12)
        opt_layout.setSpacing(4)

        opt_label = QLabel("删除选项")
        opt_label.setStyleSheet("font-size: 13px; font-weight: 500; margin-bottom: 4px;")
        opt_layout.addWidget(opt_label)

        self.cb_unlock = FluentCheckBox("强力解锁（关句柄 + NtDeleteFile + DELETE_ON_CLOSE + 卸载内存映射）")
        self.cb_unlock.setChecked(True)
        opt_layout.addWidget(self.cb_unlock)

        self.cb_kill = FluentCheckBox("结束占用进程（Restart Manager 定位，强制终止进程树，谨慎）")
        self.cb_kill.setChecked(False)
        opt_layout.addWidget(self.cb_kill)

        self.cb_owner = FluentCheckBox("接管所有权与权限（解决「拒绝访问」）")
        self.cb_owner.setChecked(True)
        opt_layout.addWidget(self.cb_owner)

        self.cb_reboot = FluentCheckBox("重启时删除（最终兜底，系统启动前自动删除）")
        self.cb_reboot.setChecked(True)
        opt_layout.addWidget(self.cb_reboot)

        self.cb_shred = FluentCheckBox("粉碎覆写（多次覆盖文件内容，防止数据恢复，较慢）")
        self.cb_shred.setChecked(False)
        opt_layout.addWidget(self.cb_shred)

        main_layout.addWidget(opt_card)

        # === 操作按钮 + 进度 ===
        action_row = QHBoxLayout()

        self.btn_scan = FluentButton("查看占用进程")
        self.btn_scan.clicked.connect(self._scan_locks)
        action_row.addWidget(self.btn_scan)

        action_row.addStretch()

        self.btn_cancel = FluentButton("取消")
        self.btn_cancel.clicked.connect(self._cancel_task)
        self.btn_cancel.setVisible(False)
        action_row.addWidget(self.btn_cancel)

        self.btn_delete = FluentButton("开始删除", primary=True)
        self.btn_delete.setMinimumWidth(120)
        self.btn_delete.clicked.connect(self._start_delete)
        action_row.addWidget(self.btn_delete)

        main_layout.addLayout(action_row)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        # === 日志卡片 ===
        log_card = CardFrame()
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(12, 10, 12, 12)
        log_layout.setSpacing(6)

        log_header = QHBoxLayout()
        log_label = QLabel("操作日志")
        log_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        log_header.addWidget(log_label)
        log_header.addStretch()
        log_layout.addLayout(log_header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(120)
        log_layout.addWidget(self.log_text)

        main_layout.addWidget(log_card, 1)

        # 管理员权限提示
        if not winapi.is_admin():
            self._log("提示：当前为普通权限，删除时会自动请求 UAC 提权", "warn")
        else:
            self._log("已以管理员权限运行", "success")

    # ========== 列表操作 ==========

    def _add_paths(self, paths):
        added = 0
        for p in paths:
            norm = os.path.normpath(p)
            if os.path.exists(norm) and norm not in self.targets:
                self.targets.append(norm)
                added += 1
        self._refresh_list()
        if added:
            self._log(f"已添加 {added} 个目标", "info")

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择要删除的文件")
        if files:
            self._add_paths(files)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择要删除的文件夹")
        if folder:
            self._add_paths([folder])

    def _paste_paths(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if not text:
            return
        paths = []
        for line in text.splitlines():
            line = line.strip().strip('"').strip("'")
            if line and os.path.exists(line):
                paths.append(line)
        if paths:
            self._add_paths(paths)
        else:
            QMessageBox.information(self, "提示", "剪贴板中未找到有效路径")

    def _remove_selected(self):
        for item in self.list_widget.selectedItems():
            path = item.data(Qt.UserRole)
            if path in self.targets:
                self.targets.remove(path)
        self._refresh_list()

    def _clear_list(self):
        self.targets.clear()
        self._refresh_list()

    def _refresh_list(self):
        self.list_widget.clear()
        for path in self.targets:
            if os.path.isdir(path):
                # 计算文件夹大小
                total = 0
                try:
                    for root, dirs, files in os.walk(path):
                        for f in files:
                            try:
                                total += os.path.getsize(os.path.join(root, f))
                            except:
                                pass
                except:
                    pass
                size_str = self._fmt_size(total)
                icon = "📁"
                type_str = "文件夹"
            elif os.path.isfile(path):
                size_str = self._fmt_size(os.path.getsize(path))
                icon = "📄"
                type_str = "文件"
            else:
                size_str = "-"
                icon = "❓"
                type_str = "不存在"

            item = QListWidgetItem(f"{icon}  {path}\n     {type_str}  ·  {size_str}")
            item.setData(Qt.UserRole, path)
            item.setSizeHint(item.sizeHint().expandedTo(item.sizeHint()))
            self.list_widget.addItem(item)

        self.count_label.setText(f"{len(self.targets)} 项")

    @staticmethod
    def _fmt_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    # ========== 日志 ==========

    def _log(self, msg, level="info"):
        color = {
            "info": "#333333",
            "success": COLOR_SUCCESS,
            "warn": COLOR_WARN,
            "error": COLOR_DANGER,
        }.get(level, "#333333")
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f'<span style="color:#999;">[{timestamp}]</span> '
                           f'<span style="color:{color};">{msg}</span>')

    # ========== 扫描占用 ==========

    def _scan_locks(self):
        if not self.targets:
            QMessageBox.information(self, "提示", "请先添加文件或文件夹")
            return
        self._log("正在查找占用进程...", "info")
        self.btn_scan.setEnabled(False)
        QTimer.singleShot(100, lambda: self._do_scan())

    def _do_scan(self):
        try:
            procs = winapi.find_locking_processes(self.targets)
            if procs:
                self._log(f"发现 {len(procs)} 个占用进程：", "warn")
                for pid, name, atype, restartable in procs:
                    self._log(f"  PID {pid}: {name} [{atype}]", "warn")
            else:
                self._log("未发现占用进程", "success")
        except Exception as e:
            self._log(f"扫描失败: {e}", "error")
        finally:
            self.btn_scan.setEnabled(True)

    # ========== 删除任务 ==========

    def _start_delete(self):
        if not self.targets:
            QMessageBox.information(self, "提示", "请先添加文件或文件夹")
            return

        # 确认对话框
        msg = f"确定要删除以下 {len(self.targets)} 个项目吗？\n\n"
        for p in self.targets[:8]:
            msg += f"  • {p}\n"
        if len(self.targets) > 8:
            msg += f"  • ...等共 {len(self.targets)} 项\n"
        msg += "\n此操作不可恢复！"

        reply = QMessageBox.warning(
            self, "确认删除", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 护栏预检
        blocked = []
        for p in self.targets:
            prot, reason = engine.is_protected(p)
            if prot:
                blocked.append((p, reason))
        if blocked:
            bmsg = "以下路径受安全护栏保护，无法删除：\n\n"
            for p, r in blocked:
                bmsg += f"  • {p}\n    {r}\n"
            QMessageBox.critical(self, "安全拦截", bmsg)
            return

        # 构建选项
        options = {
            "unlock_handles": self.cb_unlock.isChecked(),
            "kill_processes": self.cb_kill.isChecked(),
            "take_ownership": self.cb_owner.isChecked(),
            "schedule_reboot": self.cb_reboot.isChecked(),
            "shred": self.cb_shred.isChecked(),
        }

        # 创建任务文件
        task_file, out_path = worker.write_task(self.targets, options, "delete")
        self.worker_out = out_path
        self.cancel_file = task_file + ".cancel"

        # 清空日志文件位置
        self.worker_log_pos = 0

        # 启动worker（提权）
        self._log("启动提权工作进程...", "info")
        try:
            if is_frozen():
                exe = sys.executable
                cmd = [exe, "--worker", task_file]
            else:
                exe = sys.executable
                cmd = [exe, os.path.join(get_app_dir(), "worker.py"), "--worker", task_file]

            if winapi.is_admin():
                # 已经是管理员，直接启动
                self.worker_process = subprocess.Popen(
                    cmd, creationflags=0x08000000,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            else:
                # ShellExecute runas 提权
                params = f'"--worker" "{task_file}"'
                if not is_frozen():
                    params = f'"{os.path.join(get_app_dir(), "worker.py")}" "{task_file}"'
                rc = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", exe, params, None, 0
                )
                if rc <= 32:
                    self._log("用户取消了UAC提权", "warn")
                    return
                self.worker_process = None  # 提权进程无法直接跟踪

            self._set_running(True)
            self.worker_poll_timer.start(300)

        except Exception as e:
            self._log(f"启动失败: {e}", "error")

    def _cancel_task(self):
        if self.cancel_file:
            try:
                with open(self.cancel_file, "w") as f:
                    f.write("cancel")
                self._log("正在取消...", "warn")
            except:
                pass

    def _set_running(self, running):
        self.btn_delete.setVisible(not running)
        self.btn_cancel.setVisible(running)
        self.progress.setVisible(running)
        self.btn_scan.setEnabled(not running)
        if running:
            self.progress.setRange(0, len(self.targets))
            self.progress.setValue(0)

    def _poll_worker(self):
        """轮询worker输出文件"""
        if not self.worker_out or not os.path.exists(self.worker_out):
            return

        try:
            with open(self.worker_out, "r", encoding="utf-8") as f:
                f.seek(self.worker_log_pos)
                new_content = f.read()
                self.worker_log_pos = f.tell()

            for line in new_content.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    self._handle_event(event)
                except:
                    pass
        except:
            pass

    def _handle_event(self, event):
        t = event.get("t")
        if t == "log":
            self._log(event.get("m", ""), event.get("l", "info"))
        elif t == "prog":
            d = event.get("d", 0)
            n = event.get("n", 1)
            self.progress.setRange(0, n)
            self.progress.setValue(d)
        elif t == "res":
            status = event.get("status", "")
            path = event.get("path", "")
            level = event.get("level", -1)
            if status == "deleted":
                self._log(f"✓ 已删除 (L{level}): {path}", "success")
            elif status == "reboot":
                self._log(f"⏳ 已登记重启删除: {path}", "warn")
            elif status == "blocked":
                self._log(f"🚫 已拦截: {path}", "error")
            else:
                self._log(f"✗ 删除失败: {path}", "error")
        elif t == "proc":
            self._log(f"  占用: PID {event.get('pid')} {event.get('name')}", "warn")
        elif t == "end":
            self.worker_poll_timer.stop()
            self._set_running(False)
            ok = event.get("ok", False)
            deleted = event.get("deleted", 0)
            reboot = event.get("reboot", 0)
            failed = event.get("failed", 0)
            blocked = event.get("blocked", 0)
            cancelled = event.get("cancelled", False)

            if cancelled:
                self._log("任务已取消", "warn")
            elif ok:
                self._log(f"全部完成：删除 {deleted} 个" +
                         (f"，重启删除 {reboot} 个" if reboot else ""), "success")
                QMessageBox.information(self, "完成",
                    f"成功删除 {deleted} 个目标" +
                    (f"\n{reboot} 个已登记为重启时删除" if reboot else ""))
            else:
                self._log(f"完成：删除 {deleted}，重启删除 {reboot}，失败 {failed}，拦截 {blocked}",
                         "warn" if failed == 0 else "error")
                QMessageBox.warning(self, "部分失败",
                    f"删除 {deleted} 个，重启删除 {reboot} 个\n"
                    f"失败 {failed} 个，拦截 {blocked} 个")

            # 刷新列表（移除已删除的）
            self.targets = [p for p in self.targets if os.path.exists(p)]
            self._refresh_list()

            # 清理
            if self.worker_out and os.path.exists(self.worker_out):
                try:
                    os.remove(self.worker_out)
                except:
                    pass
            if self.cancel_file and os.path.exists(self.cancel_file):
                try:
                    os.remove(self.cancel_file)
                except:
                    pass
