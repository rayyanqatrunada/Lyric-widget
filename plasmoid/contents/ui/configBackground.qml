import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.kquickcontrols as KQC2
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    id: root

    // Appearance
    property alias cfg_bgColor: colorButton.color
    property alias cfg_bgOpacity: opacitySlider.value
    property alias cfg_bgFadeStart: fadeSlider.value
    property alias cfg_bgPeakPosition: peakSlider.value

    // Sizing & Bleed
    property alias cfg_bgWidthPercent: widthSlider.value
    property alias cfg_bgTopOffset: topOffsetSlider.value
    property alias cfg_bgBottomOffset: bottomOffsetSlider.value

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 12

        // Section 1: Appearance
        QQC2.Label {
            text: i18n("Appearance")
            font.bold: true
            font.pixelSize: 14
            color: Kirigami.Theme.highlightColor
            Layout.topMargin: 4
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            QQC2.Label {
                text: i18n("Background Color:")
                font.weight: Font.Medium
            }

            KQC2.ColorButton {
                id: colorButton
                showAlphaChannel: false
            }

            Item { Layout.fillWidth: true }

            QQC2.Label {
                text: colorButton.color.toString()
                opacity: 0.75
            }
        }

        // Slider 1: Opacity (Full width long slider)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Opacity:")
                    font.weight: Font.Medium
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: Math.round(opacitySlider.value * 100) + "%"
                    font.bold: true
                    opacity: 0.85
                }
            }

            QQC2.Slider {
                id: opacitySlider
                from: 0.00
                to: 1.00
                stepSize: 0.01
                Layout.fillWidth: true
            }
        }

        // Slider 2: Fade Distance (Full width long slider)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Fade Distance:")
                    font.weight: Font.Medium
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: Math.round(fadeSlider.value * 100) + "%"
                    font.bold: true
                    opacity: 0.85
                }
            }

            QQC2.Slider {
                id: fadeSlider
                from: 0.00
                to: 1.00
                stepSize: 0.01
                Layout.fillWidth: true
            }
        }

        // Slider 3: Peak Position (Full width long slider)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Peak Position:")
                    font.weight: Font.Medium
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: Math.round(peakSlider.value * 100) + "%"
                    font.bold: true
                    opacity: 0.85
                }
            }

            QQC2.Slider {
                id: peakSlider
                from: 0.00
                to: 1.00
                stepSize: 0.01
                Layout.fillWidth: true
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
            Layout.topMargin: 4
            Layout.bottomMargin: 4
        }

        // Section 2: Background Sizing & Bleed
        QQC2.Label {
            text: i18n("Background Sizing & Bleed")
            font.bold: true
            font.pixelSize: 14
            color: Kirigami.Theme.highlightColor
        }

        // Slider 4: Width (Full width long slider)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Width:")
                    font.weight: Font.Medium
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: widthSlider.value + "%"
                    font.bold: true
                    opacity: 0.85
                }
            }

            QQC2.Slider {
                id: widthSlider
                from: 20
                to: 100
                stepSize: 1
                Layout.fillWidth: true
            }
        }

        // Slider 5: Top Expansion (Full width long slider)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Top Expansion:")
                    font.weight: Font.Medium
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: "+" + topOffsetSlider.value + " px"
                    font.bold: true
                    opacity: 0.85
                }
            }

            QQC2.Slider {
                id: topOffsetSlider
                from: 0
                to: 800
                stepSize: 5
                Layout.fillWidth: true
            }
        }

        // Slider 6: Bottom Expansion (Full width long slider)
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                QQC2.Label {
                    text: i18n("Bottom Expansion:")
                    font.weight: Font.Medium
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    text: "+" + bottomOffsetSlider.value + " px"
                    font.bold: true
                    opacity: 0.85
                }
            }

            QQC2.Slider {
                id: bottomOffsetSlider
                from: 0
                to: 800
                stepSize: 5
                Layout.fillWidth: true
            }
        }
    }
}
