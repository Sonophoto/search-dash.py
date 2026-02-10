"""
Test harness for dashsub.py

Validates the DashSub string-substitution module for correctness:
  - Single and multiple dash replacements
  - Full 26-letter iteration cycle
  - Proper done signalling after 'z'
  - Behaviour when the input contains no dashes
"""

import pytest

from dashsub import DashSub


# ---------------------------------------------------------------------------
# Basic substitution tests
# ---------------------------------------------------------------------------

def test_first_call_substitutes_a():
    """The first call replaces dashes with 'a'."""
    ds = DashSub()
    assert ds.process("hello-world") == "helloaworld"


def test_second_call_substitutes_b():
    """The second call replaces dashes with 'b'."""
    ds = DashSub()
    ds.process("x")          # consume 'a'
    assert ds.process("hello-world") == "hellobworld"


def test_multiple_dashes_all_replaced():
    """Every dash in the string is replaced, not just the first."""
    ds = DashSub()
    assert ds.process("a-b-c-d") == "aabacad"


def test_no_dashes_returns_unchanged():
    """If the input has no dashes, the string is returned as-is."""
    ds = DashSub()
    assert ds.process("hello world") == "hello world"


def test_only_dashes():
    """A string composed entirely of dashes is fully replaced."""
    ds = DashSub()
    assert ds.process("---") == "aaa"


def test_empty_string():
    """An empty input returns an empty string."""
    ds = DashSub()
    assert ds.process("") == ""


# ---------------------------------------------------------------------------
# State tracking and iteration
# ---------------------------------------------------------------------------

def test_current_letter_starts_at_a():
    """current_letter is 'a' before any processing."""
    ds = DashSub()
    assert ds.current_letter == "a"


def test_current_letter_advances():
    """current_letter advances after each call to process."""
    ds = DashSub()
    ds.process("x")
    assert ds.current_letter == "b"
    ds.process("x")
    assert ds.current_letter == "c"


def test_is_done_false_initially():
    """is_done is False before processing begins."""
    ds = DashSub()
    assert ds.is_done() is False


def test_is_done_false_before_z():
    """is_done remains False until 'z' has been used."""
    ds = DashSub()
    for _ in range(25):        # a through y
        ds.process("x")
    assert ds.is_done() is False


def test_is_done_true_after_z():
    """is_done becomes True after the 26th call (letter 'z')."""
    ds = DashSub()
    for _ in range(26):        # a through z
        ds.process("x")
    assert ds.is_done() is True


def test_current_letter_empty_when_done():
    """current_letter returns '' after all letters are exhausted."""
    ds = DashSub()
    for _ in range(26):
        ds.process("x")
    assert ds.current_letter == ""


def test_process_raises_after_done():
    """Calling process after all 26 letters raises StopIteration."""
    ds = DashSub()
    for _ in range(26):
        ds.process("x")
    with pytest.raises(StopIteration):
        ds.process("x")


# ---------------------------------------------------------------------------
# Full cycle validation
# ---------------------------------------------------------------------------

def test_full_cycle_substitution():
    """Walk through all 26 letters and verify the substitution for each."""
    ds = DashSub()
    for i, letter in enumerate("abcdefghijklmnopqrstuvwxyz"):
        result = ds.process("-")
        assert result == letter, f"Iteration {i}: expected '{letter}', got '{result}'"
    assert ds.is_done() is True


def test_full_cycle_with_multiple_dashes():
    """Full cycle with a multi-dash input produces correct results."""
    ds = DashSub()
    for letter in "abcdefghijklmnopqrstuvwxyz":
        result = ds.process("x-y-z")
        assert result == f"x{letter}y{letter}z"
    assert ds.is_done() is True
