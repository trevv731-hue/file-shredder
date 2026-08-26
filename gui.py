# -*- coding: utf-8 -*-
"""文件粉碎工具 GUI - 增强版（智能模式+强力模式+详细日志）"""

import os
import sys
import json
import time
import subprocess
import tempfile

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QColor, QIcon, QPixmap, QPainter, QBrush, QPen
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QCheckBox,
    QProgressBar, QFrame, QScrollArea, QMessageBox, QSizePolicy,
    QGraphicsDropShadowEffect, QMenu
)

import worker
import winapi


ACCENT = "#0078D4"
ACCENT_HOVER = "#106EBE"
BG = "#F3F3F3"
CARD = "#FFFFFF"
TEXT = "#1A1A1A"
TEXT_SECOND = "#616161"
BORDER = "#E1E1E1"
SUCCESS = "#107C10"
WARN = "#CA5010"
ERROR = "#D13438"
INFO = "#0078D4"


def make_icon(color, symbol, size=48):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QBrush(QColor(color)))
    p.setPen(Qt.NoPen)
    p.drawEllipse(4, 4, size-8, size-8)
    p.setPen(QPen(QColor("#FFFFFF"), 3))
    p.setFont(QFont("Segoe UI", 18, QFont.Bold))
    p.drawText(pix.rect(), Qt.AlignCenter, symbol)
    p.end()
    return QIcon(pix)


