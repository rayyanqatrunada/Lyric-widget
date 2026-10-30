from lyric_core import (
    parse_lrc_text,
    parse_lrc_entries,
    active_lyric,
    active_lyric_entry,
    prepare_lyric,
    split_vocals,
)

sample_lrc = """
[ti:Core Test]
[ar:Lyric Widget]
[00:00.00]僕はエラ呼吸のサカナ
[00:03.00]I want to see you again
[00:06.00]Aku ingin bertemu denganmu lagi
[00:09.00]君に会いたい
"""

# Fixture berbasis contoh lagu "As above (feat. vally.exe)" oleh Pretty Patterns
AS_ABOVE_FIXTURE = """
[ti:As above (feat. vally.exe)]
[ar:Pretty Patterns]
[al:Kernel Hearts (Original Game Soundtrack)]
[02:34.10]With no tomorrow (If hope's a lie)
[02:38.78]There's no time to lay as meanings all return to ashes (Then give me mine)
[02:44.00](Let me try)
[02:44.86]As above so below (Eyes by thousands)
[02:50.37]When your hope gets buried (Make me fly)
[02:55.00]We just had to reach your heart (Make me fly)
[03:00.00]As above so below
[03:05.00](Backing one)
[03:08.00](Backing two)
"""

print("=== Lyric Core Integration Test ===")
lyrics = parse_lrc_text(sample_lrc)
print(f"Jumlah baris: {len(lyrics)}")

print("\n--- Tes timestamp ---")
for position in (0, 2.9, 3, 6, 9, 12):
    print(f"{position:>5.2f}s -> {active_lyric(lyrics, position)}")

print("\n--- Tes tampilan lirik ---")
for _, text in lyrics:
    display = prepare_lyric(text)
    print(f"\nAsli   : {display['original']}")
    print(f"Romaji : {display['romaji'] or 'Tidak ditampilkan'}")

# Verifikasi kompatibilitas dasar Stage terdahulu
assert len(lyrics) == 4
assert active_lyric(lyrics, 0) == "僕はエラ呼吸のサカナ"
assert active_lyric(lyrics, 3) == "I want to see you again"
assert active_lyric(lyrics, 6) == "Aku ingin bertemu denganmu lagi"
assert active_lyric(lyrics, 9) == "君に会いたい"
assert prepare_lyric("I want to see you again")["romaji"] is None

print("\n--- Tes Stage 9.8: Lead dan Backing Vocals ---")

# 1. Lead lyric diikuti backing vocals dalam tanda kurung
p1 = prepare_lyric("With no tomorrow (If hope's a lie)", timestamp=154.10)
assert p1["lead"] == "With no tomorrow", f"Expected 'With no tomorrow', got {p1['lead']}"
assert p1["backing"] == "If hope's a lie", f"Expected 'If hope's a lie', got {p1['backing']}"
assert p1["has_backing"] is True
assert p1["is_backing_only"] is False
assert p1["shared_timestamp"] is True
assert p1["original"] == "With no tomorrow (If hope's a lie)"
print("1. Lead lyric followed by backing vocals: OK")

# 2. Long lead lyric diikuti backing vocals dalam tanda kurung
long_line = "There's no time to lay as meanings all return to ashes (Then give me mine)"
p2 = prepare_lyric(long_line, timestamp=158.78)
assert p2["lead"] == "There's no time to lay as meanings all return to ashes"
assert p2["backing"] == "Then give me mine"
assert p2["has_backing"] is True
assert p2["is_backing_only"] is False
assert p2["shared_timestamp"] is True
print("2. Long lead lyric followed by backing vocals: OK")

# 3. Baris yang hanya memuat backing vocals dalam tanda kurung
p3 = prepare_lyric("(Let me try)", timestamp=164.00)
assert p3["lead"] is None
assert p3["backing"] == "Let me try"
assert p3["has_backing"] is True
assert p3["is_backing_only"] is True
assert p3["shared_timestamp"] is False
print("3. Backing-only line in parentheses: OK")

