"""
Bridge antara backend Python (MPRIS, LRCLIB, LRC parser, Romaji) dan antarmuka Qt Quick / QML.
Menyediakan properti reaktif dan sinyal Qt untuk pembaruan UI secara efisien dan thread-safe.
"""

import asyncio
import threading
import time
from typing import Optional, Any

from PySide6.QtCore import QObject, Signal, Property, Slot

from dbus_next.aio import MessageBus
from dbus_next import BusType

from lyric_core import parse_lrc_text, active_lyric_entry, prepare_lyric
from lyrics_service import find_lyrics
from main import get_player_data, fetch_track_lyrics, MPRIS_PREFIX
from settings import load_settings, save_settings, DEFAULT_SETTINGS


class LyricBridge(QObject):
    """QObject bridge yang mengekspos status pemutar dan lirik ke QML."""

    hasPlayerChanged = Signal(bool)
    playbackStatusChanged = Signal(str)
    titleChanged = Signal(str)
    artistChanged = Signal(str)
    albumChanged = Signal(str)
    activeLyricChanged = Signal()
    romajiChanged = Signal()
    backingChanged = Signal()
    positionChanged = Signal(float)
    durationChanged = Signal(float)
    settingsChanged = Signal()

    # Sinyal internal untuk transfer data thread-safe dari worker thread ke Qt main thread
    _worker_update = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._settings = load_settings()

        self._has_player: bool = False
        self._playback_status: str = ""
        self._title: str = ""
        self._artist: str = ""
        self._album: str = ""
        self._active_lead: str = ""
        self._active_backing: str = ""
        self._has_backing: bool = False
        self._is_backing_only: bool = False
        self._active_romaji: str = ""
        self._has_romaji: bool = False
        self._position: float = 0.0
        self._duration: float = 0.0

        self._worker_update.connect(self._handle_worker_update)

        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._mock_mode: bool = False

    # --- Properties untuk QML ---

    @Property(bool, notify=hasPlayerChanged)
    def hasPlayer(self) -> bool:
        return self._has_player

    @Property(str, notify=playbackStatusChanged)
    def playbackStatus(self) -> str:
        return self._playback_status

    @Property(str, notify=titleChanged)
    def title(self) -> str:
        return self._title

    @Property(str, notify=artistChanged)
    def artist(self) -> str:
        return self._artist

    @Property(str, notify=albumChanged)
    def album(self) -> str:
        return self._album

    @Property(str, notify=activeLyricChanged)
    def activeLead(self) -> str:
        return self._active_lead

    @Property(str, notify=activeLyricChanged)
    def activeBacking(self) -> str:
        return self._active_backing

    @Property(bool, notify=activeLyricChanged)
    def hasBacking(self) -> bool:
        return self._has_backing

    @Property(bool, notify=activeLyricChanged)
    def isBackingOnly(self) -> bool:
        return self._is_backing_only

    @Property(str, notify=activeLyricChanged)
    def activeRomaji(self) -> str:
        return self._active_romaji

    @Property(bool, notify=activeLyricChanged)
    def hasRomaji(self) -> bool:
        return self._has_romaji

    @Property(float, notify=positionChanged)
    def position(self) -> float:
        return self._position

    @Property(float, notify=durationChanged)
    def duration(self) -> float:
        return self._duration

    @staticmethod
    def _format_min_sec(seconds: float) -> str:
        """Format detik menjadi M.SS (misal 18.0 -> 0.18, 102.0 -> 1.42, 204.0 -> 3.24)."""
        if seconds <= 0:
            return "0.00"
        total_sec = int(seconds)
        minutes = total_sec // 60
        rem = total_sec % 60
        return f"{minutes}.{rem:02d}"

    @Property(str, notify=positionChanged)
    def formattedTime(self) -> str:
        """Format penanda waktu M.SS / M.SS (contoh: 0.00 / 3.24, 1.42 / 3.24)."""
        if not self._has_player:
            return ""
        pos_str = self._format_min_sec(self._position)
        dur_str = self._format_min_sec(self._duration) if self._duration > 0 else "--:--"
        return f"{pos_str} / {dur_str}"

    # --- Properties Pengaturan Background & Font (Stage 11 / Settings) ---

    @Property(int, notify=settingsChanged)
    def bgWidthPercent(self) -> int:
        return int(self._settings.get("bgWidthPercent", 82))

    @Property(str, notify=settingsChanged)
    def bgColor(self) -> str:
        return str(self._settings.get("bgColor", "#0a0d12"))

    @Property(float, notify=settingsChanged)
    def bgOpacity(self) -> float:
        return float(self._settings.get("bgOpacity", 0.88))

    @Property(float, notify=settingsChanged)
    def bgFadeStart(self) -> float:
        return float(self._settings.get("bgFadeStart", 0.25))

    @Property(bool, notify=settingsChanged)
    def useUnifiedFont(self) -> bool:
        return bool(self._settings.get("useUnifiedFont", False))

    @Property(str, notify=settingsChanged)
    def unifiedFontFamily(self) -> str:
        return str(self._settings.get("unifiedFontFamily", "Noto Sans"))

    @Property(str, notify=settingsChanged)
    def titleFontFamily(self) -> str:
        return str(self._settings.get("titleFontFamily", "Noto Sans"))

    @Property(str, notify=settingsChanged)
    def artistFontFamily(self) -> str:
        return str(self._settings.get("artistFontFamily", "Noto Sans"))

    @Property(str, notify=settingsChanged)
    def lyricFontFamily(self) -> str:
        return str(self._settings.get("lyricFontFamily", "Noto Sans"))

    @Property(str, notify=settingsChanged)
    def romajiFontFamily(self) -> str:
        return str(self._settings.get("romajiFontFamily", "Noto Sans"))

    @Property(str, notify=settingsChanged)
    def timerFontFamily(self) -> str:
        return str(self._settings.get("timerFontFamily", "Noto Sans"))

    @Slot(str, "QVariant")
    def setSetting(self, key: str, value) -> None:
        """Mengubah satu pengaturan dan menyimpannya secara otomatis."""
        self._settings[key] = value
        save_settings(self._settings)
        self.settingsChanged.emit()

    @Slot(dict)
    def updateSettings(self, new_settings: dict) -> None:
        """Memperbarui sekumpulan pengaturan sekaligus."""
        self._settings.update(new_settings)
        save_settings(self._settings)
        self.settingsChanged.emit()

    @Slot()
    def resetSettings(self) -> None:
        """Mengembalikan seluruh pengaturan ke konfigurasi default."""
        self._settings = dict(DEFAULT_SETTINGS)
        save_settings(self._settings)
        self.settingsChanged.emit()

    # --- Pengaturan Mock (untuk pengujian headless & pratinjau visual) ---

    @Slot(bool, str, str, str, str, str, str)
    @Slot(bool, str, str, str, str, str, str, float, float)
    def setMock(
        self,
        has_player: bool,
        status: str,
        title: str,
        artist: str,
        lead: str = "",
        backing: str = "",
        romaji: str = "",
        position: float = 0.0,
        duration: float = 0.0,
    ):
        """Memungkinkan pengujian kondisi visual tanpa ketergantungan live player."""
        self._mock_mode = True
        update = {
            "has_player": has_player,
            "status": status,
            "title": title,
            "artist": artist,
            "album": "",
            "active_lead": lead,
            "active_backing": backing,
            "has_backing": bool(backing),
            "is_backing_only": bool(backing and not lead),
            "active_romaji": romaji,
            "has_romaji": bool(romaji),
            "position": position,
            "duration": duration,
        }
        self._handle_worker_update(update)

    # --- Slot pemrosesan data di Qt Main Thread ---

    @Slot(dict)
    def _handle_worker_update(self, data: dict):
        has_player = data.get("has_player", False)
        status = data.get("status", "")
        title = data.get("title", "")
        artist = data.get("artist", "")
        album = data.get("album", "")
        lead = data.get("active_lead", "")
        backing = data.get("active_backing", "")
        has_backing = data.get("has_backing", False)
        is_backing_only = data.get("is_backing_only", False)
        romaji = data.get("active_romaji", "")
        has_romaji = data.get("has_romaji", False)
        pos = data.get("position", 0.0)
        dur = data.get("duration", 0.0)

        changed_has_player = (self._has_player != has_player)
        changed_status = (self._playback_status != status)
        changed_title = (self._title != title)
        changed_artist = (self._artist != artist)
        changed_album = (self._album != album)
        changed_lyric = (self._active_lead != lead)
        changed_backing = (
            self._active_backing != backing
            or self._has_backing != has_backing
            or self._is_backing_only != is_backing_only
        )
        changed_romaji = (
            self._active_romaji != romaji
            or self._has_romaji != has_romaji
        )
        changed_pos = (abs(self._position - pos) > 0.05)
        changed_dur = (abs(self._duration - dur) > 0.05)

        self._has_player = has_player
        self._playback_status = status
        self._title = title
        self._artist = artist
        self._album = album
        self._active_lead = lead
        self._active_backing = backing
        self._has_backing = has_backing
        self._is_backing_only = is_backing_only
        self._active_romaji = romaji
        self._has_romaji = has_romaji
        self._position = pos
        self._duration = dur

        changed_lyrics = (changed_lyric or changed_backing or changed_romaji)

        if changed_has_player:
            self.hasPlayerChanged.emit(self._has_player)
        if changed_status:
            self.playbackStatusChanged.emit(self._playback_status)
        if changed_title:
            self.titleChanged.emit(self._title)
        if changed_artist:
            self.artistChanged.emit(self._artist)
        if changed_album:
            self.albumChanged.emit(self._album)
        if changed_lyrics:
            self.activeLyricChanged.emit()
        if changed_dur:
            self.durationChanged.emit(self._duration)
        if changed_pos or changed_dur:
            self.positionChanged.emit(self._position)

    # --- Thread Worker MPRIS Background ---

    def start(self):
        """Memulai loop pemantauan MPRIS di background thread."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._run_async_worker,
            name="LyricMprisWorker",
            daemon=True,
        )
        self._worker_thread.start()

    def stop(self):
        """Menghentikan thread worker."""
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.5)
            self._worker_thread = None

    def _run_async_worker(self):
        """Menjalankan loop asyncio di thread terpisah."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._worker_loop())
        finally:
            loop.close()

    async def _worker_loop(self):
        """Loop asinkron MPRIS, pengambilan lirik, dan pencocokan posisi."""
        loop = asyncio.get_running_loop()
        bus = None
        dbus: Any = None

        lyrics_cache: dict[tuple[str, str], dict] = {}
        current_track_key: tuple[str, str, str] | None = None
        current_service: str | None = None
        last_names_check: float = 0.0
        fetch_task: asyncio.Task | None = None
        current_lyrics_data: dict | None = None
        last_displayed_entry: tuple[float, str] | None = None
        last_prep: dict | None = None

        while not self._stop_event.is_set():
            if self._mock_mode:
                await asyncio.sleep(0.5)
                continue

            try:
                if bus is None:
                    bus = await MessageBus(bus_type=BusType.SESSION).connect()
                    intro = await bus.introspect(
                        "org.freedesktop.DBus", "/org/freedesktop/DBus"
                    )
                    obj = bus.get_proxy_object(
                        "org.freedesktop.DBus", "/org/freedesktop/DBus", intro
                    )
                    dbus: Any = obj.get_interface("org.freedesktop.DBus")

                now = time.monotonic()
                selected = None

                # Query langsung pemutar yang sudah aktif untuk memangkas latensi D-Bus
                if current_service and (now - last_names_check) < 2.0:
                    data = await get_player_data(bus, current_service)
                    if data:
                        selected = (current_service, data)
                    else:
                        current_service = None

                if selected is None:
                    last_names_check = now
                    if dbus is None:
                        await asyncio.sleep(0.5)
                        continue
                    try:
                        names = await dbus.call_list_names()
                    except Exception:
                        await asyncio.sleep(0.5)
                        continue

                    players = sorted(
                        name for name in names
                        if name.startswith(MPRIS_PREFIX)
                    )

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
                    if selected:
                        current_service = selected[0]
                    else:
                        current_service = None

                if selected is None:
                    current_service = None
                    if fetch_task and not fetch_task.done():
                        fetch_task.cancel()
                        fetch_task = None
                    current_track_key = None
                    current_lyrics_data = None
                    last_displayed_entry = None
                    last_prep = None

                    self._worker_update.emit({
                        "has_player": False,
                        "status": "",
                        "title": "",
                        "artist": "",
                        "album": "",
                        "active_lead": "",
                        "active_backing": "",
                        "has_backing": False,
                        "is_backing_only": False,
                        "active_romaji": "",
                        "has_romaji": False,
                        "position": 0.0,
                        "duration": 0.0,
                    })
                    await asyncio.sleep(0.5)
                    continue

                service, data = selected
                track_key = (service, data["title"], data["artist"])
                cache_key = (data["title"].lower(), data["artist"].lower())

                # 1. Pergantian lagu
                if track_key != current_track_key:
                    if fetch_task and not fetch_task.done():
                        fetch_task.cancel()
                        fetch_task = None

                    current_track_key = track_key
                    current_lyrics_data = None
                    last_displayed_entry = None
                    last_prep = None

                    if cache_key in lyrics_cache:
                        current_lyrics_data = lyrics_cache[cache_key]
                    else:
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

                # 2. Cek task lirik selesai
                if fetch_task and fetch_task.done():
                    try:
                        res_data = fetch_task.result()
                    except (asyncio.CancelledError, Exception) as err:
                        res_data = {"type": "error", "message": str(err), "lyrics": None}
                    fetch_task = None

                    if track_key == current_track_key:
                        current_lyrics_data = res_data

                # 3. Hitung lirik aktif
                lead_text = ""
                backing_text = ""
                has_backing = False
                is_backing_only = False
                romaji_text = ""
                has_romaji = False

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
                            last_prep = prepare_lyric(raw_text, timestamp=ts)
                        else:
                            last_prep = None

                    if last_prep:
                        if last_prep.get("is_backing_only"):
                            lead_text = ""
                            backing_text = last_prep.get("backing") or ""
                            has_backing = True
                            is_backing_only = True
                            romaji_text = last_prep.get("backing_romaji") or last_prep.get("romaji") or ""
                        elif last_prep.get("has_backing"):
                            lead_text = last_prep.get("lead") or ""
                            backing_text = last_prep.get("backing") or ""
                            has_backing = True
                            is_backing_only = False
                            romaji_text = last_prep.get("lead_romaji") or last_prep.get("romaji") or ""
                        else:
                            lead_text = last_prep.get("original") or ""
                            backing_text = ""
                            has_backing = False
                            is_backing_only = False
                            romaji_text = last_prep.get("romaji") or ""

                        has_romaji = bool(romaji_text)
                elif current_lyrics_data and current_lyrics_data.get("type") == "plain":
                    # Plain lyrics jika synced tidak tersedia
                    lead_text = ""
                    romaji_text = ""
                elif last_prep:
                    # Pertahankan lirik terakhir saat paused
                    lead_text = last_prep.get("lead") or last_prep.get("original") or ""
                    backing_text = last_prep.get("backing") or ""
                    has_backing = last_prep.get("has_backing", False)
                    is_backing_only = last_prep.get("is_backing_only", False)
                    romaji_text = last_prep.get("romaji") or ""
                    has_romaji = bool(romaji_text)

                self._worker_update.emit({
                    "has_player": True,
                    "status": data["status"],
                    "title": data["title"],
                    "artist": data["artist"],
                    "album": data["album"],
                    "active_lead": lead_text,
                    "active_backing": backing_text,
                    "has_backing": has_backing,
                    "is_backing_only": is_backing_only,
                    "active_romaji": romaji_text,
                    "has_romaji": has_romaji,
                    "position": data["position"],
                    "duration": data["duration"],
                })

                # Adaptive sleep: 65ms saat Playing untuk akurasi sinkronisasi audio optimal,
                # 300ms saat Paused untuk efisiensi CPU (Stage 10.5).
                if data["status"] == "Playing":
                    await asyncio.sleep(0.065)
                else:
                    await asyncio.sleep(0.30)

            except asyncio.CancelledError:
                break
            except Exception:
                if bus:
                    try:
                        bus.disconnect()
                    except Exception:
                        pass
                bus = None
                dbus = None
                await asyncio.sleep(0.5)
        if fetch_task and not fetch_task.done():
            fetch_task.cancel()
            try:
                await fetch_task
            except (asyncio.CancelledError, Exception):
                pass
        if bus:
            try:
                bus.disconnect()
            except Exception:
                pass


