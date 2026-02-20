"""
Military lore for chess pieces.

Maps each chess piece to its military counterpart with rich descriptions
for the battle narrative system.
"""

from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# Piece → Military Unit Mapping
# ─────────────────────────────────────────────────────────────────────────────

PIECE_LORE = {
    "K": {
        "title": "Supreme Commander",
        "unit": "The Sovereign",
        "rank": "Commander-in-Chief",
        "description": (
            "The heart of the army. If the Commander falls, the war is lost. "
            "Must be protected at all costs, yet in the endgame, becomes a "
            "powerful force leading the final assault."
        ),
        "move_verbs": ["commands from", "retreats to", "advances to", "repositions to"],
        "capture_verbs": ["personally strikes down", "executes"],
        "icon": "👑",
    },
    "Q": {
        "title": "Grand General",
        "unit": "War Marshal",
        "rank": "Supreme Field Commander",
        "description": (
            "The most powerful force on the battlefield. Commands unlimited range "
            "across all axes — diagonal flanking, frontal assault, and lateral "
            "maneuvers. Losing the General is a devastating blow."
        ),
        "move_verbs": ["sweeps to", "charges to", "deploys to", "maneuvers to", "storms"],
        "capture_verbs": ["overwhelms", "decimates", "crushes", "annihilates"],
        "icon": "⚔️",
    },
    "R": {
        "title": "Siege Tower",
        "unit": "Fortress Battalion",
        "rank": "Siege Commander",
        "description": (
            "The heavy artillery of medieval warfare. Commands entire files and "
            "ranks with devastating force. Most effective on open lines of attack "
            "and when doubled, forms an unstoppable siege formation."
        ),
        "move_verbs": ["advances to", "fortifies", "positions at", "rolls to"],
        "capture_verbs": ["breaches", "razes", "demolishes", "sieges"],
        "icon": "🏰",
    },
    "B": {
        "title": "War Elephant",
        "unit": "Flanking Archer Corps",
        "rank": "Flanking Commander",
        "description": (
            "Masters of diagonal warfare and flanking maneuvers. Operating in "
            "pairs, they control both light and dark terrain. A bishop pair "
            "dominates the battlefield with crossing fields of fire."
        ),
        "move_verbs": ["flanks to", "sweeps diagonally to", "repositions to", "slides to"],
        "capture_verbs": ["outflanks", "ambushes", "pierces", "snipes"],
        "icon": "🐘",
    },
    "N": {
        "title": "Elite Cavalry",
        "unit": "Mounted Vanguard",
        "rank": "Cavalry Captain",
        "description": (
            "The most unpredictable force — capable of leaping over enemy lines. "
            "Excels at surprise attacks and forking maneuvers. The only unit that "
            "can bypass barricades and strike from unexpected angles."
        ),
        "move_verbs": ["gallops to", "charges to", "leaps to", "vaults to", "rides to"],
        "capture_verbs": ["tramples", "lances", "skewers", "ambushes"],
        "icon": "🐴",
    },
    "P": {
        "title": "Infantry",
        "unit": "Foot Soldier",
        "rank": "Private",
        "description": (
            "The backbone of any army. Individually modest, but in formation "
            "they create an impenetrable wall. A pawn that reaches enemy "
            "territory earns a field promotion — rising to the rank of General."
        ),
        "move_verbs": ["marches to", "advances to", "pushes to", "steps to"],
        "capture_verbs": ["engages", "strikes", "clashes with", "overcomes"],
        "icon": "⚔️",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Army Names
# ─────────────────────────────────────────────────────────────────────────────

ARMY_NAMES = {
    True:  {"name": "White Army",    "adjective": "White",    "banner": "The Silver Banner"},
    False: {"name": "Black Legion",  "adjective": "Black",    "banner": "The Obsidian Standard"},
}


# ─────────────────────────────────────────────────────────────────────────────
# Square Terrain Names (flavour text for locations)
# ─────────────────────────────────────────────────────────────────────────────

TERRAIN_NAMES = {
    # Center squares — strategic high ground
    "d4": "the central stronghold",
    "d5": "the heart of the battlefield",
    "e4": "the eastern command post",
    "e5": "the contested highlands",
    # Flanks
    "a1": "the western fortress",
    "h1": "the eastern fortress",
    "a8": "the northern watchtower",
    "h8": "the far eastern bastion",
    # Key squares
    "f3": "the cavalry outpost",
    "c3": "the western garrison",
    "f6": "the enemy cavalry post",
    "c6": "the enemy garrison",
    "g1": "the king's bunker",
    "c1": "the queen's quarter",
    "g8": "the enemy king's bunker",
    "c8": "the enemy queen's quarter",
}


def get_piece_lore(symbol: str) -> dict:
    """Get the military lore for a piece symbol (uppercase)."""
    return PIECE_LORE.get(symbol.upper(), PIECE_LORE["P"])


def get_terrain_name(square_name: str) -> str:
    """Get flavourful terrain name for a square, or a generic description."""
    if square_name in TERRAIN_NAMES:
        return TERRAIN_NAMES[square_name]

    file_names = {
        "a": "western", "b": "west-central", "c": "central-west",
        "d": "central", "e": "central", "f": "central-east",
        "g": "east-central", "h": "eastern",
    }
    rank_names = {
        "1": "rear line", "2": "defensive line", "3": "staging ground",
        "4": "forward position", "5": "contested zone", "6": "enemy territory",
        "7": "deep enemy lines", "8": "enemy stronghold",
    }
    f = file_names.get(square_name[0], "")
    r = rank_names.get(square_name[1], "field")
    return f"the {f} {r}"


def get_army_name(is_white: bool) -> str:
    return ARMY_NAMES[is_white]["name"]


def get_army_adjective(is_white: bool) -> str:
    return ARMY_NAMES[is_white]["adjective"]
