"""
Heads-Up Display — in-game information panels.

Renders:
  • Move history panel (right side)
  • Battle narrative panel (right side, below moves)
  • Clock display (top bar)
  • Captured pieces display
  • Evaluation bar
  • Opening name
  • Game phase indicator
"""

from __future__ import annotations

import pygame
import chess

from src.utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    RIGHT_PANEL_X, RIGHT_PANEL_WIDTH, RIGHT_PANEL_Y,
    TOP_BAR_HEIGHT, BOTTOM_BAR_Y, BOTTOM_BAR_HEIGHT, BOARD_OFFSET_X,
    BOARD_SIZE,
    BG_COLOR, PANEL_BG, PANEL_BORDER, HEADER_BG,
    TEXT_COLOR, TEXT_DIM, TEXT_GOLD, TEXT_RED, TEXT_GREEN, TEXT_BLUE, TEXT_WHITE,
    EVAL_WHITE, EVAL_BLACK,
    UNICODE_PIECES, DIFFICULTIES,
)


class HUD:
    """In-game heads-up display with move list, narrative, and info panels."""

    def __init__(self):
        pygame.font.init()
        self._title_font     = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self._header_font    = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self._move_font      = pygame.font.SysFont("Consolas", 15)
        self._narrative_font = pygame.font.SysFont("Georgia", 14, italic=True)
        self._clock_font     = pygame.font.SysFont("Consolas", 28, bold=True)
        self._small_font     = pygame.font.SysFont("Segoe UI", 13)
        self._piece_font     = pygame.font.SysFont("Segoe UI Symbol", 18)
        self._label_font     = pygame.font.SysFont("Segoe UI", 12)
        self._scroll_offset  = 0  # for move list scrolling

    def draw(
        self,
        screen: pygame.Surface,
        move_pairs: list[str],
        narratives: list[str],
        white_clock: str,
        black_clock: str,
        white_captured: list[str],
        black_captured: list[str],
        eval_score: int,
        difficulty_name: str,
        opening_name: str | None,
        game_phase: str,
        is_player_turn: bool,
        ai_thinking: bool,
        game_over: bool,
        result_text: str,
        result_narrative: str,
        flipped: bool,
    ) -> None:
        """Draw all HUD elements."""
        self._draw_top_bar(
            screen, white_clock, black_clock,
            difficulty_name, is_player_turn, ai_thinking, flipped,
        )
        self._draw_move_panel(screen, move_pairs, opening_name)
        self._draw_narrative_panel(screen, narratives)
        self._draw_bottom_bar(
            screen, white_captured, black_captured,
            eval_score, game_phase,
        )
        self._draw_eval_bar(screen, eval_score)

        if game_over:
            self._draw_game_over(screen, result_text, result_narrative)

    # ── Top Bar ─────────────────────────────────────────────────

    def _draw_top_bar(
        self, screen: pygame.Surface,
        white_clock: str, black_clock: str,
        difficulty_name: str,
        is_player_turn: bool, ai_thinking: bool,
        flipped: bool,
    ) -> None:
        bar = pygame.Rect(0, 0, WINDOW_WIDTH, TOP_BAR_HEIGHT)
        pygame.draw.rect(screen, HEADER_BG, bar)
        pygame.draw.line(screen, PANEL_BORDER, (0, TOP_BAR_HEIGHT), (WINDOW_WIDTH, TOP_BAR_HEIGHT))

        # Title
        title = self._title_font.render("⚔  CHESS BATTLE & WAR STRATEGY", True, TEXT_GOLD)
        screen.blit(title, (20, 15))

        # Clocks
        # Bottom clock = player, top clock = opponent
        top_clock = black_clock if not flipped else white_clock
        bot_clock = white_clock if not flipped else black_clock
        top_label = "BLACK" if not flipped else "WHITE"
        bot_label = "WHITE" if not flipped else "BLACK"

        # Draw both clocks in top bar
        cx = WINDOW_WIDTH - 300
        # Opponent clock
        lbl = self._label_font.render(top_label, True, TEXT_DIM)
        screen.blit(lbl, (cx, 8))
        clk = self._clock_font.render(top_clock, True, TEXT_COLOR)
        screen.blit(clk, (cx + 55, 2))

        # Player clock
        lbl2 = self._label_font.render(bot_label, True, TEXT_DIM)
        screen.blit(lbl2, (cx, 38))
        clk2_color = TEXT_GREEN if is_player_turn else TEXT_COLOR
        clk2 = self._clock_font.render(bot_clock, True, clk2_color)
        screen.blit(clk2, (cx + 55, 32))

        # Difficulty badge
        badge = self._small_font.render(f"⚔ {difficulty_name}", True, TEXT_GOLD)
        screen.blit(badge, (cx - 130, 25))

        # AI thinking indicator
        if ai_thinking:
            dots = "." * (pygame.time.get_ticks() // 400 % 4)
            think = self._small_font.render(f"AI thinking{dots}", True, TEXT_BLUE)
            screen.blit(think, (cx - 130, 8))

    # ── Move Panel ──────────────────────────────────────────────

    def _draw_move_panel(
        self, screen: pygame.Surface,
        move_pairs: list[str],
        opening_name: str | None,
    ) -> None:
        panel_h = 280
        panel = pygame.Rect(RIGHT_PANEL_X, RIGHT_PANEL_Y, RIGHT_PANEL_WIDTH, panel_h)
        pygame.draw.rect(screen, PANEL_BG, panel)
        pygame.draw.rect(screen, PANEL_BORDER, panel, 1)

        # Header
        header = pygame.Rect(RIGHT_PANEL_X, RIGHT_PANEL_Y, RIGHT_PANEL_WIDTH, 30)
        pygame.draw.rect(screen, HEADER_BG, header)
        title = self._header_font.render("📋  BATTLE LOG", True, TEXT_GOLD)
        screen.blit(title, (RIGHT_PANEL_X + 10, RIGHT_PANEL_Y + 6))

        # Opening name
        y = RIGHT_PANEL_Y + 35
        if opening_name:
            op = self._small_font.render(f"Opening: {opening_name}", True, TEXT_BLUE)
            screen.blit(op, (RIGHT_PANEL_X + 10, y))
            y += 20

        # Move pairs
        clip = pygame.Rect(RIGHT_PANEL_X + 5, y, RIGHT_PANEL_WIDTH - 10, panel_h - (y - RIGHT_PANEL_Y) - 5)
        screen.set_clip(clip)

        visible_lines = (clip.height) // 20
        start = max(0, len(move_pairs) - visible_lines)

        for i, line in enumerate(move_pairs[start:]):
            text_color = TEXT_COLOR if (start + i) == len(move_pairs) - 1 else TEXT_DIM
            rendered = self._move_font.render(line, True, text_color)
            screen.blit(rendered, (RIGHT_PANEL_X + 12, y + i * 20))

        screen.set_clip(None)

    # ── Narrative Panel ─────────────────────────────────────────

    def _draw_narrative_panel(self, screen: pygame.Surface, narratives: list[str]) -> None:
        panel_y = RIGHT_PANEL_Y + 290
        panel_h = 310
        panel = pygame.Rect(RIGHT_PANEL_X, panel_y, RIGHT_PANEL_WIDTH, panel_h)
        pygame.draw.rect(screen, PANEL_BG, panel)
        pygame.draw.rect(screen, PANEL_BORDER, panel, 1)

        # Header
        header = pygame.Rect(RIGHT_PANEL_X, panel_y, RIGHT_PANEL_WIDTH, 30)
        pygame.draw.rect(screen, HEADER_BG, header)
        title = self._header_font.render("⚔  BATTLE NARRATIVE", True, TEXT_GOLD)
        screen.blit(title, (RIGHT_PANEL_X + 10, panel_y + 6))

        # Narrative text with word wrapping
        y = panel_y + 38
        max_width = RIGHT_PANEL_WIDTH - 24
        clip = pygame.Rect(RIGHT_PANEL_X + 5, y - 2, RIGHT_PANEL_WIDTH - 10, panel_h - 42)
        screen.set_clip(clip)

        # Show most recent narratives, most recent at bottom
        display_narratives = narratives[-6:] if narratives else []
        line_y = y

        for narr in display_narratives:
            wrapped = self._wrap_text(narr, self._narrative_font, max_width)
            for line in wrapped:
                if line_y + 18 > panel_y + panel_h:
                    break
                rendered = self._narrative_font.render(line, True, TEXT_COLOR)
                screen.blit(rendered, (RIGHT_PANEL_X + 12, line_y))
                line_y += 18
            line_y += 6  # gap between narratives

        screen.set_clip(None)

    # ── Bottom Bar ──────────────────────────────────────────────

    def _draw_bottom_bar(
        self, screen: pygame.Surface,
        white_captured: list[str],
        black_captured: list[str],
        eval_score: int,
        game_phase: str,
    ) -> None:
        bar = pygame.Rect(0, BOTTOM_BAR_Y, WINDOW_WIDTH, BOTTOM_BAR_HEIGHT + 10)
        pygame.draw.rect(screen, HEADER_BG, bar)
        pygame.draw.line(screen, PANEL_BORDER, (0, BOTTOM_BAR_Y), (WINDOW_WIDTH, BOTTOM_BAR_Y))

        y = BOTTOM_BAR_Y + 10

        # Captured pieces — black's captures (white pieces taken)
        x = BOARD_OFFSET_X
        lbl = self._label_font.render("Captured by enemy:", True, TEXT_DIM)
        screen.blit(lbl, (x, y - 2))
        x += lbl.get_width() + 10
        for sym in white_captured:
            char = UNICODE_PIECES.get(sym, sym)
            rendered = self._piece_font.render(char, True, (200, 190, 170))
            screen.blit(rendered, (x, y - 4))
            x += 20

        # Player's captures
        x = BOARD_OFFSET_X
        y += 28
        lbl2 = self._label_font.render("You captured:", True, TEXT_DIM)
        screen.blit(lbl2, (x, y - 2))
        x += lbl2.get_width() + 10
        for sym in black_captured:
            char = UNICODE_PIECES.get(sym.lower(), sym)
            rendered = self._piece_font.render(char, True, (80, 80, 90))
            screen.blit(rendered, (x, y - 4))
            x += 20

        # Eval display
        eval_x = RIGHT_PANEL_X + 20
        eval_text = f"{eval_score / 100:+.1f}" if abs(eval_score) < 10000 else ("White wins" if eval_score > 0 else "Black wins")
        eval_color = TEXT_GREEN if eval_score > 50 else TEXT_RED if eval_score < -50 else TEXT_COLOR
        ev = self._small_font.render(f"Eval: {eval_text}", True, eval_color)
        screen.blit(ev, (eval_x, BOTTOM_BAR_Y + 15))

        # Phase
        phase_text = game_phase.capitalize()
        phase = self._small_font.render(f"Phase: {phase_text}", True, TEXT_DIM)
        screen.blit(phase, (eval_x, BOTTOM_BAR_Y + 38))

    # ── Evaluation Bar ──────────────────────────────────────────

    def _draw_eval_bar(self, screen: pygame.Surface, eval_score: int) -> None:
        """Draw vertical eval bar on the left edge of the board."""
        bar_x = BOARD_OFFSET_X - 28
        bar_y = RIGHT_PANEL_Y
        bar_w = 16
        bar_h = BOARD_SIZE

        # Background (black side)
        pygame.draw.rect(screen, EVAL_BLACK, (bar_x, bar_y, bar_w, bar_h))

        # White portion (from bottom)
        # Map eval score to percentage (capped at ±500cp → 0-100%)
        capped = max(-500, min(500, eval_score))
        white_pct = 0.5 + (capped / 1000)
        white_h = int(bar_h * white_pct)
        white_y = bar_y + bar_h - white_h
        pygame.draw.rect(screen, EVAL_WHITE, (bar_x, white_y, bar_w, white_h))

        # Border
        pygame.draw.rect(screen, PANEL_BORDER, (bar_x, bar_y, bar_w, bar_h), 1)

        # Center line
        center_y = bar_y + bar_h // 2
        pygame.draw.line(screen, TEXT_DIM, (bar_x, center_y), (bar_x + bar_w, center_y))

    # ── Game Over Overlay ───────────────────────────────────────

    def _draw_game_over(self, screen: pygame.Surface, result: str, narrative: str) -> None:
        # Dim overlay
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Result box
        box_w, box_h = 500, 270
        box_x = (screen.get_width() - box_w) // 2
        box_y = (screen.get_height() - box_h) // 2
        pygame.draw.rect(screen, PANEL_BG, (box_x, box_y, box_w, box_h), border_radius=10)
        pygame.draw.rect(screen, TEXT_GOLD, (box_x, box_y, box_w, box_h), 2, border_radius=10)

        # Title
        title = self._title_font.render("⚔  BATTLE CONCLUDED  ⚔", True, TEXT_GOLD)
        screen.blit(title, (box_x + (box_w - title.get_width()) // 2, box_y + 20))

        # Result
        res = self._clock_font.render(result, True, TEXT_WHITE)
        screen.blit(res, (box_x + (box_w - res.get_width()) // 2, box_y + 60))

        # Narrative
        wrapped = self._wrap_text(narrative, self._narrative_font, box_w - 40)
        y = box_y + 110
        for line in wrapped[:4]:
            rendered = self._narrative_font.render(line, True, TEXT_COLOR)
            screen.blit(rendered, (box_x + 20, y))
            y += 22

        # Quote
        q = self._small_font.render(
            '"The board remembers what the mind forgets" — Perez',
            True, TEXT_GOLD,
        )
        screen.blit(q, (box_x + (box_w - q.get_width()) // 2, box_y + box_h - 55))

        # Restart hint
        hint = self._small_font.render("ENTER: New Battle  •  A: Analysis  •  L: Leaderboard  •  T: Trophies  •  S: Save  •  ESC: Menu", True, TEXT_DIM)
        screen.blit(hint, (box_x + (box_w - hint.get_width()) // 2, box_y + box_h - 35))

    # ── Utility ─────────────────────────────────────────────────

    @staticmethod
    def _wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        """Word-wrap text to fit within max_width pixels."""
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
