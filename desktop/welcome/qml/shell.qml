pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import Quickshell
import "Singletons"

ShellRoot {
    id: app
    Component.onCompleted: Quickshell.watchFiles = false
    FloatingWindow {
        id: win
        title: "Welcome to Tsukuyomi"
        implicitWidth: 1080
        implicitHeight: 680
        minimumSize: Qt.size(640, 480)
        color: Tokens.paper
        onClosed: Qt.quit()
        Rectangle {
            anchors.fill: parent
            color: Tokens.paper
            focus: true
            Keys.onEscapePressed: Qt.quit()
            Column {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 18
                Row {
                    width: parent.width
                    spacing: 12
                    Text {
                        text: "TSUKUYOMI"
                        color: Tokens.lineStrong
                        font.family: "JetBrains Mono"
                        font.pixelSize: 13
                        font.letterSpacing: 3
                    }
                    Text {
                        text: " /  DESKTOP ESSENTIALS"
                        color: Tokens.inkMuted
                        font.pixelSize: 12
                    }
                }
                Rectangle { width: parent.width; height: 1; color: Tokens.line }
                ScrollView {
                    id: guideScroll
                    width: parent.width
                    height: parent.height - 144
                    clip: true
                    contentWidth: availableWidth
                    PageEssentials {
                        width: guideScroll.availableWidth
                        height: implicitHeight
                        onRunCommand: argv => Quickshell.execDetached(argv)
                    }
                }
                Row {
                    width: parent.width
                    spacing: 16
                    Text {
                        width: parent.width - 180
                        text: "Super + L  ·  Lock    /    Super + Shift + M  ·  Log out\nReopen this guide from the app launcher: Welcome."
                        color: Tokens.inkMuted
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }
                    Button {
                        text: "Start exploring"
                        onClicked: Qt.quit()
                        contentItem: Text { text: parent.text; color: Tokens.ink; font.pixelSize: 14; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        background: Rectangle { radius: 8; color: parent.down ? "#54232f" : "#792e40"; border.color: parent.activeFocus ? "#ffdae0" : "#c66b76"; border.width: 1 }
                        padding: 12
                    }
                }
            }
        }
    }
}
