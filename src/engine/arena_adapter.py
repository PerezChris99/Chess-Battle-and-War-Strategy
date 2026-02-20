"""
AI Arena — Adapter interface for external AI models.

Defines the common protocol that ALL external AI models must implement.
This enables a pluggable system where any model (Gemini, GPT, Claude, etc.)
can join the chess arena by implementing the `ArenaAdapter` ABC.

Each adapter:
  • Receives a chess position (FEN string)
  • Returns a UCI move string (e.g. "e2e4")
  • Reports its own name, model identifier and capabilities
  • Tracks rate-limiting / retry state
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import chess


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ArenaModelInfo:
    """Metadata about an external AI model."""
    model_id: str           # unique key, e.g. "gemini_pro"
    display_name: str       # e.g. "Gemini Pro"
    provider: str           # e.g. "Google"
    icon: str               # emoji
    description: str
    supports_analysis: bool = False   # can it explain its moves?
    default_elo: int = 1500


@dataclass
class ArenaMove:
    """Result of an external AI move request."""
    uci_move: str           # e.g. "e2e4"
    thinking_time: float    # seconds spent
    explanation: str = ""   # optional natural language reasoning
    confidence: float = 0.0
    raw_response: str = ""  # full API response for debugging
    error: str = ""         # non-empty if move generation failed


@dataclass
class RateLimitState:
    """Tracks rate-limiting for an API."""
    requests_this_minute: int = 0
    minute_start: float = 0.0
    max_per_minute: int = 15
    last_request_time: float = 0.0
    min_interval: float = 1.0  # minimum seconds between requests
    consecutive_errors: int = 0
    max_retries: int = 3
    backoff_base: float = 2.0

    def can_request(self) -> bool:
        """Check if a request is allowed right now."""
        now = time.time()
        # Reset minute counter if window elapsed
        if now - self.minute_start >= 60:
            self.requests_this_minute = 0
            self.minute_start = now
        # Check rate limits
        if self.requests_this_minute >= self.max_per_minute:
            return False
        if now - self.last_request_time < self.min_interval:
            return False
        return True

    def record_request(self) -> None:
        now = time.time()
        if now - self.minute_start >= 60:
            self.requests_this_minute = 0
            self.minute_start = now
        self.requests_this_minute += 1
        self.last_request_time = now

    def record_success(self) -> None:
        self.consecutive_errors = 0

    def record_error(self) -> None:
        self.consecutive_errors += 1

    def get_backoff_delay(self) -> float:
        """Exponential backoff delay based on consecutive errors."""
        if self.consecutive_errors == 0:
            return 0.0
        return min(60.0, self.backoff_base ** self.consecutive_errors)

    @property
    def should_retry(self) -> bool:
        return self.consecutive_errors < self.max_retries


# ─────────────────────────────────────────────────────────────────────────────
# Abstract Base Class
# ─────────────────────────────────────────────────────────────────────────────

class ArenaAdapter(ABC):
    """
    Abstract adapter for an external chess AI model.

    Subclasses implement `_request_move()` with API-specific logic.
    The base class handles rate-limiting, retry, error wrapping, and
    move validation.
    """

    def __init__(self):
        self.rate_limit = RateLimitState()
        self._configured = False

    @abstractmethod
    def get_info(self) -> ArenaModelInfo:
        """Return model metadata."""
        ...

    @abstractmethod
    def configure(self, api_key: str, **kwargs: Any) -> bool:
        """
        Configure the adapter with an API key and optional params.
        Returns True if configuration was successful (key accepted).
        """
        ...

    @abstractmethod
    def _request_move(self, fen: str, move_history: list[str]) -> ArenaMove:
        """
        Internal: send a position to the external API and get a move back.
        Subclasses implement this with provider-specific HTTP calls.

        Args:
            fen: Current board position as a FEN string.
            move_history: List of UCI moves played so far.

        Returns:
            ArenaMove with the result (may contain an error).
        """
        ...

    @property
    def is_configured(self) -> bool:
        return self._configured

    # ── Public API ──────────────────────────────────────────────

    def get_move(self, board: chess.Board, move_history: list[str] | None = None) -> ArenaMove:
        """
        Get a move from the external AI for the given board position.
        Handles rate-limiting, retry logic, and move validation.
        """
        if not self._configured:
            return ArenaMove(
                uci_move="", thinking_time=0,
                error="Model not configured. Set an API key first.",
            )

        history = move_history or []
        fen = board.fen()

        # Rate-limit check
        if not self.rate_limit.can_request():
            delay = self.rate_limit.get_backoff_delay()
            if delay > 0:
                time.sleep(min(delay, 5.0))  # cap wait at 5s
            if not self.rate_limit.can_request():
                return ArenaMove(
                    uci_move="", thinking_time=0,
                    error="Rate limit exceeded. Please wait before trying again.",
                )

        # Attempt with retry
        last_error = ""
        for attempt in range(self.rate_limit.max_retries):
            if attempt > 0:
                backoff = self.rate_limit.get_backoff_delay()
                time.sleep(min(backoff, 5.0))

            self.rate_limit.record_request()
            start = time.time()

            try:
                result = self._request_move(fen, history)
            except Exception as e:
                self.rate_limit.record_error()
                last_error = str(e)
                continue

            result.thinking_time = time.time() - start

            if result.error:
                self.rate_limit.record_error()
                last_error = result.error
                continue

            # Validate the move
            validated = self._validate_move(board, result.uci_move)
            if validated:
                result.uci_move = validated
                self.rate_limit.record_success()
                return result
            else:
                self.rate_limit.record_error()
                last_error = f"Invalid move returned by AI: {result.uci_move}"
                continue

        # All retries exhausted
        return ArenaMove(
            uci_move="", thinking_time=0,
            error=f"Failed after {self.rate_limit.max_retries} attempts: {last_error}",
        )

    @staticmethod
    def _validate_move(board: chess.Board, uci_str: str) -> str | None:
        """
        Validate a UCI move string against the current board.
        Returns the canonical UCI string if valid, None otherwise.
        """
        if not uci_str or not uci_str.strip():
            return None
        # Clean up common formatting issues
        uci_clean = uci_str.strip().lower().replace("-", "").replace(" ", "")
        # UCI moves are at least 4 chars (e.g. "e2e4")
        if len(uci_clean) >= 4:
            try:
                move = chess.Move.from_uci(uci_clean)
                if move in board.legal_moves:
                    return move.uci()
            except (ValueError, chess.InvalidMoveError):
                pass

        # Try to parse as SAN (some models return algebraic notation)
        try:
            move = board.parse_san(uci_str.strip())
            if move in board.legal_moves:
                return move.uci()
        except (ValueError, chess.InvalidMoveError, chess.AmbiguousMoveError):
            pass

        return None

    def reset(self) -> None:
        """Reset rate-limit state (e.g. between games)."""
        self.rate_limit = RateLimitState()


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, type[ArenaAdapter]] = {}


def register_adapter(model_id: str, adapter_cls: type[ArenaAdapter]) -> None:
    """Register an adapter class for a model ID."""
    _REGISTRY[model_id] = adapter_cls


def get_available_adapters() -> dict[str, type[ArenaAdapter]]:
    """Return all registered adapter classes."""
    return dict(_REGISTRY)


def create_adapter(model_id: str) -> ArenaAdapter | None:
    """Create an adapter instance by model ID."""
    cls = _REGISTRY.get(model_id)
    return cls() if cls else None
