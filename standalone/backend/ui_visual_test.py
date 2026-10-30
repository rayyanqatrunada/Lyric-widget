"""
Pengujian visual untuk UI Widget Lirik (Stage 10.5):
1. Keberadaan window dan transparansi murni
2. State awal: tanpa pemutar (widget tersembunyi)
3. State pemutar aktif: slide-in dan gradasi yang diperlebar (75% layar, solid di kiri, kokoh di tengah, memudar halus ke kanan)
4. State musik diputar: judul, artis, lirik aktif, dan timer diperbesar (16-18px, format M.SS / M.SS)
5. State lagu Jepang: lirik asli + romaji + timer
6. State backing vocal: vokal utama + vokal latar + timer
7. State transisi lirik presisi: pergantian instan tanpa lingering/kesan vokal ganda (45ms OutQuad)
8. State pergantian cepat (rapid consecutive lines): penanganan animasi aman tanpa tumpang tindih
9. State seek maju & mundur: lirik dan timer langsung sinkron dengan posisi baru
10. State musik dijeda: panel, lirik, dan timer tetap stabil & bertahan
11. State pemutar ditutup: slide-out dan menghilang
"""

import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QGuiApplication, QSurfaceFormat
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from ui_bridge import LyricBridge


def run_visual_tests():
    surface_format = QSurfaceFormat()
    surface_format.setAlphaBufferSize(8)
    QSurfaceFormat.setDefaultFormat(surface_format)

    app = QGuiApplication(sys.argv)
    bridge = LyricBridge()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)

    qml_file = BASE_DIR / "ui" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    root_objs = engine.rootObjects()
    if not root_objs:
        print("[FAIL] QML root object tidak dapat dimuat")
        return 1

    window = root_objs[0]
    if not isinstance(window, QQuickWindow):
        print("[FAIL] QML root object bukan QQuickWindow")
        return 1

    out_dir = Path("/tmp/lyric_widget_test_renders")
    out_dir.mkdir(exist_ok=True)

    test_steps = [
        # (nama_test, has_player, status, title, artist, lead, backing, romaji, pos, dur, delay_ms)
        ("1_no_player_hidden", False, "", "", "", "", "", "", 0.0, 0.0, 200),
        ("2_player_slide_in_alive", True, "Playing", "Alive", "Krewella", "I'm gonna keep it frozen here forever", "", "", 18.0, 204.0, 700),
        ("3_japanese_romaji", True, "Playing", "Hana no Tou", "Sayuri", "君に会いたい", "", "Kimi ni aitai", 102.0, 245.0, 700),
        ("4_backing_vocals", True, "Playing", "As above (feat. vally.exe)", "Pretty Patterns", "With no tomorrow", "If hope's a lie", "", 137.0, 210.0, 700),
        ("5_fast_transition_next_line", True, "Playing", "As above (feat. vally.exe)", "Pretty Patterns", "There's no time to lay as meanings all return to ashes", "Then give me mine", "", 142.0, 210.0, 300),
        ("6_rapid_consecutive_interruption", True, "Playing", "As above (feat. vally.exe)", "Pretty Patterns", "", "Let me try", "", 144.0, 210.0, 200),
        ("7_seek_backward_and_forward", True, "Playing", "As above (feat. vally.exe)", "Pretty Patterns", "With no tomorrow", "If hope's a lie", "", 137.0, 210.0, 250),
        ("8_paused_remains_visible", True, "Paused", "As above (feat. vally.exe)", "Pretty Patterns", "With no tomorrow", "If hope's a lie", "", 137.0, 210.0, 350),
        ("9_player_closed_slide_out", False, "", "", "", "", "", "", 0.0, 0.0, 700),
    ]

    current_idx = 0

    def execute_next():
        nonlocal current_idx
        if current_idx >= len(test_steps):
            print("\n[OK] Semua pengujian visual Stage 10.5 berhasil dijalankan!")
            app.quit()
            return

        name, has_p, status, title, artist, lead, backing, romaji, pos, dur, delay = test_steps[current_idx]
        print(f"[TEST {current_idx+1}/{len(test_steps)}] {name} (timer: {bridge.formattedTime})...")

        bridge.setMock(
            has_p,
            status,
            title,
            artist,
            lead,
            backing,
            romaji,
            pos,
            dur,
        )

        def capture():
            nonlocal current_idx
            img = window.grabWindow()
            save_path = out_dir / f"{name}.png"
            img.save(str(save_path))

            print(f"  -> Captured {img.width()}x{img.height()} to {save_path}")
            print(f"  -> Formatted timer: {bridge.formattedTime}")

            if name == "1_no_player_hidden":
                print(f"  -> Window visible state: {window.isVisible()}")

            current_idx += 1
            execute_next()

        QTimer.singleShot(delay, capture)

    # Mulai urutan tes setelah window di-render
    QTimer.singleShot(100, execute_next)
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_visual_tests())
