# -*- coding: utf-8 -*-
"""文件粉碎工具 v2.0 - 程序入口"""

import sys
import os


def main():
    # Worker 模式
    if len(sys.argv) >= 3 and sys.argv[1] == "--worker":
        import worker
        sys.exit(worker.run_worker(sys.argv[2]))

    # GUI 模式
    import gui
    gui.run_gui()


if __name__ == "__main__":
    main()
