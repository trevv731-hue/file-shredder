# -*- coding: utf-8 -*-
"""Win32 API ctypes 封装"""

import os
import ctypes
from ctypes import wintypes

# ==================== 常量 ====================

# 文件属性
FILE_ATTRIBUTE_READONLY = 0x00000001
FILE_ATTRIBUTE_HIDDEN = 0x00000002
FILE_ATTRIBUTE_SYSTEM = 0x00000004
FILE_ATTRIBUTE_DIRECTORY = 0x00000010
FILE_ATTRIBUTE_ARCHIVE = 0x00000020
FILE_ATTRIBUTE_NORMAL = 0x00000080

# CreateFile 常量
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
DELETE = 0x00010000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
FILE_FLAG_DELETE_ON_CLOSE = 0x04000000
FILE_FLAG_POSIX_SEMANTICS = 0x01000000
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

# CreateFile disposition
CREATE_NEW = 1
CREATE_ALWAYS = 2
OPEN_ALWAYS = 3
TRUNCATE_EXISTING = 4

# OBJECT_ATTRIBUTES 常量
OBJ_CASE_INSENSITIVE = 0x00000040
OBJ_INHERIT = 0x00000002

# Process access rights for module enumeration
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_WRITE = 0x0020

# Section access for unmap
SECTION_MAP_WRITE = 0x0002
SECTION_MAP_READ = 0x0004
SECTION_MAP_EXECUTE = 0x0008
SECTION_ALL_ACCESS = 0x10000000

# 关键系统进程PID/名称，绝不碰
CRITICAL_PIDS = {0, 4}  # System Idle, System
CRITICAL_NAMES = {
    "smss.exe", "csrss.exe", "wininit.exe", "winlogon.exe",
    "services.exe", "lsass.exe", "lsm.exe", "svchost.exe",
    "fontdrvhost.exe", "dwm.exe", "ntoskrnl.exe",
}

# FileInformationClass
FileDispositionInformation = 13
FileDispositionInformationEx = 64

# FILE_DISPOSITION_INFO_EX 标志
FILE_DISPOSITION_DELETE = 0x00000001
FILE_DISPOSITION_POSIX_SEMANTICS = 0x00000002
FILE_DISPOSITION_FORCE_IMAGE_SECTION_CHECK = 0x00000004
FILE_DISPOSITION_ON_CLOSE = 0x00000008
FILE_DISPOSITION_IGNORE_READONLY_ATTRIBUTE = 0x00000010

# 安全信息
OWNER_SECURITY_INFORMATION = 0x00000001
GROUP_SECURITY_INFORMATION = 0x00000002
DACL_SECURITY_INFORMATION = 0x00000004
SACL_SECURITY_INFORMATION = 0x00000008

# NTSTATUS
STATUS_SUCCESS = 0x00000000
STATUS_INFO_LENGTH_MISMATCH = 0xC0000004
STATUS_BUFFER_OVERFLOW = 0x80000005

# 系统信息类
SystemHandleInformation = 16
SystemExtendedHandleInformation = 64

# 对象信息类
ObjectTypeInformation = 2
ObjectNameInformation = 1

# 句柄掩码
PROCESS_DUP_HANDLE = 0x0040

# 特权
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008

# MoveFileEx
MOVEFILE_DELAY_UNTIL_REBOOT = 0x00000004

# Restart Manager
CCH_RM_MAX_APP_NAME = 255
CCH_RM_MAX_SVC_NAME = 63
RM_INVALID_SESSION = 0xFFFFFFFF
ERROR_MORE_DATA = 234
RmRebootReasonNone = 0

RM_APP_TYPE = {
    0: "未知应用", 1: "控制台应用", 2: "Windows应用",
    3: "Windows服务", 4: "资源管理器", 5: "控制台应用",
    6: "Windows应用", 7: "Windows服务",
}

# ==================== 结构体 ====================

class FILE_DISPOSITION_INFO_EX(ctypes.Structure):
    _fields_ = [("Flags", wintypes.DWORD)]

