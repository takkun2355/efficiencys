import ctypes

kernel32 = ctypes.windll.kernel32

PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

ProcessPowerThrottling = 0
PROCESS_POWER_THROTTLING_CURRENT_VERSION = 1
PROCESS_POWER_THROTTLING_EXECUTION_SPEED = 0x1


class STATE(ctypes.Structure):
    _fields_ = [
        ("Version", ctypes.c_uint32),
        ("ControlMask", ctypes.c_uint32),
        ("StateMask", ctypes.c_uint32),
    ]


def set_efficiency(pid: int):
    h = kernel32.OpenProcess(
        PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        pid
    )

    if not h:
        return False, "OpenProcess failed"

    try:
        s = STATE()
        s.Version = PROCESS_POWER_THROTTLING_CURRENT_VERSION
        s.ControlMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED
        s.StateMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED

        ok = kernel32.SetProcessInformation(
            h,
            ProcessPowerThrottling,
            ctypes.byref(s),
            ctypes.sizeof(s)
        )

        return ok, "OK" if ok else "FAIL"

    finally:
        kernel32.CloseHandle(h)