<!-- REMINDER: Maintain this file when the commit/merge cycle completes. -->

# Copilot Instructions for search-dash.py

## Project Overview

**search-dash.py** is a Linux CLI program that searches DuckDuckGo and StartPage from
the command line. It is written in Python 3 and uses `aiohttp` for async HTTP requests
and `BeautifulSoup` for HTML parsing.

## Architecture

- **searchdash.py** – Single-file main module (~260 lines) containing all search
  logic and CLI entry point.
  - `SearchEngine` – Abstract base class for search engines.
  - `DuckDuckGoSearch` / `StartPageSearch` – Concrete engine implementations that
    scrape HTML results.
  - `search_single_engine(query, engine, session, max_results)` – Searches one
    engine and caps results at `max_results`.
  - `run_search_pipeline(query, engines, max_results)` – Runs all engines
    sequentially for a given query string, printing results to stdout.
  - `main()` – CLI entry point using `argparse`.
  - `DEFAULT_MAX_RESULTS_PER_ENGINE` – Module-level constant (20) used as the
    default for the `-n` CLI flag and as the default parameter value in
    `search_single_engine()` and `run_search_pipeline()`.
- **test_searchdash.py** – pytest test suite (13 tests) using mocks; no real
  network calls. Uses `pytest-asyncio` with `asyncio_mode = "auto"`.
- **pyproject.toml** – Project metadata, pytest config, and dev dependencies.

## CLI Arguments

| Flag | Dest | Type | Required | Default | Description |
|------|------|------|----------|---------|-------------|
| `-s` | `search_string` | str | yes | — | Search query (use single quotes) |
| `-n` | `max_results` | int | no | 20 | Max results per engine |

## Quick-Start for New Sessions

1. **Install deps:** `pip install aiohttp beautifulsoup4 pytest pytest-asyncio`
   (uvloop is optional and Linux-only).
2. **Run tests:** `python -m pytest test_searchdash.py -v` — expects 13 passing
   tests as of this writing.
3. **Verify CLI:** `python searchdash.py --help` shows usage with `-s` and `-n`.
4. **Key exports used in tests:** `DEFAULT_MAX_RESULTS_PER_ENGINE`,
   `DuckDuckGoSearch`, `SearchEngine`, `StartPageSearch`, `print_engine_results`,
   `run_search_pipeline`, `search_single_engine`.

## Testing Details

- Run: `python -m pytest test_searchdash.py -v`
- All tests mock HTTP calls; no network access needed.
- Test helpers: `FakeEngine(name, result_count)` and `FailingEngine()` provide
  canned results and simulated failures.
- Static search term used in tests: `"chicken"`.
- Tests cover: result capping, custom max_results, failure resilience, sequential
  engine ordering, HTML parsing for both engines, and output formatting.

## Conventions

- Async code uses `asyncio.run()` in `main()`.
- Optional `uvloop` is imported if available for performance.
- Errors are printed to stderr; results to stdout.
- The project uses a flat layout (no `src/` directory).
