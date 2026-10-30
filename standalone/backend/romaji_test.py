
import pykakasi

converter = pykakasi.kakasi()

samples = [
    "僕はエラ呼吸のサカナ",
    "音もない水槽の中",
    "あなたの声に耳を澄ます",
    "聴こえない聴いてみたいな",
]

def convert_to_romaji(text: str) -> str:
    result = converter.convert(text)
    parts = []

    for item in result:
        original = item["orig"]
        romaji = item["hepburn"]

        # Pisahkan partikel yang menempel pada kata sebelumnya.
        particles = ["は", "の", "に", "を", "が", "で", "と", "も"]

        for particle in particles:
            if original.endswith(particle) and len(original) > len(particle):
                base = original[:-len(particle)]
                converted_base = converter.convert(base)

                if converted_base:
                    base_romaji = "".join(
                        part["hepburn"] for part in converted_base
                    )
                    particle_romaji = {
                        "は": "wa",
                        "を": "o",
                    }.get(particle, converter.convert(particle)[0]["hepburn"])

                    romaji = f"{base_romaji} {particle_romaji}"
                break

        # Perbaiki vokal panjang untuk tampilan Hepburn.
        romaji = (
            romaji.replace("ou", "ō")
                  .replace("uu", "ū")
        )

        parts.append(romaji)

    output = " ".join(parts)
    return output[:1].upper() + output[1:] if output else output


print("=== Japanese Romaji Test ===")

for text in samples:
    print(text)
    print(f"  {convert_to_romaji(text)}\n")
