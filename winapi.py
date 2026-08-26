# -*- coding: utf-8 -*-
"""Win32/NT API ctypes 封装 - 增强版"""

import os
import ctypes
from ctypes import wintypes

# ==================== 常量 ====================
FILE_ATTRIBUTE_READONLY = 0x00000001
FILE_ATTRIBUTE_HIDDEN = 0x00000002
FILE_ATTRIBUTE_SYSTEM = 0x00000004
FILE_ATTRIBUTE_DIRECTORY = 0x00000010
FILE_ATTRIBUTE_NORMAL = 0x00000080

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
DELETE = 0x00010000
SYNCHRONIZE = 0x00100000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
FILE_FLAG_DELETE_ON_CLOSE = 0x04000000
FILE_FLAG_POSIX_SEMANTICS = 0x01000000
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

FileDispositionInformation = 13
FileDispositionInformationEx = 64
FILE_DISPOSITION_DELETE = 0x00000001
FILE_DISPOSITION_POSIX_SEMANTICS = 0x00000002
FILE_DISPOSITION_IGNORE_READONLY_ATTRIBUTE = 0x00000010

OWNER_SECURITY_INFORMATION = 0x00000001
GROUP_SECURITY_INFORMATION = 0x00000002
DACL_SECURITY_INFORMATION = 0x00000004

STATUS_SUCCESS = 0x00000000
STATUS_INFO_LENGTH_MISMATCH = 0xC0000004
STATUS_BUFFER_OVERFLOW = 0x80000005

SystemExtendedHandleInformation = 64
ObjectNameInformation = 1
PROCESS_DUP_HANDLE = 0x0040
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_TERMINATE = 0x0001

MOVEFILE_DELAY_UNTIL_REBOOT = 0x00000004
CCH_RM_MAX_APP_NAME = 255
CCH_RM_MAX_SVC_NAME = 63
RM_INVALID_SESSION = 0xFFFFFFFF
ERROR_MORE_DATA = 234
LIST_MODULES_ALL = 0x03

OBJ_CASE_INSENSITIVE = 0x00000040
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008

CRITICAL_PIDS = {0, 4}
CRITICAL_NAMES = {
    "smss.exe", "csrss.exe", "wininit.exe", "winlogon.exe",
    "services.exe", "lsass.exe", "lsm.exe", "svchost.exe",
    "fontdrvhost.exe", "dwm.exe", "ntoskrnl.exe",
}

RM_APP_TYPE = {0:"未知",1:"控制台",2:"Windows应用",3:"服务",4:"资源管理器",5:"控制台",6:"Windows应用",7:"服务"}

# ==================== 结构体 ====================
class FILE_DISPOSITION_INFO_EX(ctypes.Structure):
    _fields_ = [("Flags", wintypes.DWORD)]

class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [("PrivilegeCount", wintypes.DWORD), ("Privileges", LUID_AND_ATTRIBUTES * 1)]

class SECURITY_DESCRIPTOR(ctypes.Structure):
    _fields_ = [("Revision",wintypes.BYTE),("Sbz1",wintypes.BYTE),("Control",wintypes.WORD),
                ("Owner",ctypes.c_void_p),("Group",ctypes.c_void_p),("Sacl",ctypes.c_void_p),("Dacl",ctypes.c_void_p)]

class SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX(ctypes.Structure):
    _fields_ = [("Object",ctypes.c_void_p),("UniqueProcessId",ctypes.c_void_p),("HandleValue",ctypes.c_void_p),
                ("GrantedAccess",wintypes.ULONG),("CreatorBackTraceIndex",wintypes.USHORT),
                ("ObjectTypeIndex",wintypes.USHORT),("HandleAttributes",wintypes.ULONG),("Reserved",wintypes.ULONG)]

class SYSTEM_HANDLE_INFORMATION_EX(ctypes.Structure):
    _fields_ = [("NumberOfHandles",ctypes.c_void_p),("Reserved",ctypes.c_void_p),("Handles",SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX * 1)]

class UNICODE_STRING(ctypes.Structure):
    _fields_ = [("Length",wintypes.USHORT),("MaximumLength",wintypes.USHORT),("Buffer",wintypes.LPWSTR)]

