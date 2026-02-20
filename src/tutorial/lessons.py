"""
Chess lessons — structured learning content.

Each lesson teaches a chess concept through the lens of military strategy,
following Magnus Carlsen's approach to the game.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Lesson:
    """Single lesson unit."""
    id: str
    title: str
    category: str
    description: str
    military_context: str
    key_points: list[str]
    example_fen: str | None = None
    example_moves: list[str] = field(default_factory=list)
    difficulty: int = 1  # 1-5


# ─────────────────────────────────────────────────────────────────────────────
# Lesson Catalogue
# ─────────────────────────────────────────────────────────────────────────────

LESSONS: list[Lesson] = [
    # ═══════ BASIC TRAINING ═══════
    Lesson(
        id="basics_01",
        title="The Battlefield — Understanding the Board",
        category="Basic Training",
        description="Learn the chess board layout — your theatre of war.",
        military_context=(
            "Every great general must know their terrain. The 64 squares of the "
            "chess board represent the battlefield — files are corridors, ranks are "
            "defensive lines, and diagonals are flanking routes."
        ),
        key_points=[
            "The board has 8 files (a-h, vertical) and 8 ranks (1-8, horizontal)",
            "Light square always goes on the right (h1 is light)",
            "Central squares (d4, d5, e4, e5) are the strategic high ground",
            "Each square has a unique name like 'e4' (file + rank)",
        ],
        difficulty=1,
    ),
    Lesson(
        id="basics_02",
        title="Infantry — The Pawn",
        category="Basic Training",
        description="Master the foot soldiers — the backbone of your army.",
        military_context=(
            "Pawns are your infantry — individually weak, but in formation they "
            "control territory and create an impenetrable wall. Magnus Carlsen "
            "is famous for his exceptional pawn play — he treats each pawn as "
            "a strategic asset."
        ),
        key_points=[
            "Pawns move forward one square, but capture diagonally",
            "First move: pawns can advance two squares",
            "En passant: capture a pawn that just moved two squares past yours",
            "Promotion: a pawn reaching the 8th rank becomes a Queen (or other piece)",
            "Magnus tip: Never move a pawn without a reason — each pawn move is permanent",
        ],
        example_fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        difficulty=1,
    ),
    Lesson(
        id="basics_03",
        title="Elite Cavalry — The Knight",
        category="Basic Training",
        description="Command the most unpredictable force on the battlefield.",
        military_context=(
            "Knights are your cavalry — they leap over obstacles and strike from "
            "unexpected angles. In Magnus's hands, a well-placed knight can "
            "dominate a bishop, especially in closed positions."
        ),
        key_points=[
            "Knights move in an L-shape: 2 squares + 1 square perpendicular",
            "Only piece that can jump over other pieces",
            "Best placed on central outposts (d5, e5, c5, f5)",
            "Magnus tip: A knight on the rim is dim — keep knights centralised",
        ],
        difficulty=1,
    ),
    Lesson(
        id="basics_04",
        title="War Elephants — The Bishop",
        category="Basic Training",
        description="Deploy your diagonal flanking force.",
        military_context=(
            "Bishops command the diagonals — the flanking routes of medieval warfare. "
            "A pair of bishops working together controls both light and dark terrain, "
            "creating devastating crossfire. Magnus values the bishop pair highly."
        ),
        key_points=[
            "Bishops move diagonally any number of squares",
            "Each bishop is locked to one color (light or dark squares)",
            "The bishop pair is worth roughly 0.5 pawns extra together",
            "Magnus tip: Open the position to unleash your bishops' full power",
        ],
        difficulty=1,
    ),
    Lesson(
        id="basics_05",
        title="Siege Towers — The Rook",
        category="Basic Training",
        description="Command the heavy artillery of your army.",
        military_context=(
            "Rooks are siege engines — they dominate open files and ranks with "
            "devastating force. Two rooks working together on the 7th rank is one "
            "of chess's most powerful formations."
        ),
        key_points=[
            "Rooks move horizontally or vertically any number of squares",
            "Most powerful on open files (no pawns blocking)",
            "Rooks on the 7th rank attack enemy pawns and restrict the king",
            "Magnus tip: Connect your rooks early and place them on open files",
        ],
        difficulty=1,
    ),
    Lesson(
        id="basics_06",
        title="The Grand General — Queen & Commander — King",
        category="Basic Training",
        description="Understand your two most important pieces.",
        military_context=(
            "The Queen is your most powerful weapon — combining rook and bishop "
            "movement. The King is your life — if it falls, you lose. Yet in "
            "the endgame, Magnus transforms the King into an attacking force."
        ),
        key_points=[
            "Queen moves like a Rook + Bishop combined (any direction, any distance)",
            "King moves one square in any direction",
            "Castling: King moves 2 squares toward a rook (special defensive move)",
            "Magnus tip: Don't bring the Queen out too early in the opening",
            "Magnus tip: Activate your King in the endgame — it's a strong piece!",
        ],
        difficulty=1,
    ),

    # ═══════ OPENING OPERATIONS ═══════
    Lesson(
        id="opening_01",
        title="Opening Principles — Seizing the Initiative",
        category="Opening Operations",
        description="Learn the fundamental opening principles Magnus follows.",
        military_context=(
            "The opening is like the initial deployment of forces. Magnus's openings "
            "emphasise rapid development, central control, and king safety. He "
            "doesn't grab material early — he builds a coordinated army."
        ),
        key_points=[
            "Control the center with pawns (e4, d4) and pieces",
            "Develop knights before bishops (Nf3, Nc3)",
            "Castle early (usually kingside) to secure your Commander",
            "Don't move the same piece twice without reason",
            "Connect your rooks by developing all minor pieces",
            "Magnus tip: Don't memorize openings — understand the principles",
        ],
        example_fen="r1bqkbnr/pppppppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        difficulty=2,
    ),
    Lesson(
        id="opening_02",
        title="The Ruy Lopez — Magnus's Weapon of Choice",
        category="Opening Operations",
        description="Learn Magnus's most-played opening as White.",
        military_context=(
            "The Ruy Lopez (1.e4 e5 2.Nf3 Nc6 3.Bb5) is a classical siege "
            "strategy — White puts pressure on Black's central soldier while "
            "developing rapidly. Magnus has played this hundreds of times at "
            "the highest level."
        ),
        key_points=[
            "1.e4 — Claim the center and open lines for Queen and Bishop",
            "2.Nf3 — Develop cavalry and attack e5 pawn",
            "3.Bb5 — Pin the knight defending e5 (the Ruy Lopez move)",
            "Plans: Build center with d4, castle kingside, slow squeeze",
            "Magnus tip: The Ruy Lopez is about long-term pressure, not quick attacks",
        ],
        example_fen="r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
        example_moves=["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
        difficulty=2,
    ),

    # ═══════ TACTICAL WARFARE ═══════
    Lesson(
        id="tactics_01",
        title="The Fork — Pincer Attack",
        category="Tactical Warfare",
        description="Attack two enemy units simultaneously.",
        military_context=(
            "A fork is a devastating pincer attack where one piece threatens "
            "two or more enemy units at once. The defender can only save one, "
            "losing the other. Knights are masters of the fork."
        ),
        key_points=[
            "Knight forks are most common — the L-shape creates surprise attacks",
            "A fork on the King forces a response, guaranteeing the other piece falls",
            "Look for undefended pieces as fork targets",
            "Magnus tip: Always check if your opponent's pieces can be forked",
        ],
        example_fen="r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
        difficulty=2,
    ),
    Lesson(
        id="tactics_02",
        title="The Pin — Immobilizing the Enemy",
        category="Tactical Warfare",
        description="Lock an enemy piece in place by threatening what's behind it.",
        military_context=(
            "A pin is a tactical maneuver where a piece attacks through an enemy "
            "unit to a more valuable target behind it. The pinned piece is frozen "
            "in place, unable to move without exposing its commander."
        ),
        key_points=[
            "Absolute pin: pinned piece shields the King (cannot legally move)",
            "Relative pin: pinned piece shields a valuable piece (can but shouldn't move)",
            "Bishops and Rooks are the primary pinning pieces",
            "Magnus tip: Pins create lasting weakness — exploit them patiently",
        ],
        difficulty=2,
    ),

    # ═══════ STRATEGIC COMMAND ═══════
    Lesson(
        id="strategy_01",
        title="Pawn Structure — The Skeleton of Battle",
        category="Strategic Command",
        description="Master the permanent framework of the position — Magnus's specialty.",
        military_context=(
            "Pawn structure is the skeleton of every chess position. Unlike pieces, "
            "pawns can never go backward. Magnus Carlsen is perhaps the greatest "
            "pawn player in chess history — he judges positions by their pawn "
            "structures and plans accordingly."
        ),
        key_points=[
            "Doubled pawns: Two pawns on the same file — usually weak",
            "Isolated pawns: A pawn with no friendly pawns on adjacent files",
            "Passed pawns: A pawn with no enemy pawns blocking its advance",
            "Pawn chains: Connected pawns supporting each other diagonally",
            "Magnus tip: Create passed pawns in the endgame — they win games",
        ],
        difficulty=3,
    ),

    # ═══════ ENDGAME MASTERY ═══════
    Lesson(
        id="endgame_01",
        title="King Activation — Magnus's Endgame Secret",
        category="Endgame Mastery",
        description="Learn why the King becomes a weapon in the endgame.",
        military_context=(
            "In the endgame, with fewer threats on the board, the King transforms "
            "from a liability into a powerful fighting piece. Magnus Carlsen's "
            "endgame play is legendary — he activates his King aggressively "
            "and grinds out wins from equal-looking positions."
        ),
        key_points=[
            "Centralize your King as the endgame approaches",
            "The King can support pawn advances and attack enemy pawns",
            "King activity often matters more than an extra pawn",
            "Opposition: Kings facing each other — whoever moves loses ground",
            "Magnus tip: In the endgame, the King is worth about 4 pawns in fighting value",
        ],
        difficulty=3,
    ),
    Lesson(
        id="endgame_02",
        title="Rook Endgames — The Ultimate Test",
        category="Endgame Mastery",
        description="The most common endgame type — master it like Magnus.",
        military_context=(
            "Rook endgames occur in about 50%% of all chess games. They are "
            "notoriously complex and subtle. Magnus's rook endgame technique "
            "is considered the best in chess history."
        ),
        key_points=[
            "Rooks belong behind passed pawns (yours or the opponent's)",
            "Cut off the enemy King with your Rook",
            "The Lucena position: the winning technique with Rook + Pawn vs Rook",
            "The Philidor position: the drawing technique for the defender",
            "Magnus tip: Study rook endgames — they're where most games are decided",
        ],
        difficulty=4,
    ),
]


def get_all_lessons() -> list[Lesson]:
    return LESSONS


def get_lesson_by_id(lesson_id: str) -> Lesson | None:
    return next((l for l in LESSONS if l.id == lesson_id), None)


def get_lessons_by_category(category: str) -> list[Lesson]:
    return [l for l in LESSONS if l.category == category]


def get_categories() -> list[str]:
    seen = set()
    cats = []
    for l in LESSONS:
        if l.category not in seen:
            cats.append(l.category)
            seen.add(l.category)
    return cats
