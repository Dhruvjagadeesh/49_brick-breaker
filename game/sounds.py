import math
from array import array
import pygame

SAMPLE_RATE = 22050


def _tone(freqs, duration=0.08, volume=0.4):
    """Build a short square-ish beep (one or more notes in sequence) without audio files."""
    samples = array("h")
    per_note = int(SAMPLE_RATE * duration)
    for f in freqs:
        for i in range(per_note):
            fade = 1 - i / per_note  # quick decay so it doesn't click
            val = 1 if math.sin(2 * math.pi * f * i / SAMPLE_RATE) > 0 else -1
            samples.append(int(val * volume * fade * 32767))
    return pygame.mixer.Sound(buffer=samples.tobytes())


class Sounds:
    def __init__(self):
        self.enabled = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
            self.brick = _tone([880], 0.06)
            self.paddle = _tone([440], 0.06)
            self.wall = _tone([300], 0.04, 0.25)
            self.win = _tone([523, 659, 784, 1047], 0.15)
            self.lose = _tone([392, 330, 262, 196], 0.18)
        except pygame.error:
            self.enabled = False  # no audio device: play silently

    def play(self, name):
        if self.enabled:
            getattr(self, name).play()
