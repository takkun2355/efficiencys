# main.py
import sys
import ctypes
import tkinter as tk
from tkinter import ttk
import psutil
import threading
from tkinter import filedialog

import efficiency_all
import efficiency_all_clear
import efficiency_Acquisition
import efficiency_selection as eff
import task_control


# =========================
# 管理者チェック
# =========================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def relaunch_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )


# =========================
# ログ（uvでも見えるように強制flush）
# =========================

def log(msg):
    print(f"[ログ] {msg}", flush=True)


# =========================
# GUI
# =========================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("プロセス管理ツール")
        self.root.geometry("1000x700")
        self.root.after(1000, self.auto_refresh)
        
        # CPU初期化（これしないと全部0%）
        for p in psutil.process_iter():
            try:
                p.cpu_percent(None)
            except:
                pass

        # ===== Search =====
        self.search_var = tk.StringVar()

        search_frame = tk.Frame(root)
        search_frame.pack(fill=tk.X)

        tk.Label(search_frame, text="検索").pack(side=tk.LEFT)
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var
        )

        search_entry.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True
        )

        tk.Entry(
            search_frame,
            textvariable=self.search_var
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.search_var.trace_add("write", lambda *_: self.refresh())

        # ===== Tree =====
        tree_frame = tk.Frame(root)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(frame, orient="vertical")
        scroll_x = ttk.Scrollbar(frame, orient="horizontal")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=(
                "pid",
                "name",
                "cpu",
                "memory",
                "priority",
                "efficiency",
                "type"
            ),
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # columns
        cols = {
            "pid": "PID",
            "name": "Name",
            "cpu": "CPU%",
            "mem": "MEM(MB)",
            "prio": "Priority",
            "eff": "Efficiency",
            "type": "Type"
        }

        for c, t in cols.items():
            self.tree.heading(c, text=t, command=lambda x=c: self.sort_column(x))

        self.refresh()
        
        self.tree.heading(
            "type",
            text="分類",
            command=lambda:
            self.sort_column("type")
        )

        self.tree.heading(
            "pid",
            text="PID",
            command=lambda: self.sort_column("pid")
        )

        self.tree.heading(
            "name",
            text="プロセス名",
            command=lambda: self.sort_column("name")
        )

        self.tree.heading(
            "cpu",
            text="CPU %",
            command=lambda: self.sort_column("cpu")
        )

        self.tree.heading(
            "memory",
            text="メモリ MB",
            command=lambda: self.sort_column("memory")
        )

        self.tree.heading(
            "priority",
            text="優先度",
            command=lambda: self.sort_column("priority")
        )

        self.tree.heading(
            "efficiency",
            text="効率モード",
            command=lambda: self.sort_column("efficiency")
        )
        
        tk.Button(
            frame,
            text="選択プロセス終了",
            command=self.kill_selected
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            frame,
            text="プログラム起動",
            command=self.start_program
        ).pack(side=tk.LEFT, padx=5)

        self.tree.column("pid", width=80, anchor="center")
        self.tree.column("name", width=300)
        self.tree.column("type",width=100)
        self.tree.column("cpu", width=100, anchor="center")
        self.tree.column("memory", width=100, anchor="center")
        self.tree.column("priority", width=100, anchor="center")
        self.tree.column("efficiency", width=100, anchor="center")

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        frame = tk.Frame(root)
        frame.pack(fill=tk.X)

        tk.Button(
            frame,
            text="更新",
            command=self.refresh
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            frame,
            text="選択プロセス効率モードON",
            command=self.apply_selected
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            frame,
            text="全プロセス効率モードON",
            command=self.apply_all
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            frame,
            text="全プロセス効率モード解除",
            command=self.clear_all
        ).pack(side=tk.LEFT, padx=5)
        self.refresh()
        
    def get_priority_name(proc):

        try:
            mapping = {
                psutil.IDLE_PRIORITY_CLASS: "Idle",
                psutil.BELOW_NORMAL_PRIORITY_CLASS: "Below Normal",
                psutil.NORMAL_PRIORITY_CLASS: "Normal",
                psutil.ABOVE_NORMAL_PRIORITY_CLASS: "Above Normal",
                psutil.HIGH_PRIORITY_CLASS: "High",
                psutil.REALTIME_PRIORITY_CLASS: "Realtime",
            }

            return mapping.get(proc.nice(), str(proc.nice()))

        except:
            return "?"

    # =========================
    # refresh
    # =========================

    def refresh(self):
        log("refresh")

        search = self.search_var.get().lower().strip()

        self.tree.delete(*self.tree.get_children())

        for p in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                pid = p.pid
                name = p.name()

                if search and search not in name.lower():
                    continue

                cpu = p.cpu_percent(None)
                mem = p.memory_info().rss / 1024 / 1024

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        pid,
                        name,
                        f"{cpu:.1f}",
                        f"{mem:.1f}",
                        self.get_priority(p),
                        self.get_eff(pid),
                        self.get_type(p)
                    )
                )

            except:
                continue
            
    def has_window(pid):

        user32 = ctypes.windll.user32
        found = False

        @ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p
        )
        def enum_proc(hwnd, lparam):

            nonlocal found

            window_pid = ctypes.c_ulong()

            user32.GetWindowThreadProcessId(
                hwnd,
                ctypes.byref(window_pid)
            )

            if (
                window_pid.value == pid
                and user32.IsWindowVisible(hwnd)
            ):
                found = True
                return False

            return True

        user32.EnumWindows(
            enum_proc,
            0
        )

        return found
    
    # =========================
    # process helpers
    # =========================

    def get_priority(self, p):
        try:
            return {
                0: "Idle",
                1: "Below Normal",
                2: "Normal",
                3: "Above Normal",
                4: "High",
                5: "Realtime"
            }.get(p.nice(), "Unknown")
        except:
            return "?"

    def get_type(self, p):
        try:
            u = p.username().lower()
            if "system" in u:
                return "Windows"
            return "App"
        except:
            return "?"

    # efficiency状態（軽く）
    def get_eff(self, pid):
        return efficiency_Acquisition.is_efficiency_mode(pid)
            
    # =========================
    # sort
    # =========================

    def sort_column(self, col):
        items = [
            (self.tree.set(k, col), k)
            for k in self.tree.get_children()
        ]

        if col in ("pid", "cpu", "mem"):
            items.sort(key=lambda x: float(x[0] or 0))
        else:
            items.sort(key=lambda x: x[0])

        for i, (_, k) in enumerate(items):
            self.tree.move(k, "", i)
        
    def get_process_type(proc):

        try:

            username = proc.username().lower()

            if (
                "system"
                in username
            ):
                return "Windows"

            if (
                username.endswith(
                    "\\system"
                )
            ):
                return "Windows"

            if (
                username.endswith(
                    "\\local service"
                )
            ):
                return "Windows"

            if (
                username.endswith(
                    "\\network service"
                )
            ):
                return "Windows"

            return "アプリ"

        except:
            return "不明"
        
    # =========================
    # actions
    # =========================

    def get_selected_pid(self):
        item = self.tree.focus()
        if not item:
            return None
        return int(self.tree.item(item)["values"][0])

    def kill_selected(self):
        pid = self.get_selected_pid()
        if not pid:
            return
        ok, msg = task_control.kill_pid(pid)
        log(msg)
        self.refresh()

    def start_program(self):
        path = filedialog.askopenfilename(filetypes=[("exe", "*.exe")])
        if not path:
            return
        ok, msg = task_control.start_process(path)
        log(msg)
        self.refresh()

    def apply_selected(self):
        pid = self.get_selected_pid()
        if not pid:
            return
        ok, msg = eff.set_efficiency(pid)
        log(msg)

    def apply_all(self):
        threading.Thread(target=efficiency_all.main, daemon=True).start()

    def clear_all(self):
        threading.Thread(target=efficiency_all_clear.main, daemon=True).start()

    def get_selected_pid(self):
        item = self.tree.focus()
        if not item:
            return None
        return int(self.tree.item(item)["values"][0])
        
    def apply_all(self):
        log("全プロセス効率モードON開始")
        threading.Thread(
            target=efficiency_all.main,
            daemon=True
        ).start()


    def clear_all(self):
        log("全プロセス効率モード解除開始")
        threading.Thread(
            target=efficiency_all_clear.main,
            daemon=True
        ).start()
    
# =========================
# main
# =========================

if __name__ == "__main__":

    if not is_admin():
        log("管理者権限が必要 → 再起動")
        relaunch_as_admin()
        sys.exit()

    root = tk.Tk()
    App(root)
    root.mainloop()