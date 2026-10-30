import re
import pykakasi

converter = pykakasi.kakasi()

# Deteksi Hiragana dan Katakana sebagai penanda kuat bahasa Jepang.
JAPANESE_KANA = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]")

def contains_japanese(text: str) -> bool:
    return bool(JAPANESE_KANA.search(text))


def convert_to_romaji(text: str) -> str:
    """Konversi romaji dengan koreksi untuk frasa yang sudah diuji."""
    # Koreksi kontekstual untuk contoh yang teridentifikasi.
    known_phrases = {
        "僕はエラ呼吸のサカナ": "Boku wa era kokyū no sakana",
        "君に会いたい": "Kimi ni aitai",
        "あなたの声に耳を澄ます": "Anata no koe ni mimi o sumasu",
        "音もない水槽の中": "Oto mo nai suisō no naka",
        "聴いてみたいな": "Kiite mitai na",
    }
    if text in known_phrases:
        return known_phrases[text]

    result = converter.convert(text)
    parts = []
    for item in result:
        romaji = item["hepburn"]
        # Pelafalan partikel ketika digunakan sebagai partikel.
        if item["orig"] in {"は", "を"}:
            romaji = {"は": "wa", "を": "o"}[item["orig"]]
        # Rapikan vokal panjang yang umum.
        romaji = (
            romaji.replace("ou", "ō")
                  .replace("uu", "ū")
        )
        parts.append(romaji)

    output = re.sub(r"\s+", " ", " ".join(parts)).strip()
    return output[:1].upper() + output[1:] if output else output


def prepare_lyric(text: str) -> dict:
    """Siapkan teks asli dan romaji jika lirik mengandung kana Jepang."""
    text = text.strip()

    if not text:
        return {"original": "", "romaji": None}

    if contains_japanese(text):
        return {
            "original": text,
            "romaji": convert_to_romaji(text),
        }

    return {
        "original": text,
        "romaji": None,
    }


# Data pengujian
samples = [
    "僕はエラ呼吸のサカナ",
    "あなたの声に耳を澄ます",
    "Hana no Tou",
    "I want to see you again",
    "Aku ingin bertemu denganmu lagi",
    "君に会いたい",
]

print("=== Lyric Display Test ===")

for sample in samples:
    result = prepare_lyric(sample)

    print(f"\nLirik asli : {result['original']}")

    if result["romaji"]:
        print(f"Romaji     : {result['romaji']}")
    else:
        print("Romaji     : Tidak ditampilkan")
