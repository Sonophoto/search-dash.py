<!-- REMINDER: Maintain this file when the commit/merge cycle completes. -->

# Copilot Instructions for search-dash.py

## Project Overview

**search-dash.py** is a Linux CLI program that searches DuckDuckGo and StartPage from
the command line. It is written in Python 3 and uses `aiohttp` for async HTTP requests
and `BeautifulSoup` for HTML parsing.

## Architecture

- **searchdash.py** – Main module containing all search logic and CLI entry point.
  - `SearchEngine` – Abstract base class for search engines.
  - `DuckDuckGoSearch` / `StartPageSearch` – Concrete engine implementations that
    scrape HTML results.
  - `search_single_engine()` – Searches one engine and caps results at the
    user-specified max (CLI `-n` flag, default 20).
  - `run_search_pipeline()` – Runs all engines sequentially for a given query string,
    printing results to stdout.
  - `main()` – CLI entry point using `argparse`.
- **test_searchdash.py** – pytest test suite using mocks; no real network calls.
  Uses `pytest-asyncio` with `asyncio_mode = "auto"`.
- **pyproject.toml** – Project metadata, pytest config, and dev dependencies.

## CLI Arguments

| Flag | Dest | Type | Required | Default | Description |
|------|------|------|----------|---------|-------------|
| `-s` | `search_string` | str | yes | — | Search query (use single quotes) |
| `-n` | `max_results` | int | no | 20 | Max results per engine |

## Testing

Run tests with: `python -m pytest test_searchdash.py -v`

All tests mock HTTP calls; no network access is needed.

## Conventions

- Async code uses `asyncio.run()` in `main()`.
- Optional `uvloop` is imported if available for performance.
- Errors are printed to stderr; results to stdout.
