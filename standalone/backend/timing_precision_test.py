"""
Pengujian deterministik sinkronisasi timestamp dan presisi timing lirik (Stage 10.4).
Memverifikasi:
1. Batas timestamp LRC: baris aktif berganti tepat pada saat position >= timestamp.
2. Perubahan baris lirik di LyricBridge terjadi secara instan (logis) tanpa menunggu animasi selesai.
3. Seek / lompatan waktu cepat: baris langsung sinkron dengan posisi baru.
4. Perilaku pause/resume: posisi dan lirik konsisten.
5. Format waktu playback: M.SS / M.SS dengan presisi tepat.
"""

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from lyric_core import parse_lrc_text, active_lyric_entry, active_lyric
from ui_bridge import LyricBridge


class TestTimingPrecision(unittest.TestCase):

    def setUp(self):
        self.sample_lrc = """
[00:00.00]Intro instrumental
[00:05.50]First line of vocals
[00:08.20]Second line starts here
[00:12.00]Third line (with backing)
[00:15.80](Backing only line)
[00:20.00]Final outro line
"""
        self.parsed = parse_lrc_text(self.sample_lrc)

    def test_exact_timestamp_boundary_resolution(self):
        """Memastikan baris aktif berganti tepat pada timestamp sumber, bukan sebelum atau sesudahnya."""
        # Sebelum 05.50 -> Intro instrumental
        self.assertEqual(active_lyric(self.parsed, 5.49), "Intro instrumental")
        self.assertEqual(active_lyric(self.parsed, 5.499), "Intro instrumental")

        # Tepat pada 05.50 -> First line of vocals
        self.assertEqual(active_lyric(self.parsed, 5.50), "First line of vocals")
        self.assertEqual(active_lyric(self.parsed, 5.501), "First line of vocals")

        # Mendekati 08.20 -> Masih First line
        self.assertEqual(active_lyric(self.parsed, 8.19), "First line of vocals")

        # Tepat pada 08.20 -> Second line starts here
        self.assertEqual(active_lyric(self.parsed, 8.20), "Second line starts here")

        # Tepat pada 12.00 -> Third line
        self.assertEqual(active_lyric(self.parsed, 11.999), "Second line starts here")
        self.assertEqual(active_lyric(self.parsed, 12.00), "Third line (with backing)")

    def test_immediate_bridge_property_update(self):
        """Memverifikasi properti bridge berubah secara instan saat update masuk tanpa delay animasi."""
        bridge = LyricBridge()
        emitted = []
        bridge.activeLyricChanged.connect(lambda: emitted.append(True))

        # Update baris 1
        bridge.setMock(
            True, "Playing", "Test Song", "Test Artist",
            lead="First line", backing="", romaji="", position=5.5, duration=120.0
        )
        self.assertEqual(bridge.activeLead, "First line")
        self.assertEqual(len(emitted), 1)

        # Update baris 2 tepat saat timestamp tiba
        bridge.setMock(
            True, "Playing", "Test Song", "Test Artist",
            lead="Second line", backing="", romaji="", position=8.2, duration=120.0
        )
        # Nilai properti harus langsung berganti di level logis
        self.assertEqual(bridge.activeLead, "Second line")
        self.assertEqual(len(emitted), 2)

    def test_rapid_seek_handling(self):
        """Memverifikasi jika playback di-seek jauh, bridge langsung sinkron tanpa macet."""
        bridge = LyricBridge()
        bridge.setMock(
            True, "Playing", "Song", "Artist",
            lead="Intro", backing="", romaji="", position=2.0, duration=180.0
        )
        self.assertEqual(bridge.activeLead, "Intro")
        self.assertEqual(bridge.formattedTime, "0.02 / 3.00")

        # Seek ke detik 75.0 (1m 15s)
        bridge.setMock(
            True, "Playing", "Song", "Artist",
            lead="Chorus Line", backing="", romaji="", position=75.0, duration=180.0
        )
        self.assertEqual(bridge.activeLead, "Chorus Line")
        self.assertEqual(bridge.formattedTime, "1.15 / 3.00")

        # Seek mundur ke detik 10.0
        bridge.setMock(
            True, "Playing", "Song", "Artist",
            lead="Verse 1", backing="", romaji="", position=10.0, duration=180.0
        )
        self.assertEqual(bridge.activeLead, "Verse 1")
        self.assertEqual(bridge.formattedTime, "0.10 / 3.00")

    def test_pause_resume_stability(self):
        """Memverifikasi bahwa saat paused posisi dan lirik tetap bertahan."""
        bridge = LyricBridge()
        bridge.setMock(
            True, "Playing", "Song", "Artist",
            lead="Active Vocals", backing="", romaji="", position=45.0, duration=180.0
        )
        self.assertEqual(bridge.activeLead, "Active Vocals")
        self.assertEqual(bridge.playbackStatus, "Playing")
        self.assertEqual(bridge.formattedTime, "0.45 / 3.00")

        # Jeda musik (Paused)
        bridge.setMock(
            True, "Paused", "Song", "Artist",
            lead="Active Vocals", backing="", romaji="", position=45.0, duration=180.0
        )
        self.assertEqual(bridge.activeLead, "Active Vocals")
        self.assertEqual(bridge.playbackStatus, "Paused")
        self.assertEqual(bridge.formattedTime, "0.45 / 3.00")

        # Lanjutkan musik (Resumed)
        bridge.setMock(
            True, "Playing", "Song", "Artist",
            lead="Active Vocals", backing="", romaji="", position=46.0, duration=180.0
        )
        self.assertEqual(bridge.playbackStatus, "Playing")
        self.assertEqual(bridge.formattedTime, "0.46 / 3.00")

    def test_formatted_time_specification(self):
        """Memverifikasi format M.SS / M.SS sesuai spesifikasi Stage 10.4."""
        self.assertEqual(LyricBridge._format_min_sec(0.0), "0.00")
        self.assertEqual(LyricBridge._format_min_sec(5.0), "0.05")
        self.assertEqual(LyricBridge._format_min_sec(59.0), "0.59")
        self.assertEqual(LyricBridge._format_min_sec(60.0), "1.00")
        self.assertEqual(LyricBridge._format_min_sec(137.0), "2.17")
        self.assertEqual(LyricBridge._format_min_sec(210.0), "3.30")

        bridge = LyricBridge()
        bridge.setMock(
            True, "Playing", "Song", "Artist",
            lead="Text", backing="", romaji="", position=137.0, duration=210.0
        )
        self.assertEqual(bridge.formattedTime, "2.17 / 3.30")

    def test_immediate_replacement_without_lingering(self):
        """Memverifikasi bahwa saat baris baru tiba di bridge, teks lama langsung terhapus (tidak lingering)."""
        bridge = LyricBridge()
        # Baris 1: Vokal utama bahasa Jepang dengan Romaji
        bridge.setMock(
            True, "Playing", "Song", "Artist",
            lead="君に会いたい", backing="", romaji="Kimi ni aitai", position=10.0, duration=180.0
        )
        self.assertEqual(bridge.activeLead, "君に会いたい")
        self.assertEqual(bridge.activeRomaji, "Kimi ni aitai")
        self.assertTrue(bridge.hasRomaji)
        self.assertFalse(bridge.hasBacking)

        # Baris 2: Segera berganti ke backing-only bahasa Inggris
        bridge.setMock(
            True, "Playing", "Song", "Artist",
            lead="", backing="Let me try", romaji="", position=14.0, duration=180.0
        )
        # Teks lead dan romaji sebelumnya harus langsung kosong/bersih
        self.assertEqual(bridge.activeLead, "")
        self.assertEqual(bridge.activeBacking, "Let me try")
        self.assertEqual(bridge.activeRomaji, "")
        self.assertFalse(bridge.hasRomaji)
        self.assertTrue(bridge.hasBacking)
        self.assertTrue(bridge.isBackingOnly)

        # Baris 3: Segera berganti ke lead + backing
        bridge.setMock(
            True, "Playing", "Song", "Artist",
            lead="With no tomorrow", backing="If hope's a lie", romaji="", position=18.0, duration=180.0
        )
        self.assertEqual(bridge.activeLead, "With no tomorrow")
        self.assertEqual(bridge.activeBacking, "If hope's a lie")
        self.assertTrue(bridge.hasBacking)
        self.assertFalse(bridge.isBackingOnly)


if __name__ == "__main__":
    unittest.main()
