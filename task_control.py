# task_control.py
import subprocess
import psutil


def kill_pid(pid: int):
    try:
        proc = psutil.Process(pid)
        proc.kill()
        return True, f"PID {pid} を終了"
    except Exception as e:
        return False, str(e)


def kill_name(name: str):
    count = 0

    for proc in psutil.process_iter(
        ["pid", "name"]
    ):
        try:
            if (
                proc.info["name"]
                and proc.info["name"].lower()
                == name.lower()
            ):
                proc.kill()
                count += 1

        except Exception:
            pass

    return True, f"{count}件終了"


def start_process(path: str):

    try:
        subprocess.Popen(path)

        return (
            True,
            f"起動: {path}"
        )

    except Exception as e:

        return (
            False,
            str(e)
        )


def get_process_info(pid: int):

    try:

        p = psutil.Process(pid)

        return {
            "pid": p.pid,
            "name": p.name(),
            "status": p.status(),
            "memory": p.memory_info().rss,
        }

    except Exception:

        return None