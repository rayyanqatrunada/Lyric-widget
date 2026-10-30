import asyncio
import json
import re
import time
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import pykakasi

USER_AGENT = "LyricWidget/0.1 (Fedora KDE Plasma)"

# Inisialisasi converter pykakasi untuk pencocokan fonetik Romaji <-> Kanji/Kana
_kakasi = pykakasi.kakasi()

# Cache dalam memori untuk alias metadata (key: (title.lower(), artist.lower()) -> list[(alias_title, alias_artist)])
_alias_cache: dict[tuple[str, str], list[tuple[str, str]]] = {}
_MAX_ALIAS_CACHE_SIZE = 128

# Cache dalam memori untuk fallback lyrics (key: (title.lower(), artist.lower()) -> dict | None)
_fallback_lyrics_cache: dict[tuple[str, str], dict | None] = {}
_MAX_FALLBACK_CACHE_SIZE = 128

# Pola untuk mendeteksi anotasi versi dan featured artist di judul atau nama artis
VERSION_PATTERN = re.compile(
    r"\s*[\(\[](?:feat\.?|ft\.?|featuring|acoustic|hikigatari|live|tv\s*size|tv\s*ver\.?|tv\s*version|instrumental|off\s*vocal|karaoke|remix|remaster(?:ed)?|version|ver\.?|ost|original\s*game\s*soundtrack|original\s*soundtrack|bonus\s*track)[^\)\]]*[\)\]]",
    re.IGNORECASE,
)
FEAT_DASH_PATTERN = re.compile(
    r"\s*[-–—]\s*(?:feat\.?|ft\.?|featuring|acoustic|instrumental|live|remix)[^$]*$",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Menghapus tanda baca, normalisasi spasi ganda, dan lowercase untuk perbandingan aman."""
    if not text:
        return ""
    t = text.lower()
    t = re.sub(r"[^\w\s]", "", t)
    return " ".join(t.split())


def to_romaji_clean(text: str) -> str:
    """Mengubah teks (Kanji, Kana, atau Latin) menjadi romaji alfanumerik tanpa spasi/tanda baca."""
    if not text:
        return ""
    try:
        conv = _kakasi.convert(text)
        rom = "".join(item["hepburn"] for item in conv).lower()
        return re.sub(r"[^\w]", "", rom)
    except Exception:
        return re.sub(r"[^\w]", "", text.lower())


def get_title_variants(title: str) -> list[str]:
    """Menghasilkan variasi judul yang dibatasi untuk fallback pencarian.

    Menjaga judul asli sebagai kandidat pertama dan terkuat, lalu menambahkan
    versi yang dibersihkan dari anotasi versi/feat jika berbeda.
    """
    clean_title = (title or "").strip()
    if not clean_title:
        return []

    variants = [clean_title]

    # Bersihkan anotasi dalam kurung / kurung siku
    base = VERSION_PATTERN.sub("", clean_title)
    # Bersihkan anotasi setelah tanda strip
    base = FEAT_DASH_PATTERN.sub("", base).strip()

    if base and base.lower() != clean_title.lower() and len(base) >= 2:
        variants.append(base)

    return variants


def get_artist_variants(artist: str) -> list[str]:
    """Menghasilkan variasi nama artis dengan menghapus featured artists jika ada."""
    clean_artist = (artist or "").strip()
    if not clean_artist:
        return []

    variants = [clean_artist]

    # Bersihkan pola konjungsi lokal YouTube Music Indonesia (mis. " dan ")
    with_amp = re.sub(r"\s+dan\s+", " & ", clean_artist, flags=re.IGNORECASE).strip()
    if with_amp and with_amp.lower() != clean_artist.lower() and with_amp not in variants:
        variants.append(with_amp)

    # Ekstrak artis utama sebelum pemisah multi-artis
    primary = re.split(r"\s*(?:&|,|\/|feat\.?|ft\.?|featuring|dan)\s*", clean_artist, flags=re.IGNORECASE)[0].strip()
    if primary and primary.lower() != clean_artist.lower() and primary not in variants and len(primary) >= 2:
        variants.append(primary)

    # Bersihkan pola kurung atau pemisah feat
    base = VERSION_PATTERN.sub("", clean_artist)
    base = FEAT_DASH_PATTERN.sub("", base)
    base = re.sub(
        r"\s+(?:feat\.?|ft\.?|featuring)\s+.+$", "", base, flags=re.IGNORECASE
    ).strip()

    if base and base.lower() != clean_artist.lower() and len(base) >= 2 and base not in variants:
        variants.append(base)

    return variants


def is_valid_alias(
    orig_title: str,
    orig_artist: str,
    meta_title: str,
    meta_artist: str,
    orig_duration: float = 0.0,
    meta_duration: float = 0.0,
) -> bool:
    """Memverifikasi kecocokan fonetik antara judul/artis asli dengan hasil metadata provider.

    Mencegah pemilihan alias yang salah atau ambigu dengan membandingkan transliterasi
    romaji pykakasi dan selisih durasi jika tersedia.
    """
    if not meta_title or not meta_artist:
        return False

    norm_orig_art = to_romaji_clean(orig_artist)
    norm_meta_art = to_romaji_clean(meta_artist)

    # 1. Verifikasi Artis: fonetik harus cocok atau saling mengandung (misal feat)
    if (
        norm_orig_art != norm_meta_art
        and norm_orig_art not in norm_meta_art
        and norm_meta_art not in norm_orig_art
    ):
        return False

    # 2. Verifikasi Judul: fonetik romaji harus cocok
    norm_orig_title = to_romaji_clean(orig_title)
    norm_meta_title = to_romaji_clean(meta_title)

    # Hilangkan variasi feat/version untuk perbandingan base
    base_orig_title = to_romaji_clean(
        FEAT_DASH_PATTERN.sub("", VERSION_PATTERN.sub("", orig_title))
    )
    base_meta_title = to_romaji_clean(
        FEAT_DASH_PATTERN.sub("", VERSION_PATTERN.sub("", meta_title))
    )

    title_matches = (
        norm_orig_title == norm_meta_title
        or base_orig_title == base_meta_title
        or (base_orig_title and base_orig_title in norm_meta_title)
        or (base_meta_title and base_meta_title in norm_orig_title)
    )

    if not title_matches:
        return False

    # 3. Verifikasi Durasi jika kedua sumber menyediakan
    if orig_duration > 0 and meta_duration > 0:
        if abs(orig_duration - meta_duration) > 12.0:
            return False

    return True


def fetch_metadata_aliases(
    title: str,
    artist: str,
    album: str = "",
    duration: float = 0.0,
) -> list[tuple[str, str]]:
    """Mencari alias judul/artis kanji-kana melalui public iTunes JP Search API.

    Hasil disimpan dalam cache in-memory untuk menghindari request jaringan berulang.
    """
    clean_title = (title or "").strip()
    clean_artist = (artist or "").strip()
    if not clean_title or not clean_artist:
        return []

    cache_key = (clean_title.lower(), clean_artist.lower())
    if cache_key in _alias_cache:
        return _alias_cache[cache_key]

    term = f"{clean_title} {clean_artist}"
    url = f"https://itunes.apple.com/search?{urlencode({'term': term, 'country': 'JP', 'entity': 'song', 'limit': 5})}"
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
        },
    )

    valid_aliases: list[tuple[str, str]] = []

    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
            results = payload.get("results", [])

            for item in results:
                cand_title = (item.get("trackName") or "").strip()
                cand_artist = (item.get("artistName") or "").strip()
                cand_dur = round(float(item.get("trackTimeMillis") or 0) / 1000)

                if is_valid_alias(
                    clean_title,
                    clean_artist,
                    cand_title,
                    cand_artist,
                    duration,
                    cand_dur,
                ):
                    alias_pair = (cand_title, cand_artist)
                    if alias_pair not in valid_aliases:
                        valid_aliases.append(alias_pair)

    except HTTPError as error:
        if error.code == 429 and hasattr(error, "headers") and error.headers:
            retry_header = error.headers.get("Retry-After")
            if retry_header:
                try:
                    time.sleep(min(max(1, int(retry_header)), 5))
                except (ValueError, TypeError):
                    pass
    except (URLError, TimeoutError, json.JSONDecodeError, Exception):
        pass

    # Simpan dalam cache in-memory (batasi ukuran cache)
    if len(_alias_cache) >= _MAX_ALIAS_CACHE_SIZE:
        _alias_cache.clear()
    _alias_cache[cache_key] = valid_aliases

    return valid_aliases


def clean_fallback_lyrics_text(raw_text: str) -> str:
    """Membersihkan format lirik dari provider fallback:

    - Normalisasi line breaks (\\r\\n -> \\n).
    - Memangkas leading/trailing whitespace.
    - Menghapus header metadata umum jika ada.
    """
    if not raw_text:
        return ""
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # Bersihkan header umum jika ada
    text = re.sub(
        r"^(?:Paroles de la chanson[^\n]*\n+|Lyrics of[^\n]*\n+)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text.strip()


def fetch_lyrics_ovh(
    title: str,
    artist: str,
    album: str = "",
    duration: float = 0.0,
) -> dict | None:
    """Mencari lirik alternatif dari API lyrics.ovh sebagai fallback ketika LRCLIB gagal.

    Hanya dijalankan jika seluruh pencarian LRCLIB tidak menghasilkan kandidat valid.
    Menjaga lirik sinkron jika payload menyediakan timestamp LRC asli, atau plain jika tidak.
    Hasil disimpan dalam cache in-memory untuk membatasi request jaringan.
    """
    clean_title = (title or "").strip()
    clean_artist = (artist or "").strip()

    if not clean_title or not clean_artist:
        return None

    # Validasi kecocokan dasar: tolak query kosong atau hanya tanda baca
    if not normalize_text(clean_title) or not normalize_text(clean_artist):
        return None

    cache_key = (clean_title.lower(), clean_artist.lower())
    if cache_key in _fallback_lyrics_cache:
        return _fallback_lyrics_cache[cache_key]

    # Buat variasi query yang dibatasi (maksimal 2 request)
    queries_to_try: list[tuple[str, str]] = [(clean_artist, clean_title)]

    # Coba varian dasar jika judul memiliki anotasi versi/feat
    base_title = FEAT_DASH_PATTERN.sub("", VERSION_PATTERN.sub("", clean_title)).strip()
    base_artist = FEAT_DASH_PATTERN.sub("", VERSION_PATTERN.sub("", clean_artist)).strip()
    if base_title and base_title != clean_title:
        queries_to_try.append((clean_artist, base_title))
    elif base_artist and base_artist != clean_artist:
        queries_to_try.append((base_artist, clean_title))

    found_lyrics: str | None = None

    for q_art, q_tit in queries_to_try[:2]:
        qa = quote(q_art, safe="")
        qt = quote(q_tit, safe="")
        url = f"https://api.lyrics.ovh/v1/{qa}/{qt}"
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
            },
        )

        try:
            with urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
                raw_lyrics = payload.get("lyrics")
                if raw_lyrics and isinstance(raw_lyrics, str):
                    cleaned = clean_fallback_lyrics_text(raw_lyrics)
                    if len(cleaned) >= 10:
                        found_lyrics = cleaned
                        break

        except HTTPError as error:
            # 404 Not Found: lagu tidak terdaftar
            if error.code == 404:
                continue
            # 429 Too Many Requests: hormati Retry-After jika ada
            if error.code == 429 and hasattr(error, "headers") and error.headers:
                retry_header = error.headers.get("Retry-After")
                if retry_header:
                    try:
                        time.sleep(min(max(1, int(retry_header)), 5))
                    except (ValueError, TypeError):
                        pass
                break
            continue
        except (URLError, TimeoutError, json.JSONDecodeError, Exception):
            break

    result: dict | None = None
    if found_lyrics:
        has_lrc_timestamps = bool(
            re.search(r"\[\d{2}:\d{2}(?:\.\d{2,3})?\]", found_lyrics)
        )
        if has_lrc_timestamps:
            synced_lyrics = found_lyrics
            plain_lyrics = re.sub(
                r"\[\d{2}:\d{2}(?:\.\d{2,3})?\]\s*", "", found_lyrics
            ).strip()
        else:
            synced_lyrics = None
            plain_lyrics = found_lyrics

        if plain_lyrics:
            result = {
                "id": None,
                "trackName": clean_title,
                "artistName": clean_artist,
                "albumName": album or "",
                "duration": round(float(duration)) if duration > 0 else 0,
                "instrumental": False,
                "plainLyrics": plain_lyrics,
                "syncedLyrics": synced_lyrics,
                "source": "lyrics.ovh",
            }

    # Simpan dalam cache in-memory (batasi ukuran cache)
    if len(_fallback_lyrics_cache) >= _MAX_FALLBACK_CACHE_SIZE:
        _fallback_lyrics_cache.clear()
    _fallback_lyrics_cache[cache_key] = result

    return result


def _fetch_lyrics(params: dict, endpoint: str) -> dict | list | None:
    """Mengambil data dari endpoint LRCLIB dengan penanganan error, HTTP 429, dan retry."""
    url = f"https://lrclib.net/api/{endpoint}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
        },
    )

    for attempt in range(3):
        try:
            with urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))

        except HTTPError as error:
            # 404 Not Found: lagu tidak terdaftar di database LRCLIB
            if error.code == 404:
                return None

            # 400 Bad Request: kesalahan validasi parameter query
            if error.code == 400:
                try:
                    error_payload = json.loads(error.read().decode("utf-8"))
                    _ = error_payload.get("message")
                except Exception:
                    pass
                return None

            # 429 Too Many Requests: hormati header Retry-After jika tersedia
            if error.code == 429:
                sleep_seconds = 2 * (attempt + 1)
                if hasattr(error, "headers") and error.headers:
                    retry_header = error.headers.get("Retry-After")
                    if retry_header:
                        try:
                            sleep_seconds = min(max(1, int(retry_header)), 10)
                        except (ValueError, TypeError):
                            pass
                if attempt == 2:
                    return None
                time.sleep(sleep_seconds)
                continue

            # Error sementara dari server (5xx): coba ulang dengan backoff
            if error.code not in (500, 502, 503, 504):
                return None

            if attempt == 2:
                return None

            time.sleep(2 * (attempt + 1))

        except (URLError, TimeoutError):
            # Gangguan jaringan atau timeout sementara
            if attempt == 2:
                return None
            time.sleep(2 * (attempt + 1))

        except json.JSONDecodeError:
            return None

    return None


def score_candidate(
    candidate: dict,
    req_title: str,
    title_variants: list[str],
    req_artist: str,
    artist_variants: list[str],
    req_album: str,
    req_duration: float,
) -> tuple[float, bool]:
    """Menilai kelayakan dan skor kecocokan kandidat lirik.

    Mengembalikan (skor, is_acceptable). Jika kandidat berasal dari artis
    yang salah atau lagu yang tidak relevan, is_acceptable bernilai False.
    """
    if not isinstance(candidate, dict):
        return 0.0, False

    # Kandidat harus memiliki teks lirik asli
    has_synced = bool(candidate.get("syncedLyrics"))
    has_plain = bool(candidate.get("plainLyrics"))
    if not has_synced and not has_plain:
        return 0.0, False

    cand_title = candidate.get("trackName") or ""
    cand_artist = candidate.get("artistName") or ""
    cand_album = candidate.get("albumName") or ""
    try:
        cand_duration = float(candidate.get("duration") or 0)
    except (ValueError, TypeError):
        cand_duration = 0.0

    norm_cand_artist = normalize_text(cand_artist)
    norm_cand_title = normalize_text(cand_title)

    if not norm_cand_artist or not norm_cand_title:
        return 0.0, False

    norm_req_title = normalize_text(req_title)
    base_cand_title = normalize_text(
        FEAT_DASH_PATTERN.sub("", VERSION_PATTERN.sub("", cand_title)).strip()
    )
    base_cand_artist = normalize_text(
        FEAT_DASH_PATTERN.sub("", VERSION_PATTERN.sub("", cand_artist)).strip()
    )

    # 1. Evaluasi Kesesuaian Artis (Termasuk perbandingan fonetik romaji)
    artist_match = 0.0
    for req_a in artist_variants:
        norm_a = normalize_text(req_a)
        if not norm_a:
            continue
        if norm_a == norm_cand_artist:
            artist_match = max(artist_match, 1.0)
        elif base_cand_artist and norm_a == base_cand_artist:
            artist_match = max(artist_match, 0.95)
        elif (norm_a in norm_cand_artist) or (base_cand_artist and norm_a in base_cand_artist):
            artist_match = max(artist_match, 0.9)
        elif norm_cand_artist in norm_a or (base_cand_artist and base_cand_artist in norm_a):
            artist_match = max(artist_match, 0.9)
        # Evaluasi kecocokan fonetik romaji via pykakasi
        elif to_romaji_clean(norm_a) == to_romaji_clean(norm_cand_artist):
            artist_match = max(artist_match, 0.95)

    # Tolak jika artis tidak cocok sama sekali
    if artist_match < 0.7:
        return 0.0, False

    # 2. Evaluasi Kesesuaian Judul (Termasuk perbandingan fonetik romaji)
    title_match = 0.0
    is_exact_version = False

    if norm_req_title == norm_cand_title:
        title_match = 1.0
        is_exact_version = True
    else:
        for t_var in title_variants:
            norm_v = normalize_text(t_var)
            if not norm_v:
                continue
            if norm_v == norm_cand_title:
                title_match = max(title_match, 0.95)
            elif base_cand_title and norm_v == base_cand_title:
                title_match = max(title_match, 0.9)
            elif norm_v in norm_cand_title or norm_cand_title in norm_v:
                title_match = max(title_match, 0.8)
            elif base_cand_title and (norm_v in base_cand_title or base_cand_title in norm_v):
                title_match = max(title_match, 0.8)
            elif to_romaji_clean(norm_v) == to_romaji_clean(norm_cand_title):
                title_match = max(title_match, 0.95)

    # Tolak jika judul sama sekali tidak relevan
    if title_match < 0.7:
        return 0.0, False

    # 3. Hitung Skor Total
    score = (title_match * 45.0) + (artist_match * 35.0)

    # Bonus pencocokan versi exact jika judul memiliki anotasi versi khusus
    if is_exact_version:
        score += 20.0

    # Sinyal pendukung Album (0 - 10)
    if req_album and cand_album:
        norm_req_alb = normalize_text(req_album)
        norm_cand_alb = normalize_text(cand_album)
        if norm_req_alb and (norm_req_alb == norm_cand_alb or norm_req_alb in norm_cand_alb):
            score += 10.0
        elif to_romaji_clean(norm_req_alb) == to_romaji_clean(norm_cand_alb):
            score += 10.0

    # Sinyal pendukung Durasi (0 - 10)
    if req_duration > 0 and cand_duration > 0:
        diff = abs(req_duration - cand_duration)
        if diff <= 2.5:
            score += 10.0
        elif diff <= 5.0:
            score += 7.0
        elif diff <= 15.0:
            score += 3.0
        elif diff > 45.0:
            score -= 10.0  # Penalti durasi yang sangat berbeda

    # Bonus lirik bertimestamp (15 poin) hanya jika judul & artis sudah cocok kuat
    if has_synced and title_match >= 0.8 and artist_match >= 0.8:
        score += 15.0

    return score, True


def pick_best_candidate(
    candidates: list[dict],
    req_title: str,
    title_variants: list[str],
    req_artist: str,
    artist_variants: list[str],
    req_album: str,
    req_duration: float,
) -> tuple[dict | None, float]:
    """Memilih kandidat terbaik berdasarkan penilaian komparatif."""
    best = None
    best_score = -1.0

    for cand in candidates:
        score, acceptable = score_candidate(
            cand,
            req_title,
            title_variants,
            req_artist,
            artist_variants,
            req_album,
            req_duration,
        )
        if acceptable and score > best_score:
            best_score = score
            best = cand

    return best, best_score


async def find_lyrics(
    title: str | None,
    artist: str | None,
    album: str = "",
    duration: int | float = 0,
) -> dict | None:
    """Cari lirik tersinkronisasi melalui LRCLIB.

    Alur:
    1. Coba pencarian exact via /api/get.
    2. Jika tidak ada hasil, buat variasi judul/artis yang dibatasi.
    3. Coba fallback via /api/search secara terurut dengan jeda sopan rate-limit.
    4. Evaluasi dan ranking kandidat secara aman (utamakan synced hanya jika kecocokan kuat).
    5. Jika masih belum ditemukan, lakukan metadata alias lookup untuk mendeteksi judul kanji/kana,
       lalu coba pencarian LRCLIB menggunakan alias tersebut.
    """
    clean_title = (title or "").strip()
    clean_artist = (artist or "").strip()
    clean_album = (album or "").strip()

    if not clean_title or not clean_artist:
        return None

    # Normalisasi durasi
    valid_duration = 0
    try:
        numeric_dur = round(float(duration))
        if 1 <= numeric_dur <= 3600:
            valid_duration = numeric_dur
    except (ValueError, TypeError):
        pass

    # A. Percobaan 1: Exact search via /api/get
    exact_params: dict[str, Any] = {
        "track_name": clean_title,
        "artist_name": clean_artist,
    }
    if clean_album:
        exact_params["album_name"] = clean_album
    if valid_duration > 0:
        exact_params["duration"] = valid_duration

    exact_res = await asyncio.to_thread(_fetch_lyrics, exact_params, "get")
    if exact_res and isinstance(exact_res, dict):
        if exact_res.get("syncedLyrics") or exact_res.get("plainLyrics"):
            return exact_res

    # B. Buat variasi judul dan artis yang dibatasi
    title_variants = get_title_variants(clean_title)
    artist_variants = get_artist_variants(clean_artist)

    # C. Bangun daftar query pencarian fallback yang terurut dan ter-deduplikasi
    search_queries = []

    # Query 1: Judul asli + artis asli
    search_queries.append(f"{clean_title} {clean_artist}")

    # Query 2: Variasi judul (tanpa anotasi versi/feat) + artis asli
    for t_var in title_variants[1:]:
        search_queries.append(f"{t_var} {clean_artist}")

    # Query 3: Variasi judul + variasi artis (tanpa feat)
    for a_var in artist_variants[1:]:
        for t_var in title_variants:
            search_queries.append(f"{t_var} {a_var}")

    # Query 4: Hanya judul jika query gabungan sebelumnya belum menemukan
    for t_var in title_variants:
        search_queries.append(t_var)

    # Deduplikasi query dengan mempertahankan urutan
    deduped_queries = []
    seen = set()
    for q in search_queries:
        q_norm = normalize_text(q)
        if q_norm and q_norm not in seen:
            seen.add(q_norm)
            deduped_queries.append(q.strip())

    # Batasi maksimal 4 query fallback untuk menjaga batas laju API
    deduped_queries = deduped_queries[:4]

    collected_candidates = []
    seen_ids = set()

    for idx, q in enumerate(deduped_queries):
        if idx > 0:
            # Jeda singkat antar-pencarian fallback untuk menghormati rate limit
            await asyncio.sleep(0.3)

        candidates = await asyncio.to_thread(
            _fetch_lyrics,
            {"q": q},
            "search",
        )

        if not candidates:
            continue

        if isinstance(candidates, dict):
            candidates = [candidates]

        for cand in candidates:
            if not isinstance(cand, dict):
                continue
            cand_id = cand.get("id") or (cand.get("trackName"), cand.get("artistName"))
            if cand_id not in seen_ids:
                seen_ids.add(cand_id)
                collected_candidates.append(cand)

        # Cek apakah sudah ada kandidat dengan skor tinggi dan syncedLyrics
        best_early, early_score = pick_best_candidate(
            collected_candidates,
            clean_title,
            title_variants,
            clean_artist,
            artist_variants,
            clean_album,
            valid_duration,
        )
        if best_early and early_score >= 85 and best_early.get("syncedLyrics"):
            return best_early

    # D. Evaluasi dan pilih kandidat terbaik dari pencarian standar
    best_candidate, best_score = pick_best_candidate(
        collected_candidates,
        clean_title,
        title_variants,
        clean_artist,
        artist_variants,
        clean_album,
        valid_duration,
    )

    if best_candidate and best_score >= 70:
        return best_candidate

    # E. Stage 9.6: Metadata Alias Resolver (jika lirik belum ditemukan)
    # Mencari alias kanji/kana resmi dari provider metadata publik
    aliases = await asyncio.to_thread(
        fetch_metadata_aliases,
        clean_title,
        clean_artist,
        clean_album,
        valid_duration,
    )

    if aliases:
        alias_candidates = []
        extended_title_variants = list(title_variants)
        extended_artist_variants = list(artist_variants)

        for alias_title, alias_artist in aliases[:2]:
            if alias_title not in extended_title_variants:
                extended_title_variants.append(alias_title)
            if alias_artist not in extended_artist_variants:
                extended_artist_variants.append(alias_artist)

            # Coba exact get dengan alias
            alias_get_params: dict[str, Any] = {
                "track_name": alias_title,
                "artist_name": alias_artist,
            }
            if valid_duration > 0:
                alias_get_params["duration"] = valid_duration

            alias_exact = await asyncio.to_thread(_fetch_lyrics, alias_get_params, "get")
            if alias_exact and isinstance(alias_exact, dict) and alias_exact.get("syncedLyrics"):
                score, acc = score_candidate(
                    alias_exact,
                    clean_title,
                    extended_title_variants,
                    clean_artist,
                    extended_artist_variants,
                    clean_album,
                    valid_duration,
                )
                if acc and score >= 75:
                    return alias_exact

            # Coba search dengan alias
            await asyncio.sleep(0.3)
            alias_search_res = await asyncio.to_thread(
                _fetch_lyrics,
                {"q": f"{alias_title} {alias_artist}"},
                "search",
            )
            if alias_search_res:
                if isinstance(alias_search_res, dict):
                    alias_search_res = [alias_search_res]
                for cand in alias_search_res:
                    if isinstance(cand, dict):
                        cand_id = cand.get("id") or (cand.get("trackName"), cand.get("artistName"))
                        if cand_id not in seen_ids:
                            seen_ids.add(cand_id)
                            alias_candidates.append(cand)

        # Evaluasi kandidat hasil pencarian alias
        best_alias_cand, alias_score = pick_best_candidate(
            alias_candidates,
            clean_title,
            extended_title_variants,
            clean_artist,
            extended_artist_variants,
            clean_album,
            valid_duration,
        )

        if best_alias_cand and alias_score >= 70:
            return best_alias_cand

    if best_candidate:
        return best_candidate

    # F. Stage 9.7: Multi-Source Fallback (lyrics.ovh)
    # Dijalankan hanya jika seluruh pencarian LRCLIB (exact, smart, alias) tidak menghasilkan lirik valid
    fallback_res = await asyncio.to_thread(
        fetch_lyrics_ovh,
        clean_title,
        clean_artist,
        clean_album,
        valid_duration,
    )
    if fallback_res:
        return fallback_res

    return None


def get_lyrics(
    title: str | None,
    artist: str | None,
    album: str = "",
    duration: int | float = 0,
) -> dict | None:
    """Antarmuka sinkron untuk pengujian sederhana."""
    return asyncio.run(
        find_lyrics(title, artist, album, duration)
    )