class OBJECT_NAME_INFORMATION(ctypes.Structure):
    _fields_ = [("Name", UNICODE_STRING)]

class RM_UNIQUE_PROCESS(ctypes.Structure):
    _fields_ = [("dwProcessId",wintypes.DWORD),("ProcessStartTime",wintypes.FILETIME)]

class RM_PROCESS_INFO(ctypes.Structure):
    _fields_ = [("Process",RM_UNIQUE_PROCESS),
                ("strAppName",wintypes.WCHAR*(CCH_RM_MAX_APP_NAME+1)),
                ("strServiceShortName",wintypes.WCHAR*(CCH_RM_MAX_SVC_NAME+1)),
                ("ApplicationType",wintypes.DWORD),("AppStatus",wintypes.ULONG),
                ("TSSessionId",wintypes.DWORD),("bRestartable",wintypes.BOOL)]

class OBJECT_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Length",wintypes.ULONG),("RootDirectory",wintypes.HANDLE),
                ("ObjectName",ctypes.c_void_p),("Attributes",wintypes.ULONG),
                ("SecurityDescriptor",ctypes.c_void_p),("SecurityQualityOfService",ctypes.c_void_p)]

class IO_STATUS_BLOCK(ctypes.Structure):
    _fields_ = [("Status",wintypes.LONG),("Information",ctypes.c_void_p)]

# ==================== DLL ====================
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
ntdll = ctypes.WinDLL('ntdll', use_last_error=True)
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
rstrtmgr = ctypes.WinDLL('rstrtmgr', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)

# 函数原型
kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.GetFileAttributesW.restype = wintypes.DWORD
kernel32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
kernel32.SetFileAttributesW.restype = wintypes.BOOL
kernel32.SetFileAttributesW.argtypes = [wintypes.LPCWSTR,wintypes.DWORD]
kernel32.DeleteFileW.restype = wintypes.BOOL
kernel32.DeleteFileW.argtypes = [wintypes.LPCWSTR]
kernel32.RemoveDirectoryW.restype = wintypes.BOOL
kernel32.RemoveDirectoryW.argtypes = [wintypes.LPCWSTR]
kernel32.MoveFileExW.restype = wintypes.BOOL
kernel32.MoveFileExW.argtypes = [wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
kernel32.DuplicateHandle.restype = wintypes.BOOL
kernel32.DuplicateHandle.argtypes = [wintypes.HANDLE,wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.HANDLE),wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
kernel32.TerminateProcess.restype = wintypes.BOOL
kernel32.TerminateProcess.argtypes = [wintypes.HANDLE,wintypes.UINT]
kernel32.QueryDosDeviceW.restype = wintypes.DWORD
kernel32.QueryDosDeviceW.argtypes = [wintypes.LPCWSTR,wintypes.LPWSTR,wintypes.DWORD]
kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
kernel32.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE,wintypes.LPWSTR,wintypes.DWORD,wintypes.DWORD]
kernel32.LocalFree.restype = ctypes.c_void_p
kernel32.LocalFree.argtypes = [ctypes.c_void_p]

ntdll.NtSetInformationFile.restype = wintypes.LONG
ntdll.NtSetInformationFile.argtypes = [wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,wintypes.ULONG,wintypes.ULONG]
ntdll.NtQuerySystemInformation.restype = wintypes.LONG
ntdll.NtQuerySystemInformation.argtypes = [wintypes.ULONG,ctypes.c_void_p,wintypes.ULONG,ctypes.POINTER(wintypes.ULONG)]
ntdll.NtQueryObject.restype = wintypes.LONG
ntdll.NtQueryObject.argtypes = [wintypes.HANDLE,wintypes.ULONG,ctypes.c_void_p,wintypes.ULONG,ctypes.POINTER(wintypes.ULONG)]
ntdll.NtDeleteFile.restype = wintypes.LONG
ntdll.NtDeleteFile.argtypes = [ctypes.POINTER(OBJECT_ATTRIBUTES)]
ntdll.NtUnmapViewOfSection.restype = wintypes.LONG
ntdll.NtUnmapViewOfSection.argtypes = [wintypes.HANDLE,ctypes.c_void_p]

