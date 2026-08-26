# -*- coding: utf-8 -*-
"""递进式删除引擎 L0-L6 + 安全护栏"""

import os
import time
import shutil
from dataclasses import dataclass, field
from typing import Callable, Optional

import winapi


@dataclass
class Options:
    unlock_handles: bool = True   # L4: 强制关闭占用句柄
    kill_processes: bool = False  # L5: 结束占用进程
    take_ownership: bool = True   # L3: 接管所有权
    schedule_reboot: bool = True  # L6: 重启时删除兜底
    shred: bool = False           # 删除前覆写


@dataclass
class DeleteResult:
    path: str
    status: str = "pending"  # deleted / reboot / failed / blocked / skipped
    level: int = -1
    message: str = ""
    killed_pids: list = field(default_factory=list)


def _norm(path):
    """规范化路径用于护栏比对"""
    p = os.path.abspath(path)
    p = winapi.get_final_path(p)
    p = p.replace("/", "\\").rstrip("\\")
    # 处理 \\?\ 前缀
    if p.startswith("\\\\?\\"):
        p = p[4:]
    if p.upper().startswith("\\\\?\\UNC\\"):
        p = "\\" + p[8:]
    return p


def is_protected(path):
    """
    检查路径是否受保护（不允许删除）
    返回 (bool, reason)
    """
    try:
        p = _norm(path).lower()
        drive = os.path.splitdrive(p)[0].lower()
        sys_drive = os.environ.get("SystemDrive", "C:").lower()

        # === 整棵子树保护 ===
        subtree_protected = []
        # 任意盘符下的 Windows 目录
        for d in "cdefghijklmnopqrstuvwxyz":
            subtree_protected.append(f"{d}:\\windows")
        # 系统盘关键目录
        subtree_protected.extend([
            f"{sys_drive}\\boot",
            f"{sys_drive}\\efi",
            f"{sys_drive}\\recovery",
            f"{sys_drive}\\config.msi",
        ])
        # 任意盘的 System Volume Information
        for d in "cdefghijklmnopqrstuvwxyz":
            subtree_protected.append(f"{d}:\\system volume information")

        for prot in subtree_protected:
            if p == prot or p.startswith(prot + "\\"):
                return True, f"系统关键目录: {prot}"

        # === 整体根保护（目录本身不许删，子目录可以）===
        root_protected = []
        # 所有卷根
        for d in "cdefghijklmnopqrstuvwxyz":
            root_protected.append(f"{d}:")
        # 回收站
        for d in "cdefghijklmnopqrstuvwxyz":
            root_protected.append(f"{d}:\\$recycle.bin")
        # 系统盘关键根目录
        root_protected.extend([
            f"{sys_drive}\\users",
            f"{sys_drive}\\programdata",
            f"{sys_drive}\\program files",
            f"{sys_drive}\\program files (x86)",
            f"{sys_drive}\\perflogs",
        ])
        # 当前用户主目录
        root_protected.append(os.path.expanduser("~").lower().rstrip("\\"))
        # 本程序所在目录
        if getattr(__import__('sys'), 'frozen', False):
            root_protected.append(os.path.dirname(os.path.abspath(__import__('sys').executable)).lower())
        else:
            root_protected.append(os.path.dirname(os.path.abspath(__file__)).lower())

        for prot in root_protected:
            if p == prot:
                return True, f"受保护的根目录: {prot}"

        # UNC 共享根
        if p.startswith("\\\\"):
            parts = p.split("\\")
            if len(parts) <= 4:  # \\server\share 级别
                return True, "UNC共享根目录"

        return False, ""
    except Exception as e:
        return False, ""


def _shred_file(path, passes=3):
    """覆写文件内容"""
    try:
        size = os.path.getsize(path)
        with open(path, "r+b") as f:
            for i in range(passes):
                f.seek(0)
                if i == passes - 1:
                    pat = b'\x00'
                elif i == passes - 2:
                    pat = b'\xFF'
                else:
                    pat = os.urandom(1)
                chunk = pat * min(65536, max(size, 1))
                remaining = size
                while remaining > 0:
                    w = min(len(chunk), remaining)
                    f.write(chunk[:w])
                    remaining -= w
                f.flush()
        return True
    except:
        return False


