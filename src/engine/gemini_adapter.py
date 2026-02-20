"""
Gemini (Google AI) chess adapter.

Connects to the Google Generative AI API to get chess moves from Gemini.
Sends the board as FEN, requests a UCI move, and parses the response.

Requirements:
  pip install google-generativeai
"""

from __future__ import annotations

import re
from typing import Any

from src.engine.arena_adapter import (
    ArenaAdapter, ArenaModelInfo, ArenaMove, register_adapter,
)


# ── Prompt Template ─────────────────────────────────────────────

_SYSTEM_PROMPT = """You are an expert chess engine. You will be given a chess position in FEN notation and a list of moves played so far.

Your task is to respond with ONLY the best move in UCI notation (e.g., "e2e4", "g1f3", "e7e8q" for promotion).

Rules:
- Respond with ONLY the UCI move, nothing else
- The move MUST be legal in the given position
- Use lowercase letters for files (a-h) and numbers for ranks (1-8)
- For promotions, append the piece letter: q, r, b, n (e.g., "e7e8q")
- Do not include any explanation, just the move
"""

_ANALYSIS_SYSTEM_PROMPT = """You are an expert chess engine and instructor. You will be given a chess position in FEN notation and a list of moves played so far.

Your task:
1. On the FIRST line, output ONLY the best move in UCI notation (e.g., "e2e4")
2. On the SECOND line, give a brief (1-2 sentence) explanation of your move choice

Rules for the move:
- The move MUST be legal in the given position
- Use lowercase letters for files (a-h)
- For promotions, append the piece: q, r, b, n
"""


def _build_move_prompt(fen: str, move_history: list[str], with_analysis: bool = False) -> str:
    """Build the user prompt for a move request."""
    parts = [f"Current position (FEN): {fen}"]
    if move_history:
        moves_str = " ".join(move_history[-20:])  # last 20 moves for context
        parts.append(f"Recent moves: {moves_str}")
    parts.append("Your move (UCI):")
    return "\n".join(parts)


def _extract_uci_move(text: str) -> tuple[str, str]:
    """
    Extract a UCI move from potentially messy AI output.
    Returns (uci_move, explanation).
    """
    text = text.strip()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Try first line as move
    if lines:
        first = lines[0].strip().strip("`'\"").lower()
        # Match UCI pattern: 4-5 chars like e2e4, e7e8q
        match = re.match(r'^([a-h][1-8][a-h][1-8][qrbn]?)$', first)
        if match:
            explanation = " ".join(lines[1:]) if len(lines) > 1 else ""
            return match.group(1), explanation

    # Fallback: search anywhere in text for a UCI-like pattern
    matches = re.findall(r'\b([a-h][1-8][a-h][1-8][qrbn]?)\b', text.lower())
    if matches:
        return matches[0], ""

    # Last resort: try to find SAN notation (e.g. Nf3, e4, Bxe5+)
    san_matches = re.findall(
        r'\b([KQRBNP]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?)\b', text
    )
    if san_matches:
        return san_matches[0], ""

    return text[:10] if text else "", ""


class GeminiAdapter(ArenaAdapter):
    """Google Gemini AI chess adapter."""

    def __init__(self):
        super().__init__()
        self._api_key: str = ""
        self._model_name: str = "gemini-2.0-flash"
        self._client: Any = None
        self._model: Any = None
        self._with_analysis: bool = False

    def get_info(self) -> ArenaModelInfo:
        return ArenaModelInfo(
            model_id="gemini_flash",
            display_name="Gemini 2.0 Flash",
            provider="Google",
            icon="✨",
            description="Google's fast multimodal AI model — plays creative and adaptive chess",
            supports_analysis=True,
            default_elo=1500,
        )

    def configure(self, api_key: str, **kwargs: Any) -> bool:
        """
        Configure with a Google AI API key.
        kwargs:
          - model_name: str (default "gemini-2.0-flash")
          - with_analysis: bool (default False)
        """
        self._api_key = api_key
        self._model_name = kwargs.get("model_name", "gemini-2.0-flash")
        self._with_analysis = kwargs.get("with_analysis", False)

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(
                self._model_name,
                system_instruction=(
                    _ANALYSIS_SYSTEM_PROMPT if self._with_analysis else _SYSTEM_PROMPT
                ),
            )
            self._configured = True
            return True
        except ImportError:
            self._configured = False
            return False
        except Exception:
            self._configured = False
            return False

    def _request_move(self, fen: str, move_history: list[str]) -> ArenaMove:
        """Send position to Gemini and parse the response."""
        if not self._model:
            return ArenaMove(uci_move="", thinking_time=0, error="Model not initialized")

        prompt = _build_move_prompt(fen, move_history, self._with_analysis)

        try:
            response = self._model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,   # low temp for consistent play
                    "max_output_tokens": 100,
                    "top_p": 0.8,
                },
            )

            raw_text = response.text if response.text else ""
            uci_move, explanation = _extract_uci_move(raw_text)

            return ArenaMove(
                uci_move=uci_move,
                thinking_time=0,  # set by base class
                explanation=explanation,
                raw_response=raw_text,
            )

        except Exception as e:
            return ArenaMove(
                uci_move="", thinking_time=0,
                error=f"Gemini API error: {str(e)}",
            )

    def set_analysis_mode(self, enabled: bool) -> None:
        """Toggle move explanations on/off."""
        self._with_analysis = enabled
        if self._configured and self._api_key:
            self.configure(self._api_key, model_name=self._model_name,
                           with_analysis=enabled)


# Register the adapter
register_adapter("gemini_flash", GeminiAdapter)


# ── Convenience ─────────────────────────────────────────────────

def get_gemini_models() -> list[dict[str, str]]:
    """Return available Gemini model variants."""
    return [
        {
            "id": "gemini-2.0-flash",
            "name": "Gemini 2.0 Flash",
            "description": "Fast and efficient — best for real-time chess play",
        },
        {
            "id": "gemini-2.5-pro-preview-06-05",
            "name": "Gemini 2.5 Pro",
            "description": "Most capable — deeper analysis, slower responses",
        },
        {
            "id": "gemini-2.5-flash-preview-05-20",
            "name": "Gemini 2.5 Flash",
            "description": "Balanced speed and quality — adaptive play style",
        },
    ]
