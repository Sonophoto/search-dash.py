"""
Test harness for search.py

Validates the Search pass-through module for correctness:
  - Returns the input string unchanged (including dashes)
  - Signals done after one call
  - Raises StopIteration on subsequent calls
"""

import pytest

from search import Search


# ---------------------------------------------------------------------------
# Basic pass-through tests
# ---------------------------------------------------------------------------

def test_returns_string_unchanged():
    """process() returns the exact input string."""
    s = Search()
    assert s.process("hello-world") == "hello-world"


def test_returns_string_without_dashes_unchanged():
    """Strings without dashes are also returned as-is."""
    s = Search()
    assert s.process("hello world") == "hello world"


def test_empty_string():
    """An empty input returns an empty string."""
    s = Search()
    assert s.process("") == ""


# ---------------------------------------------------------------------------
# State tracking
# ---------------------------------------------------------------------------

def test_is_done_false_initially():
    """is_done is False before processing begins."""
    s = Search()
    assert s.is_done() is False


def test_is_done_true_after_process():
    """is_done is True after a single call to process."""
    s = Search()
    s.process("x")
    assert s.is_done() is True


def test_process_raises_after_done():
    """Calling process a second time raises StopIteration."""
    s = Search()
    s.process("x")
    with pytest.raises(StopIteration):
        s.process("x")
