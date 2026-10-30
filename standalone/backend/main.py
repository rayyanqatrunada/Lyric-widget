import asyncio
import sys
from typing import Any
from dbus_next.aio import MessageBus
from dbus_next import BusType

from lyric_core import parse_lrc_text, active_lyric, active_lyric_entry, prepare_lyric
from lyrics_service import find_lyrics

MPRIS_PREFIX = "org.mpris.MediaPlayer2."


def format_time(seconds: float) -> str:
    """Format waktu detik ke format MM:SS.ss."""
    seconds = max(0.0, float(seconds))
    minutes = int(seconds) // 60
    remaining = seconds % 60
    return f"{minutes:02d}:{remaining:05.2f}"


_player_proxy_cache: dict[str, tuple[Any, Any]] = {}


async def get_player_data(bus, service: str) -> dict | None:
    """Membaca metadata, status pemutaran, dan posisi dari pemutar MPRIS dengan caching proxy efisien."""
    try:
        # Gunakan proxy object ter-cache jika tersedia untuk menghindari introspeksi D-Bus berulang
        if service not in _player_proxy_cache:
            introspection = await bus.introspect(
                service, "/org/mpris/MediaPlayer2"
            )
            obj = bus.get_proxy_object(
                service, "/org/mpris/MediaPlayer2", introspection
            )
            props = obj.get_interface("org.freedesktop.DBus.Properties")
            _player_proxy_cache[service] = (obj, props)
        else:
            obj, props = _player_proxy_cache[service]

        try:
            # Panggilan tunggal GetAll jauh lebih cepat dibanding 3 panggilan roundtrip terpisah
            all_props = await props.call_get_all("org.mpris.MediaPlayer2.Player")
            metadata_raw = all_props.get("Metadata")
            status_raw = all_props.get("PlaybackStatus")
            position_raw = all_props.get("Position", 0)
        except Exception:
            # Fallback ke pemanggilan per properti jika GetAll tidak didukung oleh implementasi player
            metadata_raw = await props.call_get(
                "org.mpris.MediaPlayer2.Player", "Metadata"
            )
            status_raw = await props.call_get(
                "org.mpris.MediaPlayer2.Player", "PlaybackStatus"
            )
            try:
                position_raw = await props.call_get(
                    "org.mpris.MediaPlayer2.Player", "Position"
                )
            except Exception:
                position_raw = 0

        # Ekstrak nilai dari Variant dbus_next
        metadata = metadata_raw.value if hasattr(metadata_raw, "value") else metadata_raw
        status = status_raw.value if hasattr(status_raw, "value") else status_raw
        position = position_raw.value if hasattr(position_raw, "value") else position_raw

        title_raw = metadata.get("xesam:title", "") if metadata else ""
        title = title_raw.value if hasattr(title_raw, "value") else title_raw
        title = str(title).strip() if title else ""

        artist_raw = metadata.get("xesam:artist", []) if metadata else []
        artist_val = artist_raw.value if hasattr(artist_raw, "value") else artist_raw
        if isinstance(artist_val, list):
            artist_str = ", ".join(str(a) for a in artist_val if a).strip()
        else:
            artist_str = str(artist_val).strip() if artist_val else ""

        album_raw = metadata.get("xesam:album", "") if metadata else ""
        album = album_raw.value if hasattr(album_raw, "value") else album_raw
        album = str(album).strip() if album else ""

        length_raw = metadata.get("mpris:length", 0) if metadata else 0
        length_val = length_raw.value if hasattr(length_raw, "value") else length_raw
        try:
            duration = float(length_val) / 1_000_000
        except (ValueError, TypeError):
            duration = 0.0

        try:
            pos_seconds = float(position) / 1_000_000
        except (ValueError, TypeError):
            pos_seconds = 0.0

        # Jika player belum memuat lagu dengan judul valid
        if not title:
            return None

        return {
            "title": title,
            "artist": artist_str or "Unknown Artist",
            "album": album,
            "duration": duration,
            "status": str(status),
            "position": max(0.0, pos_seconds),
        }
    except Exception:
        # Bersihkan cache jika player terputus atau terjadi galat D-Bus
        _player_proxy_cache.pop(service, None)
        return None


