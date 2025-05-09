from datetime import datetime
from functools import cache

import vlc
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QSlider, QLabel, QHBoxLayout, QToolButton, QSizePolicy
from typing_extensions import Literal

from music_downloader.vlc_core import VLCCore


def timestamp_to_str(timestamp: int):
    return datetime.fromtimestamp(timestamp).strftime("%M:%S")


class MediaScrubberSlider(QHBoxLayout):
    def __init__(self, core: VLCCore):
        super().__init__()
        self.core = core

        self.before_label = QLabel()
        self.after_label = QLabel()

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setTracking(True)
        self.slider.valueChanged.connect(self._update_before_label)
        self.slider.sliderReleased.connect(self.set_media_position)
        self.slider.setValue(0)

        self.addWidget(self.before_label)
        self.addWidget(self.slider)
        self.addWidget(self.after_label)

        self._update_before_label()
        self._update_after_label()

    def get_current_media_duration(self):
        return self.core.current_media.get_duration() / 1000

    @Slot()
    def _update_before_label(self, current_second: int | None = None):
        if current_second is None:
            current_second = round(self.core.media_player.get_time() / 1000)
        self.before_label.setText(timestamp_to_str(current_second))

    def _update_after_label(self):
        self.after_label.setText(timestamp_to_str(self.get_current_media_duration()))

    def update_ui_live(self, event: vlc.Event):
        new_time: float = event.u.new_time / 1000
        new_slider_position = new_time / self.get_current_media_duration() * 100
        self.slider.setValue(new_slider_position)  # TODO: BLOCK valueChanged signal!
        self._update_before_label(round(new_time))

    def update_ui_song_changed(self):
        self._update_after_label()

    @Slot()
    def set_media_position(self):
        self.core.media_player.set_position(self.slider.value() / 100)


VOLUME_ICONS = Literal["VOLUME_MUTED", "VOLUME_OFF", "VOLUME_MAX", "VOLUME_MIN"]


@cache
def get_volume_icons() -> dict[VOLUME_ICONS, QIcon]:
    return {
        "VOLUME_MUTED": QIcon("../icons/volume/volume-mute.svg"),
        "VOLUME_OFF": QIcon("../icons/volume/volume-off.svg"),
        "VOLUME_MAX": QIcon("../icons/volume/volume-max.svg"),
        "VOLUME_MIN": QIcon("../icons/volume/volume-min.svg"),
    }


class VolumeSlider(QHBoxLayout):
    def __init__(self, core: VLCCore, parent: QWidget):
        super().__init__(parent)
        self.core = core
        current_volume = self.core.media_player.audio_get_volume()
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.volume_slider.setMaximumWidth(200)
        self.volume_slider.setTracking(True)
        self.volume_slider.setValue(current_volume)
        self.volume_slider.setMaximum(100)
        self.volume_slider.valueChanged.connect(self.update_volume)

        self.volume_button: QToolButton = QToolButton()
        self.volume_button.setCheckable(True)
        self.volume_button.toggled.connect(self.toggle_volume_button)
        self.update_volume(current_volume)

        self.addWidget(self.volume_button)
        self.addWidget(self.volume_slider)

    @Slot()
    def update_volume(self, new_volume: int):
        assert self.core.media_player.audio_set_volume(new_volume) != -1
        if self.volume_button.isChecked():
            self.volume_button.setIcon(get_volume_icons()["VOLUME_MUTED"])
        elif new_volume == 0:
            self.volume_button.setIcon(get_volume_icons()["VOLUME_OFF"])
        elif new_volume == 100:
            self.volume_button.setIcon(get_volume_icons()["VOLUME_MAX"])
        else:
            self.volume_button.setIcon(get_volume_icons()["VOLUME_MIN"])

    @Slot()
    def toggle_volume_button(self):
        if self.volume_button.isChecked():
            self.update_volume(0)
            self.volume_slider.setEnabled(False)
        else:
            self.update_volume(self.volume_slider.value())
            self.volume_slider.setEnabled(True)
