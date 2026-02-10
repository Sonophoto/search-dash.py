#!/usr/bin/env python3
"""
search-dash.py - A CLI program for searching DuckDuckGo and StartPage
"""
import argparse
import asyncio
import sys
from typing import List, Dict
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


async def search_all_engines(query: str, engines: List[SearchEngine]) -> List[Dict[str, str]]:
    """Search all engines concurrently with rate limiting"""
    
    # Create aiohttp session with connection pooling
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        
        for engine in engines:
            # Add small delay for rate limiting
            await asyncio.sleep(engine.rate_limit / len(engines))
            task = engine.search(query, session)
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results and filter out exceptions
        all_results = []
        for result in results:
            if isinstance(result, Exception):
                print(f"Search failed: {result}", file=sys.stderr)
            elif isinstance(result, list):
                all_results.extend(result)
                
        return all_results


def print_results(results: List[Dict[str, str]]):
    """Print search results in a readable format"""
    if not results:
        print("No results found.")
        return
        
    print(f"\nFound {len(results)} results:\n")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. [{result['engine']}] {result['title']}")
        print(f"   URL: {result['url']}")
        if result.get('snippet'):
            print(f"   {result['snippet']}")
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Search DuckDuckGo and StartPage from the command line',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 searchdash.py -s'hello world'
  python3 searchdash.py -s'python async programming'
        """
    )
    
    parser.add_argument(
        '-s',
        dest='search_string',
        type=str,
        required=True,
        help='Search string (use single quotes)'
    )
    
    args = parser.parse_args()
    
    if not args.search_string:
        parser.error("Search string cannot be empty")
        
    print(f"Searching for: {args.search_string}")
    
    # Initialize search engines
    engines = [
        DuckDuckGoSearch(),
        StartPageSearch()
    ]
    
    # Run async search
    try:
        results = asyncio.run(search_all_engines(args.search_string, engines))
        print_results(results)
    except KeyboardInterrupt:
        print("\nSearch interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Search failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