async def fetch_track_lyrics(
    title: str,
    artist: str,
    album: str,
    duration: float,
    cache_key: tuple,
    cache: dict,
) -> dict:
    """Mengambil dan mem-parsing lirik secara asinkron di background."""
    try:
        res = await find_lyrics(title, artist, album=album, duration=duration)
        if res and res.get("syncedLyrics"):
            parsed = parse_lrc_text(res["syncedLyrics"])
            entry = {
                "type": "synced",
                "lyrics": parsed,
                "count": len(parsed),
            }
        elif res and res.get("plainLyrics"):
            entry = {
                "type": "plain",
                "lyrics": res["plainLyrics"],
            }
        else:
            entry = {
                "type": "none",
                "lyrics": None,
            }
    except Exception as err:
        entry = {
            "type": "error",
            "message": str(err),
            "lyrics": None,
        }

    cache[cache_key] = entry
    return entry


def print_lyrics_status(entry: dict) -> None:
    """Mencetak status ketersediaan lirik tanpa merusak tata letak terminal."""
    sys.stdout.write("\r\033[K")
    if not entry:
        return
    ltype = entry.get("type")
    if ltype == "synced":
        print(f"[INFO]   Lirik tersinkronisasi siap ({entry.get('count', 0)} baris).\n")
    elif ltype == "plain":
        print("[INFO]   Lirik sinkronisasi tidak tersedia (hanya lirik biasa).\n")
    elif ltype == "none":
        print("[INFO]   Lirik tidak ditemukan di LRCLIB.\n")
    elif ltype == "error":
        print(f"[INFO]   Gagal mengambil lirik: {entry.get('message', 'Network error')}\n")


