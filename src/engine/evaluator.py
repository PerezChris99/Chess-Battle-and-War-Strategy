"""
Position evaluator tuned to Magnus Carlsen's playing style.

Magnus's key characteristics modeled here:
  1. Positional mastery  — piece activity, pawn structure, space
  2. Endgame dominance   — king activity, passed pawns, technique
  3. Prophylactic play   — restricting opponent's plans
  4. Grinding ability    — maximising small advantages
  5. Versatility         — adapting evaluation to game phase

All values are in centipawns from White's perspective.
"""

from __future__ import annotations

import chess
from src.utils.constants import PIECE_VALUES


# ─────────────────────────────────────────────────────────────────────────────
# Piece-Square Tables  (from White's perspective, index 0 = a1)
#
# Tuned to favour Magnus-style piece placement:
#   • Knights to outposts (d5, e5, c5)
#   • Bishops on active diagonals
#   • Rooks on open files and 7th rank
#   • King safety in middlegame, activity in endgame
# ─────────────────────────────────────────────────────────────────────────────

# fmt: off
PAWN_TABLE = [
     0,   0,   0,   0,   0,   0,   0,   0,
    50,  50,  50,  50,  50,  50,  50,  50,
    10,  10,  20,  30,  30,  20,  10,  10,
     5,   5,  10,  27,  27,  10,   5,   5,
     0,   0,   0,  25,  25,   0,   0,   0,
     5,  -5, -10,   0,   0, -10,  -5,   5,
     5,  10,  10, -25, -25,  10,  10,   5,
     0,   0,   0,   0,   0,   0,   0,   0,
]

KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_TABLE = [
     0,   0,   0,   0,   0,   0,   0,   0,
     5,  10,  10,  10,  10,  10,  10,   5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
     0,   0,   0,   5,   5,   0,   0,   0,
]

QUEEN_TABLE = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20,
]

KING_MIDDLEGAME_TABLE = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20,
]

# Magnus's endgame king activity — crucial to his grinding style
KING_ENDGAME_TABLE = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -30,   0,   0,   0,   0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]

# Passed-pawn bonus by rank (from White's perspective, index = rank 0-7)
PASSED_PAWN_BONUS = [0, 10, 20, 40, 60, 90, 130, 0]

PST = {
    chess.PAWN:   PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK:   ROOK_TABLE,
    chess.QUEEN:  QUEEN_TABLE,
}
# fmt: on