advapi32.GetNamedSecurityInfoW.restype = wintypes.DWORD
advapi32.GetNamedSecurityInfoW.argtypes = [wintypes.LPCWSTR,wintypes.INT,wintypes.ULONG,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p)]
advapi32.SetNamedSecurityInfoW.restype = wintypes.DWORD
advapi32.SetNamedSecurityInfoW.argtypes = [wintypes.LPWSTR,wintypes.INT,wintypes.ULONG,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
advapi32.OpenProcessToken.restype = wintypes.BOOL
advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE,wintypes.DWORD,ctypes.POINTER(wintypes.HANDLE)]
advapi32.LookupPrivilegeValueW.restype = wintypes.BOOL
advapi32.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR,wintypes.LPCWSTR,ctypes.POINTER(LUID)]
advapi32.AdjustTokenPrivileges.restype = wintypes.BOOL
advapi32.AdjustTokenPrivileges.argtypes = [wintypes.HANDLE,wintypes.BOOL,ctypes.POINTER(TOKEN_PRIVILEGES),wintypes.DWORD,ctypes.c_void_p,ctypes.c_void_p]
advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = wintypes.BOOL
advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(wintypes.ULONG)]

rstrtmgr.RmStartSession.restype = wintypes.DWORD
rstrtmgr.RmStartSession.argtypes = [ctypes.POINTER(wintypes.DWORD),wintypes.DWORD,wintypes.LPWSTR]
rstrtmgr.RmEndSession.restype = wintypes.DWORD
rstrtmgr.RmEndSession.argtypes = [wintypes.DWORD]
rstrtmgr.RmRegisterResources.restype = wintypes.DWORD
rstrtmgr.RmRegisterResources.argtypes = [wintypes.DWORD,wintypes.UINT,ctypes.POINTER(wintypes.LPCWSTR),wintypes.UINT,ctypes.c_void_p,wintypes.UINT,ctypes.POINTER(wintypes.LPCWSTR)]
rstrtmgr.RmGetList.restype = wintypes.DWORD
rstrtmgr.RmGetList.argtypes = [wintypes.DWORD,ctypes.POINTER(wintypes.UINT),ctypes.POINTER(wintypes.UINT),ctypes.c_void_p,ctypes.POINTER(wintypes.DWORD)]

psapi.EnumProcesses.restype = wintypes.BOOL
psapi.EnumProcesses.argtypes = [ctypes.POINTER(wintypes.DWORD),wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
psapi.EnumProcessModulesEx.restype = wintypes.BOOL
psapi.EnumProcessModulesEx.argtypes = [wintypes.HANDLE,ctypes.POINTER(wintypes.HMODULE),wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),wintypes.DWORD]
psapi.GetModuleFileNameExW.restype = wintypes.DWORD
psapi.GetModuleFileNameExW.argtypes = [wintypes.HANDLE,wintypes.HMODULE,wintypes.LPWSTR,wintypes.DWORD]

# ==================== 工具函数 ====================
def enable_privilege(privilege_name):
    try:
        h_token = wintypes.HANDLE()
        if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES|TOKEN_QUERY, ctypes.byref(h_token)):
            return False
        try:
            luid = LUID()
            if not advapi32.LookupPrivilegeValueW(None, privilege_name, ctypes.byref(luid)):
                return False
            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Privileges[0].Luid = luid
            tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
            advapi32.AdjustTokenPrivileges(h_token, False, ctypes.byref(tp), ctypes.sizeof(tp), None, None)
            return True
        finally:
            kernel32.CloseHandle(h_token)
    except:
        return False

def enable_all_privileges():
    for priv in ["SeDebugPrivilege","SeRestorePrivilege","SeBackupPrivilege","SeTakeOwnershipPrivilege","SecurityPrivilege","SeShutdownPrivilege"]:
        enable_privilege(priv)

def clear_file_attributes(path):
    attrs = kernel32.GetFileAttributesW(path)
    if attrs == 0xFFFFFFFF: return False
    new_attrs = attrs & ~(FILE_ATTRIBUTE_READONLY|FILE_ATTRIBUTE_HIDDEN|FILE_ATTRIBUTE_SYSTEM)
    if new_attrs == 0: new_attrs = FILE_ATTRIBUTE_NORMAL
    if new_attrs != attrs:
        return bool(kernel32.SetFileAttributesW(path, new_attrs))
    return True