# 4. Beberapa baris backing vocals berurutan
entries_fixture = parse_lrc_entries(AS_ABOVE_FIXTURE)
backing_lines = [e for e in entries_fixture if e["is_backing_only"]]
assert len(backing_lines) >= 3  # (Let me try), (Backing one), (Backing two)
assert backing_lines[-2]["backing"] == "Backing one"
assert backing_lines[-1]["backing"] == "Backing two"
assert backing_lines[-2]["timestamp"] == 185.0
assert backing_lines[-1]["timestamp"] == 188.0
print("4. Multiple consecutive backing-vocal lines: OK")

# 5. Baris dengan timestamp terpisah harus tetap terpisah (tidak digabung secara artifisial)
separate_lrc = """
[02:34.10]With no tomorrow
[02:34.86]If hope's a lie then give me mine, let me try
"""
sep_parsed = parse_lrc_text(separate_lrc)
assert len(sep_parsed) == 2
assert sep_parsed[0][0] == 154.10
assert sep_parsed[0][1] == "With no tomorrow"
assert sep_parsed[1][0] == 154.86
assert sep_parsed[1][1] == "If hope's a lie then give me mine, let me try"
print("5. Separate timestamped lines remain separate: OK")

# 6. Baris tanpa tanda kurung tetap utuh dan tidak terdistorsi
p6 = prepare_lyric("As above so below")
assert p6["lead"] == "As above so below"
assert p6["backing"] is None
assert p6["has_backing"] is False
assert p6["is_backing_only"] is False
assert p6["original"] == "As above so below"
print("6. Line without parentheses remains unchanged: OK")

# 7. Lirik Jepang dan romaji tetap berfungsi dengan atau tanpa backing
jp_pure = prepare_lyric("君に会いたい")
assert jp_pure["lead"] == "君に会いたい"
assert jp_pure["backing"] is None
assert jp_pure["romaji"] == "Kimi ni aitai"

jp_backing = prepare_lyric("君に会いたい (会いたい)")
assert jp_backing["lead"] == "君に会いたい"
assert jp_backing["backing"] == "会いたい"
assert jp_backing["lead_romaji"] == "Kimi ni aitai"
assert jp_backing["has_backing"] is True

jp_fullwidth = prepare_lyric("君に会いたい（会いたい）")
assert jp_fullwidth["lead"] == "君に会いたい"
assert jp_fullwidth["backing"] == "会いたい"
print("7. Japanese lyrics and romaji functional: OK")

# 8. Baris kosong, malformed, atau kurung tidak lengkap tidak membuat parser crash
malformed_cases = [
    "",
    "   ",
    "()",
    "(   )",
    "Unmatched (parenthesis",
    "Unmatched ) parenthesis",
    "((nested))",
]
for mc in malformed_cases:
    res = prepare_lyric(mc)
    assert isinstance(res, dict)
print("8. Empty/malformed/unusual lines do not crash parser: OK")

# 9. Metadata dalam file LRC tidak dianggap sebagai vokal lirik
assert len(entries_fixture) == 9  # Tepat 9 baris lirik dari fixture As above
for ent in entries_fixture:
    assert not ent["original"].startswith("[")
print("9. Non-lyric metadata in LRC ignored safely: OK")

# 10. Split vocals helper langsung
v1 = split_vocals("As above so below (Eyes by thousands)")
assert v1["lead"] == "As above so below"
assert v1["backing"] == "Eyes by thousands"
assert v1["has_backing"] is True
assert v1["is_backing_only"] is False
print("10. split_vocals unit verification: OK")

# 11. active_lyric_entry unit verification
entry0 = active_lyric_entry(lyrics, 0)
assert entry0 == (0.0, "僕はエラ呼吸のサカナ")
entry3 = active_lyric_entry(lyrics, 3)
assert entry3 == (3.0, "I want to see you again")
print("11. active_lyric_entry unit verification: OK")

print("\nSEMUA TES BERHASIL")
