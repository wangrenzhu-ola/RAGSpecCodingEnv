import os
import sys
import time
import math
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# We'll import sentence_transformers only when needed to avoid import errors on architecture mismatch
# unless it's actually used.
SentenceTransformer = None

class EmbeddingClient:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.base_url = os.environ.get("OPENAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
        self.model = os.environ.get("HKT_MEMORY_MODEL", "embedding-3")
        self.force_local = os.environ.get("HKT_MEMORY_FORCE_LOCAL", "false").lower() == "true"
        self.mock_mode = os.environ.get("HKT_MEMORY_MOCK", "false").lower() == "true"
        
        self.client = None
        self.local_model = None

        if self.mock_mode:
            print("Using Mock Embedding Provider (for testing/verification)")
        elif not self.force_local and self.api_key and OpenAI:
            # Check if it looks like a Zhipu key (contains dot)
            if "bigmodel.cn" in self.base_url and "." not in self.api_key:
                 print("Warning: OPENAI_API_KEY format seems invalid for Zhipu AI (expected id.secret)")

            print(f"Initializing OpenAI compatible client with model: {self.model}")
            print(f"  Base URL: {self.base_url}")
            # Increase timeout to 30 seconds
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=30.0)
        else:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Initializing local model: {self.model} (Fallback)")
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
            # Or 2048 for embedding-3 if needed (Zhipu embedding-3 is 2048)
            vec = []
            dim = 2048 if self.model == "embedding-3" else 384
            for i in range(dim):
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
                        # If API fails, maybe try local fallback if available?
                        if self.local_model:
                            print("Falling back to local model...")
                            return self.local_model.encode(text).tolist()
                        raise e
        elif self.local_model:
            return self.local_model.encode(text).tolist()
        else:
            raise RuntimeError("No embedding provider available. Check your configuration (OPENAI_API_KEY).")

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
