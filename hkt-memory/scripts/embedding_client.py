import os
import sys
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

import time

class EmbeddingClient:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.base_url = os.environ.get("OPENAI_BASE_URL")
        self.model = os.environ.get("HKT_MEMORY_MODEL", "all-MiniLM-L6-v2")
        self.force_local = os.environ.get("HKT_MEMORY_FORCE_LOCAL", "false").lower() == "true"
        
        self.client = None
        self.local_model = None

        if not self.force_local and self.api_key and OpenAI:
            print(f"Initializing OpenAI compatible client with model: {self.model}")
            # Increase timeout to 30 seconds
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=30.0)
        else:
            if not SentenceTransformer:
                print("Warning: sentence-transformers not installed. Install with `pip install sentence-transformers`")
            else:
                print(f"Initializing local model: {self.model}")
                self.local_model = SentenceTransformer(self.model)

    def get_embedding(self, text: str) -> List[float]:
        if self.client:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Zhipu AI / OpenAI compatible
                    response = self.client.embeddings.create(
                        input=text,
                        model=self.model
                    )
                    return response.data[0].embedding
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Error calling embedding API (attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                        time.sleep(1 * (attempt + 1))
                    else:
                        print(f"Error calling embedding API: {e}")
                        # Fallback to local if available? For now just raise or return empty
                        raise e
        elif self.local_model:
            return self.local_model.encode(text).tolist()
        else:
            raise RuntimeError("No embedding provider available. Check your configuration.")

if __name__ == "__main__":
    # Simple CLI test
    client = EmbeddingClient()
    test_text = "This is a test sentence for embedding."
    try:
        embedding = client.get_embedding(test_text)
        print(f"Successfully generated embedding for '{test_text}'")
        print(f"Dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"Failed to generate embedding: {e}")
