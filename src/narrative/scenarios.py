"""
Battle scenario templates for different game situations.

Provides rich narrative text for openings, middlegame transitions,
tactical moments, endgame sequences, and game conclusions.
"""

from __future__ import annotations

import random


# ─────────────────────────────────────────────────────────────────────────────
# Opening Scenario Templates
# ─────────────────────────────────────────────────────────────────────────────

OPENING_SCENARIOS = [
    "The armies assemble on the field of battle. Drums echo across the valley as commanders survey the terrain.",
    "Dawn breaks over the battlefield. Both generals study the ground, planning their opening maneuvers.",
    "The war horns sound. Banners unfurl in the morning wind as the first units take their positions.",
    "Two great armies face each other across the central plain. The opening gambit will set the tone for the entire war.",
    "The battlefield stretches between two kingdoms. The first move will determine who seizes the initiative.",
]

# ─────────────────────────────────────────────────────────────────────────────
# Middlegame Transitions
# ─────────────────────────────────────────────────────────────────────────────

MIDDLEGAME_TRANSITIONS = [
    "The opening maneuvers are complete. The real battle begins now — steel meets steel.",
    "Both armies are fully deployed. The central conflict intensifies as the middlegame erupts.",
    "The pieces are positioned. Now the tactical warfare begins in earnest.",
    "The opening phase gives way to the fog of war. Every decision now carries grave consequences.",
]

# ─────────────────────────────────────────────────────────────────────────────
# Endgame Scenarios
# ─────────────────────────────────────────────────────────────────────────────

ENDGAME_SCENARIOS = [
    "The battlefield is littered with the fallen. The surviving forces must execute the final strategy.",
    "Few warriors remain. The Commanders themselves must lead the charge in this decisive endgame.",
    "The war has ground down to its essence. Every remaining unit is critical to victory.",
    "With most forces depleted, the endgame phase begins — technique and precision will decide the victor.",
]

# ─────────────────────────────────────────────────────────────────────────────
# Tactical Moment Descriptions
# ─────────────────────────────────────────────────────────────────────────────