def _try_delete_file(path, opts, log):
    """对单个文件执行 L0-L6 删除链"""
    if not os.path.exists(path) and not os.path.islink(path):
        return DeleteResult(path, "deleted", -1, "已不存在")

    # 护栏检查
    protected, reason = is_protected(path)
    if protected:
        return DeleteResult(path, "blocked", -1, f"安全护栏拦截: {reason}")

    # 粉碎覆写
    if opts.shred and os.path.isfile(path):
        log(f"  覆写文件内容: {path}")
        _shred_file(path)

    # L0: 清除属性
    log(f"  [L0] 清除文件属性")
    winapi.clear_file_attributes(path)

    # L1: POSIX 语义删除
    log(f"  [L1] POSIX语义删除")
    if winapi.posix_delete(path):
        if not os.path.exists(path):
            return DeleteResult(path, "deleted", 1)
    # L1 标记后句柄关闭才生效，等一下
    time.sleep(0.1)
    if not os.path.exists(path):
        return DeleteResult(path, "deleted", 1)

    # L2: 常规删除
    log(f"  [L2] 常规删除")
    if winapi.regular_delete(path):
        if not os.path.exists(path):
            return DeleteResult(path, "deleted", 2)
    try:
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)
        if not os.path.exists(path):
            return DeleteResult(path, "deleted", 2)
    except:
        pass

    # L3: 夺取所有权
    if opts.take_ownership:
        log(f"  [L3] 接管所有权与权限")
        if winapi.take_ownership_and_grant(path):
            winapi.clear_file_attributes(path)
            if winapi.posix_delete(path):
                time.sleep(0.1)
                if not os.path.exists(path):
                    return DeleteResult(path, "deleted", 3)
            if winapi.regular_delete(path):
                if not os.path.exists(path):
                    return DeleteResult(path, "deleted", 3)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    os.rmdir(path)
                if not os.path.exists(path):
                    return DeleteResult(path, "deleted", 3)
            except:
                pass

    # L4: 关闭远程句柄
    if opts.unlock_handles:
        log(f"  [L4] 强制关闭占用句柄")
        closed = winapi.close_remote_handle(path)
        if closed > 0:
            log(f"  已关闭 {closed} 个远程句柄")
            time.sleep(0.2)
            winapi.clear_file_attributes(path)
            if winapi.posix_delete(path):
                time.sleep(0.1)
                if not os.path.exists(path):
                    return DeleteResult(path, "deleted", 4)
            if winapi.regular_delete(path):
                if not os.path.exists(path):
                    return DeleteResult(path, "deleted", 4)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    os.rmdir(path)
                if not os.path.exists(path):
                    return DeleteResult(path, "deleted", 4)
            except:
                pass

    # L4.5: NtDeleteFile 原生 API（绕过 Win32 层）
    if opts.unlock_handles:
        log(f"  [L4.5] NtDeleteFile 原生删除")
        winapi.clear_file_attributes(path)
        if winapi.nt_delete_file(path):
            time.sleep(0.1)
            if not os.path.exists(path):
                return DeleteResult(path, "deleted", 45)
        # 再试 POSIX + 常规
        if winapi.posix_delete(path):
            time.sleep(0.1)
            if not os.path.exists(path):
                return DeleteResult(path, "deleted", 45)
        if winapi.regular_delete(path):
            if not os.path.exists(path):
                return DeleteResult(path, "deleted", 45)

    # L4.6: FILE_FLAG_DELETE_ON_CLOSE（等所有句柄关闭后自动删除）
    if opts.unlock_handles:
        log(f"  [L4.6] DELETE_ON_CLOSE 标记")
        if winapi.delete_on_close(path):
            time.sleep(0.2)
            if not os.path.exists(path):
                return DeleteResult(path, "deleted", 46)
            # 文件可能等其他进程句柄关闭后才消失，再试常规删除
            winapi.clear_file_attributes(path)
            if winapi.regular_delete(path):
                if not os.path.exists(path):
                    return DeleteResult(path, "deleted", 46)

    # L4.7: 卸载内存映射（被 LoadLibrary 加载的 DLL/EXE）
    if opts.unlock_handles and (os.path.isfile(path)):
        log(f"  [L4.7] 卸载内存映射")
        unmapped = winapi.unmap_mapped_sections(path)
        if unmapped > 0:
            log(f"  已卸载 {unmapped} 个内存映射")
            time.sleep(0.2)
            winapi.clear_file_attributes(path)
            if winapi.posix_delete(path):
                time.sleep(0.1)
                if not os.path.exists(path):
                    return DeleteResult(path, "deleted", 47)
            if winapi.regular_delete(path):
                if not os.path.exists(path):
                    return DeleteResult(path, "deleted", 47)
            try:
                os.remove(path)
                if not os.path.exists(path):
                    return DeleteResult(path, "deleted", 47)
            except:
                pass

    # L5: Restart Manager 结束进程（强制终止进程树）
    if opts.kill_processes:
        log(f"  [L5] 查找并终止占用进程")
        procs = winapi.find_locking_processes([path])
        killed = []
        for pid, name, atype, restartable in procs:
            log(f"  占用进程: PID {pid} {name}")
            if winapi.kill_process_tree(pid):
                killed.append(pid)
        if killed:
            log(f"  已终止进程: {killed}")
            time.sleep(0.3)
            winapi.clear_file_attributes(path)
            # 终止后尝试所有删除手段
            for attempt_name, attempt_fn in [
                ("POSIX", winapi.posix_delete),
                ("NtDeleteFile", winapi.nt_delete_file),
                ("常规", winapi.regular_delete),
            ]:
                try:
                    attempt_fn(path)
                    time.sleep(0.1)
                    if not os.path.exists(path):
                        result = DeleteResult(path, "deleted", 5)
                        result.killed_pids = killed
                        return result
                except:
                    pass
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    os.rmdir(path)
                if not os.path.exists(path):
                    result = DeleteResult(path, "deleted", 5)
                    result.killed_pids = killed
                    return result
            except:
                pass

    # L6: 重启时删除
    if opts.schedule_reboot:
        log(f"  [L6] 登记重启时删除")
        if winapi.schedule_delete_on_reboot(path):
            return DeleteResult(path, "reboot", 6, "已登记，下次重启时删除")

    return DeleteResult(path, "failed", -1, "所有删除手段均失败")


