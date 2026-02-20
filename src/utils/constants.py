"""
Global constants for Chess Battle & War Strategy.

All magic numbers, colors, sizes, and configuration values live here.
This is the single source of truth for the entire application.
"""

import os

# ─────────────────────────────────────────────────────────────────────────────
# Window & Display
# ─────────────────────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 800
FPS           = 60
TITLE         = "Chess Battle & War Strategy"

# ─────────────────────────────────────────────────────────────────────────────
# Board Geometry
# ─────────────────────────────────────────────────────────────────────────────
BOARD_SIZE    = 640
SQUARE_SIZE   = BOARD_SIZE // 8          # 80 px
BOARD_OFFSET_X = 40
BOARD_OFFSET_Y = 80

# ─────────────────────────────────────────────────────────────────────────────
# Panel Layout
# ─────────────────────────────────────────────────────────────────────────────
RIGHT_PANEL_X     = BOARD_OFFSET_X + BOARD_SIZE + 20   # 700
RIGHT_PANEL_WIDTH = WINDOW_WIDTH - RIGHT_PANEL_X - 20  # 560
RIGHT_PANEL_Y     = BOARD_OFFSET_Y

TOP_BAR_HEIGHT    = 70
BOTTOM_BAR_Y      = WINDOW_HEIGHT - 100
BOTTOM_BAR_HEIGHT = 90

# ─────────────────────────────────────────────────────────────────────────────
# Color Palette  (R, G, B)
# ─────────────────────────────────────────────────────────────────────────────

# Board —— war-themed parchment & wood
LIGHT_SQUARE     = (232, 220, 202)
DARK_SQUARE      = (166, 126,  90)

# Highlights
HIGHLIGHT_SQUARE = (186, 202,  68, 140)
VALID_MOVE_DOT   = (100, 120,  80, 160)
LAST_MOVE_COLOR  = (205, 210, 106, 120)
CHECK_COLOR      = (235,  97,  80, 150)
PREMOVE_COLOR    = (100, 140, 200, 100)

# UI chrome
BG_COLOR         = ( 28,  28,  35)
PANEL_BG         = ( 38,  38,  48)
PANEL_BORDER     = ( 58,  58,  72)
HEADER_BG        = ( 45,  42,  55)

# Text
TEXT_COLOR        = (220, 220, 220)
TEXT_DIM          = (140, 140, 150)
TEXT_GOLD         = (218, 185, 107)
TEXT_RED          = (220,  88,  78)
TEXT_GREEN        = ( 98, 190, 120)
TEXT_BLUE         = ( 88, 150, 220)
TEXT_WHITE        = (255, 255, 255)

# Buttons
BUTTON_BG        = ( 55,  55,  70)
BUTTON_HOVER     = ( 70,  70,  90)
BUTTON_ACTIVE    = ( 85,  85, 110)
BUTTON_TEXT       = (230, 230, 230)
BUTTON_GOLD      = (180, 150,  80)
BUTTON_GOLD_HOVER = (210, 180, 100)

# Piece tints
WHITE_PIECE_COLOR   = (245, 235, 220)
WHITE_PIECE_OUTLINE = (180, 160, 120)
BLACK_PIECE_COLOR   = ( 50,  50,  62)
BLACK_PIECE_OUTLINE = ( 30,  30,  40)

# Evaluation bar
EVAL_WHITE = (240, 235, 220)
EVAL_BLACK = ( 50,  50,  60)

# ─────────────────────────────────────────────────────────────────────────────
# Piece Values  (centipawns — used by evaluator)
# ─────────────────────────────────────────────────────────────────────────────
PIECE_VALUES = {
    "P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000,
    "p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 20000,
}

# ─────────────────────────────────────────────────────────────────────────────
# Unicode Chess Symbols
# ─────────────────────────────────────────────────────────────────────────────
UNICODE_PIECES = {
    "K": "\u2654", "Q": "\u2655", "R": "\u2656",
    "B": "\u2657", "N": "\u2658", "P": "\u2659",
    "k": "\u265A", "q": "\u265B", "r": "\u265C",
    "b": "\u265D", "n": "\u265E", "p": "\u265F",
}

# ─────────────────────────────────────────────────────────────────────────────
# Difficulty Levels
# ─────────────────────────────────────────────────────────────────────────────
DIFFICULTIES = {
    "RECRUIT":  {"depth": 2, "name": "Recruit",      "desc": "Learning the basics of warfare",           "elo": 800},
    "SOLDIER":  {"depth": 3, "name": "Soldier",       "desc": "A competent field soldier",                "elo": 1200},
    "CAPTAIN":  {"depth": 4, "name": "Captain",       "desc": "Tactical battlefield commander",           "elo": 1600},
    "GENERAL":  {"depth": 5, "name": "General",       "desc": "Strategic military genius",                "elo": 2000},
    "MAGNUS":   {"depth": 6, "name": "Magnus Mode",   "desc": "The Supreme Commander — Magnus Carlsen",   "elo": 2850},
}

DIFFICULTY_ORDER = ["RECRUIT", "SOLDIER", "CAPTAIN", "GENERAL", "MAGNUS"]

# ─────────────────────────────────────────────────────────────────────────────
# Game States
# ─────────────────────────────────────────────────────────────────────────────
STATE_MENU       = "MENU"
STATE_PLAYING    = "PLAYING"
STATE_GAME_OVER  = "GAME_OVER"
STATE_TUTORIAL   = "TUTORIAL"
STATE_SETTINGS   = "SETTINGS"
STATE_PROMOTION  = "PROMOTION"
STATE_LEADERBOARD = "LEADERBOARD"
STATE_ANALYSIS   = "ANALYSIS"

# ─────────────────────────────────────────────────────────────────────────────
# Animation & Timing
# ─────────────────────────────────────────────────────────────────────────────
ANIMATION_DURATION = 0.2   # seconds per move animation
AI_THINK_DELAY     = 0.3   # minimum delay before AI responds (feels natural)

# ─────────────────────────────────────────────────────────────────────────────
# File Paths
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS_DIR   = os.path.join(PROJECT_ROOT, "assets")
FONTS_DIR    = os.path.join(ASSETS_DIR, "fonts")
SOUNDS_DIR   = os.path.join(ASSETS_DIR, "sounds")
IMAGES_DIR   = os.path.join(ASSETS_DIR, "images")
DATA_DIR     = os.path.join(PROJECT_ROOT, "data")

# ─────────────────────────────────────────────────────────────────────────────
# Default Time Controls  (seconds)
# ─────────────────────────────────────────────────────────────────────────────
TIME_CONTROLS = {
    "bullet_1":   (60,   0),
    "bullet_2":   (120,  1),
    "blitz_3":    (180,  0),
    "blitz_5":    (300,  0),
    "rapid_10":   (600,  0),
    "rapid_15":   (900, 10),
    "classical":  (1800, 0),
    "unlimited":  (0,    0),
}

DEFAULT_TIME_CONTROL = "rapid_10"
