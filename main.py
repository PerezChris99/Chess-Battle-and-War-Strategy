"""
Chess Battle & War Strategy — Main Entry Point.

Launches the Pygame application, manages the top-level game loop,
and delegates to the appropriate screen (menu, game, tutorial, settings).
"""

from __future__ import annotations

import sys
import os

# Ensure project root is on the import path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pygame

from src.utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE, BG_COLOR,
    STATE_MENU, STATE_PLAYING, STATE_GAME_OVER,
    STATE_TUTORIAL, STATE_SETTINGS,
)
from src.utils.config import Config
from src.game.game_manager import GameManager
from src.ui.board_renderer import BoardRenderer
from src.ui.hud import HUD
from src.ui.menu import MainMenu, NewGameSetup, SettingsMenu
from src.ui.analysis_screen import AnalysisScreen
from src.tutorial.lesson_manager import LessonManager


# Custom event for AI move completion
AI_MOVE_EVENT = pygame.USEREVENT + 1


class Application:
    """Top-level application — owns the Pygame window and game loop."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Configuration
        self.config = Config()

        # Screens
        self.main_menu = MainMenu()
        self.new_game_setup = NewGameSetup()
        self.settings_menu = SettingsMenu(self.config)
        self.lesson_manager = LessonManager(self.config)
        self.analysis_screen = AnalysisScreen()

        # Game state
        self.state = STATE_MENU
        self.sub_state = "MAIN"  # "MAIN", "NEW_GAME_SETUP"
        self.game_manager: GameManager | None = None
        self.board_renderer = BoardRenderer()
        self.hud = HUD()

    def run(self) -> None:
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # delta time in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                self._handle_event(event)

            self._update(dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # ── Event Handling ──────────────────────────────────────────

    def _handle_event(self, event: pygame.event.Event) -> None:
        # Global key handling
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == STATE_PLAYING:
                    self.state = STATE_MENU
                    self.sub_state = "MAIN"
                    return

        # AI move event
        if event.type == AI_MOVE_EVENT and self.game_manager:
            ai_move = event.__dict__.get("ai_move")
            if ai_move:
                self.game_manager.handle_ai_move_event(ai_move)
            return

        # Delegate to current screen
        if self.state == STATE_MENU:
            self._handle_menu_event(event)
        elif self.state == STATE_PLAYING:
            self._handle_game_event(event)
        elif self.state == STATE_TUTORIAL:
            self._handle_tutorial_event(event)
        elif self.state == STATE_SETTINGS:
            self._handle_settings_event(event)
        elif self.state == "ANALYSIS":
            self._handle_analysis_event(event)

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        if self.sub_state == "MAIN":
            result = self.main_menu.handle_event(event)
            if result == "NEW_GAME_SETUP":
                self.sub_state = "NEW_GAME_SETUP"
            elif result == "TUTORIAL":
                self.state = STATE_TUTORIAL
            elif result == "SETTINGS":
                self.state = STATE_SETTINGS
            elif result == "QUIT":
                self.running = False

        elif self.sub_state == "NEW_GAME_SETUP":
            result = self.new_game_setup.handle_event(event)
            if result == "BACK":
                self.sub_state = "MAIN"
            elif isinstance(result, dict) and result.get("action") == "START_GAME":
                self._start_game(
                    difficulty=result["difficulty"],
                    player_color=result["color"],
                    time_control=result["time_control"],
                )

    def _handle_game_event(self, event: pygame.event.Event) -> None:
        if not self.game_manager:
            return

        # Game-over key handling
        if self.game_manager.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Restart with same settings
                    self.game_manager.new_game(
                        self.config.get("difficulty"),
                        self.config.get("player_color", "white"),
                    )
                elif event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU
                    self.sub_state = "MAIN"
                elif event.key == pygame.K_a:
                    # Show analysis
                    if self.game_manager.last_analysis:
                        self.analysis_screen.set_analysis(self.game_manager.last_analysis)
                        self.state = "ANALYSIS"
                elif event.key == pygame.K_s:
                    # Save game
                    try:
                        path = self.game_manager.save_game()
                    except Exception:
                        pass
            return

        self.game_manager.handle_event(event)

    def _handle_tutorial_event(self, event: pygame.event.Event) -> None:
        result = self.lesson_manager.handle_event(event)
        if result == "BACK":
            self.state = STATE_MENU
            self.sub_state = "MAIN"

    def _handle_settings_event(self, event: pygame.event.Event) -> None:
        result = self.settings_menu.handle_event(event)
        if result == "BACK":
            self.state = STATE_MENU
            self.sub_state = "MAIN"

    def _handle_analysis_event(self, event: pygame.event.Event) -> None:
        result = self.analysis_screen.handle_event(event)
        if result == "BACK":
            self.state = STATE_PLAYING
        elif result == "SAVE":
            if self.game_manager:
                try:
                    self.game_manager.save_game()
                except Exception:
                    pass

    # ── Game Management ─────────────────────────────────────────

    def _start_game(self, difficulty: str, player_color: str, time_control: str) -> None:
        """Initialize and start a new game."""
        self.config.update({
            "difficulty": difficulty,
            "player_color": player_color,
            "time_control": time_control,
        })
        self.game_manager = GameManager(self.config)
        self.game_manager.new_game(difficulty, player_color)
        self.state = STATE_PLAYING
        self.sub_state = "MAIN"

    # ── Update ──────────────────────────────────────────────────

    def _update(self, dt: float) -> None:
        if self.state == STATE_PLAYING and self.game_manager:
            self.game_manager.update(dt)

    # ── Drawing ─────────────────────────────────────────────────

    def _draw(self) -> None:
        if self.state == STATE_MENU:
            if self.sub_state == "MAIN":
                self.main_menu.draw(self.screen)
            elif self.sub_state == "NEW_GAME_SETUP":
                self.new_game_setup.draw(self.screen)

        elif self.state == STATE_PLAYING and self.game_manager:
            self._draw_game()

        elif self.state == STATE_TUTORIAL:
            self.lesson_manager.draw(self.screen)

        elif self.state == STATE_SETTINGS:
            self.settings_menu.draw(self.screen)

        elif self.state == "ANALYSIS":
            self.analysis_screen.draw(self.screen)

    def _draw_game(self) -> None:
        gm = self.game_manager
        self.screen.fill(BG_COLOR)

        # Board
        self.board_renderer.draw(
            self.screen,
            gm.board,
            selected_square=gm.selected_square,
            valid_moves=gm.valid_moves,
            last_move=gm.last_move,
            flipped=gm.flipped,
            drag_from=gm.drag_from if gm.dragging else None,
            drag_piece=gm.drag_piece if gm.dragging else None,
            drag_pos=gm.drag_pos if gm.dragging else None,
            promoting=gm.promoting,
            promotion_square=gm.promotion_to,
            player_color=gm.player_color,
        )

        # HUD
        wc, bc = gm.captured
        self.hud.draw(
            self.screen,
            move_pairs=gm.move_pairs,
            narratives=gm.current_narratives,
            white_clock=gm.clock.white_display,
            black_clock=gm.clock.black_display,
            white_captured=wc,
            black_captured=bc,
            eval_score=gm.eval_score,
            difficulty_name=gm.difficulty_name,
            opening_name=gm.opening_name,
            game_phase=gm.game_phase,
            is_player_turn=gm._is_player_turn(),
            ai_thinking=gm.ai_thinking,
            game_over=gm.game_over,
            result_text=gm.result_text,
            result_narrative=gm.result_narrative,
            flipped=gm.flipped,
        )


def main():
    """Entry point."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
