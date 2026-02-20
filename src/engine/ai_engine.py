"""
AI search engine — Minimax with Alpha-Beta pruning.

Tuned to play in the style of Magnus Carlsen:
  • Uses the Magnus-tuned Evaluator
  • Follows Magnus's opening book when available
  • Applies iterative deepening with move ordering
  • Quiescence search for tactical accuracy
  • Transposition table for efficiency
"""

from __future__ import annotations

import chess
import chess.polyglot
import random
import time
from typing import Optional

from .evaluator import Evaluator
from .opening_book import OpeningBook
from src.utils.constants import DIFFICULTIES, PIECE_VALUES


# Transposition table entry
class TTEntry:
    __slots__ = ("depth", "score", "flag", "best_move")
    EXACT = 0
    ALPHA = 1
    BETA  = 2

    def __init__(self, depth: int, score: int, flag: int, best_move: Optional[chess.Move]):
        self.depth = depth
        self.score = score
        self.flag = flag
        self.best_move = best_move


class AIEngine:
    """Chess AI with Magnus Carlsen-style play."""

    MAX_QUIESCE_DEPTH = 6

    def __init__(self, difficulty: str = "SOLDIER"):
        self.difficulty = difficulty
        self.depth = DIFFICULTIES.get(difficulty, DIFFICULTIES["SOLDIER"])["depth"]
        self.evaluator = Evaluator()
        self.opening_book = OpeningBook()
        self.tt: dict[int, TTEntry] = {}
        self.nodes_searched = 0
        self.search_time = 0.0
        self._best_move_root: Optional[chess.Move] = None
        self._abort = False
        self._time_limit: float = 0.0  # 0 = no limit
        self._search_start: float = 0.0
        # Killer moves heuristic (2 slots per depth)
        self._killers: dict[int, list[chess.Move]] = {}
        # History heuristic table
        self._history_table: dict[tuple[int, int], int] = {}

    def set_difficulty(self, difficulty: str) -> None:
        self.difficulty = difficulty
        self.depth = DIFFICULTIES.get(difficulty, DIFFICULTIES["SOLDIER"])["depth"]

    # ── Public API ──────────────────────────────────────────────

    def get_best_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Find the best move for the current position."""
        self.nodes_searched = 0
        self._abort = False
        start = time.time()

        # 1) Try opening book first
        book_move = self.opening_book.get_move(board)
        if book_move and book_move in board.legal_moves:
            self.search_time = time.time() - start
            return book_move

        # 2) If only one legal move, return it immediately
        legal = list(board.legal_moves)
        if len(legal) == 0:
            return None
        if len(legal) == 1:
            self.search_time = time.time() - start
            return legal[0]

        # 3) Iterative deepening search
        best_move = legal[0]
        self._search_start = start
        # Time limits per difficulty (seconds)
        time_limits = {"RECRUIT": 1.0, "SOLDIER": 2.0, "CAPTAIN": 4.0, "GENERAL": 8.0, "MAGNUS": 15.0}
        self._time_limit = time_limits.get(self.difficulty, 5.0)
        self._killers.clear()
        self._history_table.clear()

        for d in range(1, self.depth + 1):
            self._best_move_root = None
            score = self._alpha_beta(
                board, d, -50000, 50000,
                board.turn == chess.WHITE,
            )
            if self._abort:
                break
            if self._best_move_root:
                best_move = self._best_move_root

        self.search_time = time.time() - start

        # 4) Add slight randomness for lower difficulties (simulate human error)
        if self.difficulty in ("RECRUIT", "SOLDIER"):
            best_move = self._add_imperfection(board, best_move)

        return best_move

    def get_analysis(self, board: chess.Board) -> dict:
        """Return evaluation + best move for analysis display."""
        move = self.get_best_move(board)
        score = self.evaluator.evaluate(board)
        return {
            "best_move": move,
            "score": score,
            "nodes": self.nodes_searched,
            "time": self.search_time,
            "depth": self.depth,
        }

    # ── Search Algorithm ────────────────────────────────────────

    def _alpha_beta(
        self, board: chess.Board,
        depth: int, alpha: int, beta: int,
        maximizing: bool,
    ) -> int:
        """Minimax with alpha-beta pruning and TT lookup."""
        self.nodes_searched += 1
        alpha_orig = alpha

        # Time limit check (every 4096 nodes)
        if self._time_limit > 0 and self.nodes_searched % 4096 == 0:
            if time.time() - self._search_start > self._time_limit:
                self._abort = True
                return 0

        # Transposition table probe
        key = chess.polyglot.zobrist_hash(board)
        tt_entry = self.tt.get(key)
        if tt_entry and tt_entry.depth >= depth:
            if tt_entry.flag == TTEntry.EXACT:
                if depth == self.depth and tt_entry.best_move:
                    self._best_move_root = tt_entry.best_move
                return tt_entry.score
            elif tt_entry.flag == TTEntry.ALPHA:
                alpha = max(alpha, tt_entry.score)
            elif tt_entry.flag == TTEntry.BETA:
                beta = min(beta, tt_entry.score)
            if alpha >= beta:
                return tt_entry.score

        # Terminal node
        if board.is_game_over():
            if board.is_checkmate():
                return -30000 - depth if maximizing else 30000 + depth
            return 0  # draw

        # Leaf node → quiescence search
        if depth == 0:
            return self._quiescence(board, alpha, beta, maximizing, self.MAX_QUIESCE_DEPTH)

        # Move ordering (crucial for alpha-beta efficiency)
        moves = self._order_moves(board, tt_entry, depth)

        best_score = -50000 if maximizing else 50000
        best_move = moves[0] if moves else None

        for move in moves:
            board.push(move)
            score = self._alpha_beta(board, depth - 1, alpha, beta, not maximizing)
            board.pop()

            if self._abort:
                return best_score

            if maximizing:
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, score)
            else:
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, score)

            if alpha >= beta:
                # Track killer moves and history heuristic for quiet moves
                if not board.is_capture(move) and not move.promotion:
                    # Killer move
                    if depth not in self._killers:
                        self._killers[depth] = []
                    killers = self._killers[depth]
                    if move not in killers:
                        killers.insert(0, move)
                        if len(killers) > 2:
                            killers.pop()
                    # History table
                    key = (move.from_square, move.to_square)
                    self._history_table[key] = self._history_table.get(key, 0) + depth * depth
                break  # prune

        # Store in TT
        if best_score <= alpha_orig:
            flag = TTEntry.BETA
        elif best_score >= beta:
            flag = TTEntry.ALPHA
        else:
            flag = TTEntry.EXACT
        self.tt[key] = TTEntry(depth, best_score, flag, best_move)

        # Track best move at root
        if depth == self.depth:
            self._best_move_root = best_move

        return best_score

    def _quiescence(
        self, board: chess.Board,
        alpha: int, beta: int,
        maximizing: bool,
        depth_left: int,
    ) -> int:
        """Quiescence search — evaluate captures to avoid horizon effect."""
        self.nodes_searched += 1
        stand_pat = self.evaluator.evaluate(board)

        if depth_left == 0:
            return stand_pat

        if maximizing:
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)

        # Only look at captures and promotions
        capture_moves = [m for m in board.legal_moves
                         if board.is_capture(m) or m.promotion]
        capture_moves.sort(key=lambda m: self._mvv_lva(board, m), reverse=True)

        for move in capture_moves:
            board.push(move)
            score = self._quiescence(board, alpha, beta, not maximizing, depth_left - 1)
            board.pop()

            if maximizing:
                if score >= beta:
                    return beta
                alpha = max(alpha, score)
            else:
                if score <= alpha:
                    return alpha
                beta = min(beta, score)

        return alpha if maximizing else beta

    # ── Move Ordering ───────────────────────────────────────────

    def _order_moves(self, board: chess.Board, tt_entry: Optional[TTEntry],
                     depth: int = 0) -> list[chess.Move]:
        """Order moves for better alpha-beta pruning.

        Priority:
          1. TT best move (from previous iteration)
          2. Captures (MVV-LVA ordering)
          3. Killer moves (quiet moves that caused cutoffs at this depth)
          4. Checks
          5. Promotions
          6. History heuristic (quiet moves with historical success)
          7. Remaining quiet moves
        """
        moves = list(board.legal_moves)
        scores: list[tuple[int, chess.Move]] = []

        tt_move = tt_entry.best_move if tt_entry else None
        killers = self._killers.get(depth, [])

        for m in moves:
            score = 0
            if tt_move and m == tt_move:
                score += 100000
            elif board.is_capture(m):
                score += 10000 + self._mvv_lva(board, m)
            elif m in killers:
                score += 9500  # killer moves just below captures
            elif m.promotion:
                score += 9000 + (m.promotion * 100)
            elif board.gives_check(m):
                score += 8000
            else:
                # History heuristic
                h_key = (m.from_square, m.to_square)
                score += min(self._history_table.get(h_key, 0), 7000)
            scores.append((score, m))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scores]

    @staticmethod
    def _mvv_lva(board: chess.Board, move: chess.Move) -> int:
        """Most Valuable Victim — Least Valuable Attacker heuristic."""
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        victim_val = PIECE_VALUES.get(victim.symbol(), 0) if victim else 0
        attacker_val = PIECE_VALUES.get(attacker.symbol(), 0) if attacker else 100
        return victim_val * 10 - attacker_val

    # ── Difficulty Imperfection ─────────────────────────────────

    def _add_imperfection(self, board: chess.Board, best_move: chess.Move) -> chess.Move:
        """For lower difficulties, occasionally play a sub-optimal move."""
        if self.difficulty == "RECRUIT":
            blunder_chance = 0.25
        elif self.difficulty == "SOLDIER":
            blunder_chance = 0.10
        else:
            return best_move

        if random.random() < blunder_chance:
            legal = list(board.legal_moves)
            # Pick a random non-terrible move
            alternatives = []
            for m in legal:
                if m != best_move:
                    board.push(m)
                    score = self.evaluator.evaluate(board)
                    board.pop()
                    alternatives.append((score, m))
            if alternatives:
                # For Recruit: pick from top 50%, Soldier: top 25%
                alternatives.sort(
                    key=lambda x: x[0],
                    reverse=(board.turn == chess.WHITE),
                )
                cutoff = len(alternatives) // 2 if self.difficulty == "RECRUIT" else len(alternatives) // 4
                cutoff = max(1, cutoff)
                _, chosen = random.choice(alternatives[:cutoff])
                return chosen

        return best_move

    def clear_tt(self) -> None:
        """Clear transposition table (call on new game)."""
        self.tt.clear()
