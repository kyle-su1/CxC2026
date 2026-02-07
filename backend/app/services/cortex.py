from app.core.snowflake import get_snowflake_session
from snowflake.cortex import Complete, Summarize
from typing import List, Optional

class CortexService:
    def __init__(self):
        self.session = get_snowflake_session()

    def analyze_sentiment(self, text: str, model: str = "mistral-large") -> str:
        """
        Uses Cortex Complete to analyze sentiment of the text.
        """
        prompt = f"""
        Analyze the sentiment of the following product review. 
        Return a single JSON object with:
        - sentiment_score (float between -1.0 and 1.0)
        - sentiment_label (positive, negative, neutral)
        - key_themes (list of strings)
        
        Review:
        {text}
        """
        return Complete(model, prompt, session=self.session)

    def summarize_reviews(self, reviews: List[str]) -> str:
        """
        Uses Cortex Summarize to aggregate multiple reviews.
        """
        combined_text = "\\n".join(reviews)
        # Note: Cortex Summarize takes text, not a list.
        return Summarize(combined_text, session=self.session)

    def search_similar_products(self, query_vector: List[float], limit: int = 5) -> List[dict]:
        """
        Searches for similar products using VECTOR_COSINE_SIMILARITY in Snowflake.
        Assumes a 'products' table exists with a 'vector' column.
        """
        # This is a placeholder for the actual SQL query execution using Snowpark
        # In a real app, you would define the DataFrame operations here.
        # Example:
        # df = self.session.table("products")
        # df = df.select("*", call_udf("VECTOR_COSINE_SIMILARITY", col("vector"), query_vector).alias("score"))
        # df = df.order_by(col("score").desc()).limit(limit)
        # return df.collect()
        pass

cortex_service = CortexService()
