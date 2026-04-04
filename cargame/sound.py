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

# ── Module-level sound config ────────────────────────────────────
_enabled: bool = True
_theme: str = "engine"  # "engine" | "retro" | "minimal" | "silent"


def set_sound_config(enabled: bool, theme: str) -> None:
    global _enabled, _theme
    _enabled = enabled
    _theme = theme


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


# ── Crash sound variants ─────────────────────────────────────────

def _crash_crunch() -> None:
    """Noise burst + descending rumble on collision (original crash sound)."""
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


def _crash_boom() -> None:
    """Deep low boom: sine at ~60 Hz with slow exponential decay, ~0.8 s."""
    RATE = 22050
    n    = int(RATE * 0.8)
    raw  = []
    for i in range(n):
        t = i / RATE
        freq = 60.0
        s = math.sin(2 * math.pi * freq * t) * math.exp(-t * 4.0) * 0.9
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


def _crash_screech() -> None:
    """Tyre screech then crunch: high-freq sweep 800→200 Hz, ~0.5 s."""
    RATE = 22050
    dur  = 0.5
    n    = int(RATE * dur)
    rng  = random.Random(2)
    raw  = []
    phase_acc = 0.0
    for i in range(n):
        t = i / RATE
        p = t / dur  # 0 → 1
        freq      = 800 - 600 * p       # sweep 800 → 200 Hz
        phase_acc = (phase_acc + freq / RATE) % 1.0
        tone      = math.sin(2 * math.pi * phase_acc)
        noise     = rng.uniform(-1, 1) * 0.3
        amp       = (1.0 - p) ** 0.5
        s = (tone * 0.7 + noise) * amp * 0.85
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


# ── Pass sound variants ──────────────────────────────────────────

def _pass_engine() -> None:
    """'Zrrrr' engine buzz with Doppler drop as enemy car rushes past (original)."""
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


def _pass_beep() -> None:
    """Quick double-beep: two short sine tones at 880 Hz then 660 Hz, each 0.08 s."""
    RATE = 22050
    beep_dur = 0.08
    nb = int(RATE * beep_dur)
    raw = []
    for freq in (880, 660):
        for i in range(nb):
            t   = i / RATE
            p   = i / nb                 # 0 → 1 within this beep
            amp = math.sin(math.pi * p)  # smooth on/off envelope
            s   = math.sin(2 * math.pi * freq * t) * amp * 0.8
            raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


def _pass_whoosh() -> None:
    """White noise whoosh: broadband noise with fast amplitude envelope, ~0.15 s."""
    RATE = 22050
    dur  = 0.15
    n    = int(RATE * dur)
    rng  = random.Random(3)
    raw  = []
    for i in range(n):
        p   = i / n                      # 0 → 1
        # Rise to peak at 30%, then fall
        amp = math.sin(math.pi * p) ** 0.5
        s   = rng.uniform(-1, 1) * amp * 0.9
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


# ── Lane-switch sound variants ───────────────────────────────────

def _lane_engine() -> None:
    """Short tyre chirp: high-freq noise burst with very fast decay, ~0.10 s."""
    RATE = 22050
    dur  = 0.10
    n    = int(RATE * dur)
    rng  = random.Random(7)
    raw  = []
    for i in range(n):
        p   = i / n
        amp = (1.0 - p) ** 1.5
        s   = rng.uniform(-1, 1) * amp * 0.55
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


def _lane_retro() -> None:
    """Single short blip: sine at 440 Hz, 0.06 s."""
    RATE = 22050
    dur  = 0.06
    n    = int(RATE * dur)
    raw  = []
    for i in range(n):
        p   = i / n
        amp = math.sin(math.pi * p)
        s   = math.sin(2 * math.pi * 440 * i / RATE) * amp * 0.7
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


def _lane_minimal() -> None:
    """Soft swoosh: shaped noise, ~0.08 s."""
    RATE = 22050
    dur  = 0.08
    n    = int(RATE * dur)
    rng  = random.Random(11)
    raw  = []
    for i in range(n):
        p   = i / n
        amp = math.sin(math.pi * p) ** 0.7
        s   = rng.uniform(-1, 1) * amp * 0.45
        raw.append(int(max(-32767, min(32767, s * 32767))))
    _play_wav(raw, RATE)


# ── Public API ───────────────────────────────────────────────────

def play_crash_sound() -> None:
    """Play a crash sound according to the current theme."""
    if not _enabled:
        return
    try:
        if _theme == "retro":
            _crash_boom()
        elif _theme == "minimal":
            _crash_screech()
        else:  # "engine" or default
            _crash_crunch()
    except Exception:
        pass


def play_lane_switch_sound() -> None:
    """Play a lane-switch sound according to the current theme."""
    if not _enabled:
        return
    try:
        if _theme == "retro":
            _lane_retro()
        elif _theme == "minimal":
            _lane_minimal()
        else:  # "engine" or default
            _lane_engine()
    except Exception:
        pass


def play_pass_sound() -> None:
    """Play a pass sound according to the current theme."""
    if not _enabled:
        return
    try:
        if _theme == "retro":
            _pass_beep()
        elif _theme == "minimal":
            _pass_whoosh()
        else:  # "engine" or default
            _pass_engine()
    except Exception:
        pass
