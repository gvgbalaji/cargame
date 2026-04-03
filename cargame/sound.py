"""
Sound effects generated at runtime using stdlib only (wave, struct).
Played non-blocking via aplay (Linux) or afplay (macOS).
Silently no-ops when audio tools are unavailable.
"""

import io
import math
import random
import struct
import subprocess
import tempfile
import wave


def _play_wav(samples: list[int], rate: int = 22050) -> None:
    """Encode samples as a WAV and fire-and-forget via aplay/afplay."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(buf.getvalue())
        path = f.name

    for cmd in (["aplay", "-q", path], ["afplay", path]):
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return
        except FileNotFoundError:
            continue


def play_crash_sound() -> None:
    """Noise burst + descending rumble on collision."""
    try:
        RATE = 22050
        n    = int(RATE * 0.65)
        rng  = random.Random(0)
        raw  = []
        for i in range(n):
            t = i / RATE
            if t < 0.15:
                s = rng.uniform(-1, 1) * (1 - t / 0.15) ** 0.4 * 0.9
            else:
                freq = 150 * math.exp(-(t - 0.15) * 3)
                s    = (math.sin(2 * math.pi * freq * t)
                        * math.exp(-(t - 0.15) * 7) * 0.8)
            raw.append(int(max(-32767, min(32767, s * 32767))))
        _play_wav(raw, RATE)
    except Exception:
        pass


def play_pass_sound() -> None:
    """Short ascending chirp when a car is successfully dodged."""
    try:
        RATE = 22050
        n    = int(RATE * 0.12)
        raw  = []
        for i in range(n):
            t    = i / RATE
            freq = 440 + 440 * (t / 0.12)
            amp  = 0.5 * (1 - t / 0.12) ** 0.5
            raw.append(int(max(-32767, min(32767,
                        math.sin(2 * math.pi * freq * t) * amp * 32767))))
        _play_wav(raw, RATE)
    except Exception:
        pass
