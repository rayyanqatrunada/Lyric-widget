import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Item {
    id: picker

    property string currentFont: "Noto Sans"
    property var allFonts: []

    // Filtered and curated clean font list
    readonly property var cleanList: {
        var raw = picker.allFonts;
        if (!raw || raw.length === 0) return ["Noto Sans"];

        var blacklisted = ["emoji", "symbol", "math", "dingbat", "music", "braille", "marlett", "webdings", "wingdings"];
        var popular = [
            "Noto Sans", "Roboto", "Inter", "Ubuntu", "Cantarell",
            "Open Sans", "DejaVu Sans", "Liberation Sans", "Lato",
            "Montserrat", "Fira Sans", "Poppins", "Comfortaa",
            "Segoe UI", "Arial", "Helvetica", "Trebuchet MS",
            "Noto Serif", "DejaVu Serif", "Liberation Serif",
            "Noto Sans Mono", "DejaVu Sans Mono", "Monospace"
        ];

        var cleaned = [];
        var lookup = {};

        for (var i = 0; i < raw.length; i++) {
            var name = raw[i];
            if (!name || name.indexOf("[") !== -1 || name.indexOf("]") !== -1) continue;
            var lower = name.toLowerCase();
            var skip = false;
            for (var b = 0; b < blacklisted.length; b++) {
                if (lower.indexOf(blacklisted[b]) !== -1) {
                    skip = true;
                    break;
                }
            }
            if (skip) continue;
            if (!lookup[name]) {
                lookup[name] = true;
                cleaned.push(name);
            }
        }

        var top = [];
        var rest = [];
        for (var p = 0; p < popular.length; p++) {
            if (lookup[popular[p]]) {
                top.push(popular[p]);
            }
        }
        for (var c = 0; c < cleaned.length; c++) {
            if (popular.indexOf(cleaned[c]) === -1) {
                rest.push(cleaned[c]);
            }
        }
        rest.sort();
        return top.concat(rest);
    }

    implicitWidth: 260
    implicitHeight: pickerButton.implicitHeight

    QQC2.Button {
        id: pickerButton
        anchors.fill: parent
        leftPadding: 12
        rightPadding: 12
        topPadding: 6
        bottomPadding: 6

        contentItem: RowLayout {
            spacing: 8

            QQC2.Label {
                text: picker.currentFont ? picker.currentFont : i18n("Select Font...")
                font.family: picker.currentFont
                font.weight: Font.Normal
                font.pixelSize: 13
                elide: Text.ElideRight
                Layout.fillWidth: true
                verticalAlignment: Text.AlignVCenter
            }

            Kirigami.Icon {
                source: "go-down"
                implicitWidth: 12
                implicitHeight: 12
                opacity: 0.7
            }
        }

        onClicked: {
            fontPopup.open();
        }
    }

    QQC2.Popup {
        id: fontPopup
        y: pickerButton.height + 4
        width: pickerButton.width
        padding: 6
        modal: true
        focus: true
        closePolicy: QQC2.Popup.CloseOnEscape | QQC2.Popup.CloseOnPressOutside

        background: Rectangle {
            color: Kirigami.Theme.backgroundColor
            border.color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.25)
            border.width: 1
            radius: 6
        }

        onOpened: {
            searchField.text = "";
            searchField.forceActiveFocus();
            var idx = filteredList.indexOf(picker.currentFont);
            if (idx !== -1) {
                fontView.positionViewAtIndex(idx, ListView.Center);
            }
        }

        property var filteredList: picker.cleanList

        function updateFilter(query) {
            var q = query.trim().toLowerCase();
            if (!q || q === "") {
                filteredList = picker.cleanList;
            } else {
                var res = [];
                for (var i = 0; i < picker.cleanList.length; i++) {
                    var f = picker.cleanList[i];
                    if (f.toLowerCase().indexOf(q) !== -1) {
                        res.push(f);
                    }
                }
                filteredList = res;
            }
        }

        contentItem: ColumnLayout {
            spacing: 6

            QQC2.TextField {
                id: searchField
                Layout.fillWidth: true
                placeholderText: i18n("Search fonts...")
                selectByMouse: true

                onTextChanged: {
                    fontPopup.updateFilter(text);
                }
            }

            Kirigami.Separator {
                Layout.fillWidth: true
            }

            ListView {
                id: fontView
                Layout.fillWidth: true
                Layout.preferredHeight: count === 0 ? 0 : Math.min(8, count) * 32
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                model: fontPopup.filteredList

                delegate: QQC2.ItemDelegate {
                    id: delegateItem
                    width: fontView.width
                    height: 32
                    highlighted: modelData === picker.currentFont
                    leftPadding: 10
                    rightPadding: fontView.count > 8 ? 24 : 10

                    contentItem: RowLayout {
                        spacing: 8

                        QQC2.Label {
                            text: modelData
                            font.family: modelData
                            font.pixelSize: 13
                            font.weight: delegateItem.highlighted ? Font.Bold : Font.Normal
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                            verticalAlignment: Text.AlignVCenter
                            color: delegateItem.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                        }

                        Kirigami.Icon {
                            source: "dialog-ok"
                            implicitWidth: 14
                            implicitHeight: 14
                            visible: delegateItem.highlighted
                            color: Kirigami.Theme.highlightedTextColor
                        }
                    }

                    onClicked: {
                        picker.currentFont = modelData;
                        fontPopup.close();
                    }
                }

                QQC2.ScrollBar.vertical: QQC2.ScrollBar {
                    policy: fontView.count > 8 ? QQC2.ScrollBar.AlwaysOn : QQC2.ScrollBar.AsNeeded
                }
            }

            QQC2.Label {
                visible: fontView.count === 0
                text: i18n("No matching fonts")
                color: Kirigami.Theme.disabledTextColor
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                Layout.fillWidth: true
                Layout.preferredHeight: 36
            }
        }
    }
}
