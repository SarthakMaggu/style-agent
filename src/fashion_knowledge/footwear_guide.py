"""Footwear rules covering occasion appropriateness, condition severity, and shoe care.

Used by recommendation_agent to assess footwear and generate remarks.
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Occasion → allowed and forbidden footwear
# ---------------------------------------------------------------------------

@dataclass
class FootwearRules:
    """Allowed and forbidden footwear for an occasion."""

    occasion: str
    allowed: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    notes: str = ""


_FOOTWEAR_RULES: dict[str, FootwearRules] = {
    "indian_formal": FootwearRules(
        occasion="indian_formal",
        allowed=["mojaris", "juttis", "kolhapuris formal", "leather oxfords plain neutral"],
        forbidden=["sneakers", "sports sandals", "rubber chappals", "sport shoes", "trainers"],
        notes="Footwear must speak the same style language as the sherwani or bandhgala.",
    ),
    "wedding_guest_indian": FootwearRules(
        occasion="wedding_guest_indian",
        allowed=["mojaris", "juttis", "kolhapuris formal", "leather oxfords plain neutral"],
        forbidden=["sneakers", "sports sandals", "rubber chappals", "sport shoes", "trainers"],
        notes="Same as Indian formal — wedding context demands ethnic footwear.",
    ),
    "indian_casual": FootwearRules(
        occasion="indian_casual",
        allowed=["kolhapuris", "loafers", "clean white sneakers", "leather sandals"],
        forbidden=["formal black oxfords", "sports shoes"],
        notes="Casual but still coordinated — clean white sneakers are fine with an everyday kurta.",
    ),
    "western_formal": FootwearRules(
        occasion="western_formal",
        allowed=["oxford", "derby", "monk strap"],
        forbidden=["loafers", "sneakers", "suede shoes", "sport shoes", "chappals"],
        notes="Must be black or dark brown, polished. Suede is not formal.",
    ),
    "business_casual": FootwearRules(
        occasion="business_casual",
        allowed=["loafers", "clean leather sneakers", "chelsea boots", "derby"],
        forbidden=["sports shoes", "rubber sandals", "flip flops"],
        notes="Business casual allows loafers and clean leather sneakers.",
    ),
    "smart_casual": FootwearRules(
        occasion="smart_casual",
        allowed=["loafers", "clean leather sneakers", "chelsea boots", "derby", "brogues"],
        forbidden=["sports shoes", "rubber sandals"],
        notes="",
    ),
    "streetwear": FootwearRules(
        occasion="streetwear",
        allowed=["sneakers", "chunky trainers", "clean low-tops"],
        forbidden=["formal oxfords", "mojaris", "dress shoes"],
        notes="Condition is critical — dirty sneakers undermine the entire look.",
    ),
    "party": FootwearRules(
        occasion="party",
        allowed=["loafers", "chelsea boots", "clean leather sneakers", "dress shoes"],
        forbidden=["sports shoes", "rubber sandals", "old worn sneakers"],
        notes="",
    ),
    "casual": FootwearRules(
        occasion="casual",
        allowed=["sneakers", "loafers", "sandals", "kolhapuris", "chappals"],
        forbidden=[],
        notes="Most footwear works casually — condition still matters.",
    ),
    "travel": FootwearRules(
        occasion="travel",
        allowed=["sneakers", "loafers", "comfortable sandals", "chelsea boots"],
        forbidden=["formal dress shoes for long-haul"],
        notes="",
    ),
    "gym": FootwearRules(
        occasion="gym",
        allowed=["sport shoes", "trainers", "running shoes"],
        forbidden=["loafers", "dress shoes", "sandals", "mojaris"],
        notes="",
    ),
    "beach": FootwearRules(
        occasion="beach",
        allowed=["sandals", "flip flops", "bare feet"],
        forbidden=["dress shoes", "boots", "sneakers for beach"],
        notes="",
    ),
    "festival": FootwearRules(
        occasion="festival",
        allowed=["kolhapuris", "juttis", "sneakers", "sandals"],
        forbidden=[],
        notes="Festivals are flexible — colour and print matter more.",
    ),
    "lounge": FootwearRules(
        occasion="lounge",
        allowed=["slippers", "sandals", "socks and slides", "loafers"],
        forbidden=["formal dress shoes"],
        notes="",
    ),
    "ethnic_fusion": FootwearRules(
        occasion="ethnic_fusion",
        allowed=["loafers", "kolhapuris", "clean sneakers", "leather sandals"],
        forbidden=["formal black oxfords", "sports shoes", "rubber chappals"],
        notes="",
    ),
}


# ---------------------------------------------------------------------------
# Condition severity rules
# ---------------------------------------------------------------------------

@dataclass
class ConditionAssessment:
    """Assessment of footwear condition."""

    condition: str
    severity: str          # critical / moderate / none
    issue: str
    shoe_care_note: str


_CONDITION_RULES: dict[str, ConditionAssessment] = {
    "clean": ConditionAssessment(
        condition="clean",
        severity="none",
        issue="",
        shoe_care_note="",
    ),
    "scuffed": ConditionAssessment(
        condition="scuffed",
        severity="moderate",
        issue="Visibly scuffed leather reduces the quality signal of the entire outfit.",
        shoe_care_note="Polish before next wear, or take to a cobbler this week.",
    ),
    "dirty": ConditionAssessment(
        condition="dirty",
        severity="critical",
        issue="Dirty shoes undermine the entire look regardless of how good the outfit is.",
        shoe_care_note="Clean thoroughly before wearing again — this is a critical fix.",
    ),
    "worn out": ConditionAssessment(
        condition="worn out",
        severity="critical",
        issue="Worn-out shoes signal a lack of investment in the overall look.",
        shoe_care_note="Replace this pair — they are past the point of repair.",
    ),
    "sole peeling": ConditionAssessment(
        condition="sole peeling",
        severity="critical",
        issue="Peeling sole is immediately visible and damages the overall impression.",
        shoe_care_note="Replace immediately — cobbler repair may not be viable at this stage.",
    ),
    "yellowed sole": ConditionAssessment(
        condition="yellowed sole",
        severity="moderate",
        issue="Yellowed sole on sneakers reads as old and unmaintained.",
        shoe_care_note="Use sole whitener or replace if yellowing is severe.",
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_footwear_rules(occasion: str) -> FootwearRules | None:
    """Return allowed/forbidden footwear for an occasion.

    Args:
        occasion: Occasion string (normalised to snake_case).

    Returns:
        FootwearRules or None if occasion not found.
    """
    return _FOOTWEAR_RULES.get(occasion.lower().strip())


def is_footwear_appropriate(footwear_type: str, occasion: str) -> tuple[bool, str]:
    """Return whether footwear is appropriate for an occasion.

    Args:
        footwear_type: Detected footwear type (e.g. "sneakers", "oxford").
        occasion: Occasion string.

    Returns:
        Tuple of (is_appropriate, issue_description).
    """
    rules = get_footwear_rules(occasion)
    if rules is None:
        return True, ""  # Unknown occasion — no ruling

    fw = footwear_type.lower().strip()
    for forbidden in rules.forbidden:
        if forbidden in fw or fw in forbidden:
            return False, (
                f"'{footwear_type}' is not appropriate for {occasion}. "
                f"Recommended: {', '.join(rules.allowed[:3])}."
            )
    return True, ""


def assess_condition(condition: str) -> ConditionAssessment:
    """Return the severity and care note for a footwear condition.

    Args:
        condition: Condition string (e.g. "scuffed", "clean", "sole peeling").

    Returns:
        ConditionAssessment dataclass. Defaults to moderate severity for unknown conditions.
    """
    key = condition.lower().strip()
    if key in _CONDITION_RULES:
        return _CONDITION_RULES[key]
    # Unknown condition — default to moderate
    return ConditionAssessment(
        condition=condition,
        severity="moderate",
        issue=f"Condition '{condition}' is unclear — inspect footwear before wearing.",
        shoe_care_note="Inspect and clean or repair as needed.",
    )


def all_occasions_covered() -> bool:
    """Return True if the footwear rules cover all main occasion types."""
    required = {
        "indian_formal", "wedding_guest_indian", "indian_casual",
        "western_formal", "business_casual", "streetwear",
        "party", "casual", "gym", "beach",
    }
    return required.issubset(_FOOTWEAR_RULES.keys())
