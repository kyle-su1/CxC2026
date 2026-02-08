from typing import Dict, Any, List
from app.agent.state import AgentState
from app.db.session import SessionLocal
from app.services.preference_service import get_learned_weights, merge_weights, save_choice, get_user_explicit_preferences
from app.agent.scoring import calculate_weighted_score
from app.agent.skeptic import SkepticAgent
from app.core.config import settings
import logging
import time

# Configure logging
logger = logging.getLogger(__name__)

def adjust_eco_score(raw_score: float, product_name: str) -> float:
    """
    Post-process eco score to ensure a wider range for demo purposes.
    Uses keyword detection to apply deterministic adjustments.
    """
    name_lower = product_name.lower()
    adjustment = 0.0
    
    # POSITIVE ADJUSTMENTS (eco-friendly indicators)
    if 'refurbished' in name_lower or 'renewed' in name_lower or 'certified pre-owned' in name_lower:
        adjustment += 0.25  # Major boost for extending product life
    if 'recycled' in name_lower or 'sustainable' in name_lower or 'eco' in name_lower:
        adjustment += 0.20
    if 'organic' in name_lower or 'bamboo' in name_lower or 'biodegradable' in name_lower:
        adjustment += 0.15
    if 'patagonia' in name_lower or 'allbirds' in name_lower or 'b corp' in name_lower:
        adjustment += 0.20  # Known sustainability leaders
    
    # NEGATIVE ADJUSTMENTS (poor eco indicators)
    if 'disposable' in name_lower or 'single-use' in name_lower or 'throwaway' in name_lower:
        adjustment -= 0.30
    if 'fast fashion' in name_lower or 'shein' in name_lower or 'temu' in name_lower:
        adjustment -= 0.25
    if 'plastic' in name_lower and 'recycled' not in name_lower:
        adjustment -= 0.10
    if 'cheap' in name_lower or 'budget' in name_lower:
        adjustment -= 0.05  # Slight penalty for assumed lower quality/lifespan
    
    # CATEGORY-BASED ADJUSTMENTS
    if any(x in name_lower for x in ['iphone', 'samsung galaxy', 'pixel', 'oneplus']):
        # Electronics - slight penalty for e-waste, but decent recycling programs
        if 'refurbished' not in name_lower and 'renewed' not in name_lower:
            adjustment -= 0.05
    
    # Apply adjustment and clamp to 0.0-1.0
    adjusted = raw_score + adjustment
    return max(0.05, min(0.95, adjusted))  # Never go to extremes 0 or 1


def sanitize_eco_notes(eco_notes: str, product_name: str, has_research_data: bool) -> str:
    """
    Strip out hallucinated certifications from eco_notes.
    If no research data was provided, replace any certification claims with generic text.
    """
    import re
    
    # List of certification keywords that LLMs love to hallucinate
    hallucination_patterns = [
        r'\bB\s*Corp\b',
        r'\bB-Corp\b', 
        r'\bNet\s*Zero\b',
        r'\bISO\s*\d+\b',
        r'\bcarbon\s*neutral\b',
        r'\bFSC\s*certified\b',
        r'\bEnergy\s*Star\b',
        r'\bEPEAT\b',
        r'\bGreen\s*Seal\b',
        r'\bCradle\s*to\s*Cradle\b',
        r'\bFair\s*Trade\b',
        r'\bRainforest\s*Alliance\b',
    ]
    
    if not has_research_data:
        # Check if any hallucination pattern exists
        for pattern in hallucination_patterns:
            if re.search(pattern, eco_notes, re.IGNORECASE):
                # Replace the entire eco_notes with a safe generic message
                name_lower = product_name.lower()
                if 'refurbished' in name_lower or 'renewed' in name_lower:
                    return "Refurbished product - extends device lifespan, reducing e-waste. Score based on product category."
                elif any(x in name_lower for x in ['iphone', 'samsung', 'pixel', 'phone']):
                    return "Electronics product. Score based on typical smartphone lifecycle and e-waste considerations."
                else:
                    return "No verified sustainability data found. Score based on product category."
    
    return eco_notes


