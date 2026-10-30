import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    id: root

    // Component Visibility
    property alias cfg_showTitle: showTitleCheck.checked
    property alias cfg_showArtist: showArtistCheck.checked
    property alias cfg_showLyrics: showLyricsCheck.checked
    property alias cfg_showRomaji: showRomajiCheck.checked
    property alias cfg_showTimer: showTimerCheck.checked

    // Layout & Alignment
    property alias cfg_textAlignment: textAlignCombo.currentValue
    property alias cfg_maxWordsPerLine: maxWordsSlider.value
    property alias cfg_lyricLineSpacing: lineSpacingSlider.value
    property alias cfg_titleTopMargin: titleTopMarginSlider.value
    property alias cfg_timerBottomMargin: timerBottomMarginSlider.value

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 12

        // Section 1: Visibility
        QQC2.Label {
            text: i18n("Visibility")
            font.bold: true
            font.pixelSize: 14
            color: Kirigami.Theme.highlightColor
            Layout.topMargin: 4
        }

        QQC2.CheckBox {
            id: showTitleCheck
            text: i18n("Track Title")
            Layout.fillWidth: true
        }

        QQC2.CheckBox {
            id: showArtistCheck
            text: i18n("Artist Name")
            Layout.fillWidth: true
        }

        QQC2.CheckBox {
            id: showLyricsCheck
            text: i18n("Lyrics")
            Layout.fillWidth: true
        }

        QQC2.CheckBox {
            id: showRomajiCheck
            text: i18n("Japanese Romaji")
            Layout.fillWidth: true
        }

        QQC2.CheckBox {
            id: showTimerCheck
            text: i18n("Playback Timer")
            Layout.fillWidth: true
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            Layout.topMargin: 4
            Layout.bottomMargin: 4
        }

        // Section 2: Layout & Alignment
        QQC2.Label {
            text: i18n("Layout & Alignment")
            font.bold: true
            font.pixelSize: 14
            color: Kirigami.Theme.highlightColor
        }

        // Text & Widget Alignment
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4

            QQC2.Label {
                text: i18n("Text Alignment:")
                font.weight: Font.Medium
            }

            QQC2.ComboBox {
                id: textAlignCombo
                textRole: "text"
                valueRole: "value"
                model: [
                    { text: i18n("Left"), value: "left" },
                    { text: i18n("Center"), value: "center" },
                    { text: i18n("Right"), value: "right" }
                ]
                Layout.fillWidth: true
                Component.onCompleted: {
                    var idx = indexOfValue(root.cfg_textAlignment);
                    if (idx !== -1) currentIndex = idx;
                }
            }
        }

        // Slider 1: Words per Line (Long slider spanning full width)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Words per Line:")
                    font.weight: Font.Medium
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: maxWordsSlider.value
                    font.bold: true
                    opacity: 0.85
                }
            }

            QQC2.Slider {
                id: maxWordsSlider
                from: 3
                to: 25
                stepSize: 1
                Layout.fillWidth: true
            }
        }

        // Slider 2: Line Spacing (Long slider spanning full width)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Line Spacing:")
                    font.weight: Font.Medium
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: lineSpacingSlider.value.toFixed(2) + "x"
                    font.bold: true
                    opacity: 0.85
                }
            }

            QQC2.Slider {
                id: lineSpacingSlider
                from: 1.00
                to: 2.20
                stepSize: 0.05
                Layout.fillWidth: true
            }
        }

        // Slider 3: Title Top Position (Long slider spanning full width)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Title Top Position:")
                    font.weight: Font.Medium
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: titleTopMarginSlider.value + " px"
                    font.bold: true
                    opacity: 0.85
                }
            }

            QQC2.Slider {
                id: titleTopMarginSlider
                from: 0
                to: 300
                stepSize: 2
                Layout.fillWidth: true
            }
        }

        // Slider 4: Timer Bottom Margin (Long slider spanning full width)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Timer Bottom Margin:")
                    font.weight: Font.Medium
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: timerBottomMarginSlider.value + " px"
                    font.bold: true
                    opacity: 0.85
                }
            }

            QQC2.Slider {
                id: timerBottomMarginSlider
                from: 0
                to: 150
                stepSize: 2
                Layout.fillWidth: true
            }
        }
    }
}