class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [("PrivilegeCount", wintypes.DWORD),
                ("Privileges", LUID_AND_ATTRIBUTES * 1)]

class SECURITY_DESCRIPTOR(ctypes.Structure):
    _fields_ = [
        ("Revision", wintypes.BYTE),
        ("Sbz1", wintypes.BYTE),
        ("Control", wintypes.WORD),
        ("Owner", ctypes.c_void_p),
        ("Group", ctypes.c_void_p),
        ("Sacl", ctypes.c_void_p),
        ("Dacl", ctypes.c_void_p),
    ]

# NT 句柄信息
class SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX(ctypes.Structure):
    _fields_ = [
        ("Object", ctypes.c_void_p),
        ("UniqueProcessId", ctypes.c_void_p),
        ("HandleValue", ctypes.c_void_p),
        ("GrantedAccess", wintypes.ULONG),
        ("CreatorBackTraceIndex", wintypes.USHORT),
        ("ObjectTypeIndex", wintypes.USHORT),
        ("HandleAttributes", wintypes.ULONG),
        ("Reserved", wintypes.ULONG),
    ]

class SYSTEM_HANDLE_INFORMATION_EX(ctypes.Structure):
    _fields_ = [
        ("NumberOfHandles", ctypes.c_void_p),
        ("Reserved", ctypes.c_void_p),
        ("Handles", SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX * 1),
    ]

class UNICODE_STRING(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT),
        ("MaximumLength", wintypes.USHORT),
        ("Buffer", wintypes.LPWSTR),
    ]

class OBJECT_NAME_INFORMATION(ctypes.Structure):
    _fields_ = [("Name", UNICODE_STRING)]

# Restart Manager
class RM_UNIQUE_PROCESS(ctypes.Structure):
    _fields_ = [("dwProcessId", wintypes.DWORD),
                ("ProcessStartTime", wintypes.FILETIME)]

class RM_PROCESS_INFO(ctypes.Structure):
    _fields_ = [
        ("Process", RM_UNIQUE_PROCESS),
        ("strAppName", wintypes.WCHAR * (CCH_RM_MAX_APP_NAME + 1)),
        ("strServiceShortName", wintypes.WCHAR * (CCH_RM_MAX_SVC_NAME + 1)),
        ("ApplicationType", wintypes.DWORD),
        ("AppStatus", wintypes.ULONG),
        ("TSSessionId", wintypes.DWORD),
        ("bRestartable", wintypes.BOOL),
    ]

# ==================== DLL 加载 ====================

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll', use_last_error=True)
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
rstrtmgr = ctypes.WinDLL('rstrtmgr', use_last_error=True)

# ==================== 函数原型 ====================

# kernel32
kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                 ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.GetFileAttributesW.restype = wintypes.DWORD
kernel32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
kernel32.SetFileAttributesW.restype = wintypes.BOOL
kernel32.SetFileAttributesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
kernel32.DeleteFileW.restype = wintypes.BOOL
kernel32.DeleteFileW.argtypes = [wintypes.LPCWSTR]
kernel32.RemoveDirectoryW.restype = wintypes.BOOL
kernel32.RemoveDirectoryW.argtypes = [wintypes.LPCWSTR]
kernel32.MoveFileExW.restype = wintypes.BOOL
kernel32.MoveFileExW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
kernel32.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR,
                                               wintypes.DWORD, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
kernel32.DuplicateHandle.restype = wintypes.BOOL
kernel32.DuplicateHandle.argtypes = [wintypes.HANDLE, wintypes.HANDLE, wintypes.HANDLE,
                                     ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
                                     wintypes.BOOL, wintypes.DWORD]
kernel32.LocalFree.restype = ctypes.c_void_p
kernel32.LocalFree.argtypes = [ctypes.c_void_p]

