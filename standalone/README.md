# Lyric Widget (Standalone Desktop Overlay)

Standalone audio-synced desktop lyrics overlay built with **Python (PySide6 / Qt Quick)** and MPRIS for Linux (KDE, GNOME, XFCE, Sway, Hyprland, etc.).

---

## ✨ Features

- **Frameless Desktop HUD Overlay**: Transparent, click-through, and stays below/above normal windows.
- **D-Bus MPRIS 2.0 Integration**: Automatically detects running players and tracks realtime position.
- **LRCLIB Cloud Lyrics**: Fetches timestamped LRC lyrics with offline caching and title normalization.
- **Full Japanese Romaji Engine**: Powered by `pykakasi` for accurate Kanji and Kana transliteration.
- **Lead & Backing Vocal Splitting**: Accurately formats and colors main lyrics and parentheses backing vocals.
- **Settings Dialog**: Realtime customizer for background gradient, opacity, and typography (`python3 main_ui.py --settings`).
- **Mock Testing Modes**: CLI flags to test different track states (`--mock`, `--mock-japanese`, `--mock-backing`, `--mock-transition`).

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+
- PySide6
- dbus-next
- pykakasi
- jaconv

### 2. Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Overlay
```bash
python3 main_ui.py
```

### 4. Open Settings Dialog
```bash
python3 main_ui.py --settings
```

### 5. Mock Demo Modes
```bash
python3 main_ui.py --mock-transition
python3 main_ui.py --mock-japanese
```

---

## ⚙️ Running at Startup (Optional)

You can launch this application automatically when your desktop starts:

### Method A: Desktop Autostart (`~/.config/autostart/`)
Create a file `~/.config/autostart/lyric-widget.desktop`:
```ini
[Desktop Entry]
Type=Application
Name=Lyric Widget
Exec=/path/to/project/.venv/bin/python /path/to/project/main_ui.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

### Method B: Systemd User Service
Create `~/.config/systemd/user/lyric-widget.service`:
```ini
[Unit]
Description=Lyric Widget Standalone Overlay
After=graphical-session.target

[Service]
ExecStart=/path/to/project/.venv/bin/python /path/to/project/main_ui.py
Restart=on-failure

[Install]
WantedBy=graphical-session.target
```
Enable and start the service:
```bash
systemctl --user daemon-reload
systemctl --user enable --now lyric-widget.service
```

---

## 📜 License

GPL-3.0 License.
