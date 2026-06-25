import logging

from app.backend.config import settings

logger = logging.getLogger(__name__)


async def search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
    except Exception as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
        return []


async def search_wikipedia(query: str, max_results: int = 5) -> list[dict]:
    try:
        import wikipediaapi

        user_agent = "QwenDesktop/1.0"
        api = wikipediaapi.Wikipedia(
            language="en",
            user_agent=user_agent,
        )
        page = api.page(query)
        if not page.exists():
            return []
        results = [{"title": page.title, "url": page.fullurl, "snippet": page.summary[:500]}]
        return results
    except Exception as exc:
        logger.warning("Wikipedia search failed: %s", exc)
        return []


async def search(query: str, max_results: int = 5) -> list[dict]:
    provider = settings.search_provider
    if provider == "wikipedia":
        return await search_wikipedia(query, max_results)
    return await search_duckduckgo(query, max_results)
