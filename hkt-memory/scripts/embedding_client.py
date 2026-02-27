import os
import sys
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# We'll import sentence_transformers only when needed to avoid import errors on architecture mismatch
# unless it's actually used.
SentenceTransformer = None

import time
import math

class EmbeddingClient:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.base_url = os.environ.get("OPENAI_BASE_URL")
        self.model = os.environ.get("HKT_MEMORY_MODEL", "all-MiniLM-L6-v2")
        self.force_local = os.environ.get("HKT_MEMORY_FORCE_LOCAL", "false").lower() == "true"
        self.mock_mode = os.environ.get("HKT_MEMORY_MOCK", "false").lower() == "true"
        
        self.client = None
        self.local_model = None

        if self.mock_mode:
            print("Using Mock Embedding Provider (for testing/verification)")
        elif not self.force_local and self.api_key and OpenAI:
            print(f"Initializing OpenAI compatible client with model: {self.model}")
            # Increase timeout to 30 seconds
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=30.0)
        else:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Initializing local model: {self.model}")
                self.local_model = SentenceTransformer(self.model)
            except ImportError:
                print("Warning: sentence-transformers not installed. Install with `pip install sentence-transformers`")
            except Exception as e:
                print(f"Warning: Failed to load sentence-transformers: {e}")

    def get_embedding(self, text: str) -> List[float]:
        if self.mock_mode:
            # Deterministic mock embedding based on text hash
            import hashlib
            h = hashlib.sha256(text.encode('utf-8')).digest()
            # Return 384 dimensions (standard for small models)
            vec = []
            for i in range(384):
                # Use bytes to generate float between -1 and 1
                b = h[i % 32]
                val = (b / 128.0) - 1.0
                # Add some variation based on index
                val += math.sin(i) * 0.1
                vec.append(val)
            return vec

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
