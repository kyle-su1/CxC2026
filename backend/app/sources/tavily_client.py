import requests
from typing import List, Dict
from app.schemas.types import ProductQuery, ReviewSnippet
from app.core.config import settings

TAVILY_URL = "https://api.tavily.com/search"


def find_review_snippets(product: ProductQuery, trace: list) -> List[ReviewSnippet]:
    api_key = settings.TAVILY_API_KEY

    if not api_key:
        trace.append({"step": "tavily", "detail": "Missing API key"})
        return []

    queries = [
        f"{product.canonical_name} review Canada",
        f"{product.canonical_name} review reddit Canada",
        f"site:reddit.com {product.canonical_name} worth it Canada",
    ]

    results = []

    for q in queries:
        payload = {
            "api_key": api_key,
            "query": q,
            "search_depth": "basic",
        }

        r = requests.post(TAVILY_URL, json=payload, timeout=10)
        data = r.json()
        
        if data.get("error"):
             trace.append({"step": "tavily", "detail": f"API Error: {data.get('error')}"})
             continue

        for item in data.get("results", []):
            url = item.get("url")
            if not url:
                continue
            results.append(
                ReviewSnippet(
                    source=item.get("title") or "",
                    url=url,
                    snippet=item.get("content") or "",
                )
            )

    trace.append({"step": "tavily", "detail": f"Found {len(results)} review snippets"})
    return results


def search_market_context(query: str) -> List[Dict[str, str]]:
    """
    Performs a general context search using Tavily.
    Used by Market Scout to find alternatives/competitors.
    """
    api_key = settings.TAVILY_API_KEY
    if not api_key:
        return []

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_answer": True, # Get Tavily's generated answer if possible
    }

    try:
        r = requests.post(TAVILY_URL, json=payload, timeout=10)
        data = r.json()
        
        if data.get("error"):
             return []

        results = []
        # Tavily sometimes returns an 'answer' block
        if data.get("answer"):
            results.append({"title": "Tavily AI Summary", "url": "", "content": data.get("answer")})

        for item in data.get("results", []):
             results.append({
                 "title": item.get("title", ""),
                 "url": item.get("url", ""),
                 "content": item.get("content", "")
             })
        
        return results
    except Exception as e:
        print(f"Tavily Market Search Error: {e}")
        return []
