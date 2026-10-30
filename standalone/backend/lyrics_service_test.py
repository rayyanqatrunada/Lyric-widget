import asyncio
import json
import sys
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError
from email.message import Message

from lyrics_service import (
    find_lyrics,
    get_lyrics,
    _fetch_lyrics,
    get_title_variants,
    get_artist_variants,
    score_candidate,
    fetch_metadata_aliases,
    is_valid_alias,
    _alias_cache,
    fetch_lyrics_ovh,
    clean_fallback_lyrics_text,
    _fallback_lyrics_cache,
)


class TestLyricsServiceOffline(unittest.TestCase):
    """Pengujian unit lokal tanpa koneksi internet (menggunakan mock)."""

    def setUp(self):
        _alias_cache.clear()
        _fallback_lyrics_cache.clear()

    # 1. Original exact lookup succeeds without extra requests
    @patch("lyrics_service._fetch_lyrics")
    def test_exact_lookup_succeeds_without_extra_requests(self, mock_fetch):
        mock_fetch.return_value = {
            "trackName": "Proust",
            "artistName": "Sayuri",
            "syncedLyrics": "[00:01.00] test",
            "plainLyrics": "test",
        }

        result = get_lyrics("Proust", "Sayuri", album="Mikazuki no Koukai", duration=250)

        self.assertIsNotNone(result)
        self.assertEqual(result["trackName"], "Proust")
        mock_fetch.assert_called_once()
        self.assertEqual(mock_fetch.call_args[0][1], "get")

    # 2. A title with (Acoustic ver.) can fall back to a normalized title
    @patch("lyrics_service._fetch_lyrics")
    def test_title_acoustic_ver_fallback_to_normalized(self, mock_fetch):
        def side_effect(params, endpoint):
            if endpoint == "get":
                return None
            q = params.get("q", "")
            if "Kamisama Sayuri" in q:
                return [
                    {
                        "trackName": "Kamisama",
                        "artistName": "Sayuri",
                        "syncedLyrics": "[00:01.00] Kami",
                        "plainLyrics": "Kami",
                        "duration": 280,
                    }
                ]
            return []

        mock_fetch.side_effect = side_effect

        result = get_lyrics("Kamisama (Acoustic ver.)", "Sayuri")
        self.assertIsNotNone(result)
        self.assertEqual(result["trackName"], "Kamisama")

    # 3. A title with (feat. ...) can fall back safely
    @patch("lyrics_service._fetch_lyrics")
    def test_title_feat_fallback_safely(self, mock_fetch):
        def side_effect(params, endpoint):
            if endpoint == "get":
                return None
            q = params.get("q", "")
            if "As above Pretty Patterns" in q:
                return [
                    {
                        "trackName": "As Above",
                        "artistName": "Pretty Patterns ft. vally.exe",
                        "syncedLyrics": "[00:01.00] As Above",
                        "plainLyrics": "As Above",
                        "duration": 210,
                    }
                ]
            return []

        mock_fetch.side_effect = side_effect

        result = get_lyrics("As above (feat. vally.exe)", "Pretty Patterns")
        self.assertIsNotNone(result)
        self.assertEqual(result["trackName"], "As Above")

    # 4. Candidate ranking prefers correct artist/title rather than simply the first result
    @patch("lyrics_service._fetch_lyrics")
    def test_candidate_ranking_prefers_correct_artist_and_title(self, mock_fetch):
        def side_effect(params, endpoint):
            if endpoint == "get":
                return None
            return [
                {
                    "trackName": "Different Song",
                    "artistName": "Other Singer",
                    "syncedLyrics": "[00:01.00] Other",
                    "plainLyrics": "Other",
                },
                {
                    "trackName": "Birthday Song",
                    "artistName": "Sayuri",
                    "syncedLyrics": "[00:01.00] Birthday",
                    "plainLyrics": "Birthday",
                },
            ]

        mock_fetch.side_effect = side_effect

        result = get_lyrics("Birthday Song", "Sayuri")
        self.assertIsNotNone(result)
        self.assertEqual(result["trackName"], "Birthday Song")
        self.assertEqual(result["artistName"], "Sayuri")

    # 5. A wrong artist or clearly unrelated title is rejected
    @patch("lyrics_service.fetch_metadata_aliases", return_value=[])
    @patch("lyrics_service._fetch_lyrics")
    def test_wrong_artist_or_unrelated_title_rejected(self, mock_fetch, mock_alias):
        mock_fetch.side_effect = [
            None,
            [
                {
                    "trackName": "Completely Unrelated Song",
                    "artistName": "Wrong Artist XYZ",
                    "syncedLyrics": "[00:01.00] Unrelated",
                    "plainLyrics": "Unrelated",
                }
            ],
            [],
            [],
        ]

        result = get_lyrics("Birthday Song", "Sayuri")
        self.assertIsNone(result)

    # 6. Synced lyrics are preferred only among sufficiently matching candidates
    @patch("lyrics_service.fetch_metadata_aliases", return_value=[])
    @patch("lyrics_service._fetch_lyrics")
    def test_synced_preferred_only_among_matching_candidates(self, mock_fetch, mock_alias):
        def side_effect(params, endpoint):
            if endpoint == "get":
                return None
            return [
                {
                    "trackName": "Birthday Song",
                    "artistName": "Sayuri",
                    "syncedLyrics": None,
                    "plainLyrics": "Bait lirik asli",
                },
                {
                    "trackName": "Totally Different Track",
                    "artistName": "Random Band",
                    "syncedLyrics": "[00:01.00] Synced but wrong song",
                    "plainLyrics": "Wrong",
                },
            ]

        mock_fetch.side_effect = side_effect

        result = get_lyrics("Birthday Song", "Sayuri")
        self.assertIsNotNone(result)
        self.assertEqual(result["trackName"], "Birthday Song")
        self.assertIsNone(result["syncedLyrics"])
        self.assertEqual(result["plainLyrics"], "Bait lirik asli")

    # 7. Plain-only lyrics remain supported
    @patch("lyrics_service.fetch_metadata_aliases", return_value=[])
    @patch("lyrics_service._fetch_lyrics")
    def test_plain_only_lyrics_supported(self, mock_fetch, mock_alias):
        def side_effect(params, endpoint):
            if endpoint == "get":
                return None
            return [
                {
                    "trackName": "Kamisama (Acoustic ver.)",
                    "artistName": "Sayuri",
                    "syncedLyrics": None,
                    "plainLyrics": "Hanya lirik biasa tanpa timestamp",
                    "duration": 280,
                }
            ]

        mock_fetch.side_effect = side_effect

        result = get_lyrics("Kamisama (Acoustic ver.)", "Sayuri")
        self.assertIsNotNone(result)
        self.assertIsNone(result["syncedLyrics"])
        self.assertEqual(result["plainLyrics"], "Hanya lirik biasa tanpa timestamp")

    # 8. Empty title/artist return safely
    def test_empty_title_or_artist(self):
        self.assertIsNone(get_lyrics("", "Sayuri"))
        self.assertIsNone(get_lyrics("Birthday Song", ""))
        self.assertIsNone(get_lyrics("   ", "   "))
        self.assertIsNone(get_lyrics(None, "Sayuri"))
        self.assertIsNone(get_lyrics("Song", None))

    # 9. HTTP 400/404/503, timeout, malformed JSON, and network errors do not crash
    @patch("lyrics_service.urlopen")
    def test_http_errors_and_malformed_json_do_not_crash(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError("url", 400, "Bad Request", Message(), MagicMock(read=lambda: b'{"message": "err"}'))
        self.assertIsNone(_fetch_lyrics({"track_name": "T", "artist_name": "A"}, "get"))

        mock_urlopen.side_effect = HTTPError("url", 404, "Not Found", Message(), None)
        self.assertIsNone(_fetch_lyrics({"track_name": "T", "artist_name": "A"}, "get"))

        mock_urlopen.side_effect = HTTPError("url", 503, "Service Unavailable", Message(), None)
        self.assertIsNone(_fetch_lyrics({"track_name": "T", "artist_name": "A"}, "get"))

        mock_urlopen.side_effect = URLError("Network unreachable")
        self.assertIsNone(_fetch_lyrics({"q": "query"}, "search"))

        resp_mock = MagicMock()
        resp_mock.read.return_value = b"{ invalid json"
        mock_urlopen.side_effect = None
        mock_urlopen.return_value.__enter__.return_value = resp_mock
        self.assertIsNone(_fetch_lyrics({"q": "query"}, "search"))

    # 10. HTTP 429 does not trigger an uncontrolled retry loop and respects Retry-After
    @patch("lyrics_service.time.sleep")
    @patch("lyrics_service.urlopen")
    def test_http_429_bounded_retry_and_retry_after(self, mock_urlopen, mock_sleep):
        headers = Message()
        headers["Retry-After"] = "3"
        mock_urlopen.side_effect = HTTPError("url", 429, "Too Many Requests", headers, None)

        res = _fetch_lyrics({"track_name": "T", "artist_name": "A"}, "get")
        self.assertIsNone(res)
        self.assertEqual(mock_urlopen.call_count, 3)
        mock_sleep.assert_called_with(3)

    # 11. Repeated queries are deduplicated and the total request count remains bounded
    @patch("lyrics_service.fetch_metadata_aliases", return_value=[])
    @patch("lyrics_service._fetch_lyrics")
    def test_repeated_queries_deduplicated_and_bounded(self, mock_fetch, mock_alias):
        mock_fetch.return_value = None

        get_lyrics("Summer Bug", "Sayuri")

        self.assertLessEqual(mock_fetch.call_count, 5)
        search_calls = [c for c in mock_fetch.call_args_list if c[0][1] == "search"]
        self.assertLessEqual(len(search_calls), 4)

        queries_sent = [c[0][0]["q"] for c in search_calls]
        self.assertEqual(len(queries_sent), len(set(queries_sent)))

    # 12. Existing tests for duration validation and album omission still pass
    @patch("lyrics_service._fetch_lyrics")
    def test_duration_validation_and_album_omission(self, mock_fetch):
        mock_fetch.return_value = {"syncedLyrics": "...", "plainLyrics": "..."}

        get_lyrics("Song", "Artist", duration=0)
        self.assertNotIn("duration", mock_fetch.call_args[0][0])

        get_lyrics("Song", "Artist", duration=-5)
        self.assertNotIn("duration", mock_fetch.call_args[0][0])

        get_lyrics("Song", "Artist", duration=5000)
        self.assertNotIn("duration", mock_fetch.call_args[0][0])

        get_lyrics("Song", "Artist", duration=212.4)
        self.assertEqual(mock_fetch.call_args[0][0]["duration"], 212)

        get_lyrics("Song", "Artist", album="")
        self.assertNotIn("album_name", mock_fetch.call_args[0][0])

        get_lyrics("Song", "Artist", album="Album A")
        self.assertEqual(mock_fetch.call_args[0][0]["album_name"], "Album A")

    # === Stage 9.6: Japanese Track Title Alias Tests ===

    # 13. A Japanese-script alias is discovered and used for LRCLIB fallback
    @patch("lyrics_service.fetch_metadata_aliases")
    @patch("lyrics_service._fetch_lyrics")
    def test_japanese_script_alias_discovered_and_used_for_lrclib_fallback(
        self, mock_fetch, mock_alias
    ):
        mock_alias.return_value = [("花の塔", "さユり")]

        def side_effect(params, endpoint):
            # Normal search gagal
            if "Hana no Tou" in str(params):
                return None
            # Pencarian dengan alias kanji berhasil
            if "花の塔" in str(params):
                return {
                    "trackName": "花の塔",
                    "artistName": "さユり",
                    "syncedLyrics": "[00:01.00] Hana no Tou Kanji",
                    "plainLyrics": "Hana no Tou Kanji",
                }
            return None

        mock_fetch.side_effect = side_effect

        result = get_lyrics("Hana no Tou", "Sayuri")
        self.assertIsNotNone(result)
        self.assertEqual(result["trackName"], "花の塔")
        self.assertTrue(bool(result["syncedLyrics"]))
        mock_alias.assert_called_once()

    # 14. Metadata results from an unrelated artist are rejected
    @patch("lyrics_service.urlopen")
    def test_metadata_results_unrelated_artist_rejected(self, mock_urlopen):
        # Metadata provider mengembalikan artis yang sama sekali salah
        fake_itunes_resp = MagicMock()
        fake_itunes_resp.read.return_value = json.dumps({
            "results": [
                {
                    "trackName": "さくら(独唱)",
                    "artistName": "森山直太朗",
                    "trackTimeMillis": 256000,
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = fake_itunes_resp

        aliases = fetch_metadata_aliases("Hana no Tou", "Sayuri", duration=276)
        self.assertEqual(aliases, [])

    # 15. Ambiguous metadata results do not produce an unsafe alias
    def test_ambiguous_metadata_results_do_not_produce_unsafe_alias(self):
        # Judul tidak cocok fonetiknya
        self.assertFalse(is_valid_alias("Hana no Tou", "Sayuri", "ミカヅキ", "さユり", 276, 262))
        # Artis salah total
        self.assertFalse(is_valid_alias("Hana no Tou", "Sayuri", "花の塔", "Coldplay", 276, 276))
        # Durasi meleset jauh (> 12 detik)
        self.assertFalse(is_valid_alias("Hana no Tou", "Sayuri", "花の塔", "さユり", 276, 150))
        # Kecocokan valid
        self.assertTrue(is_valid_alias("Hana no Tou", "Sayuri", "花の塔", "さユり", 276, 276))

    # 16. An unavailable metadata API falls back gracefully to normal search
    @patch("lyrics_service.urlopen")
    @patch("lyrics_service._fetch_lyrics", return_value=None)
    def test_unavailable_metadata_api_falls_back_gracefully(self, mock_fetch, mock_urlopen):
        mock_urlopen.side_effect = URLError("DNS lookup failed")

        result = get_lyrics("Hana no Tou", "Sayuri")
        self.assertIsNone(result)

    # 17. HTTP errors, timeouts, and malformed metadata responses do not crash
    @patch("lyrics_service.urlopen")
    def test_metadata_api_errors_do_not_crash(self, mock_urlopen):
        # HTTP 500
        mock_urlopen.side_effect = HTTPError("url", 500, "Server Error", Message(), None)
        self.assertEqual(fetch_metadata_aliases("Title", "Artist"), [])

        # TimeoutError
        mock_urlopen.side_effect = TimeoutError()
        self.assertEqual(fetch_metadata_aliases("Title", "Artist"), [])

        # Malformed JSON
        bad_json = MagicMock()
        bad_json.read.return_value = b"{ bad: json"
        mock_urlopen.side_effect = None
        mock_urlopen.return_value.__enter__.return_value = bad_json
        self.assertEqual(fetch_metadata_aliases("Title", "Artist"), [])

    # 18. Alias requests remain bounded and are cached in-memory
    @patch("lyrics_service.urlopen")
    def test_alias_requests_bounded_and_cached(self, mock_urlopen):
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({
            "results": [
                {
                    "trackName": "花の塔",
                    "artistName": "さユり",
                    "trackTimeMillis": 276000,
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = fake_resp

        # Panggilan 1 -> Jaringan
        aliases1 = fetch_metadata_aliases("Hana no Tou", "Sayuri")
        self.assertEqual(aliases1, [("花の塔", "さユり")])
        self.assertEqual(mock_urlopen.call_count, 1)

        # Panggilan 2 -> Dari cache, tidak memanggil jaringan lagi
        aliases2 = fetch_metadata_aliases("Hana no Tou", "Sayuri")
        self.assertEqual(aliases2, [("花の塔", "さユり")])
        self.assertEqual(mock_urlopen.call_count, 1)

    # 19. LRCLIB succeeds -> fallback is not called
    @patch("lyrics_service.fetch_lyrics_ovh")
    @patch("lyrics_service._fetch_lyrics")
    def test_lrclib_success_does_not_call_fallback(self, mock_fetch, mock_fallback):
        mock_fetch.return_value = {
            "trackName": "Proust",
            "artistName": "Sayuri",
            "syncedLyrics": "[00:01.00] test",
            "plainLyrics": "test",
        }

        result = get_lyrics("Proust", "Sayuri", album="Mikazuki no Koukai", duration=250)

        self.assertIsNotNone(result)
        self.assertEqual(result["trackName"], "Proust")
        mock_fallback.assert_not_called()

    # 20. LRCLIB fails and fallback provider finds synced lyrics
    @patch("lyrics_service.urlopen")
    @patch("lyrics_service.fetch_metadata_aliases", return_value=[])
    @patch("lyrics_service._fetch_lyrics", return_value=None)
    def test_lrclib_fails_fallback_finds_synced_lyrics(self, mock_fetch, mock_alias, mock_urlopen):
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({
            "lyrics": "[00:01.00] Line one\n[00:05.00] Line two"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = fake_resp

        result = get_lyrics("Song Synced", "Artist Test")

        self.assertIsNotNone(result)
        self.assertEqual(result["syncedLyrics"], "[00:01.00] Line one\n[00:05.00] Line two")
        self.assertEqual(result["plainLyrics"], "Line one\nLine two")
        self.assertEqual(result["source"], "lyrics.ovh")

    # 21. Alternative source provides plain lyrics only (syncedLyrics is None)
    @patch("lyrics_service.urlopen")
    @patch("lyrics_service.fetch_metadata_aliases", return_value=[])
    @patch("lyrics_service._fetch_lyrics", return_value=None)
    def test_fallback_plain_lyrics_only(self, mock_fetch, mock_alias, mock_urlopen):
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({
            "lyrics": "Hello, it's me\nI was wondering if after all these years"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = fake_resp

        result = get_lyrics("Hello", "Adele")

        self.assertIsNotNone(result)
        self.assertIsNone(result["syncedLyrics"])
        self.assertEqual(result["plainLyrics"], "Hello, it's me\nI was wondering if after all these years")
        self.assertEqual(result["source"], "lyrics.ovh")
        self.assertEqual(result["trackName"], "Hello")
        self.assertEqual(result["artistName"], "Adele")

    # 22. Unmatched, empty, or whitespace title/artist rejected without network calls
    @patch("lyrics_service.urlopen")
    def test_empty_or_unmatched_candidate_rejected(self, mock_urlopen):
        self.assertIsNone(fetch_lyrics_ovh("", "Adele"))
        self.assertIsNone(fetch_lyrics_ovh("Hello", ""))
        self.assertIsNone(fetch_lyrics_ovh("   ", "   "))
        self.assertIsNone(fetch_lyrics_ovh("???", "!!!"))
        mock_urlopen.assert_not_called()

    # 23. Alternative API timeout, HTTP error, empty response, and malformed JSON do not crash
    @patch("lyrics_service.urlopen")
    def test_fallback_api_errors_and_malformed_json_do_not_crash(self, mock_urlopen):
        # HTTP 404
        mock_urlopen.side_effect = HTTPError("url", 404, "Not Found", Message(), None)
        self.assertIsNone(fetch_lyrics_ovh("Nonexistent", "Nobody"))

        # HTTP 500
        mock_urlopen.side_effect = HTTPError("url", 500, "Server Error", Message(), None)
        self.assertIsNone(fetch_lyrics_ovh("ServerErrorSong", "Nobody"))

        # TimeoutError
        mock_urlopen.side_effect = TimeoutError()
        self.assertIsNone(fetch_lyrics_ovh("TimeoutSong", "Nobody"))

        # Malformed JSON
        bad_json = MagicMock()
        bad_json.read.return_value = b"{ invalid json"
        mock_urlopen.side_effect = None
        mock_urlopen.return_value.__enter__.return_value = bad_json
        self.assertIsNone(fetch_lyrics_ovh("BadJsonSong", "Nobody"))

        # Empty lyrics response
        empty_resp = MagicMock()
        empty_resp.read.return_value = json.dumps({"lyrics": ""}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = empty_resp
        self.assertIsNone(fetch_lyrics_ovh("EmptySong", "Nobody"))

    # 24. Cache and bounded requests; fallback failure does not break subsequent queries
    @patch("lyrics_service.urlopen")
    def test_fallback_requests_cached_and_does_not_break_subsequent(self, mock_urlopen):
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({
            "lyrics": "Look at the stars, look how they shine for you"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = fake_resp

        # Panggilan 1 -> Jaringan
        res1 = fetch_lyrics_ovh("Yellow", "Coldplay")
        self.assertIsNotNone(res1)
        self.assertEqual(mock_urlopen.call_count, 1)

        # Panggilan 2 -> Dari cache
        res2 = fetch_lyrics_ovh("Yellow", "Coldplay")
        self.assertIsNotNone(res2)
        self.assertEqual(mock_urlopen.call_count, 1)

        # Kegagalan lagu lain tidak merusak cache atau query berikutnya
        mock_urlopen.side_effect = HTTPError("url", 404, "Not Found", Message(), None)
        res_fail = fetch_lyrics_ovh("Unknown Song", "Unknown Artist")
        self.assertIsNone(res_fail)

        # Lagu pertama tetap utuh di cache
        res_cached = fetch_lyrics_ovh("Yellow", "Coldplay")
        self.assertIsNotNone(res_cached)
        self.assertEqual(res_cached["plainLyrics"], "Look at the stars, look how they shine for you")


class TestLyricsServiceOnline(unittest.TestCase):
    """Pengujian aktual terhadap live LRCLIB API & metadata provider (opsional via --online)."""

    def test_online_proust_sayuri(self):
        result = get_lyrics("Proust", "Sayuri")
        self.assertIsNotNone(result)
        self.assertTrue(bool(result.get("syncedLyrics")))

    def test_online_as_above_feat(self):
        result = get_lyrics("As above (feat. vally.exe)", "Pretty Patterns")
        self.assertIsNotNone(result)
        self.assertTrue(bool(result.get("syncedLyrics")))

    def test_online_kamisama_acoustic(self):
        result = get_lyrics("Kamisama (Acoustic ver.)", "Sayuri", album="Sekai no Himitsu")
        self.assertIsNotNone(result)
        self.assertTrue(bool(result.get("plainLyrics")))

    def test_online_hana_no_tou_alias_resolution(self):
        result = get_lyrics("Hana no Tou", "Sayuri", album="Hana no Tou", duration=276)
        self.assertIsNotNone(result)
        self.assertEqual(result.get("trackName"), "花の塔")
        self.assertTrue(bool(result.get("syncedLyrics")))


if __name__ == "__main__":
    if "--online" in sys.argv:
        sys.argv.remove("--online")
        print("Menjalankan SEMUA tes (Offline + Online LRCLIB & Metadata API)...")
        unittest.main()
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLyricsServiceOffline)
        runner = unittest.TextTestRunner(verbosity=2)
        print("Menjalankan 24 pengujian offline (tanpa internet)...")
        res = runner.run(suite)
        if not res.wasSuccessful():
            sys.exit(1)