# ntdll
ntdll.NtSetInformationFile.restype = wintypes.LONG
ntdll.NtSetInformationFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                       wintypes.ULONG, wintypes.ULONG]
ntdll.NtQuerySystemInformation.restype = wintypes.LONG
ntdll.NtQuerySystemInformation.argtypes = [wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG,
                                           ctypes.POINTER(wintypes.ULONG)]
ntdll.NtQueryObject.restype = wintypes.LONG
ntdll.NtQueryObject.argtypes = [wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p,
                                wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]

# advapi32
advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
advapi32.GetNamedSecurityInfoW.argtypes = [wintypes.LPCWSTR, wintypes.INT, wintypes.ULONG,
                                           ctypes.POINTER(ctypes.c_void_p),
                                           ctypes.POINTER(ctypes.c_void_p),
                                           ctypes.POINTER(ctypes.c_void_p),
                                           ctypes.POINTER(ctypes.c_void_p),
                                           ctypes.POINTER(ctypes.c_void_p)]
advapi32.SetNamedSecurityInfoW.restype = wintypes.DWORD
advapi32.SetNamedSecurityInfoW.argtypes = [wintypes.LPWSTR, wintypes.INT, wintypes.ULONG,
                                           ctypes.c_void_p, ctypes.c_void_p,
                                           ctypes.c_void_p, ctypes.c_void_p]
advapi32.OpenProcessToken.restype = wintypes.BOOL
advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                      ctypes.POINTER(wintypes.HANDLE)]
advapi32.LookupPrivilegeValueW.restype = wintypes.BOOL
advapi32.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR,
                                           ctypes.POINTER(LUID)]
advapi32.AdjustTokenPrivileges.restype = wintypes.BOOL
advapi32.AdjustTokenPrivileges.argtypes = [wintypes.HANDLE, wintypes.BOOL,
                                           ctypes.POINTER(TOKEN_PRIVILEGES),
                                           wintypes.DWORD, ctypes.c_void_p,
                                           ctypes.c_void_p]
advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p),
    ctypes.POINTER(wintypes.ULONG)]

# rstrtmgr
rstrtmgr.RmStartSession.restype = wintypes.DWORD
rstrtmgr.RmStartSession.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD,
                                    wintypes.LPWSTR]
rstrtmgr.RmEndSession.restype = wintypes.DWORD
rstrtmgr.RmEndSession.argtypes = [wintypes.DWORD]
rstrtmgr.RmRegisterResources.restype = wintypes.DWORD
rstrtmgr.RmRegisterResources.argtypes = [wintypes.DWORD, wintypes.UINT,
                                         ctypes.POINTER(wintypes.LPCWSTR),
                                         wintypes.UINT, ctypes.c_void_p,
                                         wintypes.UINT, ctypes.POINTER(wintypes.LPCWSTR)]
rstrtmgr.RmGetList.restype = wintypes.DWORD
rstrtmgr.RmGetList.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.UINT),
                               ctypes.POINTER(wintypes.UINT), ctypes.c_void_p,
                               ctypes.POINTER(wintypes.DWORD)]
rstrtmgr.RmShutdown.restype = wintypes.DWORD
rstrtmgr.RmShutdown.argtypes = [wintypes.DWORD, wintypes.ULONG, ctypes.c_void_p]


# ==================== 高层封装函数 ====================

def enable_privilege(privilege_name):
    """启用当前进程的指定特权（如 SeDebugPrivilege, SeRestorePrivilege, SeBackupPrivilege）"""
    h_token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(),
                                     TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
                                     ctypes.byref(h_token)):
        return False
    try:
        luid = LUID()
        if not advapi32.LookupPrivilegeValueW(None, privilege_name, ctypes.byref(luid)):
            return False
        tp = TOKEN_PRIVILEGES()
        tp.PrivilegeCount = 1
        tp.Privileges[0].Luid = luid
        tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
        advapi32.AdjustTokenPrivileges(h_token, False, ctypes.byref(tp),
                                       ctypes.sizeof(tp), None, None)
        return ctypes.get_last_error() == 0 or kernel32.GetLastError() == 0
    finally:
        kernel32.CloseHandle(h_token)


