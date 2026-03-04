"""
Tests for trigger_engine.py
Run with: pytest tests/
"""

import sys
sys.path.insert(0, "../backend")

from backend.trigger_engine import process_transcript

def test_assertive_yellow_flag():
    result = process_transcript("We have a yellow flag on track at turn 3")
    assert result == "yellow_flag"

def test_speculative_no_trigger():
    result = process_transcript("There might be a yellow flag coming out")
    assert result is None

def test_red_flag_confirmed():
    result = process_transcript("It's a red flag, the race has been stopped")
    assert result == "red_flag"

def test_pit_stop():
    result = process_transcript("Hamilton is into the pits for new tyres")
    assert result == "pit_stop"
