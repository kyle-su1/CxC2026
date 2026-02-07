from typing import Dict, Any, List
from app.agent.state import AgentState
from app.sources.tavily_client import find_review_snippets
from app.schemas.types import ProductQuery

def node_market_scout(state: AgentState) -> Dict[str, Any]:
    """
    Node 2b: Market Scout (The "Explorer")
    
    Responsibilities:
    1. Analyze user preferences (or default to balanced).
    2. Generate search queries for finding ALTERNATIVE products.
    3. Search Tavily for "best X alternatives 2026" or "competitor to X".
    4. Parse results to identify 2-3 candidate product names.
    5. Enrich candidates with real-time prices, images, and purchase links.
    """
    print("--- 2b. Executing Market Scout Node (The Explorer) ---")
    log_file = "/app/debug_output.txt"
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{str(message)}\n")
        except Exception:
            pass

    log_debug("--- 2b. Executing Market Scout Node (The Explorer) ---")
    
    product_query_data = state.get('product_query', {})
    product_name = product_query_data.get('canonical_name') or product_query_data.get('product_name', '')
    user_prefs = state.get('user_preferences', {})
    search_criteria = state.get('search_criteria', {})  # From Chat Node (colors, brands, etc.)
    
    if not product_name or "Error" in product_name:
        return {"market_scout_data": {"error": "No valid product to scout"}}

    # 1. Determine Strategy based on Preferences
    # Default strategy: "Balanced" (find similar quality)
    search_modifiers = ["best alternative", "competitor"]
    
<<<<<<< Updated upstream
    # Adjust based on user preferences
=======
    # Use visual attributes if available for similarity
    visual_attrs = product_query_data.get('visual_attributes', '')
    if visual_attrs:
        print(f"   [Scout] Using visual attributes: {visual_attrs}")
        
    # Simple heuristic for demo
>>>>>>> Stashed changes
    if user_prefs.get('price_sensitivity', 0) > 0.7:
        search_modifiers = ["cheaper alternative", "best budget alternative"]
    elif user_prefs.get('quality', 0) > 0.7:
        search_modifiers = ["premium alternative", "better than"]
    
<<<<<<< Updated upstream
    # 1b. Incorporate search_criteria from Chat Node (Feedback Loop)
    # These come from user requests like "I hate red" or "show me Nike"
    color_filter = ""
    brand_filter = ""
    style_filter = ""
    
    if search_criteria:
        print(f"   [Scout] Applying search_criteria from Chat: {search_criteria}")
        
        # Handle color exclusions
        exclude_colors = search_criteria.get('exclude_colors', [])
        prefer_colors = search_criteria.get('prefer_colors', [])
        if prefer_colors:
            color_filter = " " + " ".join(prefer_colors)
        
        # Handle brand preferences
        prefer_brands = search_criteria.get('prefer_brands', [])
        exclude_brands = search_criteria.get('exclude_brands', [])
        if prefer_brands:
            brand_filter = " " + " ".join(prefer_brands)
        
        # Handle style keywords
        style_keywords = search_criteria.get('style_keywords', [])
        if style_keywords:
            style_filter = " " + " ".join(style_keywords)

    # 2. Construct Queries with filters applied
    queries = [
        f"{modifier} to {product_name}{color_filter}{brand_filter}{style_filter} 2026 reddit" 
        for modifier in search_modifiers
    ]
    # Add a general one
    queries.append(f"{product_name} vs competition 2026")
=======
    # 2. Construct Queries
    queries = []
    if visual_attrs:
         queries.append(f"{search_modifiers[0]} to {product_name} {visual_attrs} 2026")
         queries.append(f"similar {visual_attrs} like {product_name}")
    else:     
         queries = [
             f"{modifier} to {product_name} 2026 reddit" 
             for modifier in search_modifiers
         ]
         queries.append(f"{product_name} vs competition 2026")
>>>>>>> Stashed changes

    print(f"   [Scout] Strategy: {search_modifiers[0]} | Queries: {queries}")
    
    import time
    start_time = time.time()
    
    # 3. Execute Search
    print(f"   [Scout] Executing search for alternatives...")
    from app.sources.tavily_client import search_market_context
    
    scout_results = []
    # Use parallel execution for search queries to speed up
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_query = {executor.submit(search_market_context, q): q for q in queries[:2]} # Limit to 2 queries
        for future in as_completed(future_to_query):
            try:
                # Add timeout to search
                results = future.result(timeout=10)
                scout_results.extend(results)
            except Exception:
                pass
                
    # Deduplicate results based on URL
    seen_urls = set()
    unique_results = []
    for r in scout_results:
        if r.get('url') and r.get('url') not in seen_urls:
            seen_urls.add(r.get('url'))
            unique_results.append(r)
    
    # 4. Extract Candidates using LLM
    print(f"   [Scout] Extracting candidates from {len(unique_results)} search results...")
    
    context_text = "\n".join([f"- {r.get('title')}: {r.get('content')}" for r in unique_results[:8]]) # Limit context
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    from app.core.config import settings
    import json
    
    llm = ChatGoogleGenerativeAI(model=settings.MODEL_REASONING, google_api_key=settings.GOOGLE_API_KEY, temperature=0.1)
    
    prompt = f"""You are a Market Scout. 
    Product: {product_name}
    Goal: Find 3 best {search_modifiers[0]} products.
    
    Search Context:
    {context_text}
    
    Return a Strict JSON List of objects with keys: "name", "reason".
    Example: [{{"name": "Competitor X", "reason": "Better battery life"}}]
    """
    
    candidates = []
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
             content = content.split('```')[1].split('```')[0]
             
        candidates = json.loads(content)
        if not isinstance(candidates, list):
            candidates = []

