import os
import requests
from typing import List
from backend.app.schemas.types import ProductQuery, PriceOffer


SERPAPI_URL = "https://serpapi.com/search.json"


def get_shopping_offers(product: ProductQuery, trace: list) -> List[PriceOffer]:
    api_key = os.getenv("SERPAPI_API_KEY")

    if not api_key:
        trace.append({"step": "serpapi", "detail": "Missing API key"})
        return []

    params = {
        "engine": "google_shopping",
        "q": product.canonical_name,
        "gl": "ca",
        "hl": "en",
        "location": "Canada",
        "api_key": api_key,
    }

    r = requests.get(SERPAPI_URL, params=params, timeout=10)
    data = r.json()

    offers = []

    for item in data.get("shopping_results", []):
        price_str = item.get("price", "").replace("$", "").replace(",", "")
        try:
            price_cents = int(float(price_str) * 100)
        except:
            continue

        offers.append(
            PriceOffer(
                vendor=item.get("source", "Unknown"),
                price_cents=price_cents,
                currency="CAD",
                url=item.get("link"),
            )
        )

    trace.append({"step": "serpapi", "detail": f"Found {len(offers)} offers"})
    return offers
