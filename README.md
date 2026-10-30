# 🎵 Lyric Widget

A sleek, lightweight desktop lyrics overlay for Linux featuring a **3-Tier Multi-Source Lyrics Engine**, realtime **Japanese Romaji transliteration**, **Lead & Backing Vocal separation**, and customizable aesthetic gradient styling.

![Lyric Widget Preview](assets/preview.png)

---

## 🛠️ Tech Stack & System Specifications

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Operating System** | **Linux** (KDE Plasma 6 on Wayland / X11) | Tested on Fedora Linux, compatible with any KDE 6 distribution |
| **Frontend / UI** | **QML, QtQuick, Qt 6, KDE Kirigami** | Native, hardware-accelerated, lightweight UI |
| **Audio Protocol** | **MPRIS 2.0 (D-Bus)** | Supports Spotify, Strawberry, VLC, Chromium/Firefox (YouTube Music), etc. |
| **Lyrics Engine** | **Multi-Source REST APIs** (LRCLIB, NetEase, KuGou) | 3-tier automatic fallback; 100% free, requires no API key |
| **Transliteration** | **Hepburn Kana-to-Romaji Engine** | Realtime client-side conversion of Hiragana and Katakana |
| **Standalone Mode** | **Python 3.10+, PySide6 (Qt 6 for Python)** | Frameless desktop overlay for non-KDE environments |

---

## 📦 Installation Guide

### 1. KDE Plasma 6 Widget (Plasmoid)

> **Recommended**: Runs natively inside the KDE Plasma Shell with zero Python dependencies, minimal memory footprint, and automatic startup.

👉 **[📥 Download `lyric-widget.plasmoid`](https://github.com/rayyanqatrunada/Lyric-widget/raw/main/lyric-widget.plasmoid)**

#### Method A: Via Plasma Desktop GUI
1. Download **[`lyric-widget.plasmoid`](https://github.com/rayyanqatrunada/Lyric-widget/raw/main/lyric-widget.plasmoid)**.
2. Right-click any empty area on your Desktop > select **Add Widgets...**.
3. Click **Get New Widgets...** at the bottom > choose **Install from Local File...**.
4. Select the downloaded `lyric-widget.plasmoid` file.
5. Drag and drop **Lyric Widget** onto your desktop.

#### Method B: Via Terminal (CLI)
```bash
# Install widget
kpackagetool6 -t Plasma/Applet -i lyric-widget.plasmoid

# Update existing installation
kpackagetool6 -t Plasma/Applet -u lyric-widget.plasmoid

# Restart Plasma Shell to apply changes
systemctl --user restart plasma-plasmashell
```

---

### 2. Standalone Mode (Independent Desktop Overlay)

> 💡 **Note & Architecture**:  
> The Standalone version is an independent Python application running in a transparent, click-through frameless overlay window. Designed for Linux users running **desktop environments other than KDE Plasma** (e.g., GNOME, XFCE, Hyprland, Sway, i3) or for testing without installing the widget into Plasma Shell.

```bash
# Navigate to standalone directory
cd standalone

# Install Python dependencies
pip install -r requirements.txt

# Launch overlay
python main_ui.py
```

*Quick Test / Mock Simulation:*
```bash
python main_ui.py --mock-transition   # Preview automatic lyric transitions
python main_ui.py --mock-japanese     # Preview Japanese Kana & Romaji styling
```

---

## ⚙️ Key Features & How It Works

- **Precision Realtime Sync (35ms Loop)**  
  Queries playback position via D-Bus MPRIS 2.0 every 35ms, matching LRC timestamps with smooth vertical sliding and opacity fade animations.

- **3-Tier Multi-Source Lyrics Engine**  
  Automated sequential fallback pipeline:  
  1. **LRCLIB**: Exact duration match & query search.  
  2. **NetEase Cloud Music**: Database of over 40 million tracks (exceptional coverage for Western, J-Pop/Anime, K-Pop, and global indie releases).  
  3. **KuGou Music**: High-accuracy timestamped LRC fallback.  
  *If one provider is down or returns HTTP 503, the next provider resolves the request in milliseconds.*

- **Smart Media Title Sanitizer**  
  Automatically strips video noise labels common on browser players (e.g., `(Official Music Video)`, `[MV]`, `(Lyric Video)`, `(Audio)`) and intelligently splits `Artist - Title` formats for flawless API matching.

- **Browser Player Compatibility & 30s Grace Period**  
  Solves the browser track transition flicker on web players like YouTube Music. The widget stays visible during song changes, remains persistent on pause, and gracefully waits 30 seconds after playback stops before fading out.

- **Lead & Backing Vocal Splitting**  
  Detects backing vocals enclosed in parentheses `(...)` and styles them in clean, secondary italic typography without redundant text prefixes.

- **Realtime Japanese Romaji Transliteration**  
  Converts Japanese Kana (Hiragana & Katakana) into clean Hepburn Romaji below the main lyric line in realtime.

- **Aesthetic Gradient & Outline Bleed**  
  Customizable gradient backdrop with adjustable peak position (left, center, right), 0–100% opacity, and vertical bleed margins that expand beyond the widget boundary.

- **Vertical Title Positioning & Typography**  
  Includes a *Title Top Position* slider for fine-tuning layout balance, alongside curated font family selectors and size sliders.

- **Instant Refresh & Context Menu**  
  Hoverable quick-refresh button with a smooth spinning loader animation, complemented by a native desktop right-click **Refresh Lyrics** action.

---

## 📜 License
Distributed under the **GPL-3.0** License. Free to use, modify, and distribute.
