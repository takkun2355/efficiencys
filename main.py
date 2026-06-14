# main.py
import sys
import ctypes
import tkinter as tk
from tkinter import ttk
import psutil
import threading

import efficiency_all
import efficiency_all_clear
import efficiency_selection as eff


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
        self.root.geometry("900x700")
        
        tree_frame = tk.Frame(root)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("pid", "name", "cpu", "memory"),
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
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

        self.tree.column("pid", width=80, anchor="center")
        self.tree.column("name", width=350)
        self.tree.column("cpu", width=100, anchor="center")
        self.tree.column("memory", width=120, anchor="center")

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

    def refresh(self):
        log("プロセス更新")

        for item in self.tree.get_children():
            self.tree.delete(item)

        for p in psutil.process_iter(
            ["pid", "name", "memory_info", "cpu_percent"]
        ):
            try:
                mem = p.info["memory_info"].rss / 1024 / 1024
                
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        p.info["pid"],
                        p.info["name"],
                        f"{p.cpu_percent():.1f}",
                        f"{mem:.1f}",
                    )
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ):
                pass
            
    def sort_column(self, col, reverse=False):
        data = [
            (self.tree.set(item, col), item)
            for item in self.tree.get_children("")
        ]

        if col in ("pid", "cpu", "memory"):
            data.sort(
                key=lambda x: float(x[0]) if x[0] else 0,
                reverse=reverse
            )
        else:
            data.sort(
                key=lambda x: x[0].lower(),
                reverse=reverse
            )

        for index, (_, item) in enumerate(data):
            self.tree.move(item, "", index)

        self.tree.heading(
            col,
            command=lambda: self.sort_column(col, not reverse)
        )

    def get_selected_pid(self):
        item = self.tree.focus()
        if not item:
            return None
        return int(self.tree.item(item)["values"][0])

    def apply_selected(self):
        pid = self.get_selected_pid()
        if not pid:
            log("未選択")
            return

        ok, msg = eff.set_efficiency(pid)
        log(f"PID {pid} -> {msg}")
        
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