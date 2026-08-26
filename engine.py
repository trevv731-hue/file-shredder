# -*- coding: utf-8 -*-
"""递进式删除引擎 - 增强版（智能模式+多轮重试+动态策略）"""

import os
import time
import shutil
import stat
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Tuple

import winapi


@dataclass
class Options:
    unlock_handles: bool = True
    kill_processes: bool = False
    take_ownership: bool = True
    schedule_reboot: bool = True
    shred: bool = False
    smart_mode: bool = True       # 智能模式：动态策略+多轮重试
    force_mode: bool = False       # 强力模式：绕过安全护栏
    max_retries: int = 3           # 每种方法最大重试次数


@dataclass
class DeleteResult:
    path: str
    status: str = "pending"
    level: int = -1
    message: str = ""
    killed_pids: list = field(default_factory=list)
    attempts: list = field(default_factory=list)  # 每次尝试的记录


@dataclass
class AttemptRecord:
    method: str
    level: int
    success: bool
    error: str = ""
    timestamp: float = 0.0


def _norm(path):
    p = os.path.abspath(path)
    p = winapi.get_final_path(p)
    p = p.replace("/", "\\").rstrip("\\")
    if p.startswith("\\\\?\\"): p = p[4:]
    if p.upper().startswith("\\\\?\\UNC\\"): p = "\\" + p[8:]
    return p


def is_protected(path):
    try:
        p = _norm(path).lower()
        drive = os.path.splitdrive(p)[0].lower()
        sys_drive = os.environ.get("SystemDrive", "C:").lower()
        subtree_protected = []
        for d in "cdefghijklmnopqrstuvwxyz":
            subtree_protected.append(f"{d}:\\windows")
        subtree_protected.extend([f"{sys_drive}\\boot", f"{sys_drive}\\efi", f"{sys_drive}\\recovery", f"{sys_drive}\\config.msi"])
        for d in "cdefghijklmnopqrstuvwxyz":
            subtree_protected.append(f"{d}:\\system volume information")
        for prot in subtree_protected:
            if p == prot or p.startswith(prot + "\\"):
                return True, f"系统关键目录: {prot}"
        root_protected = []
        for d in "cdefghijklmnopqrstuvwxyz":
            root_protected.append(f"{d}:")
        for d in "cdefghijklmnopqrstuvwxyz":
            root_protected.append(f"{d}:\\$recycle.bin")
        root_protected.extend([f"{sys_drive}\\users", f"{sys_drive}\\programdata", f"{sys_drive}\\program files", f"{sys_drive}\\program files (x86)", f"{sys_drive}\\perflogs"])
        root_protected.append(os.path.expanduser("~").lower().rstrip("\\"))
        if getattr(__import__('sys'), 'frozen', False):
            root_protected.append(os.path.dirname(os.path.abspath(__import__('sys').executable)).lower())
        else:
            root_protected.append(os.path.dirname(os.path.abspath(__file__)).lower())
        for prot in root_protected:
            if p == prot: return True, f"受保护的根目录: {prot}"
        if p.startswith("\\\\"):
            parts = p.split("\\")
            if len(parts) <= 4: return True, "UNC共享根目录"
        return False, ""
    except:
        return False, ""


def _shred_file(path, passes=3):
    try:
        size = os.path.getsize(path)
        with open(path, "r+b") as f:
            for i in range(passes):
                f.seek(0)
                pat = b'\x00' if i == passes-1 else (b'\xFF' if i == passes-2 else os.urandom(1))
                chunk = pat * min(65536, max(size, 1))
                remaining = size
                while remaining > 0:
                    w = min(len(chunk), remaining)
                    f.write(chunk[:w])
                    remaining -= w
                f.flush()
        return True
    except: return False


def _try_method(path, method_name, level, func, log, result):
    """尝试一种删除方法，记录结果"""
    for attempt in range(3):  # 每种方法最多重试3次
        try:
            log(f"  [L{level}] {method_name}" + (f" (第{attempt+1}次)" if attempt > 0 else ""))
            func(path)
            time.sleep(0.15)
            if not os.path.exists(path):
                rec = AttemptRecord(method=method_name, level=level, success=True, timestamp=time.time())
                result.attempts.append(rec)
                return True
        except Exception as e:
            rec = AttemptRecord(method=method_name, level=level, success=False, error=str(e), timestamp=time.time())
            result.attempts.append(rec)
            log(f"  L{level} {method_name} 失败: {e}")
            time.sleep(0.1)
    return False