def enable_all_privileges():
    """启用删除操作所需的全部特权"""
    for priv in ["SeDebugPrivilege", "SeRestorePrivilege", "SeBackupPrivilege",
                 "SeTakeOwnershipPrivilege", "SecurityPrivilege"]:
        enable_privilege(priv)


def clear_file_attributes(path):
    """清除只读/隐藏/系统属性 (L0)"""
    attrs = kernel32.GetFileAttributesW(path)
    if attrs == 0xFFFFFFFF:
        return False
    new_attrs = attrs & ~(FILE_ATTRIBUTE_READONLY | FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
    if new_attrs == 0:
        new_attrs = FILE_ATTRIBUTE_NORMAL
    if new_attrs != attrs:
        return bool(kernel32.SetFileAttributesW(path, new_attrs))
    return True


def posix_delete(path):
    """
    POSIX 语义删除 (L1)
    使用 FileDispositionInformationEx 标记删除，即使文件被打开也能删除
    """
    is_dir = os.path.isdir(path)
    flags = FILE_ATTRIBUTE_NORMAL
    if is_dir:
        flags = FILE_FLAG_BACKUP_SEMANTICS

    handle = kernel32.CreateFileW(
        path, DELETE | SYNCHRONIZE,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None, OPEN_EXISTING, flags, None
    )
    if handle == INVALID_HANDLE_VALUE:
        return False

    try:
        disp_info = FILE_DISPOSITION_INFO_EX()
        disp_info.Flags = (FILE_DISPOSITION_DELETE |
                          FILE_DISPOSITION_POSIX_SEMANTICS |
                          FILE_DISPOSITION_IGNORE_READONLY_ATTRIBUTE)
        iosb = ctypes.c_void_p()
        status = ntdll.NtSetInformationFile(
            handle, ctypes.byref(iosb),
            ctypes.byref(disp_info),
            ctypes.sizeof(disp_info),
            FileDispositionInformationEx
        )
        return status == STATUS_SUCCESS
    finally:
        kernel32.CloseHandle(handle)


SYNCHRONIZE = 0x00100000


def regular_delete(path):
    """常规删除 (L2)"""
    if os.path.isdir(path):
        return bool(kernel32.RemoveDirectoryW(path))
    else:
        return bool(kernel32.DeleteFileW(path))


def take_ownership_and_grant(path):
    """
    夺取所有权并授予完全控制权限 (L3)
    """
    enable_privilege("SeTakeOwnershipPrivilege")
    enable_privilege("SeRestorePrivilege")
    enable_privilege("SeBackupPrivilege")

    SE_FILE_OBJECT = 1
    EVERYONE_SDDL = "D:(A;;GA;;;WD)"  # Everyone 完全访问

    # 先夺取所有权
    owner_sid = ctypes.c_void_p()
    group_sid = ctypes.c_void_p()
    dacl = ctypes.c_void_p()
    sacl = ctypes.c_void_p()

    # 获取当前用户的SID作为新所有者
    result = advapi32.GetNamedSecurityInfoW(
        path, SE_FILE_OBJECT,
        OWNER_SECURITY_INFORMATION | DACL_SECURITY_INFORMATION,
        ctypes.byref(owner_sid), ctypes.byref(group_sid),
        ctypes.byref(dacl), ctypes.byref(sacl), None
    )

    # 创建一个允许Everyone完全控制的SD
    sd_ptr = ctypes.c_void_p()
    sd_size = wintypes.ULONG()
    if not advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        EVERYONE_SDDL, 1, ctypes.byref(sd_ptr), ctypes.byref(sd_size)
    ):
        return False

    try:
        # 设置DACL
        result = advapi32.SetNamedSecurityInfoW(
            path, SE_FILE_OBJECT,
            DACL_SECURITY_INFORMATION,
            None, None, sd_ptr, None
        )
        if result != 0:
            return False

        # 设置所有者为当前管理员组
        # 使用BUILTIN\Administrators的SID (S-1-5-32-544)
        admin_sddl = "O:S-1-5-32-544"
        owner_sd_ptr = ctypes.c_void_p()
        if advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            admin_sddl, 1, ctypes.byref(owner_sd_ptr), ctypes.byref(sd_size)
        ):
            try:
                # 从SD中提取owner
                sd = ctypes.cast(owner_sd_ptr, ctypes.POINTER(SECURITY_DESCRIPTOR)).contents
                advapi32.SetNamedSecurityInfoW(
                    path, SE_FILE_OBJECT,
                    OWNER_SECURITY_INFORMATION,
                    sd.Owner, sd.Group, None, None
                )
            finally:
                kernel32.LocalFree(owner_sd_ptr)

        return True
    finally:
        kernel32.LocalFree(sd_ptr)


