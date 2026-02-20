"""
Move history tracker.

Records all moves in SAN notation alongside their battle narratives,
and provides formatted output for the HUD panel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import chess


@dataclass
class MoveRecord:
    """Single move entry."""
    move_number: int           # 1-based full move number
    color: str                 # "white" or "black"
    san: str                   # Standard algebraic (e.g. "Nf3")
    uci: str                   # UCI notation (e.g. "g1f3")
    narrative: str             # Battle narrative text
    is_capture: bool = False
    is_check: bool = False
    is_checkmate: bool = False
    is_castling: bool = False
    opening_name: str | None = None


class MoveHistory:
    """Tracks the full move history of a game."""

    def __init__(self):
        self._moves: list[MoveRecord] = []

    @property
    def moves(self) -> list[MoveRecord]:
        return self._moves

    @property
    def count(self) -> int:
        return len(self._moves)

    @property
    def last_move(self) -> MoveRecord | None:
        return self._moves[-1] if self._moves else None

    @property
    def last_narrative(self) -> str:
        return self._moves[-1].narrative if self._moves else ""

    def add_move(
        self,
        san: str,
        uci: str,
        narrative: str,
        move_number: int,
        is_white: bool,
        is_capture: bool = False,
        is_check: bool = False,
        is_checkmate: bool = False,
        is_castling: bool = False,
        opening_name: str | None = None,
    ) -> MoveRecord:
        record = MoveRecord(
            move_number=move_number,
            color="white" if is_white else "black",
            san=san,
            uci=uci,
            narrative=narrative,
            is_capture=is_capture,
            is_check=is_check,
            is_checkmate=is_checkmate,
            is_castling=is_castling,
            opening_name=opening_name,
        )
        self._moves.append(record)
        return record

    def undo(self) -> MoveRecord | None:
        return self._moves.pop() if self._moves else None

    def clear(self) -> None:
        self._moves.clear()

    def get_formatted_pairs(self) -> list[str]:
        """Return move list formatted as '1. e4 e5', '2. Nf3 Nc6', etc."""
        lines: list[str] = []
        i = 0
        while i < len(self._moves):
            rec = self._moves[i]
            line = f"{rec.move_number}. {rec.san}"
            # Look for black's response
            if i + 1 < len(self._moves) and self._moves[i + 1].color == "black":
                line += f"  {self._moves[i + 1].san}"
                i += 2
            else:
                if rec.color == "black":
                    line = f"{rec.move_number}. ...  {rec.san}"
                i += 1
            lines.append(line)
        return lines

    def get_recent_narratives(self, count: int = 5) -> list[str]:
        """Return the most recent narrative strings."""
        return [m.narrative for m in self._moves[-count:]]