def _smart_delete_single(path, opts, log, result):
    """智能删除单个文件/目录 - 模拟AI的动态策略"""
    # 方法链：(方法名, 级别, 函数, 前置条件)
    methods = [
        ("清除属性", 0, lambda p: winapi.clear_file_attributes(p), True),
        ("POSIX删除", 1, lambda p: winapi.posix_delete(p), True),
        ("常规删除", 2, lambda p: (winapi.regular_delete(p) if not os.path.isdir(p) else (os.rmdir(p) if os.path.isdir(p) else None)), True),
        ("Python删除", 2, lambda p: (os.remove(p) if os.path.isfile(p) or os.path.islink(p) else os.rmdir(p)), True),
        ("夺取所有权", 3, lambda p: winapi.take_ownership_and_grant(p), opts.take_ownership),
        ("夺权限后POSIX", 3, lambda p: (winapi.clear_file_attributes(p), winapi.posix_delete(p)), opts.take_ownership),
        ("夺权限后常规", 3, lambda p: (winapi.clear_file_attributes(p), winapi.regular_delete(p)), opts.take_ownership),
        ("关闭远程句柄", 4, lambda p: winapi.close_remote_handle(p), opts.unlock_handles),
        ("关句柄后POSIX", 4, lambda p: (winapi.clear_file_attributes(p), winapi.posix_delete(p)), opts.unlock_handles),
        ("关句柄后常规", 4, lambda p: (winapi.clear_file_attributes(p), winapi.regular_delete(p)), opts.unlock_handles),
        ("NtDeleteFile", 45, lambda p: winapi.nt_delete_file(p), opts.unlock_handles),
        ("NtDelete后POSIX", 45, lambda p: (winapi.clear_file_attributes(p), winapi.posix_delete(p)), opts.unlock_handles),
        ("DELETE_ON_CLOSE", 46, lambda p: winapi.delete_on_close(p), opts.unlock_handles),
        ("DOC后常规", 46, lambda p: (winapi.clear_file_attributes(p), winapi.regular_delete(p)), opts.unlock_handles),
        ("卸载内存映射", 47, lambda p: winapi.unmap_mapped_sections(p), opts.unlock_handles and os.path.isfile(p)),
        ("卸载后POSIX", 47, lambda p: (winapi.clear_file_attributes(p), winapi.posix_delete(p)), opts.unlock_handles and os.path.isfile(p)),
        ("RestartManager查占用", 5, lambda p: _rm_find_and_log(p, log), opts.kill_processes),
        ("终止占用进程树", 5, lambda p: _kill_locking_processes(p, log, result), opts.kill_processes),
        ("杀进程后POSIX", 5, lambda p: (winapi.clear_file_attributes(p), winapi.posix_delete(p)), opts.kill_processes),
        ("杀进程后NtDelete", 5, lambda p: winapi.nt_delete_file(p), opts.kill_processes),
        ("杀进程后常规", 5, lambda p: (winapi.clear_file_attributes(p), winapi.regular_delete(p)), opts.kill_processes),
    ]

    # 多轮重试：最多3轮完整方法链
    for round_num in range(opts.max_retries):
        if round_num > 0:
            log(f"  === 第{round_num+1}轮重试 ===")
            time.sleep(0.3)

        for method_name, level, func, condition in methods:
            if not condition:
                continue
            if os.path.exists(path):
                if _try_method(path, method_name, level, func, log, result):
                    result.status = "deleted"
                    result.level = level
                    result.message = f"通过{method_name}删除成功"
                    return True
            else:
                return True

    # 所有方法都失败，尝试重启删除兜底
    if opts.schedule_reboot and os.path.exists(path):
        log("  [L6] 登记重启时删除（最终兜底）")
        if winapi.schedule_delete_on_reboot(path):
            result.status = "reboot"
            result.level = 6
            result.message = "已登记，下次重启时删除"
            return True

    result.status = "failed"
    result.message = "所有删除手段均失败"
    return False


def _rm_find_and_log(path, log):
    procs = winapi.find_locking_processes([path])
    if procs:
        for pid, name, atype, restartable in procs:
            log(f"  占用进程: PID {pid} {name} [{atype}]")
    return procs


def _kill_locking_processes(path, log, result):
    procs = winapi.find_locking_processes([path])
    killed = []
    for pid, name, atype, restartable in procs:
        log(f"  终止进程树: PID {pid} {name}")
        if winapi.kill_process_tree(pid):
            killed.append(pid)
    result.killed_pids.extend(killed)
    time.sleep(0.3)
    return killed


