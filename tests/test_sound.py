from checkers.sound import SoundData


def test_sound_data() -> None:
    sound = SoundData(3)
    assert sound.loops == 3
