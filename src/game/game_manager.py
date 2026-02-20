"""
Central game manager — coordinates all game systems.

Handles player input, AI moves, game state transitions,
and delegates rendering to the UI modules.
"""

from __future__ import annotations

import chess
import pygame
import threading
import time
from typing import Optional

from src.engine.chess_engine import ChessEngine
from src.engine.ai_engine import AIEngine
from src.engine.opening_book import OpeningBook
from src.narrative.battle_narrator import BattleNarrator
from src.game.move_history import MoveHistory
from src.game.clock import ChessClock
from src.game.sound_manager import SoundManager
from src.game.save_load import SaveLoadManager
from src.game.post_game_analysis import PostGameAnalyzer, GameAnalysis
from src.competitive.ranking import RankingEngine, RatingChange
from src.competitive.stats import StatsTracker
from src.competitive.achievements import AchievementEngine, AchievementDef
from src.competitive.prizes import PrizeManager
from src.utils.config import Config
from src.utils.constants import (
    BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE,
    DIFFICULTIES, AI_THINK_DELAY,
)
from src.utils.helpers import (
    pixel_to_board, coords_to_square, algebraic_to_coords,
    get_game_phase, get_captured_pieces, get_material_balance,
)


class GameManager:
    """Central game controller — owns all game state."""

    def __init__(self, config: Config):
        self.config = config
        self.engine = ChessEngine()
        self.ai = AIEngine(config.get("difficulty", "SOLDIER"))
        self.narrator = BattleNarrator()
        self.history = MoveHistory()
        self.clock = ChessClock(config.get("time_control", "unlimited"))
        self.opening_book = OpeningBook()
        self.sound = SoundManager(
            enabled=config.get("sound_enabled", True),
            volume=config.get("volume", 0.7),
        )
        self.save_manager = SaveLoadManager()
        self.analyzer = PostGameAnalyzer()
        self.ranking = RankingEngine()
        self.stats_tracker = StatsTracker()
        self.achievements = AchievementEngine()
        self.prize_manager = PrizeManager()
        self.arena_adapter = None  # Set externally for arena mode
        self.arena_manager = None  # Set externally for arena mode
        self.last_analysis: Optional[GameAnalysis] = None
        self.last_rating_change: Optional[RatingChange] = None
        self.last_unlocked_achievements: list[AchievementDef] = []

        # Player settings
        self.player_color = chess.WHITE if config.get("player_color") == "white" else chess.BLACK
        self.flipped = config.get("flip_board", False)
        if self.player_color == chess.BLACK:
            self.flipped = True

        # Interaction state
        self.selected_square: Optional[int] = None
        self.valid_moves: list[chess.Move] = []
        self.dragging = False
        self.drag_piece: Optional[chess.Piece] = None
        self.drag_from: Optional[int] = None
        self.drag_pos: tuple[int, int] = (0, 0)

        # Game state
        self.game_over = False
        self.result_text = ""
        self.result_narrative = ""
        self.ai_thinking = False
        self.last_move: Optional[chess.Move] = None
        self.opening_name: Optional[str] = None
        self.intro_narrative = self.narrator.get_opening_text()

        # Animation state
        self.animating = False
        self.anim_start_pos: tuple[int, int] = (0, 0)
        self.anim_end_pos: tuple[int, int] = (0, 0)
        self.anim_piece: Optional[chess.Piece] = None
        self.anim_progress = 0.0
        self.anim_move: Optional[chess.Move] = None

        # Promotion state
        self.promoting = False
        self.promotion_from: Optional[int] = None
        self.promotion_to: Optional[int] = None

        # Evaluation
        self.eval_score = 0

    # ── Public API ──────────────────────────────────────────────

    def new_game(self, difficulty: str | None = None, player_color: str = "white") -> None:
        """Start a fresh game."""
        if difficulty:
            self.ai.set_difficulty(difficulty)
            self.config.set("difficulty", difficulty)
        self.engine.new_game()
        self.ai.clear_tt()
        self.narrator.reset()
        self.history.clear()
        self.clock.reset(self.config.get("time_control", "unlimited"))

        self.player_color = chess.WHITE if player_color == "white" else chess.BLACK
        self.flipped = self.player_color == chess.BLACK

        self.selected_square = None
        self.valid_moves = []
        self.game_over = False
        self.result_text = ""
        self.result_narrative = ""
        self.ai_thinking = False
        self.last_move = None
        self.opening_name = None
        self.promoting = False
        self.eval_score = 0
        self.intro_narrative = self.narrator.get_opening_text()
        self.last_rating_change = None
        self.last_unlocked_achievements = []

        self.sound.play("game_start")

        # If player is Black, AI moves first
        if self.player_color == chess.BLACK:
            self._schedule_ai_move()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a pygame event during gameplay."""
        if self.game_over or self.ai_thinking or self.animating or self.promoting:
            if self.promoting and event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_promotion_click(event.pos)
            return

        if not self._is_player_turn():
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_mouse_down(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._handle_mouse_up(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)

    def update(self, dt: float) -> None:
        """Per-frame update (dt in seconds)."""
        self.clock.update()

        # Check flag
        if self.clock.is_flagged and not self.game_over:
            self.game_over = True
            if self.clock.is_white_flagged:
                self.result_text = "0-1 (White flagged)"
            else:
                self.result_text = "1-0 (Black flagged)"
            self.result_narrative = "Time runs out! The clock claims victory!"

        # Animation update
        if self.animating:
            self.anim_progress += dt / 0.2  # 0.2s animation
            if self.anim_progress >= 1.0:
                self.anim_progress = 1.0
                self.animating = False
                if self.anim_move:
                    self._finalize_move(self.anim_move)

    # ── Properties for UI ───────────────────────────────────────

    @property
    def board(self) -> chess.Board:
        return self.engine.board

    @property
    def current_narratives(self) -> list[str]:
        narrs = self.history.get_recent_narratives(6)
        if not narrs:
            return [self.intro_narrative]
        return narrs

    @property
    def move_pairs(self) -> list[str]:
        return self.history.get_formatted_pairs()

    @property
    def captured(self) -> tuple[list[str], list[str]]:
        return get_captured_pieces(self.engine.board)

    @property
    def material_balance(self) -> int:
        return get_material_balance(self.engine.board)

    @property
    def game_phase(self) -> str:
        return get_game_phase(self.engine.board)

    @property
    def difficulty_name(self) -> str:
        diff = self.config.get("difficulty", "SOLDIER")
        return DIFFICULTIES.get(diff, {}).get("name", diff)

    # ── Internal: Input Handling ────────────────────────────────

    def _is_player_turn(self) -> bool:
        return self.engine.turn == self.player_color

    def _handle_mouse_down(self, pos: tuple[int, int]) -> None:
        board_pos = pixel_to_board(
            pos[0], pos[1],
            BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE,
            self.flipped,
        )
        if board_pos is None:
            self.selected_square = None
            self.valid_moves = []
            return

        col, row = board_pos
        square = coords_to_square(col, row)
        piece = self.engine.piece_at(square)

        # If a piece is already selected, try to move there
        if self.selected_square is not None:
            target_move = self._find_move(self.selected_square, square)
            if target_move:
                self._try_make_move(target_move)
                return

        # Select a new piece
        if piece and piece.color == self.player_color:
            self.selected_square = square
            self.valid_moves = self.engine.get_legal_moves_from(square)
            self.dragging = True
            self.drag_piece = piece
            self.drag_from = square
            self.drag_pos = pos
        else:
            self.selected_square = None
            self.valid_moves = []

    def _handle_mouse_up(self, pos: tuple[int, int]) -> None:
        if not self.dragging:
            return

        self.dragging = False
        board_pos = pixel_to_board(
            pos[0], pos[1],
            BOARD_OFFSET_X, BOARD_OFFSET_Y, SQUARE_SIZE,
            self.flipped,
        )

        if board_pos is not None and self.drag_from is not None:
            col, row = board_pos
            square = coords_to_square(col, row)
            if square != self.drag_from:
                target_move = self._find_move(self.drag_from, square)
                if target_move:
                    self._try_make_move(target_move)
                    return

        # If drop on same square or invalid, deselect
        self.drag_piece = None
        self.drag_from = None

    def _handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        if self.dragging:
            self.drag_pos = pos

    def _find_move(self, from_sq: int, to_sq: int) -> Optional[chess.Move]:
        """Find a legal move from from_sq to to_sq, handling promotion."""
        for move in self.engine.board.legal_moves:
            if move.from_square == from_sq and move.to_square == to_sq:
                if move.promotion:
                    # Need to ask for promotion choice
                    return move  # Return queen promotion by default; UI will handle
                return move
        return None

    def _try_make_move(self, move: chess.Move) -> None:
        """Attempt to execute a player move."""
        # Check for promotion
        if self.engine.is_promotion_move(move.from_square, move.to_square):
            if self.config.get("auto_queen_promote", False):
                move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)
            else:
                self.promoting = True
                self.promotion_from = move.from_square
                self.promotion_to = move.to_square
                self.selected_square = None
                self.valid_moves = []
                self.dragging = False
                return

        self._execute_move(move)

    def _handle_promotion_click(self, pos: tuple[int, int]) -> None:
        """Handle promotion piece selection."""
        # Simple promotion UI: display 4 options near the promotion square
        # For now, map click position to piece choices
        if self.promotion_to is None:
            return

        col, row = algebraic_to_coords(self.promotion_to)
        if self.flipped:
            col, row = 7 - col, 7 - row

        base_x = BOARD_OFFSET_X + col * SQUARE_SIZE
        base_y = BOARD_OFFSET_Y + row * SQUARE_SIZE

        pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        for i, piece_type in enumerate(pieces):
            px = base_x
            py = base_y + i * SQUARE_SIZE if self.player_color == chess.WHITE else base_y - i * SQUARE_SIZE
            rect = pygame.Rect(px, py, SQUARE_SIZE, SQUARE_SIZE)
            if rect.collidepoint(pos):
                move = chess.Move(self.promotion_from, self.promotion_to, promotion=piece_type)
                self.promoting = False
                self.promotion_from = None
                self.promotion_to = None
                self._execute_move(move)
                return

    # ── Internal: Move Execution ────────────────────────────────

    def _execute_move(self, move: chess.Move) -> None:
        """Execute a move (player or AI), record it, and trigger AI if needed."""
        board = self.engine.board

        # Generate narrative BEFORE the move
        narrative = self.narrator.narrate_move(board, move)
        san = board.san(move)
        is_white = board.turn == chess.WHITE
        move_number = board.fullmove_number

        # Opening detection
        self.opening_name = self.opening_book.get_opening_name(board)

        # Record move
        self.history.add_move(
            san=san,
            uci=move.uci(),
            narrative=narrative,
            move_number=move_number,
            is_white=is_white,
            is_capture=board.is_capture(move),
            is_check=board.gives_check(move),
            is_checkmate=False,  # Updated after push
            is_castling=board.is_castling(move),
            opening_name=self.opening_name,
        )

        # Play sound
        is_checkmate_sound = False
        is_check_sound = board.gives_check(move)
        self.sound.play_move(
            is_capture=board.is_capture(move),
            is_check=is_check_sound,
            is_checkmate=is_checkmate_sound,
            is_castling=board.is_castling(move),
            is_promotion=move.promotion is not None,
        )

        # Execute on board
        self.engine.make_move(move)
        self.last_move = move

        # Clock
        if self.history.count == 1:
            self.clock.start()
        else:
            self.clock.switch()

        # Clear selection
        self.selected_square = None
        self.valid_moves = []
        self.dragging = False
        self.drag_piece = None

        # Update eval
        self.eval_score = get_material_balance(self.engine.board)

        # Check game over
        if self.engine.is_game_over:
            self._handle_game_over()
            return

        # If it's now AI's turn, schedule AI move
        if not self._is_player_turn():
            self._schedule_ai_move()

    def _schedule_ai_move(self) -> None:
        """Run AI thinking in a background thread."""
        self.ai_thinking = True

        # Use external arena adapter if set
        if self.arena_adapter is not None:
            self._schedule_arena_ai_move()
            return

        def think():
            time.sleep(AI_THINK_DELAY)
            move = self.ai.get_best_move(self.engine.board)
            if move:
                # Post a custom event to execute on the main thread
                pygame.event.post(pygame.event.Event(
                    pygame.USEREVENT + 1,
                    {"ai_move": move},
                ))

        thread = threading.Thread(target=think, daemon=True)
        thread.start()

    def _schedule_arena_ai_move(self) -> None:
        """Run external AI (arena adapter) thinking in a background thread."""
        move_history = [m.uci for m in self.history.moves]

        def think():
            result = self.arena_adapter.get_move(self.engine.board, move_history)
            if result.uci_move and not result.error:
                try:
                    move = chess.Move.from_uci(result.uci_move)
                    if move in self.engine.board.legal_moves:
                        pygame.event.post(pygame.event.Event(
                            pygame.USEREVENT + 1,
                            {"ai_move": move},
                        ))
                        return
                except (ValueError, chess.InvalidMoveError):
                    pass
            # Fallback to built-in AI on failure
            time.sleep(AI_THINK_DELAY)
            move = self.ai.get_best_move(self.engine.board)
            if move:
                pygame.event.post(pygame.event.Event(
                    pygame.USEREVENT + 1,
                    {"ai_move": move},
                ))

        thread = threading.Thread(target=think, daemon=True)
        thread.start()

    def handle_ai_move_event(self, move: chess.Move) -> None:
        """Called from the main loop when AI finishes thinking."""
        self.ai_thinking = False
        if move and move in self.engine.board.legal_moves:
            self._execute_move(move)

    def _finalize_move(self, move: chess.Move) -> None:
        """Called after animation completes."""
        pass  # Move already executed before animation in current flow

    def _handle_game_over(self) -> None:
        """Process end of game."""
        self.game_over = True
        self.clock.stop()
        board = self.engine.board
        self.result_text = board.result()
        self.result_narrative = self.narrator.narrate_game_result(board)
        self.sound.play("game_over")

        # Update last move record if it was checkmate
        if board.is_checkmate() and self.history.last_move:
            self.history.last_move.is_checkmate = True

        # Auto-save
        try:
            self.save_manager.auto_save(
                board, self.history,
                self.config.get("player_color", "white"),
                self.config.get("difficulty", "SOLDIER"),
                self.opening_name or "",
                self.result_text,
            )
        except Exception:
            pass

        # Run analysis
        try:
            self.last_analysis = self.analyzer.analyze(
                self.history, board,
                self.opening_name or "Unknown",
                self.result_text,
            )
        except Exception:
            self.last_analysis = None

        # Process ranking & stats
        try:
            difficulty = self.config.get("difficulty", "SOLDIER")
            player_color = self.config.get("player_color", "white")
            game_mode = self.config.get("game_mode", "ranked")
            accuracy = self.last_analysis.accuracy if self.last_analysis else None

            # Count captures and checks for stats
            captures = sum(1 for m in self.history.moves if m.is_capture)
            player_moves = [m for m in self.history.moves if m.color == player_color]
            checks = sum(1 for m in player_moves if m.is_check)
            castled = any(m.is_castling for m in player_moves)
            duration = self.clock.elapsed_seconds if hasattr(self.clock, 'elapsed_seconds') else 0.0

            self.last_rating_change = self.ranking.process_match(
                player_name=self.config.get("player_name", "Player"),
                difficulty=difficulty,
                result=self.result_text,
                player_color=player_color,
                moves_count=self.history.count,
                duration=duration,
                opening_name=self.opening_name or "",
                accuracy=accuracy,
                game_mode=game_mode,
            )

            # Record detailed stats
            player_won = (
                (self.result_text == "1-0" and player_color == "white") or
                (self.result_text == "0-1" and player_color == "black")
            )
            self.stats_tracker.record_game_stats(
                player_name=self.config.get("player_name", "Player"),
                moves_count=len(player_moves),
                captures=captures,
                checks=checks,
                castled=castled,
                accuracy=accuracy,
                won=player_won,
                duration=duration,
            )

            # Track fast wins for achievements
            if player_won and self.history.count <= 40:  # ≤20 full moves
                from src.competitive.stats import StatsTracker
                st = StatsTracker()
                st.increment_stat(self.config.get("player_name", "Player"), "fast_wins", 1)

            # Check achievements
            match_context = {
                "difficulty": difficulty,
                "player_won": player_won,
                "player_color": player_color,
                "moves_count": self.history.count,
            }
            self.last_unlocked_achievements = self.achievements.check_unlocks(
                self.config.get("player_name", "Player"),
                match_context,
            )

            # Award prizes from unlocked achievements
            for ach in self.last_unlocked_achievements:
                if ach.prize_id:
                    self.prize_manager.award_prize(
                        self.config.get("player_name", "Player"),
                        ach.prize_id,
                        source="achievement",
                    )

            # Resolve any pending wager
            pending = self.prize_manager.get_pending_wager(
                self.config.get("player_name", "Player")
            )
            if pending:
                self.prize_manager.resolve_wager(pending["id"], player_won)

        except Exception:
            self.last_rating_change = None

    def save_game(self) -> str:
        """Manually save the current game. Returns filepath."""
        return self.save_manager.save_game(
            self.engine.board, self.history,
            self.config.get("player_color", "white"),
            self.config.get("difficulty", "SOLDIER"),
            self.opening_name or "",
            self.result_text if self.game_over else "*",
        )

    def get_pgn_string(self) -> str:
        """Get the current game as a PGN string."""
        return self.save_manager.export_pgn_string(
            self.engine.board, self.history,
            self.config.get("player_color", "white"),
            self.config.get("difficulty", "SOLDIER"),
            self.result_text if self.game_over else "*",
        )