TACTICAL_SCENARIOS = {
    "fork": [
        "A devastating pincer attack! {piece} threatens multiple enemy units simultaneously!",
        "The {piece} strikes with a deadly fork — two targets, one defender. A classic tactical ambush!",
        "Brilliant warfare! The {piece} attacks two enemies at once in a ruthless double threat!",
    ],
    "pin": [
        "The enemy unit is pinned in place — moving would expose their commander to attack!",
        "A surgical pin! The {piece} locks the defender in place, shielding a more valuable target.",
        "Tactical mastery — the {piece} creates an unbreakable pin on the enemy line.",
    ],
    "skewer": [
        "A piercing skewer! The high-value target must retreat, exposing the unit behind it!",
        "The {piece} drives through the enemy line — a devastating x-ray attack!",
    ],
    "discovered_attack": [
        "As the {piece} steps aside, a hidden threat is revealed — a discovered attack!",
        "The veil lifts! Moving the {piece} unleashes a concealed assault from behind!",
    ],
    "sacrifice": [
        "A bold sacrifice! The {piece} is given up to shatter the enemy's defenses!",
        "Audacious warfare! Material is offered to tear open the enemy position!",
        "The {piece} sacrifices itself for the greater strategy — a calculated gambit!",
    ],
    "check": [
        "The enemy Commander is under direct fire! Check!",
        "A strike at the heart! The enemy Sovereign must defend against this assault!",
        "CHECK! The enemy Commander scrambles to find safety!",
    ],
    "double_check": [
        "DOUBLE CHECK! Two units assail the enemy Commander simultaneously — devastation!",
        "A catastrophic double check — the enemy Sovereign has nowhere to hide!",
    ],
    "checkmate": [
        "CHECKMATE! The enemy Sovereign has fallen! Total victory on the battlefield!",
        "The war is won! The enemy Commander is cornered with no escape — CHECKMATE!",
        "Absolute triumph! The final blow lands — the enemy kingdom surrenders! CHECKMATE!",
        "The battle concludes in decisive victory! The enemy Commander is vanquished!",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Capture Descriptions
# ─────────────────────────────────────────────────────────────────────────────

CAPTURE_SCENARIOS = {
    "major": [
        "A devastating blow! The {attacker} destroys the enemy {victim} in a fierce engagement!",
        "Critical strike! The {victim} falls to the {attacker}'s assault!",
        "The {attacker} overwhelms the {victim} — a significant loss for the enemy!",
    ],
    "minor": [
        "The {attacker} engages and defeats the enemy {victim}.",
        "Combat! The {attacker} strikes down the opposing {victim}.",
        "The {victim} is eliminated by the advancing {attacker}.",
    ],
    "pawn_takes": [
        "The Infantry soldier bravely engages the enemy {victim}!",
        "A foot soldier rises above their station, taking down the {victim}!",
    ],
    "exchange": [
        "An exchange of forces! Both sides sustain losses in the engagement.",
        "The tactical exchange continues — material is traded in the heat of battle.",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Special Move Descriptions
# ─────────────────────────────────────────────────────────────────────────────

CASTLING_SCENARIOS = {
    "kingside": [
        "The Commander retreats to the fortified eastern bunker! The Siege Tower swings to guard the flank.",
        "Kingside fortification complete — the Sovereign is secured behind a wall of defenders.",
        "Strategic castle! The Commander takes shelter while the Siege Tower assumes a fighting position.",
    ],
    "queenside": [
        "The Commander seeks refuge in the western fortress! The Siege Tower races to the center.",
        "Queenside castling! A bold defensive maneuver — the Commander is secured on the long flank.",
        "The Sovereign retreats to the western stronghold as the Siege Tower repositions for battle.",
    ],
}

EN_PASSANT_SCENARIOS = [
    "A swift flanking maneuver! The Infantry catches the enemy pawn off-guard with an en passant strike!",
    "En passant! A brilliant ambush — the foot soldier intercepts the enemy pawn mid-advance!",
    "The Infantry executes a daring lateral capture — the en passant maneuver succeeds!",
]

PROMOTION_SCENARIOS = {
    "Q": [
        "Field promotion! Through valor in battle, the Infantry soldier is promoted to Grand General!",
        "The foot soldier reaches the enemy stronghold and emerges as a War Marshal! A new General is born!",
        "PROMOTION! The brave pawn earns the highest honor — elevated to the rank of Grand General!",
    ],
    "R": [
        "The Infantry earns promotion to Siege Tower Commander! A new fortress joins the army!",
    ],
    "B": [
        "Promotion! The pawn becomes a War Elephant — a new flanking force enters the field!",
    ],
    "N": [
        "The Infantry trades sword for lance — promoted to Elite Cavalry!",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# Game Result Narratives
# ─────────────────────────────────────────────────────────────────────────────

RESULT_SCENARIOS = {
    "white_wins": [
        "The White Army stands victorious! The Black Legion's Commander has fallen. Glory to the Silver Banner!",
        "Total victory for the White forces! The battlefield belongs to the conquering army!",
    ],
    "black_wins": [
        "The Black Legion triumphs! The White Commander has been vanquished. The Obsidian Standard flies high!",
        "Victory for the Black forces! The White Army crumbles before the relentless assault!",
    ],
    "stalemate": [
        "The battle reaches a standstill. Neither commander can advance — a stalemate is declared.",
        "The armies grind to a halt. With no legal maneuvers remaining, the war ends in stalemate.",
    ],
    "draw": [
        "The generals agree to a ceasefire. The battle ends in a draw — both armies live to fight another day.",
        "Neither side can claim victory. The war concludes in a diplomatic draw.",
    ],
    "resignation": [
        "The defeated commander lowers their banner in surrender. The battle is conceded.",
        "Recognising the hopeless position, the commander offers resignation. The war is over.",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_random(scenario_list: list[str], **kwargs) -> str:
    """Pick a random template and format it with kwargs."""
    template = random.choice(scenario_list)
    return template.format(**kwargs) if kwargs else template


def get_opening_scenario() -> str:
    return get_random(OPENING_SCENARIOS)


def get_middlegame_transition() -> str:
    return get_random(MIDDLEGAME_TRANSITIONS)


def get_endgame_scenario() -> str:
    return get_random(ENDGAME_SCENARIOS)


def get_checkmate_narrative() -> str:
    return get_random(TACTICAL_SCENARIOS["checkmate"])


def get_check_narrative() -> str:
    return get_random(TACTICAL_SCENARIOS["check"])


def get_result_narrative(result_key: str) -> str:
    scenarios = RESULT_SCENARIOS.get(result_key, RESULT_SCENARIOS["draw"])
    return get_random(scenarios)