def _get_device_path(path):
    """将DOS路径转换为NT设备路径，用于句柄比对"""
    drive = os.path.splitdrive(os.path.abspath(path))[0]
    if not drive:
        return None
    # 查询 \??\X: 的符号链接目标
    buf = ctypes.create_unicode_buffer(512)
    kernel32.QueryDosDeviceW(drive.rstrip(':'), buf, 512)
    return buf.value


def _normalize_nt_path(nt_path):
    """规范化NT路径用于比较"""
    if not nt_path:
        return ""
    p = nt_path
    if p.startswith("\\??\\"):
        p = p[4:]
    p = p.rstrip("\\")
    return p.lower()


def close_remote_handle(path):
    """
    强制关闭其他进程持有的指向目标文件/目录的句柄 (L4)
    返回关闭的句柄数
    """
    enable_privilege("SeDebugPrivilege")

    target_path = os.path.abspath(path).lower().rstrip("\\")
    # 获取NT设备路径前缀
    drive = os.path.splitdrive(target_path)[0].upper()
    try:
        buf = ctypes.create_unicode_buffer(512)
        n = kernel32.QueryDosDeviceW(drive.rstrip(':'), buf, 512)
        nt_prefix = buf.value.lower() if n else None
    except:
        nt_prefix = None

    closed = 0
    current_pid = os.getpid()

    # 枚举系统句柄
    buf_size = 0x200000  # 2MB 初始
    while True:
        buf = ctypes.create_string_buffer(buf_size)
        ret_len = wintypes.ULONG()
        status = ntdll.NtQuerySystemInformation(
            SystemExtendedHandleInformation,
            buf, buf_size, ctypes.byref(ret_len)
        )
        if status == STATUS_SUCCESS:
            break
        elif status in (STATUS_INFO_LENGTH_MISMATCH, STATUS_BUFFER_OVERFLOW):
            buf_size = ret_len.value + 0x1000
            if buf_size > 0x2000000:  # 32MB 上限
                return closed
            continue
        else:
            return closed

    info = ctypes.cast(buf, ctypes.POINTER(SYSTEM_HANDLE_INFORMATION_EX)).contents
    handle_count = int(info.NumberOfHandles)

    # 遍历句柄
    handles_array = ctypes.cast(
        ctypes.addressof(info) + ctypes.sizeof(ctypes.c_void_p) * 2,
        ctypes.POINTER(SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX)
    )

    for i in range(handle_count):
        try:
            entry = handles_array[i]
            pid = int(entry.UniqueProcessId)
            if pid == current_pid or pid == 0 or pid == 4:  # 跳过自身和System
                continue

            handle_value = entry.HandleValue
            if not handle_value:
                continue

            # 打开进程
            h_proc = kernel32.OpenProcess(PROCESS_DUP_HANDLE, False, pid)
            if not h_proc:
                continue

            try:
                # 复制句柄查询对象名
                h_dup = wintypes.HANDLE()
                if not kernel32.DuplicateHandle(
                    h_proc, wintypes.HANDLE(handle_value),
                    kernel32.GetCurrentProcess(),
                    ctypes.byref(h_dup), 0, False,
                    0x2  # DUPLICATE_SAME_ACCESS
                ):
                    continue

                try:
                    # 查询对象名
                    name_buf = ctypes.create_string_buffer(2048)
                    ret_len2 = wintypes.ULONG()
                    name_status = ntdll.NtQueryObject(
                        h_dup, ObjectNameInformation,
                        name_buf, 2048, ctypes.byref(ret_len2)
                    )
                    if name_status == STATUS_SUCCESS:
                        obj_name = ctypes.cast(
                            name_buf, ctypes.POINTER(OBJECT_NAME_INFORMATION)
                        ).contents.Name
                        if obj_name.Buffer and obj_name.Length > 0:
                            raw_path = obj_name.Buffer
                            # 比对路径
                            check_path = raw_path.lower().rstrip("\\")
                            match = False
                            if check_path == target_path:
                                match = True
                            elif check_path.startswith(target_path + "\\"):
                                match = True
                            elif nt_prefix:
                                # 转换NT路径比较
                                np = check_path
                                if np.startswith(nt_prefix):
                                    np = drive + np[len(nt_prefix):]
                                if np == target_path or np.startswith(target_path + "\\"):
                                    match = True

                            if match:
                                # 关闭句柄（用DUPLICATE_CLOSE_SOURCE）
                                h_close = wintypes.HANDLE()
                                if kernel32.DuplicateHandle(
                                    h_proc, wintypes.HANDLE(handle_value),
                                    kernel32.GetCurrentProcess(),
                                    ctypes.byref(h_close), 0, False,
                                    0x1  # DUPLICATE_CLOSE_SOURCE
                                ):
                                    kernel32.CloseHandle(h_close)
                                    closed += 1
                finally:
                    kernel32.CloseHandle(h_dup)
            finally:
                kernel32.CloseHandle(h_proc)
        except Exception:
            continue

    return closed


