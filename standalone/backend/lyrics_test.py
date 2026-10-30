import re
from pathlib import Path

LRC_FILE = Path(__file__).resolve().parent.parent / "lyrics" / "test.lrc"

TIMESTAMP = re.compile(r"\[(\d{2}):(\d{2})(?:\.(\d{1,3}))?\]")


def parse_lrc(path):
    lyrics = []

    for line in path.read_text(encoding="utf-8-sig").splitlines():
        timestamps = TIMESTAMP.findall(line)
        text = TIMESTAMP.sub("", line).strip()

        if not timestamps or not text:
            continue

        for minute, second, fraction in timestamps:
            fraction = (fraction or "0").ljust(3, "0")
            timestamp = int(minute) * 60 + int(second) + int(fraction) / 1000
            lyrics.append((timestamp, text))

    return sorted(lyrics, key=lambda item: item[0])


def active_lyric(lyrics, position):
    current = None

    for timestamp, text in lyrics:
        if timestamp > position:
            break
        current = text

    return current


def main():
    lyrics = parse_lrc(LRC_FILE)

    if not lyrics:
        print("Tidak ada lirik bertimestamp yang ditemukan.")
        return

    print("=== Lyric Widget: LRC Parser Test ===")
    print(f"File: {LRC_FILE}")
    print(f"Jumlah baris: {len(lyrics)}\n")

    for position in (0, 2.9, 3, 5.9, 6, 9, 12):
        print(f"{position:>5.2f}s -> {active_lyric(lyrics, position)}")


if __name__ == "__main__":
    main()
