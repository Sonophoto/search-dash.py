# search-dash.py

[![CI](https://github.com/Sonophoto/search-dash.py/actions/workflows/ci.yml/badge.svg)](https://github.com/Sonophoto/search-dash.py/actions/workflows/ci.yml)

A Linux CLI program that searches DuckDuckGo and StartPage for a word with a metacharacter substitution.

## Features

- Concurrent searches on multiple search engines (DuckDuckGo and StartPage)
- **Iterative dash substitution** — when the search string contains `-` characters,
  each dash is replaced with successive letters of the alphabet (a–z) and a search
  is run for every letter automatically
- **Pluggable substitution modules** — the default module (`dashsub`) can be
  swapped via the `-m` flag for a custom module that implements the same interface
- Async I/O with aiohttp and uvloop for performance
- Rate limiting and timeout protection
- Clean command-line interface with argparse
- Beautiful Soup for HTML parsing
- Connection timeout: 10 seconds per search
- Total timeout: 30 seconds for all searches
- Graceful error handling with informative messages

## Requirements

- Python 3.8 or higher
- Dependencies (installed via pip or uv):
  - aiohttp
  - beautifulsoup4
  - uvloop (Linux/macOS only)

## Installation

### Using pip

```bash
pip install aiohttp beautifulsoup4 uvloop
```

### Using uv (recommended)

```bash
uv pip install -e .
```

## Usage

Search for a query using both search engines:

```bash
python3 searchdash.py -s'search term'
```

### Dash Substitution

When the search string contains `-` characters, the `dashsub` module
automatically replaces every dash with each letter of the alphabet in turn
(a through z), running the full search pipeline for each substitution:

```bash
# Searches for 'webascraping', 'webbscraping', … 'webzscraping'
python3 searchdash.py -s'web-scraping'
```

If the search string has **no** dashes, a single search is performed with the
original string (no substitution).

### Using a Different Module

The `-m` flag lets you specify an alternative substitution module:

```bash
python3 searchdash.py -s'web-scraping' -m my_custom_module
```

The module must expose a class (named in PascalCase from the module name,
e.g. `my_custom_module` → `MyCustomModule`) with:
- `process(text: str) -> str` — perform one substitution and advance state
- `is_done() -> bool` — return `True` when all iterations are complete

### Examples

```bash
# Search for Python programming (no dashes — single search)
python3 searchdash.py -s'python programming'

# Search for a phrase with multiple words
python3 searchdash.py -s'async await tutorial'

# Use dash substitution for compound words (26 iterations, a-z)
python3 searchdash.py -s'web-scraping'

# Limit results per engine
python3 searchdash.py -s'web-scraping' -n 5
```

## Implementation Details

The codebase is structured with:
- `SearchEngine` base class for extensibility
- Individual search engine implementations (`DuckDuckGoSearch`, `StartPageSearch`)
- `dashsub.py` — default substitution module (replaces `-` with a–z)
- Pluggable module system via `-m` flag and `importlib`
- Async search orchestration with `run_search_pipeline()`
- Clean separation of concerns: string processing → search → output

## License

See LICENSE file for details.