<<<<<<< Updated upstream
        from app.schemas.types import ProductCandidate
        
        # Define Output Structure for Gemini
        class CandidateList(BaseModel):
            items: List[ProductCandidate] = Field(description="List of alternative products found")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1
        )
        
        # Prepare context text from search results
        context_text = ""
        for res in scout_results[:5]: # Limit to top 5 results
            context_text += f"Source: {res.get('title')}\nContent: {res.get('content')}\n\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a market research assistant. Your goal is to identify alternative products based on search results."),
            ("human", "User Strategy: {strategy}\n\nSearch Results:\n{context}\n\nIdentify the top 3 alternative products mentioned. Return a list of candidates with fields: name, reason, estimated_price, pros, cons.")
        ])
        
        structured_llm = llm.with_structured_output(CandidateList)
        chain = prompt | structured_llm
        
        extraction_start = time.time()
        result = chain.invoke({"strategy": search_modifiers[0], "context": context_text})
        extraction_time = time.time() - extraction_start
        print(f"--- Scout Node: Candidate Extraction took {extraction_time:.2f}s ---")
        
        if result and result.items:
            # Convert Pydantic models to dicts for serialization
            candidates = [item.model_dump() for item in result.items]
            print(f"   [Scout] Successfully extracted {len(candidates)} candidates via Gemini.")

            # --- Vector Feedback Loop ---
            # Save these candidates back to Snowflake so we remember them for next time
            print("   [Scout] Feedback Loop: Upserting candidates to Snowflake...")
            try:
                vector_start = time.time()
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                from app.services.snowflake_vector import snowflake_vector_service
                
                # Initialize embedding model if not already (for the feedback loop)
                embeddings_feedback = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-001", 
                    google_api_key=settings.GOOGLE_API_KEY
                )
                
                for cand in candidates:
                    try:
                        c_name = cand.get('name')
                        c_desc = cand.get('reason', '') + " " + " ".join(cand.get('pros', []))
                        
                        # Generate ID deterministically from name
                        import hashlib
                        c_id = f"ext_{hashlib.md5(c_name.encode()).hexdigest()}"
                        
                        # Generate Vector
                        text_to_embed = f"{c_name} - {c_desc}"
                        vector = embeddings_feedback.embed_query(text_to_embed)
                        
                        # Prepare data
                        p_data = {
                            "id": c_id,
                            "name": c_name,
                            "description": c_desc,
                            "price": 0.0, # We might not have price yet, let enrichment fill it or update later
                            "image_url": "",
                            "source_url": ""
                        }
                        
                        # Insert
                        snowflake_vector_service.insert_product(p_data, vector)
                        print(f"       -> Saved {c_name} to Vector DB.")
                        
                    except Exception as inner_e:
                        print(f"       -> Failed to save {cand.get('name')}: {inner_e}")
                
                vector_time = time.time() - vector_start
                print(f"--- Scout Node: Vector Feedback took {vector_time:.2f}s ---")
                        
            except Exception as e:
                print(f"   [Scout] Feedback Loop Failed: {e}")
            # ---------------------------

            # 5. Enrich with Real-Time Prices and Reviews (Node 2a logic for alternatives)
            print("   [Scout] Fetching prices and reviews for candidates...")
            
            # --- Snowflake Vector Search Integration ---
            # Checks for similar products already in our database
            # Uses search_criteria to create a more targeted embedding query
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                from app.services.snowflake_vector import snowflake_vector_service
                
                print("   [Scout] Checking Snowflake Vector DB for known alternatives...")
                
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-001", 
                    google_api_key=settings.GOOGLE_API_KEY
                )
                
                # Build enhanced query with search_criteria from Chat Node
                enhanced_query = product_name
                if search_criteria:
                    criteria_parts = []
                    if search_criteria.get('prefer_colors'):
                        criteria_parts.append(" ".join(search_criteria['prefer_colors']))
                    if search_criteria.get('prefer_brands'):
                        criteria_parts.append(" ".join(search_criteria['prefer_brands']))
                    if search_criteria.get('style_keywords'):
                        criteria_parts.append(" ".join(search_criteria['style_keywords']))
                    if criteria_parts:
                        enhanced_query = f"{product_name} {' '.join(criteria_parts)}"
                        print(f"   [Scout] Enhanced vector query: '{enhanced_query}'")
                
                query_vector = embeddings.embed_query(enhanced_query)
                
                # Search Snowflake
                vector_results = snowflake_vector_service.search_similar_products(query_vector, limit=3)
                
                if vector_results:
                    print(f"   [Scout] Found {len(vector_results)} matches in Snowflake.")
                    for res in vector_results:
                        # Filter out results that match excluded colors/brands
                        res_name = res.get('name', '').lower()
                        exclude_colors = search_criteria.get('exclude_colors', [])
                        exclude_brands = search_criteria.get('exclude_brands', [])
                        
                        # Skip if product matches exclusions
                        if any(color.lower() in res_name for color in exclude_colors):
                            print(f"       -> Skipping {res.get('name')} (excluded color)")
                            continue
                        if any(brand.lower() in res_name for brand in exclude_brands):
                            print(f"       -> Skipping {res.get('name')} (excluded brand)")
                            continue
                        
                        # Convert to candidate format
                        cand = {
                            "name": res.get('name'),
                            "reason": "Found in internal database (High Similarity)",
                            "estimated_price": f"${res.get('price')} (Historical)",
                            "pros": ["Verified Product"],
                            "cons": [],
                            "source": "Snowflake Vector DB"
                        }
                        # Add to candidates if not duplicate
                        if not any(c.get('name') == cand['name'] for c in candidates):
                            candidates.append(cand)
            except Exception as e:
                print(f"   [Scout] Snowflake Vector Search skipped: {e}")
            
            # --- End Snowflake Integration ---

            enrich_start = time.time()
