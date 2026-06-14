# efficiency_Acquisition.py
import ctypes

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

ProcessPowerThrottling = 0

PROCESS_POWER_THROTTLING_CURRENT_VERSION = 1
PROCESS_POWER_THROTTLING_EXECUTION_SPEED = 0x1

kernel32 = ctypes.windll.kernel32


class PROCESS_POWER_THROTTLING_STATE(ctypes.Structure):
    _fields_ = [
        ("Version", ctypes.c_uint32),
        ("ControlMask", ctypes.c_uint32),
        ("StateMask", ctypes.c_uint32),
    ] 
    
def is_efficiency_mode(pid):

    handle = kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        pid
    )

    if not handle:
        return "?"

    try:

        state = PROCESS_POWER_THROTTLING_STATE()

        size = ctypes.c_ulong(
            ctypes.sizeof(state)
        )

        ok = kernel32.GetProcessInformation(
            handle,
            ProcessPowerThrottling,
            ctypes.byref(state),
            ctypes.sizeof(state)
        )

        if not ok:
            return "?"

        return (
            "ON"
            if (
                state.StateMask
                & PROCESS_POWER_THROTTLING_EXECUTION_SPEED
            )
            else "OFF"
        )

    except:
        return "?"

    finally:
        kernel32.CloseHandle(handle)
        
        