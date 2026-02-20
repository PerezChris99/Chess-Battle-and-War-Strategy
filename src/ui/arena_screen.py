"""
AI Arena Screen — model selection, API key configuration, match setup.

Provides the full UI for:
  • Selecting an external AI model to play against
  • Entering / managing API keys
  • Choosing match settings (player color, spectator mode)
  • Viewing external model profiles and stats
"""

from __future__ import annotations

import pygame
from typing import Any

from src.utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    BG_COLOR, PANEL_BG, PANEL_BORDER, HEADER_BG,
    TEXT_COLOR, TEXT_DIM, TEXT_GOLD, TEXT_GREEN, TEXT_RED, TEXT_BLUE, TEXT_WHITE,
    BUTTON_BG, BUTTON_HOVER, BUTTON_ACTIVE, BUTTON_TEXT,
    BUTTON_GOLD, BUTTON_GOLD_HOVER,
)
from src.engine.arena_adapter import (
    ArenaModelInfo, get_available_adapters, create_adapter,
)
from src.engine.gemini_adapter import get_gemini_models


class ArenaScreen:
    """AI Arena — model selection and match setup UI."""

    def __init__(self):
        pygame.font.init()
        self._title_font = pygame.font.SysFont("Georgia", 36, bold=True)
        self._header_font = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self._body_font = pygame.font.SysFont("Segoe UI", 16)
        self._small_font = pygame.font.SysFont("Segoe UI", 13)
        self._input_font = pygame.font.SysFont("Consolas", 16)
        self._button_font = pygame.font.SysFont("Segoe UI", 17, bold=True)
        self._icon_font = pygame.font.SysFont("Segoe UI Symbol", 28)

        # State
        self._view = "MODEL_SELECT"  # MODEL_SELECT, API_KEY, MATCH_SETUP, MODEL_STATS
        self._selected_model: str | None = None
        self._api_key_input: str = ""
        self._api_key_cursor_visible = True
        self._api_key_cursor_timer = 0
        self._api_key_saved: dict[str, str] = {}  # model_id -> api_key
        self._selected_color = "white"
        self._selected_mode = "player_vs_ai"  # player_vs_ai, ai_vs_ai
        self._selected_gemini_model = "gemini-2.0-flash"
        self._error_message = ""
        self._success_message = ""
        self._model_profiles: list[dict[str, Any]] = []  # from arena_manager
        self._scroll_offset = 0

        # Available models from adapters
        self._available_models: list[dict[str, Any]] = []
        self._refresh_models()

    def _refresh_models(self) -> None:
        """Refresh the list of available AI models."""
        self._available_models = []
        adapters = get_available_adapters()
        for model_id, adapter_cls in adapters.items():
            adapter = adapter_cls()
            info = adapter.get_info()
            self._available_models.append({
                "model_id": model_id,
                "info": info,
                "configured": model_id in self._api_key_saved,
            })

    def set_model_profiles(self, profiles: list[dict[str, Any]]) -> None:
        """Set model profiles from the arena manager for stats display."""
        self._model_profiles = profiles

    def handle_event(self, event: pygame.event.Event) -> str | dict | None:
        """
        Handle input events.
        Returns:
          "BACK" — return to menu
          {"action": "START_ARENA", ...} — start an arena match
          None — no action
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self._view != "MODEL_SELECT":
                    self._view = "MODEL_SELECT"
                    self._error_message = ""
                    self._success_message = ""
                    return None
                return "BACK"

            # API key input
            if self._view == "API_KEY":
                return self._handle_api_key_input(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)

        if event.type == pygame.MOUSEMOTION:
            pass  # hover effects could be added here

        return None

    def _handle_api_key_input(self, event: pygame.event.Event) -> str | None:
        """Handle keyboard input for the API key entry field."""
        if event.key == pygame.K_RETURN:
            return self._save_api_key()
        elif event.key == pygame.K_BACKSPACE:
            self._api_key_input = self._api_key_input[:-1]
        elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
            # Paste from clipboard
            try:
                text = pygame.scrap.get(pygame.SCRAP_TEXT)
                if text:
                    self._api_key_input += text.decode("utf-8", errors="ignore").strip("\x00")
            except Exception:
                pass
        elif event.unicode and event.unicode.isprintable():
            self._api_key_input += event.unicode
        return None

    def _save_api_key(self) -> str | None:
        """Validate and save the API key."""
        if not self._api_key_input.strip():
            self._error_message = "Please enter an API key"
            return None

        if not self._selected_model:
            self._error_message = "No model selected"
            return None

        self._api_key_saved[self._selected_model] = self._api_key_input.strip()
        self._success_message = "API key saved! Ready to battle."
        self._error_message = ""
        self._refresh_models()
        self._view = "MATCH_SETUP"
        return None

    def _handle_click(self, pos: tuple[int, int]) -> str | dict | None:
        """Handle mouse click based on current view."""
        if self._view == "MODEL_SELECT":
            return self._handle_model_select_click(pos)
        elif self._view == "API_KEY":
            return self._handle_api_key_click(pos)
        elif self._view == "MATCH_SETUP":
            return self._handle_match_setup_click(pos)
        return None

    def _handle_model_select_click(self, pos: tuple[int, int]) -> str | dict | None:
        """Handle clicks on the model selection screen."""
        x, y = pos

        # Back button
        if self._back_btn_rect and self._back_btn_rect.collidepoint(pos):
            return "BACK"

        # Model cards
        for i, model in enumerate(self._available_models):
            card_y = 180 + i * 110
            card_rect = pygame.Rect(100, card_y, WINDOW_WIDTH - 200, 95)
            if card_rect.collidepoint(pos):
                self._selected_model = model["model_id"]
                # Check if key already saved
                if model["model_id"] in self._api_key_saved:
                    self._view = "MATCH_SETUP"
                else:
                    self._api_key_input = ""
                    self._error_message = ""
                    self._success_message = ""
                    self._view = "API_KEY"
                return None

        return None

    def _handle_api_key_click(self, pos: tuple[int, int]) -> str | None:
        """Handle clicks on the API key screen."""
        # Save button
        if self._save_btn_rect and self._save_btn_rect.collidepoint(pos):
            return self._save_api_key()
        # Back button
        if self._back_btn_rect and self._back_btn_rect.collidepoint(pos):
            self._view = "MODEL_SELECT"
            self._error_message = ""
        return None

    def _handle_match_setup_click(self, pos: tuple[int, int]) -> str | dict | None:
        """Handle clicks on the match setup screen."""
        x, y = pos

        # Color buttons
        for i, (key, label) in enumerate([("white", "⬜ Play as White"), ("black", "⬛ Play as Black")]):
            btn_rect = pygame.Rect(100, 300 + i * 55, 280, 45)
            if btn_rect.collidepoint(pos):
                self._selected_color = key
                self._selected_mode = "player_vs_ai"
                return None

        # Spectator mode button
        spectator_rect = pygame.Rect(100, 300 + 2 * 55, 280, 45)
        if spectator_rect.collidepoint(pos):
            self._selected_mode = "ai_vs_ai"
            return None

        # Gemini model variant buttons
        gemini_models = get_gemini_models()
        for i, gm in enumerate(gemini_models):
            btn_rect = pygame.Rect(500, 300 + i * 55, 350, 45)
            if btn_rect.collidepoint(pos):
                self._selected_gemini_model = gm["id"]
                return None

        # Start button
        if self._start_btn_rect and self._start_btn_rect.collidepoint(pos):
            return self._start_match()

        # Back button
        if self._back_btn_rect and self._back_btn_rect.collidepoint(pos):
            self._view = "MODEL_SELECT"
        return None

    def _start_match(self) -> dict[str, Any] | None:
        """Gather settings and return the start action."""
        if not self._selected_model:
            self._error_message = "No model selected"
            return None
        if self._selected_model not in self._api_key_saved:
            self._error_message = "API key not configured"
            return None

        return {
            "action": "START_ARENA",
            "model_id": self._selected_model,
            "api_key": self._api_key_saved[self._selected_model],
            "player_color": self._selected_color,
            "mode": self._selected_mode,
            "gemini_model": self._selected_gemini_model,
        }

    # ── Drawing ─────────────────────────────────────────────────

    # Rects stored during draw for click handling
    _back_btn_rect: pygame.Rect | None = None
    _save_btn_rect: pygame.Rect | None = None
    _start_btn_rect: pygame.Rect | None = None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BG_COLOR)

        if self._view == "MODEL_SELECT":
            self._draw_model_select(screen)
        elif self._view == "API_KEY":
            self._draw_api_key(screen)
        elif self._view == "MATCH_SETUP":
            self._draw_match_setup(screen)

    def _draw_model_select(self, screen: pygame.Surface) -> None:
        """Draw the model selection screen."""
        # Title
        title = self._title_font.render("🤖  AI ARENA", True, TEXT_GOLD)
        screen.blit(title, ((WINDOW_WIDTH - title.get_width()) // 2, 40))

        subtitle = self._small_font.render(
            "Challenge external AI models — compete for leaderboard dominance",
            True, TEXT_DIM,
        )
        screen.blit(subtitle, ((WINDOW_WIDTH - subtitle.get_width()) // 2, 90))

        # Decorative line
        pygame.draw.line(screen, PANEL_BORDER,
                         (WINDOW_WIDTH // 2 - 250, 120),
                         (WINDOW_WIDTH // 2 + 250, 120))

        label = self._header_font.render("Select an AI Model", True, TEXT_COLOR)
        screen.blit(label, (100, 145))

        # Model cards
        for i, model in enumerate(self._available_models):
            info: ArenaModelInfo = model["info"]
            card_y = 180 + i * 110
            card_rect = pygame.Rect(100, card_y, WINDOW_WIDTH - 200, 95)
            configured = model["configured"]

            # Card background
            bg = (50, 55, 65) if not configured else (45, 60, 50)
            pygame.draw.rect(screen, bg, card_rect, border_radius=8)
            pygame.draw.rect(screen, PANEL_BORDER, card_rect, 1, border_radius=8)

            # Icon
            icon = self._icon_font.render(info.icon, True, TEXT_GOLD)
            screen.blit(icon, (card_rect.x + 15, card_rect.y + 20))

            # Name + provider
            name = self._header_font.render(info.display_name, True, TEXT_WHITE)
            screen.blit(name, (card_rect.x + 60, card_rect.y + 12))

            provider = self._small_font.render(f"by {info.provider}", True, TEXT_DIM)
            screen.blit(provider, (card_rect.x + 60 + name.get_width() + 10, card_rect.y + 16))

            # Description
            desc = self._body_font.render(info.description, True, TEXT_DIM)
            screen.blit(desc, (card_rect.x + 60, card_rect.y + 40))

            # Status badge
            if configured:
                status = self._small_font.render("✅ Configured", True, TEXT_GREEN)
            else:
                status = self._small_font.render("🔑 API Key Required", True, TEXT_GOLD)
            screen.blit(status, (card_rect.x + 60, card_rect.y + 65))

            # Profile stats if available
            profile = next(
                (p for p in self._model_profiles if p.get("model_id") == model["model_id"]),
                None,
            )
            if profile:
                elo_text = self._body_font.render(f"ELO: {profile['elo']}", True, TEXT_GOLD)
                screen.blit(elo_text, (card_rect.right - 200, card_rect.y + 15))
                games = self._small_font.render(
                    f"W:{profile['wins']} L:{profile['losses']} D:{profile['draws']}",
                    True, TEXT_DIM,
                )
                screen.blit(games, (card_rect.right - 200, card_rect.y + 42))

        # Back button
        self._back_btn_rect = pygame.Rect(100, WINDOW_HEIGHT - 70, 150, 40)
        pygame.draw.rect(screen, BUTTON_BG, self._back_btn_rect, border_radius=6)
        back_lbl = self._button_font.render("← Back", True, BUTTON_TEXT)
        screen.blit(back_lbl, (self._back_btn_rect.x + 35, self._back_btn_rect.y + 8))

        # Footer
        footer = self._small_font.render(
            "\"The arena tests all warriors equally.\"", True, TEXT_DIM,
        )
        screen.blit(footer, ((WINDOW_WIDTH - footer.get_width()) // 2, WINDOW_HEIGHT - 30))

    def _draw_api_key(self, screen: pygame.Surface) -> None:
        """Draw the API key configuration screen."""
        title = self._title_font.render("🔑  API Key Setup", True, TEXT_GOLD)
        screen.blit(title, ((WINDOW_WIDTH - title.get_width()) // 2, 60))

        if self._selected_model:
            model_name = self._selected_model.replace("_", " ").title()
            inst = self._body_font.render(
                f"Enter your Google AI API key to connect {model_name}:",
                True, TEXT_COLOR,
            )
            screen.blit(inst, (100, 140))

        # Instructions
        steps = [
            "1. Visit https://aistudio.google.com/apikey",
            "2. Create a new API key (free tier available)",
            "3. Paste the key below",
        ]
        for i, step in enumerate(steps):
            txt = self._small_font.render(step, True, TEXT_DIM)
            screen.blit(txt, (120, 180 + i * 25))

        # Input field
        input_rect = pygame.Rect(100, 280, WINDOW_WIDTH - 200, 45)
        pygame.draw.rect(screen, (45, 45, 58), input_rect, border_radius=6)
        pygame.draw.rect(screen, TEXT_GOLD if self._api_key_input else PANEL_BORDER,
                         input_rect, 2, border_radius=6)

        # Masked display (show last 4 chars)
        if self._api_key_input:
            masked = "•" * max(0, len(self._api_key_input) - 4) + self._api_key_input[-4:]
            display = masked[-50:]  # limit visible chars
        else:
            display = "Paste your API key here..."

        color = TEXT_COLOR if self._api_key_input else TEXT_DIM
        txt = self._input_font.render(display, True, color)
        screen.blit(txt, (input_rect.x + 12, input_rect.y + 12))

        # Cursor blink
        self._api_key_cursor_timer = (self._api_key_cursor_timer + 1) % 60
        if self._api_key_cursor_timer < 30 and self._api_key_input:
            cursor_x = input_rect.x + 12 + txt.get_width() + 2
            pygame.draw.line(screen, TEXT_GOLD,
                             (cursor_x, input_rect.y + 10),
                             (cursor_x, input_rect.y + 35))

        # Error / success
        if self._error_message:
            err = self._body_font.render(self._error_message, True, TEXT_RED)
            screen.blit(err, (100, 340))
        if self._success_message:
            suc = self._body_font.render(self._success_message, True, TEXT_GREEN)
            screen.blit(suc, (100, 340))

        # Save button
        self._save_btn_rect = pygame.Rect(
            (WINDOW_WIDTH - 200) // 2, 380, 200, 45,
        )
        pygame.draw.rect(screen, BUTTON_GOLD, self._save_btn_rect, border_radius=6)
        save_lbl = self._button_font.render("Save & Continue", True, (30, 30, 30))
        screen.blit(save_lbl, (
            self._save_btn_rect.x + (self._save_btn_rect.width - save_lbl.get_width()) // 2,
            self._save_btn_rect.y + 10,
        ))

        # Back button
        self._back_btn_rect = pygame.Rect(100, WINDOW_HEIGHT - 70, 150, 40)
        pygame.draw.rect(screen, BUTTON_BG, self._back_btn_rect, border_radius=6)
        back_lbl = self._button_font.render("← Back", True, BUTTON_TEXT)
        screen.blit(back_lbl, (self._back_btn_rect.x + 35, self._back_btn_rect.y + 8))

        # Security note
        note = self._small_font.render(
            "🔒 Your API key is stored locally and never sent to any server except Google AI.",
            True, TEXT_DIM,
        )
        screen.blit(note, ((WINDOW_WIDTH - note.get_width()) // 2, WINDOW_HEIGHT - 30))

    def _draw_match_setup(self, screen: pygame.Surface) -> None:
        """Draw the match setup screen."""
        title = self._title_font.render("⚔  Arena Match Setup", True, TEXT_GOLD)
        screen.blit(title, ((WINDOW_WIDTH - title.get_width()) // 2, 40))

        # Model info
        if self._selected_model:
            adapters = get_available_adapters()
            cls = adapters.get(self._selected_model)
            if cls:
                info = cls().get_info()
                model_label = self._header_font.render(
                    f"{info.icon}  {info.display_name}  ({info.provider})",
                    True, TEXT_GOLD,
                )
                screen.blit(model_label, (100, 110))

        # Decorative line
        pygame.draw.line(screen, PANEL_BORDER, (100, 150), (WINDOW_WIDTH - 100, 150))

        # ── Left column: Play mode ──
        mode_label = self._header_font.render("Battle Mode", True, TEXT_COLOR)
        screen.blit(mode_label, (100, 170))

        color_options = [
            ("white", "⬜ Play as White"),
            ("black", "⬛ Play as Black"),
        ]
        for i, (key, label) in enumerate(color_options):
            btn_rect = pygame.Rect(100, 300 + i * 55, 280, 45)
            is_selected = self._selected_color == key and self._selected_mode == "player_vs_ai"
            bg = BUTTON_ACTIVE if is_selected else BUTTON_BG
            pygame.draw.rect(screen, bg, btn_rect, border_radius=6)
            if is_selected:
                pygame.draw.rect(screen, TEXT_GOLD, btn_rect, 2, border_radius=6)
            lbl = self._button_font.render(label, True, TEXT_WHITE if is_selected else BUTTON_TEXT)
            screen.blit(lbl, (btn_rect.x + 20, btn_rect.y + 10))

        # Spectator mode
        spectator_rect = pygame.Rect(100, 300 + 2 * 55, 280, 45)
        is_spectator = self._selected_mode == "ai_vs_ai"
        bg = BUTTON_ACTIVE if is_spectator else BUTTON_BG
        pygame.draw.rect(screen, bg, spectator_rect, border_radius=6)
        if is_spectator:
            pygame.draw.rect(screen, TEXT_GOLD, spectator_rect, 2, border_radius=6)
        spec_lbl = self._button_font.render("👁  Spectator (AI vs AI)", True,
                                            TEXT_WHITE if is_spectator else BUTTON_TEXT)
        screen.blit(spec_lbl, (spectator_rect.x + 20, spectator_rect.y + 10))

        # Mode descriptions
        if self._selected_mode == "player_vs_ai":
            desc = self._small_font.render(
                f"You play as {self._selected_color} against the AI model", True, TEXT_DIM,
            )
        else:
            desc = self._small_font.render(
                "Watch the external AI vs built-in Magnus AI", True, TEXT_DIM,
            )
        screen.blit(desc, (100, 470 + 15))

        # ── Right column: Gemini model variant ──
        variant_label = self._header_font.render("Model Variant", True, TEXT_COLOR)
        screen.blit(variant_label, (500, 170))

        gemini_models = get_gemini_models()
        for i, gm in enumerate(gemini_models):
            btn_rect = pygame.Rect(500, 300 + i * 55, 350, 45)
            is_selected = self._selected_gemini_model == gm["id"]
            bg = BUTTON_ACTIVE if is_selected else BUTTON_BG
            pygame.draw.rect(screen, bg, btn_rect, border_radius=6)
            if is_selected:
                pygame.draw.rect(screen, TEXT_GOLD, btn_rect, 2, border_radius=6)
            lbl = self._button_font.render(gm["name"], True,
                                           TEXT_WHITE if is_selected else BUTTON_TEXT)
            screen.blit(lbl, (btn_rect.x + 15, btn_rect.y + 10))

        # Model descriptions
        selected_gm = next((g for g in gemini_models if g["id"] == self._selected_gemini_model), None)
        if selected_gm:
            gm_desc = self._small_font.render(selected_gm["description"], True, TEXT_DIM)
            screen.blit(gm_desc, (500, 470 + 15))

        # ── Start button ──
        self._start_btn_rect = pygame.Rect(
            (WINDOW_WIDTH - 300) // 2, WINDOW_HEIGHT - 130, 300, 50,
        )
        pygame.draw.rect(screen, BUTTON_GOLD, self._start_btn_rect, border_radius=8)
        start_lbl = self._title_font.render("⚔  ENTER ARENA", True, (30, 30, 30))
        # Scale down if too wide
        start_lbl_small = self._button_font.render("⚔  ENTER ARENA", True, (30, 30, 30))
        screen.blit(start_lbl_small, (
            self._start_btn_rect.x + (self._start_btn_rect.width - start_lbl_small.get_width()) // 2,
            self._start_btn_rect.y + 12,
        ))

        # Error
        if self._error_message:
            err = self._body_font.render(self._error_message, True, TEXT_RED)
            screen.blit(err, ((WINDOW_WIDTH - err.get_width()) // 2, WINDOW_HEIGHT - 165))

        # Back button
        self._back_btn_rect = pygame.Rect(100, WINDOW_HEIGHT - 70, 150, 40)
        pygame.draw.rect(screen, BUTTON_BG, self._back_btn_rect, border_radius=6)
        back_lbl = self._button_font.render("← Back", True, BUTTON_TEXT)
        screen.blit(back_lbl, (self._back_btn_rect.x + 35, self._back_btn_rect.y + 8))
