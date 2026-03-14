# ⚡ ScpGUI

A **WinSCP-like** file transfer client for **SFTP** and **SCP** protocols, built with Python, Tkinter, and Paramiko.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

- 🔐 **SFTP & SCP** protocol support
- 🔖 **Bookmarks** — save and manage remote connections (stored in `~/.scpgui/bookmarks.json`)
- 📂 **Dual-pane** file browser — Local on the left, Remote on the right
- ⬆⬇ **Multi-file transfer** — select multiple files, click Upload or Download
- 📊 **Progress bar** per-file transfer with percentage
- 📋 **Session log** — color-coded activity log at the bottom
- 🗝️ **SSH key auth** — supports PEM/OpenSSH private keys + password auth
- 🌑 **Dark terminal aesthetic** UI

---

## 🚀 Quick Start

### Run from source

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/scpgui.git
cd scpgui

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch the app
python main.py
```

### Use a pre-built binary

Download the latest release for your platform from the [Releases page](../../releases).

| Platform | File |
|----------|------|
| Windows x64 | `ScpGUI-Windows-x64.exe` |
| macOS Intel | `ScpGUI-macOS-Intel.zip` |
| macOS Apple Silicon | `ScpGUI-macOS-AppleSilicon.zip` |
| Linux x64 | `ScpGUI-Linux-x64.tar.gz` |
| Linux ARM64 | `ScpGUI-Linux-arm64.tar.gz` |

> **macOS note:** Right-click → Open on first launch to bypass Gatekeeper for unsigned apps.  
> **Linux note:** `chmod +x ScpGUI && ./ScpGUI`

---

## 📖 Usage

1. **Add a bookmark** — Click `⊕ New` in the toolbar, fill in host/user/password or key path
2. **Connect** — Select the bookmark from the dropdown, click `▶ Connect`
3. **Navigate** — Double-click folders to enter them; use `↑` to go up; type a path and press Enter
4. **Transfer files**
   - Select files in the **local pane** → click `⬆ Upload`
   - Select files in the **remote pane** → click `← Download`
5. **Monitor** — Watch the session log and progress bar at the bottom

---

## 🏗️ Build from source (PyInstaller)

```bash
pip install pyinstaller
pyinstaller ScpGUI.spec --clean --noconfirm
# Output: dist/ScpGUI  (or dist/ScpGUI.app on macOS)
```

---

## 🔄 CI/CD — GitHub Actions

The included workflow (`.github/workflows/build.yml`) automatically builds on every push:

| Job | Runner | Output |
|-----|--------|--------|
| Windows | `windows-latest` | `.exe` |
| macOS Intel | `macos-13` | `.zip` (`.app` bundle) |
| macOS Apple Silicon | `macos-14` | `.zip` (`.app` bundle) |
| Linux x64 | `ubuntu-22.04` | `.tar.gz` |
| Linux ARM64 | QEMU + Docker | `.tar.gz` |

A **GitHub Release** is created automatically when you push a tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 📁 Project Structure

```
scpgui/
├── main.py              # Main application (single-file)
├── requirements.txt     # Python dependencies
├── ScpGUI.spec          # PyInstaller build spec
├── README.md
└── .github/
    └── workflows/
        └── build.yml    # Cross-platform CI build
```

---

## 🛠️ Dependencies

| Package | Purpose |
|---------|---------|
| `paramiko` | SSH/SFTP protocol implementation |
| `cryptography` | Key handling (pulled in by paramiko) |
| `tkinter` | GUI (bundled with Python on most platforms) |

---

## 🐛 Troubleshooting

**`paramiko` not found**  
```bash
pip install paramiko
```

**tkinter not available on Linux**  
```bash
# Debian/Ubuntu
sudo apt-get install python3-tk
# Fedora
sudo dnf install python3-tkinter
# Arch
sudo pacman -S tk
```

**macOS "App can't be opened"**  
Right-click the app → Open → Open anyway.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
