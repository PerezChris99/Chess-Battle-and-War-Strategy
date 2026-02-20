"""
Post-game analysis — generates a detailed battle report after a game ends.

Provides move-by-move assessment, critical moments, accuracy stats,
and narrative-style battle summary.
"""

from __future__ import annotations

import chess
from dataclasses import dataclass, field
from typing import Optional

from src.engine.evaluator import Evaluator
from src.game.move_history import MoveHistory, MoveRecord
from src.narrative.piece_lore import PIECE_LORE
from src.utils.constants import PIECE_VALUES


@dataclass
class MoveAssessment:
    """Assessment of a single move."""
    move_number: int
    is_white: bool
    san: str
    eval_before: int
    eval_after: int
    eval_change: int
    classification: str   # "best", "excellent", "good", "inaccuracy", "mistake", "blunder"
    narrative: str = ""


@dataclass
class GameAnalysis:
    """Full post-game analysis."""
    total_moves: int = 0
    white_accuracy: float = 0.0
    black_accuracy: float = 0.0
    assessments: list[MoveAssessment] = field(default_factory=list)
    critical_moments: list[MoveAssessment] = field(default_factory=list)
    opening_name: str = "Unknown Opening"
    game_result: str = "*"
    phase_summary: dict[str, str] = field(default_factory=dict)
    battle_report: str = ""

    # Classification counts
    white_blunders: int = 0
    white_mistakes: int = 0
    white_inaccuracies: int = 0
    black_blunders: int = 0
    black_mistakes: int = 0
    black_inaccuracies: int = 0


