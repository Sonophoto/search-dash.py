"""
search.py - Pass-through search module for searchdash.py

This module performs no transformation on the search string.  It returns the
original text unchanged and immediately signals that processing is done.
Use it when you want to run a single search with the exact string provided
on the command line, even if that string contains dashes.

Usage:
    python3 searchdash.py -s'full search string' -m search
"""


class Search:
    """Pass-through processor that searches with the original string."""

    def __init__(self):
        self._done = False

    def process(self, text: str) -> str:
        """Return *text* unchanged and mark processing as complete.

        Raises:
            StopIteration: If called after processing is already done.
        """
        if self._done:
            raise StopIteration("Processing has already been completed.")

        self._done = True
        return text

    def is_done(self) -> bool:
        """Return True when processing is complete."""
        return self._done
