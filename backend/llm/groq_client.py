from groq import Groq
from typing import List, Dict, Any
import os
import logging
from config.settings import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self):
        """
        Initialize Groq client with API key from settings.
        """
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=settings.groq_api_key)
        # Use a currently supported Groq model by default.
        self.model = "llama-3.1-8b-instant"
    
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate response using Groq LLM.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a facts-only mutual fund assistant. Answer using ONLY the provided context. Provide concise, source-backed responses without investment advice."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.1,  # Low temperature for factual responses
            )
            
            response = chat_completion.choices[0].message.content
            logger.info(f"Generated response of length: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response with Groq: {e}")
            raise
    
    def classify_query(self, query: str) -> Dict[str, Any]:
        """
        Classify user query into factual, advisory, or performance categories.
        """
        classification_prompt = f"""
        Classify the following query into one of these categories:
        1. "factual" - Objective questions about fund details (expense ratio, exit load, etc.)
        2. "advisory" - Questions seeking investment advice or recommendations
        3. "performance" - Questions about returns or performance data
        
        Query: "{query}"
        
        Respond with only the category name.
        """
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a query classifier. Respond with only the category name."
                    },
                    {
                        "role": "user",
                        "content": classification_prompt
                    }
                ],
                model=self.model,
                max_tokens=10,
                temperature=0.1,
            )
            
            category = chat_completion.choices[0].message.content.strip().lower()
            logger.info(f"Query classified as: {category}")
            
            # Validate category
            valid_categories = ["factual", "advisory", "performance"]
            if category not in valid_categories:
                logger.warning(f"Invalid category '{category}', defaulting to 'factual'")
                category = "factual"
            
            return {
                "category": category,
                "query": query,
                "confidence": 0.8  # Placeholder - could be enhanced
            }
            
        except Exception as e:
            logger.error(f"Error classifying query with Groq: {e}")
            return {"category": "factual", "query": query, "confidence": 0.0}
    
    def test_connection(self) -> bool:
        """
        Test Groq API connection.
        """
        try:
            test_response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": "test"}],
                model=self.model,
                max_tokens=5
            )
            logger.info("Groq API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Groq API connection test failed: {e}")
            return False

# Initialize global Groq client
groq_client = GroqClient()

if __name__ == "__main__":
    # Test the connection
    groq_client.test_connection()
