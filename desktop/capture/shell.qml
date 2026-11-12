pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

ShellRoot {
    id: root

    property string page: "shot"
    property string operation: ""
    property string message: ""
    property string preview: ""
    property string saved: ""
    property bool hidePanel: false
    property var inputs: []
    property var recording: ({})
    property int seconds: 0
    readonly property bool audioActive: ["starting", "recording", "finalizing"].includes(recording.phase)
    readonly property string runtime: Quickshell.env("XDG_RUNTIME_DIR") + "/constos-capture/"
    readonly property string backend: "/usr/bin/constos-capture"

    function execute(op, args) {
        if (operation.length)
            return;
        operation = op;
        message = "";
        task.command = args;
        task.running = true;
    }

    function shot(mode) {
        if (operation.length || audioActive)
            return;
        hidePanel = true;
        shotDelay.mode = mode;
        shotDelay.start();
    }

    function close() {
        if (!audioActive && !operation.length)
            Qt.quit();
    }

    function refreshPreview() {
        preview = "";
        preview = "file://" + runtime + "preview.png";
    }

    function parse(value, fallback) {
        try { return JSON.parse(value); } catch (_) { return fallback; }
    }

    Component.onCompleted: statusCheck.running = true

    Timer {
        id: shotDelay
        property string mode
        interval: 450
        onTriggered: root.execute("grab", [root.backend, "grab", mode])
    }

    Timer {
        interval: 500
        repeat: true
        running: root.page === "audio" || root.audioActive
        onTriggered: if (!statusCheck.running) statusCheck.running = true
    }

    Process {
        id: statusCheck
        command: [root.backend, "status"]
        stdout: StdioCollector {
            onStreamFinished: {
                root.recording = root.parse(text, {});
                root.seconds = root.recording.started
                    ? Math.max(0, Math.floor(Date.now() / 1000) - root.recording.started) : 0;
                if (root.audioActive)
                    root.page = "audio";
            }
        }
    }

    Process {
        id: task
        stdout: StdioCollector { id: output }
        stderr: StdioCollector { id: errors }
        onExited: (code, status) => {
            const op = root.operation;
            root.operation = "";
            root.hidePanel = false;
            if (code !== 0) {
                if (code !== 2)
                    root.message = errors.text.trim().split("\n").pop() || "The action failed.";
                return;
            }
            if (op === "grab" || op === "edit") {
                root.saved = "";
                root.refreshPreview();
            } else if (op === "copy") {
                root.message = "Copied to clipboard";
            } else if (op === "save") {
                root.saved = output.text.trim();
                root.message = "Screenshot saved";
            } else if (op === "sources") {
                root.inputs = root.parse(output.text, []);
                input.currentIndex = root.inputs.length === 1 ? 0 : -1;
            } else if (op === "start" || op === "stop") {
                if (!statusCheck.running)
                    statusCheck.running = true;
            }
        }
    }

    component Action: Button {
        id: button
        implicitHeight: 36
        implicitWidth: Math.max(54, label.implicitWidth + 24)
        contentItem: Text {
            id: label
            text: button.text
            color: button.enabled ? "#f5eff2" : "#a3919a"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 9
            color: button.down ? "#683747" : button.hovered ? "#492938" : "#271b23"
            border.color: button.activeFocus ? "#e493a8" : "#58404d"
        }
    }

    PanelWindow {
        id: panel
        visible: !root.hidePanel
        anchors.top: true
        margins.top: 66
        readonly property int requestedWidth: root.page === "shot" && !root.preview && !root.message ? 360 : 640
        implicitWidth: Math.min(requestedWidth, screen ? screen.width - 24 : requestedWidth)
        implicitHeight: contents.implicitHeight + 24
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: WlrLayer.Top
        WlrLayershell.namespace: "constos-capture"
        WlrLayershell.keyboardFocus: root.audioActive
            ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.Exclusive

        Rectangle {
            anchors.fill: parent
            color: "#161016"
            radius: 15
            border.color: "#654454"

            FocusScope {
                anchors.fill: parent
                focus: true
                Keys.onEscapePressed: root.close()

                ColumnLayout {
                    id: contents
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
                    spacing: 9

                    RowLayout {
                        Layout.fillWidth: true
                        Action { text: "Area"; enabled: !root.operation && !root.audioActive; onClicked: root.page = "shot", root.shot("region") }
                        Action { text: "Screen"; enabled: !root.operation && !root.audioActive; onClicked: root.page = "shot", root.shot("screen") }
                        Action {
                            text: "Record audio"
                            enabled: !root.operation
                            onClicked: {
                                root.page = "audio";
                                if (!root.audioActive)
                                    root.execute("sources", [root.backend, "sources"]);
                            }
                        }
                        Item { Layout.fillWidth: true }
                        Action { text: "Close"; enabled: !root.audioActive && !root.operation; onClicked: root.close() }
                    }

                    Image {
                        visible: root.page === "shot" && root.preview.length > 0
                        Layout.fillWidth: true
                        Layout.preferredHeight: visible ? Math.min(320, panel.screen.height * 0.4) : 0
                        source: root.preview
                        fillMode: Image.PreserveAspectFit
                        cache: false
                    }

                    RowLayout {
                        visible: root.page === "shot" && root.preview.length > 0
                        Action { text: "Copy"; enabled: !root.operation; onClicked: root.execute("copy", [root.backend, "copy"]) }
                        Action { text: "Save PNG"; enabled: !root.operation; onClicked: root.execute("save", [root.backend, "save"]) }
                        Action {
                            text: "Annotate"
                            enabled: !root.operation
                            onClicked: {
                                root.hidePanel = true;
                                root.execute("edit", [root.backend, "edit"]);
                            }
                        }
                        Action {
                            text: "Open folder"
                            visible: root.saved.length > 0
                            onClicked: Quickshell.execDetached(["xdg-open", root.saved.slice(0, root.saved.lastIndexOf("/"))])
                        }
                    }

                    RowLayout {
                        visible: root.page === "audio" && !root.audioActive
                        Layout.fillWidth: true
                        ComboBox {
                            id: input
                            Layout.fillWidth: true
                            model: root.inputs
                            textRole: "label"
                            displayText: currentIndex < 0 ? "Choose a microphone or output"
                                : root.inputs[currentIndex].kind + " · " + currentText
                        }
                        Action {
                            text: "Refresh"
                            enabled: !root.operation
                            onClicked: root.execute("sources", [root.backend, "sources"])
                        }
                        Action {
                            text: "Start"
                            enabled: input.currentIndex >= 0 && !root.operation
                            onClicked: root.execute("start", ["systemctl", "--user", "start",
                                "constos-audio@" + root.inputs[input.currentIndex].serial + ".service"])
                        }
                    }

                    RowLayout {
                        visible: root.page === "audio"
                        Layout.fillWidth: true
                        Text {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: root.recording.phase === "recording" ? "#ff9aaf" : "#dbc8d1"
                            text: root.recording.phase === "recording"
                                ? "● " + Math.floor(root.seconds / 60) + ":" + String(root.seconds % 60).padStart(2, "0") + "  " + root.recording.source
                                : root.recording.phase === "starting" ? "Connecting to the selected source…"
                                : root.recording.phase === "finalizing" ? "Finalizing audio…"
                                : root.recording.phase === "completed" ? "Recording saved"
                                : root.recording.phase === "failed" ? root.recording.message
                                : root.inputs.length === 0 && !root.operation ? "No audio sources available" : ""
                        }
                        Action {
                            text: "Stop"
                            visible: root.audioActive
                            enabled: !root.operation && root.recording.phase !== "finalizing"
                            onClicked: root.execute("stop", [root.backend, "stop"])
                        }
                        Action {
                            text: root.recording.phase === "failed" ? "Open partial" : "Play"
                            visible: !root.audioActive && !!root.recording.path
                            onClicked: Quickshell.execDetached(["xdg-open", root.recording.path])
                        }
                    }

                    Text {
                        visible: text.length > 0
                        Layout.fillWidth: true
                        color: "#dbc8d1"
                        wrapMode: Text.WordWrap
                        text: root.message
                    }
                }
            }
        }
    }
}