# QueryDosDevice 原型
kernel32.QueryDosDeviceW.restype = wintypes.DWORD
kernel32.QueryDosDeviceW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]


def find_locking_processes(paths):
    """
    使用 Restart Manager 查找占用进程 (L5)
    返回: [(pid, app_name, app_type, restartable), ...]
    """
    if isinstance(paths, str):
        paths = [paths]
    paths = [os.path.abspath(p) for p in paths if os.path.exists(p)]
    if not paths:
        return []

    session_handle = wintypes.DWORD(RM_INVALID_SESSION)
    session_key = ctypes.create_unicode_buffer(CCH_RM_MAX_APP_NAME + 1)

    result = rstrtmgr.RmStartSession(ctypes.byref(session_handle), 0, session_key)
    if result != 0:
        return []

    try:
        path_array = (wintypes.LPCWSTR * len(paths))(*paths)
        result = rstrtmgr.RmRegisterResources(
            session_handle, len(paths), path_array, 0, None, 0, None
        )
        if result != 0:
            return []

        pn_needed = wintypes.UINT(0)
        pn_count = wintypes.UINT(0)
        reboot_reasons = wintypes.DWORD(0)

        result = rstrtmgr.RmGetList(
            session_handle, ctypes.byref(pn_needed),
            ctypes.byref(pn_count), None,
            ctypes.byref(reboot_reasons)
        )

        if result == ERROR_MORE_DATA and pn_needed.value > 0:
            proc_array = (RM_PROCESS_INFO * pn_needed.value)()
            pn_count.value = pn_needed.value
            result = rstrtmgr.RmGetList(
                session_handle, ctypes.byref(pn_needed),
                ctypes.byref(pn_count), proc_array,
                ctypes.byref(reboot_reasons)
            )
            if result == 0:
                processes = []
                for i in range(pn_count.value):
                    info = proc_array[i]
                    processes.append((
                        info.Process.dwProcessId,
                        info.strAppName or f"PID_{info.Process.dwProcessId}",
                        RM_APP_TYPE.get(info.ApplicationType, "未知"),
                        info.bRestartable,
                    ))
                return processes
        return []
    finally:
        rstrtmgr.RmEndSession(ctypes.byref(session_handle))


