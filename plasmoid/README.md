# Lyric Widget (KDE Plasma 6 Plasmoid)

Audio-synced desktop lyrics overlay widget for **KDE Plasma 6** with native MPRIS support, LRCLIB cloud integration, Japanese Romaji transliteration, vocal separation, and customizable aesthetic glow.

---

## ✨ Features

- **Pure KDE Plasma 6 Applet**: Runs natively inside `plasmashell` without any external Python daemon or dependencies.
- **Native MPRIS 2.0 Integration**: Automatically syncs playback status, track metadata, and position from Strawberry, Spotify, VLC, Firefox, Chromium, etc.
- **Synced Lyrics (LRCLIB)**: Automatically fetches word-accurate timestamped synced lyrics.
- **Vocal Separation**: Automatically detects and styles Lead Vocals vs Backing Vocals (parentheses).
- **Japanese Kana to Romaji**: Transliterates Hiragana & Katakana directly into readable Romaji pronunciation.
- **Non-Clipping Background Bleed**: Background can expand top and bottom outside the widget outline (allowing other desktop widgets to sit on top of the black gradient).
- **Customizable Appearance & Typography**:
  - Horizontal Gradient background width, opacity (0-100%), and fade distance (0-100%).
  - Peak gradient position slider (0% left to 100% right).
  - Top & Bottom expansion sliders (0px - 800px) to eliminate screen gaps.
  - Granular font configuration (individual fonts and sizes for Title, Artist, Lyrics, Romaji, and Timer, or a single master font).

---

## 🚀 Installation & Usage

### 1. Test in Sandbox (Without Installing)
To test the widget in a standalone test container window:
```bash
plasmoidviewer -a .
```

### 2. Install to KDE Plasma Desktop
Install the widget applet into your local Plasma packages directory (`~/.local/share/plasma/plasmoids/`):
```bash
kpackagetool6 -t Plasma/Applet -i lyric-widget.plasmoid
```

### 3. Update / Reload after Code Changes
```bash
kpackagetool6 -t Plasma/Applet -u lyric-widget.plasmoid
systemctl --user restart plasma-plasmashell
```

### 4. Uninstall
```bash
kpackagetool6 -t Plasma/Applet -r com.github.rayy.lyricwidget
```

---

## 🖥️ Adding to Desktop / Panel

1. Right-click on your KDE Plasma Desktop or Panel.
2. Select **Add Widgets...**.
3. Search for **"Lyric Widget"**.
4. Drag and drop it anywhere onto your desktop or panel.
5. Play music on any MPRIS-supported media player (e.g. Strawberry, Spotify, browser). The widget will dynamically appear and sync lyrics!

---

## ⚙️ Configuration

Right-click the widget on your desktop and choose **Configure Lyric Widget...** to access:
- **1. Components**:
  - Visibility toggles for Track Title, Artist Name, Lyrics, Japanese Romaji, and Playback Timer.
  - Words per Line (3 – 25 words).
  - Line Spacing (1.00x - 2.20x) and Item Spacing (2px - 32px).
  - Timer Bottom Margin (0px - 150px).
- **2. Background**:
  - Background Color, Opacity (0% - 100%), Fade Distance (0% - 100%).
  - Peak Position slider (0% Left to 100% Right).
  - Alignment (Left, Center, Right) and Width (20% - 100%).
  - **Top Expansion (0px - 800px)**: Extends background upwards beyond the widget outline.
  - **Bottom Expansion (0px - 800px)**: Extends background downwards beyond the widget outline to close any screen edge gap.
- **3. Typography**:
  - Granular font family selection or unified master font.
  - Pixel size sliders for Track Title, Artist Name, Lyrics, Romaji, and Timer.
