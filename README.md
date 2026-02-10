# search-dash.py

A Linux CLI program that searches DuckDuckGo and StartPage concurrently using async/await.

## Features

- Concurrent searches on multiple search engines (DuckDuckGo and StartPage)
- Async I/O with aiohttp and uvloop for performance
- Rate limiting and timeout protection
- Clean command-line interface with argparse
- Beautiful Soup for HTML parsing

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

### Examples

```bash
# Search for Python programming
python3 searchdash.py -s'python programming'

# Search for a phrase with multiple words
python3 searchdash.py -s'async await tutorial'

# Use dash substitution for compound words
python3 searchdash.py -s'web-scraping'
```

## Features

### Rate Limiting
The tool includes basic rate limiting to avoid overwhelming search engines. Each search engine has a configurable rate limit (default 1.0 second).

### Robustness
- Connection timeout: 10 seconds per search
- Total timeout: 30 seconds for all searches
- Automatic retry on transient network errors
- Graceful error handling with informative messages

### Output Format
Results are displayed with:
- Search engine source
- Result title
- URL
- Text snippet (when available)

## Development

The codebase is structured with:
- `SearchEngine` base class for extensibility
- Individual search engine implementations
- Async search orchestration with `asyncio.gather()`
- Clean separation of concerns

## License

See LICENSE file for details.
