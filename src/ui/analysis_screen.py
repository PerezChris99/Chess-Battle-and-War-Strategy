"""
Post-game analysis screen — renders the battle report after a game.

Displays accuracy, move classifications, critical moments,
phase summary, and the full battle report narrative.
"""

from __future__ import annotations

import pygame
from typing import Optional

from src.game.post_game_analysis import GameAnalysis, MoveAssessment
from src.utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BG_COLOR, PANEL_BG, PANEL_BORDER,
    TEXT_COLOR, TEXT_DIM, TEXT_GOLD, TEXT_RED, TEXT_GREEN, TEXT_BLUE,
    TEXT_WHITE, BUTTON_BG, BUTTON_HOVER, BUTTON_TEXT,
)


class AnalysisScreen:
    """Renders the post-game analysis / battle report."""

    def __init__(self):
        self.analysis: Optional[GameAnalysis] = None
        self.scroll_y = 0
        self.max_scroll = 0

        # Fonts
        self.font_title = pygame.font.SysFont("Segoe UI", 28, bold=True)
        self.font_heading = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 16)
        self.font_small = pygame.font.SysFont("Segoe UI", 14)
        self.font_btn = pygame.font.SysFont("Segoe UI", 16, bold=True)

        # Buttons
        self.back_rect = pygame.Rect(WINDOW_WIDTH - 160, WINDOW_HEIGHT - 50, 140, 36)
        self.save_rect = pygame.Rect(WINDOW_WIDTH - 320, WINDOW_HEIGHT - 50, 140, 36)

    def set_analysis(self, analysis: GameAnalysis) -> None:
        """Load analysis data for display."""
        self.analysis = analysis
        self.scroll_y = 0

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle analysis screen events. Returns 'BACK' or 'SAVE' or None."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.back_rect.collidepoint(event.pos):
                    return "BACK"
                if self.save_rect.collidepoint(event.pos):
                    return "SAVE"
            # Scroll
            if event.button == 4:  # scroll up
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.button == 5:  # scroll down
                self.scroll_y = min(self.max_scroll, self.scroll_y + 30)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "BACK"
            elif event.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.key == pygame.K_DOWN:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 30)

        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Render the analysis screen."""
        screen.fill(BG_COLOR)

        if not self.analysis:
            txt = self.font_title.render("No analysis available", True, TEXT_DIM)
            screen.blit(txt, (WINDOW_WIDTH // 2 - txt.get_width() // 2, 100))
            return

        a = self.analysis
        y = 20 - self.scroll_y

        # Title
        y = self._draw_centered_text(screen, "BATTLE REPORT", self.font_title, TEXT_GOLD, y)
        y += 5
        y = self._draw_centered_text(screen, a.opening_name, self.font_body, TEXT_DIM, y)
        y += 20

        # Result
        result_color = TEXT_GREEN if "1-0" in a.game_result else TEXT_RED if "0-1" in a.game_result else TEXT_BLUE
        y = self._draw_centered_text(screen, a.game_result, self.font_heading, result_color, y)
        y += 25

        # Accuracy bars
        y = self._draw_accuracy_section(screen, a, y)
        y += 20

        # Error summary
        y = self._draw_section_header(screen, "Tactical Errors", y)
        y += 5
        y = self._draw_error_row(screen, "White", a.white_blunders, a.white_mistakes, a.white_inaccuracies, y)
        y = self._draw_error_row(screen, "Black", a.black_blunders, a.black_mistakes, a.black_inaccuracies, y)
        y += 15

        # Phase summary
        y = self._draw_section_header(screen, "Campaign Phases", y)
        y += 5
        for phase, desc in a.phase_summary.items():
            y = self._draw_text(screen, f"{phase}: ", self.font_body, TEXT_GOLD, 60, y)
            # Wrap description
            for line in self._wrap_text(desc, self.font_small, WINDOW_WIDTH - 140):
                y = self._draw_text(screen, line, self.font_small, TEXT_DIM, 80, y)
            y += 5
        y += 10

        # Critical moments
        if a.critical_moments:
            y = self._draw_section_header(screen, "Critical Moments", y)
            y += 5
            for cm in a.critical_moments[:8]:
                prefix = f"{cm.move_number}." if cm.is_white else f"{cm.move_number}..."
                cls_color = TEXT_RED if cm.classification == "blunder" else (255, 180, 60)
                label = f"  {prefix}{cm.san} ({cm.classification.upper()})"
                y = self._draw_text(screen, label, self.font_body, cls_color, 60, y)
                for line in self._wrap_text(cm.narrative, self.font_small, WINDOW_WIDTH - 160):
                    y = self._draw_text(screen, line, self.font_small, TEXT_DIM, 80, y)
                y += 3
            y += 10

        # Move list with classifications
        y = self._draw_section_header(screen, "Move-by-Move Assessment", y)
        y += 5
        for i, assess in enumerate(a.assessments):
            cls_colors = {
                "best": TEXT_GREEN, "excellent": (140, 210, 140),
                "good": TEXT_COLOR, "inaccuracy": (255, 210, 100),
                "mistake": (255, 170, 70), "blunder": TEXT_RED,
            }
            color = cls_colors.get(assess.classification, TEXT_COLOR)
            prefix = f"{assess.move_number}." if assess.is_white else f"{assess.move_number}..."
            symbols = {"best": "!!", "excellent": "!", "good": "", "inaccuracy": "?!", "mistake": "?", "blunder": "??"}
            sym = symbols.get(assess.classification, "")
            line = f"  {prefix}{assess.san}{sym}  [{assess.eval_after/100:+.1f}]"
            y = self._draw_text(screen, line, self.font_small, color, 60, y)

        y += 30
        self.max_scroll = max(0, y + self.scroll_y - WINDOW_HEIGHT + 80)

        # Fixed bottom bar with buttons
        bar = pygame.Rect(0, WINDOW_HEIGHT - 60, WINDOW_WIDTH, 60)
        pygame.draw.rect(screen, BG_COLOR, bar)
        pygame.draw.line(screen, PANEL_BORDER, (0, WINDOW_HEIGHT - 60), (WINDOW_WIDTH, WINDOW_HEIGHT - 60))

        self._draw_button(screen, self.back_rect, "Back to Menu")
        self._draw_button(screen, self.save_rect, "Save PGN")

    # ── Drawing Helpers ─────────────────────────────────────────

    def _draw_centered_text(self, screen, text, font, color, y):
        surf = font.render(text, True, color)
        screen.blit(surf, (WINDOW_WIDTH // 2 - surf.get_width() // 2, y))
        return y + surf.get_height() + 2

    def _draw_text(self, screen, text, font, color, x, y):
        surf = font.render(text, True, color)
        screen.blit(surf, (x, y))
        return y + surf.get_height() + 1

    def _draw_section_header(self, screen, text, y):
        surf = self.font_heading.render(f"— {text} —", True, TEXT_GOLD)
        screen.blit(surf, (WINDOW_WIDTH // 2 - surf.get_width() // 2, y))
        return y + surf.get_height() + 2

    def _draw_accuracy_section(self, screen, a: GameAnalysis, y: int) -> int:
        """Draw accuracy bars for both sides."""
        bar_width = 300
        bar_height = 22
        cx = WINDOW_WIDTH // 2

        # White accuracy
        label_w = self.font_body.render(f"White: {a.white_accuracy:.1f}%", True, TEXT_WHITE)
        screen.blit(label_w, (cx - bar_width // 2, y))
        y += 22
        bg_rect = pygame.Rect(cx - bar_width // 2, y, bar_width, bar_height)
        fill_w = int(bar_width * a.white_accuracy / 100)
        fill_rect = pygame.Rect(cx - bar_width // 2, y, fill_w, bar_height)
        pygame.draw.rect(screen, (50, 50, 60), bg_rect, border_radius=4)
        if fill_w > 0:
            color = self._accuracy_color(a.white_accuracy)
            pygame.draw.rect(screen, color, fill_rect, border_radius=4)
        pygame.draw.rect(screen, PANEL_BORDER, bg_rect, 1, border_radius=4)
        y += bar_height + 8

        # Black accuracy
        label_b = self.font_body.render(f"Black: {a.black_accuracy:.1f}%", True, TEXT_WHITE)
        screen.blit(label_b, (cx - bar_width // 2, y))
        y += 22
        bg_rect = pygame.Rect(cx - bar_width // 2, y, bar_width, bar_height)
        fill_b = int(bar_width * a.black_accuracy / 100)
        fill_rect = pygame.Rect(cx - bar_width // 2, y, fill_b, bar_height)
        pygame.draw.rect(screen, (50, 50, 60), bg_rect, border_radius=4)
        if fill_b > 0:
            color = self._accuracy_color(a.black_accuracy)
            pygame.draw.rect(screen, color, fill_rect, border_radius=4)
        pygame.draw.rect(screen, PANEL_BORDER, bg_rect, 1, border_radius=4)
        y += bar_height + 5

        return y

    def _accuracy_color(self, accuracy: float) -> tuple:
        if accuracy >= 90:
            return (80, 200, 120)
        elif accuracy >= 70:
            return (180, 200, 80)
        elif accuracy >= 50:
            return (220, 180, 60)
        else:
            return (220, 90, 70)

    def _draw_error_row(self, screen, side: str, blunders, mistakes, inaccuracies, y):
        text = f"  {side}: {blunders} blunder(s), {mistakes} mistake(s), {inaccuracies} inaccuracy(ies)"
        return self._draw_text(screen, text, self.font_body, TEXT_COLOR, 60, y)

    def _draw_button(self, screen, rect, text):
        mouse = pygame.mouse.get_pos()
        color = BUTTON_HOVER if rect.collidepoint(mouse) else BUTTON_BG
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, PANEL_BORDER, rect, 1, border_radius=6)
        surf = self.font_btn.render(text, True, BUTTON_TEXT)
        screen.blit(surf, (rect.centerx - surf.get_width() // 2, rect.centery - surf.get_height() // 2))

    def _wrap_text(self, text: str, font, max_width: int) -> list[str]:
        words = text.split()
        lines = []
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
        return lines or [""]
