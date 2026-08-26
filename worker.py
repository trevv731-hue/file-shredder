# -*- coding: utf-8 -*-
"""提权工作进程：接收JSON任务，执行删除，输出JSONL日志"""

import os
import sys
import json
import time
import tempfile

import winapi
import engine


def emit(out_path, event):
    """向JSONL文件写入一个事件"""
    try:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()
    except:
        pass


def run_worker(task_file):
    """worker主函数"""
    try:
        with open(task_file, "r", encoding="utf-8") as f:
            task = json.load(f)
    except Exception as e:
        print(f"无法读取任务文件: {e}", file=sys.stderr)
        return 1

    kind = task.get("kind", "delete")
    targets = task.get("targets", [])
    out_path = task.get("out", os.path.join(tempfile.gettempdir(), "fdf_worker.jsonl"))
    opts_dict = task.get("options", {})
    opts = engine.Options(**opts_dict)

    # 清空输出文件
    try:
        open(out_path, "w").close()
    except:
        pass

    if kind == "scan":
        # 只扫描占用进程
        emit(out_path, {"t": "log", "m": f"扫描 {len(targets)} 个目标的占用进程...", "l": "info"})
        procs = winapi.find_locking_processes(targets)
        for pid, name, atype, restartable in procs:
            emit(out_path, {"t": "proc", "pid": pid, "name": name, "type": atype,
                            "restartable": restartable, "count": 1})
        emit(out_path, {"t": "end", "ok": True, "found": len(procs)})
        return 0

    # 删除任务
    emit(out_path, {"t": "log", "m": f"开始删除 {len(targets)} 个目标", "l": "info"})
    emit(out_path, {"t": "prog", "d": 0, "n": len(targets)})

    # 启用特权
    winapi.enable_all_privileges()

    ok_count = 0
    fail_count = 0
    blocked_count = 0
    reboot_count = 0
    cancelled = False

    for i, target in enumerate(targets):
        # 检查取消标记
        cancel_file = task_file + ".cancel"
        if os.path.exists(cancel_file):
            cancelled = True
            emit(out_path, {"t": "log", "m": "用户取消", "l": "warn"})
            break

        def log(msg, level="info"):
            emit(out_path, {"t": "log", "m": msg, "l": level})

        try:
            result = engine.delete_path(target, opts, log=log)
        except Exception as e:
            result = engine.DeleteResult(target, "failed", -1, str(e))

        emit(out_path, {"t": "res", "path": target, "status": result.status,
                        "level": result.level, "message": result.message,
                        "killed": result.killed_pids})

        if result.status == "deleted":
            ok_count += 1
            emit(out_path, {"t": "log", "m": f"已删除: {target}", "l": "info"})
        elif result.status == "reboot":
            reboot_count += 1
            emit(out_path, {"t": "log", "m": f"已登记重启删除: {target}", "l": "warn"})
        elif result.status == "blocked":
            blocked_count += 1
            emit(out_path, {"t": "log", "m": f"已拦截: {target} - {result.message}", "l": "error"})
        else:
            fail_count += 1
            emit(out_path, {"t": "log", "m": f"删除失败: {target} - {result.message}", "l": "error"})

        emit(out_path, {"t": "prog", "d": i + 1, "n": len(targets)})

    emit(out_path, {"t": "end", "ok": fail_count == 0 and not cancelled,
                    "deleted": ok_count, "reboot": reboot_count,
                    "failed": fail_count, "blocked": blocked_count,
                    "cancelled": cancelled})

    # 清理任务文件
    try:
        os.remove(task_file)
    except:
        pass

    return 0 if fail_count == 0 and not cancelled else 1


def write_task(targets, options, kind="delete"):
    """创建任务文件并返回路径和输出文件路径"""
    task_file = os.path.join(tempfile.gettempdir(), f"fdf_task_{os.getpid()}_{int(time.time()*1000)}.json")
    out_path = task_file + ".jsonl"
    task = {
        "kind": kind,
        "targets": targets,
        "options": options,
        "out": out_path,
    }
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task, f, ensure_ascii=False)
    return task_file, out_path


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "--worker":
        print("Usage: python worker.py --worker <task_file>", file=sys.stderr)
        sys.exit(1)
    sys.exit(run_worker(sys.argv[2]))
