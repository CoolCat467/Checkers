"""Sound - Play sounds."""

# Programmed by CoolCat467

from __future__ import annotations

# Sound - Play sounds
# Copyright (C) 2024  CoolCat467
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__title__ = "sound"
__author__ = "CoolCat467"
__version__ = "0.0.0"
__license__ = "GNU General Public License Version 3"


from typing import TYPE_CHECKING, NamedTuple

from pygame import mixer

if TYPE_CHECKING:
    from os import PathLike


class SoundData(NamedTuple):
    """Sound data container."""

    loops: int = 0
    maxtime: int = 0
    fade_ms: int = 0
    volume: int = 100
    # volume_left: int = 100
    # volume_right: int = 100


def play_sound(  # pragma: nocover
    filename: PathLike[str] | str,
    sound_data: SoundData,
) -> tuple[mixer.Sound, int | float]:
    """Play sound with pygame."""
    sound_object = mixer.Sound(filename)
    sound_object.set_volume(sound_data.volume)
    seconds: int | float = sound_object.get_length()
    if sound_data.maxtime > 0:
        seconds = sound_data.maxtime
    _channel = sound_object.play(
        loops=sound_data.loops,
        maxtime=sound_data.maxtime,
        fade_ms=sound_data.fade_ms,
    )
    # channel.set_volume(
    # sound_data.volume_left,
    # sound_data.volume_right,
    # )
    return sound_object, seconds
