#!/usr/bin/env python3
"""
Entry point untuk Lyric Widget Desktop Overlay (KDE Plasma 6).
Menghubungkan backend MPRIS/lirik dengan antarmuka Qt Quick / QML.
"""

import sys
import signal
from pathlib import Path

# Tambahkan direktori backend ke sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QGuiApplication, QSurfaceFormat
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from ui_bridge import LyricBridge


def main():
    # 1. Konfigurasi buffer alpha 8-bit agar window mendukung transparansi murni
    surface_format = QSurfaceFormat()
    surface_format.setAlphaBufferSize(8)
    QSurfaceFormat.setDefaultFormat(surface_format)

    # 2. Inisialisasi QGuiApplication
    app = QGuiApplication(sys.argv)
    app.setApplicationName("lyric-widget")
    app.setOrganizationName("LyricWidget")

    # 3. Buat bridge QObject untuk backend
    bridge = LyricBridge()

    # 4. Inisialisasi QML engine dan daftarkan bridge
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)

    qml_file = BASE_DIR / "ui" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        print(f"[ERROR] Gagal memuat file QML dari: {qml_file}", file=sys.stderr)
        return 1

    # Buka dialog pengaturan jika diminta via argumen CLI --settings
    settings_window = None
    if "--settings" in sys.argv or "-s" in sys.argv:
        settings_file = BASE_DIR / "ui" / "SettingsDialog.qml"
        engine.load(QUrl.fromLocalFile(str(settings_file)))
        if len(engine.rootObjects()) > 1:
            settings_window = engine.rootObjects()[-1]
            if isinstance(settings_window, QQuickWindow):
                settings_window.show()

    # 5. Tangani sinyal Ctrl+C / SIGINT agar keluar dengan bersih
    signal.signal(signal.SIGINT, lambda *args: app.quit())
    signal.signal(signal.SIGTERM, lambda *args: app.quit())

    # Timer periodik agar Python dapat memproses sinyal OS di event loop Qt
    sig_timer = QTimer()
    sig_timer.timeout.connect(lambda: None)
    sig_timer.start(250)

    # 6. Mode khusus untuk pengujian argumen CLI (misal mock testing)
    mock_timer = None
    if "--mock" in sys.argv:
        bridge.setMock(
            has_player=True,
            status="Playing",
            title="Alive",
            artist="Krewella",
            lead="I'm gonna keep it frozen here forever",
            position=18.0,
            duration=204.0,  # 0.18 / 3.24
        )
    elif "--mock-japanese" in sys.argv:
        bridge.setMock(
            has_player=True,
            status="Playing",
            title="Hana no Tou",
            artist="Sayuri",
            lead="君に会いたい",
            romaji="Kimi ni aitai",
            position=102.0,
            duration=245.0,  # 1.42 / 4.05
        )
    elif "--mock-backing" in sys.argv:
        bridge.setMock(
            has_player=True,
            status="Playing",
            title="As above (feat. vally.exe)",
            artist="Pretty Patterns",
            lead="With no tomorrow",
            backing="If hope's a lie",
            position=127.0,
            duration=188.0,  # 2.07 / 3.08
        )
    elif "--mock-transition" in sys.argv:
        # Siklus transisi lirik otomatis setiap 2.5 detik untuk memverifikasi crossfade halus
        lines = [
            ("I'm gonna keep it frozen here forever", "", "", 18.0),
            ("Let's make this last for life", "", "", 24.0),
            ("And make it all feel right", "", "", 30.0),
            ("君に会いたい", "", "Kimi ni aitai", 36.0),
            ("With no tomorrow", "If hope's a lie", "", 42.0),
        ]
        line_idx = 0

        def cycle_line():
            nonlocal line_idx
            lead, backing, romaji, pos = lines[line_idx]
            bridge.setMock(
                has_player=True,
                status="Playing",
                title="Alive",
                artist="Krewella",
                lead=lead,
                backing=backing,
                romaji=romaji,
                position=pos,
                duration=204.0,
            )
            line_idx = (line_idx + 1) % len(lines)

        cycle_line()
        mock_timer = QTimer()
        mock_timer.timeout.connect(cycle_line)
        mock_timer.start(2500)
    else:
        # Tampilkan informasi startup ke terminal agar pengguna tahu widget aktif
        print("==================================================")
        print("  Lyric Widget Desktop Overlay (KDE Plasma 6)")
        print("==================================================")
        print("[INFO] Widget aktif dan memantau pemutar musik...")
        print("[INFO] Jalankan musik di Strawberry, Spotify, dsb.")
        print("[INFO] Widget overlay akan otomatis muncul saat lagu diputar.")
        print("[INFO] Konfigurasi tema & font: jalankan dengan --settings")
        print("[INFO] Tekan Ctrl+C di terminal ini untuk berhenti.")
        print("--------------------------------------------------")

        def on_player_changed(has_p):
            if has_p and bridge.title:
                print(f"[PLAYING] {bridge.title} — {bridge.artist}")
            elif not has_p:
                print("[IDLE] Tidak ada pemutar musik aktif. Widget overlay tersembunyi.")

        bridge.hasPlayerChanged.connect(on_player_changed)
        bridge.titleChanged.connect(lambda t: print(f"[TRACK] {bridge.title} — {bridge.artist}") if t else None)

        # Jalankan worker MPRIS background normal
        bridge.start()

    # 7. Jalankan Qt event loop
    try:
        ret = app.exec()
    finally:
        bridge.stop()

    return ret


if __name__ == "__main__":
    sys.exit(main())
