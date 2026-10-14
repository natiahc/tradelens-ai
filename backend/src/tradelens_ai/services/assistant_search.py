"""Optional real web search for owner-authenticated TradeLens chat.

Only the server-selected Brave Search endpoint is contacted. No caller URLs
are fetched, and API keys stay on Render. Result links are untrusted content.
"""

import os
import re
from urllib.parse import quote_plus, urlsplit

import httpx


def requests_search(message: str) -> bool:
    return bool(re.search(
        r"(?i)(?:\bsearch(?:\s+(?:the\s+)?web|\s+online|\s+for|\s+about|\s+internet)?\b|"
        r"\bbrowse\b|\bgoogle\b|\blook\s*up\b|\bfind\s+online\b|"
        r"\blatest\s+(?:news|price|updates?|information|research)\b|"
        r"\b(?:today'?s|current|recent)\s+(?:news|price|market|events|updates)\b)", message
    ))


def search_web(question: str) -> dict:
    """Return sources (when configured) or an honest external-search fallback."""
    query = question.strip()[:450]
    if not query:
        raise ValueError("Search query must not be empty")
    fallback = "https://search.brave.com/search?q=" + quote_plus(query)
    key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if not key:
        return {
            "configured": False, "results": [],
            "external_url": fallback,
            "message": "Web search isn't connected to this Render backend. "
                       "Open the external search link instead. No results were fetched.",
        }

    try:
        with httpx.Client(timeout=9, follow_redirects=False) as client:
            response = client.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"Accept": "application/json", "X-Subscription-Token": key},
                params={"q": query, "count": 5, "country": "IN", "search_lang": "en"},
            )
            response.raise_for_status()
        raw = response.json().get("web", {}).get("results", [])
        results = []
        for item in raw:
            link = str(item.get("url") or "").strip()
            parsed = urlsplit(link)
            if parsed.scheme not in {"https", "http"} or not parsed.hostname:
                continue
            results.append({
                "title": str(item.get("title") or parsed.hostname)[:160],
                "url": link[:1000],
                "description": re.sub("<[^>]*>", "", str(item.get("description") or ""))[:360],
            })
            if len(results) == 5:
                break
        return {
            "configured": True,
            "results": results,
            "external_url": fallback,
            "message": ("Retrieved " + str(len(results)) + " web search result(s).")
                       if results else "No relevant web results were returned.",
        }
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        return {
            "configured": True, "results": [],
            "external_url": fallback,
            "message": "The connected search service is unavailable. "
                       "Use the external link to search manually.",
        }
