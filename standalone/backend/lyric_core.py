
import re
import pykakasi
from pathlib import Path

converter = pykakasi.kakasi()

TIMESTAMP = re.compile(r"\[(\d{2}):(\d{2})(?:\.(\d{1,3}))?\]")
METADATA_TAG = re.compile(r"^\[[a-zA-Z]{1,10}:")
JAPANESE_KANA = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]")
PAREN_BACKING_PATTERN = re.compile(r"[\(\uff08]+([^\(\)\uff08\uff09]+)[\)\uff09]+")

# Koreksi frasa yang sudah diverifikasi pada tahap sebelumnya.
KNOWN_PHRASES = {
    "君に会いたい": "Kimi ni aitai",
    "あなたの声に耳を澄ます": "Anata no koe ni mimi o sumasu",
    "音もない水槽の中": "Oto mo nai suisō no naka",
    "聴いてみたいな": "Kiite mitai na",
}


def split_vocals(text: str) -> dict:
    """Memisahkan lead vocals dan backing vocals (dalam tanda kurung).

    Mengenali:
    - Lead diikuti backing: "With no tomorrow (If hope's a lie)"
    - Backing-only: "(Let me try)"
    - Plain lead tanpa backing: "As above so below"
    - Mengabaikan tanda kurung kosong seperti "()" atau "(   )".
    """
    if not text:
        return {
            "lead": None,
            "backing": None,
            "has_backing": False,
            "is_backing_only": False,
        }

    raw = text.strip()
    if not re.sub(r"[\(\uff08\s\)\uff09]", "", raw):
        return {
            "lead": None,
            "backing": None,
            "has_backing": False,
            "is_backing_only": False,
        }

    matches = list(PAREN_BACKING_PATTERN.finditer(raw))
    if not matches:
        return {
            "lead": raw,
            "backing": None,
            "has_backing": False,
            "is_backing_only": False,
        }

    backing_parts = [m.group(1).strip() for m in matches if m.group(1).strip()]
    backing_text = " ".join(backing_parts) if backing_parts else None

    lead_text = PAREN_BACKING_PATTERN.sub("", raw)
    lead_text = re.sub(r"\s+", " ", lead_text).strip()
    if not lead_text:
        lead_text = None

    has_backing = backing_text is not None
    is_backing_only = has_backing and (lead_text is None)

    return {
        "lead": lead_text,
        "backing": backing_text,
        "has_backing": has_backing,
        "is_backing_only": is_backing_only,
    }


def parse_lrc_text(content: str) -> list[tuple[float, str]]:
    """Mengubah teks LRC menjadi daftar (timestamp, lirik)."""
    lyrics = []

    for line in content.lstrip("\ufeff").splitlines():
        timestamps = TIMESTAMP.findall(line)
        text = TIMESTAMP.sub("", line).strip()

        if not timestamps or not text:
            continue

        # Hindari membaca tag metadata non-lirik sebagai baris lirik
        if METADATA_TAG.match(text):
            continue

        for minute, second, fraction in timestamps:
            fraction = (fraction or "0").ljust(3, "0")
            timestamp = (
                int(minute) * 60
                + int(second)
                + int(fraction) / 1000
            )
            lyrics.append((timestamp, text))

    return sorted(lyrics, key=lambda item: item[0])


def parse_lrc_entries(content: str) -> list[dict]:
    """Mengubah teks LRC menjadi daftar entri terstruktur dengan timestamp dan pemisahan vokal."""
    raw_lines = parse_lrc_text(content)
    entries = []
    for timestamp, text in raw_lines:
        entries.append(prepare_lyric(text, timestamp=timestamp))
    return entries


def parse_lrc_file(path: str | Path) -> list[tuple[float, str]]:
    path = Path(path)
    return parse_lrc_text(path.read_text(encoding="utf-8-sig"))


def active_lyric_entry(
    lyrics: list[tuple[float, str]],
    position: float,
) -> tuple[float, str] | None:
    """Mengembalikan tuple (timestamp, lirik) yang aktif pada posisi lagu tertentu."""
    current = None

    for item in lyrics:
        ts = item[0] if isinstance(item, (tuple, list)) else item.get("timestamp", 0.0)
        if ts > position:
            break
        current = item

    return current


def active_lyric(
    lyrics: list[tuple[float, str]],
    position: float,
) -> str | None:
    """Mengembalikan lirik yang aktif pada posisi lagu tertentu."""
    entry = active_lyric_entry(lyrics, position)
    if entry is None:
        return None
    if isinstance(entry, (tuple, list)):
        return entry[1]
    if isinstance(entry, dict):
        return entry.get("original")
    return str(entry)


def contains_japanese(text: str) -> bool:
    # Kana menjadi penanda kuat bahasa Jepang.
    return bool(JAPANESE_KANA.search(text))


def convert_to_romaji(text: str) -> str:
    if text in KNOWN_PHRASES:
        return KNOWN_PHRASES[text]

    result = converter.convert(text)
    parts = []

    for item in result:
        original = item["orig"]
        romaji = item["hepburn"]

        if original in {"は", "を"}:
            romaji = {"は": "wa", "を": "o"}[original]

        romaji = (
            romaji.replace("ou", "ō")
                  .replace("uu", "ū")
        )
        parts.append(romaji)

    output = re.sub(r"\s+", " ", " ".join(parts)).strip()
    return output[:1].upper() + output[1:] if output else output


def prepare_lyric(text: str, timestamp: float | None = None) -> dict:
    """Siapkan lirik asli, pemisahan vokal lead/backing, dan romaji opsional untuk UI."""
    text = (text or "").strip()

    if not text:
        return {
            "original": "",
            "lead": None,
            "backing": None,
            "has_backing": False,
            "is_backing_only": False,
            "shared_timestamp": False,
            "timestamp": timestamp,
            "romaji": None,
            "lead_romaji": None,
            "backing_romaji": None,
        }

    vocals = split_vocals(text)
    lead_text = vocals["lead"]
    backing_text = vocals["backing"]
    has_backing = vocals["has_backing"]
    is_backing_only = vocals["is_backing_only"]
    shared_timestamp = has_backing and (lead_text is not None)

    # Romaji opsional untuk bahasa Jepang
    lead_romaji = None
    if lead_text and contains_japanese(lead_text):
        lead_romaji = convert_to_romaji(lead_text)

    backing_romaji = None
    if backing_text and contains_japanese(backing_text):
        backing_romaji = convert_to_romaji(backing_text)

    # Romaji utama untuk kompatibilitas balik
    if is_backing_only:
        main_romaji = backing_romaji or (convert_to_romaji(text) if contains_japanese(text) else None)
    elif lead_romaji:
        main_romaji = lead_romaji
    elif contains_japanese(text):
        main_romaji = convert_to_romaji(text)
    else:
        main_romaji = None

    return {
        "original": text,
        "lead": lead_text,
        "backing": backing_text,
        "has_backing": has_backing,
        "is_backing_only": is_backing_only,
        "shared_timestamp": shared_timestamp,
        "timestamp": timestamp,
        "romaji": main_romaji,
        "lead_romaji": lead_romaji,
        "backing_romaji": backing_romaji,
    }
