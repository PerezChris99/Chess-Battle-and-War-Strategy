"""
Game configuration manager with JSON persistence.

Handles user preferences, difficulty settings, and runtime options.
Settings are automatically saved to config.json in the project root.
"""

import json
import os
from .constants import PROJECT_ROOT


class Config:
    """Manages game configuration with file-backed persistence."""

    DEFAULT = {
        # Gameplay
        "difficulty":          "SOLDIER",
        "player_color":        "white",
        "time_control":        "rapid_10",

        # Display
        "show_valid_moves":    True,
        "show_coordinates":    True,
        "show_last_move":      True,
        "show_evaluation":     True,
        "flip_board":          False,
        "animation_enabled":   True,

        # Narrative
        "narrative_enabled":   True,
        "narrative_detail":    "full",     # "minimal", "standard", "full"

        # Audio
        "sound_enabled":       True,
        "music_enabled":       False,
        "volume":              0.7,

        # Tutorial
        "completed_lessons":   [],
        "hint_level":          "full",     # "none", "basic", "full"

        # UI
        "theme":               "classic_war",
        "auto_queen_promote":  False,
    }

    def __init__(self, config_path: str | None = None):
        self._path = config_path or os.path.join(PROJECT_ROOT, "config.json")
        self._data: dict = dict(self.DEFAULT)
        self._load()

    # ── public API ──────────────────────────────────────────────

    def get(self, key: str, default=None):
        """Return a configuration value."""
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a configuration value and persist to disk."""
        self._data[key] = value
        self._save()

    def update(self, mapping: dict) -> None:
        """Bulk-update multiple settings."""
        self._data.update(mapping)
        self._save()

    def reset(self) -> None:
        """Restore all settings to defaults."""
        self._data = dict(self.DEFAULT)
        self._save()

    @property
    def data(self) -> dict:
        return dict(self._data)

    # ── persistence ─────────────────────────────────────────────

    def _load(self) -> None:
        try:
            if os.path.exists(self._path):
                with open(self._path, "r", encoding="utf-8") as fh:
                    saved = json.load(fh)
                self._data.update(saved)
        except (json.JSONDecodeError, IOError, OSError):
            pass  # keep defaults

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, ensure_ascii=False)
        except (IOError, OSError):
            pass
