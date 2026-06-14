import ctypes
import sys
import subprocess
from typing import Set

import psutil

# Win32 constants
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_SET_INFORMATION = 0x0200

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

SYSTEM_PROCESS_NAMES = {
    "System",
    "System Idle Process",
    "Registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "winlogon.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
    "fontdrvhost.exe",
    "dwm.exe",
    "taskmgr.exe",
    "memcompression",
    "MemCompression",
    "ShellHost.exe",
    "ShellExperienceHost.exe",
    "StartMenuExperienceHost.exe",
    "RuntimeBroker.exe",
    "SearchHost.exe",
    "SearchIndexer.exe",
}

def get_service_pids() -> Set[int]:
    """
    稼働中の Windows サービスの ProcessId を PowerShell 経由で集める。
    """
    ps = r"""
    Get-CimInstance Win32_Service |
      Where-Object { $_.State -eq 'Running' -and $_.ProcessId -gt 0 } |
      Select-Object -ExpandProperty ProcessId
    """
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
    except Exception as e:
        print(f"[WARN] サービスPID取得失敗: {e}")
        return set()

    pids = set()
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pids.add(int(line))
        except ValueError:
            pass
    return pids

def set_efficiency_mode(pid: int) -> tuple[bool, str]:
    handle = kernel32.OpenProcess(
        PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        pid,
    )
    if not handle:
        return False, f"OpenProcess failed ({ctypes.get_last_error()})"

    try:
        state = PROCESS_POWER_THROTTLING_STATE()
        state.Version = PROCESS_POWER_THROTTLING_CURRENT_VERSION
        state.ControlMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED
        state.StateMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED

        ok = kernel32.SetProcessInformation(
            handle,
            ProcessPowerThrottling,
            ctypes.byref(state),
            ctypes.sizeof(state),
        )
        if not ok:
            return False, f"SetProcessInformation failed ({ctypes.get_last_error()})"
        return True, "OK"
    finally:
        kernel32.CloseHandle(handle)

def main():
    if sys.platform != "win32":
        print("Windows専用")
        return

    service_pids = get_service_pids()

    for proc in psutil.process_iter(["pid", "name"]):
        pid = proc.info["pid"]
        name = proc.info["name"] or ""

        if pid in service_pids:
            print(f"SKIP PID={pid:<6} {name:<35} service")
            continue

        if name in SYSTEM_PROCESS_NAMES:
            print(f"SKIP PID={pid:<6} {name:<35} system/core")
            continue

        try:
            ok, msg = set_efficiency_mode(pid)
            if ok:
                print(f"ON   PID={pid:<6} {name:<35} efficiency")
            else:
                print(f"FAIL PID={pid:<6} {name:<35} {msg}")
        except psutil.NoSuchProcess:
            continue
        except psutil.AccessDenied:
            print(f"SKIP PID={pid:<6} {name:<35} access denied")
        except Exception as e:
            print(f"FAIL PID={pid:<6} {name:<35} {e}")

if __name__ == "__main__":
    main()