def posix_delete(path):
    is_dir = os.path.isdir(path)
    flags = FILE_ATTRIBUTE_NORMAL | (FILE_FLAG_BACKUP_SEMANTICS if is_dir else 0)
    handle = kernel32.CreateFileW(path, DELETE|SYNCHRONIZE, FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE, None, OPEN_EXISTING, flags, None)
    if handle == INVALID_HANDLE_VALUE: return False
    try:
        disp = FILE_DISPOSITION_INFO_EX()
        disp.Flags = FILE_DISPOSITION_DELETE|FILE_DISPOSITION_POSIX_SEMANTICS|FILE_DISPOSITION_IGNORE_READONLY_ATTRIBUTE
        iosb = ctypes.c_void_p()
        status = ntdll.NtSetInformationFile(handle, ctypes.byref(iosb), ctypes.byref(disp), ctypes.sizeof(disp), FileDispositionInformationEx)
        return status == STATUS_SUCCESS
    finally:
        kernel32.CloseHandle(handle)

def regular_delete(path):
    if os.path.isdir(path):
        return bool(kernel32.RemoveDirectoryW(path))
    return bool(kernel32.DeleteFileW(path))

def _to_nt_path(path):
    try:
        abs_path = os.path.abspath(path)
        drive = os.path.splitdrive(abs_path)[0]
        if drive: return "\\??\\" + abs_path
        elif abs_path.startswith("\\\\"): return "\\??\\UNC\\" + abs_path[2:]
        return None
    except: return None

def nt_delete_file(path):
    enable_privilege("SeBackupPrivilege")
    enable_privilege("SeRestorePrivilege")
    nt_path = _to_nt_path(path)
    if not nt_path: return False
    us = UNICODE_STRING()
    us.Buffer = nt_path
    us.Length = len(nt_path) * 2
    us.MaximumLength = us.Length + 2
    oa = OBJECT_ATTRIBUTES()
    oa.Length = ctypes.sizeof(OBJECT_ATTRIBUTES)
    oa.RootDirectory = None
    oa.ObjectName = ctypes.cast(ctypes.pointer(us), ctypes.c_void_p)
    oa.Attributes = OBJ_CASE_INSENSITIVE
    return ntdll.NtDeleteFile(ctypes.byref(oa)) == STATUS_SUCCESS

def delete_on_close(path):
    is_dir = os.path.isdir(path)
    flags = FILE_FLAG_DELETE_ON_CLOSE|FILE_FLAG_POSIX_SEMANTICS|(FILE_FLAG_BACKUP_SEMANTICS if is_dir else 0)
    handle = kernel32.CreateFileW(path, DELETE, FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE, None, OPEN_EXISTING, flags, None)
    if handle == INVALID_HANDLE_VALUE: return False
    kernel32.CloseHandle(handle)
    return True

def take_ownership_and_grant(path):
    enable_privilege("SeTakeOwnershipPrivilege")
    enable_privilege("SeRestorePrivilege")
    SE_FILE_OBJECT = 1
    sd_ptr = ctypes.c_void_p()
    sd_size = wintypes.ULONG()
    if not advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW("D:(A;;GA;;;WD)", 1, ctypes.byref(sd_ptr), ctypes.byref(sd_size)):
        return False
    try:
        result = advapi32.SetNamedSecurityInfoW(path, SE_FILE_OBJECT, DACL_SECURITY_INFORMATION, None, None, sd_ptr, None)
        if result != 0: return False
        owner_sd_ptr = ctypes.c_void_p()
        if advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW("O:S-1-5-32-544", 1, ctypes.byref(owner_sd_ptr), ctypes.byref(sd_size)):
            try:
                sd = ctypes.cast(owner_sd_ptr, ctypes.POINTER(SECURITY_DESCRIPTOR)).contents
                advapi32.SetNamedSecurityInfoW(path, SE_FILE_OBJECT, OWNER_SECURITY_INFORMATION, sd.Owner, sd.Group, None, None)
            finally:
                kernel32.LocalFree(owner_sd_ptr)
        return True
    finally:
        kernel32.LocalFree(sd_ptr)