=======
        # 5. Enrich with Real-Time Prices, Images, and Reviews
        if candidates:
>>>>>>> Stashed changes
            try:
                from app.sources.serpapi_client import get_shopping_offers
                from app.sources.tavily_client import find_review_snippets
                from app.schemas.types import ProductQuery
                # ensure concurrent.futures is imported
                from concurrent.futures import ThreadPoolExecutor, as_completed

                def enrich_candidate(cand):
                    name = cand.get('name')
                    if not name:
                        return
                    
                    try:
                        temp_query = ProductQuery(canonical_name=name)
                        temp_trace = []
                        
                        # Get prices
                        price_offers = get_shopping_offers(temp_query, temp_trace)
                        cand['prices'] = [
                            {"vendor": p.vendor, "price": p.price_cents / 100, "currency": p.currency, "url": p.url}
                            for p in price_offers
                        ]
                        
                        if price_offers:
                            # Capture Image and Link from best offer
                            best_offer = price_offers[0] 
                            cand['image_url'] = getattr(best_offer, 'thumbnail', None)
                            cand['purchase_link'] = best_offer.url
                            
                            sorted_prices = sorted([p.price_cents for p in price_offers])
                            median_idx = len(sorted_prices) // 2
                            median_price = sorted_prices[median_idx] / 100
                            cand['estimated_price'] = f"${median_price:.2f} CAD"
                            cand['price_text'] = f"${median_price:.2f}"
                            print(f"       -> {name}: {len(price_offers)} prices found.")
                        else:
                            # Fallback: Create a direct Google Shopping search link
                            import urllib.parse
                            encoded_name = urllib.parse.quote(name)
                            cand['purchase_link'] = f"https://www.google.com/search?tbm=shop&q={encoded_name}"
                            cand['estimated_price'] = "Check Price"
                            cand['price_text'] = "Check Price"
                            print(f"       -> {name}: No direct offers, using fallback link.")

                        # Get reviews
                        review_snippets = find_review_snippets(temp_query, temp_trace)
                        cand['reviews'] = [
                            {"source": r.source, "snippet": r.snippet, "url": r.url}
                            for r in review_snippets
                        ]
                        print(f"       -> {name}: {len(review_snippets)} reviews found")
                        
                    except Exception as inner_e:
                        print(f"       -> Error enriching {name}: {inner_e}")

                # Run enrichment in parallel, limit to 3 to avoid API rate limits
                # Latency Optimization: Limit to top 3 candidates total to prevent massive fan-out
                candidates_to_process = candidates[:3]
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = [executor.submit(enrich_candidate, cand) for cand in candidates_to_process]
                    for future in as_completed(futures):
                        try:
                            future.result(timeout=15)
                        except Exception as exc:
                            print(f"   [Scout] Candidate enrichment failed: {exc}")
                    
            except Exception as e:
                print(f"       -> Enrichment setup failed: {e}")
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"   [Scout] LLM Extraction skipped or failed: {e}")
        # Fallback: just return empty candidates
        pass

    total_time = time.time() - start_time
    print(f"--- Market Scout Node: Total time {total_time:.2f}s ---")
    log_debug("Market Scout Node Completed")
    return {
        "market_scout_data": {
            "strategy": search_modifiers[0],
            "raw_search_results": unique_results,
            "candidates": candidates
        }
    }