async def main():
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    intro = await bus.introspect(
        "org.freedesktop.DBus", "/org/freedesktop/DBus"
    )
    obj = bus.get_proxy_object(
        "org.freedesktop.DBus", "/org/freedesktop/DBus", intro
    )
    dbus: Any = obj.get_interface("org.freedesktop.DBus")

    lyrics_cache: dict[tuple[str, str], dict] = {}
    current_track_key: tuple[str, str, str] | None = None
    fetch_task: asyncio.Task | None = None
    current_lyrics_data: dict | None = None
    last_displayed_entry: tuple[float, str] | None = None
    last_status: str | None = None
    previous_state: str | None = None

    print("=== Lyric Widget Backend ===")
    print("Menunggu pemutar musik... (Ctrl+C untuk berhenti)\n")

    while True:
        try:
            try:
                names = await dbus.call_list_names()
            except Exception:
                await asyncio.sleep(0.5)
                continue

            players = sorted(
                name for name in names
                if name.startswith(MPRIS_PREFIX)
            )

            # Deteksi pemutar musik yang aktif:
            # Utamakan yang sedang 'Playing', lalu 'Paused'
            active_player = None
            paused_player = None

            for service in players:
                data = await get_player_data(bus, service)
                if not data:
                    continue
                if data["status"] == "Playing":
                    active_player = (service, data)
                    break
                elif data["status"] == "Paused" and paused_player is None:
                    paused_player = (service, data)

            selected = active_player or paused_player

            if selected is None:
                if previous_state != "NO_PLAYER":
                    if fetch_task and not fetch_task.done():
                        fetch_task.cancel()
                        fetch_task = None
                    sys.stdout.write("\r\033[K")
                    print("[PLAYER] Tidak ada lagu aktif.")
                    previous_state = "NO_PLAYER"
                    current_track_key = None
                    current_lyrics_data = None
                    last_displayed_entry = None
                    last_status = None
                await asyncio.sleep(0.5)
                continue

            service, data = selected
            previous_state = "PLAYER_ACTIVE"
            track_key = (service, data["title"], data["artist"])
            cache_key = (data["title"].lower(), data["artist"].lower())

            # 1. Deteksi pergantian lagu (Track Change)
            if track_key != current_track_key:
                # Batalkan task unduh sebelumnya jika masih berjalan
                if fetch_task and not fetch_task.done():
                    fetch_task.cancel()
                    fetch_task = None

                # Bersihkan lirik lagu sebelumnya segera agar tidak stale
                current_track_key = track_key
                current_lyrics_data = None
                last_displayed_entry = None

                # Tampilkan informasi lagu yang baru aktif
                player_short = service.removeprefix(MPRIS_PREFIX)
                sys.stdout.write("\r\033[K")
                print(f"\n[PLAYER] {player_short}")
                print(f"[LAGU]   {data['title']} — {data['artist']}")
                if data["album"]:
                    print(f"[ALBUM]  {data['album']}")
                print(f"[STATUS] {data['status']}")
                last_status = data["status"]

                # Cek cache lirik terlebih dahulu
                if cache_key in lyrics_cache:
                    current_lyrics_data = lyrics_cache[cache_key]
                    print_lyrics_status(current_lyrics_data)
                else:
                    print("[INFO]   Mencari lirik di LRCLIB...")
                    # Mulai fetch di background tanpa memblokir loop pemutaran
                    fetch_task = asyncio.create_task(
                        fetch_track_lyrics(
                            data["title"],
                            data["artist"],
                            data["album"],
                            data["duration"],
                            cache_key,
                            lyrics_cache,
                        )
                    )

            # 2. Cek apakah task unduh lirik di background telah selesai
            if fetch_task and fetch_task.done():
                try:
                    res_data = fetch_task.result()
                except (asyncio.CancelledError, Exception) as err:
                    res_data = {"type": "error", "message": str(err), "lyrics": None}
                fetch_task = None

                # Pastikan hasil cocok dengan lagu yang sedang aktif saat ini
                if track_key == current_track_key:
                    current_lyrics_data = res_data
                    print_lyrics_status(current_lyrics_data)

            # 3. Deteksi perubahan status Playback (Playing <-> Paused)
            if data["status"] != last_status:
                sys.stdout.write("\r\033[K")
                print(f"[STATUS] {data['status']}")
                last_status = data["status"]

            # 4. Tampilkan lirik aktif sesuai posisi pemutaran saat ini
            if (
                current_lyrics_data
                and current_lyrics_data.get("type") == "synced"
                and isinstance(current_lyrics_data.get("lyrics"), list)
            ):
                pos = data["position"]
                lyrics_list = current_lyrics_data["lyrics"]
                active_entry = active_lyric_entry(lyrics_list, pos)

                if active_entry != last_displayed_entry:
                    last_displayed_entry = active_entry
                    if active_entry:
                        ts, raw_text = active_entry[0], active_entry[1]
                        sys.stdout.write("\r\033[K")
                        prep = prepare_lyric(raw_text, timestamp=ts)
                        time_str = format_time(ts)

                        if prep.get("is_backing_only"):
                            print(f"[{time_str}] (Backing) {prep['backing']}")
                            if prep.get("backing_romaji"):
                                print(f"           {prep['backing_romaji']}")
                        elif prep.get("has_backing"):
                            print(f"[{time_str}] {prep['lead']}")
                            print(f"           (Backing) {prep['backing']}")
                            if prep.get("lead_romaji"):
                                print(f"           {prep['lead_romaji']}")
                        else:
                            print(f"[{time_str}] {prep['original']}")
                            if prep.get("romaji"):
                                print(f"           {prep['romaji']}")
                        print()

            # 5. Tampilkan indikator posisi pemutaran secara dinamis
            sys.stdout.write(f"\r[POSISI] {format_time(data['position'])}   ")
            sys.stdout.flush()

            await asyncio.sleep(0.25)

        except asyncio.CancelledError:
            break
        except Exception:
            # Toleransi error sesaat pada D-Bus tanpa mematikan program
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        sys.stdout.write("\r\033[K")
        print("\nBackend dihentikan.")
