"""
trigger_engine.py
Core logic: scans transcribed text for F1 event phrases,
applies confidence rules, and enforces cooldown timers.
"""

import time
from typing import Optional, Dict, List

# --- Phrase definitions ---
# Map trigger keywords to their canonical event type
TRIGGER_PHRASES = {
    "yellow flag":             "yellow_flag",
    "double yellow":           "yellow_flag",
    "safety car":              "safety_car",
    "virtual safety car":      "virtual_safety_car",
    "red flag":                "red_flag",
    "pit stop":                "pit_stop",
    "into the pits":           "pit_stop",
    "comes into the pits":     "pit_stop",
    "heading into the pits":   "pit_stop",
    "penalty":                 "penalty",
    "drive-through":           "penalty",
    "five-second penalty":     "penalty",
    "investigation":           "investigation",
}

# Assertive signal words that increase confidence
ASSERTIVE_SIGNALS = [
    "is out",
    "has been deployed",
    "is deployed",
    "is finally deployed",
    "we have",
    "we've got",
    "confirmed",
    "it's a",
    "it is a",
    "there is a",
    "there's a",
    "is ending",
    "comes into",
    "heading into",
    "is interrupted",
    "has been shown",
    "is waving",
    "are waving",
    "is out in",
    "we see a",
]

# Speculative words that block a trigger
SPECULATIVE_WORDS = ["might", "could", "maybe", "possibly", "perhaps"]

# Cooldown in seconds per event type
COOLDOWN_SECONDS = 10

# --- State ---
_last_triggered: Dict[str, float] = {}
_recent_mentions: Dict[str, List[float]] = {}
CONFIRM_WINDOW_S = 15  # seconds within which a second mention confirms the event


def process_transcript(text: str) -> Optional[str]:
    """
    Given a transcript string, return an event type string if a trigger
    fires, or None if no trigger should fire.
    """
    text_lower = text.lower()
    now = time.time()

    # Block if speculative language present
    if any(word in text_lower for word in SPECULATIVE_WORDS):
        return None

    for phrase, event_type in sorted(TRIGGER_PHRASES.items(), key=lambda x: len(x[0]), reverse=True):
        if phrase not in text_lower:
            continue

        is_assertive = any(signal in text_lower for signal in ASSERTIVE_SIGNALS)

        # Count mentions within this single transcript too
        phrase_count = text_lower.count(phrase)

        mentions = _recent_mentions.get(event_type, [])
        mentions = [t for t in mentions if now - t < CONFIRM_WINDOW_S]  # prune old
        mentions.append(now)
        _recent_mentions[event_type] = mentions

        confirmed = is_assertive or len(mentions) >= 2 or phrase_count >= 2

        if not confirmed:
            continue

        # Check cooldown
        last = _last_triggered.get(event_type, 0)
        if now - last < COOLDOWN_SECONDS:
            continue

        # Fire!
        _last_triggered[event_type] = now
        _recent_mentions[event_type] = []
        return event_type

    return None