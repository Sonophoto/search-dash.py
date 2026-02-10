#!/usr/bin/env python3
"""
searchdash.py - A CLI program for searching DuckDuckGo and StartPage

Supports iterative dash-substitution via pluggable modules.  The default
module (dashsub) replaces every '-' in the search string with successive
letters of the alphabet (a-z), running the search pipeline once per letter
and quitting after 'z'.  A different module can be specified with the -m
flag (future plugin support).
"""
import argparse
import asyncio
import importlib
import sys
from typing import List, Dict, Optional
from urllib.parse import quote_plus

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    # uvloop not available on Windows or not installed
    pass

import aiohttp
from bs4 import BeautifulSoup


class SearchEngine:
    """Base class for search engines"""
    
    def __init__(self, name: str, rate_limit: float = 1.0):
        self.name = name
        self.rate_limit = rate_limit
        
    async def search(self, query: str, session: aiohttp.ClientSession) -> List[Dict[str, str]]:
        """Perform search and return results"""
        raise NotImplementedError


class DuckDuckGoSearch(SearchEngine):
    """DuckDuckGo search implementation"""
    
    def __init__(self):
        super().__init__("DuckDuckGo", rate_limit=1.0)
        self.base_url = "https://html.duckduckgo.com/html/"
        
    async def search(self, query: str, session: aiohttp.ClientSession) -> List[Dict[str, str]]:
        """Search DuckDuckGo and parse results"""
        results = []
        
        try:
            # DuckDuckGo HTML version uses POST with form data
            data = {
                'q': query,
                'b': '',
                'kl': 'us-en'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with session.post(
                self.base_url,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    print(f"DuckDuckGo returned status {response.status}", file=sys.stderr)
                    return results
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Parse search results
                for result_div in soup.find_all('div', class_='result'):
                    title_elem = result_div.find('a', class_='result__a')
                    snippet_elem = result_div.find('a', class_='result__snippet')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get('href', '')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'engine': self.name
                        })
                        
        except asyncio.TimeoutError:
            print(f"Timeout searching {self.name}", file=sys.stderr)
        except Exception as e:
            print(f"Error searching {self.name}: {e}", file=sys.stderr)
            
        return results


class StartPageSearch(SearchEngine):
    """StartPage search implementation"""
    
    def __init__(self):
        super().__init__("StartPage", rate_limit=1.0)
        self.base_url = "https://www.startpage.com/do/search"
        
    async def search(self, query: str, session: aiohttp.ClientSession) -> List[Dict[str, str]]:
        """Search StartPage and parse results"""
        results = []
        
        try:
            params = {
                'query': query,
                'cat': 'web',
                'language': 'english'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with session.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    print(f"StartPage returned status {response.status}", file=sys.stderr)
                    return results
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Parse search results - StartPage uses different class names
                # Looking for result containers
                for result in soup.find_all('div', class_='w-gl__result'):
                    title_elem = result.find('a', class_='w-gl__result-title')
                    url_elem = result.find('a', class_='w-gl__result-url')
                    snippet_elem = result.find('p', class_='w-gl__description')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        url = url_elem.get('href', '') if url_elem else title_elem.get('href', '')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet,
                            'engine': self.name
                        })
                        
        except asyncio.TimeoutError:
            print(f"Timeout searching {self.name}", file=sys.stderr)
        except Exception as e:
            print(f"Error searching {self.name}: {e}", file=sys.stderr)
            
        return results


DEFAULT_MAX_RESULTS_PER_ENGINE = 20


async def search_single_engine(
    query: str,
    engine: SearchEngine,
    session: aiohttp.ClientSession,
    max_results: int = DEFAULT_MAX_RESULTS_PER_ENGINE,
) -> List[Dict[str, str]]:
    """Search one engine and return at most *max_results* results."""
    try:
        results = await engine.search(query, session)
    except Exception as exc:
        print(f"Search failed ({engine.name}): {exc}", file=sys.stderr)
        results = []
    return results[:max_results]


def print_engine_results(engine_name: str, results: List[Dict[str, str]]):
    """Print results for a single engine to stdout."""
    if not results:
        print(f"\n[{engine_name}] No results found.")
        return

    print(f"\n[{engine_name}] Found {len(results)} results:\n")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        if result.get('snippet'):
            print(f"   {result['snippet']}")
    print()


async def run_search_pipeline(
    query: str,
    engines: Optional[List[SearchEngine]] = None,
    max_results: int = DEFAULT_MAX_RESULTS_PER_ENGINE,
):
    """Run the search pipeline for a single query string.

    For each engine (in order): search, then print first *max_results* links
    to stdout.  This function isolates string processing from the caller so
    that future iterative-substitution logic only needs to provide query
    strings.
    """
    if engines is None:
        engines = [DuckDuckGoSearch(), StartPageSearch()]

    connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for engine in engines:
            results = await search_single_engine(query, engine, session, max_results)
            print_engine_results(engine.name, results)


def main():
    """Main entry point.

    When the search string contains '-' characters, the configured
    substitution module (default: dashsub) is used to iteratively replace
    them with successive letters.  Each iteration runs the full search
    pipeline.  If there are no dashes, the search is performed once with
    the original string.
    """
    parser = argparse.ArgumentParser(
        description='Search DuckDuckGo and StartPage from the command line',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 searchdash.py -s'hello world'
  python3 searchdash.py -s'python async programming'
  python3 searchdash.py -s'web-scraping'
  python3 searchdash.py -s'web-scraping' -m dashsub
        """
    )

    parser.add_argument(
        '-s',
        dest='search_string',
        type=str,
        required=True,
        help='Search string (use single quotes)'
    )

    parser.add_argument(
        '-n',
        dest='max_results',
        type=int,
        default=DEFAULT_MAX_RESULTS_PER_ENGINE,
        help=f'Maximum results per engine (default: {DEFAULT_MAX_RESULTS_PER_ENGINE})'
    )

    parser.add_argument(
        '-m',
        dest='module',
        type=str,
        default='dashsub',
        help='Substitution module to use (default: dashsub)'
    )

    args = parser.parse_args()

    # If no dashes in the input, run a single search and exit.
    if '-' not in args.search_string:
        print(f"Searching for: {args.search_string}")
        try:
            asyncio.run(run_search_pipeline(args.search_string, max_results=args.max_results))
        except KeyboardInterrupt:
            print("\nSearch interrupted by user", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Search failed: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Dynamically load the substitution module and instantiate its processor.
    # The module must expose a class whose name is the module name in PascalCase
    # (e.g. dashsub -> DashSub) with process(str)->str and is_done()->bool.
    try:
        mod = importlib.import_module(args.module)
    except ModuleNotFoundError:
        print(f"Error: substitution module '{args.module}' not found.", file=sys.stderr)
        sys.exit(1)

    # Derive class name from module name: dashsub -> DashSub
    class_name = ''.join(part.capitalize() for part in args.module.split('_'))
    try:
        processor_cls = getattr(mod, class_name)
    except AttributeError:
        print(f"Error: module '{args.module}' has no class '{class_name}'.", file=sys.stderr)
        sys.exit(1)

    processor = processor_cls()

    # Iterative substitution loop: run the pipeline once per letter until done.
    try:
        while not processor.is_done():
            query = processor.process(args.search_string)
            print(f"Searching for: {query}")
            asyncio.run(run_search_pipeline(query, max_results=args.max_results))
    except KeyboardInterrupt:
        print("\nSearch interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Search failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
