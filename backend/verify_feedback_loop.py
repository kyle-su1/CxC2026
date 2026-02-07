from app.services.snowflake_vector import snowflake_vector_service
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings

def verify_feedback(query="Ergonomic Chair"):
    print(f"Verifying Feedback Loop for '{query}'...")
    
    # 1. Embed query
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GOOGLE_API_KEY
    )
    query_vector = embeddings_model.embed_query(query)
    
    # 2. Search before feedback
    print("Pre-feedback Search...")
    results_pre = snowflake_vector_service.search_similar_products(query_vector, limit=5)
    print(f"Found {len(results_pre)} results.")
    
    # 3. Simulate Logic of Market Scout (upserting a new product)
    new_product = {
        "id": "ext_feedback_test_123",
        "name": "Test Ergonomic Chair 9000",
        "description": "A high-end ergonomic chair with lumbar support and feedback loop testing features. " * 5,
        "price": 599.99,
        "image_url": "http://example.com/chair.jpg",
        "source_url": "http://example.com"
    }
    
    # Add to DB
    print(f"Upserting simulated product: {new_product['name']}...", flush=True)
    text_to_embed = f"{new_product['name']} - {new_product['description']}"
    vector_new = embeddings_model.embed_query(text_to_embed)
    print("Vector generated.", flush=True)
    snowflake_vector_service.insert_product(new_product, vector_new)
    print("Product inserted.", flush=True)
    
    # 4. Search after feedback
    print("Post-feedback Search...")
    results_post = snowflake_vector_service.search_similar_products(query_vector, limit=5)
    
    found = False
    for res in results_post:
        print(f"- {res['name']} (Score: {res['score']:.4f})")
        if res['name'] == new_product['name']:
            found = True
            
    if found:
        print("SUCCESS! Feedback loop product found in search results.")
    else:
        print("FAILURE! Feedback loop product NOT found.")

if __name__ == "__main__":
    verify_feedback()