def close_remote_handle(path):
    enable_privilege("SeDebugPrivilege")
    target_path = os.path.abspath(path).lower().rstrip("\\")
    drive = os.path.splitdrive(target_path)[0].upper()
    try:
        buf = ctypes.create_unicode_buffer(512)
        n = kernel32.QueryDosDeviceW(drive.rstrip(':'), buf, 512)
        nt_prefix = buf.value.lower() if n else None
    except: nt_prefix = None
    closed = 0
    current_pid = os.getpid()
    buf_size = 0x200000
    while True:
        buf = ctypes.create_string_buffer(buf_size)
        ret_len = wintypes.ULONG()
        status = ntdll.NtQuerySystemInformation(SystemExtendedHandleInformation, buf, buf_size, ctypes.byref(ret_len))
        if status == STATUS_SUCCESS: break
        elif status in (STATUS_INFO_LENGTH_MISMATCH, STATUS_BUFFER_OVERFLOW):
            buf_size = ret_len.value + 0x1000
            if buf_size > 0x2000000: return closed
            continue
        else: return closed
    info = ctypes.cast(buf, ctypes.POINTER(SYSTEM_HANDLE_INFORMATION_EX)).contents
    handle_count = int(info.NumberOfHandles)
    handles_array = ctypes.cast(ctypes.addressof(info)+ctypes.sizeof(ctypes.c_void_p)*2, ctypes.POINTER(SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX))
    for i in range(handle_count):
        try:
            entry = handles_array[i]
            pid = int(entry.UniqueProcessId)
            if pid in (current_pid, 0, 4): continue
            handle_value = entry.HandleValue
            if not handle_value: continue
            h_proc = kernel32.OpenProcess(PROCESS_DUP_HANDLE, False, pid)
            if not h_proc: continue
            try:
                h_dup = wintypes.HANDLE()
                if not kernel32.DuplicateHandle(h_proc, wintypes.HANDLE(handle_value), kernel32.GetCurrentProcess(), ctypes.byref(h_dup), 0, False, 0x2): continue
                try:
                    name_buf = ctypes.create_string_buffer(2048)
                    ret_len2 = wintypes.ULONG()
                    if ntdll.NtQueryObject(h_dup, ObjectNameInformation, name_buf, 2048, ctypes.byref(ret_len2)) == STATUS_SUCCESS:
                        obj_name = ctypes.cast(name_buf, ctypes.POINTER(OBJECT_NAME_INFORMATION)).contents.Name
                        if obj_name.Buffer and obj_name.Length > 0:
                            check_path = obj_name.Buffer.lower().rstrip("\\")
                            match = check_path == target_path or check_path.startswith(target_path+"\\")
                            if not match and nt_prefix:
                                np = check_path
                                if np.startswith(nt_prefix): np = drive + np[len(nt_prefix):]
                                match = np == target_path or np.startswith(target_path+"\\")
                            if match:
                                h_close = wintypes.HANDLE()
                                if kernel32.DuplicateHandle(h_proc, wintypes.HANDLE(handle_value), kernel32.GetCurrentProcess(), ctypes.byref(h_close), 0, False, 0x1):
                                    kernel32.CloseHandle(h_close)
                                    closed += 1
                finally: kernel32.CloseHandle(h_dup)
            finally: kernel32.CloseHandle(h_proc)
        except: continue
    return closed

