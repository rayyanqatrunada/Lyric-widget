"""
Modul konfigurasi dan persistensi pengaturan widget (Background & Fonts).
Menyediakan nilai default, pemuatan dari file JSON, dan penyimpanan otomatis.
"""

import json
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".config" / "lyric-widget"
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULT_SETTINGS: Dict[str, Any] = {
    # 1. Pengaturan Background
    "bgWidthPercent": 82,            # Lebar background (20% - 100% layar)
    "bgColor": "#0a0d12",            # Warna dasar background hex
    "bgOpacity": 0.88,               # Tingkat opacity puncak (0.10 - 1.00)
    "bgFadeStart": 0.25,             # Titik awal pemudaran gradasi ke kanan (0.05 - 0.70)

    # 2. Pengaturan Font Komponen Teks
    "useUnifiedFont": False,         # Opsi 'Select All' / satu font untuk semua teks
    "unifiedFontFamily": "Noto Sans",# Font master jika useUnifiedFont aktif

    "titleFontFamily": "Noto Sans",  # Font judul lagu
    "artistFontFamily": "Noto Sans", # Font nama artis
    "lyricFontFamily": "Noto Sans",  # Font lirik utama & backing
    "romajiFontFamily": "Noto Sans", # Font teks romaji
    "timerFontFamily": "Noto Sans",  # Font indikator waktu playback
}


def load_settings() -> Dict[str, Any]:
    """Memuat pengaturan dari ~/.config/lyric-widget/settings.json dengan fallback default."""
    settings = dict(DEFAULT_SETTINGS)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    settings.update(data)
        except Exception as e:
            print(f"[WARN] Gagal membaca {CONFIG_FILE}, menggunakan default: {e}")
    return settings


def save_settings(settings: Dict[str, Any]) -> bool:
    """Menyimpan pengaturan ke ~/.config/lyric-widget/settings.json."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Merge dengan default agar semua key valid
        current = dict(DEFAULT_SETTINGS)
        current.update(settings)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=4)
        return True
    except Exception as e:
        print(f"[ERROR] Gagal menyimpan pengaturan ke {CONFIG_FILE}: {e}")
        return False
