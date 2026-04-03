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
    """'Zrrrr' engine buzz with Doppler drop as enemy car rushes past."""
    try:
        RATE = 22050
        dur  = 0.20
        n    = int(RATE * dur)
        rng  = random.Random(1)
        raw  = []
        phase_acc = 0.0
        for i in range(n):
            t = i / RATE
            p = t / dur                          # 0 → 1 progress

            # Doppler: pitch higher as car approaches, drops as it passes
            freq      = 140 - 70 * p            # 140 Hz → 70 Hz
            phase_acc = (phase_acc + freq / RATE) % 1.0

            # Sawtooth wave — gives the raw "rrr" engine buzz texture
            buzz  = 2 * phase_acc - 1

            # Light broadband noise for the wind/tyre hiss layer
            noise = rng.uniform(-1, 1) * 0.25

            # Amplitude envelope: fast attack, sustain, fast fade
            if p < 0.08:
                amp = p / 0.08
            elif p > 0.80:
                amp = (1.0 - p) / 0.20
            else:
                amp = 1.0

            s = (buzz * 0.65 + noise) * amp * 0.75
            raw.append(int(max(-32767, min(32767, s * 32767))))
        _play_wav(raw, RATE)
    except Exception:
        pass
