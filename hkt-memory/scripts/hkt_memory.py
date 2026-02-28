import argparse
import os
import re
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add script directory to sys.path
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

try:
    from vector_store import VectorStore
except ImportError:
    VectorStore = None
    print("Warning: vector_store module not found. Vector search capabilities will be disabled.")

BASE_DIR = Path(os.environ.get("HKT_MEMORY_DIR", Path.cwd() / "memory"))

# --- Chunking Logic (Aligned with OpenClaw) ---

def estimate_tokens(text: str) -> int:
    """Estimate tokens: ~4 characters per token."""
    return len(text) // 4

def chunk_markdown_with_lines(
    content: str, 
    max_tokens: int = 512, 
    overlap_tokens: int = 50
) -> List[Dict[str, Any]]:
    """
    Split markdown content into chunks with line number tracking.
    Aligned with OpenClaw's chunkMarkdown strategy.
    """
    max_chars = max_tokens * 4
    overlap_chars = overlap_tokens * 4
    
    lines = content.split('\n')
    chunks = []
    
    current_lines = []
    current_chars = 0
    current_start_line = 0 # 0-based index for internal logic, will convert to 1-based for output
    
    # Pre-process lines to handle very long lines
    processed_lines = []
    for i, line in enumerate(lines):
        if len(line) > max_chars:
            # Split long line
            parts = [line[j:j+max_chars] for j in range(0, len(line), max_chars)]
            for part in parts:
                processed_lines.append({"text": part, "line_no": i + 1})
        else:
            processed_lines.append({"text": line, "line_no": i + 1})
            
    if not processed_lines:
        return []

    # Iterate through processed lines
    for i, item in enumerate(processed_lines):
        line_text = item["text"]
        line_len = len(line_text)
        
        # If adding this line exceeds max_chars, flush current chunk
        if current_chars + line_len > max_chars and current_lines:
            # Flush
            chunk_text = "\n".join([l["text"] for l in current_lines])
            start_line = current_lines[0]["line_no"]
            end_line = current_lines[-1]["line_no"]
            
            chunks.append({
                "content": chunk_text,
                "start_line": start_line,
                "end_line": end_line,
                "tokens": estimate_tokens(chunk_text)
            })
            
            # Carry over overlap
            # Backtrack from end to find lines that fit in overlap_chars
            overlap_buffer = []
            overlap_len = 0
            for l in reversed(current_lines):
                if overlap_len + len(l["text"]) > overlap_chars:
                    break
                overlap_buffer.insert(0, l)
                overlap_len += len(l["text"])
            
            current_lines = overlap_buffer
            current_chars = overlap_len
            
        current_lines.append(item)
        current_chars += line_len
        
    # Flush remaining
    if current_lines:
        chunk_text = "\n".join([l["text"] for l in current_lines])
        start_line = current_lines[0]["line_no"]
        end_line = current_lines[-1]["line_no"]
        chunks.append({
            "content": chunk_text,
            "start_line": start_line,
            "end_line": end_line,
            "tokens": estimate_tokens(chunk_text)
        })
        
    return chunks

# --- Command Handlers ---

def handle_init(args: argparse.Namespace) -> None:
    if not BASE_DIR.exists():
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created memory directory: {BASE_DIR}")
    
    memory_md = BASE_DIR / "MEMORY.md"
    if not memory_md.exists():
        memory_md.write_text("# Evergreen Memory\n\nStore permanent context here.\n", encoding="utf-8")
        print(f"Created {memory_md}")

def handle_add(args: argparse.Namespace) -> None:
    """
    Add a new memory item.
    Default: Append to memory/YYYY-MM-DD.md
    If --evergreen: Append to MEMORY.md
    """
    if not BASE_DIR.exists():
        BASE_DIR.mkdir(parents=True, exist_ok=True)

    title = args.title.strip()
    content_lines = [item.strip() for item in args.content if item.strip()]
    
    if not title or not content_lines:
        print("Error: --title and --content required")
        return

    # Determine target file
    if args.evergreen:
        target_file = BASE_DIR / "MEMORY.md"
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        target_file = BASE_DIR / f"{today}.md"
        # target_file.parent.mkdir(exist_ok=True) # Parent is BASE_DIR, already exists

    # Format entry
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"\n### {title} ({timestamp})\n"
    for line in content_lines:
        entry += f"- {line}\n"
    
    # Append
    mode = "a" if target_file.exists() else "w"
    if mode == "w" and not args.evergreen:
        # Add header for new daily file
        entry = f"# Daily Memory: {datetime.now().strftime('%Y-%m-%d')}\n" + entry
        
    with open(target_file, mode, encoding="utf-8") as f:
        f.write(entry)
        
    print(f"Added memory to {target_file}")
    
    # Auto-sync if vector store available
    if VectorStore and not args.no_sync:
        print("Syncing...")
        # Create a mini args object for sync
        sync_args = argparse.Namespace(force=False, verbose=False)
        handle_sync(sync_args)

