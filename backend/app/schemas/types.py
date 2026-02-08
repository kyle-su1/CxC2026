from typing import List, Optional, Dict
from pydantic import BaseModel


class ProductQuery(BaseModel):
    canonical_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    keywords: List[str] = []
    category: Optional[str] = None
    attributes: Dict[str, str] = {}
    region: str = "CA"


class ReviewSnippet(BaseModel):
    source: str
    url: str
    snippet: str
    date: Optional[str] = None
    sentiment: Optional[str] = None
    credibility_score: Optional[float] = None
    images: List[str] = []


class PriceOffer(BaseModel):
    vendor: str
    price_cents: int
    currency: str
    url: str
    shipping_cents: Optional[int] = None
    total_cents: Optional[int] = None
    in_stock: Optional[bool] = None
    source: str = "serpapi"
    thumbnail: Optional[str] = None


class SourceTrace(BaseModel):
    step: str
    detail: str


class ProductCandidate(BaseModel):
    name: str
    reason: str
    estimated_price: Optional[str] = None
    pros: List[str] = []
    cons: List[str] = []
    source_url: Optional[str] = None