def unmap_mapped_sections(path):
    enable_privilege("SeDebugPrivilege")
    target_lower = os.path.abspath(path).lower()
    unmapped = 0
    pids = (wintypes.DWORD * 2048)()
    bytes_returned = wintypes.DWORD()
    if not psapi.EnumProcesses(pids, ctypes.sizeof(pids), ctypes.byref(bytes_returned)): return 0
    count = bytes_returned.value // ctypes.sizeof(wintypes.DWORD)
    for i in range(count):
        pid = pids[i]
        if pid in CRITICAL_PIDS or pid == os.getpid(): continue
        proc_name = _get_process_name(pid)
        if proc_name in CRITICAL_NAMES: continue
        h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_VM_READ|PROCESS_VM_OPERATION, False, pid)
        if not h_proc: continue
        try:
            h_mods = (wintypes.HMODULE * 1024)()
            needed = wintypes.DWORD()
            if not psapi.EnumProcessModulesEx(h_proc, h_mods, ctypes.sizeof(h_mods), ctypes.byref(needed), LIST_MODULES_ALL): continue
            mod_count = min(needed.value // ctypes.sizeof(wintypes.HMODULE), 1024)
            for j in range(mod_count):
                try:
                    name_buf = ctypes.create_unicode_buffer(260)
                    n = psapi.GetModuleFileNameExW(h_proc, h_mods[j], name_buf, 260)
                    if n > 0:
                        mod_path = os.path.normpath(name_buf.value).lower()
                        if mod_path == target_lower or mod_path.startswith(target_lower+"\\"):
                            if ntdll.NtUnmapViewOfSection(h_proc, ctypes.cast(h_mods[j], ctypes.c_void_p)) == STATUS_SUCCESS:
                                unmapped += 1
                except: continue
        finally: kernel32.CloseHandle(h_proc)
    return unmapped

def _get_process_name(pid):
    try:
        import subprocess
        r = subprocess.run(["tasklist","/FI",f"PID eq {pid}","/FO","CSV","/NH"], capture_output=True, text=True, timeout=5, creationflags=0x08000000)
        if r.stdout:
            parts = r.stdout.strip().split('","')
            if parts: return parts[0].strip('"').lower()
    except: pass
    return ""

def find_locking_processes(paths):
    if isinstance(paths, str): paths = [paths]
    paths = [os.path.abspath(p) for p in paths if os.path.exists(p)]
    if not paths: return []
    session_handle = wintypes.DWORD(RM_INVALID_SESSION)
    session_key = ctypes.create_unicode_buffer(CCH_RM_MAX_APP_NAME+1)
    if rstrtmgr.RmStartSession(ctypes.byref(session_handle), 0, session_key) != 0: return []
    try:
        path_array = (wintypes.LPCWSTR * len(paths))(*paths)
        if rstrtmgr.RmRegisterResources(session_handle, len(paths), path_array, 0, None, 0, None) != 0: return []
        pn_needed = wintypes.UINT(0)
        pn_count = wintypes.UINT(0)
        reboot_reasons = wintypes.DWORD(0)
        result = rstrtmgr.RmGetList(session_handle, ctypes.byref(pn_needed), ctypes.byref(pn_count), None, ctypes.byref(reboot_reasons))
        if result == ERROR_MORE_DATA and pn_needed.value > 0:
            proc_array = (RM_PROCESS_INFO * pn_needed.value)()
            pn_count.value = pn_needed.value
            if rstrtmgr.RmGetList(session_handle, ctypes.byref(pn_needed), ctypes.byref(pn_count), proc_array, ctypes.byref(reboot_reasons)) == 0:
                processes = []
                for i in range(pn_count.value):
                    info = proc_array[i]
                    processes.append((info.Process.dwProcessId, info.strAppName or f"PID_{info.Process.dwProcessId}", RM_APP_TYPE.get(info.ApplicationType,"未知"), info.bRestartable))
                return processes
        return []
    finally:
        rstrtmgr.RmEndSession(ctypes.byref(session_handle))

def kill_process_tree(pid):
    import subprocess
    try:
        r = subprocess.run(["taskkill","/F","/T","/PID",str(pid)], capture_output=True, timeout=10, creationflags=0x08000000)
        return r.returncode == 0
    except: return False

def schedule_delete_on_reboot(path):
    return bool(kernel32.MoveFileExW(path, None, MOVEFILE_DELAY_UNTIL_REBOOT))

def get_final_path(path):
    try:
        handle = kernel32.CreateFileW(path, 0, FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE, None, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT, None)
        if handle == INVALID_HANDLE_VALUE: return os.path.abspath(path)
        try:
            buf = ctypes.create_unicode_buffer(4096)
            n = kernel32.GetFinalPathNameByHandleW(handle, buf, 4096, 0)
            if n > 0:
                result = buf.value
                if result.startswith("\\\\?\\"): result = result[4:]
                return result
            return os.path.abspath(path)
        finally: kernel32.CloseHandle(handle)
    except: return os.path.abspath(path)

def is_admin():
    try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except: return False
