"""
Sound manager — handles all game audio.

Plays move sounds, capture sounds, battle ambiance, and UI feedback.
Generates synthetic sounds at runtime so no external .wav files are needed.
"""

from __future__ import annotations

import math
import pygame
import struct
from typing import Optional

from src.utils.constants import SOUNDS_DIR


class SoundManager:
    """Manages all game audio — synthesizes sounds on the fly."""

    def __init__(self, enabled: bool = True, volume: float = 0.7):
        self.enabled = enabled
        self.volume = max(0.0, min(1.0, volume))
        self._initialized = False
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._init_audio()

    def _init_audio(self) -> None:
        """Initialize the pygame mixer and generate all sounds."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._initialized = True
            self._generate_sounds()
        except Exception:
            self._initialized = False

    def _generate_sounds(self) -> None:
        """Generate all game sounds synthetically."""
        if not self._initialized:
            return

        # Move — soft wooden tap
        self._sounds["move"] = self._make_sound(
            duration=0.08, freq=320, wave="sine",
            attack=0.005, decay=0.075, volume=0.5,
        )

        # Capture — aggressive hit
        self._sounds["capture"] = self._make_sound(
            duration=0.15, freq=180, wave="noise_tone",
            attack=0.005, decay=0.145, volume=0.7,
        )

        # Check — sharp alert
        self._sounds["check"] = self._make_sound(
            duration=0.12, freq=660, wave="sine",
            attack=0.005, decay=0.115, volume=0.6,
        )

        # Checkmate — dramatic chord
        self._sounds["checkmate"] = self._overlay([
            self._make_sound(0.4, 220, "sine", 0.01, 0.39, 0.5),
            self._make_sound(0.4, 277, "sine", 0.01, 0.39, 0.4),
            self._make_sound(0.4, 330, "sine", 0.01, 0.39, 0.4),
        ])

        # Castling — double tap
        self._sounds["castling"] = self._overlay([
            self._make_sound(0.06, 350, "sine", 0.005, 0.055, 0.5),
            self._make_sound(0.06, 420, "sine", 0.005, 0.055, 0.5, delay=0.08),
        ])

        # Promotion — ascending tone
        self._sounds["promotion"] = self._make_sound(
            duration=0.2, freq=400, wave="sweep_up",
            attack=0.01, decay=0.19, volume=0.5,
        )

        # Game start — horn
        self._sounds["game_start"] = self._make_sound(
            duration=0.3, freq=440, wave="sine",
            attack=0.05, decay=0.25, volume=0.4,
        )

        # Game over — low tone
        self._sounds["game_over"] = self._make_sound(
            duration=0.5, freq=150, wave="sine",
            attack=0.02, decay=0.48, volume=0.5,
        )

        # Button click
        self._sounds["click"] = self._make_sound(
            duration=0.04, freq=800, wave="sine",
            attack=0.002, decay=0.038, volume=0.3,
        )

        # Illegal move — error buzz
        self._sounds["illegal"] = self._make_sound(
            duration=0.1, freq=120, wave="square",
            attack=0.005, decay=0.095, volume=0.3,
        )

    # ── Public API ──────────────────────────────────────────────

    def play(self, sound_name: str) -> None:
        """Play a named sound effect."""
        if not self.enabled or not self._initialized:
            return
        snd = self._sounds.get(sound_name)
        if snd:
            snd.set_volume(self.volume)
            snd.play()

    def play_move(self, is_capture: bool = False, is_check: bool = False,
                  is_checkmate: bool = False, is_castling: bool = False,
                  is_promotion: bool = False) -> None:
        """Play the appropriate sound for a chess move."""
        if is_checkmate:
            self.play("checkmate")
        elif is_check:
            self.play("check")
        elif is_capture:
            self.play("capture")
        elif is_castling:
            self.play("castling")
        elif is_promotion:
            self.play("promotion")
        else:
            self.play("move")

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    # ── Sound Synthesis ─────────────────────────────────────────

    def _make_sound(
        self,
        duration: float,
        freq: float,
        wave: str = "sine",
        attack: float = 0.01,
        decay: float = 0.1,
        volume: float = 0.5,
        delay: float = 0.0,
    ) -> pygame.mixer.Sound:
        """Generate a synthetic sound as a pygame Sound object."""
        sample_rate = 44100
        n_samples = int(sample_rate * (duration + delay))
        delay_samples = int(sample_rate * delay)
        buf = []

        for i in range(n_samples):
            if i < delay_samples:
                buf.append(0)
                continue

            t = (i - delay_samples) / sample_rate
            progress = t / duration if duration > 0 else 0

            # Envelope
            if t < attack:
                env = t / attack if attack > 0 else 1.0
            elif t < duration - decay + attack:
                env = 1.0
            else:
                remaining = duration - t
                env = remaining / decay if decay > 0 else 0.0
            env = max(0.0, min(1.0, env))

            # Waveform
            if wave == "sine":
                sample = math.sin(2 * math.pi * freq * t)
            elif wave == "square":
                sample = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            elif wave == "noise_tone":
                # Tone mixed with pseudo-noise for percussive feel
                tone = math.sin(2 * math.pi * freq * t)
                noise = math.sin(2 * math.pi * freq * 3.7 * t + 1.3) * 0.3
                sample = tone * 0.7 + noise
            elif wave == "sweep_up":
                current_freq = freq + (freq * 0.5) * progress
                sample = math.sin(2 * math.pi * current_freq * t)
            else:
                sample = math.sin(2 * math.pi * freq * t)

            value = int(sample * env * volume * 32767)
            value = max(-32767, min(32767, value))
            buf.append(value)

        # Pack as 16-bit mono PCM then create Sound
        raw = struct.pack(f"<{len(buf)}h", *buf)
        sound = pygame.mixer.Sound(buffer=raw)
        return sound

    def _overlay(self, sounds: list[pygame.mixer.Sound]) -> pygame.mixer.Sound:
        """Mix multiple sounds into one."""
        if not sounds:
            return self._make_sound(0.01, 440)

        # Find max length
        raw_arrays = []
        max_len = 0
        for snd in sounds:
            raw = snd.get_raw()
            raw_arrays.append(raw)
            max_len = max(max_len, len(raw))

        # Mix
        result = [0] * (max_len // 2)
        for raw in raw_arrays:
            samples = struct.unpack(f"<{len(raw) // 2}h", raw)
            for i, s in enumerate(samples):
                result[i] += s

        # Clamp
        result = [max(-32767, min(32767, s)) for s in result]
        raw_out = struct.pack(f"<{len(result)}h", *result)
        return pygame.mixer.Sound(buffer=raw_out)
