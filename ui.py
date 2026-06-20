import json
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse
import os

from converter import process

from PySide6.QtCore import (
    QAbstractListModel,
    QByteArray,
    QModelIndex,
    Qt,
    Signal,
    Property,
    Slot,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


CONFIG_FILE = Path(os.path.join(os.path.expanduser("~"), ".config/pictureframe-tool"))


@dataclass(frozen=True)
class Screen:
    width: int
    height: int


@dataclass
class Device:
    name: str
    screen: Screen


def _default_devices() -> List[Device]:
    return [
        Device(name="16:9 FHD", screen=Screen(1920, 1080)),
        Device(name="16:10 WUXGA", screen=Screen(1920, 1200)),
        Device(name="4:3 XGA", screen=Screen(1024, 768)),
    ]


class DeviceConfiguration(QAbstractListModel):
    NameRole: int = Qt.UserRole + 1
    WidthRole: int = Qt.UserRole + 2
    HeightRole: int = Qt.UserRole + 3

    currentIndexChanged = Signal()
    currentNameChanged = Signal()
    currentWidthChanged = Signal()
    currentHeightChanged = Signal()
    countChanged = Signal()
    lastDeviceChanged = Signal()
    lastInputDirectoryChanged = Signal()
    lastOutputDirectoryChanged = Signal()
    progressChanged = Signal()
    finished = Signal()

    def __init__(
        self,
        devices: Optional[List[Device]] = None,
        last_device: Optional[str] = None,
        last_input_directory: Optional[str] = None,
        last_output_directory: Optional[str] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._devices: List[Device] = list(devices) if devices is not None else _default_devices()
        self._last_device: str = (
            last_device if last_device is not None else self._devices[0].name
        )
        self._current_index: int = self._index_for_name(self._last_device)
        if self._current_index < 0:
            self._current_index = 0
        self._last_input_directory: str = last_input_directory or ""
        self._last_output_directory: str = last_output_directory or ""
        self._progress: float = 0.0

    def roleNames(self):
        return {
            self.NameRole: QByteArray(b"name"),
            self.WidthRole: QByteArray(b"width"),
            self.HeightRole: QByteArray(b"height"),
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._devices)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._devices):
            return None
        device = self._devices[index.row()]
        if role in (self.NameRole, Qt.DisplayRole):
            return device.name
        if role == self.WidthRole:
            return device.screen.width
        if role == self.HeightRole:
            return device.screen.height
        return None

    def _current_device(self) -> Optional[Device]:
        if 0 <= self._current_index < len(self._devices):
            return self._devices[self._current_index]
        return None

    def _get_current_index(self) -> int:
        return self._current_index

    def _set_current_index(self, value: int) -> None:
        if 0 <= value < len(self._devices) and value != self._current_index:
            self._current_index = value
            self._last_device = self._devices[value].name
            self.currentIndexChanged.emit()
            self.currentNameChanged.emit()
            self.currentWidthChanged.emit()
            self.currentHeightChanged.emit()
            self.lastDeviceChanged.emit()
        elif 0 <= value < len(self._devices):
            self._last_device = self._devices[value].name
            self.lastDeviceChanged.emit()

    currentIndex = Property(
        int, _get_current_index, _set_current_index, notify=currentIndexChanged
    )

    def _get_current_name(self) -> str:
        device = self._current_device()
        return device.name if device is not None else ""

    def _get_current_width(self) -> int:
        device = self._current_device()
        return device.screen.width if device is not None else 0

    def _get_current_height(self) -> int:
        device = self._current_device()
        return device.screen.height if device is not None else 0

    currentName = Property(str, _get_current_name, notify=currentNameChanged)
    currentWidth = Property(int, _get_current_width, notify=currentWidthChanged)
    currentHeight = Property(int, _get_current_height, notify=currentHeightChanged)

    @Slot(int, str, int, int, result=bool)
    def updateDevice(self, row: int, name: str, width: int, height: int) -> bool:
        if not 0 <= row < len(self._devices):
            return False
        try:
            new_device = Device(
                name=str(name),
                screen=Screen(int(width), int(height)),
            )
        except (TypeError, ValueError):
            return False
        self._devices[row] = new_device
        top_left = self.index(row, 0)
        bottom_right = self.index(row, 0)
        self.dataChanged.emit(top_left, bottom_right,
                              [self.NameRole, self.WidthRole, self.HeightRole])
        if row == self._current_index:
            self.currentNameChanged.emit()
            self.currentWidthChanged.emit()
            self.currentHeightChanged.emit()
            if self._last_device != new_device.name:
                self._last_device = new_device.name
                self.lastDeviceChanged.emit()
        elif self._last_device == self._devices[row].name:
            self._last_device = new_device.name
            self.lastDeviceChanged.emit()
        return True

    def _get_count(self) -> int:
        return len(self._devices)

    count = Property(int, _get_count, notify=countChanged)

    def _get_last_device(self) -> str:
        return self._last_device

    def _index_for_name(self, name: str) -> int:
        for i, device in enumerate(self._devices):
            if device.name == name:
                return i
        return -1

    def _set_last_device(self, value: str) -> None:
        idx = self._index_for_name(value)
        if idx < 0:
            return
        self._last_device = value
        if idx != self._current_index:
            self._current_index = idx
            self.currentIndexChanged.emit()
            self.currentNameChanged.emit()
            self.currentWidthChanged.emit()
            self.currentHeightChanged.emit()
        self.lastDeviceChanged.emit()

    lastDevice = Property(
        str, _get_last_device, _set_last_device, notify=lastDeviceChanged
    )

    def _strip_file_prefix(self, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme == "file":
            return parsed.path
        return value

    def _get_last_input_directory(self) -> str:
        return self._last_input_directory

    def _set_last_input_directory(self, value) -> None:
        value = str(value) if value is not None else ""
        value = self._strip_file_prefix(value)
        if value != self._last_input_directory:
            self._last_input_directory = value
            self.lastInputDirectoryChanged.emit()

    lastInputDirectory = Property(
        str,
        _get_last_input_directory,
        _set_last_input_directory,
        notify=lastInputDirectoryChanged,
    )

    def _get_last_output_directory(self) -> str:
        return self._last_output_directory

    def _set_last_output_directory(self, value) -> None:
        value = str(value) if value is not None else ""
        value = self._strip_file_prefix(value)
        if value != self._last_output_directory:
            self._last_output_directory = value
            self.lastOutputDirectoryChanged.emit()

    lastOutputDirectory = Property(
        str,
        _get_last_output_directory,
        _set_last_output_directory,
        notify=lastOutputDirectoryChanged,
    )

    def _make_default_name(self) -> str:
        existing = {d.name for d in self._devices}
        base = "New Device"
        if base not in existing:
            return base
        i = 1
        while f"{base} {i}" in existing:
            i += 1
        return f"{base} {i}"

    @Slot(result=int)
    def addDevice(self) -> int:
        new_device = Device(
            name=self._make_default_name(),
            screen=Screen(1920, 1080),
        )
        row = len(self._devices)
        self.beginInsertRows(QModelIndex(), row, row)
        self._devices.append(new_device)
        self.endInsertRows()
        self.countChanged.emit()
        self._set_current_index(row)
        return row

    @Slot(result=bool)
    def removeCurrentDevice(self) -> bool:
        if len(self._devices) <= 1:
            return False
        row = self._current_index
        if not 0 <= row < len(self._devices):
            return False
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._devices[row]
        self.endRemoveRows()
        self.countChanged.emit()
        new_index = min(row, len(self._devices) - 1)
        self._set_current_index(new_index)
        return True

    @Slot()
    def save(self) -> None:
        if not self._last_device:
            self._last_device = self._devices[self._current_index].name
        payload = {
            "devices": [
                {
                    "name": d.name,
                    "screen": {"width": d.screen.width, "height": d.screen.height},
                }
                for d in self._devices
            ],
            "last_device": self._last_device,
            "last_input_directory": self._last_input_directory,
            "last_output_directory": self._last_output_directory,
        }
        CONFIG_FILE.write_text(json.dumps(payload, indent=2))

    @Slot(str, str, int, int)
    def generate(self, input_directory: str, output_directory: str, width: int, height: int) -> None:
        self._set_progress(0.0)

        def worker():
            try:
                process(input_directory, output_directory, width, height, "jpg", "", self._on_progress)
            finally:
                self.finished.emit()

        threading.Thread(target=worker).start()

    def _on_progress(self, current: int, total: int) -> None:
        if total <= 0:
            value = 0.0
        else:
            value = current / total
            if value < 0.0:
                value = 0.0
            elif value > 1.0:
                value = 1.0
        self._set_progress(value)

    def _set_progress(self, value: float) -> None:
        if value == self._progress:
            return
        self._progress = value
        self.progressChanged.emit()

    def _get_progress(self) -> float:
        return self._progress

    progress = Property(float, _get_progress, notify=progressChanged)


def _load_from_disk() -> Optional[tuple[List[Device], Optional[str], Optional[str], Optional[str]]]:
    if not CONFIG_FILE.is_file():
        return None
    try:
        raw = json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None

    items = raw.get("devices", [])
    last_device = raw.get("last_device")
    if last_device is not None and not isinstance(last_device, str):
        return None

    last_input_directory = raw.get("last_input_directory", "")
    last_output_directory = raw.get("last_output_directory", "")
    if not isinstance(last_input_directory, str) or not isinstance(last_output_directory, str):
        return None

    try:
        devices = [
            Device(
                name=str(item["name"]),
                screen=Screen(int(item["screen"]["width"]), int(item["screen"]["height"])),
            )
            for item in items
        ]
    except (KeyError, TypeError, ValueError):
        return None
    return devices, last_device, last_input_directory, last_output_directory


def main() -> int:
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.addImportPath(sys.path[0])

    loaded = _load_from_disk()
    if loaded is not None:
        devices, last_device, last_input_directory, last_output_directory = loaded
    else:
        devices = last_device = last_input_directory = last_output_directory = None
    config = DeviceConfiguration(
        devices=devices,
        last_device=last_device,
        last_input_directory=last_input_directory,
        last_output_directory=last_output_directory,
        parent=engine,
    )

    ctx = engine.rootContext()
    ctx.setContextProperty("deviceConfiguration", config)

    engine.loadFromModule("ui", "Main")
    if not engine.rootObjects():
        return -1

    app.aboutToQuit.connect(config.save)

    exit_code = app.exec()
    del engine
    sys.stdout.flush()
    sys.stderr.flush()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
