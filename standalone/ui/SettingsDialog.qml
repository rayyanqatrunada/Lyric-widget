import QtQuick
import QtQuick.Window
import QtQuick.Controls as QQC2
import QtQuick.Layouts

Window {
    id: settingsWindow
    title: "Pengaturan Lyric Widget"
    width: 520
    height: 620
    minimumWidth: 480
    minimumHeight: 560
    color: "#181a20"
    visible: false

    readonly property var b: (typeof bridge !== "undefined" && bridge) ? bridge : null
    readonly property var systemFonts: Qt.fontFamilies()

    // Palet warna preset untuk memudahkan pengguna
    readonly property var colorPresets: [
        { name: "Charcoal (Default)", color: "#0a0d12" },
        { name: "Midnight Navy", color: "#0a1128" },
        { name: "Dark Amethyst", color: "#140920" },
        { name: "Deep Emerald", color: "#081a14" },
        { name: "Pure Black", color: "#000000" }
    ]

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        // Header
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "⚙️ Pengaturan Lyric Widget"
                font.pixelSize: 18
                font.bold: true
                color: "#FFFFFF"
            }
            Item { Layout.fillWidth: true }
            QQC2.Button {
                text: "Reset Default"
                onClicked: {
                    if (b) b.resetSettings();
                }
            }
        }

        QQC2.TabBar {
            id: tabBar
            Layout.fillWidth: true
            QQC2.TabButton { text: "Background" }
            QQC2.TabButton { text: "Font Komponen" }
        }

        StackLayout {
            id: stackLayout
            currentIndex: tabBar.currentIndex
            Layout.fillWidth: true
            Layout.fillHeight: true

            // =================================================================
            // TAB 1: PENGATURAN BACKGROUND
            // =================================================================
            QQC2.ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                ColumnLayout {
                    width: stackLayout.width - 24
                    spacing: 14

                    // 1. Lebar Background
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "Lebar Background"; color: "#E0E2EC"; font.bold: true }
                            Item { Layout.fillWidth: true }
                            Text { text: Math.round(widthSlider.value) + "%"; color: "#A0A4B8"; font.bold: true }
                        }
                        QQC2.Slider {
                            id: widthSlider
                            Layout.fillWidth: true
                            from: 20
                            to: 100
                            stepSize: 1
                            value: b ? b.bgWidthPercent : 82
                            onMoved: if (b) b.setSetting("bgWidthPercent", Math.round(value))
                        }
                    }

                    // 2. Warna Dasar Background
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Text { text: "Warna Dasar Background"; color: "#E0E2EC"; font.bold: true }

                        RowLayout {
                            spacing: 8
                            Repeater {
                                model: settingsWindow.colorPresets
                                delegate: Rectangle {
                                    width: 32
                                    height: 32
                                    radius: 6
                                    color: modelData.color
                                    border.color: (b && b.bgColor === modelData.color) ? "#4C9AFF" : "#404452"
                                    border.width: (b && b.bgColor === modelData.color) ? 2 : 1

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: if (b) b.setSetting("bgColor", modelData.color)
                                    }
                                }
                            }

                            QQC2.TextField {
                                id: customColorField
                                Layout.fillWidth: true
                                placeholderText: "#0a0d12"
                                text: b ? b.bgColor : "#0a0d12"
                                onEditingFinished: if (b && text.startsWith("#")) b.setSetting("bgColor", text)
                            }
                        }
                    }

                    // 3. Opacity Background
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "Tingkat Opacity Puncak"; color: "#E0E2EC"; font.bold: true }
                            Item { Layout.fillWidth: true }
                            Text { text: Math.round(opacitySlider.value * 100) + "%"; color: "#A0A4B8"; font.bold: true }
                        }
                        QQC2.Slider {
                            id: opacitySlider
                            Layout.fillWidth: true
                            from: 0.10
                            to: 1.00
                            stepSize: 0.01
                            value: b ? b.bgOpacity : 0.88
                            onMoved: if (b) b.setSetting("bgOpacity", parseFloat(value.toFixed(2)))
                        }
                    }

                    // 4. Titik Awal Fade
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: "Titik Awal Fade (Panjang Fade)"; color: "#E0E2EC"; font.bold: true }
                            Item { Layout.fillWidth: true }
                            Text { text: Math.round(fadeSlider.value * 100) + "%"; color: "#A0A4B8"; font.bold: true }
                        }
                        QQC2.Slider {
                            id: fadeSlider
                            Layout.fillWidth: true
                            from: 0.05
                            to: 0.70
                            stepSize: 0.01
                            value: b ? b.bgFadeStart : 0.25
                            onMoved: if (b) b.setSetting("bgFadeStart", parseFloat(value.toFixed(2)))
                        }
                        Text {
                            text: "Semakin kecil persentase, semakin awal dan panjang rentang gradasi memudar ke wallpaper."
                            color: "#808498"
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            // =================================================================
            // TAB 2: PENGATURAN FONT PADA SETIAP KOMPONEN
            // =================================================================
            QQC2.ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                ColumnLayout {
                    width: stackLayout.width - 24
                    spacing: 12

                    // Opsi Select All / Terapkan ke Semua
                    QQC2.CheckBox {
                        id: unifiedFontCheck
                        text: "Terapkan satu font ke semua teks (Select All)"
                        checked: b ? b.useUnifiedFont : false
                        onToggled: if (b) b.setSetting("useUnifiedFont", checked)
                    }

                    // Master Font
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: unifiedFontCheck.checked
                        spacing: 4
                        Text { text: "Font Universal (Semua Komponen):"; color: "#E0E2EC"; font.bold: true }
                        QQC2.ComboBox {
                            Layout.fillWidth: true
                            model: settingsWindow.systemFonts
                            currentIndex: model.indexOf(b ? b.unifiedFontFamily : "Noto Sans")
                            onActivated: if (b) b.setSetting("unifiedFontFamily", currentText)
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#2C303E"
                        visible: !unifiedFontCheck.checked
                    }

                    // 1. Font Judul
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: !unifiedFontCheck.checked
                        spacing: 4
                        Text { text: "Font Judul Lagu:"; color: "#E0E2EC" }
                        QQC2.ComboBox {
                            Layout.fillWidth: true
                            model: settingsWindow.systemFonts
                            currentIndex: model.indexOf(b ? b.titleFontFamily : "Noto Sans")
                            onActivated: if (b) b.setSetting("titleFontFamily", currentText)
                        }
                    }

                    // 2. Font Artis
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: !unifiedFontCheck.checked
                        spacing: 4
                        Text { text: "Font Nama Artis:"; color: "#E0E2EC" }
                        QQC2.ComboBox {
                            Layout.fillWidth: true
                            model: settingsWindow.systemFonts
                            currentIndex: model.indexOf(b ? b.artistFontFamily : "Noto Sans")
                            onActivated: if (b) b.setSetting("artistFontFamily", currentText)
                        }
                    }

                    // 3. Font Lirik Utama & Backing
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: !unifiedFontCheck.checked
                        spacing: 4
                        Text { text: "Font Lirik Utama & Backing:"; color: "#E0E2EC" }
                        QQC2.ComboBox {
                            Layout.fillWidth: true
                            model: settingsWindow.systemFonts
                            currentIndex: model.indexOf(b ? b.lyricFontFamily : "Noto Sans")
                            onActivated: if (b) b.setSetting("lyricFontFamily", currentText)
                        }
                    }

                    // 4. Font Romaji
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: !unifiedFontCheck.checked
                        spacing: 4
                        Text { text: "Font Teks Romaji:"; color: "#E0E2EC" }
                        QQC2.ComboBox {
                            Layout.fillWidth: true
                            model: settingsWindow.systemFonts
                            currentIndex: model.indexOf(b ? b.romajiFontFamily : "Noto Sans")
                            onActivated: if (b) b.setSetting("romajiFontFamily", currentText)
                        }
                    }

                    // 5. Font Timer
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: !unifiedFontCheck.checked
                        spacing: 4
                        Text { text: "Font Timer Waktu:"; color: "#E0E2EC" }
                        QQC2.ComboBox {
                            Layout.fillWidth: true
                            model: settingsWindow.systemFonts
                            currentIndex: model.indexOf(b ? b.timerFontFamily : "Noto Sans")
                            onActivated: if (b) b.setSetting("timerFontFamily", currentText)
                        }
                    }
                }
            }
        }

        // Footer
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            QQC2.Button {
                text: "Tutup"
                onClicked: settingsWindow.close()
            }
        }
    }
}
