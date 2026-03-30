import sqlite3
import json
import os
import re
import math
import numpy as np
import sys
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime

# Use the embedding client from the same directory
try:
    from embedding_client import EmbeddingClient
except ImportError:
    # Handle import if running from different location
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from embedding_client import EmbeddingClient

class VectorStore:
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        self.embedding_client = EmbeddingClient()

    def _init_db(self):
        cursor = self.conn.cursor()
        
        # Meta table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        # Files table to track changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                hash TEXT NOT NULL,
                mtime INTEGER NOT NULL
            );
        """)

        # Chunks table with embedding stored as JSON for portability
        # Updated to include start_line and end_line for OpenClaw alignment
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT, -- JSON array
                metadata TEXT, -- JSON object
                start_line INTEGER,
                end_line INTEGER,
                updated_at INTEGER NOT NULL
            );
        """)

        # Check if start_line/end_line columns exist (for migration)
        cursor.execute("PRAGMA table_info(chunks)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'start_line' not in columns:
            print("Migrating schema: Adding start_line/end_line columns...")
            cursor.execute("ALTER TABLE chunks ADD COLUMN start_line INTEGER")
            cursor.execute("ALTER TABLE chunks ADD COLUMN end_line INTEGER")

        # FTS5 table for keyword search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                content,
                content='chunks'
            );
        """)

        # Triggers to keep FTS in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid, content) VALUES (new.rowid, new.content);
            END;
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', old.rowid, old.content);
            END;
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES('delete', old.rowid, old.content);
                INSERT INTO chunks_fts(rowid, content) VALUES (new.rowid, new.content);
            END;
        """)

        self.conn.commit()

    def add_chunk(self, chunk_id: str, file_path: str, content: str, 
                  start_line: int, end_line: int,
                  metadata: Dict[str, Any] = None, updated_at: int = None):
        if metadata is None:
            metadata = {}
        
        # Generate embedding
        try:
            embedding = self.embedding_client.get_embedding(content)
            embedding_json = json.dumps(embedding)
        except Exception as e:
            print(f"Error generating embedding for chunk {chunk_id}: {e}")
            embedding_json = None

        cursor = self.conn.cursor()
        
        if updated_at is None:
            # Use current time
            cursor.execute("""
                INSERT OR REPLACE INTO chunks (id, file_path, content, embedding, metadata, start_line, end_line, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, strftime('%s', 'now'))
            """, (chunk_id, file_path, content, embedding_json, json.dumps(metadata), start_line, end_line))
        else:
            # Use provided time
            cursor.execute("""
                INSERT OR REPLACE INTO chunks (id, file_path, content, embedding, metadata, start_line, end_line, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (chunk_id, file_path, content, embedding_json, json.dumps(metadata), start_line, end_line, updated_at))
            
        self.conn.commit()

    def delete_file_chunks(self, file_path: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM chunks WHERE file_path = ?", (file_path,))
        self.conn.commit()

    def search_similar(self, query: str, limit: int = 5) -> Tuple[List[Dict[str, Any]], List[float]]:
        """
        Perform vector similarity search (cosine similarity).
        Returns results and query_embedding.
        """
        query_embedding = self.embedding_client.get_embedding(query)
        if not query_embedding:
            return [], []
        
        query_vec = np.array(query_embedding)
        norm_query = np.linalg.norm(query_vec)

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, file_path, content, embedding, metadata, start_line, end_line, updated_at FROM chunks WHERE embedding IS NOT NULL")
        rows = cursor.fetchall()

        results = []
        for row in rows:
            chunk_embedding = np.array(json.loads(row['embedding']))
            norm_chunk = np.linalg.norm(chunk_embedding)
            
            if norm_query == 0 or norm_chunk == 0:
                similarity = 0.0
            else:
                similarity = float(np.dot(query_vec, chunk_embedding) / (norm_query * norm_chunk))
            
            results.append({
                'id': row['id'],
                'file_path': row['file_path'],
                'content': row['content'],
                'metadata': json.loads(row['metadata']),
                'start_line': row['start_line'],
                'end_line': row['end_line'],
                'score': similarity,
                'updated_at': row['updated_at'],
                'embedding': chunk_embedding # Store as numpy array for MMR
            })
        
        # Sort by similarity desc
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit], query_embedding

    def search_keyword(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform keyword search using FTS5.
        Returns results with normalized BM25 score.
        """
        cursor = self.conn.cursor()
        # FTS5 match query
        cursor.execute("""
            SELECT c.id, c.file_path, c.content, c.embedding, c.metadata, c.start_line, c.end_line, c.updated_at, chunks_fts.rank
            FROM chunks_fts 
            JOIN chunks c ON chunks_fts.rowid = c.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            rank = row['rank']
            # Normalize BM25 rank to score: 1 / (1 + rank)
            # FTS5 rank is lower is better.
            score = 1.0 / (1.0 + rank) if rank >= 0 else 0.0
            
            embedding_json = row['embedding']
            embedding = np.array(json.loads(embedding_json)) if embedding_json else None

            results.append({
                'id': row['id'],
                'file_path': row['file_path'],
                'content': row['content'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                'start_line': row['start_line'],
                'end_line': row['end_line'],
                'score': score,
                'updated_at': row['updated_at'],
                'embedding': embedding
            })
        return results

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        if vec1 is None or vec2 is None:
            return 0.0
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def _mmr_rerank(self, items: List[Dict[str, Any]], lambda_param: float = 0.7) -> List[Dict[str, Any]]:
        """
        Maximal Marginal Relevance (MMR) re-ranking using Vector Similarity.
        """
        if not items or lambda_param >= 1.0:
            return sorted(items, key=lambda x: x['score'], reverse=True)

        selected = []
        remaining = items[:]
        
        while remaining:
            best_score = -float('inf')
            best_item = None
            
            for item in remaining:
                relevance = item['score']
                max_sim = 0.0
                
                # Calculate max similarity with already selected items
                item_vec = item.get('embedding')
                if item_vec is not None:
                    for sel in selected:
                        sel_vec = sel.get('embedding')
                        sim = self._cosine_similarity(item_vec, sel_vec)
                        if sim > max_sim:
                            max_sim = sim
                else:
                    pass

                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_item = item
            
            if best_item:
                selected.append(best_item)
                remaining.remove(best_item)
            else:
                break
                
        return selected

    def _is_evergreen(self, file_path: str) -> bool:
        """
        Check if file is 'Evergreen' (not decaying).
        Based on OpenClaw logic: MEMORY.md, or not matching YYYY-MM-DD.md pattern in memory/
        """
        normalized = file_path.replace("\\", "/").lstrip("./")
        if normalized in ["MEMORY.md", "memory.md"]:
            return True
        if not normalized.startswith("memory/"):
            return False
        
        # Check for YYYY-MM-DD.md pattern
        match = re.search(r'(?:^|/)(\d{4})-(\d{2})-(\d{2})\.md$', normalized)
        return match is None

    def _parse_date_from_path(self, file_path: str) -> Optional[datetime]:
        """Parse date from YYYY-MM-DD.md filename."""
        normalized = file_path.replace("\\", "/").lstrip("./")
        match = re.search(r'(?:^|/)(\d{4})-(\d{2})-(\d{2})\.md$', normalized)
        if match:
            try:
                year, month, day = map(int, match.groups())
                return datetime(year, month, day)
            except ValueError:
                return None
        return None

    def _calculate_decay(self, updated_at_ts: int, file_path: str, half_life_days: float = 30.0) -> float:
        if not half_life_days or half_life_days <= 0:
            return 1.0
        
        # Evergreen check
        if self._is_evergreen(file_path):
            return 1.0
            
        now = datetime.utcnow().timestamp()
        
        # Try to get age from filename date first (OpenClaw behavior)
        file_date = self._parse_date_from_path(file_path)
        if file_date:
            age_seconds = max(0, now - file_date.timestamp())
        else:
            # Fallback to updated_at_ts (mtime)
            age_seconds = max(0, now - updated_at_ts)
            
        age_days = age_seconds / (24 * 3600)
        
        decay_lambda = math.log(2) / half_life_days
        return math.exp(-decay_lambda * age_days)

    def hybrid_search(self, query: str, limit: int = 5, 
                      vector_weight: float = 0.7, 
                      text_weight: float = 0.3,
                      mmr_enabled: bool = False,
                      mmr_lambda: float = 0.7,
                      decay_enabled: bool = False,
                      decay_days: float = 30.0) -> List[Dict[str, Any]]:
        """
        Perform Weighted Hybrid Search with optional MMR and Temporal Decay.
        """
        candidate_limit = limit * 2 if mmr_enabled else limit
        
        # 1. Vector Search
        vec_results, _ = self.search_similar(query, limit=candidate_limit)
        
        # 2. Keyword Search
        kw_results = self.search_keyword(query, limit=candidate_limit)
        
        # 3. Merge Results
        all_items = {}
        
        # Process Vector Results
        for item in vec_results:
            doc_id = item['id']
            item['vector_score'] = item['score']
            item['text_score'] = 0.0
            all_items[doc_id] = item

        # Process Keyword Results
        for item in kw_results:
            doc_id = item['id']
            if doc_id in all_items:
                all_items[doc_id]['text_score'] = item['score']
                if all_items[doc_id].get('embedding') is None and item.get('embedding') is not None:
                    all_items[doc_id]['embedding'] = item['embedding']
            else:
                item['vector_score'] = 0.0
                item['text_score'] = item['score']
                all_items[doc_id] = item
        
        # Calculate Weighted Score
        merged_results = []
        for item in all_items.values():
            # Weighted Sum
            raw_score = (item['vector_score'] * vector_weight) + (item['text_score'] * text_weight)
            item['score'] = raw_score
            
            # Apply Temporal Decay
            if decay_enabled:
                file_path = item.get('file_path', '')
                updated_at = item.get('updated_at', 0)
                decay = self._calculate_decay(updated_at, file_path, decay_days)
                item['score'] *= decay
                item['decay_factor'] = decay

            merged_results.append(item)
            
        # Sort by score descending
        merged_results.sort(key=lambda x: x['score'], reverse=True)
        
        # 4. Apply MMR if enabled
        if mmr_enabled:
            merged_results = self._mmr_rerank(merged_results, mmr_lambda)
            
        return merged_results[:limit]

if __name__ == "__main__":
    # Test
    db_path = os.environ.get("HKT_MEMORY_DB", "memory.db")
    store = VectorStore(db_path)
    
    # Add some dummy data
    store.add_chunk("1", "memory/test.md", "This is a test document about apples.", 1, 1, {"category": "fruit"})
    store.add_chunk("2", "memory/test.md", "This is a test document about oranges.", 2, 2, {"category": "fruit"})
    store.add_chunk("3", "memory/test.md", "I like to code in Python.", 3, 3, {"category": "coding"})

    print("Searching for 'fruit'...")
    results = store.hybrid_search("fruit", limit=2, mmr_enabled=True)
    for res in results:
        print(f"ID: {res['id']}, Path: {res['file_path']}, Lines: {res['start_line']}-{res['end_line']}, Score: {res['score']:.4f}, Content: {res['content']}")

    print("\nSearching for 'python'...")
    results = store.hybrid_search("python", limit=2)
    for res in results:
        print(f"ID: {res['id']}, Path: {res['file_path']}, Lines: {res['start_line']}-{res['end_line']}, Score: {res['score']:.4f}, Content: {res['content']}")
