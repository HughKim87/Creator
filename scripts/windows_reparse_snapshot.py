"""Opaque Windows reparse-point preservation; never follows the target."""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import os
from pathlib import Path


def reparse(path):
    try:
        return bool(Path(path).lstat().st_file_attributes & 0x400)
    except (AttributeError, FileNotFoundError):
        return False


def control(path, code, payload=None):
    if os.name != 'nt':
        raise OSError('Windows reparse preservation requires Windows')
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    api.CreateFileW.restype = wintypes.HANDLE
    api.DeviceIoControl.argtypes = (wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
                                   wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
                                   ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p)
    api.DeviceIoControl.restype = wintypes.BOOL
    api.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = api.CreateFileW(str(Path(path).absolute()), 0x40000000 if payload is not None else 0,
                             7, None, 3, 0x02200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        incoming = ctypes.create_string_buffer(payload) if payload is not None else None
        outgoing = ctypes.create_string_buffer(16384) if payload is None else None
        returned = wintypes.DWORD()
        if not api.DeviceIoControl(handle, code, incoming, len(payload) if payload is not None else 0,
                                   outgoing, len(outgoing) if outgoing is not None else 0,
                                   ctypes.byref(returned), None):
            raise ctypes.WinError(ctypes.get_last_error())
        return outgoing.raw[:returned.value] if outgoing is not None else None
    finally:
        api.CloseHandle(handle)


def read_point(path):
    return control(path, 0x000900A8)


def set_mtime(path, mtime_ns):
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    api.CreateFileW.restype = wintypes.HANDLE
    api.SetFileTime.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
                               ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME))
    api.SetFileTime.restype = wintypes.BOOL
    api.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = api.CreateFileW(str(Path(path).absolute()), 0x100, 7, None, 3, 0x02200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        ticks = mtime_ns // 100 + 116444736000000000
        value = wintypes.FILETIME(ticks & 0xffffffff, ticks >> 32)
        if not api.SetFileTime(handle, None, None, ctypes.byref(value)):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        api.CloseHandle(handle)


def restore_point(path, payload, mtime_ns, directory=False):
    path = Path(path)
    if reparse(path) or path.exists():
        raise FileExistsError('reparse restore destination already exists')
    path.parent.mkdir(parents=True, exist_ok=True)
    if directory:
        path.mkdir()
    else:
        with path.open('xb'):
            pass
    try:
        control(path, 0x000900A4, payload)
        set_mtime(path, mtime_ns)
        if read_point(path) != payload or path.lstat().st_mtime_ns != mtime_ns:
            raise ValueError('restored reparse payload/mtime mismatch')
    except BaseException:
        # Only this invocation's new placeholder; the preserved original stays intact.
        if directory:
            path.rmdir()
        else:
            path.unlink()
        raise
