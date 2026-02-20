"""
Menu system — main menu, new game setup, settings, and pause menu.

Full-screen menus with war-themed aesthetics.
"""

from __future__ import annotations

import pygame
from src.utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    BG_COLOR, PANEL_BG, PANEL_BORDER, HEADER_BG,
    TEXT_COLOR, TEXT_DIM, TEXT_GOLD, TEXT_WHITE, TEXT_GREEN, TEXT_RED, TEXT_BLUE,
    BUTTON_BG, BUTTON_HOVER, BUTTON_ACTIVE, BUTTON_TEXT, BUTTON_GOLD,
    BUTTON_GOLD_HOVER,
    DIFFICULTIES, DIFFICULTY_ORDER,
    TIME_CONTROLS, DEFAULT_TIME_CONTROL,
)


class Button:
    """Clickable UI button with hover effect."""

    def __init__(
        self, x: int, y: int, w: int, h: int,
        text: str, font: pygame.font.Font,
        color: tuple = BUTTON_BG,
        hover_color: tuple = BUTTON_HOVER,
        text_color: tuple = BUTTON_TEXT,
        border_color: tuple | None = None,
    ):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_color = border_color
        self.hovered = False
        self.selected = False

    def draw(self, screen: pygame.Surface) -> None:
        bg = self.hover_color if self.hovered else self.color
        if self.selected:
            bg = BUTTON_ACTIVE
        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        if self.border_color:
            pygame.draw.rect(screen, self.border_color, self.rect, 2, border_radius=6)
        elif self.selected:
            pygame.draw.rect(screen, TEXT_GOLD, self.rect, 2, border_radius=6)

        label = self.font.render(self.text, True, self.text_color)
        lx = self.rect.x + (self.rect.width - label.get_width()) // 2
        ly = self.rect.y + (self.rect.height - label.get_height()) // 2
        screen.blit(label, (lx, ly))

    def handle_motion(self, pos: tuple[int, int]) -> None:
        self.hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


