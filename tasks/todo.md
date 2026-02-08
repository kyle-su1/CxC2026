# Node 6 (Chat) Implementation Tasks

# Plan: Connect Real Data (Images/Prices) to Frontend

## User Objective
Ensure actual product images and prices are displayed, even if Google Shopping (SerpAPI) fails. Use Tavily as a secondary source for images and web scraping for data.

## 1. Upgrade Tavily Client
- [x] **Modify `backend/app/sources/tavily_client.py`**:
    - [x] Update `search_market_context` payload to include `"include_images": True`.
    - [x] Extract `image_url` from Tavily results.
    - [x] Return this data in the result dictionary.

## 2. Upgrade Market Scout Node
- [x] **Modify `backend/app/agent/nodes/market_scout.py`**:
    - [x] In `node_market_scout`, strictly preserve `image_url` from Tavily results during the candidate extraction phase.
    - [x] In `enrich_candidate`:
        - [x] If SerpAPI (`get_shopping_offers`) returns data, use it (Best Quality).
        - [x] If SerpAPI fails:
            - [x] Fallback to the `image_url` found by Tavily.
            - [x] If Tavily image is missing, ONLY THEN use the placeholder.
            - [x] For Price: Attempt to extract price from Tavily snippet using Regex/LLM, or fallback to "Check Price".
            - [x] For Link: Use the URL from the Tavily result (which is a real page) instead of a generic Google Search link.

## 3. Verification
- [x] **Test Script**:
    - [x] Run `scripts/test_market_scout_real.py`.
    - [x] Verify output contains real image URLs (not placeholders).
    - [x] Verify output contains real links (not just google search).

## 4. Security & Cleanup
- [x] Check for exposed API keys in logs.
- [x] Ensure valid JSON responses.

# Review
## Summary of Changes
1.  **Tavily Client Upgrade**: Modified `backend/app/sources/tavily_client.py` to request images (`include_images=True`) and return them.
2.  **Market Scout Robustness**: Modified `backend/app/agent/nodes/market_scout.py` to:
    -   Collect these Tavily images as a fallback pool.
    -   Use them if SerpAPI fails to find a product image.
    -   Use Tavily result URLs as fallback purchase links if SerpAPI fails.
    -   Generate a Google Shopping search link as a last resort.
3.  **Result**: The frontend will now always display an image and a working link for every alternative product, eliminating broken UI cards.

## Security Check
-   No API keys are hardcoded; all use `settings.*`.
-   No sensitive data is logged to console (only debug info).
-   Fallbacks use standard, safe URLs (Google Shopping).

# Task: Connect Main Product & Verdict to Frontend

- [x] **Data Alignment in `analysis.py`** <!-- id: 13 -->
    - [x] Update `process_candidate` to return BOTH `image`/`image_url` and `link`/`purchase_link` (Hybrid compatibility).
    - [x] Construct `active_product` structure in `analysis_object` using the winner `display_product`.
    - [x] Construct `price_analysis` with `verdict` ("Great Deal", "Fair Price", etc.) based on score/price.
    - [x] Ensure `price_text` is passed to `active_product`.
- [x] **Verification** <!-- id: 14 -->
    - [x] Run `test_analysis_node.py` (or create a new specific test) to verify JSON structure.

# Review
## Summary of Changes - Main Product & Verdict
1.  **Analysis Node Upgrade**: Modified `backend/app/agent/nodes/analysis.py` to:
    -   Return `active_product` with `image_url`, `purchase_link`, `price_text`.
    -   Return `price_analysis` with `verdict` based on market average comparison.
    -   Ensure alternatives have hybrid keys for compatibility.
2.  **Result**: Main product card should now display correctly with image, link, and price verdict.

# Task: Logging & Main Product Fixes

- [x] **Implement Price Logging** <!-- id: 15 -->
    - [x] Modify `market_scout.py` and `research.py` to append found prices (Item, Price, Vendor, URL) to `logs/price_debug.log`.
- [x] **Fix Main Product Data** <!-- id: 16 -->
    - [x] Update `backend/app/schemas/types.py` to add `thumbnail: Optional[str] = None` to `PriceOffer`.
    - [x] Update `backend/app/sources/serpapi_client.py` to extract `thumbnail` from API response.
    - [x] Investigate `research.py` (Node 2) to see why `image_url` and `price` are missing.
    - [x] Implement fallback logic for Main Product (similar to Alternatives) if primary search fails.
    - [x] Ensure `analysis.py` correctly maps Main Product data from `research_data`.

