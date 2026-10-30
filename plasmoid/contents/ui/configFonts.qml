import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    id: root

    // Font Family Aliases
    property alias cfg_useUnifiedFont: unifiedCheckBox.checked
    property alias cfg_unifiedFontFamily: unifiedPicker.currentFont
    property alias cfg_titleFontFamily: titlePicker.currentFont
    property alias cfg_artistFontFamily: artistPicker.currentFont
    property alias cfg_lyricFontFamily: lyricPicker.currentFont
    property alias cfg_romajiFontFamily: romajiPicker.currentFont
    property alias cfg_timerFontFamily: timerPicker.currentFont

    // Font Size Aliases
    property alias cfg_titleFontSize: titleSizeSlider.value
    property alias cfg_artistFontSize: artistSizeSlider.value
    property alias cfg_lyricFontSize: lyricSizeSlider.value
    property alias cfg_romajiFontSize: romajiSizeSlider.value
    property alias cfg_timerFontSize: timerSizeSlider.value

    // Single cached list of system fonts
    readonly property var systemFonts: Qt.fontFamilies()

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 12

        // Master Font Option
        QQC2.Label {
            text: i18n("Master Typography")
            font.bold: true
            font.pixelSize: 14
            color: Kirigami.Theme.highlightColor
            Layout.topMargin: 4
        }

        QQC2.CheckBox {
            id: unifiedCheckBox
            text: i18n("Use single font for all components")
            Layout.fillWidth: true
        }

        RowLayout {
            visible: unifiedCheckBox.checked
            Layout.fillWidth: true
            spacing: 16

            QQC2.Label {
                text: i18n("Universal Font:")
                font.weight: Font.Medium
            }

            FontPicker {
                id: unifiedPicker
                allFonts: root.systemFonts
                currentFont: root.cfg_unifiedFontFamily || "Noto Sans"
                Layout.preferredWidth: 260
                Layout.maximumWidth: 300
            }

            Item { Layout.fillWidth: true }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            Layout.topMargin: 4
            Layout.bottomMargin: 4
        }

        // Section: Granular Components
        QQC2.Label {
            text: i18n("Individual Component Fonts & Sizes")
            font.bold: true
            font.pixelSize: 14
            color: Kirigami.Theme.highlightColor
        }

        // 1. Track Title
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            QQC2.Label {
                text: i18n("Track Title")
                font.weight: Font.DemiBold
                font.pixelSize: 13
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                FontPicker {
                    id: titlePicker
                    visible: !unifiedCheckBox.checked
                    allFonts: root.systemFonts
                    currentFont: root.cfg_titleFontFamily || "Noto Sans"
                    Layout.preferredWidth: 260
                    Layout.maximumWidth: 280
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    QQC2.Label {
                        text: i18n("Size:")
                        font.weight: Font.Medium
                    }

                    QQC2.Slider {
                        id: titleSizeSlider
                        from: 14
                        to: 64
                        stepSize: 1
                        Layout.fillWidth: true
                    }

                    QQC2.Label {
                        text: titleSizeSlider.value + " px"
                        font.bold: true
                        Layout.preferredWidth: 45
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            opacity: 0.4
        }

        // 2. Artist Name
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            QQC2.Label {
                text: i18n("Artist Name")
                font.weight: Font.DemiBold
                font.pixelSize: 13
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                FontPicker {
                    id: artistPicker
                    visible: !unifiedCheckBox.checked
                    allFonts: root.systemFonts
                    currentFont: root.cfg_artistFontFamily || "Noto Sans"
                    Layout.preferredWidth: 260
                    Layout.maximumWidth: 280
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    QQC2.Label {
                        text: i18n("Size:")
                        font.weight: Font.Medium
                    }

                    QQC2.Slider {
                        id: artistSizeSlider
                        from: 10
                        to: 36
                        stepSize: 1
                        Layout.fillWidth: true
                    }

                    QQC2.Label {
                        text: artistSizeSlider.value + " px"
                        font.bold: true
                        Layout.preferredWidth: 45
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            opacity: 0.4
        }

        // 3. Lyrics
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            QQC2.Label {
                text: i18n("Lyrics")
                font.weight: Font.DemiBold
                font.pixelSize: 13
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                FontPicker {
                    id: lyricPicker
                    visible: !unifiedCheckBox.checked
                    allFonts: root.systemFonts
                    currentFont: root.cfg_lyricFontFamily || "Noto Sans"
                    Layout.preferredWidth: 260
                    Layout.maximumWidth: 280
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    QQC2.Label {
                        text: i18n("Size:")
                        font.weight: Font.Medium
                    }

                    QQC2.Slider {
                        id: lyricSizeSlider
                        from: 14
                        to: 60
                        stepSize: 1
                        Layout.fillWidth: true
                    }

                    QQC2.Label {
                        text: lyricSizeSlider.value + " px"
                        font.bold: true
                        Layout.preferredWidth: 45
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            opacity: 0.4
        }

        // 4. Japanese Romaji
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            QQC2.Label {
                text: i18n("Japanese Romaji")
                font.weight: Font.DemiBold
                font.pixelSize: 13
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                FontPicker {
                    id: romajiPicker
                    visible: !unifiedCheckBox.checked
                    allFonts: root.systemFonts
                    currentFont: root.cfg_romajiFontFamily || "Noto Sans"
                    Layout.preferredWidth: 260
                    Layout.maximumWidth: 280
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    QQC2.Label {
                        text: i18n("Size:")
                        font.weight: Font.Medium
                    }

                    QQC2.Slider {
                        id: romajiSizeSlider
                        from: 12
                        to: 40
                        stepSize: 1
                        Layout.fillWidth: true
                    }

                    QQC2.Label {
                        text: romajiSizeSlider.value + " px"
                        font.bold: true
                        Layout.preferredWidth: 45
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            opacity: 0.4
        }

        // 5. Playback Timer
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            QQC2.Label {
                text: i18n("Playback Timer")
                font.weight: Font.DemiBold
                font.pixelSize: 13
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                FontPicker {
                    id: timerPicker
                    visible: !unifiedCheckBox.checked
                    allFonts: root.systemFonts
                    currentFont: root.cfg_timerFontFamily || "Noto Sans"
                    Layout.preferredWidth: 260
                    Layout.maximumWidth: 280
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    QQC2.Label {
                        text: i18n("Size:")
                        font.weight: Font.Medium
                    }

                    QQC2.Slider {
                        id: timerSizeSlider
                        from: 10
                        to: 32
                        stepSize: 1
                        Layout.fillWidth: true
                    }

                    QQC2.Label {
                        text: timerSizeSlider.value + " px"
                        font.bold: true
                        Layout.preferredWidth: 45
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }
        }
    }
}
