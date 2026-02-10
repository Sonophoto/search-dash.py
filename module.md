# Substitution Module Interface

This document describes how to write a substitution module (plugin) for
`searchdash.py`.  A module transforms the search string one or more times
before each search is run.  The built-in module is `dashsub`; you can create
your own by following the template below.

## How It Works

When a user passes a search string that contains `-` characters,
`searchdash.py` loads a substitution module, creates an instance of its class,
and calls it in a loop:

```
processor = YourModule()          # 1. create an instance (no arguments)

while not processor.is_done():    # 2. loop until the module says it is done
    query = processor.process(original_string)   # 3. get the next variant
    ... run search with query ...                # 4. search and print results
```

Each call to `process()` should return a new variant of the string and advance
the module's internal state.  When all variants have been produced,
`is_done()` must return `True` so the loop exits.

If the search string contains **no** dashes, `searchdash.py` skips the module
entirely and searches with the original string once.

## File and Class Naming

`searchdash.py` converts the module file name to a class name automatically
using PascalCase (split on `_`, capitalise each part):

| Module file       | Class name `searchdash.py` looks for |
|-------------------|--------------------------------------|
| `dashsub.py`      | `DashSub`                            |
| `my_module.py`    | `MyModule`                           |
| `vowel_sub.py`    | `VowelSub`                           |

Place the file in the same directory as `searchdash.py` (or anywhere on
`sys.path`) and select it with `-m`:

```bash
python3 searchdash.py -s'web-scraping' -m my_module
```

## Module Template

Copy the skeleton below into a new `.py` file, rename the class to match your
file name (see table above), and fill in the three marked sections with your
own logic.

```python
"""
my_module.py – A custom substitution module for searchdash.py

<Describe what your module does here.>
"""


class MyModule:
    """<One-line summary of what this module does.>"""

    def __init__(self):
        # ------------------------------------------------------------
        # TODO: Initialise any state your module needs.
        #
        # For example you might set up:
        #   - a list or iterator of replacement values
        #   - a counter to track the current iteration
        #   - a flag to record when you are finished
        # ------------------------------------------------------------
        self._done = False

    def process(self, text: str) -> str:
        """Transform *text* and advance to the next variant.

        This method is called once per iteration.  It receives the
        original search string every time (the same value each call).
        Return the modified string that should be used as the search
        query for this iteration.

        Raise StopIteration if called after is_done() is True.
        """
        if self._done:
            raise StopIteration("All iterations have been completed.")

        # ------------------------------------------------------------
        # TODO: Replace this section with your string processing.
        #
        # ``text`` is the original search string (e.g. 'web-scraping').
        # Transform it however you like and store the result in
        # ``result``.  Then update your internal state so the next
        # call produces a different result.
        #
        # When you have produced the last variant, set self._done to
        # True so that is_done() returns True after this call.
        # ------------------------------------------------------------
        result = text  # <-- replace with your transformation

        return result

    def is_done(self) -> bool:
        """Return True when all variants have been produced."""
        return self._done
```

### Using Your Module

```bash
python3 searchdash.py -s'web-scraping' -m my_module
```

## Required Methods — Quick Reference

### `process(text: str) -> str`

| Aspect        | Detail                                                       |
|---------------|--------------------------------------------------------------|
| **Input**     | The original search string, unchanged between calls.         |
| **Output**    | The transformed string to use as the search query.           |
| **State**     | Must advance internal state so the next call differs.        |
| **Final call**| After producing the last variant, set `is_done()` to `True`. |
| **Overrun**   | Raise `StopIteration` if called when already done.           |

### `is_done() -> bool`

| Aspect        | Detail                                                       |
|---------------|--------------------------------------------------------------|
| **Before any calls** | Must return `False`.                                  |
| **During iteration** | Must return `False`.                                  |
| **After last variant** | Must return `True`.                                 |

## Reference Implementation: `dashsub.py`

The built-in `dashsub` module is a complete working example.  It iterates
through the 26 lowercase English letters (a–z), replacing every `-` in the
input with the current letter on each call.  After the 26th call (letter `z`)
`is_done()` returns `True`.  See `dashsub.py` for the full source.