class MainMenu:
    """Main menu screen."""

    def __init__(self):
        pygame.font.init()
        self._title_font = pygame.font.SysFont("Georgia", 52, bold=True)
        self._subtitle_font = pygame.font.SysFont("Georgia", 20, italic=True)
        self._button_font = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self._small_font = pygame.font.SysFont("Segoe UI", 14)
        self._desc_font = pygame.font.SysFont("Segoe UI", 15)

        # Buttons
        bw, bh = 280, 48
        cx = WINDOW_WIDTH // 2 - bw // 2
        by = 280

        self.btn_new_game = Button(cx, by, bw, bh, "⚔  NEW BATTLE", self._button_font,
                                   BUTTON_GOLD, BUTTON_GOLD_HOVER, (30, 30, 30))
        self.btn_tutorial = Button(cx, by + 60, bw, bh, "📖  WAR ACADEMY", self._button_font)
        self.btn_arena = Button(cx, by + 120, bw, bh, "🤖  AI ARENA", self._button_font,
                                (50, 60, 75), (70, 80, 100))
        self.btn_leaderboard = Button(cx, by + 180, bw, bh, "🏆  LEADERBOARD", self._button_font,
                                      (60, 70, 50), (80, 95, 65))
        self.btn_trophies = Button(cx, by + 240, bw, bh, "🎖  TROPHIES", self._button_font,
                                   (70, 55, 70), (95, 70, 95))
        self.btn_settings = Button(cx, by + 300, bw, bh, "⚙  SETTINGS", self._button_font)
        self.btn_quit     = Button(cx, by + 360, bw, bh, "🚪  RETREAT", self._button_font,
                                   (80, 40, 40), (110, 50, 50))

        self.buttons = [self.btn_new_game, self.btn_tutorial, self.btn_arena,
                        self.btn_leaderboard, self.btn_trophies, self.btn_settings, self.btn_quit]

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns action string or None."""
        if event.type == pygame.MOUSEMOTION:
            for btn in self.buttons:
                btn.handle_motion(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_new_game.is_clicked(event.pos):
                return "NEW_GAME_SETUP"
            if self.btn_tutorial.is_clicked(event.pos):
                return "TUTORIAL"
            if self.btn_leaderboard.is_clicked(event.pos):
                return "LEADERBOARD"
            if self.btn_arena.is_clicked(event.pos):
                return "ARENA"
            if self.btn_trophies.is_clicked(event.pos):
                return "TROPHIES"
            if self.btn_settings.is_clicked(event.pos):
                return "SETTINGS"
            if self.btn_quit.is_clicked(event.pos):
                return "QUIT"
        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BG_COLOR)

        # Title
        title = self._title_font.render("CHESS BATTLE", True, TEXT_GOLD)
        screen.blit(title, ((WINDOW_WIDTH - title.get_width()) // 2, 100))

        subtitle = self._subtitle_font.render("& WAR STRATEGY", True, TEXT_DIM)
        screen.blit(subtitle, ((WINDOW_WIDTH - subtitle.get_width()) // 2, 165))

        tagline = self._small_font.render(
            "Master the art of war through chess — inspired by Magnus Carlsen",
            True, TEXT_DIM,
        )
        screen.blit(tagline, ((WINDOW_WIDTH - tagline.get_width()) // 2, 200))

        # Decorative line
        line_y = 240
        pygame.draw.line(screen, PANEL_BORDER, (WINDOW_WIDTH // 2 - 200, line_y),
                         (WINDOW_WIDTH // 2 + 200, line_y))

        # Buttons
        for btn in self.buttons:
            btn.draw(screen)

        # Footer — quote, author & copyright
        quote = self._small_font.render(
            "\"Every square is a battlefield, every piece a soldier — think before you move.\"",
            True, TEXT_DIM,
        )
        screen.blit(quote, ((WINDOW_WIDTH - quote.get_width()) // 2, WINDOW_HEIGHT - 78))

        credit = self._small_font.render(
            "Created by Perez  ·  perezchris.netlify.app",
            True, TEXT_BLUE,
        )
        screen.blit(credit, ((WINDOW_WIDTH - credit.get_width()) // 2, WINDOW_HEIGHT - 55))

        copy_text = self._small_font.render(
            "© 2026 Perez. All rights reserved.",
            True, TEXT_DIM,
        )
        screen.blit(copy_text, ((WINDOW_WIDTH - copy_text.get_width()) // 2, WINDOW_HEIGHT - 35))


class NewGameSetup:
    """New game configuration screen — difficulty, color, time control."""

    def __init__(self):
        pygame.font.init()
        self._title_font  = pygame.font.SysFont("Georgia", 36, bold=True)
        self._label_font  = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self._desc_font   = pygame.font.SysFont("Segoe UI", 14)
        self._button_font = pygame.font.SysFont("Segoe UI", 17, bold=True)
        self._small_font  = pygame.font.SysFont("Segoe UI", 13)

        # State
        self.selected_difficulty = "SOLDIER"
        self.selected_color = "white"
        self.selected_time = "unlimited"

        # Build buttons
        self.difficulty_buttons: list[tuple[str, Button]] = []
        self.color_buttons: list[tuple[str, Button]] = []
        self.time_buttons: list[tuple[str, Button]] = []
        self.btn_start: Button | None = None
        self.btn_back: Button | None = None
        self._build_buttons()

    def _build_buttons(self) -> None:
        base_y = 120
        bw, bh = 200, 42

        # Difficulty selection
        dx = 80
        for i, key in enumerate(DIFFICULTY_ORDER):
            info = DIFFICULTIES[key]
            btn = Button(dx, base_y + 40 + i * 52, bw, bh, info["name"], self._button_font)
            if key == self.selected_difficulty:
                btn.selected = True
            self.difficulty_buttons.append((key, btn))

        # Color selection
        cx = 350
        for i, (key, label) in enumerate([("white", "⬜ White (First)"), ("black", "⬛ Black (Second)")]):
            btn = Button(cx, base_y + 40 + i * 52, bw + 40, bh, label, self._button_font)
            if key == self.selected_color:
                btn.selected = True
            self.color_buttons.append((key, btn))

        # Time control
        tx = 650
        time_labels = [
            ("bullet_2", "Bullet 2+1"),
            ("blitz_5", "Blitz 5min"),
            ("rapid_10", "Rapid 10min"),
            ("rapid_15", "Rapid 15+10"),
            ("classical", "Classical 30min"),
            ("unlimited", "♾  Unlimited"),
        ]
        for i, (key, label) in enumerate(time_labels):
            btn = Button(tx, base_y + 40 + i * 52, bw + 20, bh, label, self._button_font)
            if key == self.selected_time:
                btn.selected = True
            self.time_buttons.append((key, btn))

        # Start / Back
        self.btn_start = Button(
            WINDOW_WIDTH // 2 - 140, WINDOW_HEIGHT - 100, 280, 55,
            "⚔  BEGIN BATTLE", self._button_font,
            BUTTON_GOLD, BUTTON_GOLD_HOVER, (30, 30, 30),
        )
        self.btn_back = Button(
            20, WINDOW_HEIGHT - 60, 100, 35,
            "← Back", self._small_font,
        )

    def handle_event(self, event: pygame.event.Event) -> str | dict | None:
        if event.type == pygame.MOUSEMOTION:
            for _, btn in self.difficulty_buttons + self.color_buttons + self.time_buttons:
                btn.handle_motion(event.pos)
            self.btn_start.handle_motion(event.pos)
            self.btn_back.handle_motion(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Difficulty
            for key, btn in self.difficulty_buttons:
                if btn.is_clicked(event.pos):
                    self.selected_difficulty = key
                    for k2, b2 in self.difficulty_buttons:
                        b2.selected = (k2 == key)

            # Color
            for key, btn in self.color_buttons:
                if btn.is_clicked(event.pos):
                    self.selected_color = key
                    for k2, b2 in self.color_buttons:
                        b2.selected = (k2 == key)

            # Time
            for key, btn in self.time_buttons:
                if btn.is_clicked(event.pos):
                    self.selected_time = key
                    for k2, b2 in self.time_buttons:
                        b2.selected = (k2 == key)

            # Start
            if self.btn_start.is_clicked(event.pos):
                return {
                    "action": "START_GAME",
                    "difficulty": self.selected_difficulty,
                    "color": self.selected_color,
                    "time_control": self.selected_time,
                }

            # Back
            if self.btn_back.is_clicked(event.pos):
                return "BACK"

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "BACK"

        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BG_COLOR)

        # Title
        title = self._title_font.render("⚔  Prepare for Battle", True, TEXT_GOLD)
        screen.blit(title, ((WINDOW_WIDTH - title.get_width()) // 2, 30))

        # Section labels
        sections = [
            (80,  "DIFFICULTY"),
            (350, "PLAY AS"),
            (650, "TIME CONTROL"),
        ]
        for sx, label in sections:
            lbl = self._label_font.render(label, True, TEXT_COLOR)
            screen.blit(lbl, (sx, 120))

        # Draw buttons
        for _, btn in self.difficulty_buttons:
            btn.draw(screen)
        for _, btn in self.color_buttons:
            btn.draw(screen)
        for _, btn in self.time_buttons:
            btn.draw(screen)

        # Difficulty description
        info = DIFFICULTIES.get(self.selected_difficulty)
        if info:
            desc = self._desc_font.render(info["desc"], True, TEXT_DIM)
            elo = self._small_font.render(f"~{info['elo']} ELO", True, TEXT_BLUE)
            screen.blit(desc, (80, 390))
            screen.blit(elo, (80, 410))

        self.btn_start.draw(screen)
        self.btn_back.draw(screen)


class SettingsMenu:
    """Settings / Options screen."""

    def __init__(self, config):
        pygame.font.init()
        self.config = config
        self._title_font  = pygame.font.SysFont("Georgia", 36, bold=True)
        self._label_font  = pygame.font.SysFont("Segoe UI", 17)
        self._button_font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self._small_font  = pygame.font.SysFont("Segoe UI", 13)

        self.btn_back = Button(20, WINDOW_HEIGHT - 60, 100, 35, "← Back", self._small_font)

        # Toggle buttons for settings
        self.toggles: list[tuple[str, str, Button]] = []
        self._build_toggles()

    def _build_toggles(self) -> None:
        self.toggles.clear()
        settings = [
            ("show_valid_moves", "Show Valid Moves"),
            ("show_coordinates", "Show Coordinates"),
            ("show_last_move",   "Highlight Last Move"),
            ("show_evaluation",  "Show Evaluation"),
            ("narrative_enabled","Battle Narrative"),
            ("animation_enabled","Move Animations"),
            ("sound_enabled",    "Sound Effects"),
            ("auto_queen_promote", "Auto Queen Promote"),
        ]
        sx, sy = 100, 120
        for i, (key, label) in enumerate(settings):
            val = self.config.get(key, True)
            btn_text = f"{'ON' if val else 'OFF'}"
            btn = Button(sx + 300, sy + i * 50, 80, 35, btn_text, self._button_font,
                         (60, 120, 60) if val else (120, 60, 60),
                         (80, 150, 80) if val else (150, 80, 80))
            self.toggles.append((key, label, btn))

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.MOUSEMOTION:
            self.btn_back.handle_motion(event.pos)
            for _, _, btn in self.toggles:
                btn.handle_motion(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.is_clicked(event.pos):
                return "BACK"
            for key, label, btn in self.toggles:
                if btn.is_clicked(event.pos):
                    new_val = not self.config.get(key, True)
                    self.config.set(key, new_val)
                    self._build_toggles()
                    return None

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "BACK"

        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BG_COLOR)
        title = self._title_font.render("⚙  Settings", True, TEXT_GOLD)
        screen.blit(title, ((WINDOW_WIDTH - title.get_width()) // 2, 30))

        sx, sy = 100, 120
        for i, (key, label, btn) in enumerate(self.toggles):
            lbl = self._label_font.render(label, True, TEXT_COLOR)
            screen.blit(lbl, (sx, sy + i * 50 + 6))
            btn.draw(screen)

        self.btn_back.draw(screen)
