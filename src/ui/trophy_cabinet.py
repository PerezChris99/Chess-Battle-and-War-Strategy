"""
Trophy Cabinet UI — displays achievements and prizes.

Shows earned achievements with progress bars, owned prizes grouped by type,
and the player's active title/badge.
"""

from __future__ import annotations

import pygame
from typing import Any

from src.competitive.achievements import AchievementEngine, CATEGORIES, RARITY_ORDER as ACH_RARITY
from src.competitive.prizes import PrizeManager, RARITY_ORDER, PrizeDef
from src.utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    BG_COLOR, PANEL_BG, PANEL_BORDER, HEADER_BG,
    TEXT_COLOR, TEXT_DIM, TEXT_GOLD, TEXT_GREEN, TEXT_RED, TEXT_BLUE, TEXT_WHITE,
    BUTTON_BG, BUTTON_HOVER, BUTTON_TEXT,
)


# Rarity colors
RARITY_COLORS = {
    "common":    (180, 180, 180),
    "uncommon":  (80, 200, 80),
    "rare":      (80, 140, 255),
    "epic":      (200, 80, 255),
    "legendary": (255, 180, 40),
}


class TrophyCabinet:
    """Full-screen trophy cabinet — achievements and prizes display."""

    def __init__(self):
        self.achievements_engine = AchievementEngine()
        self.prize_manager = PrizeManager()
        self.player_name = "Player"

        # Cached data
        self._progress: list[dict[str, Any]] = []
        self._cabinet: dict[str, list[PrizeDef]] = {}
        self._active_title: PrizeDef | None = None
        self._active_badge: PrizeDef | None = None

        # View state
        self.tab = 0  # 0=achievements, 1=prizes
        self.scroll_y = 0
        self.max_scroll = 0

        # Buttons
        self._back_rect = pygame.Rect(20, WINDOW_HEIGHT - 60, 120, 40)
        self._tab_rects = [
            pygame.Rect(WINDOW_WIDTH // 2 - 200, 75, 190, 35),
            pygame.Rect(WINDOW_WIDTH // 2 + 10, 75, 190, 35),
        ]
        self._back_hover = False

    def refresh(self, player_name: str = "Player") -> None:
        """Reload all data from the database."""
        self.player_name = player_name
        self._progress = self.achievements_engine.get_progress(player_name)
        self._cabinet = self.prize_manager.get_trophy_cabinet(player_name)
        self._active_title = self.prize_manager.get_active_title(player_name)
        self._active_badge = self.prize_manager.get_active_badge(player_name)
        self.scroll_y = 0

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input. Returns 'BACK' to exit."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return "BACK"
            if event.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - 40)
            if event.key == pygame.K_DOWN:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 40)
            if event.key == pygame.K_TAB:
                self.tab = 1 - self.tab
                self.scroll_y = 0

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self._back_rect.collidepoint(event.pos):
                    return "BACK"
                for i, rect in enumerate(self._tab_rects):
                    if rect.collidepoint(event.pos):
                        self.tab = i
                        self.scroll_y = 0
            if event.button == 4:
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.button == 5:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 30)

        if event.type == pygame.MOUSEMOTION:
            self._back_hover = self._back_rect.collidepoint(event.pos)

        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Render the trophy cabinet."""
        screen.fill(BG_COLOR)
        self._draw_header(screen)
        self._draw_tabs(screen)

        content_y = 120
        if self.tab == 0:
            max_y = self._draw_achievements(screen, content_y)
        else:
            max_y = self._draw_prizes(screen, content_y)

        self.max_scroll = max(0, max_y + self.scroll_y - WINDOW_HEIGHT + 80)
        self._draw_back_button(screen)

    # ── Header ──────────────────────────────────────────────────

    def _draw_header(self, screen: pygame.Surface) -> None:
        header_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 70)
        pygame.draw.rect(screen, HEADER_BG, header_rect)
        pygame.draw.line(screen, PANEL_BORDER, (0, 70), (WINDOW_WIDTH, 70))

        font = pygame.font.SysFont("segoeui", 28, bold=True)
        title = font.render("🏆 TROPHY CABINET", True, TEXT_GOLD)
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 18))

    # ── Tabs ────────────────────────────────────────────────────

    def _draw_tabs(self, screen: pygame.Surface) -> None:
        font = pygame.font.SysFont("segoeui", 16, bold=True)
        labels = [
            f"🎖 Achievements ({self._earned_count}/{len(self._progress)})",
            f"🎁 Prizes ({self._prize_count})",
        ]
        for i, rect in enumerate(self._tab_rects):
            active = self.tab == i
            color = TEXT_GOLD if active else PANEL_BORDER
            bg = PANEL_BG if active else BG_COLOR
            pygame.draw.rect(screen, bg, rect, border_radius=6)
            pygame.draw.rect(screen, color, rect, 2 if active else 1, border_radius=6)
            surf = font.render(labels[i], True, TEXT_WHITE if active else TEXT_DIM)
            screen.blit(surf, (rect.x + (rect.width - surf.get_width()) // 2, rect.y + 8))

    @property
    def _earned_count(self) -> int:
        return sum(1 for p in self._progress if p["earned"])

    @property
    def _prize_count(self) -> int:
        return sum(len(v) for v in self._cabinet.values())

    # ── Achievements Tab ────────────────────────────────────────

    def _draw_achievements(self, screen: pygame.Surface, start_y: int) -> int:
        font_cat = pygame.font.SysFont("segoeui", 18, bold=True)
        font_name = pygame.font.SysFont("segoeui", 14, bold=True)
        font_desc = pygame.font.SysFont("segoeui", 12)

        y = start_y - self.scroll_y
        margin_x = 30
        card_w = WINDOW_WIDTH - 60

        # Group by category
        by_category: dict[str, list[dict]] = {}
        for p in self._progress:
            cat = p["achievement"].category
            by_category.setdefault(cat, []).append(p)

        for cat in CATEGORIES:
            if cat not in by_category:
                continue
            items = by_category[cat]

            # Category header
            if 70 < y < WINDOW_HEIGHT - 60:
                earned_in_cat = sum(1 for i in items if i["earned"])
                hdr = font_cat.render(f"{cat}  ({earned_in_cat}/{len(items)})", True, TEXT_GOLD)
                screen.blit(hdr, (margin_x, y))
            y += 30

            # Achievement cards
            for item in items:
                ach = item["achievement"]
                earned = item["earned"]
                progress = item["progress_pct"]

                card_h = 50
                card_rect = pygame.Rect(margin_x, y, card_w, card_h)

                if card_rect.bottom > 70 and card_rect.top < WINDOW_HEIGHT - 60:
                    # Card background
                    bg_col = (50, 55, 45) if earned else PANEL_BG
                    pygame.draw.rect(screen, bg_col, card_rect, border_radius=5)

                    rarity_col = RARITY_COLORS.get(ach.rarity, TEXT_DIM)
                    if earned:
                        pygame.draw.rect(screen, rarity_col, card_rect, 1, border_radius=5)

                    # Icon + Name
                    icon_surf = font_name.render(f"{ach.icon}  {ach.name}", True,
                                                  TEXT_WHITE if earned else TEXT_COLOR)
                    screen.blit(icon_surf, (margin_x + 10, y + 6))

                    # Rarity label
                    rarity_surf = font_desc.render(ach.rarity.upper(), True, rarity_col)
                    screen.blit(rarity_surf, (margin_x + card_w - rarity_surf.get_width() - 10, y + 8))

                    # Description
                    desc_surf = font_desc.render(ach.description, True, TEXT_DIM)
                    screen.blit(desc_surf, (margin_x + 10, y + 26))

                    # Progress bar
                    if not earned:
                        bar_x = margin_x + card_w - 120
                        bar_y = y + 30
                        bar_w = 100
                        bar_h = 8
                        pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
                        fill_w = int(bar_w * progress / 100)
                        if fill_w > 0:
                            pygame.draw.rect(screen, rarity_col, (bar_x, bar_y, fill_w, bar_h), border_radius=3)
                    else:
                        check = font_desc.render("✅ EARNED", True, TEXT_GREEN)
                        screen.blit(check, (margin_x + card_w - check.get_width() - 10, y + 30))

                y += card_h + 5

            y += 15  # gap between categories

        return y

    # ── Prizes Tab ──────────────────────────────────────────────

    def _draw_prizes(self, screen: pygame.Surface, start_y: int) -> int:
        font_type = pygame.font.SysFont("segoeui", 18, bold=True)
        font_name = pygame.font.SysFont("segoeui", 14, bold=True)
        font_desc = pygame.font.SysFont("segoeui", 12)

        y = start_y - self.scroll_y
        margin_x = 30
        card_w = WINDOW_WIDTH - 60

        # Active title/badge header
        if y > 70 and y < WINDOW_HEIGHT - 60:
            active_parts = []
            if self._active_title:
                active_parts.append(f"Title: {self._active_title.icon} {self._active_title.name}")
            if self._active_badge:
                active_parts.append(f"Badge: {self._active_badge.icon} {self._active_badge.name}")
            if active_parts:
                active_text = "  •  ".join(active_parts)
                active_surf = font_name.render(active_text, True, TEXT_GOLD)
                screen.blit(active_surf, (margin_x, y))
                y += 30

        type_labels = {
            "title": "🎖 TITLES",
            "badge": "🛡 BADGES",
            "medal": "⭐ WAR MEDALS",
            "banner": "🏰 BANNERS",
        }

        for prize_type in ["title", "badge", "medal", "banner"]:
            prizes = self._cabinet.get(prize_type, [])
            # Show section even if empty
            if y > 70 and y < WINDOW_HEIGHT - 60:
                label = f"{type_labels.get(prize_type, prize_type.upper())} ({len(prizes)})"
                hdr = font_type.render(label, True, TEXT_GOLD)
                screen.blit(hdr, (margin_x, y))
            y += 28

            if not prizes:
                if 70 < y < WINDOW_HEIGHT - 60:
                    empty = font_desc.render("No prizes earned yet", True, TEXT_DIM)
                    screen.blit(empty, (margin_x + 10, y))
                y += 22
            else:
                for prize in prizes:
                    card_h = 40
                    card_rect = pygame.Rect(margin_x, y, card_w, card_h)

                    if card_rect.bottom > 70 and card_rect.top < WINDOW_HEIGHT - 60:
                        rarity_col = RARITY_COLORS.get(prize.rarity, TEXT_DIM)
                        pygame.draw.rect(screen, PANEL_BG, card_rect, border_radius=5)
                        pygame.draw.rect(screen, rarity_col, card_rect, 1, border_radius=5)

                        name_surf = font_name.render(
                            f"{prize.icon}  {prize.name}", True, TEXT_WHITE
                        )
                        screen.blit(name_surf, (margin_x + 10, y + 4))

                        desc_surf = font_desc.render(prize.description, True, TEXT_DIM)
                        screen.blit(desc_surf, (margin_x + 10, y + 22))

                        rarity_surf = font_desc.render(
                            prize.rarity.upper(), True, rarity_col
                        )
                        screen.blit(rarity_surf, (
                            margin_x + card_w - rarity_surf.get_width() - 10, y + 12
                        ))

                    y += card_h + 4

            y += 15

        return y

    # ── Back Button ─────────────────────────────────────────────

    def _draw_back_button(self, screen: pygame.Surface) -> None:
        color = BUTTON_HOVER if self._back_hover else BUTTON_BG
        pygame.draw.rect(screen, color, self._back_rect, border_radius=6)
        font = pygame.font.SysFont("segoeui", 16, bold=True)
        text = font.render("← BACK (ESC)", True, BUTTON_TEXT)
        screen.blit(text, (
            self._back_rect.x + (self._back_rect.width - text.get_width()) // 2,
            self._back_rect.y + (self._back_rect.height - text.get_height()) // 2,
        ))