class DropArea(QFrame):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setStyleSheet(f"""
            DropArea {{
                background: {CARD};
                border: 2px dashed {BORDER};
                border-radius: 12px;
            }}
            DropArea:hover {{ border-color: {ACCENT}; }}
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.icon_label = QLabel("📁")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 42px;")
        self.text_label = QLabel("将文件或文件夹拖到这里\n或点击选择")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet(f"color: {TEXT_SECOND}; font-size: 14px;")
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            paths, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "所有文件 (*.*)")
            if paths: self.files_dropped.emit(paths)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"background: {CARD}; border: 2px solid {ACCENT}; border-radius: 12px;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"background: {CARD}; border: 2px dashed {BORDER}; border-radius: 12px;")

    def dropEvent(self, event: QDropEvent):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.toLocalFile()]
        if paths: self.files_dropped.emit(paths)
        self.setStyleSheet(f"background: {CARD}; border: 2px dashed {BORDER}; border-radius: 12px;")


class FileItem(QFrame):
    removed = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.setStyleSheet(f"background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        icon = "📁" if os.path.isdir(path) else "📄"
        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet("font-size: 20px;")
        self.name_label = QLabel(os.path.basename(path) or path)
        self.name_label.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 500;")
        self.path_label = QLabel(path)
        self.path_label.setStyleSheet(f"color: {TEXT_SECOND}; font-size: 11px;")
        text_layout = QVBoxLayout()
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.path_label)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 12px; font-weight: 600;")
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.setStyleSheet(f"QPushButton {{ background: transparent; border: none; color: {TEXT_SECOND}; font-size: 14px; border-radius: 14px; }} QPushButton:hover {{ background: {BORDER}; color: {TEXT}; }}")
        self.remove_btn.clicked.connect(lambda: self.removed.emit(self.path))
        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout, 1)
        layout.addWidget(self.status_label)
        layout.addWidget(self.remove_btn)

    def set_status(self, status, message=""):
        colors = {"deleted": SUCCESS, "reboot": WARN, "failed": ERROR, "blocked": ERROR, "pending": TEXT_SECOND}
        icons = {"deleted": "✓", "reboot": "⏳", "failed": "✗", "blocked": "🚫", "pending": ""}
        color = colors.get(status, TEXT_SECOND)
        icon = icons.get(status, "")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")
        self.status_label.setText(f"{icon} {message}" if message else icon)


class DeleteWorker(QThread):
    log_signal = Signal(str, str)
    result_signal = Signal(dict)
    progress_signal = Signal(int, int)
    proc_signal = Signal(dict)
    finished_signal = Signal(dict)

    def __init__(self, targets, options):
        super().__init__()
        self.targets = targets
        self.options = options
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            task_file, out_path = worker.write_task(self.targets, self.options)
        except Exception as e:
            self.log_signal.emit(f"创建任务失败: {e}", "error")
            self.finished_signal.emit({"ok": False, "deleted": 0, "failed": len(self.targets), "reboot": 0, "blocked": 0})
            return

        exe = sys.executable
        if getattr(sys, 'frozen', False):
            exe = sys.executable
        try:
            proc = subprocess.Popen([exe, "--worker", task_file],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    creationflags=0x08000000)
        except Exception as e:
            self.log_signal.emit(f"启动工作进程失败: {e}", "error")
            self.finished_signal.emit({"ok": False, "deleted": 0, "failed": len(self.targets), "reboot": 0, "blocked": 0})
            return

        last_size = 0
        while proc.poll() is None:
            if self._cancel:
                try:
                    with open(task_file + ".cancel", "w") as f: f.write("1")
                except: pass
            try:
                if os.path.exists(out_path):
                    size = os.path.getsize(out_path)
                    if size > last_size:
                        with open(out_path, "r", encoding="utf-8") as f:
                            f.seek(last_size)
                            for line in f:
                                line = line.strip()
                                if not line: continue
                                try:
                                    evt = json.loads(line)
                                    if evt.get("t") == "log":
                                        self.log_signal.emit(evt.get("m",""), evt.get("l","info"))
                                    elif evt.get("t") == "res":
                                        self.result_signal.emit(evt)
                                    elif evt.get("t") == "prog":
                                        self.progress_signal.emit(evt.get("d",0), evt.get("n",0))
                                    elif evt.get("t") == "proc":
                                        self.proc_signal.emit(evt)
                                    elif evt.get("t") == "end":
                                        self.finished_signal.emit(evt)
                                except: pass
                        last_size = size
            except: pass
            time.sleep(0.15)

        try:
            if os.path.exists(out_path):
                with open(out_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        try:
                            evt = json.loads(line)
                            if evt.get("t") == "log": self.log_signal.emit(evt.get("m",""), evt.get("l","info"))
                            elif evt.get("t") == "res": self.result_signal.emit(evt)
                            elif evt.get("t") == "end": self.finished_signal.emit(evt)
                        except: pass
        except: pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("文件粉碎工具 v2.0")
        self.setMinimumSize(720, 680)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")
        self.targets = {}
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel("文件粉碎工具")
        title_label.setStyleSheet(f"color: {TEXT}; font-size: 24px; font-weight: 700;")
        subtitle = QLabel("智能强制删除 · 多轮重试 · 深度占用分析")
        subtitle.setStyleSheet(f"color: {TEXT_SECOND}; font-size: 12px;")
        title_text = QVBoxLayout()
        title_text.addWidget(title_label)
        title_text.addWidget(subtitle)
        title_layout.addLayout(title_text)
        title_layout.addStretch()
        self.admin_label = QLabel("⚡ 管理员" if winapi.is_admin() else "🔒 未提权")
        self.admin_label.setStyleSheet(f"color: {SUCCESS if winapi.is_admin() else WARN}; font-size: 12px; font-weight: 600; padding: 4px 10px; background: {CARD}; border-radius: 12px;")
        title_layout.addWidget(self.admin_label)
        main_layout.addLayout(title_layout)

        # 拖拽区
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self._add_files)
        main_layout.addWidget(self.drop_area)

        # 文件列表
        list_card = QFrame()
        list_card.setStyleSheet(f"background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(12, 12, 12, 12)
        list_header = QHBoxLayout()
        self.list_title = QLabel("待删除文件 (0)")
        self.list_title.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 600;")
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setFixedHeight(28)
        self.clear_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT_SECOND}; border: 1px solid {BORDER}; border-radius: 6px; padding: 0 12px; }} QPushButton:hover {{ background: {BORDER}; color: {TEXT}; }}")
        self.clear_btn.clicked.connect(self._clear_files)
        list_header.addWidget(self.list_title)
        list_header.addStretch()
        list_header.addWidget(self.clear_btn)
        list_layout.addLayout(list_header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet(f"QScrollArea {{ background: {CARD}; }}")
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()
        self.scroll.setWidget(self.list_widget)
        self.scroll.setMaximumHeight(200)
        list_layout.addWidget(self.scroll)
        main_layout.addWidget(list_card)

        # 选项
        opts_card = QFrame()
        opts_card.setStyleSheet(f"background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;")
        opts_layout = QVBoxLayout(opts_card)
        opts_layout.setContentsMargins(16, 12, 16, 12)
        opts_title = QLabel("删除选项")
        opts_title.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 600; margin-bottom: 4px;")
        opts_layout.addWidget(opts_title)

        row1 = QHBoxLayout()
        self.cb_smart = QCheckBox("🧠 智能模式（动态策略+多轮重试）")
        self.cb_smart.setChecked(True)
        self.cb_smart.setStyleSheet(f"QCheckBox {{ color: {TEXT}; font-size: 12px; spacing: 6px; }}")
        self.cb_unlock = QCheckBox("🔓 关闭文件句柄")
        self.cb_unlock.setChecked(True)
        self.cb_unlock.setStyleSheet(f"QCheckBox {{ color: {TEXT}; font-size: 12px; spacing: 6px; }}")
        row1.addWidget(self.cb_smart)
        row1.addWidget(self.cb_unlock)
        opts_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.cb_owner = QCheckBox("🔑 夺取所有权")
        self.cb_owner.setChecked(True)
        self.cb_owner.setStyleSheet(f"QCheckBox {{ color: {TEXT}; font-size: 12px; spacing: 6px; }}")
        self.cb_kill = QCheckBox("💀 终止占用进程")
        self.cb_kill.setChecked(False)
        self.cb_kill.setStyleSheet(f"QCheckBox {{ color: {TEXT}; font-size: 12px; spacing: 6px; }}")
        row2.addWidget(self.cb_owner)
        row2.addWidget(self.cb_kill)
        opts_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.cb_reboot = QCheckBox("🔄 重启时删除（兜底）")
        self.cb_reboot.setChecked(True)
        self.cb_reboot.setStyleSheet(f"QCheckBox {{ color: {TEXT}; font-size: 12px; spacing: 6px; }}")
        self.cb_shred = QCheckBox("🔨 粉碎覆写（不可恢复）")
        self.cb_shred.setChecked(False)
        self.cb_shred.setStyleSheet(f"QCheckBox {{ color: {TEXT}; font-size: 12px; spacing: 6px; }}")
        row3.addWidget(self.cb_reboot)
        row3.addWidget(self.cb_shred)
        opts_layout.addLayout(row3)

        # 强力模式（单独一行，带警告）
        self.cb_force = QCheckBox("⚠️ 强力模式（绕过安全护栏，仅在确认目标安全时使用）")
        self.cb_force.setChecked(False)
        self.cb_force.setStyleSheet(f"QCheckBox {{ color: {WARN}; font-size: 12px; spacing: 6px; font-weight: 500; }}")
        opts_layout.addWidget(self.cb_force)

        main_layout.addWidget(opts_card)

        # 日志
        log_card = QFrame()
        log_card.setStyleSheet(f"background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(12, 10, 12, 10)
        log_title = QLabel("操作日志")
        log_title.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 600;")
        log_layout.addWidget(log_title)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(160)
        self.log_text.setStyleSheet(f"QTextEdit {{ background: #FAFAFA; border: 1px solid {BORDER}; border-radius: 8px; color: {TEXT}; font-family: 'Consolas', 'Microsoft YaHei', monospace; font-size: 11px; }}")
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_card)

        # 进度条和按钮
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet(f"QProgressBar {{ background: {BORDER}; border: none; border-radius: 6px; height: 8px; text-align: center; }} QProgressBar::chunk {{ background: {ACCENT}; border-radius: 6px; }}")
        main_layout.addWidget(self.progress)

        btn_layout = QHBoxLayout()
        self.delete_btn = QPushButton("🗑️  开始粉碎删除")
        self.delete_btn.setFixedHeight(44)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{ background: {ACCENT}; color: white; border: none; border-radius: 10px; font-size: 15px; font-weight: 600; }}
            QPushButton:hover {{ background: {ACCENT_HOVER}; }}
            QPushButton:disabled {{ background: {BORDER}; color: {TEXT_SECOND}; }}
        """)
        self.delete_btn.clicked.connect(self._start_delete)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedHeight(44)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{ background: {CARD}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 10px; font-size: 14px; }}
            QPushButton:hover {{ background: {BORDER}; }}
        """)
        self.cancel_btn.clicked.connect(self._cancel_delete)
        btn_layout.addWidget(self.delete_btn, 1)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

    def _add_files(self, paths):
        for p in paths:
            if p not in self.targets:
                item = FileItem(p)
                item.removed.connect(self._remove_file)
                self.targets[p] = item
                self.list_layout.insertWidget(self.list_layout.count() - 1, item)
        self._update_list_title()

    def _remove_file(self, path):
        if path in self.targets:
            item = self.targets.pop(path)
            item.setParent(None)
            item.deleteLater()
        self._update_list_title()

    def _clear_files(self):
        for p in list(self.targets.keys()):
            self._remove_file(p)

    def _update_list_title(self):
        self.list_title.setText(f"待删除文件 ({len(self.targets)})")

    def _log(self, msg, level="info"):
        colors = {"success": SUCCESS, "warn": WARN, "error": ERROR, "info": INFO}
        color = colors.get(level, TEXT)
        ts = time.strftime("%H:%M:%S")
        self.log_text.append(f'<span style="color:{TEXT_SECOND}">[{ts}]</span> <span style="color:{color}">{msg}</span>')
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def _start_delete(self):
        if not self.targets:
            QMessageBox.warning(self, "提示", "请先添加要删除的文件或文件夹")
            return
        if self.cb_force.isChecked():
            reply = QMessageBox.warning(self, "强力模式确认",
                "强力模式将绕过安全护栏，可能删除系统关键文件！\n\n请确认你添加的目标都是安全的。\n\n是否继续？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.cb_force.setChecked(False)
                return

        options = {
            "unlock_handles": self.cb_unlock.isChecked(),
            "kill_processes": self.cb_kill.isChecked(),
            "take_ownership": self.cb_owner.isChecked(),
            "schedule_reboot": self.cb_reboot.isChecked(),
            "shred": self.cb_shred.isChecked(),
            "smart_mode": self.cb_smart.isChecked(),
            "force_mode": self.cb_force.isChecked(),
            "max_retries": 3,
        }

        self.log_text.clear()
        self._log(f"开始删除 {len(self.targets)} 个目标" + (" [智能模式]" if options["smart_mode"] else "") + (" [强力模式]" if options["force_mode"] else ""), "info")

        for item in self.targets.values():
            item.set_status("pending")

        self.delete_btn.setEnabled(False)
        self.delete_btn.setText("删除中...")
        self.cancel_btn.setVisible(True)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(self.targets))
        self.progress.setValue(0)

        self.worker = DeleteWorker(list(self.targets.keys()), options)
        self.worker.log_signal.connect(self._log)
        self.worker.result_signal.connect(self._on_result)
        self.worker.progress_signal.connect(lambda d, n: self.progress.setValue(d))
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_result(self, evt):
        path = evt.get("path", "")
        status = evt.get("status", "failed")
        message = evt.get("message", "")
        if path in self.targets:
            self.targets[path].set_status(status, message)

    def _on_finished(self, evt):
        deleted = evt.get("deleted", 0)
        failed = evt.get("failed", 0)
        reboot = evt.get("reboot", 0)
        blocked = evt.get("blocked", 0)
        cancelled = evt.get("cancelled", False)

        self._log(f"=== 完成 ===", "info")
        self._log(f"✓ 已删除: {deleted}", "success")
        if reboot: self._log(f"⏳ 重启删除: {reboot}", "warn")
        if blocked: self._log(f"🚫 已拦截: {blocked}", "error")
        if failed: self._log(f"✗ 失败: {failed}", "error")
        if cancelled: self._log("已取消", "warn")

        self.delete_btn.setEnabled(True)
        self.delete_btn.setText("🗑️  开始粉碎删除")
        self.cancel_btn.setVisible(False)
        self.progress.setVisible(False)

        if failed == 0 and not cancelled:
            QMessageBox.information(self, "完成", f"删除完成！\n\n已删除: {deleted}\n重启删除: {reboot}")
        elif cancelled:
            QMessageBox.information(self, "已取消", "操作已取消")
        else:
            QMessageBox.warning(self, "部分失败", f"部分文件删除失败\n\n已删除: {deleted}\n失败: {failed}\n重启删除: {reboot}\n\n请查看日志了解详情")

    def _cancel_delete(self):
        if self.worker:
            self.worker.cancel()
            self._log("正在取消...", "warn")


def run_gui():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