def handle_sync(args: argparse.Namespace) -> None:
    if VectorStore is None:
        print("VectorStore not available.")
        return

    if not BASE_DIR.exists():
        print(f"Memory directory {BASE_DIR} not found.")
        return

    db_path = BASE_DIR / "memory.db"
    store = VectorStore(str(db_path))
    
    if args.verbose:
        print(f"Syncing memory to vector store: {db_path}")

    # Get existing file hashes
    cursor = store.conn.cursor()
    cursor.execute("SELECT path, hash FROM files")
    db_files = {row['path']: row['hash'] for row in cursor.fetchall()}
    
    current_files = set()
    processed_count = 0
    skipped_count = 0
    
    # Collect files to scan
    # Scan all .md files in BASE_DIR recursively
    files_to_scan = []
    
    for path in sorted(BASE_DIR.rglob("*.md")):
        # Skip index.md and README.md
        if path.name.lower() in ["index.md", "readme.md"]:
            continue
        files_to_scan.append(path)

    for file_path in files_to_scan:
        try:
            rel_path = str(file_path.relative_to(BASE_DIR))
            current_files.add(rel_path)
            
            content_text = file_path.read_text(encoding='utf-8')
            current_hash = hashlib.sha256(content_text.encode('utf-8')).hexdigest()
            
            # Check if changed
            if not args.force and rel_path in db_files and db_files[rel_path] == current_hash:
                skipped_count += 1
                continue
            
            if args.verbose:
                print(f"  Ingesting: {rel_path}")
            
            # Chunking
            chunks = chunk_markdown_with_lines(content_text)
            
            # Delete old chunks for this file
            store.delete_file_chunks(rel_path)
            
            # Add new chunks
            for i, chunk in enumerate(chunks):
                chunk_id = f"{rel_path}_{i}"
                meta = {
                    "source": rel_path,
                    "tokens": chunk["tokens"]
                }
                store.add_chunk(
                    chunk_id, 
                    rel_path, 
                    chunk["content"], 
                    chunk["start_line"], 
                    chunk["end_line"], 
                    meta, 
                    updated_at=int(file_path.stat().st_mtime)
                )

            # Update files table
            cursor.execute("INSERT OR REPLACE INTO files (path, hash, mtime) VALUES (?, ?, ?)", 
                           (rel_path, current_hash, int(file_path.stat().st_mtime)))
            store.conn.commit()
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    # Cleanup deleted files
    removed_count = 0
    for db_path in list(db_files.keys()):
        if db_path not in current_files:
            if args.verbose:
                print(f"  Removing: {db_path}")
            store.delete_file_chunks(db_path)
            cursor.execute("DELETE FROM files WHERE path = ?", (db_path,))
            store.conn.commit()
            removed_count += 1
            
    if args.verbose:
        print(f"Sync complete. Processed: {processed_count}, Skipped: {skipped_count}, Removed: {removed_count}")

def handle_query(args: argparse.Namespace) -> None:
    if VectorStore is None:
        print("Error: VectorStore module not available.")
        return

    db_path = BASE_DIR / "memory.db"
    if not db_path.exists():
        print("Error: Memory database not found. Please run 'sync' first.")
        return

    query_text = " ".join(args.keyword or [])
    if not query_text.strip():
        print("Error: --keyword required")
        return

    store = VectorStore(str(db_path))
    
    try:
        results = store.hybrid_search(
            query_text, 
            limit=args.limit,
            vector_weight=args.vector_weight,
            text_weight=args.text_weight,
            mmr_enabled=args.mmr,
            mmr_lambda=args.mmr_lambda,
            decay_enabled=args.decay,
            decay_days=args.decay_days
        )
    except Exception as e:
        print(f"Error during search: {e}")
        return

    if not results:
        print("No results found.")
        return

    # Format Output: [SCORE] path:start-end snippet
    for res in results:
        score = res.get('score', 0.0)
        path = res.get('file_path', 'unknown')
        start = res.get('start_line', 0)
        end = res.get('end_line', 0)
        content = res.get('content', '').strip()
        
        # Truncate content for display if too long
        display_content = content.replace('\n', ' ')
        if len(display_content) > 200:
            display_content = display_content[:197] + "..."
            
        print(f"[{score:.4f}] {path}:{start}-{end}")
        print(f"{display_content}")
        print(f"Source: {path}")
        print()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hkt-memory")
    subparsers = parser.add_subparsers(dest="command")

    # init
    subparsers.add_parser("init")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--content", action="append", required=True)
    add_parser.add_argument("--evergreen", action="store_true", help="Add to MEMORY.md instead of daily log")
    add_parser.add_argument("--no-sync", action="store_true", help="Skip auto-sync")

    # query
    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("--keyword", action="append", required=True)
    query_parser.add_argument("--limit", type=int, default=10)
    query_parser.add_argument("--vector-weight", type=float, default=0.7)
    query_parser.add_argument("--text-weight", type=float, default=0.3)
    query_parser.add_argument("--mmr", action="store_true", default=True) # Default True for OpenClaw alignment
    query_parser.add_argument("--mmr-lambda", type=float, default=0.7)
    query_parser.add_argument("--decay", action="store_true", default=True) # Default True for OpenClaw alignment
    query_parser.add_argument("--decay-days", type=float, default=30.0)
    # Legacy compat
    query_parser.add_argument("--hybrid", action="store_true", help="Ignored (always hybrid)")

    # sync
    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--force", action="store_true")
    sync_parser.add_argument("--verbose", action="store_true", default=True)

    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    
    if args.command == "init":
        handle_init(args)
    elif args.command == "add":
        handle_add(args)
    elif args.command == "query":
        handle_query(args)
    elif args.command == "sync":
        handle_sync(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