def delete_path(path, opts, log=print, cancel_check=None):
    """删除文件或文件夹（递归）"""
    if not os.path.exists(path) and not os.path.islink(path):
        return DeleteResult(path, "deleted", -1, "已不存在")

    # 护栏检查（强力模式绕过）
    if not opts.force_mode:
        protected, reason = is_protected(path)
        if protected:
            log(f"[拦截] {path}: {reason}")
            return DeleteResult(path, "blocked", -1, reason)
    else:
        log(f"[强力模式] 绕过安全护栏: {path}")

    log(f"处理: {path}")
    result = DeleteResult(path=path)

    # 粉碎覆写
    if opts.shred and os.path.isfile(path):
        log(f"  覆写文件内容: {path}")
        _shred_file(path)

    if os.path.isdir(path) and not os.path.islink(path):
        # 递归删除目录内容
        try:
            entries = list(os.walk(path, topdown=False))
        except Exception as e:
            log(f"  遍历目录失败: {e}")
            entries = []

        all_ok = True
        reboot_scheduled = False

        for root, dirs, files in entries:
            if cancel_check and cancel_check():
                result.status = "failed"
                result.message = "用户取消"
                return result
            for name in files:
                fp = os.path.join(root, name)
                if opts.shred:
                    log(f"  覆写: {fp}")
                    _shred_file(fp)
                sub_result = DeleteResult(path=fp)
                if opts.smart_mode:
                    _smart_delete_single(fp, opts, log, sub_result)
                else:
                    _legacy_delete_single(fp, opts, log, sub_result)
                if sub_result.status == "failed": all_ok = False
                elif sub_result.status == "reboot": reboot_scheduled = True
                elif sub_result.status == "blocked": all_ok = False
            for name in dirs:
                dp = os.path.join(root, name)
                sub_result = DeleteResult(path=dp)
                if opts.smart_mode:
                    _smart_delete_single(dp, opts, log, sub_result)
                else:
                    _legacy_delete_single(dp, opts, log, sub_result)
                if sub_result.status == "failed": all_ok = False
                elif sub_result.status == "reboot": reboot_scheduled = True

        # 删除目录本身
        if os.path.exists(path):
            if opts.smart_mode:
                _smart_delete_single(path, opts, log, result)
            else:
                _legacy_delete_single(path, opts, log, result)

        if result.status == "deleted":
            return result
        elif reboot_scheduled and not os.path.exists(path):
            result.status = "deleted"
            result.level = 6
            return result
        elif reboot_scheduled:
            if opts.schedule_reboot and winapi.schedule_delete_on_reboot(path):
                result.status = "reboot"
                result.level = 6
                result.message = "部分文件已登记重启删除"
                return result
            result.status = "reboot"
            result.level = 6
            result.message = "部分文件已登记重启删除"
            return result
        else:
            result.status = "failed"
            result.message = "部分文件删除失败"
            return result
    else:
        if opts.smart_mode:
            _smart_delete_single(path, opts, log, result)
        else:
            _legacy_delete_single(path, opts, log, result)
        return result


def _legacy_delete_single(path, opts, log, result):
    """旧版固定删除链（兼容模式）"""
    winapi.clear_file_attributes(path)
    if winapi.posix_delete(path):
        time.sleep(0.1)
        if not os.path.exists(path):
            result.status = "deleted"; result.level = 1; return
    if winapi.regular_delete(path):
        if not os.path.exists(path):
            result.status = "deleted"; result.level = 2; return
    try:
        if os.path.isfile(path) or os.path.islink(path): os.remove(path)
        elif os.path.isdir(path): os.rmdir(path)
        if not os.path.exists(path):
            result.status = "deleted"; result.level = 2; return
    except: pass
    if opts.take_ownership:
        winapi.take_ownership_and_grant(path)
        winapi.clear_file_attributes(path)
        if winapi.posix_delete(path):
            time.sleep(0.1)
            if not os.path.exists(path): result.status = "deleted"; result.level = 3; return
    if opts.unlock_handles:
        winapi.close_remote_handle(path)
        time.sleep(0.2)
        winapi.clear_file_attributes(path)
        if winapi.posix_delete(path):
            time.sleep(0.1)
            if not os.path.exists(path): result.status = "deleted"; result.level = 4; return
        winapi.nt_delete_file(path)
        if not os.path.exists(path): result.status = "deleted"; result.level = 45; return
        winapi.delete_on_close(path)
        if not os.path.exists(path): result.status = "deleted"; result.level = 46; return
    if opts.kill_processes:
        procs = winapi.find_locking_processes([path])
        for pid, name, atype, r in procs:
            winapi.kill_process_tree(pid)
            result.killed_pids.append(pid)
        time.sleep(0.3)
        winapi.clear_file_attributes(path)
        if winapi.posix_delete(path):
            time.sleep(0.1)
            if not os.path.exists(path): result.status = "deleted"; result.level = 5; return
    if opts.schedule_reboot:
        if winapi.schedule_delete_on_reboot(path):
            result.status = "reboot"; result.level = 6; result.message = "已登记重启删除"; return
    result.status = "failed"
    result.message = "所有删除手段均失败"


def scan_locks(paths):
    return winapi.find_locking_processes(paths)