def rm_shutdown_processes(session_handle):
    """通过Restart Manager终止进程"""
    return rstrtmgr.RmShutdown(session_handle, 0, None) == 0


def schedule_delete_on_reboot(path):
    """登记为重启时删除 (L6)"""
    return bool(kernel32.MoveFileExW(path, None, MOVEFILE_DELAY_UNTIL_REBOOT))


def get_final_path(path):
    """获取最终规范化路径（解析符号链接/junction）"""
    try:
        handle = kernel32.CreateFileW(
            path, 0, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            None, OPEN_EXISTING,
            FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, None
        )
        if handle == INVALID_HANDLE_VALUE:
            return os.path.abspath(path)
        try:
            buf = ctypes.create_unicode_buffer(4096)
            n = kernel32.GetFinalPathNameByHandleW(handle, buf, 4096, 0)
            if n > 0:
                result = buf.value
                if result.startswith("\\\\?\\"):
                    result = result[4:]
                return result
            return os.path.abspath(path)
        finally:
            kernel32.CloseHandle(handle)
    except:
        return os.path.abspath(path)


def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False


# ==================== L4.5: NtDeleteFile 原生删除 ====================

class OBJECT_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.ULONG),
        ("RootDirectory", wintypes.HANDLE),
        ("ObjectName", ctypes.c_void_p),
        ("Attributes", wintypes.ULONG),
        ("SecurityDescriptor", ctypes.c_void_p),
        ("SecurityQualityOfService", ctypes.c_void_p),
    ]

class IO_STATUS_BLOCK(ctypes.Structure):
    _fields_ = [
        ("Status", wintypes.LONG),
        ("Information", ctypes.c_void_p),
    ]

ntdll.NtDeleteFile.restype = wintypes.LONG
ntdll.NtDeleteFile.argtypes = [ctypes.POINTER(OBJECT_ATTRIBUTES)]


def nt_delete_file(path):
    """
    L4.5: 直接调用 NtDeleteFile 原生 API 删除文件
    绕过 Win32 层的某些检查，直接向 I/O 管理器发送删除请求
    """
    enable_privilege("SeBackupPrivilege")
    enable_privilege("SeRestorePrivilege")

    # 构造 NT 路径
    nt_path = _to_nt_path(path)
    if not nt_path:
        return False

    us = UNICODE_STRING()
    us.Buffer = nt_path
    us.Length = len(nt_path) * 2
    us.MaximumLength = us.Length + 2

    oa = OBJECT_ATTRIBUTES()
    oa.Length = ctypes.sizeof(OBJECT_ATTRIBUTES)
    oa.RootDirectory = None
    oa.ObjectName = ctypes.cast(ctypes.pointer(us), ctypes.c_void_p)
    oa.Attributes = OBJ_CASE_INSENSITIVE

    status = ntdll.NtDeleteFile(ctypes.byref(oa))
    return status == STATUS_SUCCESS


def _to_nt_path(path):
    """将 DOS 路径转换为 NT 原生路径 (\\??\\X:\\...)"""
    try:
        abs_path = os.path.abspath(path)
        drive = os.path.splitdrive(abs_path)[0]
        if drive:
            return "\\??\\" + abs_path
        elif abs_path.startswith("\\\\"):
            return "\\??\\UNC\\" + abs_path[2:]
        return None
    except:
        return None


# ==================== L4.6: FILE_FLAG_DELETE_ON_CLOSE ====================

def delete_on_close(path):
    """
    L4.6: 以 FILE_FLAG_DELETE_ON_CLOSE 标志打开文件
    文件在所有句柄（包括其他进程的）关闭后自动删除
    同时配合 FILE_SHARE_DELETE 共享
    """
    is_dir = os.path.isdir(path)
    flags = FILE_FLAG_DELETE_ON_CLOSE | FILE_FLAG_POSIX_SEMANTICS
    if is_dir:
        flags |= FILE_FLAG_BACKUP_SEMANTICS

    handle = kernel32.CreateFileW(
        path, DELETE,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None, OPEN_EXISTING, flags, None
    )
    if handle == INVALID_HANDLE_VALUE:
        return False
    # 立即关闭我们的句柄，文件会在其他进程的句柄关闭后删除
    kernel32.CloseHandle(handle)
    return True


