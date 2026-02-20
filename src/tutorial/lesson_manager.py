"""
Tutorial / lesson manager — controls the learning flow.

Renders lesson content on screen and tracks progress.
"""

from __future__ import annotations

import pygame
import chess

from src.tutorial.lessons import (
    Lesson, get_all_lessons, get_lesson_by_id,
    get_lessons_by_category, get_categories,
)
from src.utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    BG_COLOR, PANEL_BG, PANEL_BORDER, HEADER_BG,
    TEXT_COLOR, TEXT_DIM, TEXT_GOLD, TEXT_WHITE, TEXT_GREEN, TEXT_BLUE,
    BUTTON_BG, BUTTON_HOVER, BUTTON_TEXT,
    BOARD_SIZE, SQUARE_SIZE,
)
from src.ui.board_renderer import BoardRenderer
from src.ui.menu import Button


class LessonManager:
    """Manages the tutorial / lesson UI and flow."""

    def __init__(self, config):
        pygame.font.init()
        self.config = config
        self._title_font     = pygame.font.SysFont("Georgia", 32, bold=True)
        self._cat_font       = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self._lesson_font    = pygame.font.SysFont("Segoe UI", 16)
        self._body_font      = pygame.font.SysFont("Segoe UI", 15)
        self._italic_font    = pygame.font.SysFont("Georgia", 14, italic=True)
        self._small_font     = pygame.font.SysFont("Segoe UI", 13)
        self._header_font    = pygame.font.SysFont("Segoe UI", 15, bold=True)

        self.board_renderer = BoardRenderer()
        self.categories = get_categories()
        self.all_lessons = get_all_lessons()

        # State
        self.mode = "LIST"  # "LIST" or "DETAIL"
        self.current_lesson: Lesson | None = None
        self.scroll_offset = 0

        # Buttons
        self.btn_back = Button(20, WINDOW_HEIGHT - 60, 100, 35, "← Back", self._small_font)
        self.lesson_buttons: list[tuple[Lesson, Button]] = []
        self._build_lesson_buttons()

    def _build_lesson_buttons(self) -> None:
        self.lesson_buttons.clear()
        y = 100
        for cat in self.categories:
            y += 35
            lessons = get_lessons_by_category(cat)
            for lesson in lessons:
                completed = lesson.id in self.config.get("completed_lessons", [])
                prefix = "✅ " if completed else "⬜ "
                btn = Button(
                    40, y, WINDOW_WIDTH - 80, 32,
                    f"{prefix}{lesson.title}", self._lesson_font,
                    PANEL_BG, BUTTON_HOVER,
                )
                self.lesson_buttons.append((lesson, btn))
                y += 38

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns 'BACK' to return to main menu, or None."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.mode == "DETAIL":
                self.mode = "LIST"
                return None
            return "BACK"

        if event.type == pygame.MOUSEMOTION:
            self.btn_back.handle_motion(event.pos)
            if self.mode == "LIST":
                for _, btn in self.lesson_buttons:
                    btn.handle_motion(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.is_clicked(event.pos):
                if self.mode == "DETAIL":
                    self.mode = "LIST"
                    return None
                return "BACK"

            if self.mode == "LIST":
                for lesson, btn in self.lesson_buttons:
                    if btn.is_clicked(event.pos):
                        self.current_lesson = lesson
                        self.mode = "DETAIL"
                        return None

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_offset += event.y * 30

        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BG_COLOR)

        if self.mode == "LIST":
            self._draw_lesson_list(screen)
        elif self.mode == "DETAIL" and self.current_lesson:
            self._draw_lesson_detail(screen, self.current_lesson)

        self.btn_back.draw(screen)

    def _draw_lesson_list(self, screen: pygame.Surface) -> None:
        title = self._title_font.render("📖  War Academy", True, TEXT_GOLD)
        screen.blit(title, ((WINDOW_WIDTH - title.get_width()) // 2, 20))

        subtitle = self._small_font.render(
            "Learn chess through the art of war — Magnus Carlsen's approach",
            True, TEXT_DIM,
        )
        screen.blit(subtitle, ((WINDOW_WIDTH - subtitle.get_width()) // 2, 60))

        # Category headers and lesson buttons
        y = 100 + self.scroll_offset
        for cat in self.categories:
            cat_label = self._cat_font.render(f"▸ {cat}", True, TEXT_GOLD)
            screen.blit(cat_label, (40, y))
            y += 35

            lessons = get_lessons_by_category(cat)
            for lesson in lessons:
                for les, btn in self.lesson_buttons:
                    if les.id == lesson.id:
                        btn.rect.y = y
                        btn.draw(screen)
                y += 38

    def _draw_lesson_detail(self, screen: pygame.Surface, lesson: Lesson) -> None:
        # Title
        title = self._title_font.render(lesson.title, True, TEXT_GOLD)
        screen.blit(title, (40, 20))

        cat = self._small_font.render(lesson.category, True, TEXT_BLUE)
        screen.blit(cat, (40, 60))

        # Military context (italic)
        y = 90
        wrapped = self._wrap_text(lesson.military_context, self._italic_font, WINDOW_WIDTH - 80)
        for line in wrapped:
            rendered = self._italic_font.render(line, True, TEXT_DIM)
            screen.blit(rendered, (40, y))
            y += 20
        y += 10

        # Key points
        header = self._header_font.render("Key Points:", True, TEXT_GREEN)
        screen.blit(header, (40, y))
        y += 25

        for point in lesson.key_points:
            # Magnus tips in gold
            color = TEXT_GOLD if point.startswith("Magnus tip") else TEXT_COLOR
            wrapped = self._wrap_text(f"• {point}", self._body_font, WINDOW_WIDTH - 100)
            for line in wrapped:
                rendered = self._body_font.render(line, True, color)
                screen.blit(rendered, (50, y))
                y += 20
            y += 5

        # Example board (if FEN provided)
        if lesson.example_fen:
            board = chess.Board(lesson.example_fen)
            board_size = 320
            scale = board_size / BOARD_SIZE
            # Draw a mini board on the right
            bx = WINDOW_WIDTH - board_size - 40
            by = 90

            # Simple mini-board rendering
            sq_size = board_size // 8
            for row in range(8):
                for col in range(8):
                    is_light = (col + row) % 2 == 0
                    color = (232, 220, 202) if is_light else (166, 126, 90)
                    pygame.draw.rect(screen, color, (bx + col * sq_size, by + row * sq_size, sq_size, sq_size))

            # Pieces
            piece_font = pygame.font.SysFont("Segoe UI Symbol", sq_size - 8)
            from src.utils.constants import UNICODE_PIECES
            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if piece:
                    col = chess.square_file(sq)
                    row = 7 - chess.square_rank(sq)
                    char = UNICODE_PIECES.get(piece.symbol(), piece.symbol())
                    pc = (245, 235, 220) if piece.color == chess.WHITE else (50, 50, 62)
                    rendered = piece_font.render(char, True, pc)
                    px = bx + col * sq_size + (sq_size - rendered.get_width()) // 2
                    py = by + row * sq_size + (sq_size - rendered.get_height()) // 2
                    screen.blit(rendered, (px, py))

            pygame.draw.rect(screen, PANEL_BORDER, (bx - 1, by - 1, board_size + 2, board_size + 2), 1)

        # Mark as completed hint
        hint = self._small_font.render("Press ESC to return to lessons", True, TEXT_DIM)
        screen.blit(hint, (40, WINDOW_HEIGHT - 40))

    @staticmethod
    def _wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
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
        return lines
