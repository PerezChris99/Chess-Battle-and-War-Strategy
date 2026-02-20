"""
Leaderboard & Ranking UI Screen.

Full-screen display showing:
- Player profile card (ELO, tier, stats)
- Unified leaderboard (player + all AI opponents)
- Recent match history
- Head-to-head records
"""

from __future__ import annotations

import pygame
from typing import Optional

from src.competitive.leaderboard import Leaderboard, LeaderboardEntry
from src.competitive.ranking import get_tier, TIERS
from src.competitive.stats import StatsTracker
from src.utils.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    BG_COLOR, PANEL_BG, PANEL_BORDER, HEADER_BG,
    TEXT_COLOR, TEXT_DIM, TEXT_GOLD, TEXT_GREEN, TEXT_RED, TEXT_BLUE, TEXT_WHITE,
    BUTTON_BG, BUTTON_HOVER, BUTTON_TEXT,
)


class LeaderboardScreen:
    """Full-screen leaderboard and ranking display."""

    def __init__(self):
        self.leaderboard = Leaderboard()
        self.stats_tracker = StatsTracker()
        self.player_name = "Player"

        # Cached data
        self._entries: list[LeaderboardEntry] = []
        self._summary: dict = {}
        self._recent_matches: list[dict] = []
        self._display_stats: list[tuple[str, str]] = []
        self._rating_change: Optional[dict] = None

        # Scroll state
        self.scroll_y = 0
        self.max_scroll = 0

        # Button states
        self._back_rect = pygame.Rect(20, WINDOW_HEIGHT - 60, 120, 40)
        self._back_hover = False

    def refresh(self, player_name: str = "Player") -> None:
        """Reload all leaderboard data from the database."""
        self.player_name = player_name
        self._entries = self.leaderboard.get_unified_leaderboard(player_name)
        self._summary = self.leaderboard.get_player_summary(player_name)
        self._recent_matches = self.leaderboard.get_recent_matches(player_name, 10)
        self._display_stats = self.stats_tracker.get_display_stats(player_name)
        self.scroll_y = 0

    def set_rating_change(self, change: dict) -> None:
        """Set the most recent rating change for display emphasis."""
        self._rating_change = change

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle input. Returns 'BACK' to exit."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                return "BACK"
            if event.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - 40)
            if event.key == pygame.K_DOWN:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 40)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self._back_rect.collidepoint(event.pos):
                    return "BACK"
            # Scroll wheel
            if event.button == 4:
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.button == 5:
                self.scroll_y = min(self.max_scroll, self.scroll_y + 30)

        if event.type == pygame.MOUSEMOTION:
            self._back_hover = self._back_rect.collidepoint(event.pos)

        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Render the leaderboard screen."""
        screen.fill(BG_COLOR)

        # Header
        self._draw_header(screen)

        # Two-column layout
        left_x = 30
        right_x = WINDOW_WIDTH // 2 + 15
        col_width = WINDOW_WIDTH // 2 - 45
        content_y = 80

        # Left column: Player profile + stats
        y = content_y - self.scroll_y
        y = self._draw_player_profile(screen, left_x, y, col_width)
        y += 15
        y = self._draw_stats_panel(screen, left_x, y, col_width)
        y += 15
        y = self._draw_recent_matches(screen, left_x, y, col_width)

        # Right column: Leaderboard table
        self._draw_leaderboard_table(screen, right_x, content_y, col_width)

        # Calculate scroll bounds
        self.max_scroll = max(0, y + self.scroll_y - WINDOW_HEIGHT + 80)

        # Back button
        self._draw_back_button(screen)

    # ── Header ──────────────────────────────────────────────────

    def _draw_header(self, screen: pygame.Surface) -> None:
        header_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 70)
        pygame.draw.rect(screen, HEADER_BG, header_rect)
        pygame.draw.line(screen, PANEL_BORDER, (0, 70), (WINDOW_WIDTH, 70))

        font = pygame.font.SysFont("segoeui", 28, bold=True)
        title = font.render("⚔ LEADERBOARD & RANKINGS", True, TEXT_GOLD)
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 18))

    # ── Player Profile Card ─────────────────────────────────────

    def _draw_player_profile(self, screen: pygame.Surface, x: int, y: int, w: int) -> int:
        if not self._summary:
            return y

        s = self._summary
        tier_info = get_tier(s["elo"])
        card_h = 150
        card_rect = pygame.Rect(x, y, w, card_h)

        if card_rect.bottom > 70 and card_rect.top < WINDOW_HEIGHT - 60:
            pygame.draw.rect(screen, PANEL_BG, card_rect, border_radius=8)
            pygame.draw.rect(screen, PANEL_BORDER, card_rect, 1, border_radius=8)

            # Tier color bar on left
            tier_bar = pygame.Rect(x, y, 6, card_h)
            pygame.draw.rect(screen, tier_info["color"], tier_bar, border_radius=3)

            font_lg = pygame.font.SysFont("segoeui", 22, bold=True)
            font_md = pygame.font.SysFont("segoeui", 16)
            font_sm = pygame.font.SysFont("segoeui", 13)

            # Name and ELO
            name_surf = font_lg.render(f"{s['badge']}  {s['name']}", True, TEXT_WHITE)
            screen.blit(name_surf, (x + 18, y + 12))

            elo_color = TEXT_GOLD
            elo_surf = font_lg.render(f"{s['elo']} ELO", True, elo_color)
            screen.blit(elo_surf, (x + w - elo_surf.get_width() - 18, y + 12))

            # Tier and rank
            tier_surf = font_md.render(f"{s['tier']}  •  Rank #{s['rank']}", True, tier_info["color"])
            screen.blit(tier_surf, (x + 18, y + 42))

            peak_surf = font_sm.render(f"Peak: {s['peak_elo']}", True, TEXT_DIM)
            screen.blit(peak_surf, (x + w - peak_surf.get_width() - 18, y + 45))

            # W/L/D row
            record_y = y + 72
            wr = s["win_rate"] * 100
            stats_parts = [
                (f"W: {s['wins']}", TEXT_GREEN),
                (f"L: {s['losses']}", TEXT_RED),
                (f"D: {s['draws']}", TEXT_BLUE),
                (f"WR: {wr:.0f}%", TEXT_COLOR),
            ]
            sx = x + 18
            for text, color in stats_parts:
                surf = font_md.render(text, True, color)
                screen.blit(surf, (sx, record_y))
                sx += surf.get_width() + 20

            # Streak
            streak_text = f"Streak: {s['win_streak']}  (Best: {s['best_streak']})"
            streak_surf = font_sm.render(streak_text, True, TEXT_DIM)
            screen.blit(streak_surf, (x + 18, record_y + 28))

            # Rating change highlight
            if self._rating_change:
                rc = self._rating_change
                change = rc.get("change", 0)
                if change > 0:
                    change_text = f"+{change}"
                    change_color = TEXT_GREEN
                elif change < 0:
                    change_text = str(change)
                    change_color = TEXT_RED
                else:
                    change_text = "±0"
                    change_color = TEXT_DIM
                rc_surf = font_md.render(change_text, True, change_color)
                screen.blit(rc_surf, (x + w - rc_surf.get_width() - 18, record_y))

        return y + card_h

    # ── Stats Panel ─────────────────────────────────────────────

    def _draw_stats_panel(self, screen: pygame.Surface, x: int, y: int, w: int) -> int:
        if not self._display_stats:
            return y

        font_header = pygame.font.SysFont("segoeui", 16, bold=True)
        font_stat = pygame.font.SysFont("segoeui", 14)
        row_h = 24
        panel_h = 30 + len(self._display_stats) * row_h + 10
        panel_rect = pygame.Rect(x, y, w, panel_h)

        if panel_rect.bottom > 70 and panel_rect.top < WINDOW_HEIGHT - 60:
            pygame.draw.rect(screen, PANEL_BG, panel_rect, border_radius=6)
            pygame.draw.rect(screen, PANEL_BORDER, panel_rect, 1, border_radius=6)

            header_surf = font_header.render("BATTLE STATISTICS", True, TEXT_GOLD)
            screen.blit(header_surf, (x + 12, y + 8))

            sy = y + 32
            for label, value in self._display_stats:
                label_surf = font_stat.render(label, True, TEXT_DIM)
                value_surf = font_stat.render(value, True, TEXT_COLOR)
                screen.blit(label_surf, (x + 16, sy))
                screen.blit(value_surf, (x + w - value_surf.get_width() - 16, sy))
                sy += row_h

        return y + panel_h

    # ── Recent Matches ──────────────────────────────────────────

    def _draw_recent_matches(self, screen: pygame.Surface, x: int, y: int, w: int) -> int:
        if not self._recent_matches:
            return y

        font_header = pygame.font.SysFont("segoeui", 16, bold=True)
        font_match = pygame.font.SysFont("segoeui", 13)
        row_h = 26
        panel_h = 30 + min(len(self._recent_matches), 10) * row_h + 10
        panel_rect = pygame.Rect(x, y, w, panel_h)

        if panel_rect.bottom > 70 and panel_rect.top < WINDOW_HEIGHT - 60:
            pygame.draw.rect(screen, PANEL_BG, panel_rect, border_radius=6)
            pygame.draw.rect(screen, PANEL_BORDER, panel_rect, 1, border_radius=6)

            header_surf = font_header.render("RECENT BATTLES", True, TEXT_GOLD)
            screen.blit(header_surf, (x + 12, y + 8))

            sy = y + 32
            for match in self._recent_matches[:10]:
                won = match["player_won"]
                if won == 1:
                    result_text = "WIN"
                    result_color = TEXT_GREEN
                elif won == 0:
                    result_text = "LOSS"
                    result_color = TEXT_RED
                else:
                    result_text = "DRAW"
                    result_color = TEXT_BLUE

                res_surf = font_match.render(result_text, True, result_color)
                screen.blit(res_surf, (x + 16, sy))

                opp_surf = font_match.render(f"vs {match['opponent_name']}", True, TEXT_COLOR)
                screen.blit(opp_surf, (x + 70, sy))

                change = match["elo_change"]
                if change > 0:
                    elo_str = f"+{change}"
                    elo_col = TEXT_GREEN
                elif change < 0:
                    elo_str = str(change)
                    elo_col = TEXT_RED
                else:
                    elo_str = "±0"
                    elo_col = TEXT_DIM
                elo_surf = font_match.render(elo_str, True, elo_col)
                screen.blit(elo_surf, (x + w - elo_surf.get_width() - 16, sy))

                sy += row_h

        return y + panel_h

    # ── Leaderboard Table ───────────────────────────────────────

    def _draw_leaderboard_table(self, screen: pygame.Surface, x: int, y: int, w: int) -> None:
        font_header = pygame.font.SysFont("segoeui", 16, bold=True)
        font_row = pygame.font.SysFont("segoeui", 14)
        ROW_H = 36

        # Panel background
        table_h = 50 + len(self._entries) * ROW_H + 10
        panel_rect = pygame.Rect(x, y, w, min(table_h, WINDOW_HEIGHT - y - 70))
        pygame.draw.rect(screen, PANEL_BG, panel_rect, border_radius=8)
        pygame.draw.rect(screen, PANEL_BORDER, panel_rect, 1, border_radius=8)

        # Table header
        header_surf = font_header.render("UNIFIED RANKINGS", True, TEXT_GOLD)
        screen.blit(header_surf, (x + 12, y + 10))

        # Column headers
        col_y = y + 38
        cols = [
            (x + 12,  "#",     50),
            (x + 50,  "Name",  180),
            (x + 230, "ELO",   60),
            (x + 295, "Tier",  80),
            (x + 380, "W/L/D", 100),
            (x + 485, "WR",    50),
        ]
        for cx, label, _ in cols:
            surf = font_row.render(label, True, TEXT_DIM)
            screen.blit(surf, (cx, col_y))

        # Separator
        pygame.draw.line(
            screen, PANEL_BORDER,
            (x + 8, col_y + 22), (x + w - 8, col_y + 22)
        )

        # Rows
        row_y = col_y + 28
        for entry in self._entries:
            if row_y < y + 38:
                row_y += ROW_H
                continue
            if row_y > panel_rect.bottom - 10:
                break

            # Highlight current player
            if entry.is_current_player:
                highlight = pygame.Surface((w - 16, ROW_H - 4), pygame.SRCALPHA)
                highlight.fill((80, 120, 60, 50))
                screen.blit(highlight, (x + 8, row_y - 2))

            # Rank
            rank_color = TEXT_GOLD if entry.rank <= 3 else TEXT_COLOR
            rank_surf = font_row.render(f"{entry.rank}", True, rank_color)
            screen.blit(rank_surf, (x + 16, row_y))

            # Name
            name_color = TEXT_WHITE if entry.is_current_player else TEXT_COLOR
            name_text = entry.name
            if len(name_text) > 18:
                name_text = name_text[:17] + "…"
            name_surf = font_row.render(name_text, True, name_color)
            screen.blit(name_surf, (x + 50, row_y))

            # ELO
            elo_surf = font_row.render(str(entry.elo), True, TEXT_GOLD)
            screen.blit(elo_surf, (x + 230, row_y))

            # Tier badge
            tier_info = get_tier(entry.elo)
            tier_surf = font_row.render(entry.tier, True, tier_info["color"])
            screen.blit(tier_surf, (x + 295, row_y))

            # W/L/D
            wld = f"{entry.wins}/{entry.losses}/{entry.draws}"
            wld_surf = font_row.render(wld, True, TEXT_DIM)
            screen.blit(wld_surf, (x + 380, row_y))

            # Win rate
            wr_text = f"{entry.win_rate * 100:.0f}%" if entry.games_played > 0 else "—"
            wr_surf = font_row.render(wr_text, True, TEXT_COLOR)
            screen.blit(wr_surf, (x + 485, row_y))

            row_y += ROW_H

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