def delete_path(path, opts, log=print, cancel_check=None):
    """
    删除文件或文件夹（递归），返回 DeleteResult
    log: 日志回调
    cancel_check: 返回True时取消
    """
    if not os.path.exists(path) and not os.path.islink(path):
        return DeleteResult(path, "deleted", -1, "已不存在")

    # 护栏检查
    protected, reason = is_protected(path)
    if protected:
        log(f"[拦截] {path}: {reason}")
        return DeleteResult(path, "blocked", -1, reason)

    log(f"处理: {path}")

    if os.path.isdir(path) and not os.path.islink(path):
        # 递归删除目录内容
        all_ok = True
        reboot_scheduled = False
        try:
            entries = list(os.walk(path, topdown=False))
        except Exception as e:
            log(f"  遍历目录失败: {e}")
            entries = []

        for root, dirs, files in entries:
            if cancel_check and cancel_check():
                return DeleteResult(path, "failed", -1, "用户取消")
            for name in files:
                fp = os.path.join(root, name)
                r = _try_delete_file(fp, opts, log)
                if r.status == "failed":
                    all_ok = False
                elif r.status == "reboot":
                    reboot_scheduled = True
                elif r.status == "blocked":
                    all_ok = False
            for name in dirs:
                dp = os.path.join(root, name)
                if cancel_check and cancel_check():
                    return DeleteResult(path, "failed", -1, "用户取消")
                r = _try_delete_file(dp, opts, log)
                if r.status == "failed":
                    all_ok = False
                elif r.status == "reboot":
                    reboot_scheduled = True

        # 删除目录本身
        if all_ok and os.path.exists(path):
            r = _try_delete_file(path, opts, log)
            if r.status == "deleted":
                return r
            elif r.status == "reboot":
                return r
            else:
                return r
        elif reboot_scheduled and not os.path.exists(path):
            return DeleteResult(path, "deleted", 6)
        elif reboot_scheduled:
            # 尝试登记目录本身重启删除
            if opts.schedule_reboot and winapi.schedule_delete_on_reboot(path):
                return DeleteResult(path, "reboot", 6, "已登记，下次重启时删除")
            return DeleteResult(path, "reboot", 6, "部分文件已登记重启删除")
        else:
            return DeleteResult(path, "failed", -1, "部分文件删除失败")
    else:
        return _try_delete_file(path, opts, log)


def scan_locks(paths):
    """扫描占用进程（不删除）"""
    return winapi.find_locking_processes(paths)
