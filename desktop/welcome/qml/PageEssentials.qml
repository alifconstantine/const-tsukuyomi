pragma ComponentBehavior: Bound

import QtQuick
import "Singletons"

Item {
    id: root
    implicitHeight: contents.implicitHeight

    signal runCommand(var argv)

    readonly property var essentials: [
        { chord: "Super + Space", title: "Launcher", description: "Find and open applications.", command: ["dms", "ipc", "call", "spotlight", "toggle"] },
        { chord: "Super + Return", title: "Terminal", description: "Open Kitty with Fish.", command: ["kitty"] },
        { chord: "Super + B", title: "Web browser", description: "Open your default browser.", command: ["constos-browser"] },
        { chord: "Super + E", title: "Files", description: "Browse your files in Nautilus.", command: ["nautilus"] },
        { chord: "Super + N", title: "Text editor", description: "Open Mousepad.", command: ["mousepad"] },
        { chord: "Super + comma", title: "Settings", description: "Personalise Dux Shell and your desktop.", command: ["dms", "ipc", "call", "settings", "focusOrToggle"] },
        { chord: "Super + Esc", title: "Quick settings", description: "Network, volume and session controls.", command: ["dms", "ipc", "call", "control-center", "toggle"] },
        { chord: "Super + Q", title: "Close window", description: "Close the focused application.", command: [] },
        { chord: "Super + 1–0", title: "Workspaces", description: "Switch workspace; add Shift to move a window.", command: [] },
        { chord: "Super + Tab", title: "Workspace overview", description: "See and select open windows.", command: ["dms", "ipc", "call", "hypr", "toggleOverview"] },
        { chord: "Super + ↑↓←→", title: "Window focus", description: "Focus a tile; add Shift to move it. Alt + Tab returns to the last window.", command: [] },
        { chord: "Super + F", title: "Fullscreen", description: "Toggle fullscreen and return to your tiles.", command: [] },
        { chord: "Super + Shift + S", title: "Screenshot", description: "Select an area. Print also selects an area; Alt + Print captures the screen.", command: ["constos-screenshot", "region"] }
    ]

    Column {
        id: contents
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: Tokens.s4

        PageTitle {
            width: parent.width
            title: qsTr("The keys that matter")
            description: qsTr("Super is the Windows key on most keyboards. Click a card or use Tab and Enter to try an action.")
        }

        Flow {
            id: list
            width: parent.width
            spacing: Tokens.s2

            Repeater {
                model: root.essentials

                ActionKey {
                    required property var modelData
                    width: list.width < 760 ? list.width : Math.floor((list.width - list.spacing) / 2)
                    chord: modelData.chord
                    title: modelData.title
                    description: modelData.description
                    command: modelData.command
                    onRunCommand: argv => root.runCommand(argv)
                }
            }
        }
    }
}
