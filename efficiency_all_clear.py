#effeciency_all_clear.py
import ctypes
import psutil
import sys

kernel32 = ctypes.windll.kernel32

PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000

def set_priority(pid: int):
    handle = kernel32.OpenProcess(
        PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION,
        False,
        pid
    )

    if not handle:
        return False, ctypes.get_last_error()

    try:
        ok = kernel32.SetPriorityClass(handle, ABOVE_NORMAL_PRIORITY_CLASS)
        if not ok:
            return False, ctypes.get_last_error()
        return True, "OK"
    finally:
        kernel32.CloseHandle(handle)


def main():
    if sys.platform != "win32":
        print("Windows専用")
        return

    for p in psutil.process_iter(["pid", "name"]):
        pid = p.info["pid"]
        name = p.info["name"] or ""

        try:
            ok, msg = set_priority(pid)

            if ok:
                print(f"BOOST  {pid:<6} {name:<30} ABOVE_NORMAL")
            else:
                print(f"FAIL   {pid:<6} {name:<30} {msg}")

        except psutil.AccessDenied:
            print(f"SKIP   {pid:<6} {name:<30} access denied")
        except psutil.NoSuchProcess:
            continue


if __name__ == "__main__":
    main()