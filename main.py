#!/usr/bin/env python3
"""
ScpGUI - A WinSCP-like file transfer application
Supports SCP and SFTP protocols with a dual-pane file manager interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import os
import json
import datetime
import platform
from pathlib import Path

# Try to import paramiko, show helpful error if missing
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

# ─── Constants ────────────────────────────────────────────────────────────────
APP_NAME = "ScpGUI"
VERSION = "1.0.0"
CONFIG_DIR = Path.home() / ".scpgui"
BOOKMARKS_FILE = CONFIG_DIR / "bookmarks.json"
KNOWN_HOSTS_FILE = CONFIG_DIR / "known_hosts"

# Color palette – dark industrial terminal aesthetic
COLORS = {
    "bg":           "#0d1117",
    "bg2":          "#161b22",
    "bg3":          "#21262d",
    "border":       "#30363d",
    "accent":       "#58a6ff",
    "accent2":      "#3fb950",
    "warn":         "#d29922",
    "error":        "#f85149",
    "text":         "#e6edf3",
    "text_dim":     "#8b949e",
    "text_dimmer":  "#484f58",
    "selection":    "#1f4068",
    "header_bg":    "#0d1117",
    "log_bg":       "#010409",
}

FONTS = {
    "ui":     ("Consolas" if platform.system() == "Windows" else "Monaco" if platform.system() == "Darwin" else "DejaVu Sans Mono", 9),
    "ui_sm":  ("Consolas" if platform.system() == "Windows" else "Monaco" if platform.system() == "Darwin" else "DejaVu Sans Mono", 8),
    "ui_lg":  ("Consolas" if platform.system() == "Windows" else "Monaco" if platform.system() == "Darwin" else "DejaVu Sans Mono", 11),
    "mono":   ("Consolas" if platform.system() == "Windows" else "Monaco" if platform.system() == "Darwin" else "DejaVu Sans Mono", 9),
    "title":  ("Consolas" if platform.system() == "Windows" else "Monaco" if platform.system() == "Darwin" else "DejaVu Sans Mono", 13, "bold"),
}


# ─── Bookmark Model ───────────────────────────────────────────────────────────
class Bookmark:
    def __init__(self, name, host, port=22, username="", password="", key_path="", protocol="SFTP", remote_path="/"):
        self.name = name
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.key_path = key_path
        self.protocol = protocol
        self.remote_path = remote_path

    def to_dict(self):
        return {
            "name": self.name, "host": self.host, "port": self.port,
            "username": self.username, "password": self.password,
            "key_path": self.key_path, "protocol": self.protocol,
            "remote_path": self.remote_path,
        }

    @staticmethod
    def from_dict(d):
        return Bookmark(d.get("name",""), d.get("host",""), d.get("port",22),
                        d.get("username",""), d.get("password",""),
                        d.get("key_path",""), d.get("protocol","SFTP"),
                        d.get("remote_path","/"))


# ─── Bookmark Manager ─────────────────────────────────────────────────────────
class BookmarkManager:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.bookmarks: list[Bookmark] = []
        self.load()

    def load(self):
        if BOOKMARKS_FILE.exists():
            try:
                with open(BOOKMARKS_FILE) as f:
                    data = json.load(f)
                self.bookmarks = [Bookmark.from_dict(d) for d in data]
            except Exception:
                self.bookmarks = []

    def save(self):
        with open(BOOKMARKS_FILE, "w") as f:
            json.dump([b.to_dict() for b in self.bookmarks], f, indent=2)

    def add(self, bookmark: Bookmark):
        self.bookmarks.append(bookmark)
        self.save()

    def remove(self, index: int):
        if 0 <= index < len(self.bookmarks):
            self.bookmarks.pop(index)
            self.save()

    def update(self, index: int, bookmark: Bookmark):
        if 0 <= index < len(self.bookmarks):
            self.bookmarks[index] = bookmark
            self.save()


# ─── SSH Connection Manager ───────────────────────────────────────────────────
class SSHConnection:
    def __init__(self, bookmark: Bookmark, log_callback):
        self.bookmark = bookmark
        self.log = log_callback
        self.ssh: paramiko.SSHClient | None = None
        self.sftp: paramiko.SFTPClient | None = None
        self.connected = False

    def connect(self):
        if not PARAMIKO_AVAILABLE:
            raise RuntimeError("paramiko not installed. Run: pip install paramiko")

        self.log(f"[INFO] Connecting to {self.bookmark.username}@{self.bookmark.host}:{self.bookmark.port} via {self.bookmark.protocol}…")
        self.ssh = paramiko.SSHClient()

        # Load known hosts if file exists
        if KNOWN_HOSTS_FILE.exists():
            self.ssh.load_host_keys(str(KNOWN_HOSTS_FILE))
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self.bookmark.host,
            "port": self.bookmark.port,
            "username": self.bookmark.username,
            "timeout": 15,
        }

        if self.bookmark.key_path and os.path.exists(self.bookmark.key_path):
            self.log(f"[INFO] Using private key: {self.bookmark.key_path}")
            connect_kwargs["key_filename"] = self.bookmark.key_path
        elif self.bookmark.password:
            connect_kwargs["password"] = self.bookmark.password

        self.ssh.connect(**connect_kwargs)
        self.sftp = self.ssh.open_sftp()
        self.connected = True
        self.log(f"[OK]   Connected successfully to {self.bookmark.host}")

    def disconnect(self):
        if self.sftp:
            try: self.sftp.close()
            except: pass
        if self.ssh:
            try: self.ssh.close()
            except: pass
        self.connected = False
        self.log("[INFO] Disconnected.")

    def list_dir(self, path):
        if not self.connected:
            raise RuntimeError("Not connected")
        entries = []
        for attr in self.sftp.listdir_attr(path):
            is_dir = paramiko.stat.S_ISDIR(attr.st_mode) if attr.st_mode else False
            size = attr.st_size or 0
            mtime = datetime.datetime.fromtimestamp(attr.st_mtime).strftime("%Y-%m-%d %H:%M") if attr.st_mtime else ""
            entries.append({"name": attr.filename, "is_dir": is_dir, "size": size, "mtime": mtime})
        entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
        return entries

    def upload(self, local_path, remote_path, progress_cb=None):
        self.log(f"[UP]   {local_path} → {remote_path}")
        if progress_cb:
            total = os.path.getsize(local_path)
            def callback(transferred, total_size):
                pct = int(transferred / total_size * 100) if total_size else 100
                progress_cb(pct)
            self.sftp.put(local_path, remote_path, callback=callback)
        else:
            self.sftp.put(local_path, remote_path)
        self.log(f"[OK]   Uploaded {os.path.basename(local_path)}")

    def download(self, remote_path, local_path, progress_cb=None):
        self.log(f"[DOWN] {remote_path} → {local_path}")
        if progress_cb:
            stat = self.sftp.stat(remote_path)
            total = stat.st_size or 1
            def callback(transferred, total_size):
                pct = int(transferred / total_size * 100) if total_size else 100
                progress_cb(pct)
            self.sftp.get(remote_path, local_path, callback=callback)
        else:
            self.sftp.get(remote_path, local_path)
        self.log(f"[OK]   Downloaded {os.path.basename(remote_path)}")

    def mkdir(self, path):
        self.sftp.mkdir(path)

    def remove(self, path, is_dir=False):
        if is_dir:
            self.sftp.rmdir(path)
        else:
            self.sftp.remove(path)

    def rename(self, old_path, new_path):
        self.sftp.rename(old_path, new_path)

    def exec_command(self, cmd):
        _, stdout, stderr = self.ssh.exec_command(cmd)
        return stdout.read().decode(), stderr.read().decode()


# ─── Bookmark Dialog ──────────────────────────────────────────────────────────
class BookmarkDialog(tk.Toplevel):
    def __init__(self, parent, bookmark: Bookmark | None = None):
        super().__init__(parent)
        self.result: Bookmark | None = None
        self.bookmark = bookmark
        self.title("Edit Connection" if bookmark else "New Connection")
        self.configure(bg=COLORS["bg2"])
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if bookmark:
            self._populate(bookmark)
        self.wait_window()

    def _label(self, parent, text, row, col=0):
        lbl = tk.Label(parent, text=text, bg=COLORS["bg2"], fg=COLORS["text_dim"],
                       font=FONTS["ui_sm"], anchor="w")
        lbl.grid(row=row, column=col, sticky="w", padx=(12,4), pady=3)
        return lbl

    def _entry(self, parent, row, col=1, show=None, width=28):
        e = tk.Entry(parent, bg=COLORS["bg3"], fg=COLORS["text"], insertbackground=COLORS["accent"],
                     relief="flat", font=FONTS["mono"], width=width, show=show or "",
                     highlightthickness=1, highlightbackground=COLORS["border"],
                     highlightcolor=COLORS["accent"])
        e.grid(row=row, column=col, sticky="ew", padx=(4,12), pady=3)
        return e

    def _build(self):
        self.configure(padx=0, pady=0)
        # Title bar
        hdr = tk.Frame(self, bg=COLORS["bg"], pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  Connection Settings", bg=COLORS["bg"], fg=COLORS["accent"],
                 font=FONTS["title"]).pack(padx=16, anchor="w")

        sep = tk.Frame(self, bg=COLORS["border"], height=1)
        sep.pack(fill="x")

        frm = tk.Frame(self, bg=COLORS["bg2"])
        frm.pack(fill="both", expand=True, padx=0, pady=8)
        frm.columnconfigure(1, weight=1)

        self._label(frm, "Bookmark Name", 0)
        self.e_name = self._entry(frm, 0)

        self._label(frm, "Protocol", 1)
        self.proto_var = tk.StringVar(value="SFTP")
        proto_frame = tk.Frame(frm, bg=COLORS["bg2"])
        proto_frame.grid(row=1, column=1, sticky="w", padx=(4,12), pady=3)
        for p in ("SFTP", "SCP"):
            rb = tk.Radiobutton(proto_frame, text=p, variable=self.proto_var, value=p,
                                bg=COLORS["bg2"], fg=COLORS["text"], selectcolor=COLORS["bg3"],
                                activebackground=COLORS["bg2"], activeforeground=COLORS["accent"],
                                font=FONTS["ui"])
            rb.pack(side="left", padx=4)

        self._label(frm, "Hostname / IP", 2)
        self.e_host = self._entry(frm, 2)

        self._label(frm, "Port", 3)
        self.e_port = self._entry(frm, 3, width=8)
        self.e_port.insert(0, "22")

        self._label(frm, "Username", 4)
        self.e_user = self._entry(frm, 4)

        self._label(frm, "Password", 5)
        self.e_pass = self._entry(frm, 5, show="•")

        self._label(frm, "Private Key", 6)
        key_row = tk.Frame(frm, bg=COLORS["bg2"])
        key_row.grid(row=6, column=1, sticky="ew", padx=(4,12), pady=3)
        self.e_key = tk.Entry(key_row, bg=COLORS["bg3"], fg=COLORS["text"],
                              insertbackground=COLORS["accent"], relief="flat",
                              font=FONTS["mono"], width=20, highlightthickness=1,
                              highlightbackground=COLORS["border"], highlightcolor=COLORS["accent"])
        self.e_key.pack(side="left", fill="x", expand=True)
        tk.Button(key_row, text="…", bg=COLORS["bg3"], fg=COLORS["text_dim"],
                  font=FONTS["ui_sm"], relief="flat", cursor="hand2",
                  command=self._browse_key).pack(side="left", padx=(4,0))

        self._label(frm, "Remote Path", 7)
        self.e_rpath = self._entry(frm, 7)
        self.e_rpath.insert(0, "/")

        sep2 = tk.Frame(self, bg=COLORS["border"], height=1)
        sep2.pack(fill="x")

        btn_row = tk.Frame(self, bg=COLORS["bg2"], pady=10)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="Cancel", bg=COLORS["bg3"], fg=COLORS["text_dim"],
                  font=FONTS["ui"], relief="flat", cursor="hand2", padx=12,
                  command=self.destroy).pack(side="right", padx=(4,12))
        tk.Button(btn_row, text="Save", bg=COLORS["accent"], fg="#000000",
                  font=(*FONTS["ui"][:2], "bold"), relief="flat", cursor="hand2", padx=16,
                  command=self._save).pack(side="right", padx=4)

    def _browse_key(self):
        path = filedialog.askopenfilename(title="Select Private Key",
                                          filetypes=[("PEM/Key files", "*.pem *.key *.ppk *"),
                                                     ("All files", "*.*")])
        if path:
            self.e_key.delete(0, "end")
            self.e_key.insert(0, path)

    def _populate(self, b: Bookmark):
        self.e_name.insert(0, b.name)
        self.proto_var.set(b.protocol)
        self.e_host.insert(0, b.host)
        self.e_port.delete(0, "end"); self.e_port.insert(0, str(b.port))
        self.e_user.insert(0, b.username)
        self.e_pass.insert(0, b.password)
        self.e_key.insert(0, b.key_path)
        self.e_rpath.delete(0, "end"); self.e_rpath.insert(0, b.remote_path)

    def _save(self):
        name = self.e_name.get().strip()
        host = self.e_host.get().strip()
        if not name or not host:
            messagebox.showerror("Validation", "Name and Hostname are required.", parent=self)
            return
        try:
            port = int(self.e_port.get().strip())
        except ValueError:
            messagebox.showerror("Validation", "Port must be a number.", parent=self)
            return
        self.result = Bookmark(name, host, port, self.e_user.get().strip(),
                               self.e_pass.get(), self.e_key.get().strip(),
                               self.proto_var.get(), self.e_rpath.get().strip() or "/")
        self.destroy()


# ─── File Pane ────────────────────────────────────────────────────────────────
class FilePane(tk.Frame):
    """Dual-use file browser pane (local or remote)."""

    def __init__(self, parent, title, is_remote=False, **kwargs):
        super().__init__(parent, bg=COLORS["bg2"], **kwargs)
        self.is_remote = is_remote
        self.title = title
        self.current_path = str(Path.home()) if not is_remote else "/"
        self.entries: list[dict] = []
        self.conn: SSHConnection | None = None
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=COLORS["bg"], pady=6)
        hdr.pack(fill="x")
        icon = "☁" if self.is_remote else "💻"
        tk.Label(hdr, text=f"{icon}  {self.title}", bg=COLORS["bg"], fg=COLORS["accent"],
                 font=FONTS["ui_lg"]).pack(side="left", padx=12)

        if not self.is_remote:
            tk.Button(hdr, text="⌂", bg=COLORS["bg"], fg=COLORS["text_dim"],
                      relief="flat", font=FONTS["ui"], cursor="hand2",
                      command=self._go_home).pack(side="right", padx=4)

        sep = tk.Frame(self, bg=COLORS["border"], height=1)
        sep.pack(fill="x")

        # Path bar
        path_row = tk.Frame(self, bg=COLORS["bg3"], pady=5)
        path_row.pack(fill="x")
        tk.Button(path_row, text="↑", bg=COLORS["bg3"], fg=COLORS["text_dim"],
                  font=FONTS["ui"], relief="flat", cursor="hand2",
                  command=self.go_up).pack(side="left", padx=(8,4))
        self.path_var = tk.StringVar(value=self.current_path)
        path_entry = tk.Entry(path_row, textvariable=self.path_var, bg=COLORS["bg3"],
                              fg=COLORS["text"], insertbackground=COLORS["accent"],
                              relief="flat", font=FONTS["mono"],
                              highlightthickness=1, highlightbackground=COLORS["border"],
                              highlightcolor=COLORS["accent"])
        path_entry.pack(side="left", fill="x", expand=True, padx=4)
        path_entry.bind("<Return>", lambda e: self.navigate_to(self.path_var.get()))
        tk.Button(path_row, text="→", bg=COLORS["bg3"], fg=COLORS["text_dim"],
                  font=FONTS["ui"], relief="flat", cursor="hand2",
                  command=lambda: self.navigate_to(self.path_var.get())).pack(side="left", padx=(0,8))

        # File list with scrollbar
        list_frame = tk.Frame(self, bg=COLORS["bg2"])
        list_frame.pack(fill="both", expand=True)

        scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x = ttk.Scrollbar(list_frame, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview",
                         background=COLORS["bg2"], foreground=COLORS["text"],
                         fieldbackground=COLORS["bg2"], borderwidth=0,
                         font=FONTS["mono"], rowheight=22)
        style.configure("Custom.Treeview.Heading",
                         background=COLORS["bg3"], foreground=COLORS["text_dim"],
                         font=FONTS["ui_sm"], relief="flat", borderwidth=0)
        style.map("Custom.Treeview",
                  background=[("selected", COLORS["selection"])],
                  foreground=[("selected", COLORS["accent"])])
        style.map("Custom.Treeview.Heading", background=[("active", COLORS["bg3"])])

        self.tree = ttk.Treeview(list_frame, columns=("name", "size", "mtime"),
                                  show="headings", style="Custom.Treeview",
                                  yscrollcommand=scrollbar_y.set,
                                  xscrollcommand=scrollbar_x.set,
                                  selectmode="extended")
        self.tree.heading("name", text="Name", anchor="w")
        self.tree.heading("size", text="Size", anchor="e")
        self.tree.heading("mtime", text="Modified", anchor="w")
        self.tree.column("name", width=220, minwidth=120)
        self.tree.column("size", width=80, minwidth=60, anchor="e")
        self.tree.column("mtime", width=130, minwidth=100)
        self.tree.pack(fill="both", expand=True)
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        self.tree.bind("<Double-1>", self._on_double_click)

        # Status bar
        status_row = tk.Frame(self, bg=COLORS["bg3"], pady=3)
        status_row.pack(fill="x")
        self.status_var = tk.StringVar(value="")
        tk.Label(status_row, textvariable=self.status_var, bg=COLORS["bg3"],
                 fg=COLORS["text_dim"], font=FONTS["ui_sm"], anchor="w").pack(padx=8, fill="x")

        if not self.is_remote:
            self.refresh()

    def _go_home(self):
        self.navigate_to(str(Path.home()))

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if idx < len(self.entries):
            entry = self.entries[idx]
            if entry["is_dir"]:
                if self.is_remote:
                    new_path = self.current_path.rstrip("/") + "/" + entry["name"]
                    self.navigate_to(new_path)
                else:
                    new_path = os.path.join(self.current_path, entry["name"])
                    self.navigate_to(new_path)

    def navigate_to(self, path):
        self.current_path = path
        self.path_var.set(path)
        self.refresh()

    def go_up(self):
        if self.is_remote:
            parts = self.current_path.rstrip("/").rsplit("/", 1)
            parent = parts[0] if parts[0] else "/"
        else:
            parent = str(Path(self.current_path).parent)
        self.navigate_to(parent)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.entries = []
        if self.is_remote and self.conn and self.conn.connected:
            try:
                self.entries = self.conn.list_dir(self.current_path)
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                return
        elif not self.is_remote:
            try:
                raw = os.listdir(self.current_path)
                for name in sorted(raw, key=lambda n: (not os.path.isdir(os.path.join(self.current_path, n)), n.lower())):
                    full = os.path.join(self.current_path, name)
                    is_dir = os.path.isdir(full)
                    try:
                        size = os.path.getsize(full) if not is_dir else 0
                        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        size, mtime = 0, ""
                    self.entries.append({"name": name, "is_dir": is_dir, "size": size, "mtime": mtime})
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                return
        else:
            self.status_var.set("Not connected")
            return

        for entry in self.entries:
            icon = "📁 " if entry["is_dir"] else "📄 "
            size_str = "" if entry["is_dir"] else self._fmt_size(entry["size"])
            self.tree.insert("", "end", values=(icon + entry["name"], size_str, entry["mtime"]))

        count = len(self.entries)
        dirs = sum(1 for e in self.entries if e["is_dir"])
        files = count - dirs
        self.status_var.set(f"{dirs} folder(s), {files} file(s)")

    def _fmt_size(self, size):
        if size < 1024: return f"{size} B"
        if size < 1024**2: return f"{size/1024:.1f} KB"
        if size < 1024**3: return f"{size/1024**2:.1f} MB"
        return f"{size/1024**3:.2f} GB"

    def get_selected_entries(self):
        selected = []
        for item in self.tree.selection():
            idx = self.tree.index(item)
            if idx < len(self.entries):
                selected.append(self.entries[idx])
        return selected

    def set_connection(self, conn: SSHConnection | None):
        self.conn = conn
        if conn and conn.connected:
            self.navigate_to(conn.bookmark.remote_path)
        else:
            self.tree.delete(*self.tree.get_children())
            self.entries = []
            self.status_var.set("Not connected")


# ─── Main Application ─────────────────────────────────────────────────────────
class ScpGuiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME}  v{VERSION}")
        self.configure(bg=COLORS["bg"])
        self.geometry("1200x780")
        self.minsize(900, 600)

        self.bookmark_manager = BookmarkManager()
        self.conn: SSHConnection | None = None
        self.transfer_in_progress = False

        self._apply_styles()
        self._build_menu()
        self._build_ui()
        self._check_paramiko()

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TProgressbar", troughcolor=COLORS["bg3"],
                         background=COLORS["accent2"], borderwidth=0)

    def _check_paramiko(self):
        if not PARAMIKO_AVAILABLE:
            self.log("[WARN] paramiko not found. Install it: pip install paramiko", "warn")
            self.log("[WARN] File transfers will not work until paramiko is installed.", "warn")

    def _build_menu(self):
        menubar = tk.Menu(self, bg=COLORS["bg2"], fg=COLORS["text"],
                          activebackground=COLORS["selection"], activeforeground=COLORS["accent"],
                          relief="flat", border=0)
        # File menu
        file_menu = tk.Menu(menubar, tearoff=False, bg=COLORS["bg2"], fg=COLORS["text"],
                             activebackground=COLORS["selection"], activeforeground=COLORS["accent"])
        file_menu.add_command(label="New Bookmark…", command=self._add_bookmark)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Connection menu
        conn_menu = tk.Menu(menubar, tearoff=False, bg=COLORS["bg2"], fg=COLORS["text"],
                             activebackground=COLORS["selection"], activeforeground=COLORS["accent"])
        conn_menu.add_command(label="Connect Selected", command=self._connect)
        conn_menu.add_command(label="Disconnect", command=self._disconnect)
        menubar.add_cascade(label="Connection", menu=conn_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=False, bg=COLORS["bg2"], fg=COLORS["text"],
                             activebackground=COLORS["selection"], activeforeground=COLORS["accent"])
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_ui(self):
        # ── Top toolbar ──────────────────────────────────────────────────────
        toolbar = tk.Frame(self, bg=COLORS["bg"], pady=6, padx=8)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text=f"⚡ {APP_NAME}", bg=COLORS["bg"], fg=COLORS["accent"],
                 font=FONTS["title"]).pack(side="left", padx=(4,16))

        # Bookmark selector
        tk.Label(toolbar, text="Bookmark:", bg=COLORS["bg"], fg=COLORS["text_dim"],
                 font=FONTS["ui"]).pack(side="left")
        self.bookmark_var = tk.StringVar()
        self.bookmark_combo = ttk.Combobox(toolbar, textvariable=self.bookmark_var,
                                            state="readonly", width=24, font=FONTS["ui"])
        self.bookmark_combo.pack(side="left", padx=6)

        def styled_btn(parent, text, fg, cmd, side="left", padx=4):
            return tk.Button(parent, text=text, bg=COLORS["bg3"], fg=fg, font=FONTS["ui"],
                             relief="flat", cursor="hand2", padx=10, command=cmd).pack(side=side, padx=padx)

        tk.Button(toolbar, text="⊕ New", bg=COLORS["bg3"], fg=COLORS["text_dim"],
                  font=FONTS["ui"], relief="flat", cursor="hand2", padx=8,
                  command=self._add_bookmark).pack(side="left", padx=2)
        tk.Button(toolbar, text="✎ Edit", bg=COLORS["bg3"], fg=COLORS["text_dim"],
                  font=FONTS["ui"], relief="flat", cursor="hand2", padx=8,
                  command=self._edit_bookmark).pack(side="left", padx=2)
        tk.Button(toolbar, text="✕ Delete", bg=COLORS["bg3"], fg=COLORS["error"],
                  font=FONTS["ui"], relief="flat", cursor="hand2", padx=8,
                  command=self._delete_bookmark).pack(side="left", padx=2)

        sep = tk.Frame(toolbar, bg=COLORS["border"], width=1)
        sep.pack(side="left", fill="y", padx=12, pady=2)

        self.connect_btn = tk.Button(toolbar, text="▶ Connect", bg=COLORS["accent2"],
                                      fg="#000000", font=(*FONTS["ui"][:2], "bold"),
                                      relief="flat", cursor="hand2", padx=12,
                                      command=self._connect)
        self.connect_btn.pack(side="left", padx=4)

        self.disconnect_btn = tk.Button(toolbar, text="■ Disconnect", bg=COLORS["error"],
                                         fg="#ffffff", font=(*FONTS["ui"][:2], "bold"),
                                         relief="flat", cursor="hand2", padx=12,
                                         command=self._disconnect, state="disabled")
        self.disconnect_btn.pack(side="left", padx=4)

        # Connection status indicator
        self.status_dot = tk.Label(toolbar, text="●", bg=COLORS["bg"],
                                    fg=COLORS["text_dimmer"], font=(*FONTS["ui"][:2], "bold"))
        self.status_dot.pack(side="right", padx=(0,4))
        self.status_label = tk.Label(toolbar, text="Disconnected", bg=COLORS["bg"],
                                      fg=COLORS["text_dimmer"], font=FONTS["ui_sm"])
        self.status_label.pack(side="right")

        sep2 = tk.Frame(self, bg=COLORS["border"], height=1)
        sep2.pack(fill="x")

        # ── Main content area ────────────────────────────────────────────────
        main_pane = tk.PanedWindow(self, orient="vertical", bg=COLORS["border"],
                                    sashwidth=4, sashrelief="flat", handlesize=0)
        main_pane.pack(fill="both", expand=True)

        # File panes container
        file_area = tk.Frame(main_pane, bg=COLORS["border"])
        main_pane.add(file_area, minsize=300)

        # Transfer toolbar between panes
        dual_pane = tk.PanedWindow(file_area, orient="horizontal", bg=COLORS["border"],
                                    sashwidth=4, sashrelief="flat")
        dual_pane.pack(fill="both", expand=True)

        self.local_pane = FilePane(dual_pane, "Local Computer", is_remote=False)
        dual_pane.add(self.local_pane, minsize=300)

        # Center transfer panel
        xfer_panel = tk.Frame(file_area, bg=COLORS["bg2"], width=90)
        xfer_panel.pack_propagate(False)

        self.remote_pane = FilePane(dual_pane, "Remote Server", is_remote=True)
        dual_pane.add(self.remote_pane, minsize=300)

        # Transfer controls (overlaid)
        ctrl_frame = tk.Frame(self, bg=COLORS["bg"], pady=4)
        ctrl_frame.pack(fill="x")

        sep3 = tk.Frame(ctrl_frame, bg=COLORS["border"], height=1)
        sep3.pack(fill="x", pady=(0,6))

        inner = tk.Frame(ctrl_frame, bg=COLORS["bg"])
        inner.pack()

        self.upload_btn = tk.Button(inner, text="⬆  Upload  →", bg=COLORS["accent"],
                                     fg="#000000", font=(*FONTS["ui"][:2], "bold"),
                                     relief="flat", cursor="hand2", padx=16, pady=4,
                                     command=self._upload, state="disabled")
        self.upload_btn.pack(side="left", padx=8)

        self.download_btn = tk.Button(inner, text="←  Download  ⬇", bg=COLORS["accent"],
                                       fg="#000000", font=(*FONTS["ui"][:2], "bold"),
                                       relief="flat", cursor="hand2", padx=16, pady=4,
                                       command=self._download, state="disabled")
        self.download_btn.pack(side="left", padx=8)

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(inner, variable=self.progress_var, maximum=100,
                                         length=200, mode="determinate", style="TProgressbar")
        self.progress.pack(side="left", padx=16)

        self.progress_label = tk.Label(inner, text="", bg=COLORS["bg"],
                                        fg=COLORS["text_dim"], font=FONTS["ui_sm"])
        self.progress_label.pack(side="left")

        # ── Log area ─────────────────────────────────────────────────────────
        log_frame = tk.Frame(main_pane, bg=COLORS["bg"])
        main_pane.add(log_frame, minsize=120)

        log_header = tk.Frame(log_frame, bg=COLORS["bg3"], pady=4)
        log_header.pack(fill="x")
        tk.Label(log_header, text="📋  Session Log", bg=COLORS["bg3"], fg=COLORS["text_dim"],
                 font=FONTS["ui_sm"]).pack(side="left", padx=10)
        tk.Button(log_header, text="Clear", bg=COLORS["bg3"], fg=COLORS["text_dimmer"],
                  font=FONTS["ui_sm"], relief="flat", cursor="hand2",
                  command=self._clear_log).pack(side="right", padx=8)

        log_scroll = tk.Scrollbar(log_frame, bg=COLORS["bg3"])
        log_scroll.pack(side="right", fill="y")
        self.log_text = tk.Text(log_frame, bg=COLORS["log_bg"], fg=COLORS["text_dim"],
                                 font=FONTS["mono"], state="disabled", relief="flat",
                                 yscrollcommand=log_scroll.set, height=8, wrap="word",
                                 selectbackground=COLORS["selection"],
                                 insertbackground=COLORS["accent"])
        self.log_text.pack(fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)

        # Configure log text tags
        self.log_text.tag_configure("ok",   foreground=COLORS["accent2"])
        self.log_text.tag_configure("warn", foreground=COLORS["warn"])
        self.log_text.tag_configure("err",  foreground=COLORS["error"])
        self.log_text.tag_configure("info", foreground=COLORS["text_dim"])
        self.log_text.tag_configure("up",   foreground=COLORS["accent"])
        self.log_text.tag_configure("down", foreground="#c792ea")

        self._refresh_bookmark_list()
        self.log(f"[INFO] {APP_NAME} v{VERSION} started. Select a bookmark and click Connect.")

    # ── Bookmark management ───────────────────────────────────────────────────
    def _refresh_bookmark_list(self):
        names = [b.name for b in self.bookmark_manager.bookmarks]
        self.bookmark_combo["values"] = names
        if names and not self.bookmark_var.get():
            self.bookmark_combo.current(0)

    def _add_bookmark(self):
        dlg = BookmarkDialog(self)
        if dlg.result:
            self.bookmark_manager.add(dlg.result)
            self._refresh_bookmark_list()
            self.bookmark_combo.current(len(self.bookmark_manager.bookmarks) - 1)
            self.log(f"[INFO] Bookmark added: {dlg.result.name}")

    def _edit_bookmark(self):
        idx = self.bookmark_combo.current()
        if idx < 0:
            messagebox.showinfo("Edit", "Select a bookmark first.")
            return
        b = self.bookmark_manager.bookmarks[idx]
        dlg = BookmarkDialog(self, bookmark=b)
        if dlg.result:
            self.bookmark_manager.update(idx, dlg.result)
            self._refresh_bookmark_list()
            self.bookmark_combo.current(idx)
            self.log(f"[INFO] Bookmark updated: {dlg.result.name}")

    def _delete_bookmark(self):
        idx = self.bookmark_combo.current()
        if idx < 0:
            messagebox.showinfo("Delete", "Select a bookmark first.")
            return
        name = self.bookmark_manager.bookmarks[idx].name
        if messagebox.askyesno("Delete Bookmark", f"Delete '{name}'?"):
            self.bookmark_manager.remove(idx)
            self._refresh_bookmark_list()
            self.log(f"[INFO] Bookmark deleted: {name}")

    def _get_selected_bookmark(self) -> Bookmark | None:
        idx = self.bookmark_combo.current()
        if idx < 0 or idx >= len(self.bookmark_manager.bookmarks):
            return None
        return self.bookmark_manager.bookmarks[idx]

    # ── Connection management ─────────────────────────────────────────────────
    def _connect(self):
        b = self._get_selected_bookmark()
        if not b:
            messagebox.showinfo("Connect", "Select a bookmark first.")
            return
        if self.conn and self.conn.connected:
            self._disconnect()
        self.connect_btn.config(state="disabled")
        self._set_status("Connecting…", COLORS["warn"])
        threading.Thread(target=self._connect_thread, args=(b,), daemon=True).start()

    def _connect_thread(self, b: Bookmark):
        try:
            conn = SSHConnection(b, self.log)
            conn.connect()
            self.conn = conn
            self.after(0, self._on_connected)
        except Exception as e:
            self.log(f"[ERR]  Connection failed: {e}", "err")
            self.after(0, lambda: self._set_status("Connection failed", COLORS["error"]))
            self.after(0, lambda: self.connect_btn.config(state="normal"))

    def _on_connected(self):
        self.remote_pane.set_connection(self.conn)
        self._set_status(f"Connected: {self.conn.bookmark.host}", COLORS["accent2"])
        self.connect_btn.config(state="disabled")
        self.disconnect_btn.config(state="normal")
        self.upload_btn.config(state="normal")
        self.download_btn.config(state="normal")

    def _disconnect(self):
        if self.conn:
            self.conn.disconnect()
            self.conn = None
        self.remote_pane.set_connection(None)
        self._set_status("Disconnected", COLORS["text_dimmer"])
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        self.upload_btn.config(state="disabled")
        self.download_btn.config(state="disabled")

    def _set_status(self, text, color):
        self.status_label.config(text=text, fg=color)
        self.status_dot.config(fg=color)

    # ── Transfers ─────────────────────────────────────────────────────────────
    def _upload(self):
        if not self.conn or not self.conn.connected:
            messagebox.showinfo("Upload", "Not connected.")
            return
        files = self.local_pane.get_selected_entries()
        if not files:
            messagebox.showinfo("Upload", "Select files in the local pane.")
            return
        files = [f for f in files if not f["is_dir"]]
        if not files:
            messagebox.showinfo("Upload", "Directory upload not supported yet. Select files only.")
            return
        threading.Thread(target=self._transfer_thread,
                         args=(files, "upload"), daemon=True).start()

    def _download(self):
        if not self.conn or not self.conn.connected:
            messagebox.showinfo("Download", "Not connected.")
            return
        files = self.remote_pane.get_selected_entries()
        if not files:
            messagebox.showinfo("Download", "Select files in the remote pane.")
            return
        files = [f for f in files if not f["is_dir"]]
        if not files:
            messagebox.showinfo("Download", "Directory download not supported yet. Select files only.")
            return
        threading.Thread(target=self._transfer_thread,
                         args=(files, "download"), daemon=True).start()

    def _transfer_thread(self, files, direction):
        self.transfer_in_progress = True
        self.after(0, lambda: self.upload_btn.config(state="disabled"))
        self.after(0, lambda: self.download_btn.config(state="disabled"))
        total = len(files)
        for i, entry in enumerate(files):
            try:
                name = entry["name"]
                if direction == "upload":
                    local_path = os.path.join(self.local_pane.current_path, name)
                    remote_path = self.remote_pane.current_path.rstrip("/") + "/" + name
                    def prog(pct, file_label=name):
                        self.after(0, lambda: self._update_progress(pct, f"Uploading {file_label}"))
                    self.conn.upload(local_path, remote_path, prog)
                else:
                    remote_path = self.remote_pane.current_path.rstrip("/") + "/" + name
                    local_path = os.path.join(self.local_pane.current_path, name)
                    def prog(pct, file_label=name):
                        self.after(0, lambda: self._update_progress(pct, f"Downloading {file_label}"))
                    self.conn.download(remote_path, local_path, prog)
                self.after(0, lambda: self._update_progress(100, "Done"))
            except Exception as e:
                self.log(f"[ERR]  Transfer failed for {entry['name']}: {e}", "err")

        self.after(0, self._on_transfer_done)

    def _update_progress(self, pct, label=""):
        self.progress_var.set(pct)
        self.progress_label.config(text=f"{label} {pct}%")

    def _on_transfer_done(self):
        self.transfer_in_progress = False
        self.local_pane.refresh()
        self.remote_pane.refresh()
        self.upload_btn.config(state="normal")
        self.download_btn.config(state="normal")
        self.after(2000, lambda: self._update_progress(0, ""))
        self.log("[OK]   All transfers complete.")

    # ── Log ───────────────────────────────────────────────────────────────────
    def log(self, message: str, tag: str = "info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"

        # Auto-detect tag from prefix
        if tag == "info":
            msg_lower = message.lower()
            if "[ok]" in msg_lower:   tag = "ok"
            elif "[err]" in msg_lower: tag = "err"
            elif "[warn]" in msg_lower: tag = "warn"
            elif "[up]" in msg_lower:  tag = "up"
            elif "[down]" in msg_lower: tag = "down"

        self.log_text.config(state="normal")
        self.log_text.insert("end", line, tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    # ── About ─────────────────────────────────────────────────────────────────
    def _show_about(self):
        messagebox.showinfo("About ScpGUI",
                            f"{APP_NAME} v{VERSION}\n\n"
                            "A WinSCP-like file transfer client\n"
                            "supporting SFTP and SCP protocols.\n\n"
                            "Built with Python + Tkinter + Paramiko")


if __name__ == "__main__":
    app = ScpGuiApp()
    app.mainloop()
