<!-- REMINDER: Maintain this file when the commit/merge cycle completes. -->

# Copilot Instructions for search-dash.py

## Project Overview

**search-dash.py** is a Linux CLI program that searches DuckDuckGo and StartPage from
the command line. It is written in Python 3 and uses `aiohttp` for async HTTP requests
and `BeautifulSoup` for HTML parsing.  When the search string contains `-` characters,
a pluggable substitution module iterates through letter replacements and runs the search
pipeline for each variant.

## Architecture

- **searchdash.py** – Main module (~310 lines) containing all search logic, CLI entry
  point, and the iterative substitution loop.
  - `SearchEngine` – Abstract base class for search engines.
  - `DuckDuckGoSearch` / `StartPageSearch` – Concrete engine implementations that
    scrape HTML results.
  - `search_single_engine(query, engine, session, max_results)` – Searches one
    engine and caps results at `max_results`.
  - `run_search_pipeline(query, engines, max_results)` – Runs all engines
    sequentially for a given query string, printing results to stdout.
  - `main()` – CLI entry point using `argparse`.  Dynamically loads the
    substitution module specified by `-m` (default: `dashsub`), iterates through
    substitutions, and feeds each variant into `run_search_pipeline()`.
  - `DEFAULT_MAX_RESULTS_PER_ENGINE` – Module-level constant (20) used as the
    default for the `-n` CLI flag and as the default parameter value in
    `search_single_engine()` and `run_search_pipeline()`.

- **dashsub.py** – Default substitution module.
  - `DashSub` class – Replaces every `-` in the input with a letter of the alphabet
    (a–z), advancing one letter per call.  Signals completion via `is_done()` after
    'z' has been used.
  - Public interface:
    - `process(text: str) -> str` – Perform substitution and advance state.
    - `is_done() -> bool` – `True` after all 26 letters have been used.
    - `current_letter` (property) – The letter that will be used next.

- **Plugin convention** – Any module can replace `dashsub` as long as it exposes a
  class whose name is the PascalCase version of the module name (e.g.
  `my_module` → `MyModule`) implementing `process(str) -> str` and
  `is_done() -> bool`.

- **test_searchdash.py** – pytest test suite (13 tests) using mocks; no real
  network calls. Uses `pytest-asyncio` with `asyncio_mode = "auto"`.

- **test_dashsub.py** – pytest test suite (15 tests) for the `DashSub` class.
  Covers single/multi-dash substitution, full a–z cycle, state tracking,
  `is_done()` signalling, and `StopIteration` after exhaustion.

- **pyproject.toml** – Project metadata, pytest config, and dev dependencies.

## CLI Arguments

| Flag | Dest | Type | Required | Default | Description |
|------|------|------|----------|---------|-------------|
| `-s` | `search_string` | str | yes | — | Search query (use single quotes) |
| `-n` | `max_results` | int | no | 20 | Max results per engine |
| `-m` | `module` | str | no | `dashsub` | Substitution module to load |

## Quick-Start for New Sessions

1. **Install deps:** `pip install aiohttp beautifulsoup4 pytest pytest-asyncio`
   (uvloop is optional and Linux-only).
2. **Run tests:** `python -m pytest test_searchdash.py test_dashsub.py -v` —
   expects 28 passing tests as of this writing.
3. **Verify CLI:** `python searchdash.py --help` shows usage with `-s`, `-n`,
   and `-m`.
4. **Key exports used in tests:**
   - From `searchdash`: `DEFAULT_MAX_RESULTS_PER_ENGINE`, `DuckDuckGoSearch`,
     `SearchEngine`, `StartPageSearch`, `print_engine_results`,
     `run_search_pipeline`, `search_single_engine`.
   - From `dashsub`: `DashSub`.

## Testing Details

- Run: `python -m pytest test_searchdash.py test_dashsub.py -v`
- All tests mock HTTP calls; no network access needed.
- Test helpers: `FakeEngine(name, result_count)` and `FailingEngine()` provide
  canned results and simulated failures.
- Static search term used in searchdash tests: `"chicken"`.
- `test_dashsub.py` tests cover: single/multi-dash replacement, no-dash passthrough,
  empty strings, full a–z cycle, `current_letter` tracking, `is_done()` signalling,
  and `StopIteration` after exhaustion.
- `test_searchdash.py` tests cover: result capping, custom max_results, failure
  resilience, sequential engine ordering, HTML parsing for both engines, and
  output formatting.

## Data Flow

1. User provides `-s'web-scraping'` on the CLI.
2. `main()` detects dashes in the string and loads the substitution module
   (default: `dashsub.DashSub`).
3. Loop: while `processor.is_done()` is `False`:
   a. `processor.process("web-scraping")` → `"webascraping"` (first call, letter 'a').
   b. The substituted query is passed to `run_search_pipeline()`.
   c. Results are printed to stdout.
4. After 'z' is used, `processor.is_done()` returns `True` and the program exits.

## Conventions

- Async code uses `asyncio.run()` in `main()`.
- Optional `uvloop` is imported if available for performance.
- Errors are printed to stderr; results to stdout.
- The project uses a flat layout (no `src/` directory).
- Substitution modules follow the plugin convention described above.
