"""
dashsub.py - Default string-substitution module for search-dash.py

This module replaces every '-' (dash) character in an input string with a
letter of the English alphabet.  It is designed to be called repeatedly:

    1. On the first call it substitutes 'a' for every '-'.
    2. On the next call it substitutes 'b', then 'c', and so on.
    3. When 'z' is used (the 26th call) it signals that processing is done.

The module is stateful — a single DashSub instance remembers which letter
it is up to.  It is the default "plugin"; future modules can implement the
same interface (process / is_done) to provide alternative substitution
strategies.
"""

import string


class DashSub:
    """Iterative dash-to-letter substitution processor.

    Attributes:
        _index: Current position in the alphabet (0 = 'a', 25 = 'z').
        _done:  True after 'z' has been used.
    """

    # The full lowercase English alphabet used for substitutions.
    ALPHABET = string.ascii_lowercase  # 'abcdefghijklmnopqrstuvwxyz'

    def __init__(self):
        self._index = 0
        self._done = False

    # -- public interface ----------------------------------------------------

    def process(self, text: str) -> str:
        """Replace every '-' in *text* with the current letter.

        Returns the transformed string and advances the internal counter.
        After processing with 'z', :meth:`is_done` will return ``True``.

        Raises:
            StopIteration: If called after all 26 letters have been used.
        """
        if self._done:
            raise StopIteration("All 26 substitutions have been completed.")

        letter = self.ALPHABET[self._index]
        result = text.replace("-", letter)

        # If we just used 'z', mark ourselves as finished.
        if self._index == len(self.ALPHABET) - 1:
            self._done = True
        self._index += 1

        return result

    def is_done(self) -> bool:
        """Return ``True`` when all 26 letters have been used."""
        return self._done

    @property
    def current_letter(self) -> str:
        """The letter that will be used on the *next* call to :meth:`process`.

        Returns an empty string if all letters have been exhausted.
        """
        if self._done:
            return ""
        return self.ALPHABET[self._index]
