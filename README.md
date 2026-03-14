# 🛡️ TypeGuard — Local Text Recovery System

**Never lose your typed text again.**

TypeGuard is a lightweight, always-on background utility for Windows that continuously captures your keystrokes and maintains a rolling buffer of your last **2,000 words**. When a page reloads, an app crashes, or you accidentally close a tab, your text is safe.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| ⌨️ **Keystroke Capture** | Silently records everything you type, system-wide |
| 📋 **Clipboard Tracking** | Also captures text you copy to clipboard |
| 🔄 **FIFO Buffer (2000 words)** | Oldest words are automatically removed; newest are always preserved |
| 💾 **Survives Reboots** | Text is stored in a local SQLite database |
| 🖥️ **System Tray Icon** | Quick access via right-click menu |
| 🌐 **Web Dashboard** | Beautiful local UI at `http://localhost:5757` |
| ⌨️ **Global Hotkeys** | `Ctrl+Shift+R` to instantly recover text |
| ⏸️ **Privacy Pause** | `Ctrl+Shift+P` to pause recording |
| 🚀 **Auto-Start** | Runs automatically when you log in |
| 🔒 **100% Local** | No internet, no cloud — everything stays on your PC |

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd d:\LocalKeylogger
pip install -r requirements.txt
```

### 2. Run TypeGuard
```bash
python -m typeguard.main
```
You'll see a green **T** icon in your system tray. That's it — TypeGuard is now recording.

### 3. Recover Your Text
- **Web Dashboard**: Open [http://localhost:5757](http://localhost:5757) in your browser
- **Quick Copy**: Press `Ctrl+Shift+R` to copy last 100 words to clipboard
- **System Tray**: Right-click the tray icon → Copy Last 50/200/All Words

### 4. Set Up Auto-Start (Run as Administrator)
```bash
python typeguard/install.py
```
TypeGuard will now start automatically every time you log in.

---

## 🎮 Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl+Shift+P` | Pause / Resume recording |
| `Ctrl+Shift+R` | Copy last 100 words to clipboard |

---

## 📂 Where Is My Data?

All data is stored locally at:
```
C:\Users\<YourName>\AppData\Roaming\TypeGuard\
├── typeguard.db    ← SQLite database (your words)
├── typeguard.log   ← Application log
└── typeguard.lock  ← Single-instance lock file
```

---

## 🏗️ Building a Standalone .exe

```bash
build.bat
```

This creates `dist/TypeGuard.exe` — a single executable that doesn't require Python.

---

## 🗑️ Uninstall Auto-Start

```bash
python typeguard/install.py --uninstall
```

---

## ⚡ Performance Impact

TypeGuard is designed to be extremely lightweight:
- **CPU**: < 0.1% usage (only processes key events)
- **RAM**: ~15-25 MB
- **Disk**: Database stays under 1 MB (only 2000 words)
- **Network**: Zero — no internet connection used

---

## 🔒 Privacy

- All data is stored **locally only** on your PC
- No data is ever sent over the network
- Press `Ctrl+Shift+P` to pause recording when entering sensitive information
- The tray icon turns **amber** when paused

---

## License

Personal use only. Built for your own productivity.
