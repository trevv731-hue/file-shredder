# -*- coding: utf-8 -*-
"""文件粉碎工具 - 入口"""

import sys
import os

# 确保能找到同目录模块
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)


def main():
    # worker 模式：由提权子进程调用
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker":
        from worker import run_worker
        sys.exit(run_worker(sys.argv[2]))

    # GUI 模式
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QTimer
    from gui import MainWindow

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()

    # 确保窗口在最前面
    QTimer.singleShot(100, lambda: (
        window.raise_(),
        window.activateWindow(),
        window.setWindowState(window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
    ))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
