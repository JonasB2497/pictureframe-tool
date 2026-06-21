import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: window
    Component.onCompleted: {
        const margins = 2 * layoutRoot.anchors.margins
        width = layoutRoot.implicitWidth * 1.5 + margins
        height = layoutRoot.implicitHeight + margins + 30
        minimumWidth = width
        minimumHeight = height
        maximumWidth = width
        maximumHeight = height
    }
    onWidthChanged: {
        if (minimumWidth !== width) minimumWidth = width
        if (maximumWidth !== width) maximumWidth = width
    }
    onHeightChanged: {
        if (minimumHeight !== height) minimumHeight = height
        if (maximumHeight !== height) maximumHeight = height
    }
    visible: true
    title: qsTr("Generator")

    property string inputDirectory: ""
    property string outputDirectory: ""

    ColumnLayout {
        id: layoutRoot
        anchors.fill: parent
        anchors.margins: 5

        TabBar {
            id: tab_bar
            Layout.fillWidth: true
            TabButton {
                text: qsTr("Directories")
            }
            TabButton {
                text: qsTr("Display Configuration")
            }
        }

        StackLayout {
            id: stack_layout
            currentIndex: tab_bar.currentIndex
            ColumnLayout {
                Label {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: deviceConfiguration.count > 0
                        ? qsTr("Device: %1 (%2x%3)")
                          .arg(deviceConfiguration.currentName)
                          .arg(deviceConfiguration.currentWidth)
                          .arg(deviceConfiguration.currentHeight)
                        : qsTr("No device selected")
                }

                // Input directory
                Label {
                    text: qsTr("Input Directory")
                }

                RowLayout {
                    Layout.fillWidth: true

                    TextField {
                        Layout.fillWidth: true
                        readOnly: true
                        placeholderText: qsTr("Select input directory...")
                        text: deviceConfiguration.lastInputDirectory
                        onTextChanged: deviceConfiguration.lastInputDirectory = text
                    }

                    Button {
                        text: qsTr("Browse")
                        onClicked: inputDirDialog.open()
                    }
                }

                // Output directory
                Label {
                    text: qsTr("Output Directory")
                }

                RowLayout {
                    Layout.fillWidth: true

                    TextField {
                        Layout.fillWidth: true
                        readOnly: true
                        placeholderText: qsTr("Select output directory...")
                        text: deviceConfiguration.lastOutputDirectory
                        onTextChanged: deviceConfiguration.lastOutputDirectory = text
                    }

                    Button {
                        text: qsTr("Browse")
                        onClicked: outputDirDialog.open()
                    }
                }

                // Generate button
                Button {
                    text: qsTr("Generate")
                    Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom
                    onClicked: {
                        generateDialog.open()
                    }
                }

                ProgressBar {
                    Layout.fillWidth: true
                    from: 0.0
                    to: 1.0
                    value: deviceConfiguration.progress
                }
            }

            ColumnLayout {
                // Device dropdown
                Label {
                    text: qsTr("Device")
                }

                RowLayout {
                    Layout.fillWidth: true

                    ComboBox {
                        id: deviceCombo
                        Layout.fillWidth: true
                        model: deviceConfiguration
                        textRole: "name"
                        currentIndex: deviceConfiguration.currentIndex
                        onActivated: deviceConfiguration.currentIndex = currentIndex
                    }

                    Button {
                        text: "+"
                        padding: 0
                        ToolTip.text: qsTr("Add device configuration")
                        ToolTip.visible: hovered
                        ToolTip.delay: 500
                        onClicked: deviceConfiguration.addDevice()
                    }

                    Button {
                        text: "-"
                        padding: 0
                        enabled: deviceConfiguration.count > 1
                        ToolTip.text: qsTr("Remove selected device configuration")
                        ToolTip.visible: hovered
                        ToolTip.delay: 500
                        onClicked: deviceConfiguration.removeCurrentDevice()
                    }
                }

                // Name field
                Label {
                    text: qsTr("Name")
                }

                RowLayout {
                    Layout.fillWidth: true

                    TextField {
                        id: deviceNameField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Device name...")
                        text: deviceConfiguration.currentName
                        onTextEdited: deviceConfiguration.updateDevice(deviceCombo.currentIndex, text, parseInt(deviceWidthField.text), parseInt(deviceHeightField.text))
                    }
                }

                // Width field
                Label {
                    text: qsTr("Width")
                }

                RowLayout {
                    Layout.fillWidth: true

                    TextField {
                        id: deviceWidthField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Enter width...")
                        text: deviceConfiguration.currentWidth
                        validator: IntValidator { bottom: 1 }
                        onTextEdited: deviceConfiguration.updateDevice(deviceCombo.currentIndex, deviceNameField.text, parseInt(text), parseInt(deviceHeightField.text))
                    }
                }

                Label {
                    text: qsTr("Height")
                }

                RowLayout {
                    Layout.fillWidth: true

                    TextField {
                        id: deviceHeightField
                        Layout.fillWidth: true
                        placeholderText: qsTr("Enter height...")
                        text: deviceConfiguration.currentHeight
                        validator: IntValidator { bottom: 1 }
                        onTextEdited: deviceConfiguration.updateDevice(deviceCombo.currentIndex, deviceNameField.text, parseInt(deviceWidthField.text), parseInt(text))
                    }
                }
            }
        }
    }

    // Input directory dialog
    FolderDialog {
        id: inputDirDialog
        title: qsTr("Select Input Directory")
        onAccepted: {
            deviceConfiguration.lastInputDirectory = selectedFolder
        }
    }

    // Output directory dialog
    FolderDialog {
        id: outputDirDialog
        title: qsTr("Select Output Directory")
        onAccepted: {
            deviceConfiguration.lastOutputDirectory = selectedFolder
        }
    }

    // Generate warning dialog
    MessageDialog {
        id: generateDialog
        title: qsTr("Confirm Generate")
        text: qsTr("The content of the output folder will be irreversibly deleted.")
        buttons: MessageDialog.Yes | MessageDialog.No
        onButtonClicked: function(button, role) {
            if (role === MessageDialog.YesRole) {
                deviceConfiguration.generate(deviceConfiguration.lastInputDirectory,
                         deviceConfiguration.lastOutputDirectory,
                         deviceConfiguration.currentWidth,
                         deviceConfiguration.currentHeight)
            }
        }
    }

    // Done notification dialog
    MessageDialog {
        id: doneDialog
        title: qsTr("Done")
        text: qsTr("Processing completed successfully.")
        buttons: MessageDialog.Ok
    }

    Connections {
        target: deviceConfiguration
        function onFinished() {
            doneDialog.open()
        }
    }
}