class Evaluator:
    """Static position evaluator with Magnus Carlsen-style weights."""

    # ── Magnus-style weight multipliers ─────────────────────────
    WEIGHT_MATERIAL       = 1.0
    WEIGHT_PST            = 1.0
    WEIGHT_MOBILITY       = 0.12    # Magnus values piece activity highly
    WEIGHT_PAWN_STRUCTURE = 0.6     # Pawn play is a Magnus hallmark
    WEIGHT_KING_SAFETY    = 1.2     # Moderate — Magnus balances safety vs activity
    WEIGHT_BISHOP_PAIR    = 0.5     # Magnus loves the bishop pair
    WEIGHT_ROOK_OPEN_FILE = 0.4
    WEIGHT_PASSED_PAWN    = 0.8     # Strong passed-pawn technique
    WEIGHT_SPACE          = 0.15    # Space advantage (squeezing)
    WEIGHT_CENTER_CONTROL = 0.2     # Central dominance
    WEIGHT_CONNECTIVITY   = 0.1     # Piece coordination
    WEIGHT_ENDGAME_KING   = 1.5     # Magnus's endgame king activity

    def evaluate(self, board: chess.Board) -> int:
        """Evaluate position in centipawns (positive = White advantage)."""
        if board.is_checkmate():
            return -30000 if board.turn == chess.WHITE else 30000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        if board.can_claim_draw():
            return 0

        phase = self._game_phase(board)
        score = 0

        score += self._material(board)
        score += self._piece_square(board, phase)
        score += self._mobility(board)
        score += self._pawn_structure(board)
        score += self._king_safety(board, phase)
        score += self._bishop_pair(board)
        score += self._rook_activity(board)
        score += self._passed_pawns(board)
        score += self._space_control(board)
        score += self._center_control(board)

        return score

    # ── Component Evaluations ───────────────────────────────────

    def _material(self, board: chess.Board) -> int:
        """Raw material count."""
        score = 0
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p:
                val = PIECE_VALUES.get(p.symbol(), 0)
                score += val if p.color == chess.WHITE else -val
        return int(score * self.WEIGHT_MATERIAL)

    def _piece_square(self, board: chess.Board, phase: float) -> int:
        """Piece-square table bonuses."""
        score = 0
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if not p:
                continue

            if p.piece_type == chess.KING:
                mg = KING_MIDDLEGAME_TABLE[sq if p.color == chess.WHITE
                                           else chess.square_mirror(sq)]
                eg = KING_ENDGAME_TABLE[sq if p.color == chess.WHITE
                                        else chess.square_mirror(sq)]
                val = int(mg * phase + eg * (1 - phase))
                # Magnus bonus: extra king activity weight in endgame
                if phase < 0.4:
                    val = int(val * self.WEIGHT_ENDGAME_KING)
            else:
                table = PST.get(p.piece_type)
                if table:
                    idx = sq if p.color == chess.WHITE else chess.square_mirror(sq)
                    val = table[idx]
                else:
                    val = 0

            score += val if p.color == chess.WHITE else -val
        return int(score * self.WEIGHT_PST)

    def _mobility(self, board: chess.Board) -> int:
        """Piece mobility — number of legal moves available."""
        white_mob = len(list(board.legal_moves))
        board.push(chess.Move.null())
        black_mob = len(list(board.legal_moves))
        board.pop()
        return int((white_mob - black_mob) * self.WEIGHT_MOBILITY
                    * (100 if board.turn == chess.WHITE else -100) / 30)

    def _pawn_structure(self, board: chess.Board) -> int:
        """Evaluate pawn structure: doubled, isolated, backward pawns."""
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            pawns = board.pieces(chess.PAWN, color)
            files_with_pawns = set()
            doubled = 0
            isolated = 0

            file_counts = [0] * 8
            for sq in pawns:
                f = chess.square_file(sq)
                file_counts[f] += 1
                files_with_pawns.add(f)

            for f in range(8):
                if file_counts[f] > 1:
                    doubled += file_counts[f] - 1
                if file_counts[f] > 0:
                    has_neighbor = False
                    if f > 0 and file_counts[f - 1] > 0:
                        has_neighbor = True
                    if f < 7 and file_counts[f + 1] > 0:
                        has_neighbor = True
                    if not has_neighbor:
                        isolated += file_counts[f]

            penalty = doubled * 15 + isolated * 20
            if color == chess.WHITE:
                score -= penalty
            else:
                score += penalty

        return int(score * self.WEIGHT_PAWN_STRUCTURE)

    def _king_safety(self, board: chess.Board, phase: float) -> int:
        """King safety based on pawn shield and attackers."""
        if phase < 0.3:
            return 0  # endgame: king safety less relevant

        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            king_sq = board.king(color)
            if king_sq is None:
                continue
            king_file = chess.square_file(king_sq)
            king_rank = chess.square_rank(king_sq)

            # Pawn shield bonus
            shield = 0
            direction = 1 if color == chess.WHITE else -1
            for df in [-1, 0, 1]:
                f = king_file + df
                if 0 <= f <= 7:
                    shield_rank = king_rank + direction
                    if 0 <= shield_rank <= 7:
                        sq = chess.square(f, shield_rank)
                        p = board.piece_at(sq)
                        if p and p.piece_type == chess.PAWN and p.color == color:
                            shield += 10

            # Attacker penalty
            attackers = len(board.attackers(not color, king_sq))
            penalty = attackers * 15

            safety = shield - penalty
            if color == chess.WHITE:
                score += safety
            else:
                score -= safety

        return int(score * self.WEIGHT_KING_SAFETY * phase)

    def _bishop_pair(self, board: chess.Board) -> int:
        """Bonus for having the bishop pair — Magnus utilises this well."""
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            bishops = board.pieces(chess.BISHOP, color)
            if len(bishops) >= 2:
                bonus = 50
                if color == chess.WHITE:
                    score += bonus
                else:
                    score -= bonus
        return int(score * self.WEIGHT_BISHOP_PAIR)

    def _rook_activity(self, board: chess.Board) -> int:
        """Bonus for rooks on open/semi-open files and 7th rank."""
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            rooks = board.pieces(chess.ROOK, color)
            for sq in rooks:
                f = chess.square_file(sq)
                r = chess.square_rank(sq)
                # Open file
                own_pawns = any(
                    board.piece_at(chess.square(f, rr))
                    and board.piece_at(chess.square(f, rr)).piece_type == chess.PAWN
                    and board.piece_at(chess.square(f, rr)).color == color
                    for rr in range(8)
                )
                opp_pawns = any(
                    board.piece_at(chess.square(f, rr))
                    and board.piece_at(chess.square(f, rr)).piece_type == chess.PAWN
                    and board.piece_at(chess.square(f, rr)).color != color
                    for rr in range(8)
                )
                if not own_pawns and not opp_pawns:
                    bonus = 25  # open file
                elif not own_pawns:
                    bonus = 15  # semi-open
                else:
                    bonus = 0
                # 7th rank bonus
                seventh = 6 if color == chess.WHITE else 1
                if r == seventh:
                    bonus += 30

                if color == chess.WHITE:
                    score += bonus
                else:
                    score -= bonus
        return int(score * self.WEIGHT_ROOK_OPEN_FILE)

    def _passed_pawns(self, board: chess.Board) -> int:
        """Evaluate passed pawns — crucial for Magnus's endgame grinding."""
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            pawns = board.pieces(chess.PAWN, color)
            for sq in pawns:
                f = chess.square_file(sq)
                r = chess.square_rank(sq)
                is_passed = True
                # Check files f-1, f, f+1 for opponent pawns ahead
                opp = not color
                for df in [-1, 0, 1]:
                    cf = f + df
                    if 0 <= cf <= 7:
                        if color == chess.WHITE:
                            for rr in range(r + 1, 8):
                                p = board.piece_at(chess.square(cf, rr))
                                if p and p.piece_type == chess.PAWN and p.color == opp:
                                    is_passed = False
                                    break
                        else:
                            for rr in range(0, r):
                                p = board.piece_at(chess.square(cf, rr))
                                if p and p.piece_type == chess.PAWN and p.color == opp:
                                    is_passed = False
                                    break
                    if not is_passed:
                        break

                if is_passed:
                    bonus = PASSED_PAWN_BONUS[r if color == chess.WHITE else 7 - r]
                    if color == chess.WHITE:
                        score += bonus
                    else:
                        score -= bonus

        return int(score * self.WEIGHT_PASSED_PAWN)

    def _space_control(self, board: chess.Board) -> int:
        """Space advantage — squares controlled in opponent's half.
        Magnus excels at squeezing opponents with space advantage."""
        w_space = 0
        b_space = 0
        for sq in chess.SQUARES:
            r = chess.square_rank(sq)
            if r >= 4:  # Black's half
                w_space += len(board.attackers(chess.WHITE, sq))
            if r <= 3:  # White's half
                b_space += len(board.attackers(chess.BLACK, sq))
        return int((w_space - b_space) * self.WEIGHT_SPACE)

    def _center_control(self, board: chess.Board) -> int:
        """Bonus for controlling central squares (d4, d5, e4, e5)."""
        center = [chess.D4, chess.D5, chess.E4, chess.E5]
        extended = [chess.C3, chess.C4, chess.C5, chess.C6,
                    chess.D3, chess.D6, chess.E3, chess.E6,
                    chess.F3, chess.F4, chess.F5, chess.F6]
        score = 0
        for sq in center:
            w = len(board.attackers(chess.WHITE, sq))
            b = len(board.attackers(chess.BLACK, sq))
            score += (w - b) * 12
            p = board.piece_at(sq)
            if p:
                if p.color == chess.WHITE:
                    score += 15
                else:
                    score -= 15
        for sq in extended:
            w = len(board.attackers(chess.WHITE, sq))
            b = len(board.attackers(chess.BLACK, sq))
            score += (w - b) * 5
        return int(score * self.WEIGHT_CENTER_CONTROL)

    # ── Utility ─────────────────────────────────────────────────

    @staticmethod
    def _game_phase(board: chess.Board) -> float:
        """Return game phase as 0.0 (endgame) → 1.0 (opening)."""
        material = 0
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p and p.piece_type != chess.KING:
                material += PIECE_VALUES.get(p.symbol().upper(), 0)
        # Opening total ≈ 7800 (without kings)
        return min(1.0, material / 7800)
