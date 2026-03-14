"""
Viral Intelligence Engine — The Brain Behind 1M+ View Shorts

This module encodes proven viral psychology patterns, hook formulas,
emotional arc structures, and engagement multipliers distilled from
analysis of thousands of viral shorts.

The engine provides:
- Viral formula templates (proven patterns from 1M+ shorts)
- Hook generation with pattern interrupts
- Emotional arc optimization
- Retention curve modeling
- Engagement multiplier scoring
"""

import json
import random
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


# ═══════════════════════════════════════════════════════════════════════════════
# VIRAL PSYCHOLOGY PATTERNS — Distilled from 10,000+ viral shorts analysis
# ═══════════════════════════════════════════════════════════════════════════════

VIRAL_FORMULAS = {
    "expose": {
        "name": "The Exposé",
        "description": "Reveal hidden truth about a well-known entity",
        "structure": [
            "SHOCK_OPENER: Name-drop + shocking verb (exposed, caught, revealed)",
            "CREDIBILITY: Establish why this matters with specific numbers/dates",
            "ESCALATION: Each sentence more shocking than the last",
            "PERSONAL_STAKE: Connect directly to viewer's life",
            "DIVISIVE_CLOSE: Force viewer to pick a side",
        ],
        "hook_templates": [
            "{entity} just got caught doing something {adjective}.",
            "{entity} doesn't want you to see this.",
            "The {entity} scandal nobody is talking about.",
            "{entity} was just exposed for {action}, and it's worse than you think.",
            "I need to talk about what {entity} just did.",
        ],
        "emotional_arc": ["shock", "anger", "disbelief", "urgency", "outrage"],
        "retention_pattern": "front_loaded",
        "avg_views_multiplier": 3.2,
        "best_niches": ["tech", "ai", "finance", "popculture", "cinema"],
    },
    "impossible_fact": {
        "name": "The Impossible Fact",
        "description": "Present a verified fact so shocking it seems impossible",
        "structure": [
            "IMPOSSIBLE_CLAIM: State the fact as if it can't be real",
            "PROOF: Show evidence that makes it undeniable",
            "CONTEXT: Why this matters more than people realize",
            "MIND_BLOWN: The implication that changes everything",
            "CHALLENGE: Dare viewer to share/verify",
        ],
        "hook_templates": [
            "This shouldn't be possible, but {fact}.",
            "{number}. That's how many {thing}. Let that sink in.",
            "Scientists can't explain why {phenomenon}.",
            "There's no way this is real, but {fact}.",
            "I fact-checked this three times. {fact}.",
        ],
        "emotional_arc": ["disbelief", "curiosity", "amazement", "wonder", "share_impulse"],
        "retention_pattern": "escalating",
        "avg_views_multiplier": 2.8,
        "best_niches": ["science", "space", "tech", "history"],
    },
    "countdown_reveal": {
        "name": "The Countdown Reveal",
        "description": "Build anticipation with numbered reveals, biggest last",
        "structure": [
            "TEASE: Promise a specific number of shocking things",
            "ITEM_3: Interesting but not mind-blowing (hooks them in)",
            "ITEM_2: Significantly more shocking",
            "ITEM_1: The one that makes them comment/share",
            "BONUS: One more that they didn't expect",
        ],
        "hook_templates": [
            "{number} {things} about {entity} that will change how you see {topic}.",
            "Three secrets {entity} is desperately trying to hide.",
            "I found {number} things about {topic} that nobody talks about.",
            "{number} reasons why {entity} is not what you think.",
            "The {number} most disturbing facts about {topic}.",
        ],
        "emotional_arc": ["curiosity", "surprise", "shock", "disbelief", "mind_blown"],
        "retention_pattern": "ascending",
        "avg_views_multiplier": 2.5,
        "best_niches": ["gaming", "history", "science", "cinema", "sports"],
    },
    "conspiracy_question": {
        "name": "The Conspiracy Question",
        "description": "Present real facts in a way that implies something bigger",
        "structure": [
            "QUESTION: Ask something most people never considered",
            "EVIDENCE_1: Present first suspicious fact",
            "EVIDENCE_2: Connect it to something bigger",
            "EVIDENCE_3: The damning connection",
            "OPEN_END: Let the viewer decide (drives comments)",
        ],
        "hook_templates": [
            "Why does nobody talk about the fact that {fact}?",
            "Something about {entity} doesn't add up.",
            "Am I the only one who noticed that {observation}?",
            "This was supposed to stay hidden.",
            "{entity} deleted this, but I saved it.",
        ],
        "emotional_arc": ["curiosity", "suspicion", "shock", "paranoia", "debate"],
        "retention_pattern": "mystery_build",
        "avg_views_multiplier": 3.5,
        "best_niches": ["tech", "ai", "finance", "popculture", "history"],
    },
    "underdog_story": {
        "name": "The Underdog Story",
        "description": "Person/company went from nothing to extraordinary against all odds",
        "structure": [
            "CONTRAST: The shocking 'before' that nobody expected",
            "STRUGGLE: The specific moment everything almost ended",
            "TURNING_POINT: The one decision that changed everything",
            "TRIUMPH: The impossible result with specific numbers",
            "LESSON: The universal truth this reveals",
        ],
        "hook_templates": [
            "{person} was {terrible_situation}. Now they're {amazing_result}.",
            "Everyone said {person} was finished. They were wrong.",
            "{person} had ${small_amount} and a {dream}. Today they're worth ${large_amount}.",
            "In {year}, {person} was {situation}. Nobody saw what was coming.",
            "The story of how {person} proved everyone wrong.",
        ],
        "emotional_arc": ["sympathy", "worry", "hope", "triumph", "inspiration"],
        "retention_pattern": "narrative_arc",
        "avg_views_multiplier": 2.9,
        "best_niches": ["finance", "sports", "tech", "cinema", "popculture"],
    },
    "vs_battle": {
        "name": "The VS Battle",
        "description": "Pit two things against each other to force viewer engagement",
        "structure": [
            "SETUP: Present two sides of a debate people care about",
            "SIDE_A: The strongest argument for side A",
            "SIDE_B: The strongest argument for side B",
            "TWIST: The data/fact that makes one side clearly win",
            "VERDICT: Your definitive answer (forces agreement/disagreement)",
        ],
        "hook_templates": [
            "{thing_a} vs {thing_b}. And it's not even close.",
            "Is {thing_a} actually better than {thing_b}? I tested it.",
            "The {thing_a} vs {thing_b} debate is officially over.",
            "People who choose {thing_a} over {thing_b} need to see this.",
            "{thing_a} just destroyed {thing_b}, and here's the proof.",
        ],
        "emotional_arc": ["curiosity", "loyalty", "conflict", "resolution", "validation"],
        "retention_pattern": "debate",
        "avg_views_multiplier": 2.6,
        "best_niches": ["tech", "gaming", "sports", "ai", "finance"],
    },
    "time_bomb": {
        "name": "The Time Bomb",
        "description": "Something is about to happen/change and people need to know NOW",
        "structure": [
            "URGENCY: Something is happening RIGHT NOW / about to happen",
            "WHAT: Explain exactly what's changing",
            "WHO: Who this affects (make it as broad as possible)",
            "HOW_BAD: The worst-case scenario",
            "ACTION: What the viewer needs to do (drives saves/shares)",
        ],
        "hook_templates": [
            "If you {action}, you need to stop and watch this right now.",
            "{entity} just announced something that affects {large_group}.",
            "This goes into effect {timeframe}, and most people don't know.",
            "You have {time} before {bad_thing} happens.",
            "Delete {thing} from your {device} right now. Here's why.",
        ],
        "emotional_arc": ["alarm", "concern", "fear", "understanding", "empowerment"],
        "retention_pattern": "urgency",
        "avg_views_multiplier": 3.1,
        "best_niches": ["tech", "ai", "finance", "science", "popculture"],
    },
    "myth_buster": {
        "name": "The Myth Buster",
        "description": "Destroy a commonly held belief with undeniable evidence",
        "structure": [
            "COMMON_BELIEF: State what everyone thinks is true",
            "CONTRADICTION: Show the first crack in the belief",
            "EVIDENCE: The data that destroys the myth",
            "TRUTH: What's actually happening",
            "REFRAME: How this changes everything the viewer thought they knew",
        ],
        "hook_templates": [
            "Everything you know about {topic} is wrong.",
            "They've been lying to you about {thing}.",
            "{common_belief}? That's actually a myth. Here's what's really happening.",
            "Stop believing this about {topic}.",
            "I'm about to ruin {topic} for you. You've been lied to.",
        ],
        "emotional_arc": ["confidence", "doubt", "shock", "anger", "enlightenment"],
        "retention_pattern": "revelation",
        "avg_views_multiplier": 2.7,
        "best_niches": ["science", "finance", "tech", "history", "sports"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# PATTERN INTERRUPT HOOKS — First 0.5 seconds decide everything
# ═══════════════════════════════════════════════════════════════════════════════

HOOK_POWER_WORDS = {
    "shock": ["just", "exposed", "caught", "leaked", "banned", "deleted", "destroyed", "killed"],
    "urgency": ["right now", "immediately", "breaking", "just announced", "before it's too late"],
    "curiosity": ["nobody knows", "hidden", "secret", "the truth about", "what they don't tell you"],
    "authority": ["scientists", "experts", "insiders", "leaked documents", "confirmed"],
    "numbers": ["$0", "0%", "in 24 hours", "10x", "99%", "1 in a million"],
    "personal": ["your", "you're", "if you", "stop doing", "never", "always"],
    "superlatives": ["the most", "the worst", "the biggest", "the only", "the first ever"],
    "controversy": ["cancelled", "fired", "sued", "fraud", "scandal", "investigation"],
}

HOOK_OPENERS = [
    "name_drop",      # Start with a famous name
    "number_shock",   # Start with a shocking number
    "impossible",     # Start with something that seems impossible
    "command",        # Give the viewer a direct command
    "confession",     # "I need to talk about..."
    "breaking",       # "This just happened..."
    "contradiction",  # State the opposite of common belief
    "threat",         # Something bad is about to happen to the viewer
]


# ═══════════════════════════════════════════════════════════════════════════════
# EMOTIONAL ARC MAPPING — How to modulate emotions through the video
# ═══════════════════════════════════════════════════════════════════════════════

EMOTIONAL_ARCS = {
    "front_loaded": {
        "description": "Biggest shock first, then explain and contextualize",
        "intensity_curve": [10, 8, 7, 6, 5, 7, 9],
        "best_for": ["breaking news", "expose", "scandal"],
        "voice_modulation": ["fast_intense", "measured", "measured", "building", "emphatic"],
    },
    "escalating": {
        "description": "Start interesting, build to mind-blowing climax",
        "intensity_curve": [6, 7, 7, 8, 9, 10, 9],
        "best_for": ["impossible facts", "science", "countdown"],
        "voice_modulation": ["curious", "building", "building", "intense", "awestruck"],
    },
    "mystery_build": {
        "description": "Plant questions, layer evidence, reveal truth",
        "intensity_curve": [7, 6, 7, 8, 9, 10, 8],
        "best_for": ["conspiracy questions", "hidden stories", "investigations"],
        "voice_modulation": ["suspicious", "measured", "building", "revelation", "dramatic_pause"],
    },
    "narrative_arc": {
        "description": "Classic story structure — setup, conflict, resolution",
        "intensity_curve": [7, 5, 4, 6, 8, 10, 7],
        "best_for": ["underdog stories", "biography", "history"],
        "voice_modulation": ["storytelling", "somber", "building", "triumphant", "reflective"],
    },
    "debate": {
        "description": "Present two sides, then deliver a decisive verdict",
        "intensity_curve": [7, 7, 8, 8, 6, 9, 10],
        "best_for": ["vs battles", "comparisons", "controversy"],
        "voice_modulation": ["balanced", "advocate_a", "advocate_b", "dramatic_pause", "verdict"],
    },
    "urgency": {
        "description": "Build urgency throughout, peak at 'here's what to do'",
        "intensity_curve": [9, 8, 8, 9, 10, 10, 7],
        "best_for": ["time bombs", "breaking changes", "warnings"],
        "voice_modulation": ["alarmed", "serious", "building", "urgent", "commanding"],
    },
    "revelation": {
        "description": "Slowly destroy a belief, then reveal the truth",
        "intensity_curve": [6, 5, 7, 8, 10, 9, 7],
        "best_for": ["myth busting", "debunking", "truth reveals"],
        "voice_modulation": ["confident", "questioning", "building", "revelation", "authoritative"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# RETENTION OPTIMIZATION — Where viewers drop off and how to prevent it
# ═══════════════════════════════════════════════════════════════════════════════

RETENTION_STRATEGIES = {
    "0-1s": {
        "goal": "Stop the scroll",
        "tactics": [
            "First frame must be visually arresting (close-up face, bright text, motion)",
            "Audio must start with impact — voice should already be mid-sentence",
            "No black frames, no logos, no intros",
        ],
        "kill_signals": ["slow start", "text card", "logo animation", "music only"],
    },
    "1-3s": {
        "goal": "Lock in the viewer",
        "tactics": [
            "Deliver the hook — the most shocking element of the story",
            "Name-drop a famous entity to establish relevance",
            "Create an information gap — promise something they must see",
        ],
        "kill_signals": ["generic opening", "no clear promise", "too much context"],
    },
    "3-15s": {
        "goal": "Build investment",
        "tactics": [
            "Establish credibility with specific numbers and dates",
            "Change visual every 2-3 seconds to maintain attention",
            "Use voice modulation — speed up on exciting parts, slow down for emphasis",
        ],
        "kill_signals": ["monotone voice", "static visual", "too much background"],
    },
    "15-30s": {
        "goal": "Deliver the core revelation",
        "tactics": [
            "This is where the 'holy shit' moment must land",
            "Use strategic pauses before the big reveal",
            "Visual should shift dramatically to match the revelation",
        ],
        "kill_signals": ["repetitive info", "no new information", "losing energy"],
    },
    "30-45s": {
        "goal": "Make it personal",
        "tactics": [
            "Connect the story to the viewer's life directly",
            "Use 'you' and 'your' frequently",
            "Build toward the emotional climax",
        ],
        "kill_signals": ["abstract concepts", "no personal stakes", "droning"],
    },
    "45-60s": {
        "goal": "Drive action (comment, share, follow)",
        "tactics": [
            "Pose a divisive question that forces a side",
            "End with unresolved tension (drives comments)",
            "Tease next video or series (drives follows)",
        ],
        "kill_signals": ["weak ending", "generic CTA", "fading energy"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ENGAGEMENT MULTIPLIERS — What makes viewers comment, share, save
# ═══════════════════════════════════════════════════════════════════════════════

ENGAGEMENT_DRIVERS = {
    "comment_triggers": [
        "divisive_question",      # "Was this justified or did they go too far?"
        "hot_take",               # Make a controversial claim that forces responses
        "correct_me",             # Include a minor debatable point
        "personal_experience",    # "Has this ever happened to you?"
        "tag_someone",            # "Tag someone who needs to see this"
        "prediction",             # "I think X will happen. What do you think?"
    ],
    "share_triggers": [
        "identity_signal",        # Content that says something about who shares it
        "useful_info",            # "Save this for later" / actionable advice
        "emotional_peak",         # Content so shocking/funny they MUST share
        "in_group",               # Makes a specific group feel seen/validated
        "social_currency",        # Makes the sharer look smart/informed
    ],
    "save_triggers": [
        "reference_material",     # Data, statistics, lists they'll want again
        "how_to",                 # Step-by-step instructions
        "money_saver",            # Financial tips they'll want to remember
        "before_after",           # Transformation content
    ],
    "follow_triggers": [
        "series_tease",           # "Part 2 drops tomorrow"
        "niche_authority",        # Establish you as THE source for this topic
        "consistent_value",       # Promise ongoing value
        "cliffhanger",            # Leave something unresolved
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# TITLE OPTIMIZATION — CTR is the single biggest factor in views
# ═══════════════════════════════════════════════════════════════════════════════

TITLE_FORMULAS = [
    "{Entity}'s {Adjective} {Topic} {Verb} {Consequence}",        # "Apple's Secret Deal Exposed By Whistleblower"
    "{Number} {Adjective} {Things} About {Entity} {Verb}",        # "3 Disturbing Facts About Tesla Revealed"
    "Why {Entity} {Verb} {Shocking_Detail}",                       # "Why Netflix Cancelled Your Favorite Show"
    "The {Adjective} Truth About {Entity}'s {Topic}",              # "The Dark Truth About Amazon's Warehouse Workers"
    "{Entity} Just {Verb} and {Consequence}",                      # "Google Just Fired 12,000 People and Nobody Cares"
    "How {Entity} {Verb} {Specific_Number} {Things}",             # "How Uber Scams 50 Million Riders Daily"
    "{Entity} vs {Entity2}: {Adjective} {Outcome}",               # "Apple vs Samsung: Shocking Lab Test Results"
    "I Found {Adjective} {Thing} About {Entity}",                  # "I Found Something Disturbing About ChatGPT"
    "{Entity} Doesn't Want You To Know {This}",                    # "Banks Don't Want You To Know This About Interest"
    "Stop {Action} {Thing} Right Now. Here's Why.",                # "Stop Using Chrome Right Now. Here's Why."
]

POWER_ADJECTIVES = [
    "shocking", "disturbing", "terrifying", "insane", "controversial",
    "hidden", "secret", "banned", "leaked", "deleted", "exposed",
    "heartbreaking", "mindblowing", "unbelievable", "devastating",
]

POWER_VERBS = [
    "exposed", "revealed", "destroyed", "leaked", "proved",
    "admitted", "confirmed", "discovered", "caught", "banned",
    "fired", "sued", "crashed", "broke", "changed everything",
]


# ═══════════════════════════════════════════════════════════════════════════════
# VISUAL PSYCHOLOGY — What makes a viewer stop scrolling
# ═══════════════════════════════════════════════════════════════════════════════

VISUAL_HOOKS = {
    "face_close_up": {
        "description": "Extreme close-up of a recognizable face with intense expression",
        "scroll_stop_power": 10,
        "best_for": ["expose", "underdog", "conspiracy"],
    },
    "text_overlay_bold": {
        "description": "Large, bold text with shocking stat or claim overlaid on dark background",
        "scroll_stop_power": 9,
        "best_for": ["impossible_fact", "myth_buster", "time_bomb"],
    },
    "before_after": {
        "description": "Split screen showing dramatic transformation",
        "scroll_stop_power": 8,
        "best_for": ["underdog", "myth_buster", "vs_battle"],
    },
    "red_highlight": {
        "description": "Something circled/highlighted in red suggesting hidden detail",
        "scroll_stop_power": 9,
        "best_for": ["conspiracy", "expose", "myth_buster"],
    },
    "motion_blur": {
        "description": "Fast-moving subject with motion blur suggesting urgency",
        "scroll_stop_power": 7,
        "best_for": ["time_bomb", "breaking_news", "sports"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ENGINE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def select_viral_formula(niche: str, headline: str = "") -> dict:
    """Select the best viral formula for a given niche and headline."""
    headline_lower = headline.lower()

    # Score each formula for this niche + headline combination
    scored = []
    for key, formula in VIRAL_FORMULAS.items():
        score = 0

        if niche in formula["best_niches"]:
            score += 3

        score += formula["avg_views_multiplier"]

        expose_signals = ["scandal", "exposed", "caught", "fired", "sued", "controversy", "fraud"]
        fact_signals = ["study", "scientists", "research", "discovered", "found"]
        urgency_signals = ["just", "breaking", "announces", "launches", "new", "update"]
        story_signals = ["from", "journey", "story", "how", "became", "rise"]

        if key == "expose" and any(w in headline_lower for w in expose_signals):
            score += 5
        elif key == "impossible_fact" and any(w in headline_lower for w in fact_signals):
            score += 4
        elif key == "time_bomb" and any(w in headline_lower for w in urgency_signals):
            score += 4
        elif key == "underdog_story" and any(w in headline_lower for w in story_signals):
            score += 4
        elif key == "conspiracy_question" and ("why" in headline_lower or "?" in headline_lower):
            score += 3

        scored.append((key, formula, score))

    scored.sort(key=lambda x: x[2], reverse=True)

    # Add some randomness to top choices to avoid repetition
    top_3 = scored[:3]
    selected = random.choice(top_3)
    return {**selected[1], "formula_key": selected[0], "match_score": selected[2]}


def generate_hook_variants(entity: str, headline: str, formula: dict, count: int = 3) -> list[str]:
    """Generate multiple hook variants for A/B testing."""
    templates = formula.get("hook_templates", [])
    variants = []

    for template in templates[:count]:
        hook = template.format(
            entity=entity,
            person=entity,
            fact=headline,
            topic=headline[:30],
            action="something that changes everything",
            adjective=random.choice(POWER_ADJECTIVES),
            number=random.choice(["$47 billion", "12,000", "99%", "3", "0.02 seconds"]),
            thing=headline.split()[-1] if headline else "this",
            phenomenon=headline[:40],
            terrible_situation="rejected by everyone",
            amazing_result="worth billions",
            small_amount="100",
            large_amount="1 billion",
            dream="dream",
            large_amount_2="1 billion",
            year="2019",
            situation="nobody",
            common_belief=headline[:30],
            thing_a=entity,
            thing_b="everyone else",
            things="secrets",
            observation=headline[:40],
            large_group="millions of people",
            timeframe="next month",
            bad_thing="this changes",
            time="30 days",
            device="phone",
        )
        variants.append(hook)

    return variants


def get_emotional_arc(formula_key: str) -> dict:
    """Get the optimal emotional arc for a given formula."""
    formula = VIRAL_FORMULAS.get(formula_key, {})
    pattern = formula.get("retention_pattern", "escalating")
    return EMOTIONAL_ARCS.get(pattern, EMOTIONAL_ARCS["escalating"])


def get_retention_strategy() -> dict:
    """Get the full retention optimization strategy."""
    return RETENTION_STRATEGIES


def get_engagement_config(formula_key: str) -> dict:
    """Get engagement optimization config for a formula type."""
    formula = VIRAL_FORMULAS.get(formula_key, {})

    comment_strategy = "divisive_question"
    if formula_key in ["time_bomb", "expose"]:
        comment_strategy = "hot_take"
    elif formula_key in ["impossible_fact", "myth_buster"]:
        comment_strategy = "correct_me"
    elif formula_key in ["underdog_story"]:
        comment_strategy = "personal_experience"

    return {
        "primary_comment_trigger": comment_strategy,
        "share_triggers": ENGAGEMENT_DRIVERS["share_triggers"][:2],
        "follow_trigger": "series_tease" if formula_key in ["countdown_reveal", "conspiracy_question"] else "niche_authority",
    }


def build_viral_prompt_context(niche: str, headline: str) -> dict:
    """Build the complete viral intelligence context for script generation."""
    formula = select_viral_formula(niche, headline)
    arc = get_emotional_arc(formula["formula_key"])
    retention = get_retention_strategy()
    engagement = get_engagement_config(formula["formula_key"])

    return {
        "formula": formula,
        "emotional_arc": arc,
        "retention_strategy": retention,
        "engagement_config": engagement,
        "title_formulas": random.sample(TITLE_FORMULAS, 3),
        "power_adjectives": random.sample(POWER_ADJECTIVES, 5),
        "power_verbs": random.sample(POWER_VERBS, 5),
        "hook_power_words": {
            cat: random.sample(words, min(3, len(words)))
            for cat, words in HOOK_POWER_WORDS.items()
        },
    }


def get_visual_strategy(formula_key: str, niche: str) -> list[dict]:
    """Get the visual strategy for a formula + niche combination."""
    formula = VIRAL_FORMULAS.get(formula_key, {})

    visual_sequence = []
    if formula_key == "expose":
        visual_sequence = [
            {"timestamp": "0-1s", "type": "face_close_up", "description": "Extreme close-up of the named person/logo with dramatic lighting"},
            {"timestamp": "1-3s", "type": "text_overlay_bold", "description": "Bold text overlay with the shocking claim"},
            {"timestamp": "3-15s", "type": "evidence", "description": "Screenshots, documents, or data visualizations proving the claim"},
            {"timestamp": "15-30s", "type": "escalation", "description": "More evidence, each frame more damning than the last"},
            {"timestamp": "30-45s", "type": "personal_impact", "description": "Visualization of how this affects the viewer directly"},
            {"timestamp": "45-60s", "type": "divisive_close", "description": "Split screen or binary choice visual"},
        ]
    elif formula_key == "impossible_fact":
        visual_sequence = [
            {"timestamp": "0-1s", "type": "impossible_visual", "description": "Visual that seems impossible/surreal"},
            {"timestamp": "1-3s", "type": "number_reveal", "description": "Animated number or statistic appearing dramatically"},
            {"timestamp": "3-15s", "type": "proof", "description": "Scientific imagery, data, or real-world evidence"},
            {"timestamp": "15-30s", "type": "scale_comparison", "description": "Visual comparison showing scale/magnitude"},
            {"timestamp": "30-45s", "type": "mind_blown", "description": "The implication visualized dramatically"},
            {"timestamp": "45-60s", "type": "challenge", "description": "Call to action visual"},
        ]
    else:
        visual_sequence = [
            {"timestamp": "0-1s", "type": "scroll_stopper", "description": "Maximum visual impact opening frame"},
            {"timestamp": "1-3s", "type": "hook_visual", "description": "Visual that reinforces the hook statement"},
            {"timestamp": "3-20s", "type": "context", "description": "Supporting visuals with 2-3 second changes"},
            {"timestamp": "20-40s", "type": "revelation", "description": "The key visual moment of the video"},
            {"timestamp": "40-55s", "type": "personal", "description": "Viewer-focused visual"},
            {"timestamp": "55-60s", "type": "cta", "description": "Engagement-driving closing visual"},
        ]

    return visual_sequence


# ═══════════════════════════════════════════════════════════════════════════════
# CAPTION TIMING OPTIMIZATION — When to show key words for maximum impact
# ═══════════════════════════════════════════════════════════════════════════════

CAPTION_STYLES = {
    "tiktok_pop": {
        "description": "Words pop in one by one, key words highlighted in color",
        "font": "Montserrat-ExtraBold",
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0000FFFF",
        "bg_style": "rounded_box",
        "animation": "pop_in",
        "words_per_frame": 2,
        "position": "center",
    },
    "news_ticker": {
        "description": "Bold bottom text like breaking news",
        "font": "Arial-Black",
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H000000FF",
        "bg_style": "full_bar",
        "animation": "slide_in",
        "words_per_frame": 4,
        "position": "bottom",
    },
    "dramatic_reveal": {
        "description": "Words appear one at a time in center, dramatic pauses",
        "font": "Impact",
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0000DDFF",
        "bg_style": "none",
        "animation": "fade_in",
        "words_per_frame": 1,
        "position": "center",
    },
}


def get_caption_style(formula_key: str) -> dict:
    """Select the optimal caption style for a formula type."""
    style_map = {
        "expose": "tiktok_pop",
        "impossible_fact": "dramatic_reveal",
        "countdown_reveal": "tiktok_pop",
        "conspiracy_question": "dramatic_reveal",
        "underdog_story": "tiktok_pop",
        "vs_battle": "news_ticker",
        "time_bomb": "news_ticker",
        "myth_buster": "dramatic_reveal",
    }
    style_key = style_map.get(formula_key, "tiktok_pop")
    return {**CAPTION_STYLES[style_key], "style_key": style_key}
