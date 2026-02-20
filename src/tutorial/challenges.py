"""
Practice challenges — tactical puzzles and training positions.

Each challenge presents a position where the player must find
the best move, reinforcing lessons learned.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Challenge:
    """A tactical puzzle / practice position."""
    id: str
    title: str
    category: str
    description: str
    fen: str
    solution_moves: list[str]         # UCI moves (correct sequence)
    hint: str
    narrative: str                     # Battle context for the puzzle
    difficulty: int = 1               # 1-5
    related_lesson: str | None = None  # lesson ID


CHALLENGES: list[Challenge] = [
    # ═══ BASIC TACTICS ═══
    Challenge(
        id="tactic_001",
        title="Knight Fork — Royal Ambush",
        category="Forks",
        description="Find the knight fork that wins material.",
        fen="r1bqk2r/pppp1ppp/2n5/4p3/1bB1n3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1",
        solution_moves=["c3d5"],
        hint="Your Cavalry can strike two valuable targets at once!",
        narrative=(
            "The enemy forces are scattered. Your Elite Cavalry spots an opening — "
            "a devastating fork that will shatter the enemy's formation!"
        ),
        difficulty=1,
        related_lesson="tactics_01",
    ),
    Challenge(
        id="tactic_002",
        title="Back Rank Mate — Siege Breakthrough",
        category="Checkmate Patterns",
        description="Deliver checkmate on the back rank.",
        fen="6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
        solution_moves=["a1a8"],
        hint="The enemy Commander is trapped behind his own Infantry!",
        narrative=(
            "The enemy Sovereign cowers behind a wall of his own foot soldiers. "
            "Your Siege Tower can breach the final defensive line!"
        ),
        difficulty=1,
    ),
    Challenge(
        id="tactic_003",
        title="Pin and Win",
        category="Pins",
        description="Use a pin to win material.",
        fen="r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
        solution_moves=["f3g5"],
        hint="Threaten the weak f7 point while keeping pressure!",
        narrative=(
            "The enemy's defenses are stretched thin. A precise strike at their "
            "weakest point will shatter their formation!"
        ),
        difficulty=2,
        related_lesson="tactics_02",
    ),
    Challenge(
        id="tactic_004",
        title="Queen Sacrifice — The Ultimate Gambit",
        category="Sacrifices",
        description="Sacrifice the Queen to force checkmate!",
        fen="r1bqr1k1/pppp1ppp/2n2n2/8/1bBPP3/2N1BN2/PPP2PPP/R2QK2R w KQ - 0 1",
        solution_moves=["d1b3"],
        hint="Sometimes the Grand General must lead the final charge!",
        narrative=(
            "The battle hangs in the balance. Your Grand General can make the "
            "ultimate sacrifice — giving her life to secure total victory!"
        ),
        difficulty=3,
    ),
    Challenge(
        id="tactic_005",
        title="Endgame Conversion — Magnus Style",
        category="Endgames",
        description="Convert a winning pawn advantage into victory.",
        fen="8/8/4k3/8/3KP3/8/8/8 w - - 0 1",
        solution_moves=["d4d5"],
        hint="Advance your Commander to support the Infantry's promotion!",
        narrative=(
            "The battlefield is nearly empty. Your lone foot soldier must "
            "reach the enemy stronghold. Your Commander leads the escort — "
            "this is Magnus Carlsen's specialty."
        ),
        difficulty=2,
        related_lesson="endgame_01",
    ),
    Challenge(
        id="tactic_006",
        title="Discovered Attack — Hidden Threat",
        category="Discovered Attacks",
        description="Move one piece to reveal an attack from another!",
        fen="r1bqkbnr/pppp1ppp/2n5/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq d3 0 3",
        solution_moves=["e5d4"],
        hint="Moving the Infantry reveals a hidden line of attack!",
        narrative=(
            "As the Infantry steps aside, a concealed threat is revealed — "
            "a devastating discovered attack that catches the enemy off-guard!"
        ),
        difficulty=2,
    ),
]


def get_all_challenges() -> list[Challenge]:
    return CHALLENGES


def get_challenge_by_id(challenge_id: str) -> Challenge | None:
    return next((c for c in CHALLENGES if c.id == challenge_id), None)


def get_challenges_by_category(category: str) -> list[Challenge]:
    return [c for c in CHALLENGES if c.category == category]


def get_challenge_categories() -> list[str]:
    seen = set()
    cats = []
    for c in CHALLENGES:
        if c.category not in seen:
            cats.append(c.category)
            seen.add(c.category)
    return cats
