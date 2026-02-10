"""
Test harness for searchdash.py

Uses the static search term 'chicken' and mocks network calls to validate
that string processing is properly isolated from network logic.
"""
import asyncio
import sys
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from searchdash import (
    DuckDuckGoSearch,
    MAX_RESULTS_PER_ENGINE,
    SearchEngine,
    StartPageSearch,
    print_engine_results,
    run_search_pipeline,
    search_single_engine,
)

SEARCH_TERM = "chicken"
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_results(engine_name: str, count: int):
    """Return a list of fake result dicts."""
    return [
        {
            "title": f"Result {i} for {SEARCH_TERM}",
            "url": f"https://example.com/{engine_name.lower()}/{i}",
            "snippet": f"Snippet {i}",
            "engine": engine_name,
        }
        for i in range(1, count + 1)
    ]


class FakeEngine(SearchEngine):
    """A search engine that returns canned results without network access."""

    def __init__(self, name: str, result_count: int = 5):
        super().__init__(name)
        self.result_count = result_count
        self.last_query = None

    async def search(self, query, session):
        self.last_query = query
        return _make_results(self.name, self.result_count)


class FailingEngine(SearchEngine):
    """A search engine that always raises."""

    def __init__(self):
        super().__init__("FailEngine")

    async def search(self, query, session):
        raise RuntimeError("network down")
# ---------------------------------------------------------------------------
# Tests for search_single_engine
# ---------------------------------------------------------------------------
async def test_search_single_engine_returns_results():
    """search_single_engine returns results from the engine."""
    engine = FakeEngine("TestEngine", result_count=3)
    session = MagicMock()
    results = await search_single_engine(SEARCH_TERM, engine, session)
    assert len(results) == 3
    assert engine.last_query == SEARCH_TERM


async def test_search_single_engine_caps_at_max():
    """Results are capped at MAX_RESULTS_PER_ENGINE (20)."""
    engine = FakeEngine("BigEngine", result_count=30)
    session = MagicMock()
    results = await search_single_engine(SEARCH_TERM, engine, session)
    assert len(results) == MAX_RESULTS_PER_ENGINE


async def test_search_single_engine_handles_failure():
    """Engine exceptions are caught and an empty list is returned."""
    engine = FailingEngine()
    session = MagicMock()
    results = await search_single_engine(SEARCH_TERM, engine, session)
    assert results == []
# ---------------------------------------------------------------------------
# Tests for print_engine_results
# ---------------------------------------------------------------------------

def test_print_engine_results_outputs_links(capsys):
    """print_engine_results writes results to stdout."""
    results = _make_results("DuckDuckGo", 3)
    print_engine_results("DuckDuckGo", results)
    out = capsys.readouterr().out
    assert "[DuckDuckGo]" in out
    assert "Result 1" in out
    assert "https://example.com/duckduckgo/3" in out


def test_print_engine_results_no_results(capsys):
    """Empty results prints 'No results found'."""
    print_engine_results("StartPage", [])
    out = capsys.readouterr().out
    assert "No results found" in out
# ---------------------------------------------------------------------------
# Tests for run_search_pipeline (integration with mocked engines)
# ---------------------------------------------------------------------------
async def test_pipeline_sequential_order(capsys):
    """DDG results are printed before StartPage results."""
    ddg = FakeEngine("DuckDuckGo", result_count=2)
    sp = FakeEngine("StartPage", result_count=2)

    await run_search_pipeline(SEARCH_TERM, engines=[ddg, sp])

    out = capsys.readouterr().out
    ddg_pos = out.index("[DuckDuckGo]")
    sp_pos = out.index("[StartPage]")
    assert ddg_pos < sp_pos, "DuckDuckGo results must appear before StartPage"


async def test_pipeline_passes_query_to_engines():
    """The query string reaches each engine unchanged."""
    ddg = FakeEngine("DuckDuckGo")
    sp = FakeEngine("StartPage")

    await run_search_pipeline(SEARCH_TERM, engines=[ddg, sp])

    assert ddg.last_query == SEARCH_TERM
    assert sp.last_query == SEARCH_TERM


async def test_pipeline_caps_results_per_engine(capsys):
    """Each engine's output is capped at 20 results."""
    ddg = FakeEngine("DuckDuckGo", result_count=25)
    sp = FakeEngine("StartPage", result_count=25)

    await run_search_pipeline(SEARCH_TERM, engines=[ddg, sp])

    out = capsys.readouterr().out
    # Each engine section should show exactly 20
    assert out.count("Found 20 results") == 2


async def test_pipeline_resilient_to_one_engine_failing(capsys):
    """If one engine fails, the other still produces output."""
    failing = FailingEngine()
    good = FakeEngine("StartPage", result_count=3)

    await run_search_pipeline(SEARCH_TERM, engines=[failing, good])

    out = capsys.readouterr().out
    assert "[StartPage]" in out
    assert "Result 1" in out
# ---------------------------------------------------------------------------
# Tests for engine classes (unit-level, mocked HTTP)
# ---------------------------------------------------------------------------
async def test_duckduckgo_search_parses_html():
    """DuckDuckGoSearch.search parses result divs correctly."""
    html = """
    <html><body>
    <div class="result">
        <a class="result__a" href="https://example.com/1">Chicken Recipe 1</a>
        <a class="result__snippet">A great chicken recipe</a>
    </div>
    <div class="result">
        <a class="result__a" href="https://example.com/2">Chicken Recipe 2</a>
    </div>
    </body></html>
    """
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value=html)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.post = MagicMock(return_value=mock_response)

    engine = DuckDuckGoSearch()
    results = await engine.search(SEARCH_TERM, session)

    assert len(results) == 2
    assert results[0]["title"] == "Chicken Recipe 1"
    assert results[0]["url"] == "https://example.com/1"
    assert results[0]["snippet"] == "A great chicken recipe"
    assert results[1]["snippet"] == ""


async def test_startpage_search_parses_html():
    """StartPageSearch.search parses result divs correctly."""
    html = """
    <html><body>
    <div class="w-gl__result">
        <a class="w-gl__result-title" href="https://example.com/sp/1">SP Chicken 1</a>
        <a class="w-gl__result-url" href="https://example.com/sp/1">example.com</a>
        <p class="w-gl__description">StartPage snippet</p>
    </div>
    </body></html>
    """
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value=html)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.get = MagicMock(return_value=mock_response)

    engine = StartPageSearch()
    results = await engine.search(SEARCH_TERM, session)

    assert len(results) == 1
    assert results[0]["title"] == "SP Chicken 1"
    assert results[0]["url"] == "https://example.com/sp/1"
    assert results[0]["snippet"] == "StartPage snippet"