# ==================== L4.7: 卸载内存映射 (NtUnmapViewOfSection) ====================

psapi = ctypes.WinDLL('psapi', use_last_error=True)

kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]

psapi.EnumProcessModulesEx.restype = wintypes.BOOL
psapi.EnumProcessModulesEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE),
                                       wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
psapi.GetModuleFileNameExW.restype = wintypes.DWORD
psapi.GetModuleFileNameExW.argtypes = [wintypes.HANDLE, wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]

ntdll.NtUnmapViewOfSection.restype = wintypes.LONG
ntdll.NtUnmapViewOfSection.argtypes = [wintypes.HANDLE, ctypes.c_void_p]

# LIST_MODULES_ALL
LIST_MODULES_ALL = 0x03


def _get_process_name(pid):
    """获取进程名"""
    try:
        import subprocess
        r = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5,
            creationflags=0x08000000
        )
        if r.stdout:
            parts = r.stdout.strip().split('","')
            if parts:
                return parts[0].strip('"').lower()
    except:
        pass
    return ""


def unmap_mapped_sections(path):
    """
    L4.7: 卸载被 LoadLibrary / MapViewOfFile 映射到其他进程内存中的目标文件
    对于被加载的 DLL/EXE，关句柄删不掉，必须先 unmap
    只对非关键进程操作，跳过系统进程
    返回卸载的模块数
    """
    enable_privilege("SeDebugPrivilege")

    target_lower = os.path.abspath(path).lower()
    unmapped = 0

    # 枚举所有进程
    buf_size = 0x100000
    pids = (wintypes.DWORD * 2048)()
    bytes_returned = wintypes.DWORD()
    if not psapi.EnumProcesses(pids, ctypes.sizeof(pids), ctypes.byref(bytes_returned)):
        return 0

    count = bytes_returned.value // ctypes.sizeof(wintypes.DWORD)

    for i in range(count):
        pid = pids[i]
        if pid in CRITICAL_PIDS or pid == os.getpid():
            continue

        proc_name = _get_process_name(pid)
        if proc_name in CRITICAL_NAMES:
            continue

        h_proc = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_OPERATION,
            False, pid
        )
        if not h_proc:
            continue

        try:
            # 枚举进程模块
            h_mods = (wintypes.HMODULE * 1024)()
            needed = wintypes.DWORD()
            if not psapi.EnumProcessModulesEx(
                h_proc, h_mods, ctypes.sizeof(h_mods),
                ctypes.byref(needed), LIST_MODULES_ALL
            ):
                continue

            mod_count = min(needed.value // ctypes.sizeof(wintypes.HMODULE), 1024)
            for j in range(mod_count):
                try:
                    name_buf = ctypes.create_unicode_buffer(260)
                    n = psapi.GetModuleFileNameExW(h_proc, h_mods[j], name_buf, 260)
                    if n > 0:
                        mod_path = os.path.normpath(name_buf.value).lower()
                        if mod_path == target_lower or mod_path.startswith(target_lower + "\\"):
                            # 卸载这个模块
                            base_addr = ctypes.cast(h_mods[j], ctypes.c_void_p)
                            status = ntdll.NtUnmapViewOfSection(h_proc, base_addr)
                            if status == STATUS_SUCCESS:
                                unmapped += 1
                except:
                    continue
        finally:
            kernel32.CloseHandle(h_proc)

    return unmapped


# ==================== L5+: 强制终止进程树 ====================

def kill_process_tree(pid):
    """强制终止进程及其子进程 (taskkill /F /T)"""
    import subprocess
    try:
        r = subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True, text=True, timeout=10,
            creationflags=0x08000000
        )
        return r.returncode == 0
    except:
        return False
