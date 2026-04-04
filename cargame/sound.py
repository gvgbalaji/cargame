"""
Sound effects — uses pygame.mixer when available, falls back to wav+aplay.
"""

import io
import math
import random
import struct
import subprocess
import tempfile
import wave

# Try to use pygame.mixer for better audio
_use_pygame_mixer = False
try:
    import pygame.mixer
    _use_pygame_mixer = True
except ImportError:
    pass

# ── Module-level sound config ────────────────────────────────────
_enabled: bool = True
_theme: str = "engine"


def set_sound_config(enabled: bool, theme: str) -> None:
    global _enabled, _theme
    _enabled = enabled
    _theme = theme


def init_mixer():
    """Initialize pygame mixer if available."""
    global _use_pygame_mixer
    if _use_pygame_mixer:
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        except Exception:
            _use_pygame_mixer = False


def _play_wav(samples: list[int], rate: int = 22050) -> None:
    """Play samples as audio."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    if _use_pygame_mixer:
        try:
            buf.seek(0)
            sound = pygame.mixer.Sound(buf)
            sound.play()
            return
        except Exception:
            pass

    # Fallback to aplay/afplay
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


# ── Crash sound variants ─────────────────────────────────────────

def _crash_crunch() -> None:
    RATE = 22050
    n = int(RATE * 0.65)
    rng = random.Random(0)
    raw = []
    for i in range(n):
        t = i / RATE
        if t < 0.15:
            s = rng.uniform(-1, 1) * (1 - t / 0.15) ** 0.4 * 0.9
        else:
            freq = 150 * math.exp(-(t - 0.15) * 3)
            s = (math.sin(2 * math.pi * freq * t)
                 * math.exp(-(t - 0.15) * 7) * 0.8)
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


def _crash_boom() -> None:
    RATE = 22050
    n = int(RATE * 0.8)
    raw = []
    for i in range(n):
        t = i / RATE
        s = math.sin(2 * math.pi * 60.0 * t) * math.exp(-t * 4.0) * 0.9
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


def _crash_screech() -> None:
    RATE = 22050
    n = int(RATE * 0.5)
    rng = random.Random(2)
    raw = []
    phase_acc = 0.0
    for i in range(n):
        t = i / RATE
        p = t / 0.5
        freq = 800 - 600 * p
        phase_acc = (phase_acc + freq / RATE) % 1.0
        tone = math.sin(2 * math.pi * phase_acc)
        noise = rng.uniform(-1, 1) * 0.3
        amp = (1.0 - p) ** 0.5
        s = (tone * 0.7 + noise) * amp * 0.85
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


# ── Pass sound variants ──────────────────────────────────────────

def _pass_engine() -> None:
    RATE = 22050
    dur = 0.20
    n = int(RATE * dur)
    rng = random.Random(1)
    raw = []
    phase_acc = 0.0
    for i in range(n):
        t = i / RATE
        p = t / dur
        freq = 140 - 70 * p
        phase_acc = (phase_acc + freq / RATE) % 1.0
        buzz = 2 * phase_acc - 1
        noise = rng.uniform(-1, 1) * 0.25
        if p < 0.08:
            amp = p / 0.08
        elif p > 0.80:
            amp = (1.0 - p) / 0.20
        else:
            amp = 1.0
        s = (buzz * 0.65 + noise) * amp * 0.75
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


def _pass_beep() -> None:
    RATE = 22050
    nb = int(RATE * 0.08)
    raw = []
    for freq in (880, 660):
        for i in range(nb):
            p = i / nb
            amp = math.sin(math.pi * p)
            s = math.sin(2 * math.pi * freq * i / RATE) * amp * 0.8
            raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


def _pass_whoosh() -> None:
    RATE = 22050
    n = int(RATE * 0.15)
    rng = random.Random(3)
    raw = []
    for i in range(n):
        p = i / n
        amp = math.sin(math.pi * p) ** 0.5
        s = rng.uniform(-1, 1) * amp * 0.9
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


# ── Lane-switch sound variants ───────────────────────────────────

def _lane_engine() -> None:
    RATE = 22050
    n = int(RATE * 0.10)
    rng = random.Random(7)
    raw = []
    for i in range(n):
        p = i / n
        amp = (1.0 - p) ** 1.5
        s = rng.uniform(-1, 1) * amp * 0.55
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


def _lane_retro() -> None:
    RATE = 22050
    n = int(RATE * 0.06)
    raw = []
    for i in range(n):
        p = i / n
        amp = math.sin(math.pi * p)
        s = math.sin(2 * math.pi * 440 * i / RATE) * amp * 0.7
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


def _lane_minimal() -> None:
    RATE = 22050
    n = int(RATE * 0.08)
    rng = random.Random(11)
    raw = []
    for i in range(n):
        p = i / n
        amp = math.sin(math.pi * p) ** 0.7
        s = rng.uniform(-1, 1) * amp * 0.45
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


# ── Public API ───────────────────────────────────────────────────

def play_crash_sound() -> None:
    if not _enabled:
        return
    try:
        {"retro": _crash_boom, "minimal": _crash_screech}.get(
            _theme, _crash_crunch)()
    except Exception:
        pass


def play_lane_switch_sound() -> None:
    if not _enabled:
        return
    try:
        {"retro": _lane_retro, "minimal": _lane_minimal}.get(
            _theme, _lane_engine)()
    except Exception:
        pass


def play_pass_sound() -> None:
    if not _enabled:
        return
    try:
        {"retro": _pass_beep, "minimal": _pass_whoosh}.get(
            _theme, _pass_engine)()
    except Exception:
        pass
