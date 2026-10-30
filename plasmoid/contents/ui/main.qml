import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import Qt5Compat.GraphicalEffects
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.private.mpris as Mpris

PlasmoidItem {
    id: root
    clip: false

    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    implicitWidth: 640
    implicitHeight: 380
    Layout.minimumWidth: 320
    Layout.minimumHeight: 180

    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: i18n("Refresh Lyrics")
            icon.name: "view-refresh"
            onTriggered: root.refreshLyrics(true)
        }
    ]

    // =========================================================================
    // KONFIGURASI TEMA & PENGATURAN DARI KCONFIGXT (KDE PLASMA)
    // =========================================================================
    readonly property var cfg: Plasmoid.configuration

    // 1. Visibilitas Komponen (Show / Hide)
    readonly property bool showTitle: (cfg && typeof cfg.showTitle !== "undefined") ? (cfg.showTitle === true || cfg.showTitle === "true" || cfg.showTitle === 1) : true
    readonly property bool showArtist: (cfg && typeof cfg.showArtist !== "undefined") ? (cfg.showArtist === true || cfg.showArtist === "true" || cfg.showArtist === 1) : true
    readonly property bool showLyrics: (cfg && typeof cfg.showLyrics !== "undefined") ? (cfg.showLyrics === true || cfg.showLyrics === "true" || cfg.showLyrics === 1) : true
    readonly property bool showRomaji: (cfg && typeof cfg.showRomaji !== "undefined") ? (cfg.showRomaji === true || cfg.showRomaji === "true" || cfg.showRomaji === 1) : true
    readonly property bool showTimer: (cfg && typeof cfg.showTimer !== "undefined") ? (cfg.showTimer === true || cfg.showTimer === "true" || cfg.showTimer === 1) : true

    // 2. Format & Spacing Layout
    readonly property string textAlignment: (cfg && typeof cfg.textAlignment !== "undefined" && cfg.textAlignment) ? cfg.textAlignment : "left"
    readonly property int qmlTextAlignment: root.textAlignment === "center" ? Text.AlignHCenter : (root.textAlignment === "right" ? Text.AlignRight : Text.AlignLeft)
    readonly property int maxWordsPerLine: (cfg && typeof cfg.maxWordsPerLine !== "undefined") ? Number(cfg.maxWordsPerLine) : 7
    readonly property real lyricLineSpacing: (cfg && typeof cfg.lyricLineSpacing !== "undefined") ? Number(cfg.lyricLineSpacing) : 1.25
    readonly property int lyricItemSpacing: (cfg && typeof cfg.lyricItemSpacing !== "undefined") ? Number(cfg.lyricItemSpacing) : 8
    readonly property int bgTopOffset: (cfg && typeof cfg.bgTopOffset !== "undefined") ? Math.max(0, Number(cfg.bgTopOffset)) : 0
    readonly property int bgBottomOffset: (cfg && typeof cfg.bgBottomOffset !== "undefined") ? Math.max(0, Number(cfg.bgBottomOffset)) : 0
    readonly property int titleTopMargin: (cfg && typeof cfg.titleTopMargin !== "undefined") ? Number(cfg.titleTopMargin) : 36
    readonly property int timerBottomMargin: (cfg && typeof cfg.timerBottomMargin !== "undefined") ? Number(cfg.timerBottomMargin) : 36

    // 3. Ukuran Font (px)
    readonly property int titleFontSize: (cfg && typeof cfg.titleFontSize !== "undefined") ? Number(cfg.titleFontSize) : 28
    readonly property int artistFontSize: (cfg && typeof cfg.artistFontSize !== "undefined") ? Number(cfg.artistFontSize) : 16
    readonly property int lyricFontSize: (cfg && typeof cfg.lyricFontSize !== "undefined") ? Number(cfg.lyricFontSize) : 26
    readonly property int romajiFontSize: (cfg && typeof cfg.romajiFontSize !== "undefined") ? Number(cfg.romajiFontSize) : 18
    readonly property int timerFontSize: (cfg && typeof cfg.timerFontSize !== "undefined") ? Number(cfg.timerFontSize) : 16

    // 4. Pengaturan Background & Posisi Puncak Gradasi
    readonly property int bgWidthPercent: (cfg && typeof cfg.bgWidthPercent !== "undefined") ? Number(cfg.bgWidthPercent) : 82
    readonly property color bgColor: (cfg && typeof cfg.bgColor !== "undefined") ? cfg.bgColor : "#0a0d12"
    readonly property real bgOpacity: (cfg && typeof cfg.bgOpacity !== "undefined") ? Math.max(0.0, Math.min(1.0, Number(cfg.bgOpacity))) : 0.88
    readonly property real bgFadeStart: (cfg && typeof cfg.bgFadeStart !== "undefined") ? Math.max(0.0, Math.min(1.0, Number(cfg.bgFadeStart))) : 0.25
    readonly property real bgPeakPosition: (cfg && typeof cfg.bgPeakPosition !== "undefined") ? Math.max(0.0, Math.min(1.0, Number(cfg.bgPeakPosition))) : 0.00

    // 5. Pengaturan Font Family
    readonly property bool useUnifiedFont: (cfg && typeof cfg.useUnifiedFont !== "undefined") ? (cfg.useUnifiedFont === true || cfg.useUnifiedFont === "true") : false
    readonly property string unifiedFontFamily: (cfg && typeof cfg.unifiedFontFamily !== "undefined") ? cfg.unifiedFontFamily : "Noto Sans"

    readonly property string titleFontFamily: useUnifiedFont ? unifiedFontFamily : ((cfg && cfg.titleFontFamily) ? cfg.titleFontFamily : "Noto Sans")
    readonly property string artistFontFamily: useUnifiedFont ? unifiedFontFamily : ((cfg && cfg.artistFontFamily) ? cfg.artistFontFamily : "Noto Sans")
    readonly property string lyricFontFamily: useUnifiedFont ? unifiedFontFamily : ((cfg && cfg.lyricFontFamily) ? cfg.lyricFontFamily : "Noto Sans")
    readonly property string romajiFontFamily: useUnifiedFont ? unifiedFontFamily : ((cfg && cfg.romajiFontFamily) ? cfg.romajiFontFamily : "Noto Sans")
    readonly property string timerFontFamily: useUnifiedFont ? unifiedFontFamily : ((cfg && cfg.timerFontFamily) ? cfg.timerFontFamily : "Noto Sans")

    // =========================================================================
    // NATIVE MPRIS INTEGRATION (KDE PLASMA 6) & FALLBACK
    // =========================================================================
    Mpris.Mpris2Model {
        id: mprisModel
    }

    readonly property var activePlayer: mprisModel.currentPlayer
    readonly property bool isPlaying: activePlayer ? (activePlayer.playbackStatus === Mpris.PlaybackStatus.Playing) : false
    readonly property bool isPaused: activePlayer ? (activePlayer.playbackStatus === Mpris.PlaybackStatus.Paused) : false

    // Opsional fallback jika dijalankan di harness dengan bridge PySide
    readonly property var b: (typeof bridge !== "undefined" && bridge) ? bridge : null

    // Cache metadata lagu untuk mencegah widget hilang saat jeda/transisi/buffering browser (YouTube Music)
    property string cachedTitle: ""
    property string cachedArtist: ""
    property string cachedAlbum: ""
    property real cachedDuration: 0.0

    readonly property string title: b ? b.title : ((activePlayer && activePlayer.track && activePlayer.track.length > 0) ? activePlayer.track : cachedTitle)
    readonly property string artist: b ? b.artist : ((activePlayer && activePlayer.artist && activePlayer.artist.length > 0) ? activePlayer.artist : cachedArtist)
    readonly property string album: b ? b.album : ((activePlayer && activePlayer.album && activePlayer.album.length > 0) ? activePlayer.album : cachedAlbum)
    readonly property real duration: b ? b.duration : ((activePlayer && activePlayer.length > 0) ? (activePlayer.length / 1000000.0) : cachedDuration)

    // Logika visibilitas widget dengan tenggat 30 detik & pause tetap aktif
    property bool isWidgetVisible: false
    property bool hasEverPlayed: false

    readonly property bool hasPlayer: b ? b.hasPlayer : isWidgetVisible

    onActivePlayerChanged: handlePlaybackState()
    onIsPlayingChanged: handlePlaybackState()
    onIsPausedChanged: handlePlaybackState()

    Timer {
        id: hideGraceTimer
        interval: 30000 // 30 detik grace period
        repeat: false
        onTriggered: {
            if (!root.isPlaying && !root.isPaused) {
                root.isWidgetVisible = false;
                root.cachedTitle = "";
                root.cachedArtist = "";
                root.cachedAlbum = "";
                root.cachedDuration = 0.0;
                root.lastTrackKey = "";
                root.parsedLyrics = [];
                root.currentLyricIndex = -1;
                root.lyricChanged("", "", false, false, "", false);
                root.formattedTime = "";
            }
        }
    }

    function handlePlaybackState() {
        if (root.b) {
            root.isWidgetVisible = root.b.hasPlayer;
            return;
        }

        if (root.isPlaying) {
            root.hasEverPlayed = true;
            root.isWidgetVisible = true;
            if (hideGraceTimer.running) {
                hideGraceTimer.stop();
            }
        } else if (root.isPaused) {
            // Lagu di-pause: widget tetap tampil tanpa batas waktu
            if (root.hasEverPlayed || root.title.length > 0) {
                root.isWidgetVisible = true;
                if (hideGraceTimer.running) {
                    hideGraceTimer.stop();
                }
            }
        } else {
            // Lagu berhenti, berganti trek di browser (YouTube Music), atau player tertutup
            if (root.isWidgetVisible && root.hasEverPlayed) {
                if (!hideGraceTimer.running) {
                    hideGraceTimer.start();
                }
            }
        }
    }

    // State lirik & waktu yang aktif
    property string activeLead: b ? b.activeLead : ""
    property string activeBacking: b ? b.activeBacking : ""
    property bool hasBacking: b ? b.hasBacking : false
    property bool isBackingOnly: b ? b.isBackingOnly : false
    property string activeRomaji: b ? b.activeRomaji : ""
    property bool hasRomaji: b ? b.hasRomaji : false
    property string formattedTime: b ? b.formattedTime : ""

    signal lyricChanged(string lead, string backing, bool hasBacking, bool isBackingOnly, string romaji, bool hasRomaji)

    property real currentPositionSeconds: 0.0
    property var parsedLyrics: []
    property int currentLyricIndex: -1
    property string lastTrackKey: ""
    property var lyricsCache: ({})
    property bool isFetchingLyrics: false

    readonly property real baseLeftPadding: Math.max(36, Math.round(width * 0.045))
    readonly property real baseTopPadding: Math.max(36, Math.round(height * 0.065))

    // =========================================================================
    // HELPER FUNCTIONS: GRADASI HALUS BERDASARKAN POSISI PEAK (STRONG)
    // =========================================================================

    // Menghitung opacity gradasi di posisi tertentu (0.00 s/d 1.00)
    function getGradientOpacity(pos) {
        if (root.bgOpacity <= 0) return 0.0;
        var peak = Math.max(0.0, Math.min(1.0, root.bgPeakPosition));
        var dist = Math.abs(pos - peak);

        var maxSpan = Math.max(peak, 1.0 - peak);
        if (maxSpan <= 0.001) return root.bgOpacity;

        // Zona plateau di sekitar peak
        var plateau = Math.max(0.0, root.bgFadeStart * 0.40);
        if (dist <= plateau) {
            return root.bgOpacity;
        }

        var remainingSpan = maxSpan - plateau;
        if (remainingSpan <= 0.001) return 0.0;

        var t = Math.min(1.0, (dist - plateau) / remainingSpan);
        var factor = 0.5 * (1.0 + Math.cos(t * Math.PI));
        return Math.max(0.0, root.bgOpacity * factor);
    }

    // Pemecah kalimat panjang berdasarkan konfigurasi maxWordsPerLine
    function splitLongSentence(str) {
        if (!str) return "";
        var maxWords = root.maxWordsPerLine;
        if (maxWords <= 0) return str;
        var lines = str.split("\n");
        return lines.map(function(line) {
            var trimmed = line.trim();
            if (!trimmed) return "";
            var words = trimmed.split(/\s+/);
            if (words.length <= maxWords) return trimmed;
            var chunks = [];
            for (var i = 0; i < words.length; i += maxWords) {
                chunks.push(words.slice(i, i + maxWords).join(" "));
            }
            return chunks.join("\n");
        }).join("\n");
    }

    // Format waktu MM:SS (atau HH:MM:SS jika jam), tanpa milidetik
    function formatTime(seconds) {
        if (isNaN(seconds) || seconds < 0) return "00:00";
        var totalSec = Math.floor(seconds);
        var hrs = Math.floor(totalSec / 3600);
        var mins = Math.floor((totalSec % 3600) / 60);
        var secs = totalSec % 60;

        var minStr = (mins < 10 ? "0" : "") + mins;
        var secStr = (secs < 10 ? "0" : "") + secs;

        if (hrs > 0 || (root.duration >= 3600)) {
            var hrStr = (hrs < 10 ? "0" : "") + hrs;
            return hrStr + ":" + minStr + ":" + secStr;
        }
        return minStr + ":" + secStr;
    }

    // Deteksi karakter Kana Jepang (Hiragana & Katakana)
    function containsJapanese(text) {
        return /[\u3040-\u309F\u30A0-\u30FF]/.test(text);
    }

    // Konversi Kana Jepang ke Romaji Hepburn murni
    function kanaToRomaji(text) {
        if (!text) return "";
        var kanaMap = {
            "あ":"a","い":"i","う":"u","え":"e","お":"o",
            "か":"ka","き":"ki","く":"ku","け":"ke","こ":"ko",
            "さ":"sa","し":"shi","す":"su","せ":"se","そ":"so",
            "た":"ta","ち":"chi","つ":"tsu","て":"te","と":"to",
            "な":"na","に":"ni","ぬ":"nu","ね":"ne","の":"no",
            "は":"ha","ひ":"hi","ふ":"fu","へ":"he","ほ":"ho",
            "ま":"ma","み":"mi","む":"mu","め":"me","も":"mo",
            "や":"ya","ゆ":"yu","よ":"yo",
            "ら":"ra","り":"ri","る":"ru","れ":"re","ろ":"ro",
            "わ":"wa","を":"o","ん":"n",
            "が":"ga","ぎ":"gi","ぐ":"gu","げ":"ge","ご":"go",
            "ざ":"za","じ":"ji","ず":"zu","ぜ":"ze","ぞ":"zo",
            "だ":"da","ぢ":"ji","づ":"zu","で":"de","ど":"do",
            "ば":"ba","び":"bi","ぶ":"bu","べ":"be","ぼ":"bo",
            "ぱ":"pa","ぴ":"pi","ぷ":"pu","ぺ":"pe","ぽ":"po",
            "きゃ":"kya","きゅ":"kyu","きょ":"kyo",
            "しゃ":"sha","しゅ":"shu","しょ":"sho",
            "ちゃ":"cha","ちゅ":"chu","ちょ":"cho",
            "にゃ":"nya","にゅ":"nyu","にょ":"nyo",
            "ひゃ":"hya","ひゅ":"hyu","ひょ":"hyo",
            "みゃ":"mya","みゅ":"myu","みょ":"myo",
            "りゃ":"rya","りゅ":"ryu","りょ":"ryo",
            "ぎゃ":"gya","ぎゅ":"gyu","ぎょ":"gyo",
            "じゃ":"ja","じゅ":"ju","じょ":"jo",
            "びゃ":"bya","びゅ":"byu","びょ":"byo",
            "ぴゃ":"pya","ぴゅ":"pyu","ぴょ":"pyo",
            // Katakana
            "ア":"a","イ":"i","ウ":"u","エ":"e","オ":"o",
            "カ":"ka","キ":"ki","ク":"ku","ケ":"ke","コ":"ko",
            "サ":"sa","シ":"shi","ス":"su","セ":"se","ソ":"so",
            "タ":"ta","チ":"chi","ツ":"tsu","テ":"te","ト":"to",
            "ナ":"na","ニ":"ni","ヌ":"nu","ネ":"ne","ノ":"no",
            "ハ":"ha","ヒ":"hi","フ":"fu","ヘ":"he","ホ":"ho",
            "マ":"ma","ミ":"mi","ム":"mu","メ":"me","モ":"mo",
            "ヤ":"ya","ユ":"yu","ヨ":"yo",
            "ラ":"ra","リ":"ri","ル":"ru","レ":"re","ロ":"ro",
            "ワ":"wa","ヲ":"o","ン":"n",
            "ガ":"ga","ギ":"gi","グ":"gu","ゲ":"ge","ご":"go",
            "ザ":"za","ジ":"ji","ズ":"zu","ゼ":"ze","ぞ":"zo",
            "ダ":"da","ヂ":"ji","ヅ":"zu","デ":"de","ド":"do",
            "バ":"ba","ビ":"bi","ブ":"bu","べ":"be","ぼ":"bo",
            "パ":"pa","ピ":"pi","プ":"pu","ペ":"pe","ぽ":"po"
        };

        var result = "";
        for (var i = 0; i < text.length; i++) {
            if (i + 1 < text.length) {
                var doubleChar = text.substr(i, 2);
                if (kanaMap[doubleChar]) {
                    result += kanaMap[doubleChar] + " ";
                    i++;
                    continue;
                }
            }
            var singleChar = text[i];
            if (kanaMap[singleChar]) {
                result += kanaMap[singleChar] + " ";
            } else {
                result += singleChar;
            }
        }
        var cleaned = result.replace(/\s+/g, " ").trim();
        return cleaned ? (cleaned.charAt(0).toUpperCase() + cleaned.slice(1)) : cleaned;
    }

    // Pemisah lead & backing vocals (tanda kurung)
    function splitVocals(text) {
        if (!text) {
            return { lead: "", backing: "", hasBacking: false, isBackingOnly: false };
        }
        var raw = text.trim();
        var parenPattern = /[\(\uff08]+([^\(\)\uff08\uff09]+)[\)\uff09]+/;
        var match = raw.match(parenPattern);

        if (!match) {
            return { lead: raw, backing: "", hasBacking: false, isBackingOnly: false };
        }

        var backingText = match[1].trim();
        var leadText = raw.replace(/[\(\uff08]+[^\(\)\uff08\uff09]+[\)\uff09]+/g, "").replace(/\s+/g, " ").trim();

        var hasBacking = backingText.length > 0;
        var isBackingOnly = hasBacking && (leadText.length === 0);

        return {
            lead: leadText,
            backing: backingText,
            hasBacking: hasBacking,
            isBackingOnly: isBackingOnly
        };
    }

    // Parser lirik format LRC
    function parseLrc(content) {
        if (!content) return [];
        var lines = content.split(/\r?\n/);
        var entries = [];
        var timestampRegex = /\[(\d{2}):(\d{2})(?:\.(\d{1,3}))?\]/g;

        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (!line || /^\[[a-zA-Z]{1,10}:/.test(line)) continue;

            var timestamps = [];
            var match;
            while ((match = timestampRegex.exec(line)) !== null) {
                var mins = parseInt(match[1], 10);
                var secs = parseInt(match[2], 10);
                var fracStr = (match[3] || "0");
                while (fracStr.length < 3) fracStr += "0";
                var ms = parseInt(fracStr.substr(0, 3), 10);
                timestamps.push(mins * 60 + secs + (ms / 1000.0));
            }

            var text = line.replace(/\[\d{2}:\d{2}(?:\.\d{1,3})?\]/g, "").trim();
            if (!text || timestamps.length === 0) continue;

            // Abaikan baris metadata/kredit yang bukan lirik nyanyian
            if (/^(作词|作曲|编曲|制作人|监制|混音|吉他|贝斯|鼓|键盘|录音|和声|母带|发行|lrc\s*by|lyrics\s*by|music\s*by|composed\s*by|produced\s*by)\s*[:：]/i.test(text)) {
                continue;
            }

            var vocals = splitVocals(text);
            var leadRomaji = containsJapanese(vocals.lead) ? kanaToRomaji(vocals.lead) : "";
            var backingRomaji = containsJapanese(vocals.backing) ? kanaToRomaji(vocals.backing) : "";
            var mainRomaji = vocals.isBackingOnly ? backingRomaji : (leadRomaji || (containsJapanese(text) ? kanaToRomaji(text) : ""));

            for (var t = 0; t < timestamps.length; t++) {
                entries.push({
                    timestamp: timestamps[t],
                    lead: vocals.lead,
                    backing: vocals.backing,
                    hasBacking: vocals.hasBacking,
                    isBackingOnly: vocals.isBackingOnly,
                    romaji: mainRomaji,
                    hasRomaji: mainRomaji.length > 0,
                    original: text
                });
            }
        }

        entries.sort(function(a, b) { return a.timestamp - b.timestamp; });
        return entries;
    }

    // Pembersihan judul & artis dari label video YouTube / fitur tambahan
    function sanitizeTrackTitle(raw) {
        if (!raw) return "";
        var s = raw;
        // Hapus label video seperti (Official Music Video), [MV], (Lyric Video), dll.
        s = s.replace(/[\(\[](?:official\s*(?:music\s*)?video|official\s*audio|music\s*video|lyric\s*video|lyrics|audio|mv|visualizer|prod\.?|clip\s*officiel)[^\)\]]*[\)\]]/gi, "");
        // Hapus (feat. ...) atau (ft. ...)
        s = s.replace(/[\(\[](?:feat\.?|ft\.?|featuring)[^\)\]]*[\)\]]/gi, "");
        // Hapus akhiran "- Official Video" atau "| MV"
        s = s.replace(/\s*[\-\|]\s*(?:official\s*(?:music\s*)?video|official\s*audio|music\s*video|mv|visualizer).*$/gi, "");
        return s.replace(/\s+/g, " ").trim();
    }

    // Fungsi refresh lirik (dapat dipanggil dari tombol atau menu klik kanan)
    function refreshLyrics(clearAll) {
        if (clearAll) {
            lyricsCache = ({});
        }
        var curTitle = root.title;
        var curArtist = root.artist;
        var curAlbum = root.album;
        var curDuration = root.duration;

        var cleanT = sanitizeTrackTitle(curTitle);
        var cleanA = sanitizeTrackTitle(curArtist);
        var k = (cleanT + "---" + cleanA).toLowerCase();
        delete lyricsCache[k];

        lastTrackKey = "";
        parsedLyrics = [];
        currentLyricIndex = -1;
        lyricChanged("", "", false, false, "", false);

        if (curTitle.length > 0) {
            fetchLyrics(curTitle, curArtist, curAlbum, curDuration);
        }
    }

    function applyLyricData(data, cacheKey) {
        if (!data) return false;
        if (data.syncedLyrics && data.syncedLyrics.trim().length > 0) {
            var parsed = parseLrc(data.syncedLyrics);
            if (parsed.length > 0) {
                lyricsCache[cacheKey] = parsed;
                parsedLyrics = parsed;
                currentLyricIndex = -1;
                return true;
            }
        } else if (data.plainLyrics && data.plainLyrics.trim().length > 0) {
            var plain = [{
                timestamp: 0.0,
                lead: data.plainLyrics.split("\n")[0] || "",
                backing: "",
                hasBacking: false,
                isBackingOnly: false,
                romaji: "",
                hasRomaji: false,
                original: data.plainLyrics
            }];
            lyricsCache[cacheKey] = plain;
            parsedLyrics = plain;
            currentLyricIndex = -1;
            return true;
        }
        return false;
    }

    // =========================================================================
    // MULTI-SOURCE LYRICS ENGINE: LRCLIB -> NETEASE CLOUD MUSIC -> KUGOU MUSIC
    // =========================================================================

    function fetchLyrics(trackTitle, trackArtist, trackAlbum, trackDuration) {
        if (!trackTitle) return;
        var cleanTitle = sanitizeTrackTitle(trackTitle);
        var cleanArtist = sanitizeTrackTitle(trackArtist);

        // Jika artis kosong atau generik (mis. "YouTube") dan judul format "Artis - Lagu"
        if ((!cleanArtist || cleanArtist.toLowerCase() === "youtube" || cleanArtist.toLowerCase() === "unknown") && cleanTitle.indexOf(" - ") !== -1) {
            var dashParts = cleanTitle.split(/\s+-\s+/);
            if (dashParts.length >= 2) {
                cleanArtist = dashParts[0].trim();
                cleanTitle = dashParts.slice(1).join(" - ").trim();
            }
        }

        var cacheKey = (cleanTitle + "---" + cleanArtist).toLowerCase();

        if (lyricsCache[cacheKey]) {
            parsedLyrics = lyricsCache[cacheKey];
            currentLyricIndex = -1;
            return;
        }

        isFetchingLyrics = true;

        // Mulai rantai multi-sumber: 1. LRCLIB -> 2. NetEase -> 3. KuGou
        fetchFromLrclib(cleanTitle, cleanArtist, trackDuration, cacheKey);
    }

    // Sumber 1: LRCLIB (Database Komunitas Terbuka)
    function fetchFromLrclib(cleanTitle, cleanArtist, trackDuration, cacheKey) {
        var queryParams = "track_name=" + encodeURIComponent(cleanTitle) + "&artist_name=" + encodeURIComponent(cleanArtist);
        if (trackDuration > 0) queryParams += "&duration=" + Math.round(trackDuration);
        var url1 = "https://lrclib.net/api/get?" + queryParams;

        var xhr1 = new XMLHttpRequest();
        xhr1.open("GET", url1, true);
        xhr1.setRequestHeader("User-Agent", "LyricWidget-KDE/1.0");

        xhr1.onreadystatechange = function() {
            if (xhr1.readyState === XMLHttpRequest.DONE) {
                if (xhr1.status === 200) {
                    try {
                        var data = JSON.parse(xhr1.responseText);
                        if (applyLyricData(data, cacheKey)) {
                            root.isFetchingLyrics = false;
                            return;
                        }
                    } catch (e) {}
                }

                // Coba search LRCLIB jika get spesifik gagal
                var q = cleanTitle + (cleanArtist ? (" " + cleanArtist) : "");
                var urlSearch = "https://lrclib.net/api/search?q=" + encodeURIComponent(q);
                var xhrSearch = new XMLHttpRequest();
                xhrSearch.open("GET", urlSearch, true);
                xhrSearch.setRequestHeader("User-Agent", "LyricWidget-KDE/1.0");

                xhrSearch.onreadystatechange = function() {
                    if (xhrSearch.readyState === XMLHttpRequest.DONE) {
                        if (xhrSearch.status === 200) {
                            try {
                                var list = JSON.parse(xhrSearch.responseText);
                                if (Array.isArray(list) && list.length > 0) {
                                    for (var i = 0; i < list.length; i++) {
                                        if (applyLyricData(list[i], cacheKey)) {
                                            root.isFetchingLyrics = false;
                                            return;
                                        }
                                    }
                                }
                            } catch (e) {}
                        }

                        // Jika LRCLIB tidak menemukan atau error 503, fallback ke Sumber 2: NetEase
                        fetchFromNetease(cleanTitle, cleanArtist, trackDuration, cacheKey);
                    }
                };
                xhrSearch.send();
            }
        };

        xhr1.send();
    }

    // Sumber 2: NetEase Cloud Music (Basis data raksasa global & Asia, gratis & ringan)
    function fetchFromNetease(cleanTitle, cleanArtist, trackDuration, cacheKey) {
        var q = cleanTitle + (cleanArtist ? (" " + cleanArtist) : "");
        var searchUrl = "http://music.163.com/api/search/get/";
        var postData = "s=" + encodeURIComponent(q) + "&type=1&offset=0&total=true&limit=3";

        var xhrSearch = new XMLHttpRequest();
        xhrSearch.open("POST", searchUrl, true);
        xhrSearch.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        xhrSearch.setRequestHeader("User-Agent", "Mozilla/5.0 (X11; Linux x86_64)");
        xhrSearch.setRequestHeader("Referer", "http://music.163.com/");

        xhrSearch.onreadystatechange = function() {
            if (xhrSearch.readyState === XMLHttpRequest.DONE) {
                if (xhrSearch.status === 200) {
                    try {
                        var res = JSON.parse(xhrSearch.responseText);
                        var songs = res && res.result && res.result.songs;
                        if (Array.isArray(songs) && songs.length > 0) {
                            var songId = songs[0].id;
                            var lyricUrl = "http://music.163.com/api/song/lyric?os=pc&id=" + songId + "&lv=-1&kv=-1&tv=-1";
                            var xhrLyric = new XMLHttpRequest();
                            xhrLyric.open("GET", lyricUrl, true);
                            xhrLyric.setRequestHeader("User-Agent", "Mozilla/5.0 (X11; Linux x86_64)");
                            xhrLyric.setRequestHeader("Referer", "http://music.163.com/");

                            xhrLyric.onreadystatechange = function() {
                                if (xhrLyric.readyState === XMLHttpRequest.DONE) {
                                    if (xhrLyric.status === 200) {
                                        try {
                                            var ldata = JSON.parse(xhrLyric.responseText);
                                            var rawLrc = ldata && ldata.lrc && ldata.lrc.lyric;
                                            if (rawLrc && rawLrc.trim().length > 0) {
                                                var parsed = parseLrc(rawLrc);
                                                if (parsed.length > 0) {
                                                    lyricsCache[cacheKey] = parsed;
                                                    parsedLyrics = parsed;
                                                    currentLyricIndex = -1;
                                                    root.isFetchingLyrics = false;
                                                    return;
                                                }
                                            }
                                        } catch (e) {}
                                    }
                                    // Jika NetEase tidak ada lirik, fallback ke Sumber 3: KuGou
                                    fetchFromKugou(cleanTitle, cleanArtist, trackDuration, cacheKey);
                                }
                            };
                            xhrLyric.send();
                            return;
                        }
                    } catch (e) {}
                }
                // Jika pencarian NetEase gagal, coba Sumber 3: KuGou
                fetchFromKugou(cleanTitle, cleanArtist, trackDuration, cacheKey);
            }
        };

        xhrSearch.send(postData);
    }

    // Sumber 3: KuGou Music (Basis data cadangan dengan format lrc sinkron)
    function fetchFromKugou(cleanTitle, cleanArtist, trackDuration, cacheKey) {
        var q = (cleanArtist ? (cleanArtist + " - ") : "") + cleanTitle;
        var durMs = trackDuration > 0 ? Math.round(trackDuration * 1000) : 0;
        var searchUrl = "http://lyrics.kugou.com/search?ver=1&man=yes&client=pc&keyword=" + encodeURIComponent(q) + "&duration=" + durMs + "&hash=";

        var xhrSearch = new XMLHttpRequest();
        xhrSearch.open("GET", searchUrl, true);
        xhrSearch.setRequestHeader("User-Agent", "Mozilla/5.0");

        xhrSearch.onreadystatechange = function() {
            if (xhrSearch.readyState === XMLHttpRequest.DONE) {
                if (xhrSearch.status === 200) {
                    try {
                        var res = JSON.parse(xhrSearch.responseText);
                        var candidates = res && res.candidates;
                        if (Array.isArray(candidates) && candidates.length > 0) {
                            var cand = candidates[0];
                            var dlUrl = "http://lyrics.kugou.com/download?ver=1&client=pc&id=" + cand.id + "&accesskey=" + cand.accesskey + "&fmt=lrc&charset=utf8";
                            var xhrDl = new XMLHttpRequest();
                            xhrDl.open("GET", dlUrl, true);
                            xhrDl.setRequestHeader("User-Agent", "Mozilla/5.0");

                            xhrDl.onreadystatechange = function() {
                                if (xhrDl.readyState === XMLHttpRequest.DONE) {
                                    root.isFetchingLyrics = false;
                                    if (xhrDl.status === 200) {
                                        try {
                                            var ddata = JSON.parse(xhrDl.responseText);
                                            var b64Content = ddata && ddata.content;
                                            if (b64Content) {
                                                var rawLrc = "";
                                                try {
                                                    rawLrc = decodeURIComponent(escape(Qt.atob(b64Content)));
                                                } catch (ex) {
                                                    rawLrc = Qt.atob(b64Content);
                                                }
                                                var parsed = parseLrc(rawLrc);
                                                if (parsed.length > 0) {
                                                    lyricsCache[cacheKey] = parsed;
                                                    parsedLyrics = parsed;
                                                    currentLyricIndex = -1;
                                                    return;
                                                }
                                            }
                                        } catch (e) {}
                                    }
                                }
                            };
                            xhrDl.send();
                            return;
                        }
                    } catch (e) {}
                }
                root.isFetchingLyrics = false;
            }
        };

        xhrSearch.send();
    }

    // =========================================================================
    // TIMER SINKRONISASI REALTIME (MPRIS & LIRIK)
    // =========================================================================
    Timer {
        id: syncTimer
        interval: 35
        running: true
        repeat: true
        onTriggered: {
            if (root.b) {
                // Jika terhubung ke bridge PySide, biarkan sinyal bridge yang mengatur
                return;
            }

            // Perbarui cache metadata saat active player memiliki info lagu
            if (root.activePlayer && root.activePlayer.track && root.activePlayer.track.length > 0) {
                root.cachedTitle = root.activePlayer.track;
                root.cachedArtist = root.activePlayer.artist || "";
                root.cachedAlbum = root.activePlayer.album || "";
                root.cachedDuration = (root.activePlayer.length || 0) / 1000000.0;
            }

            root.handlePlaybackState();

            if (!root.activePlayer) {
                return;
            }

            // Perbarui posisi playback dari modul MPRIS Plasma
            if (typeof root.activePlayer.updatePosition === "function") {
                root.activePlayer.updatePosition();
            }

            var rawPos = root.activePlayer.position || 0;
            root.currentPositionSeconds = Math.max(0.0, rawPos / 1000000.0);
            root.formattedTime = root.formatTime(root.currentPositionSeconds);

            // Deteksi pergantian trek lagu
            var trackKey = (root.title + "---" + root.artist).toLowerCase();
            if (trackKey !== root.lastTrackKey && root.title.length > 0) {
                root.lastTrackKey = trackKey;
                root.parsedLyrics = [];
                root.currentLyricIndex = -1;
                root.lyricChanged("", "", false, false, "", false);

                root.fetchLyrics(root.title, root.artist, root.album, root.duration);
            }

            // Temukan baris lirik yang aktif berdasarkan posisi detik lagu
            if (root.parsedLyrics.length > 0) {
                var foundIndex = -1;
                for (var i = 0; i < root.parsedLyrics.length; i++) {
                    if (root.currentPositionSeconds >= root.parsedLyrics[i].timestamp) {
                        foundIndex = i;
                    } else {
                        break;
                    }
                }

                if (foundIndex !== root.currentLyricIndex) {
                    root.currentLyricIndex = foundIndex;
                    if (foundIndex >= 0) {
                        var item = root.parsedLyrics[foundIndex];
                        root.activeLead = item.lead;
                        root.activeBacking = item.backing;
                        root.hasBacking = item.hasBacking;
                        root.isBackingOnly = item.isBackingOnly;
                        root.activeRomaji = item.romaji;
                        root.hasRomaji = item.hasRomaji;

                        root.lyricChanged(
                            item.lead,
                            item.backing,
                            item.hasBacking,
                            item.isBackingOnly,
                            item.romaji,
                            item.hasRomaji
                        );
                    } else {
                        root.activeLead = "";
                        root.activeBacking = "";
                        root.hasBacking = false;
                        root.isBackingOnly = false;
                        root.activeRomaji = "";
                        root.hasRomaji = false;
                        root.lyricChanged("", "", false, false, "", false);
                    }
                }
            }
        }
    }

    fullRepresentation: Item {
        id: fullRep
        anchors.fill: parent
        clip: false

        // Deteksi hover mouse di atas widget (tidak memblokir klik)
        MouseArea {
            id: widgetHoverArea
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
        }

        // Background Gradient Layer (Bleeds top and bottom outside the widget outline)
        Item {
            id: panel
            clip: false
            x: root.textAlignment === "left" ? 0 : (root.textAlignment === "center" ? Math.round((fullRep.width - width) / 2) : (fullRep.width - width))
            y: -root.bgTopOffset
            width: Math.round(fullRep.width * (root.bgWidthPercent / 100.0))
            height: fullRep.height + root.bgTopOffset + root.bgBottomOffset

            opacity: root.hasPlayer ? 1.0 : 0.0

            Behavior on opacity {
                NumberAnimation {
                    duration: root.hasPlayer ? 500 : 400
                    easing.type: Easing.InOutQuad
                }
            }

            Rectangle {
                id: gradientBg
                anchors.fill: parent
                clip: false

                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.00; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.getGradientOpacity(0.00)) }
                    GradientStop { position: 0.10; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.getGradientOpacity(0.10)) }
                    GradientStop { position: 0.20; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.getGradientOpacity(0.20)) }
                    GradientStop { position: 0.35; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.getGradientOpacity(0.35)) }
                    GradientStop { position: 0.50; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.getGradientOpacity(0.50)) }
                    GradientStop { position: 0.65; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.getGradientOpacity(0.65)) }
                    GradientStop { position: 0.80; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.getGradientOpacity(0.80)) }
                    GradientStop { position: 0.90; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.getGradientOpacity(0.90)) }
                    GradientStop { position: 1.00; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.getGradientOpacity(1.00)) }
                }
            }
        }

        // Content Area (Track Info, Lyrics, Timer - stays within widget outline)
        Item {
            id: contentArea
            anchors.fill: parent
            clip: false
            opacity: root.hasPlayer ? 1.0 : 0.0

            Behavior on opacity {
                NumberAnimation {
                    duration: root.hasPlayer ? 500 : 400
                    easing.type: Easing.InOutQuad
                }
            }

            // Tombol Refresh Lirik (Muncul saat hover panel atau saat loading)
            Rectangle {
                id: refreshButton
                x: panel.x + panel.width - width - root.baseLeftPadding
                y: root.titleTopMargin
                width: 28
                height: 28
                radius: 14
                z: 10
                color: refreshMouseArea.containsMouse ? Qt.rgba(1, 1, 1, 0.22) : (refreshMouseArea.pressed ? Qt.rgba(1, 1, 1, 0.32) : Qt.rgba(0, 0, 0, 0.30))
                border.color: Qt.rgba(1, 1, 1, refreshMouseArea.containsMouse ? 0.45 : 0.15)
                border.width: 1
                visible: root.hasPlayer
                opacity: (root.isFetchingLyrics || refreshMouseArea.containsMouse || widgetHoverArea.containsMouse) ? 0.95 : 0.0

                Behavior on opacity {
                    NumberAnimation { duration: 250 }
                }

                Kirigami.Icon {
                    id: refreshIcon
                    anchors.centerIn: parent
                    implicitWidth: 15
                    implicitHeight: 15
                    source: "view-refresh"
                    color: refreshMouseArea.containsMouse ? "#FFFFFF" : Qt.rgba(1, 1, 1, 0.80)

                    RotationAnimator {
                        target: refreshIcon
                        from: 0
                        to: 360
                        duration: 800
                        loops: Animation.Infinite
                        running: root.isFetchingLyrics
                    }
                }

                MouseArea {
                    id: refreshMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        root.refreshLyrics(true);
                    }
                }

                QQC2.ToolTip.visible: refreshMouseArea.containsMouse
                QQC2.ToolTip.text: i18n("Refresh Lyrics")
                QQC2.ToolTip.delay: 300
            }

            // Informasi Lagu (Kiri Atas)
            Column {
                id: trackInfo
                width: Math.round(panel.width * 0.85)
                x: panel.x + (root.textAlignment === "center" ? Math.round((panel.width - width) / 2) : (root.textAlignment === "right" ? (panel.width - width - root.baseLeftPadding) : root.baseLeftPadding))
                y: root.titleTopMargin
                spacing: 6
                visible: (root.showTitle && root.title.length > 0) || (root.showArtist && root.artist.length > 0)

                Item {
                    id: titleItem
                    width: parent.width
                    height: (root.showTitle && root.title.length > 0) ? titleLabel.implicitHeight : 0
                    visible: root.showTitle && (root.title.length > 0)

                    Text {
                        x: 1
                        y: 2
                        width: parent.width
                        visible: parent.visible
                        text: root.title
                        font.family: root.titleFontFamily + ", Noto Sans, sans-serif"
                        font.pixelSize: root.titleFontSize
                        font.weight: Font.Bold
                        color: Qt.rgba(0, 0, 0, 0.45)
                        wrapMode: Text.WordWrap
                        elide: Text.ElideRight
                        maximumLineCount: 2
                        horizontalAlignment: root.qmlTextAlignment
                    }

                    Glow {
                        anchors.fill: titleLabel
                        visible: parent.visible
                        radius: 8
                        samples: 17
                        color: Qt.rgba(1.0, 1.0, 1.0, 0.32)
                        source: titleLabel
                        spread: 0.14
                    }

                    Text {
                        id: titleLabel
                        width: parent.width
                        visible: parent.visible
                        text: root.title
                        font.family: root.titleFontFamily + ", Noto Sans, sans-serif"
                        font.pixelSize: root.titleFontSize
                        font.weight: Font.Bold
                        color: "#FFFFFF"
                        wrapMode: Text.WordWrap
                        elide: Text.ElideRight
                        maximumLineCount: 2
                        horizontalAlignment: root.qmlTextAlignment
                    }
                }

                Item {
                    id: artistItem
                    width: parent.width
                    height: (root.showArtist && root.artist.length > 0) ? artistLabel.implicitHeight : 0
                    visible: root.showArtist && (root.artist.length > 0)

                    Text {
                        x: 1
                        y: 1
                        width: parent.width
                        visible: parent.visible
                        text: root.artist
                        font.family: root.artistFontFamily + ", Noto Sans, sans-serif"
                        font.pixelSize: root.artistFontSize
                        font.weight: Font.Medium
                        color: Qt.rgba(0, 0, 0, 0.40)
                        wrapMode: Text.WordWrap
                        elide: Text.ElideRight
                        maximumLineCount: 1
                        horizontalAlignment: root.qmlTextAlignment
                    }

                    Text {
                        id: artistLabel
                        width: parent.width
                        visible: parent.visible
                        text: root.artist
                        font.family: root.artistFontFamily + ", Noto Sans, sans-serif"
                        font.pixelSize: root.artistFontSize
                        font.weight: Font.Medium
                        color: Qt.rgba(0.92, 0.93, 0.96, 0.72)
                        wrapMode: Text.WordWrap
                        elide: Text.ElideRight
                        maximumLineCount: 1
                        horizontalAlignment: root.qmlTextAlignment
                    }
                }
            }

            // Kontainer Lirik
            Item {
                id: lyricContainer
                width: Math.round(panel.width * 0.88)
                x: panel.x + (root.textAlignment === "center" ? Math.round((panel.width - width) / 2) : (root.textAlignment === "right" ? (panel.width - width - root.baseLeftPadding) : root.baseLeftPadding))
                y: Math.max((trackInfo.visible ? (trackInfo.y + trackInfo.height + 30) : root.titleTopMargin), Math.round(fullRep.height * 0.40))
                height: Math.max(layerA.implicitHeight, layerB.implicitHeight)
                visible: root.showLyrics

                property Item currentLayer: layerA
                property Item incomingLayer: layerB

                function updateLyric(newLead, newBacking, newHasBacking, newIsBackingOnly, newRomaji, newHasRomaji) {
                    if (currentLayer.leadText === newLead &&
                        currentLayer.backingText === newBacking &&
                        currentLayer.romajiText === newRomaji &&
                        currentLayer.hasBacking === newHasBacking &&
                        currentLayer.isBackingOnly === newIsBackingOnly &&
                        currentLayer.hasRomaji === newHasRomaji) {
                        return;
                    }

                    if (revealAnim.running) revealAnim.stop();

                    currentLayer.opacity = 0.0;
                    currentLayer.leadText = "";
                    currentLayer.backingText = "";
                    currentLayer.romajiText = "";
                    currentLayer.hasBacking = false;
                    currentLayer.isBackingOnly = false;
                    currentLayer.hasRomaji = false;

                    if (!newLead && !newBacking) {
                        incomingLayer.opacity = 0.0;
                        incomingLayer.leadText = "";
                        incomingLayer.backingText = "";
                        incomingLayer.romajiText = "";
                        return;
                    }

                    incomingLayer.leadText = newLead;
                    incomingLayer.backingText = newBacking;
                    incomingLayer.hasBacking = newHasBacking;
                    incomingLayer.isBackingOnly = newIsBackingOnly;
                    incomingLayer.romajiText = newRomaji;
                    incomingLayer.hasRomaji = newHasRomaji;

                    var prevCurrent = currentLayer;
                    currentLayer = incomingLayer;
                    incomingLayer = prevCurrent;

                    revealAnim.target = currentLayer;
                    revealAnim.restart();
                }

                Connections {
                    target: root
                    function onLyricChanged(newLead, newBacking, newHasBacking, newIsBackingOnly, newRomaji, newHasRomaji) {
                        lyricContainer.updateLyric(
                            newLead,
                            newBacking,
                            newHasBacking,
                            newIsBackingOnly,
                            newRomaji,
                            newHasRomaji
                        );
                    }
                }

                Connections {
                    target: root.b
                    enabled: root.b !== null
                    function onActiveLyricChanged() {
                        lyricContainer.updateLyric(
                            root.activeLead,
                            root.activeBacking,
                            root.hasBacking,
                            root.isBackingOnly,
                            root.activeRomaji,
                            root.hasRomaji
                        );
                    }
                }

                NumberAnimation {
                    id: revealAnim
                    property: "opacity"
                    from: 0.2
                    to: 1.0
                    duration: 45
                    easing.type: Easing.OutQuad
                }

                component LyricDisplayLayer: Item {
                    id: layer
                    property string leadText: ""
                    property string backingText: ""
                    property bool hasBacking: false
                    property bool isBackingOnly: false
                    property string romajiText: ""
                    property bool hasRomaji: false

                    readonly property string displayLead: root.splitLongSentence(leadText)
                    readonly property string displayBacking: root.splitLongSentence(backingText)
                    readonly property string displayRomaji: root.splitLongSentence(romajiText)

                    width: parent ? parent.width : 0
                    implicitHeight: col.implicitHeight

                    Column {
                        id: col
                        width: parent.width
                        spacing: root.lyricItemSpacing

                        Item {
                            width: parent.width
                            height: leadTextItem.implicitHeight
                            visible: !layer.isBackingOnly && (layer.displayLead.length > 0)

                            Text {
                                x: 1
                                y: 2
                                width: parent.width
                                text: layer.displayLead
                                font.family: root.lyricFontFamily + ", Noto Sans, sans-serif"
                                font.pixelSize: root.lyricFontSize
                                font.weight: Font.Bold
                                color: Qt.rgba(0, 0, 0, 0.45)
                                wrapMode: Text.WordWrap
                                lineHeight: root.lyricLineSpacing
                                horizontalAlignment: root.qmlTextAlignment
                            }

                            Glow {
                                anchors.fill: leadTextItem
                                radius: 7
                                samples: 15
                                color: Qt.rgba(1.0, 1.0, 1.0, 0.30)
                                source: leadTextItem
                                spread: 0.12
                            }

                            Text {
                                id: leadTextItem
                                width: parent.width
                                text: layer.displayLead
                                font.family: root.lyricFontFamily + ", Noto Sans, sans-serif"
                                font.pixelSize: root.lyricFontSize
                                font.weight: Font.Bold
                                color: "#FFFFFF"
                                wrapMode: Text.WordWrap
                                lineHeight: root.lyricLineSpacing
                                horizontalAlignment: root.qmlTextAlignment
                            }
                        }

                        Item {
                            width: parent.width
                            height: backingTextItem.implicitHeight
                            visible: layer.hasBacking && (layer.displayBacking.length > 0)

                            Text {
                                x: 1
                                y: 1
                                width: parent.width
                                text: layer.displayBacking
                                font.family: root.lyricFontFamily + ", Noto Sans, sans-serif"
                                font.pixelSize: Math.max(12, Math.round(root.lyricFontSize * 0.82))
                                font.weight: Font.DemiBold
                                font.italic: true
                                color: Qt.rgba(0, 0, 0, 0.40)
                                wrapMode: Text.WordWrap
                                lineHeight: root.lyricLineSpacing
                                horizontalAlignment: root.qmlTextAlignment
                            }

                            Glow {
                                anchors.fill: backingTextItem
                                radius: 5
                                samples: 11
                                color: Qt.rgba(0.90, 0.92, 0.96, 0.22)
                                source: backingTextItem
                                spread: 0.10
                            }

                            Text {
                                id: backingTextItem
                                width: parent.width
                                text: layer.displayBacking
                                font.family: root.lyricFontFamily + ", Noto Sans, sans-serif"
                                font.pixelSize: Math.max(12, Math.round(root.lyricFontSize * 0.82))
                                font.weight: Font.DemiBold
                                font.italic: true
                                color: Qt.rgba(0.90, 0.92, 0.96, 0.78)
                                wrapMode: Text.WordWrap
                                lineHeight: root.lyricLineSpacing
                                horizontalAlignment: root.qmlTextAlignment
                            }
                        }

                        Item {
                            width: parent.width
                            height: romajiTextItem.implicitHeight
                            visible: root.showRomaji && layer.hasRomaji && (layer.displayRomaji.length > 0)

                            Text {
                                x: 1
                                y: 1
                                width: parent.width
                                text: layer.displayRomaji
                                font.family: root.romajiFontFamily + ", Noto Sans, sans-serif"
                                font.pixelSize: root.romajiFontSize
                                font.weight: Font.Normal
                                color: Qt.rgba(0, 0, 0, 0.40)
                                wrapMode: Text.WordWrap
                                lineHeight: root.lyricLineSpacing
                                horizontalAlignment: root.qmlTextAlignment
                            }

                            Glow {
                                anchors.fill: romajiTextItem
                                radius: 5
                                samples: 11
                                color: Qt.rgba(0.88, 0.90, 0.94, 0.20)
                                source: romajiTextItem
                                spread: 0.10
                            }

                            Text {
                                id: romajiTextItem
                                width: parent.width
                                text: layer.displayRomaji
                                font.family: root.romajiFontFamily + ", Noto Sans, sans-serif"
                                font.pixelSize: root.romajiFontSize
                                font.weight: Font.Normal
                                color: Qt.rgba(0.88, 0.90, 0.94, 0.80)
                                wrapMode: Text.WordWrap
                                lineHeight: root.lyricLineSpacing
                                horizontalAlignment: root.qmlTextAlignment
                            }
                        }
                    }
                }

                LyricDisplayLayer {
                    id: layerA
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    opacity: 1.0
                }

                LyricDisplayLayer {
                    id: layerB
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    opacity: 0.0
                }
            }

            // Indikator Waktu Playback (Mengunci ke dasar widget outline)
            Item {
                id: playbackTimeItem
                width: timeLabel.implicitWidth + 2
                height: timeLabel.implicitHeight + 2
                x: panel.x + (root.textAlignment === "center" ? Math.round((panel.width - width) / 2) : (root.textAlignment === "right" ? (panel.width - width - root.baseLeftPadding) : root.baseLeftPadding))
                anchors.bottom: parent.bottom
                anchors.bottomMargin: root.timerBottomMargin
                visible: root.showTimer && root.hasPlayer && (root.formattedTime.length > 0)

                Text {
                    x: 1
                    y: 1
                    text: root.formattedTime
                    font.family: root.timerFontFamily + ", Noto Sans, sans-serif"
                    font.pixelSize: root.timerFontSize
                    font.weight: Font.Medium
                    color: Qt.rgba(0, 0, 0, 0.55)
                }

                Text {
                    id: timeLabel
                    text: root.formattedTime
                    font.family: root.timerFontFamily + ", Noto Sans, sans-serif"
                    font.pixelSize: root.timerFontSize
                    font.weight: Font.Medium
                    color: Qt.rgba(0.95, 0.96, 0.98, 0.85)
                }
            }
        }
    }
}
