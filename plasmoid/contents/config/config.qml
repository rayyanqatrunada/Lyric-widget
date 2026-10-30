import QtQuick
import org.kde.plasma.configuration

ConfigModel {
    ConfigCategory {
        name: i18n("Components")
        icon: "preferences-desktop-display"
        source: "configComponents.qml"
    }

    ConfigCategory {
        name: i18n("Typography")
        icon: "preferences-desktop-font"
        source: "configFonts.qml"
    }

    ConfigCategory {
        name: i18n("Background")
        icon: "preferences-desktop-wallpaper"
        source: "configBackground.qml"
    }
}