def node_analysis_synthesis(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: Analysis & Synthesis (The "Brain")
    
    Responsibilities:
    1. Load user preferences (explicit + learned).
    2. Run Skeptic analysis on alternatives (if not done in Node 3).
    3. Calculate weighted scores for all products (Main + Alternatives).
    4. Rank products and generate final analysis.
    5. Save preference context (optional, happens on final choice usually, 
       but we can prep the data here).
    """
    print("--- 4. Executing Analysis Node (The Brain) ---")
    log_file = "/app/debug_output.txt"
    def log_debug(message):
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{str(message)}\n")
        except Exception:
            pass

    log_debug("--- 4. Executing Analysis Node (The Brain) ---")
    
    # Inputs
    research = state.get('research_data', {})
    risk = state.get('risk_report', {})
    market_scout = state.get('market_scout_data', {})
    market_scout = state.get('market_scout_data', {})
    
    # 1. Load User Preferences
    db = SessionLocal()
    final_weights = {}
    try:
        # Get explicit quals (from DB or State)
        state_prefs = state.get('user_preferences', {})
        
        # Determine User ID - try state, then session lookup, then default
        state_id = state.get('user_id')
        user_id = 1
        if state_id:
            try:
                user_id = int(state_id)
            except:
                pass

        db_prefs = get_user_explicit_preferences(db, user_id)
        
        # Merge explicit (State > DB)
        # If State has params, they override DB (e.g. current session tweaks)
        explicit_prefs = {**db_prefs, **state_prefs}
        
        # Get learned weights from past behavior
        learned_weights = get_learned_weights(db, user_id)
        
        # Merge everything
        final_weights = merge_weights(explicit_prefs, learned_weights)
        print(f"   [Analysis] Final Weights: {final_weights}")
        
    except Exception as e:
        print(f"   [Analysis] Error loading preferences: {e}")
        # Fallback
        state_prefs = state.get('user_preferences', {})
        final_weights = merge_weights(state_prefs, {})
        
    finally:
        db.close()
    print(f"   [Analysis] Final Weights (DB Skipped): {final_weights}")
        
    # 2. Analyze Alternatives (if available)
    alternatives = market_scout.get('candidates', [])
    
    # 2b. Add Main Product to analysis list
    # We construct a 'candidate-like' object for the main product to unify logic
    product_query = state.get('product_query', {})
    main_product_name = product_query.get('canonical_name') or product_query.get('product_name') or "Main Product"
    
    # Extract price for main product
    main_prices = research.get('competitor_prices', [])
    main_price_val = 0.0
    if main_prices:
         try:
             # competitor_prices from Node 2 structure: PriceOffer.dict()
             # PriceOffer uses 'price_cents' (integer in cents), NOT 'price'
             price_cents = main_prices[0].get('price_cents', 0)
             main_price_val = float(price_cents) / 100.0  # Convert cents to dollars
         except:
             pass
    
    # Extract reviews for main product
    main_reviews = research.get('reviews', [])

    # Try to find main product image/link from research prices or context
    main_image = None
    main_link = None
    if main_prices:
        main_image = main_prices[0].get('thumbnail') # SerpAPI often has this
        main_link = main_prices[0].get('url')

    # --- MAIN PRODUCT FALLBACKS ---
    # 1. Fallback Image from Reviews (if main has no image)
    if not main_image:
        # Check reviews for images
        for r in main_reviews:
            # r is a dict here (ReviewSnippet.dict())
            if r.get('images'):
                main_image = r['images'][0]
                print(f"   [Analysis] Used fallback image from reviews for Main Product.")
                break

    # 2. Main Price Text
    main_price_text = "Check Price"
    if main_price_val > 0:
        # Assuming CAD for now or extracting from first price offer
        curr = main_prices[0].get('currency', 'CAD') if main_prices else 'CAD'
        main_price_text = f"${main_price_val:.2f} {curr}"
    # ------------------------------

    if main_product_name:
        alternatives.append({
            "name": main_product_name,
            "reason": "Original Selection",
            "prices": [{"price": main_price_val}],
            "reviews": main_reviews,
            "is_main": True,
            "image_url": main_image,
            "purchase_link": main_link,
            "price_text": main_price_text
        })

    alternatives_scored = []
    
    # Get eco_context from research data
    eco_data = state.get('research_data', {}).get('eco_data', {})
    eco_context = eco_data.get('eco_context', '')
    if eco_context:
        print(f"   [Analysis] Eco data available ({len(eco_context)} chars)")
    
    print(f"   [Analysis] Scoring {len(alternatives)} candidates (including Main Product)...")
    log_debug(f"Scoring {len(alternatives)} candidates...")
    
    # Calculate Market Average Price across all candidates
    all_prices = []
    for alt in alternatives:
        prices_list = alt.get('prices', [])
        p_str = prices_list[0].get('price', 0) if prices_list else 0
        try:
            val = float(p_str)
            if val > 0:
                all_prices.append(val)
        except:
            pass
            
    market_avg = sum(all_prices) / len(all_prices) if all_prices else 0.0
    print(f"   [Analysis] Market Average Price: ${market_avg:.2f}")

    # --- BATCH OPTIMIZATION: Process all candidates in one (or two) LLM calls ---
    from app.agent.skeptic import SkepticAgent
    agent = SkepticAgent(model_name=settings.MODEL_ANALYSIS)
    
    # 1. Split Main Product and Alternatives
    main_candidate = next((a for a in alternatives if a.get('is_main')), None)
    other_candidates = [a for a in alternatives if not a.get('is_main')]
    
    # 2. Analyze Main Product (Detailed)
    # We use Node 3 risk report if available to avoid a third LLM call
    if main_candidate:
        print(f"   [Analysis] Processing Main Product: {main_candidate['name']}")
        main_reviews = main_candidate.get('reviews', [])[:5] # Limit to 5
        
        # Reuse Node 3 Risk Report if Trust Score is present
        if risk and 'trust_score' in risk:
             print(f"   [Analysis] ♻️ Reusing Risk Report from Node 3 for {main_candidate['name']}")
             # Map Risk Report to Sentiment Data
             main_sentiment = {
                 "summary": risk.get('summary', "Found through visual search."),
                 "trust_score": risk.get('trust_score', 7.0),
                 "sentiment_score": risk.get('sentiment_score', 0.5), # Default or extract
                 "eco_score": risk.get('eco_score', 0.5),
                 "eco_notes": risk.get('eco_notes', "Analysis based on product category."),
                 "verdict": risk.get('verdict', "Neutral assessment")
             }
        else:
             # Fallback: Individual analysis for main product
             from app.agent.skeptic import Review
             valid_reviews = []
             for r in main_reviews:
                 try:
                     valid_reviews.append(Review(source=r.get("source", "Unknown"), text=r.get("snippet", "") or r.get("text", ""), rating=r.get("rating"), date=r.get("date")))
                 except: pass
             
             sentiment_result = agent.analyze_reviews(main_candidate['name'], valid_reviews, eco_context)
             main_sentiment = sentiment_result.model_dump()
             
        # Create full candidate object for main product
        price = main_candidate.get('prices', [{}])[0].get('price', 0)
        score_obj = calculate_weighted_score(
            trust_score=main_sentiment.get('trust_score', 5.0),
            sentiment_score=main_sentiment.get('sentiment_score', 0.0),
            price_val=price,
            market_avg=market_avg, 
            weights=final_weights,
            eco_score=main_sentiment.get('eco_score', 0.5)
        )
        
        main_scored = {
            "name": main_candidate['name'],
            "score_details": score_obj.model_dump(),
            "sentiment_summary": main_sentiment.get('summary'),
            "reason": main_candidate.get('reason'),
            "image_url": main_candidate.get('image_url'),
            "purchase_link": main_candidate.get('purchase_link'),
            "is_main": True,
            "eco_score": adjust_eco_score(main_sentiment.get('eco_score', 0.5), main_candidate['name']),
            "eco_notes": sanitize_eco_notes(main_sentiment.get('eco_notes', ''), main_candidate['name'], bool(eco_context))
        }
        alternatives_scored.append(main_scored)

    # 3. Analyze Alternatives (BATCH)
    if other_candidates:
        print(f"   [Analysis] 🚀 Batch Analyzing {len(other_candidates)} alternatives...")
        batch_results = agent.batch_analyze_alternatives(other_candidates, eco_context)
        
        for i, alt in enumerate(other_candidates):
            try:
                # Use results from batch call (order matches)
                sentiment_data = batch_results[i].model_dump() if i < len(batch_results) else {}
                
                price = alt.get('prices', [{}])[0].get('price', 0)
                score_obj = calculate_weighted_score(
                    trust_score=sentiment_data.get('trust_score', 5.0),
                    sentiment_score=sentiment_data.get('sentiment_score', 0.0),
                    price_val=price,
                    market_avg=market_avg, 
                    weights=final_weights,
                    eco_score=sentiment_data.get('eco_score', 0.5)
                )
                
                # Boost if matched brand
                product_name_lower = alt.get('name', '').lower()
                preferred_brands = explicit_prefs.get('prefer_brands', [])
                for brand in preferred_brands:
                    if brand.lower() in product_name_lower:
                        score_obj.total_score += 50.0 
                        break

                alternatives_scored.append({
                    "name": alt.get('name'),
                    "score_details": score_obj.model_dump(),
                    "sentiment_summary": sentiment_data.get('summary'),
                    "reason": alt.get('reason'),
                    "image_url": alt.get('image_url'),
                    "purchase_link": alt.get('purchase_link'),
                    "is_main": False,
                    "eco_score": adjust_eco_score(sentiment_data.get('eco_score', 0.5), alt.get('name', '')),
                    "eco_notes": sanitize_eco_notes(sentiment_data.get('eco_notes', ''), alt.get('name', ''), bool(eco_context))
                })
            except Exception as e:
                print(f"   [Analysis] Error processing alternative {alt.get('name')}: {e}")

    start_time = time.time() # Just for reference in total time

    # Sort by Total Score (for alternatives ranking)
    alternatives_scored.sort(key=lambda x: x['score_details']['total_score'], reverse=True)
    
    # Find the main product (user's selected item) - this should always be the "recommended_product"
    main_product = next((a for a in alternatives_scored if a.get('is_main')), None)
    
    # Top score (could be main or alternative)
    top_pick = alternatives_scored[0] if alternatives_scored else None
    
    # Use main product as the recommended product, fall back to top_pick if no main found
    display_product = main_product if main_product else top_pick
    
    # 3. Construct Analysis Object
    
    # Determine Verdict
    verdict = "Fair Price"
    if display_product:
        price_val = display_product.get('price_val', 0)
        if price_val > 0 and market_avg > 0:
            if price_val < market_avg * 0.9:
                verdict = "Great Deal"
            elif price_val > market_avg * 1.1:
                verdict = "Premium Price"

    analysis_object = {
        "match_score": display_product['score_details']['total_score'] if display_product else 0.0,
        "recommended_product": display_product['name'] if display_product else "None",
        "scoring_breakdown": display_product['score_details'] if display_product else {},
        "identified_product": display_product['name'] if display_product else "Unknown",
        "summary": display_product.get('sentiment_summary') if display_product else "Analysis complete.",
        
        # ACTIVE PRODUCT (Main Card) - Ensure keys match DashboardPage.jsx expectations
        "active_product": {
            "name": display_product['name'] if display_product else "Unknown",
            "image_url": display_product.get('image_url') if display_product else None,
            "purchase_link": display_product.get('purchase_link') if display_product else None,
            "price_text": display_product.get('price_text') if display_product else "Check Price",
            "detected_objects": [], # Populated by Vision/Lens if available, kept empty here
            "eco_score": display_product.get('eco_score', 0.5) if display_product else 0.5,
            "eco_notes": display_product.get('eco_notes', '') if display_product else ""
        },
        
        # PRICE ANALYSIS (Verdict)
        "price_analysis": {
            "verdict": verdict,
            "market_average": f"${market_avg:.2f}",
            "price_difference": f"{((display_product.get('price_val', 0) - market_avg) / market_avg * 100):.0f}%" if display_product and market_avg > 0 else "0%"
        },
        
        # Flag if a better alternative exists
        "better_alternative_exists": top_pick and main_product and top_pick['name'] != main_product['name'],
        "best_alternative": top_pick['name'] if top_pick and main_product and top_pick['name'] != main_product['name'] else None,
        "alternatives_ranked": [
            {
                "name": a['name'], 
                "score": a['score_details']['total_score'],
                "reason": a['reason'],
                "image": a.get('image_url'), # Hybrid key
                "link": a.get('purchase_link'), # Hybrid key
                "price_text": a.get('price_text'),
                "eco_score": a.get('eco_score', 0.5),
                "eco_notes": a.get('eco_notes', '')
            } 
            for a in alternatives_scored if not a.get('is_main')  # Exclude main from alternatives list
        ],
        "alternatives": [ # DashboardPage.jsx uses 'alternatives' for the mapping, NOT 'alternatives_ranked'
            {
               "name": a['name'],
               "score": a['score_details']['total_score'],
               "score_breakdown": {
                   "price": round(a['score_details']['price_score'] * 100, 1),
                   "quality": round((a['score_details']['sentiment_score'] + 1) / 2 * 100, 1),  # -1 to 1 -> 0 to 100
                   "trust": round(a['score_details']['trust_score'] * 10, 1),  # 0-10 -> 0-100
                   "eco": round(a['score_details']['eco_score'] * 100, 1),  # 0-1 -> 0-100
               },
               "reason": a['reason'],
               "image": a.get('image_url'),
               "link": a.get('purchase_link'),
               "price_text": a.get('price_text'),
               "eco_score": a.get('eco_score', 0.5),
               "eco_notes": a.get('eco_notes', '')
            }
            for a in alternatives_scored if not a.get('is_main')
        ],
        "applied_preferences": final_weights
    }
    
    total_time = time.time() - start_time
    print(f"--- Analysis Node: Total time {total_time:.2f}s ---")
    log_debug("Analysis Node Completed")
    
    # Get existing timings and add this node's time
    existing_timings = state.get('node_timings', {}) or {}
    existing_timings['analysis'] = total_time
    
    return {
        "analysis_object": analysis_object, 
        "alternatives_analysis": alternatives_scored,
        "node_timings": existing_timings
    }