class PostGameAnalyzer:
    """Analyzes a completed game and produces a battle report."""

    # Centipawn thresholds for move classification
    BLUNDER_THRESHOLD = 200        # >= 200cp loss
    MISTAKE_THRESHOLD = 100        # >= 100cp loss
    INACCURACY_THRESHOLD = 50      # >= 50cp loss

    def __init__(self):
        self.evaluator = Evaluator()

    def analyze(self, history: MoveHistory, board: chess.Board,
                opening_name: str = "Unknown", result: str = "*") -> GameAnalysis:
        """Analyze the full game from move history."""
        analysis = GameAnalysis()
        analysis.total_moves = history.count
        analysis.opening_name = opening_name or "Unknown Opening"
        analysis.game_result = result

        if history.count == 0:
            analysis.battle_report = "No moves were played. The armies stood idle."
            return analysis

        # Replay through the game to evaluate each position
        replay_board = chess.Board()
        prev_eval = self.evaluator.evaluate(replay_board)

        white_eval_losses = []
        black_eval_losses = []

        for record in history.moves:
            move = chess.Move.from_uci(record.uci)
            if move not in replay_board.legal_moves:
                break

            eval_before = prev_eval
            replay_board.push(move)
            eval_after = self.evaluator.evaluate(replay_board)

            # From the perspective of the side that moved
            is_white = record.color == "white"
            if is_white:
                eval_change = eval_after - eval_before
                loss = max(0, -eval_change)
                white_eval_losses.append(loss)
            else:
                eval_change = eval_before - eval_after
                loss = max(0, -eval_change)
                black_eval_losses.append(loss)

            # Classify the move
            classification = self._classify_move(loss)
            narrative = self._assessment_narrative(record, classification, loss, is_white)

            assessment = MoveAssessment(
                move_number=record.move_number,
                is_white=is_white,
                san=record.san,
                eval_before=eval_before,
                eval_after=eval_after,
                eval_change=eval_change,
                classification=classification,
                narrative=narrative,
            )
            analysis.assessments.append(assessment)

            # Track classification counts
            if is_white:
                if classification == "blunder":
                    analysis.white_blunders += 1
                elif classification == "mistake":
                    analysis.white_mistakes += 1
                elif classification == "inaccuracy":
                    analysis.white_inaccuracies += 1
            else:
                if classification == "blunder":
                    analysis.black_blunders += 1
                elif classification == "mistake":
                    analysis.black_mistakes += 1
                elif classification == "inaccuracy":
                    analysis.black_inaccuracies += 1

            # Mark critical moments (blunders & mistakes)
            if classification in ("blunder", "mistake"):
                analysis.critical_moments.append(assessment)

            prev_eval = eval_after

        # Calculate accuracy (100 - average centipawn loss, clamped)
        if white_eval_losses:
            avg_white = sum(white_eval_losses) / len(white_eval_losses)
            analysis.white_accuracy = max(0.0, min(100.0, 100 - avg_white / 3))
        if black_eval_losses:
            avg_black = sum(black_eval_losses) / len(black_eval_losses)
            analysis.black_accuracy = max(0.0, min(100.0, 100 - avg_black / 3))

        # Phase summary
        analysis.phase_summary = self._build_phase_summary(analysis.assessments)

        # Build narrative battle report
        analysis.battle_report = self._build_battle_report(analysis)

        return analysis

    def _classify_move(self, centipawn_loss: int) -> str:
        """Classify a move based on centipawn loss."""
        if centipawn_loss >= self.BLUNDER_THRESHOLD:
            return "blunder"
        elif centipawn_loss >= self.MISTAKE_THRESHOLD:
            return "mistake"
        elif centipawn_loss >= self.INACCURACY_THRESHOLD:
            return "inaccuracy"
        elif centipawn_loss <= 10:
            return "best"
        elif centipawn_loss <= 25:
            return "excellent"
        else:
            return "good"

    def _assessment_narrative(self, record: MoveRecord, classification: str,
                              loss: int, is_white: bool) -> str:
        """Generate a narrative description for a move assessment."""
        side = "White" if is_white else "Black"
        emoji_map = {
            "best": "!!",
            "excellent": "!",
            "good": "",
            "inaccuracy": "?!",
            "mistake": "?",
            "blunder": "??",
        }
        symbol = emoji_map.get(classification, "")

        if classification == "blunder":
            return (f"{side}'s {record.san}{symbol} — A catastrophic tactical "
                    f"error! The commander loses {loss}cp of advantage.")
        elif classification == "mistake":
            return (f"{side}'s {record.san}{symbol} — A strategic misstep "
                    f"that weakens the army's position by {loss}cp.")
        elif classification == "inaccuracy":
            return (f"{side}'s {record.san}{symbol} — A slightly imprecise "
                    f"maneuver, costing the force {loss}cp.")
        elif classification == "best":
            return f"{side}'s {record.san}{symbol} — A flawless tactical decision."
        elif classification == "excellent":
            return f"{side}'s {record.san}{symbol} — Strong and decisive command."
        else:
            return f"{side}'s {record.san} — Solid operational move."

    def _build_phase_summary(self, assessments: list[MoveAssessment]) -> dict[str, str]:
        """Summarize performance by game phase."""
        phases = {"Opening": [], "Middlegame": [], "Endgame": []}
        total = len(assessments)

        for i, a in enumerate(assessments):
            progress = i / max(total, 1)
            if progress < 0.2:
                phases["Opening"].append(a)
            elif progress < 0.65:
                phases["Middlegame"].append(a)
            else:
                phases["Endgame"].append(a)

        summary = {}
        for phase_name, moves in phases.items():
            if not moves:
                summary[phase_name] = "No significant activity."
                continue

            blunders = sum(1 for m in moves if m.classification == "blunder")
            mistakes = sum(1 for m in moves if m.classification == "mistake")
            best_moves = sum(1 for m in moves if m.classification in ("best", "excellent"))

            if blunders > 0:
                summary[phase_name] = (f"Turbulent — {blunders} blunder(s) and "
                                       f"{mistakes} mistake(s) among {len(moves)} moves.")
            elif mistakes > 0:
                summary[phase_name] = (f"Uneven — {mistakes} mistake(s) but "
                                       f"{best_moves} strong moves among {len(moves)}.")
            elif best_moves > len(moves) * 0.6:
                summary[phase_name] = f"Dominant — {best_moves}/{len(moves)} moves were excellent or best."
            else:
                summary[phase_name] = f"Solid — {len(moves)} measured moves with no major errors."

        return summary

    def _build_battle_report(self, analysis: GameAnalysis) -> str:
        """Build a narrative-style battle report."""
        lines = []
        lines.append(f"=== BATTLE REPORT: {analysis.opening_name} ===")
        lines.append("")

        # Result
        result_narratives = {
            "1-0": "The White army claims total victory!",
            "0-1": "The Black army has conquered the field!",
            "1/2-1/2": "Neither army could break through — an honorable truce.",
        }
        lines.append(result_narratives.get(analysis.game_result, f"Result: {analysis.game_result}"))
        lines.append("")

        # Accuracy
        lines.append(f"White Commander Accuracy: {analysis.white_accuracy:.1f}%")
        lines.append(f"Black Commander Accuracy: {analysis.black_accuracy:.1f}%")
        lines.append("")

        # Errors summary
        lines.append("--- Tactical Errors ---")
        lines.append(f"White: {analysis.white_blunders} blunders, "
                     f"{analysis.white_mistakes} mistakes, "
                     f"{analysis.white_inaccuracies} inaccuracies")
        lines.append(f"Black: {analysis.black_blunders} blunders, "
                     f"{analysis.black_mistakes} mistakes, "
                     f"{analysis.black_inaccuracies} inaccuracies")
        lines.append("")

        # Phase summary
        lines.append("--- Campaign Phases ---")
        for phase, desc in analysis.phase_summary.items():
            lines.append(f"{phase}: {desc}")
        lines.append("")

        # Critical moments
        if analysis.critical_moments:
            lines.append("--- Critical Moments ---")
            for cm in analysis.critical_moments[:5]:
                prefix = f"{cm.move_number}." if cm.is_white else f"{cm.move_number}..."
                lines.append(f"  {prefix}{cm.san} ({cm.classification}) — {cm.narrative}")
            lines.append("")

        lines.append(f"Total moves: {analysis.total_moves}")
        lines.append("=== END OF REPORT ===")

        return "\n".join(lines)
