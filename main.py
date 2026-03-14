#!/usr/bin/env python3
"""
ScpGUI - A WinSCP-like file transfer application
Supports SCP and SFTP protocols with a dual-pane file manager interface.
Includes 15 preset themes with persistence.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import json
import datetime
import platform
from pathlib import Path

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

# ─── Constants ────────────────────────────────────────────────────────────────
APP_NAME = "ScpGUI"
VERSION  = "1.0.0"
CONFIG_DIR       = Path.home() / ".scpgui"
BOOKMARKS_FILE   = CONFIG_DIR / "bookmarks.json"
SETTINGS_FILE    = CONFIG_DIR / "settings.json"
KNOWN_HOSTS_FILE = CONFIG_DIR / "known_hosts"

_MONO = ("Consolas" if platform.system() == "Windows"
         else "Monaco" if platform.system() == "Darwin"
         else "DejaVu Sans Mono")

FONTS = {
    "ui":    (_MONO,  9),
    "ui_sm": (_MONO,  8),
    "ui_lg": (_MONO, 11),
    "mono":  (_MONO,  9),
    "title": (_MONO, 13, "bold"),
}

# ─── 15 Preset Themes ─────────────────────────────────────────────────────────
THEMES: dict[str, dict] = {
    "Dark Terminal": {
        "bg":"#0d1117","bg2":"#161b22","bg3":"#21262d","border":"#30363d",
        "accent":"#58a6ff","accent2":"#3fb950","warn":"#d29922","error":"#f85149",
        "text":"#e6edf3","text_dim":"#8b949e","text_dimmer":"#484f58",
        "selection":"#1f4068","log_bg":"#010409","btn_fg":"#000000",
    },
    "Neon Synthwave": {
        "bg":"#0f0e17","bg2":"#1a1a2e","bg3":"#16213e","border":"#533483",
        "accent":"#ff2a6d","accent2":"#05d9e8","warn":"#ffbe0b","error":"#ff2a6d",
        "text":"#f1f1ef","text_dim":"#a8a8b3","text_dimmer":"#533483",
        "selection":"#533483","log_bg":"#07060f","btn_fg":"#ffffff",
    },
    "Ocean Breeze": {
        "bg":"#0a192f","bg2":"#112240","bg3":"#1d3461","border":"#1d3461",
        "accent":"#64ffda","accent2":"#48cae4","warn":"#ffd166","error":"#ef476f",
        "text":"#ccd6f6","text_dim":"#8892b0","text_dimmer":"#495670",
        "selection":"#1d3461","log_bg":"#020c1b","btn_fg":"#000000",
    },
    "Vibrant Candy": {
        "bg":"#1a0533","bg2":"#2d0b59","bg3":"#3d1172","border":"#7b2d8b",
        "accent":"#ff6eb4","accent2":"#a8ff78","warn":"#ffcc02","error":"#ff4757",
        "text":"#ffffff","text_dim":"#cc99ff","text_dimmer":"#7b2d8b",
        "selection":"#7b2d8b","log_bg":"#0d001f","btn_fg":"#000000",
    },
    "Forest Hacker": {
        "bg":"#0b1a0b","bg2":"#0f2311","bg3":"#1a3a1a","border":"#2d5a2d",
        "accent":"#39ff14","accent2":"#7fff00","warn":"#ffd700","error":"#ff4444",
        "text":"#d4f5d4","text_dim":"#7db87d","text_dimmer":"#3a6b3a",
        "selection":"#1a4a1a","log_bg":"#040a04","btn_fg":"#000000",
    },
    "Sunset Fire": {
        "bg":"#1a0a00","bg2":"#2d1200","bg3":"#3d1f00","border":"#7a3500",
        "accent":"#ff6b35","accent2":"#ffd700","warn":"#ffaa00","error":"#ff2244",
        "text":"#fff5e6","text_dim":"#cc9966","text_dimmer":"#7a4a22",
        "selection":"#5c2800","log_bg":"#0d0500","btn_fg":"#000000",
    },
    "Arctic Ice": {
        "bg":"#f0f4f8","bg2":"#dde6ed","bg3":"#c9d6df","border":"#aab4be",
        "accent":"#0077b6","accent2":"#00b4d8","warn":"#e07a00","error":"#d62828",
        "text":"#1a1a2e","text_dim":"#4a6070","text_dimmer":"#8a9ab0",
        "selection":"#90e0ef","log_bg":"#e8f0f5","btn_fg":"#ffffff",
    },
    "Rose Gold": {
        "bg":"#1a0a0f","bg2":"#2d1520","bg3":"#3d1f2d","border":"#7a3555",
        "accent":"#ff85a1","accent2":"#ffc8dd","warn":"#ffb347","error":"#ff4466",
        "text":"#fff0f5","text_dim":"#cc8899","text_dimmer":"#7a4455",
        "selection":"#5c2240","log_bg":"#0d0508","btn_fg":"#000000",
    },
    "Cyber Yellow": {
        "bg":"#0d0d00","bg2":"#1a1a00","bg3":"#262600","border":"#4d4d00",
        "accent":"#f5f500","accent2":"#aaff00","warn":"#ff8800","error":"#ff2200",
        "text":"#fffff0","text_dim":"#b3b366","text_dimmer":"#666633",
        "selection":"#333300","log_bg":"#070700","btn_fg":"#000000",
    },
    "Dracula": {
        "bg":"#282a36","bg2":"#1e1f29","bg3":"#373844","border":"#44475a",
        "accent":"#bd93f9","accent2":"#50fa7b","warn":"#ffb86c","error":"#ff5555",
        "text":"#f8f8f2","text_dim":"#6272a4","text_dimmer":"#44475a",
        "selection":"#44475a","log_bg":"#191a21","btn_fg":"#000000",
    },
    "Monokai Vivid": {
        "bg":"#1e1e1e","bg2":"#272822","bg3":"#3e3d32","border":"#75715e",
        "accent":"#66d9e8","accent2":"#a6e22e","warn":"#e6db74","error":"#f92672",
        "text":"#f8f8f2","text_dim":"#75715e","text_dimmer":"#4f4a3a",
        "selection":"#49483e","log_bg":"#141414","btn_fg":"#000000",
    },
    "Solarized Dark": {
        "bg":"#002b36","bg2":"#073642","bg3":"#0d4455","border":"#586e75",
        "accent":"#268bd2","accent2":"#2aa198","warn":"#b58900","error":"#dc322f",
        "text":"#fdf6e3","text_dim":"#839496","text_dimmer":"#586e75",
        "selection":"#0d4455","log_bg":"#001b23","btn_fg":"#ffffff",
    },
    "Tokyo Night": {
        "bg":"#1a1b26","bg2":"#16161e","bg3":"#1f2335","border":"#292e42",
        "accent":"#7aa2f7","accent2":"#9ece6a","warn":"#e0af68","error":"#f7768e",
        "text":"#c0caf5","text_dim":"#565f89","text_dimmer":"#3b4261",
        "selection":"#2d3f76","log_bg":"#0d0e17","btn_fg":"#000000",
    },
    "Coral Reef": {
        "bg":"#fff8f0","bg2":"#ffe8d6","bg3":"#ffd5b5","border":"#ffb380",
        "accent":"#e05c00","accent2":"#00897b","warn":"#f57c00","error":"#c62828",
        "text":"#2d1600","text_dim":"#7a4522","text_dimmer":"#cc9977",
        "selection":"#ffc08a","log_bg":"#fff4e8","btn_fg":"#ffffff",
    },
    "Midnight Galaxy": {
        "bg":"#07071a","bg2":"#0d0d2b","bg3":"#14143d","border":"#2a2a6b",
        "accent":"#c084fc","accent2":"#34d399","warn":"#fbbf24","error":"#fb7185",
        "text":"#e2e8f0","text_dim":"#7c6fcd","text_dimmer":"#3b3580",
        "selection":"#2a2a6b","log_bg":"#030310","btn_fg":"#000000",
    },
}

# Active live color dict — mutated in-place on theme change
COLORS: dict[str, str] = dict(THEMES["Dark Terminal"])


# ─── Settings ─────────────────────────────────────────────────────────────────
class Settings:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.data: dict = {}
        self.load()

    def load(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE) as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def save(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()


# ─── Bookmark Model ───────────────────────────────────────────────────────────
class Bookmark:
    def __init__(self, name, host, port=22, username="", password="",
                 key_path="", protocol="SFTP", remote_path="/"):
        self.name = name; self.host = host; self.port = int(port)
        self.username = username; self.password = password
        self.key_path = key_path; self.protocol = protocol
        self.remote_path = remote_path

    def to_dict(self):
        return {"name":self.name,"host":self.host,"port":self.port,
                "username":self.username,"password":self.password,
                "key_path":self.key_path,"protocol":self.protocol,
                "remote_path":self.remote_path}

    @staticmethod
    def from_dict(d):
        return Bookmark(d.get("name",""),d.get("host",""),d.get("port",22),
                        d.get("username",""),d.get("password",""),
                        d.get("key_path",""),d.get("protocol","SFTP"),
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
                    self.bookmarks = [Bookmark.from_dict(d) for d in json.load(f)]
            except Exception:
                self.bookmarks = []

    def save(self):
        with open(BOOKMARKS_FILE,"w") as f:
            json.dump([b.to_dict() for b in self.bookmarks],f,indent=2)

    def add(self, b): self.bookmarks.append(b); self.save()
    def remove(self, i):
        if 0 <= i < len(self.bookmarks): self.bookmarks.pop(i); self.save()
    def update(self, i, b):
        if 0 <= i < len(self.bookmarks): self.bookmarks[i] = b; self.save()


# ─── SSH Connection ───────────────────────────────────────────────────────────
class SSHConnection:
    def __init__(self, bookmark: Bookmark, log_callback):
        self.bookmark = bookmark
        self.log = log_callback
        self.ssh = None; self.sftp = None; self.connected = False

    def connect(self):
        if not PARAMIKO_AVAILABLE:
            raise RuntimeError("paramiko not installed. Run: pip install paramiko")
        self.log(f"[INFO] Connecting to {self.bookmark.username}@{self.bookmark.host}:{self.bookmark.port} via {self.bookmark.protocol}…")
        self.ssh = paramiko.SSHClient()
        if KNOWN_HOSTS_FILE.exists():
            self.ssh.load_host_keys(str(KNOWN_HOSTS_FILE))
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kw = {"hostname":self.bookmark.host,"port":self.bookmark.port,
              "username":self.bookmark.username,"timeout":15}
        if self.bookmark.key_path and os.path.exists(self.bookmark.key_path):
            self.log(f"[INFO] Using private key: {self.bookmark.key_path}")
            kw["key_filename"] = self.bookmark.key_path
        elif self.bookmark.password:
            kw["password"] = self.bookmark.password
        self.ssh.connect(**kw)
        self.sftp = self.ssh.open_sftp()
        self.connected = True
        self.log(f"[OK]   Connected successfully to {self.bookmark.host}")

    def disconnect(self):
        for obj in (self.sftp, self.ssh):
            if obj:
                try: obj.close()
                except: pass
        self.connected = False
        self.log("[INFO] Disconnected.")

    def list_dir(self, path):
        if not self.connected: raise RuntimeError("Not connected")
        entries = []
        for attr in self.sftp.listdir_attr(path):
            is_dir = paramiko.stat.S_ISDIR(attr.st_mode) if attr.st_mode else False
            mtime = (datetime.datetime.fromtimestamp(attr.st_mtime).strftime("%Y-%m-%d %H:%M")
                     if attr.st_mtime else "")
            entries.append({"name":attr.filename,"is_dir":is_dir,
                            "size":attr.st_size or 0,"mtime":mtime})
        entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
        return entries

    def upload(self, local, remote, progress_cb=None):
        self.log(f"[UP]   {local} → {remote}")
        if progress_cb:
            def cb(t,tot): progress_cb(int(t/tot*100) if tot else 100)
            self.sftp.put(local, remote, callback=cb)
        else:
            self.sftp.put(local, remote)
        self.log(f"[OK]   Uploaded {os.path.basename(local)}")

    def download(self, remote, local, progress_cb=None):
        self.log(f"[DOWN] {remote} → {local}")
        if progress_cb:
            tot = self.sftp.stat(remote).st_size or 1
            def cb(t,_): progress_cb(int(t/tot*100))
            self.sftp.get(remote, local, callback=cb)
        else:
            self.sftp.get(remote, local)
        self.log(f"[OK]   Downloaded {os.path.basename(remote)}")


# ─── Theme Picker Dialog ──────────────────────────────────────────────────────
class ThemeDialog(tk.Toplevel):
    """Visual gallery of all 15 themes with colour swatches."""

    def __init__(self, parent, current_theme: str, on_apply):
        super().__init__(parent)
        self.on_apply = on_apply
        self.selected = current_theme
        self.card_widgets: dict[str, dict] = {}
        self.title("Choose Theme")
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)
        self.geometry("720x520")
        self.grab_set()
        self._build()
        self.wait_window()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=COLORS["bg"], pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🎨  Theme Gallery", bg=COLORS["bg"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(padx=16, anchor="w")
        tk.Label(hdr, text="Select a theme — it applies and saves instantly",
                 bg=COLORS["bg"], fg=COLORS["text_dim"],
                 font=FONTS["ui_sm"]).pack(padx=16, anchor="w")
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

        # Scrollable canvas
        outer = tk.Frame(self, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(outer, orient="vertical")
        vsb.pack(side="right", fill="y")
        canvas = tk.Canvas(outer, bg=COLORS["bg"], highlightthickness=0,
                           yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.config(command=canvas.yview)

        grid = tk.Frame(canvas, bg=COLORS["bg"])
        cwin = canvas.create_window((0,0), window=grid, anchor="nw")

        def _on_grid_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(cwin, width=canvas.winfo_width())
        grid.bind("<Configure>", _on_grid_cfg)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cwin, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        COLS = 3
        for idx, (name, t) in enumerate(THEMES.items()):
            row, col = divmod(idx, COLS)
            is_sel = (name == self.selected)

            card = tk.Frame(grid, bg=t["bg2"], highlightthickness=2,
                            highlightbackground=t["accent"] if is_sel else t["border"])
            card.grid(row=row, column=col, padx=8, pady=6, sticky="nsew")
            grid.columnconfigure(col, weight=1)

            # Colour swatch strip
            sw = tk.Frame(card, bg=t["bg2"])
            sw.pack(fill="x")
            for ck in ("bg","accent","accent2","warn","error","text_dim"):
                tk.Frame(sw, bg=t[ck], height=7).pack(side="left", fill="x", expand=True)

            body = tk.Frame(card, bg=t["bg2"], padx=8, pady=6)
            body.pack(fill="both", expand=True)

            name_lbl = tk.Label(body, text=name, bg=t["bg2"], fg=t["accent"],
                                font=(*FONTS["ui"][:2],"bold"), anchor="w")
            name_lbl.pack(fill="x")

            # Mini file list preview
            mini = tk.Frame(body, bg=t["bg3"], pady=2, padx=4)
            mini.pack(fill="x", pady=(4,0))
            for (txt, ck) in [("📁  Documents",    "text"),
                               ("📄  deploy.sh",    "text_dim"),
                               ("📄  config.yaml",  "text_dimmer")]:
                tk.Label(mini, text=txt, bg=t["bg3"], fg=t[ck],
                         font=FONTS["ui_sm"], anchor="w").pack(fill="x")

            # Apply button
            btn = tk.Button(body,
                            text="✓ Active" if is_sel else "Apply",
                            bg=t["accent"] if is_sel else t["bg3"],
                            fg=t["btn_fg"] if is_sel else t["text_dim"],
                            font=FONTS["ui_sm"], relief="flat", cursor="hand2")
            btn.pack(anchor="e", pady=(6,0))

            self.card_widgets[name] = {"card": card, "btn": btn, "t": t}

            def make_cmd(n=name):
                def cmd():
                    self._select(n)
                    self.on_apply(n)
                return cmd
            btn.config(command=make_cmd())
            card.bind("<Button-1>", lambda e, n=name: (self._select(n), self.on_apply(n)))

        # Footer
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")
        foot = tk.Frame(self, bg=COLORS["bg"], pady=8)
        foot.pack(fill="x")
        tk.Button(foot, text="Close", bg=COLORS["bg3"], fg=COLORS["text_dim"],
                  font=FONTS["ui"], relief="flat", cursor="hand2", padx=16,
                  command=self.destroy).pack(side="right", padx=12)

    def _select(self, name: str):
        # Deselect old
        if self.selected in self.card_widgets:
            old = self.card_widgets[self.selected]
            old["card"].configure(highlightbackground=old["t"]["border"])
            old["btn"].configure(text="Apply",
                                 bg=old["t"]["bg3"], fg=old["t"]["text_dim"])
        # Select new
        self.selected = name
        new = self.card_widgets[name]
        new["card"].configure(highlightbackground=new["t"]["accent"])
        new["btn"].configure(text="✓ Active",
                             bg=new["t"]["accent"], fg=new["t"]["btn_fg"])


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
        if bookmark: self._populate(bookmark)
        self.wait_window()

    def _lbl(self, p, text, row):
        tk.Label(p, text=text, bg=COLORS["bg2"], fg=COLORS["text_dim"],
                 font=FONTS["ui_sm"], anchor="w").grid(
                     row=row, column=0, sticky="w", padx=(12,4), pady=3)

    def _entry(self, p, row, show=None, width=28):
        e = tk.Entry(p, bg=COLORS["bg3"], fg=COLORS["text"],
                     insertbackground=COLORS["accent"], relief="flat",
                     font=FONTS["mono"], width=width, show=show or "",
                     highlightthickness=1, highlightbackground=COLORS["border"],
                     highlightcolor=COLORS["accent"])
        e.grid(row=row, column=1, sticky="ew", padx=(4,12), pady=3)
        return e

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["bg"], pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  Connection Settings", bg=COLORS["bg"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(padx=16, anchor="w")
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

        frm = tk.Frame(self, bg=COLORS["bg2"])
        frm.pack(fill="both", expand=True, pady=8)
        frm.columnconfigure(1, weight=1)

        self._lbl(frm,"Bookmark Name",0); self.e_name = self._entry(frm,0)
        self._lbl(frm,"Protocol",1)
        self.proto_var = tk.StringVar(value="SFTP")
        pf = tk.Frame(frm, bg=COLORS["bg2"])
        pf.grid(row=1, column=1, sticky="w", padx=(4,12), pady=3)
        for p in ("SFTP","SCP"):
            tk.Radiobutton(pf, text=p, variable=self.proto_var, value=p,
                           bg=COLORS["bg2"], fg=COLORS["text"],
                           selectcolor=COLORS["bg3"],
                           activebackground=COLORS["bg2"],
                           activeforeground=COLORS["accent"],
                           font=FONTS["ui"]).pack(side="left", padx=4)

        self._lbl(frm,"Hostname / IP",2); self.e_host = self._entry(frm,2)
        self._lbl(frm,"Port",3);          self.e_port = self._entry(frm,3,width=8)
        self.e_port.insert(0,"22")
        self._lbl(frm,"Username",4);      self.e_user = self._entry(frm,4)
        self._lbl(frm,"Password",5);      self.e_pass = self._entry(frm,5,show="•")
        self._lbl(frm,"Private Key",6)
        kr = tk.Frame(frm, bg=COLORS["bg2"])
        kr.grid(row=6, column=1, sticky="ew", padx=(4,12), pady=3)
        self.e_key = tk.Entry(kr, bg=COLORS["bg3"], fg=COLORS["text"],
                              insertbackground=COLORS["accent"], relief="flat",
                              font=FONTS["mono"], width=20, highlightthickness=1,
                              highlightbackground=COLORS["border"],
                              highlightcolor=COLORS["accent"])
        self.e_key.pack(side="left", fill="x", expand=True)
        tk.Button(kr, text="…", bg=COLORS["bg3"], fg=COLORS["text_dim"],
                  font=FONTS["ui_sm"], relief="flat", cursor="hand2",
                  command=self._browse_key).pack(side="left", padx=(4,0))

        self._lbl(frm,"Remote Path",7); self.e_rpath = self._entry(frm,7)
        self.e_rpath.insert(0,"/")

        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")
        br = tk.Frame(self, bg=COLORS["bg2"], pady=10)
        br.pack(fill="x")
        tk.Button(br, text="Cancel", bg=COLORS["bg3"], fg=COLORS["text_dim"],
                  font=FONTS["ui"], relief="flat", cursor="hand2", padx=12,
                  command=self.destroy).pack(side="right", padx=(4,12))
        tk.Button(br, text="Save", bg=COLORS["accent"], fg=COLORS["btn_fg"],
                  font=(*FONTS["ui"][:2],"bold"), relief="flat", cursor="hand2",
                  padx=16, command=self._save).pack(side="right", padx=4)

    def _browse_key(self):
        p = filedialog.askopenfilename(title="Select Private Key",
            filetypes=[("Key files","*.pem *.key *.ppk *"),("All","*.*")])
        if p: self.e_key.delete(0,"end"); self.e_key.insert(0,p)

    def _populate(self, b: Bookmark):
        self.e_name.insert(0,b.name); self.proto_var.set(b.protocol)
        self.e_host.insert(0,b.host)
        self.e_port.delete(0,"end"); self.e_port.insert(0,str(b.port))
        self.e_user.insert(0,b.username); self.e_pass.insert(0,b.password)
        self.e_key.insert(0,b.key_path)
        self.e_rpath.delete(0,"end"); self.e_rpath.insert(0,b.remote_path)

    def _save(self):
        name = self.e_name.get().strip(); host = self.e_host.get().strip()
        if not name or not host:
            messagebox.showerror("Validation","Name and Hostname are required.",parent=self); return
        try: port = int(self.e_port.get().strip())
        except ValueError:
            messagebox.showerror("Validation","Port must be a number.",parent=self); return
        self.result = Bookmark(name,host,port,self.e_user.get().strip(),
                               self.e_pass.get(),self.e_key.get().strip(),
                               self.proto_var.get(),self.e_rpath.get().strip() or "/")
        self.destroy()


# ─── File Pane ────────────────────────────────────────────────────────────────
class FilePane(tk.Frame):
    def __init__(self, parent, title, is_remote=False, **kwargs):
        super().__init__(parent, bg=COLORS["bg2"], **kwargs)
        self.is_remote = is_remote
        self.pane_title = title
        self.current_path = str(Path.home()) if not is_remote else "/"
        self.entries: list[dict] = []
        self.conn: SSHConnection | None = None
        self._build()

    def _build(self):
        self.hdr = tk.Frame(self, bg=COLORS["bg"], pady=6)
        self.hdr.pack(fill="x")
        icon = "☁" if self.is_remote else "💻"
        self.hdr_lbl = tk.Label(self.hdr, text=f"{icon}  {self.pane_title}",
                                 bg=COLORS["bg"], fg=COLORS["accent"], font=FONTS["ui_lg"])
        self.hdr_lbl.pack(side="left", padx=12)
        if not self.is_remote:
            self.home_btn = tk.Button(self.hdr, text="⌂", bg=COLORS["bg"],
                                      fg=COLORS["text_dim"], relief="flat",
                                      font=FONTS["ui"], cursor="hand2",
                                      command=lambda: self.navigate_to(str(Path.home())))
            self.home_btn.pack(side="right", padx=4)

        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x")

        self.path_row = tk.Frame(self, bg=COLORS["bg3"], pady=5)
        self.path_row.pack(fill="x")
        self.up_btn = tk.Button(self.path_row, text="↑", bg=COLORS["bg3"],
                                 fg=COLORS["text_dim"], font=FONTS["ui"],
                                 relief="flat", cursor="hand2", command=self.go_up)
        self.up_btn.pack(side="left", padx=(8,4))
        self.path_var = tk.StringVar(value=self.current_path)
        self.path_entry = tk.Entry(self.path_row, textvariable=self.path_var,
                                    bg=COLORS["bg3"], fg=COLORS["text"],
                                    insertbackground=COLORS["accent"], relief="flat",
                                    font=FONTS["mono"], highlightthickness=1,
                                    highlightbackground=COLORS["border"],
                                    highlightcolor=COLORS["accent"])
        self.path_entry.pack(side="left", fill="x", expand=True, padx=4)
        self.path_entry.bind("<Return>", lambda e: self.navigate_to(self.path_var.get()))
        self.go_btn = tk.Button(self.path_row, text="→", bg=COLORS["bg3"],
                                 fg=COLORS["text_dim"], font=FONTS["ui"],
                                 relief="flat", cursor="hand2",
                                 command=lambda: self.navigate_to(self.path_var.get()))
        self.go_btn.pack(side="left", padx=(0,8))

        list_frame = tk.Frame(self, bg=COLORS["bg2"])
        list_frame.pack(fill="both", expand=True)
        sy = ttk.Scrollbar(list_frame, orient="vertical")
        sy.pack(side="right", fill="y")
        sx = ttk.Scrollbar(list_frame, orient="horizontal")
        sx.pack(side="bottom", fill="x")

        self._apply_tree_style()
        self.tree = ttk.Treeview(list_frame, columns=("name","size","mtime"),
                                  show="headings", style="Custom.Treeview",
                                  yscrollcommand=sy.set, xscrollcommand=sx.set,
                                  selectmode="extended")
        for col,lbl,w,anch in [("name","Name",220,"w"),("size","Size",80,"e"),("mtime","Modified",130,"w")]:
            self.tree.heading(col, text=lbl, anchor=anch)
            self.tree.column(col, width=w, minwidth=60, anchor=anch)
        self.tree.pack(fill="both", expand=True)
        sy.config(command=self.tree.yview); sx.config(command=self.tree.xview)
        self.tree.bind("<Double-1>", self._on_double_click)

        self.status_bar = tk.Frame(self, bg=COLORS["bg3"], pady=3)
        self.status_bar.pack(fill="x")
        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(self.status_bar, textvariable=self.status_var,
                                    bg=COLORS["bg3"], fg=COLORS["text_dim"],
                                    font=FONTS["ui_sm"], anchor="w")
        self.status_lbl.pack(padx=8, fill="x")

        if not self.is_remote:
            self.refresh()

    def _apply_tree_style(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("Custom.Treeview",
                     background=COLORS["bg2"], foreground=COLORS["text"],
                     fieldbackground=COLORS["bg2"], borderwidth=0,
                     font=FONTS["mono"], rowheight=22)
        s.configure("Custom.Treeview.Heading",
                     background=COLORS["bg3"], foreground=COLORS["text_dim"],
                     font=FONTS["ui_sm"], relief="flat", borderwidth=0)
        s.map("Custom.Treeview",
              background=[("selected", COLORS["selection"])],
              foreground=[("selected",  COLORS["accent"])])

    def apply_theme(self):
        self._apply_tree_style()
        self.configure(bg=COLORS["bg2"])
        self.hdr.configure(bg=COLORS["bg"])
        self.hdr_lbl.configure(bg=COLORS["bg"], fg=COLORS["accent"])
        if hasattr(self,"home_btn"):
            self.home_btn.configure(bg=COLORS["bg"], fg=COLORS["text_dim"])
        self.path_row.configure(bg=COLORS["bg3"])
        self.up_btn.configure(bg=COLORS["bg3"], fg=COLORS["text_dim"])
        self.path_entry.configure(bg=COLORS["bg3"], fg=COLORS["text"],
                                   insertbackground=COLORS["accent"],
                                   highlightbackground=COLORS["border"],
                                   highlightcolor=COLORS["accent"])
        self.go_btn.configure(bg=COLORS["bg3"], fg=COLORS["text_dim"])
        self.status_bar.configure(bg=COLORS["bg3"])
        self.status_lbl.configure(bg=COLORS["bg3"], fg=COLORS["text_dim"])
        self.refresh()

    def _on_double_click(self, _):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        if idx < len(self.entries) and self.entries[idx]["is_dir"]:
            if self.is_remote:
                self.navigate_to(self.current_path.rstrip("/")+"/"+self.entries[idx]["name"])
            else:
                self.navigate_to(os.path.join(self.current_path, self.entries[idx]["name"]))

    def navigate_to(self, path):
        self.current_path = path; self.path_var.set(path); self.refresh()

    def go_up(self):
        if self.is_remote:
            parts = self.current_path.rstrip("/").rsplit("/",1)
            parent = parts[0] if parts[0] else "/"
        else:
            parent = str(Path(self.current_path).parent)
        self.navigate_to(parent)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.entries = []
        if self.is_remote:
            if not (self.conn and self.conn.connected):
                self.status_var.set("Not connected"); return
            try: self.entries = self.conn.list_dir(self.current_path)
            except Exception as e: self.status_var.set(f"Error: {e}"); return
        else:
            try:
                for name in sorted(os.listdir(self.current_path),
                                   key=lambda n:(not os.path.isdir(os.path.join(self.current_path,n)),n.lower())):
                    full = os.path.join(self.current_path, name)
                    is_dir = os.path.isdir(full)
                    try: size = os.path.getsize(full) if not is_dir else 0
                    except: size = 0
                    try: mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M")
                    except: mtime = ""
                    self.entries.append({"name":name,"is_dir":is_dir,"size":size,"mtime":mtime})
            except Exception as e: self.status_var.set(f"Error: {e}"); return

        for e in self.entries:
            icon = "📁 " if e["is_dir"] else "📄 "
            self.tree.insert("","end",values=(
                icon+e["name"], "" if e["is_dir"] else self._fmt(e["size"]), e["mtime"]))
        dirs = sum(1 for e in self.entries if e["is_dir"])
        self.status_var.set(f"{dirs} folder(s), {len(self.entries)-dirs} file(s)")

    def _fmt(self, s):
        if s < 1024:    return f"{s} B"
        if s < 1024**2: return f"{s/1024:.1f} KB"
        if s < 1024**3: return f"{s/1024**2:.1f} MB"
        return f"{s/1024**3:.2f} GB"

    def get_selected_entries(self):
        return [self.entries[self.tree.index(i)]
                for i in self.tree.selection()
                if self.tree.index(i) < len(self.entries)]

    def set_connection(self, conn):
        self.conn = conn
        if conn and conn.connected: self.navigate_to(conn.bookmark.remote_path)
        else:
            self.tree.delete(*self.tree.get_children())
            self.entries = []; self.status_var.set("Not connected")


# ─── Main Application ─────────────────────────────────────────────────────────
class ScpGuiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.bookmark_manager = BookmarkManager()
        self.conn: SSHConnection | None = None
        self.transfer_in_progress = False

        # Load saved theme before building UI
        saved = self.settings.get("theme", "Dark Terminal")
        if saved not in THEMES: saved = "Dark Terminal"
        self._current_theme = saved
        COLORS.update(THEMES[saved])

        self.title(f"{APP_NAME}  v{VERSION}")
        self.configure(bg=COLORS["bg"])
        self.geometry("1200x780")
        self.minsize(900, 600)

        self._seps: list[tk.Widget] = []
        self._apply_ttk_styles()
        self._build_menu()
        self._build_ui()
        self._check_paramiko()

    # ── Theme engine ──────────────────────────────────────────────────────────
    def apply_theme(self, name: str):
        if name not in THEMES: return
        self._current_theme = name
        COLORS.update(THEMES[name])
        self.settings.set("theme", name)
        self._apply_ttk_styles()
        self._recolour_all()
        self.log(f"[INFO] Theme changed to: {name}")

    def _apply_ttk_styles(self):
        s = ttk.Style(self)
        s.theme_use("default")
        s.configure("TProgressbar", troughcolor=COLORS["bg3"],
                    background=COLORS["accent2"], borderwidth=0)
        s.configure("TCombobox", fieldbackground=COLORS["bg3"],
                    background=COLORS["bg3"], foreground=COLORS["text"],
                    selectbackground=COLORS["selection"],
                    selectforeground=COLORS["accent"])
        s.map("TCombobox",
              fieldbackground=[("readonly", COLORS["bg3"])],
              foreground=[("readonly", COLORS["text"])],
              selectbackground=[("readonly", COLORS["selection"])])

    def _recolour_all(self):
        self.configure(bg=COLORS["bg"])
        try:
            self.app_lbl.configure(bg=COLORS["bg"], fg=COLORS["accent"])
            self.bm_lbl.configure(bg=COLORS["bg"], fg=COLORS["text_dim"])
            self.toolbar.configure(bg=COLORS["bg"])
            self.new_btn.configure(bg=COLORS["bg3"],  fg=COLORS["text_dim"])
            self.edit_btn.configure(bg=COLORS["bg3"], fg=COLORS["text_dim"])
            self.del_btn.configure(bg=COLORS["bg3"],  fg=COLORS["error"])
            self.theme_btn.configure(bg=COLORS["bg3"], fg=COLORS["accent"])
            self.connect_btn.configure(bg=COLORS["accent2"], fg="#000000")
            self.disconnect_btn.configure(bg=COLORS["error"], fg="#ffffff")
            self.status_dot.configure(bg=COLORS["bg"])
            self.status_lbl_w.configure(bg=COLORS["bg"])
            self.ctrl_frame.configure(bg=COLORS["bg"])
            self.ctrl_inner.configure(bg=COLORS["bg"])
            self.upload_btn.configure(bg=COLORS["accent"],  fg=COLORS["btn_fg"])
            self.download_btn.configure(bg=COLORS["accent"], fg=COLORS["btn_fg"])
            self.prog_lbl.configure(bg=COLORS["bg"], fg=COLORS["text_dim"])
            self.log_frame.configure(bg=COLORS["bg"])
            self.log_hdr.configure(bg=COLORS["bg3"])
            self.log_hdr_lbl.configure(bg=COLORS["bg3"], fg=COLORS["text_dim"])
            self.log_clear_btn.configure(bg=COLORS["bg3"], fg=COLORS["text_dimmer"])
            self.log_scroll.configure(bg=COLORS["bg3"])
            self.log_text.configure(bg=COLORS["log_bg"], fg=COLORS["text_dim"],
                                     selectbackground=COLORS["selection"],
                                     insertbackground=COLORS["accent"])
            self.log_text.tag_configure("ok",   foreground=COLORS["accent2"])
            self.log_text.tag_configure("warn", foreground=COLORS["warn"])
            self.log_text.tag_configure("err",  foreground=COLORS["error"])
            self.log_text.tag_configure("info", foreground=COLORS["text_dim"])
            self.log_text.tag_configure("up",   foreground=COLORS["accent"])
            self.log_text.tag_configure("down", foreground=COLORS["accent2"])
            for sep in self._seps:
                sep.configure(bg=COLORS["border"])
        except Exception:
            pass
        if hasattr(self,"local_pane"):  self.local_pane.apply_theme()
        if hasattr(self,"remote_pane"): self.remote_pane.apply_theme()
        self._rebuild_menu()

    # ── Menu ──────────────────────────────────────────────────────────────────
    def _build_menu(self):
        self._mbar = tk.Menu(self, bg=COLORS["bg2"], fg=COLORS["text"],
                              activebackground=COLORS["selection"],
                              activeforeground=COLORS["accent"],
                              relief="flat", border=0)

        def _menu(label, items):
            m = tk.Menu(self._mbar, tearoff=False, bg=COLORS["bg2"], fg=COLORS["text"],
                         activebackground=COLORS["selection"],
                         activeforeground=COLORS["accent"])
            for item in items:
                if item is None: m.add_separator()
                else: m.add_command(label=item[0], command=item[1])
            self._mbar.add_cascade(label=label, menu=m)
            return m

        _menu("File", [("New Bookmark…", self._add_bookmark), None, ("Quit", self.quit)])
        _menu("Connection", [("Connect Selected", self._connect), ("Disconnect", self._disconnect)])
        _menu("View", [("🎨 Choose Theme…", self._open_theme_dialog)])
        _menu("Help", [("About", self._show_about)])
        self.config(menu=self._mbar)

    def _rebuild_menu(self):
        try:
            self._mbar.configure(bg=COLORS["bg2"], fg=COLORS["text"],
                                  activebackground=COLORS["selection"],
                                  activeforeground=COLORS["accent"])
            for i in range(self._mbar.index("end")+1):
                try:
                    sub = self._mbar.nametowidget(self._mbar.entrycget(i,"menu"))
                    sub.configure(bg=COLORS["bg2"], fg=COLORS["text"],
                                  activebackground=COLORS["selection"],
                                  activeforeground=COLORS["accent"])
                except Exception: pass
        except Exception: pass

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Toolbar
        self.toolbar = tk.Frame(self, bg=COLORS["bg"], pady=6, padx=8)
        self.toolbar.pack(fill="x")

        self.app_lbl = tk.Label(self.toolbar, text=f"⚡ {APP_NAME}",
                                 bg=COLORS["bg"], fg=COLORS["accent"], font=FONTS["title"])
        self.app_lbl.pack(side="left", padx=(4,16))

        self.bm_lbl = tk.Label(self.toolbar, text="Bookmark:",
                                bg=COLORS["bg"], fg=COLORS["text_dim"], font=FONTS["ui"])
        self.bm_lbl.pack(side="left")

        self.bookmark_var = tk.StringVar()
        self.bookmark_combo = ttk.Combobox(self.toolbar, textvariable=self.bookmark_var,
                                            state="readonly", width=22, font=FONTS["ui"])
        self.bookmark_combo.pack(side="left", padx=6)

        def _tbtn(text, fg, cmd, padx_=2):
            b = tk.Button(self.toolbar, text=text, bg=COLORS["bg3"], fg=fg,
                          font=FONTS["ui"], relief="flat", cursor="hand2",
                          padx=8, command=cmd)
            b.pack(side="left", padx=padx_)
            return b

        self.new_btn  = _tbtn("⊕ New",    COLORS["text_dim"], self._add_bookmark)
        self.edit_btn = _tbtn("✎ Edit",   COLORS["text_dim"], self._edit_bookmark)
        self.del_btn  = _tbtn("✕ Delete", COLORS["error"],    self._delete_bookmark)

        sep1 = tk.Frame(self.toolbar, bg=COLORS["border"], width=1)
        sep1.pack(side="left", fill="y", padx=10, pady=2)
        self._seps.append(sep1)

        self.connect_btn = tk.Button(self.toolbar, text="▶ Connect",
                                      bg=COLORS["accent2"], fg="#000000",
                                      font=(*FONTS["ui"][:2],"bold"),
                                      relief="flat", cursor="hand2", padx=12,
                                      command=self._connect)
        self.connect_btn.pack(side="left", padx=4)

        self.disconnect_btn = tk.Button(self.toolbar, text="■ Disconnect",
                                         bg=COLORS["error"], fg="#ffffff",
                                         font=(*FONTS["ui"][:2],"bold"),
                                         relief="flat", cursor="hand2", padx=12,
                                         command=self._disconnect, state="disabled")
        self.disconnect_btn.pack(side="left", padx=4)

        # Theme button (right side of toolbar)
        self.theme_btn = tk.Button(self.toolbar, text="🎨 Theme",
                                    bg=COLORS["bg3"], fg=COLORS["accent"],
                                    font=FONTS["ui"], relief="flat",
                                    cursor="hand2", padx=10,
                                    command=self._open_theme_dialog)
        self.theme_btn.pack(side="right", padx=(4,8))

        # Status indicator
        self.status_dot = tk.Label(self.toolbar, text="●", bg=COLORS["bg"],
                                    fg=COLORS["text_dimmer"],
                                    font=(*FONTS["ui"][:2],"bold"))
        self.status_dot.pack(side="right", padx=(0,2))
        self.status_lbl_w = tk.Label(self.toolbar, text="Disconnected",
                                      bg=COLORS["bg"], fg=COLORS["text_dimmer"],
                                      font=FONTS["ui_sm"])
        self.status_lbl_w.pack(side="right", padx=(0,4))

        sep2 = tk.Frame(self, bg=COLORS["border"], height=1)
        sep2.pack(fill="x")
        self._seps.append(sep2)

        # Main split pane
        main_pane = tk.PanedWindow(self, orient="vertical", bg=COLORS["border"],
                                    sashwidth=4, sashrelief="flat", handlesize=0)
        main_pane.pack(fill="both", expand=True)

        file_area = tk.Frame(main_pane, bg=COLORS["border"])
        main_pane.add(file_area, minsize=300)

        dual_pane = tk.PanedWindow(file_area, orient="horizontal", bg=COLORS["border"],
                                    sashwidth=4, sashrelief="flat")
        dual_pane.pack(fill="both", expand=True)

        self.local_pane  = FilePane(dual_pane, "Local Computer",  is_remote=False)
        self.remote_pane = FilePane(dual_pane, "Remote Server",   is_remote=True)
        dual_pane.add(self.local_pane,  minsize=300)
        dual_pane.add(self.remote_pane, minsize=300)

        # Transfer controls
        self.ctrl_frame = tk.Frame(self, bg=COLORS["bg"], pady=4)
        self.ctrl_frame.pack(fill="x")

        sep3 = tk.Frame(self.ctrl_frame, bg=COLORS["border"], height=1)
        sep3.pack(fill="x", pady=(0,6))
        self._seps.append(sep3)

        self.ctrl_inner = tk.Frame(self.ctrl_frame, bg=COLORS["bg"])
        self.ctrl_inner.pack()

        self.upload_btn = tk.Button(self.ctrl_inner, text="⬆  Upload  →",
                                     bg=COLORS["accent"], fg=COLORS["btn_fg"],
                                     font=(*FONTS["ui"][:2],"bold"), relief="flat",
                                     cursor="hand2", padx=16, pady=4,
                                     command=self._upload, state="disabled")
        self.upload_btn.pack(side="left", padx=8)

        self.download_btn = tk.Button(self.ctrl_inner, text="←  Download  ⬇",
                                       bg=COLORS["accent"], fg=COLORS["btn_fg"],
                                       font=(*FONTS["ui"][:2],"bold"), relief="flat",
                                       cursor="hand2", padx=16, pady=4,
                                       command=self._download, state="disabled")
        self.download_btn.pack(side="left", padx=8)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(self.ctrl_inner, variable=self.progress_var,
                                         maximum=100, length=200, mode="determinate",
                                         style="TProgressbar")
        self.progress.pack(side="left", padx=16)

        self.prog_lbl = tk.Label(self.ctrl_inner, text="", bg=COLORS["bg"],
                                  fg=COLORS["text_dim"], font=FONTS["ui_sm"])
        self.prog_lbl.pack(side="left")

        # Log area
        self.log_frame = tk.Frame(main_pane, bg=COLORS["bg"])
        main_pane.add(self.log_frame, minsize=120)

        self.log_hdr = tk.Frame(self.log_frame, bg=COLORS["bg3"], pady=4)
        self.log_hdr.pack(fill="x")
        self.log_hdr_lbl = tk.Label(self.log_hdr, text="📋  Session Log",
                                     bg=COLORS["bg3"], fg=COLORS["text_dim"],
                                     font=FONTS["ui_sm"])
        self.log_hdr_lbl.pack(side="left", padx=10)
        self.log_clear_btn = tk.Button(self.log_hdr, text="Clear",
                                        bg=COLORS["bg3"], fg=COLORS["text_dimmer"],
                                        font=FONTS["ui_sm"], relief="flat",
                                        cursor="hand2", command=self._clear_log)
        self.log_clear_btn.pack(side="right", padx=8)

        self.log_scroll = tk.Scrollbar(self.log_frame, bg=COLORS["bg3"])
        self.log_scroll.pack(side="right", fill="y")
        self.log_text = tk.Text(self.log_frame, bg=COLORS["log_bg"],
                                 fg=COLORS["text_dim"], font=FONTS["mono"],
                                 state="disabled", relief="flat",
                                 yscrollcommand=self.log_scroll.set,
                                 height=8, wrap="word",
                                 selectbackground=COLORS["selection"],
                                 insertbackground=COLORS["accent"])
        self.log_text.pack(fill="both", expand=True)
        self.log_scroll.config(command=self.log_text.yview)

        self.log_text.tag_configure("ok",   foreground=COLORS["accent2"])
        self.log_text.tag_configure("warn", foreground=COLORS["warn"])
        self.log_text.tag_configure("err",  foreground=COLORS["error"])
        self.log_text.tag_configure("info", foreground=COLORS["text_dim"])
        self.log_text.tag_configure("up",   foreground=COLORS["accent"])
        self.log_text.tag_configure("down", foreground=COLORS["accent2"])

        self._refresh_bookmark_list()
        self.log(f"[INFO] {APP_NAME} v{VERSION} started — theme: {self._current_theme}")

    # ── Theme dialog ──────────────────────────────────────────────────────────
    def _open_theme_dialog(self):
        ThemeDialog(self, self._current_theme, on_apply=self.apply_theme)

    # ── Bookmarks ─────────────────────────────────────────────────────────────
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
            self.bookmark_combo.current(len(self.bookmark_manager.bookmarks)-1)
            self.log(f"[INFO] Bookmark added: {dlg.result.name}")

    def _edit_bookmark(self):
        idx = self.bookmark_combo.current()
        if idx < 0: messagebox.showinfo("Edit","Select a bookmark first."); return
        dlg = BookmarkDialog(self, bookmark=self.bookmark_manager.bookmarks[idx])
        if dlg.result:
            self.bookmark_manager.update(idx, dlg.result)
            self._refresh_bookmark_list(); self.bookmark_combo.current(idx)
            self.log(f"[INFO] Bookmark updated: {dlg.result.name}")

    def _delete_bookmark(self):
        idx = self.bookmark_combo.current()
        if idx < 0: messagebox.showinfo("Delete","Select a bookmark first."); return
        name = self.bookmark_manager.bookmarks[idx].name
        if messagebox.askyesno("Delete Bookmark", f"Delete '{name}'?"):
            self.bookmark_manager.remove(idx)
            self._refresh_bookmark_list()
            self.log(f"[INFO] Bookmark deleted: {name}")

    def _get_selected_bookmark(self):
        idx = self.bookmark_combo.current()
        if idx < 0 or idx >= len(self.bookmark_manager.bookmarks): return None
        return self.bookmark_manager.bookmarks[idx]

    # ── Connection ────────────────────────────────────────────────────────────
    def _connect(self):
        b = self._get_selected_bookmark()
        if not b: messagebox.showinfo("Connect","Select a bookmark first."); return
        if self.conn and self.conn.connected: self._disconnect()
        self.connect_btn.config(state="disabled")
        self._set_status("Connecting…", COLORS["warn"])
        threading.Thread(target=self._connect_thread, args=(b,), daemon=True).start()

    def _connect_thread(self, b):
        try:
            conn = SSHConnection(b, self.log); conn.connect()
            self.conn = conn; self.after(0, self._on_connected)
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
        if self.conn: self.conn.disconnect(); self.conn = None
        self.remote_pane.set_connection(None)
        self._set_status("Disconnected", COLORS["text_dimmer"])
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        self.upload_btn.config(state="disabled")
        self.download_btn.config(state="disabled")

    def _set_status(self, text, color):
        self.status_lbl_w.config(text=text, fg=color)
        self.status_dot.config(fg=color)

    # ── Transfers ─────────────────────────────────────────────────────────────
    def _upload(self):
        if not self.conn or not self.conn.connected:
            messagebox.showinfo("Upload","Not connected."); return
        files = [f for f in self.local_pane.get_selected_entries() if not f["is_dir"]]
        if not files: messagebox.showinfo("Upload","Select files in the local pane."); return
        threading.Thread(target=self._xfer_thread, args=(files,"upload"), daemon=True).start()

    def _download(self):
        if not self.conn or not self.conn.connected:
            messagebox.showinfo("Download","Not connected."); return
        files = [f for f in self.remote_pane.get_selected_entries() if not f["is_dir"]]
        if not files: messagebox.showinfo("Download","Select files in the remote pane."); return
        threading.Thread(target=self._xfer_thread, args=(files,"download"), daemon=True).start()

    def _xfer_thread(self, files, direction):
        self.transfer_in_progress = True
        self.after(0, lambda: self.upload_btn.config(state="disabled"))
        self.after(0, lambda: self.download_btn.config(state="disabled"))
        for entry in files:
            try:
                name = entry["name"]
                if direction == "upload":
                    lp = os.path.join(self.local_pane.current_path, name)
                    rp = self.remote_pane.current_path.rstrip("/")+"/"+name
                    def prog(pct,lbl=name): self.after(0,lambda:self._upd_prog(pct,f"Uploading {lbl}"))
                    self.conn.upload(lp, rp, prog)
                else:
                    rp = self.remote_pane.current_path.rstrip("/")+"/"+name
                    lp = os.path.join(self.local_pane.current_path, name)
                    def prog(pct,lbl=name): self.after(0,lambda:self._upd_prog(pct,f"Downloading {lbl}"))
                    self.conn.download(rp, lp, prog)
                self.after(0, lambda: self._upd_prog(100,"Done"))
            except Exception as e:
                self.log(f"[ERR]  Transfer failed for {entry['name']}: {e}","err")
        self.after(0, self._on_xfer_done)

    def _upd_prog(self, pct, label=""):
        self.progress_var.set(pct)
        self.prog_lbl.config(text=f"{label} {pct}%")

    def _on_xfer_done(self):
        self.transfer_in_progress = False
        self.local_pane.refresh(); self.remote_pane.refresh()
        self.upload_btn.config(state="normal"); self.download_btn.config(state="normal")
        self.after(2000, lambda: self._upd_prog(0,""))
        self.log("[OK]   All transfers complete.")

    # ── Log ───────────────────────────────────────────────────────────────────
    def log(self, message: str, tag: str = "info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        if tag == "info":
            m = message.lower()
            if "[ok]"   in m: tag = "ok"
            elif "[err]"  in m: tag = "err"
            elif "[warn]" in m: tag = "warn"
            elif "[up]"   in m: tag = "up"
            elif "[down]" in m: tag = "down"
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{ts}] {message}\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0","end")
        self.log_text.config(state="disabled")

    # ── Misc ──────────────────────────────────────────────────────────────────
    def _check_paramiko(self):
        if not PARAMIKO_AVAILABLE:
            self.log("[WARN] paramiko not found — install it: pip install paramiko","warn")

    def _show_about(self):
        messagebox.showinfo("About ScpGUI",
                            f"{APP_NAME} v{VERSION}\n\n"
                            "A WinSCP-like file transfer client\n"
                            "supporting SFTP and SCP protocols.\n\n"
                            f"Current theme: {self._current_theme}\n\n"
                            "Built with Python + Tkinter + Paramiko")


if __name__ == "__main__":
    app = ScpGuiApp()
    app.mainloop()
