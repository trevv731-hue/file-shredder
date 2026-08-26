# -*- coding: utf-8 -*-
"""提权工作进程"""

import os
import sys
import json
import time
import tempfile

import winapi
import engine


def emit(out_path, event):
    try:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()
    except: pass


def run_worker(task_file):
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

    try: open(out_path, "w").close()
    except: pass

    if kind == "scan":
        emit(out_path, {"t": "log", "m": f"扫描 {len(targets)} 个目标的占用进程...", "l": "info"})
        procs = winapi.find_locking_processes(targets)
        for pid, name, atype, restartable in procs:
            emit(out_path, {"t": "proc", "pid": pid, "name": name, "type": atype, "restartable": restartable, "count": 1})
        emit(out_path, {"t": "end", "ok": True, "found": len(procs)})
        return 0

    emit(out_path, {"t": "log", "m": f"开始删除 {len(targets)} 个目标" + (" [智能模式]" if opts.smart_mode else "") + (" [强力模式]" if opts.force_mode else ""), "l": "info"})
    emit(out_path, {"t": "prog", "d": 0, "n": len(targets)})

    winapi.enable_all_privileges()

    ok_count = 0
    fail_count = 0
    blocked_count = 0
    reboot_count = 0
    cancelled = False

    for i, target in enumerate(targets):
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
                        "killed": result.killed_pids, "attempts": len(result.attempts)})

        if result.status == "deleted":
            ok_count += 1
            emit(out_path, {"t": "log", "m": f"✓ 已删除 (L{result.level}): {target}", "l": "success"})
        elif result.status == "reboot":
            reboot_count += 1
            emit(out_path, {"t": "log", "m": f"⏳ 已登记重启删除: {target}", "l": "warn"})
        elif result.status == "blocked":
            blocked_count += 1
            emit(out_path, {"t": "log", "m": f"🚫 已拦截: {target} - {result.message}", "l": "error"})
        else:
            fail_count += 1
            emit(out_path, {"t": "log", "m": f"✗ 删除失败: {target} - {result.message}", "l": "error"})

        emit(out_path, {"t": "prog", "d": i + 1, "n": len(targets)})

    emit(out_path, {"t": "end", "ok": fail_count == 0 and not cancelled,
                    "deleted": ok_count, "reboot": reboot_count,
                    "failed": fail_count, "blocked": blocked_count,
                    "cancelled": cancelled})

    try: os.remove(task_file)
    except: pass

    return 0 if fail_count == 0 and not cancelled else 1


def write_task(targets, options, kind="delete"):
    task_file = os.path.join(tempfile.gettempdir(), f"fdf_task_{os.getpid()}_{int(time.time()*1000)}.json")
    out_path = task_file + ".jsonl"
    task = {"kind": kind, "targets": targets, "options": options, "out": out_path}
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task, f, ensure_ascii=False)
    return task_file, out_path


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "--worker":
        print("Usage: python worker.py --worker <task_file>", file=sys.stderr)
        sys.exit(1)
    sys.exit(run_worker(sys.argv[2]))
