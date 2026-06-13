# main.py
import sys
import ctypes
import tkinter as tk
from tkinter import ttk
import psutil

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
        self.root.geometry("900x600")

        self.tree = ttk.Treeview(root, columns=("pid", "name"), show="headings")
        self.tree.heading("pid", text="PID")
        self.tree.heading("name", text="プロセス名")
        self.tree.pack(fill=tk.BOTH, expand=True)

        frame = tk.Frame(root)
        frame.pack(fill=tk.X)

        tk.Button(frame, text="更新", command=self.refresh).pack(side=tk.LEFT)
        tk.Button(frame, text="効率モード適用", command=self.apply_selected).pack(side=tk.LEFT)

        self.refresh()

    def refresh(self):
        log("プロセス更新")
        for i in self.tree.get_children():
            self.tree.delete(i)

        for p in psutil.process_iter(["pid", "name"]):
            try:
                self.tree.insert("", "end", values=(p.info["pid"], p.info["name"]))
            except:
                pass

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