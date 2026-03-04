"""
content_templates.py
Maps event types to popup content: title, definition, and why it matters.
"""

TEMPLATES: dict[str, dict] = {
    "yellow_flag": {
        "title": "🟡 Yellow Flag",
        "definition": "A yellow flag signals danger ahead on track — a crashed car, debris, or a marshal on the circuit.",
        "why_it_matters": "All drivers must slow down and are forbidden from overtaking. It bunches up the field and can change race strategy.",
    },
    "red_flag": {
        "title": "🔴 Red Flag",
        "definition": "A red flag stops the race entirely, usually due to a serious crash, severe weather, or unsafe track conditions.",
        "why_it_matters": "The race is suspended and cars return to the pit lane. It can be restarted from a standing start, completely reshuffling the order.",
    },
    "safety_car": {
        "title": "🚗 Safety Car",
        "definition": "A safety car is deployed to neutralise the race when conditions are too dangerous to continue at full speed.",
        "why_it_matters": "All cars must queue up behind it and cannot overtake. Teams use this as a free opportunity to pit, making it a huge strategic moment.",
    },
    "virtual_safety_car": {
        "title": "VSC — Virtual Safety Car",
        "definition": "Like a safety car, but without a physical car on track. All drivers must slow to a set delta time.",
        "why_it_matters": "It's used for minor incidents. Drivers must maintain speed limits and cannot pit as advantageously as under a real safety car.",
    },
    "pit_stop": {
        "title": "🔧 Pit Stop",
        "definition": "A driver pulls into the pit lane to have their tyres changed and potentially receive repairs.",
        "why_it_matters": "Tyre strategy is one of F1's biggest tactical battlegrounds. When a team pits can gain or lose multiple positions.",
    },
    "penalty": {
        "title": "⚠️ Penalty",
        "definition": "A driver has been penalised for breaking a rule — common examples include overtaking off-track or unsafe releases from the pit box.",
        "why_it_matters": "Penalties add time to a driver's race result or force a drive-through, and can cost them positions or even a podium finish.",
    },
    "investigation": {
        "title": "🔍 Under Investigation",
        "definition": "The stewards are reviewing an incident to decide whether a driver broke the rules.",
        "why_it_matters": "An investigation can result in a time penalty or no further action, and the outcome may not be known until after the race.",
    },
}

def get_template(event_type: str) -> dict | None:
    return TEMPLATES.get(event_type)