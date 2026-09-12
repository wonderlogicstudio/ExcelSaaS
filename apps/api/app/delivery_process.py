"""OS process memory/lifetime limits applied before any workbook data is sent."""

from __future__ import annotations

import os
from contextlib import contextmanager


@contextmanager
def process_limits(process):
    if os.name != "nt":
        import resource

        resource.prlimit(process.pid, resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
        resource.prlimit(process.pid, resource.RLIMIT_CORE, (0, 0))
        resource.prlimit(process.pid, resource.RLIMIT_FSIZE, (2 * 1024**2, 2 * 1024**2))
        yield
        return
    import ctypes
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class Counters(ctypes.Structure):
        _fields_ = [
            (name, ctypes.c_ulonglong)
            for name in [
                "ReadOperationCount",
                "WriteOperationCount",
                "OtherOperationCount",
                "ReadTransferCount",
                "WriteTransferCount",
                "OtherTransferCount",
            ]
        ]

    class Extended(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", Basic),
            ("IoInfo", Counters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise OSError("Could not create process limit")
    try:
        info = Extended()
        info.BasicLimitInformation.LimitFlags = 0x100 | 0x2000 | 0x8
        info.BasicLimitInformation.ActiveProcessLimit = 1
        info.ProcessMemoryLimit = 512 * 1024**2
        if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            raise OSError("Could not install process limits")
        if not kernel.AssignProcessToJobObject(handle, int(process._handle)):
            raise OSError("Could not bind process limits")
        yield
    finally:
        kernel.CloseHandle(handle)
