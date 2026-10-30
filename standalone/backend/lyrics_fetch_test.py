import asyncio
import time
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from dbus_next.aio import MessageBus
from dbus_next import BusType, Message

PLAYER = "org.mpris.MediaPlayer2.strawberry"
PATH = "/org/mpris/MediaPlayer2"
PROPERTIES = "org.freedesktop.DBus.Properties"
PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"


def fetch_lyrics(params, endpoint):
    url = f"https://lrclib.net/api/{endpoint}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": "LyricWidget/0.1 (Fedora KDE Plasma)",
        },
    )

    for attempt in range(3):
        try:
            with urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))

        except HTTPError as error:
            if error.code == 404:
                return None

            if error.code not in (429, 500, 502, 503, 504):
                raise

            if attempt == 2:
                raise

            time.sleep(2 * (attempt + 1))

    return None


async def main():
    bus = await MessageBus(bus_type=BusType.SESSION).connect()

    try:
        reply = await bus.call(
            Message(
                destination=PLAYER,
                path=PATH,
                interface=PROPERTIES,
                member="Get",
                signature="ss",
                body=[PLAYER_INTERFACE, "Metadata"],
            )
        )
        if not reply or not reply.body:
            print("Gagal mengambil metadata pemutar.")
            return
        metadata = reply.body[0].value

        title = metadata.get("xesam:title")
        artists = metadata.get("xesam:artist")
        album = metadata.get("xesam:album")
        length = metadata.get("mpris:length")

        title = title.value if title else ""
        artists = artists.value if artists else []
        artist = artists[0] if artists else ""
        album = album.value if album else ""
        duration = round(length.value / 1_000_000) if length else 0

        if not title or not artist:
            print("Judul atau artis lagu tidak tersedia.")
            return

        print(f"Lagu   : {title}")
        print(f"Artis  : {artist}")
        print(f"Album  : {album or '-'}")
        print(f"Durasi : {duration} detik")
        print("\nMencari lirik tersinkronisasi...")

        params = {
            "track_name": title,
            "artist_name": artist,
            "duration": duration,
        }
        if album:
            params["album_name"] = album

        result = await asyncio.to_thread(
            fetch_lyrics, params, "get"
        )

        if result is None:
            queries = [
                f"{title} {artist}",
                title,
            ]

            for query in queries:
                print(f"Mencari: {query}")

                result = await asyncio.to_thread(
                    fetch_lyrics,
                    {"q": query},
                    "search",
                )

                if result:
                    break

            if not result:
                print("Lirik tidak ditemukan di LRCLIB.")
                return

            candidates = (
                result if isinstance(result, list) else [result]
            )

            candidates.sort(
                key=lambda item: (
                    bool(item.get("syncedLyrics")),
                    -abs(
                        (item.get("duration") or duration)
                        - duration
                    ),
                ),
                reverse=True,
            )

            result = candidates[0]

            print(
                "Kandidat terpilih:",
                result.get("trackName", "?"),
                "—",
                result.get("artistName", "?"),
            )

        synced = result.get("syncedLyrics")
        plain = result.get("plainLyrics")

        if synced:
            print("\nBERHASIL: lirik bertimestamp ditemukan!")
            print("\nContoh beberapa baris:")
            print("\n".join(synced.splitlines()[:5]))
        elif plain:
            print("\nLirik ditemukan, tetapi tidak memiliki timestamp.")
            print("\n".join(plain.splitlines()[:5]))
        else:
            print("Hasil ditemukan, tetapi tidak berisi teks lirik.")

        synced = result.get("syncedLyrics")
        plain = result.get("plainLyrics")

        if synced:
            print("\nBERHASIL: lirik bertimestamp ditemukan!")
            print("\nContoh beberapa baris:")
            print("\n".join(synced.splitlines()[:5]))
        elif plain:
            print("\nLirik ditemukan, tetapi tidak memiliki timestamp.")
            print("\n".join(plain.splitlines()[:5]))
        else:
            print("Hasil ditemukan, tetapi tidak berisi teks lirik.")

    except (URLError, TimeoutError) as error:
        print(f"Gagal mengakses layanan lirik: {error}")
    except Exception as error:
        print(f"Gagal membaca metadata atau hasil API: {error}")
    finally:
        bus.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
