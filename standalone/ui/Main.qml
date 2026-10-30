import QtQuick
import QtQuick.Window
import Qt5Compat.GraphicalEffects

Window {
    id: root

    // Properti reaktif aman untuk menghindari evaluasi null saat parser pertama kali memuat QML
    readonly property var b: (typeof bridge !== "undefined" && bridge) ? bridge : null
    readonly property bool hasPlayer: b ? b.hasPlayer : false
    readonly property string playbackStatus: b ? b.playbackStatus : ""
    readonly property string title: b ? b.title : ""
    readonly property string artist: b ? b.artist : ""
    readonly property string activeLead: b ? b.activeLead : ""
    readonly property string activeBacking: b ? b.activeBacking : ""
    readonly property bool hasBacking: b ? b.hasBacking : false
    readonly property bool isBackingOnly: b ? b.isBackingOnly : false
    readonly property string activeRomaji: b ? b.activeRomaji : ""
    readonly property bool hasRomaji: b ? b.hasRomaji : false
    readonly property string formattedTime: b ? b.formattedTime : ""

    // =========================================================================
    // PENGATURAN TEMA & KUSTOMISASI (BACKGROUND & FONT)
    // Mendukung integrasi KDE Plasma configuration (Plasmoid.configuration)
    // serta fallback reaktif dari LyricBridge untuk standalone / testing
    // =========================================================================
    readonly property var plasmaCfg: (typeof Plasmoid !== "undefined" && Plasmoid && Plasmoid.configuration) ? Plasmoid.configuration : null

    // 1. Pengaturan Background
    readonly property int bgWidthPercent: plasmaCfg ? plasmaCfg.bgWidthPercent : (b ? b.bgWidthPercent : 82)
    readonly property color bgColor: plasmaCfg ? plasmaCfg.bgColor : (b ? b.bgColor : "#0a0d12")
    readonly property real bgOpacity: plasmaCfg ? plasmaCfg.bgOpacity : (b ? b.bgOpacity : 0.88)
    readonly property real bgFadeStart: plasmaCfg ? plasmaCfg.bgFadeStart : (b ? b.bgFadeStart : 0.25)

    // 2. Pengaturan Font (Judul, Artis, Lirik, Romaji, Timer + Select All)
    readonly property bool useUnifiedFont: plasmaCfg ? plasmaCfg.useUnifiedFont : (b ? b.useUnifiedFont : false)
    readonly property string unifiedFontFamily: plasmaCfg ? plasmaCfg.unifiedFontFamily : (b ? b.unifiedFontFamily : "Noto Sans")

    readonly property string titleFontFamily: useUnifiedFont ? unifiedFontFamily : (plasmaCfg ? plasmaCfg.titleFontFamily : (b ? b.titleFontFamily : "Noto Sans"))
    readonly property string artistFontFamily: useUnifiedFont ? unifiedFontFamily : (plasmaCfg ? plasmaCfg.artistFontFamily : (b ? b.artistFontFamily : "Noto Sans"))
    readonly property string lyricFontFamily: useUnifiedFont ? unifiedFontFamily : (plasmaCfg ? plasmaCfg.lyricFontFamily : (b ? b.lyricFontFamily : "Noto Sans"))
    readonly property string romajiFontFamily: useUnifiedFont ? unifiedFontFamily : (plasmaCfg ? plasmaCfg.romajiFontFamily : (b ? b.romajiFontFamily : "Noto Sans"))
    readonly property string timerFontFamily: useUnifiedFont ? unifiedFontFamily : (plasmaCfg ? plasmaCfg.timerFontFamily : (b ? b.timerFontFamily : "Noto Sans"))

    // Widget overlay di atas desktop KDE Plasma 6
    visible: root.hasPlayer || panel.x > -panel.width || panel.opacity > 0.01
    color: "transparent"

    // Flags: frameless, transparan terhadap input mouse, tetap di bawah jendela aplikasi lain
    flags: Qt.FramelessWindowHint | Qt.Window | Qt.WindowStaysOnBottomHint | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus

    // Ukuran jendela memenuhi layar aktif
    width: Screen.width
    height: Screen.height
    x: Screen.virtualX
    y: Screen.virtualY

    // Resolusi dasar responsif
    readonly property real baseLeftPadding: Math.max(48, Math.round(width * 0.045))
    readonly property real baseTopPadding: Math.max(48, Math.round(height * 0.065))

    // Memecah kalimat lirik panjang: maksimal 7 kata per baris, kata berikutnya pindah ke baris berikutnya
    function splitLongSentence(str) {
        if (!str) return "";
        var lines = str.split("\n");
        return lines.map(function(line) {
            var trimmed = line.trim();
            if (!trimmed) return "";
            var words = trimmed.split(/\s+/);
            if (words.length <= 7) return trimmed;
            var chunks = [];
            for (var i = 0; i < words.length; i += 7) {
                chunks.push(words.slice(i, i + 7).join(" "));
            }
            return chunks.join("\n");
        }).join("\n");
    }

    // =========================================================================
    // KOMPONEN LAYER TAMPILAN LIRIK (DIGUNAKAN UNTUK CROSSFADE DUA LAYER)
    // =========================================================================
    component LyricDisplayLayer: Item {
        id: layer
        property string leadText: ""
        property string backingText: ""
        property bool hasBacking: false
        property bool isBackingOnly: false
        property string romajiText: ""
        property bool hasRomaji: false

        // Teks yang diformat: jika lebih dari 7 kata, baris akan dipecah dengan maksimal 7 kata per baris
        readonly property string displayLead: root.splitLongSentence(leadText)
        readonly property string displayBacking: root.splitLongSentence(backingText)
        readonly property string displayRomaji: root.splitLongSentence(romajiText)

        width: parent ? parent.width : 0
        implicitHeight: col.implicitHeight

        Column {
            id: col
            width: parent.width
            spacing: 8

            // 1. Baris Vokal Utama (Lead Vocal / Single Active Lyric)
            Item {
                width: parent.width
                height: leadTextItem.implicitHeight
                visible: !layer.isBackingOnly && (layer.displayLead.length > 0)

                // Bayangan teks untuk kontras sempurna
                Text {
                    x: 1
                    y: 2
                    width: parent.width
                    text: layer.displayLead
                    font.family: root.lyricFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                    font.pixelSize: Math.round(Math.min(28, Math.max(22, root.height * 0.026)))
                    font.weight: Font.Bold
                    color: Qt.rgba(0, 0, 0, 0.50)
                    wrapMode: Text.WordWrap
                    lineHeight: 1.25
                }

                // Efek glow halus di belakang lirik utama
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
                    font.family: root.lyricFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                    font.pixelSize: Math.round(Math.min(28, Math.max(22, root.height * 0.026)))
                    font.weight: Font.Bold
                    color: "#FFFFFF"
                    wrapMode: Text.WordWrap
                    lineHeight: 1.25
                }
            }

            // 2. Baris Backing Vocal (jika tersedia)
            Item {
                width: parent.width
                height: backingTextItem.implicitHeight
                visible: layer.hasBacking && (layer.displayBacking.length > 0)

                Text {
                    x: 1
                    y: 1
                    width: parent.width
                    text: layer.displayBacking
                    font.family: root.lyricFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                    font.pixelSize: Math.round(Math.min(22, Math.max(18, root.height * 0.021)))
                    font.weight: Font.DemiBold
                    font.italic: true
                    color: Qt.rgba(0, 0, 0, 0.40)
                    wrapMode: Text.WordWrap
                    lineHeight: 1.25
                }

                // Efek glow halus di belakang backing vocal
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
                    font.family: root.lyricFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                    font.pixelSize: Math.round(Math.min(22, Math.max(18, root.height * 0.021)))
                    font.weight: Font.DemiBold
                    font.italic: true
                    color: Qt.rgba(0.90, 0.92, 0.96, 0.78)
                    wrapMode: Text.WordWrap
                    lineHeight: 1.25
                }
            }

            // 3. Romaji (Hanya tampil untuk lirik berbahasa Jepang jika tersedia)
            Item {
                width: parent.width
                height: romajiTextItem.implicitHeight
                visible: layer.hasRomaji && (layer.displayRomaji.length > 0)

                Text {
                    x: 1
                    y: 1
                    width: parent.width
                    text: layer.displayRomaji
                    font.family: root.romajiFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                    font.pixelSize: Math.round(Math.min(20, Math.max(16, root.height * 0.019)))
                    font.weight: Font.Normal
                    color: Qt.rgba(0, 0, 0, 0.40)
                    wrapMode: Text.WordWrap
                    lineHeight: 1.22
                }

                // Efek glow halus di belakang teks romaji
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
                    font.family: root.romajiFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                    font.pixelSize: Math.round(Math.min(20, Math.max(16, root.height * 0.019)))
                    font.weight: Font.Normal
                    color: Qt.rgba(0.88, 0.90, 0.94, 0.80)
                    wrapMode: Text.WordWrap
                    lineHeight: 1.22
                }
            }
        }
    }

    // =========================================================================
    // PANEL BACKGROUND DENGAN GRADIENT TRANSPARANSI
    // =========================================================================
    Item {
        id: panel

        // Lebar panel dinamis mengikuti pengaturan pengguna (default 82%)
        width: Math.round(root.width * (root.bgWidthPercent / 100.0))
        height: root.height

        // Animasi Slide-In dari kiri saat player aktif, Slide-Out ke kiri saat player ditutup
        x: root.hasPlayer ? 0 : -width
        opacity: root.hasPlayer ? 1.0 : 0.0

        Behavior on x {
            NumberAnimation {
                duration: root.hasPlayer ? 550 : 450
                easing.type: root.hasPlayer ? Easing.OutCubic : Easing.InCubic
            }
        }

        Behavior on opacity {
            NumberAnimation {
                duration: root.hasPlayer ? 500 : 400
                easing.type: Easing.InOutQuad
            }
        }

        // Background dinamis dengan warna, opacity, dan titik awal fade yang dapat diatur
        Rectangle {
            id: gradientBg
            anchors.fill: parent

            gradient: Gradient {
                orientation: Gradient.Horizontal
                // 0.00: Sisi paling kiri nyaman dan kontras sesuai preferensi warna & opacity pengguna
                GradientStop { position: 0.00; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.bgOpacity) }
                // Posisi tengah sebelum fade:
                GradientStop { position: Math.max(0.04, root.bgFadeStart * 0.60); color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.bgOpacity * 0.98) }
                // Titik awal pemudaran (bgFadeStart):
                GradientStop { position: root.bgFadeStart; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.bgOpacity * 0.93) }
                // Rentang transisi memanjang proporsional:
                GradientStop { position: Math.min(0.99, root.bgFadeStart + (1.0 - root.bgFadeStart) * 0.16); color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.bgOpacity * 0.77) }
                GradientStop { position: Math.min(0.99, root.bgFadeStart + (1.0 - root.bgFadeStart) * 0.33); color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.bgOpacity * 0.57) }
                GradientStop { position: Math.min(0.99, root.bgFadeStart + (1.0 - root.bgFadeStart) * 0.51); color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.bgOpacity * 0.36) }
                GradientStop { position: Math.min(0.99, root.bgFadeStart + (1.0 - root.bgFadeStart) * 0.68); color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.bgOpacity * 0.20) }
                GradientStop { position: Math.min(0.99, root.bgFadeStart + (1.0 - root.bgFadeStart) * 0.84); color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.bgOpacity * 0.08) }
                GradientStop { position: Math.min(0.99, root.bgFadeStart + (1.0 - root.bgFadeStart) * 0.95); color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, root.bgOpacity * 0.015) }
                // 1.00: 100% transparan menyatu sempurna ke wallpaper
                GradientStop { position: 1.00; color: Qt.rgba(root.bgColor.r, root.bgColor.g, root.bgColor.b, 0.00) }
            }
        }

        // =====================================================================
        // INFORMASI LAGU (KIRI ATAS)
        // =====================================================================
        Column {
            id: trackInfo
            x: root.baseLeftPadding
            y: root.baseTopPadding
            width: Math.round(panel.width * 0.85)
            spacing: 6

            // Judul Lagu
            Item {
                width: parent.width
                height: titleLabel.implicitHeight

                // Bayangan lembut agar tetap terbaca pada wallpaper terang
                Text {
                    x: 1
                    y: 2
                    width: parent.width
                    text: root.title
                    font.family: root.titleFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                    font.pixelSize: Math.round(Math.min(32, Math.max(24, root.height * 0.030)))
                    font.weight: Font.Bold
                    color: Qt.rgba(0, 0, 0, 0.45)
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    maximumLineCount: 2
                }

                // Efek glow halus di belakang judul lagu
                Glow {
                    anchors.fill: titleLabel
                    radius: 8
                    samples: 17
                    color: Qt.rgba(1.0, 1.0, 1.0, 0.32)
                    source: titleLabel
                    spread: 0.14
                }

                Text {
                    id: titleLabel
                    width: parent.width
                    text: root.title
                    font.family: root.titleFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                    font.pixelSize: Math.round(Math.min(32, Math.max(24, root.height * 0.030)))
                    font.weight: Font.Bold
                    color: "#FFFFFF"
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    maximumLineCount: 2
                }
            }

            // Nama Artis (tepat di bawah judul, lebih kecil dan sedikit redup)
            Item {
                width: parent.width
                height: artistLabel.implicitHeight

                Text {
                    x: 1
                    y: 1
                    width: parent.width
                    text: root.artist
                    font.family: root.artistFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                    font.pixelSize: Math.round(Math.min(18, Math.max(14, root.height * 0.017)))
                    font.weight: Font.Medium
                    color: Qt.rgba(0, 0, 0, 0.40)
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }

                Text {
                    id: artistLabel
                    width: parent.width
                    text: root.artist
                    font.family: root.artistFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                    font.pixelSize: Math.round(Math.min(18, Math.max(14, root.height * 0.017)))
                    font.weight: Font.Medium
                    color: Qt.rgba(0.92, 0.93, 0.96, 0.72)
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }
            }
        }

        // =====================================================================
        // LIRIK AKTIF DENGAN PERGANTIAN RESPONSIF & PRESISI (STAGE 10.5)
        // Prioritas pada sinkronisasi audio: teks lama langsung berhenti,
        // tanpa lingering atau efek tumpang tindih vokal ganda.
        // =====================================================================
        Item {
            id: lyricContainer
            x: root.baseLeftPadding
            y: Math.max(trackInfo.y + trackInfo.height + 50, Math.round(root.height * 0.43))
            width: Math.round(panel.width * 0.88)
            height: Math.max(layerA.implicitHeight, layerB.implicitHeight)

            // Pointer layer aktif (sedang tampil) dan incoming (layer tujuan berikutnya)
            property Item currentLayer: layerA
            property Item incomingLayer: layerB

            function updateLyric(newLead, newBacking, newHasBacking, newIsBackingOnly, newRomaji, newHasRomaji) {
                // Hindari trigger jika isi lirik sama persis
                if (currentLayer.leadText === newLead &&
                    currentLayer.backingText === newBacking &&
                    currentLayer.romajiText === newRomaji &&
                    currentLayer.hasBacking === newHasBacking &&
                    currentLayer.isBackingOnly === newIsBackingOnly &&
                    currentLayer.hasRomaji === newHasRomaji) {
                    return;
                }

                // Hentikan animasi transisi sebelumnya jika masih berjalan
                if (revealAnim.running) {
                    revealAnim.stop();
                }

                // 1. Teks lama SEGERA BERHENTI DITAMPILKAN (Stage 10.5)
                // Memastikan teks lama tidak lingering saat vokal audio baris berikutnya dimulai,
                // dan mencegah dua baris terlihat bersamaan yang menimbulkan kesan vokal ganda.
                currentLayer.opacity = 0.0;
                currentLayer.leadText = "";
                currentLayer.backingText = "";
                currentLayer.romajiText = "";
                currentLayer.hasBacking = false;
                currentLayer.isBackingOnly = false;
                currentLayer.hasRomaji = false;

                // 2. Jika lirik baru kosong (misal jeda instrumen tanpa lirik):
                if (!newLead && !newBacking) {
                    incomingLayer.opacity = 0.0;
                    incomingLayer.leadText = "";
                    incomingLayer.backingText = "";
                    incomingLayer.romajiText = "";
                    return;
                }

                // 3. Muat konten lirik baru ke incomingLayer
                incomingLayer.leadText = newLead;
                incomingLayer.backingText = newBacking;
                incomingLayer.hasBacking = newHasBacking;
                incomingLayer.isBackingOnly = newIsBackingOnly;
                incomingLayer.romajiText = newRomaji;
                incomingLayer.hasRomaji = newHasRomaji;

                // 4. Tukar referensi layer
                var prevCurrent = currentLayer;
                currentLayer = incomingLayer;
                incomingLayer = prevCurrent;

                // 5. Animasi kemunculan yang sangat cepat & tegas (Stage 10.5)
                // Durasi 45 ms OutQuad dari opacity 0.2: teks baru langsung terbaca jelas
                // pada saat vokal audio dimulai tanpa menunda waktu baca lirik.
                revealAnim.target = currentLayer;
                revealAnim.restart();
            }

            // Pantau perubahan lirik dari backend secara reaktif (satu sinyal tunggal terpadu)
            Connections {
                target: root.b
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

            // Animasi transisi yang tegas dan singkat: 45 ms untuk kejelasan seketika
            NumberAnimation {
                id: revealAnim
                property: "opacity"
                from: 0.2
                to: 1.0
                duration: 45
                easing.type: Easing.OutQuad
            }

            // Layer A
            LyricDisplayLayer {
                id: layerA
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                opacity: 1.0
            }

            // Layer B
            LyricDisplayLayer {
                id: layerB
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                opacity: 0.0
            }
        }

        // =====================================================================
        // INDIKATOR WAKTU PEMUTARAN (POJOK KIRI BAWAH) - STAGE 10.5
        // Format: M.SS / M.SS (contoh: 0.00 / 3.24, 2.17 / 3.30)
        // Diperbesar ke 16-18 px dengan bobot Medium dan kontras tinggi
        // =====================================================================
        Item {
            id: playbackTimeItem
            x: root.baseLeftPadding
            anchors.bottom: panel.bottom
            anchors.bottomMargin: Math.max(36, Math.round(root.height * 0.050))
            width: timeLabel.implicitWidth + 2
            height: timeLabel.implicitHeight + 2
            visible: root.hasPlayer && root.formattedTime.length > 0

            // Bayangan teks lembut agar tetap kontras pada wallpaper terang
            Text {
                x: 1
                y: 1
                text: root.formattedTime
                font.family: root.timerFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                font.pixelSize: Math.round(Math.min(18, Math.max(16, root.height * 0.0165)))
                font.weight: Font.Medium
                color: Qt.rgba(0, 0, 0, 0.55)
            }

            Text {
                id: timeLabel
                text: root.formattedTime
                font.family: root.timerFontFamily + ", Noto Sans, Cantarell, Inter, sans-serif"
                font.pixelSize: Math.round(Math.min(18, Math.max(16, root.height * 0.0165)))
                font.weight: Font.Medium
                color: Qt.rgba(0.95, 0.96, 0.98, 0.85)
            }
        }
    }

    // Inisialisasi awal lirik jika backend telah memuat lirik saat startup
    Component.onCompleted: {
        if (root.activeLead !== "" || root.activeBacking !== "") {
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
}
