import argparse
import os
import re
import sys
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

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

CONSOLIDATE_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "for",
    "of",
    "in",
    "on",
    "with",
    "by",
    "is",
    "are",
    "was",
    "were",
    "be",
    "this",
    "that",
    "it",
    "as",
    "from",
    "我们",
    "你们",
    "他们",
    "这个",
    "那个",
    "进行",
    "需要",
    "已经",
    "当前",
    "可以",
    "以及",
}

KIND_VOCAB = {"decision", "action", "risk", "todo", "fact", "constraint"}
SCOPE_VOCAB = {"session", "feature", "project", "global"}
STATUS_VOCAB = {"active", "draft", "deprecated", "blocked", "done"}
TOPIC_VOCAB = {"memory_search", "routing", "graph", "sync", "schema", "misc"}

TOPIC_KEYWORD_MAP = {
    "routing": ["routing", "route", "query router", "no-routing", "路由"],
    "graph": ["graph", "graphrag", "multi-hop", "多跳", "图扩展", "图谱"],
    "sync": ["sync", "index", "ingest", "ingestion", "索引", "同步"],
    "schema": ["schema", "tag", "label", "taxonomy", "词表", "标签", "分类"],
    "memory_search": ["memory", "hybrid", "mmr", "decay", "vector", "fts", "检索", "向量"],
}

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

def _normalize_context_line(line: str) -> str:
    cleaned = line.strip()
    cleaned = re.sub(r"^[\-\*\d\.\)\s]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def _extract_keywords(lines: List[str], top_k: int = 5) -> List[str]:
    freq: Dict[str, int] = {}
    for line in lines:
        for token in re.findall(r"[\w\u4e00-\u9fff-]+", line.lower()):
            if len(token) <= 1:
                continue
            if token in CONSOLIDATE_STOPWORDS:
                continue
            freq[token] = freq.get(token, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [token for token, _ in ranked[:top_k]]

def _build_consolidated_points(raw_lines: List[str], max_points: int) -> List[str]:
    normalized: List[str] = []
    seen = set()
    for raw in raw_lines:
        line = _normalize_context_line(raw)
        if not line:
            continue
        if line in seen:
            continue
        seen.add(line)
        normalized.append(line)
    if not normalized:
        return []
    points = normalized[: max(1, max_points)]
    keywords = _extract_keywords(points)
    if keywords:
        points.append(f"关键词聚合：{', '.join(keywords)}")
    return points

def _infer_kind(text: str) -> str:
    normalized = text.lower()
    if any(keyword in normalized for keyword in ["决策", "决定", "结论", "方案", "decision"]):
        return "decision"
    if any(keyword in normalized for keyword in ["行动", "执行", "实施", "落地", "新增", "修复", "改造", "action"]):
        return "action"
    if any(keyword in normalized for keyword in ["风险", "问题", "隐患", "阻塞", "故障", "risk"]):
        return "risk"
    if any(keyword in normalized for keyword in ["待办", "todo", "下一步", "后续"]):
        return "todo"
    if any(keyword in normalized for keyword in ["约束", "限制", "规范", "必须", "constraint"]):
        return "constraint"
    return "fact"

def _infer_topic(text: str, default_topic: str) -> str:
    normalized = text.lower()
    for topic, keywords in TOPIC_KEYWORD_MAP.items():
        if any(keyword in normalized for keyword in keywords):
            return topic
    return default_topic if default_topic in TOPIC_VOCAB else "misc"

def _build_structured_items(points: List[str], args: argparse.Namespace) -> List[Dict[str, str]]:
    scope = args.scope if args.scope in SCOPE_VOCAB else "session"
    status = args.status if args.status in STATUS_VOCAB else "active"
    structured: List[Dict[str, str]] = []
    for point in points:
        kind = _infer_kind(point)
        topic = _infer_topic(point, args.default_topic)
        if kind not in KIND_VOCAB:
            kind = "fact"
        if topic not in TOPIC_VOCAB:
            topic = "misc"
        structured.append({
            "point": point,
            "kind": kind,
            "scope": scope,
            "status": status,
            "topic": topic,
        })
    return structured

def _validate_structured_items(items: List[Dict[str, str]], args: argparse.Namespace) -> Tuple[bool, Dict[str, float]]:
    if not items:
        return False, {"unknown_topic_ratio": 1.0, "fallback_kind_ratio": 1.0}
    total = len(items)
    unknown_topic = sum(1 for item in items if item.get("topic") == "misc")
    fallback_kind = sum(1 for item in items if item.get("kind") == "fact")
    unknown_topic_ratio = unknown_topic / total
    fallback_kind_ratio = fallback_kind / total
    passed = (
        unknown_topic_ratio <= args.max_unknown_topic_ratio
        and fallback_kind_ratio <= args.max_fallback_kind_ratio
    )
    return passed, {
        "unknown_topic_ratio": unknown_topic_ratio,
        "fallback_kind_ratio": fallback_kind_ratio,
    }

def handle_consolidate(args: argparse.Namespace) -> None:
    input_lines = list(args.content or [])
    if args.stdin:
        stdin_text = sys.stdin.read()
        if stdin_text.strip():
            input_lines.extend(stdin_text.splitlines())
    elif not args.content and not sys.stdin.isatty():
        stdin_text = sys.stdin.read()
        if stdin_text.strip():
            input_lines.extend(stdin_text.splitlines())

    points = _build_consolidated_points(input_lines, args.max_points)
    if not points:
        print("Error: no context lines to consolidate. Use --content or pipe stdin.")
        return

    structured_items = _build_structured_items(points, args)
    passed, metrics = _validate_structured_items(structured_items, args)
    if not passed and not args.allow_threshold_breach:
        print(
            "Error: structured tag validation failed. "
            f"unknown_topic_ratio={metrics['unknown_topic_ratio']:.2f}, "
            f"fallback_kind_ratio={metrics['fallback_kind_ratio']:.2f}"
        )
        print("Tip: tune input points or use --allow-threshold-breach for forced write.")
        return

    title = args.title.strip() if args.title else "整合当前记忆"
    source_prefix = args.source.strip() if args.source else "当前上下文"
    final_points = []
    for item in structured_items:
        final_points.append(
            f"[{source_prefix}][kind={item['kind']}][scope={item['scope']}][status={item['status']}][topic={item['topic']}] {item['point']}"
        )

    add_args = argparse.Namespace(
        title=title,
        content=final_points,
        evergreen=bool(args.evergreen),
        no_sync=bool(args.no_sync),
    )
    handle_add(add_args)
    print(
        f"Consolidated {len(points)} points into memory. "
        f"unknown_topic_ratio={metrics['unknown_topic_ratio']:.2f}, "
        f"fallback_kind_ratio={metrics['fallback_kind_ratio']:.2f}"
    )

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

def _tokenize(text: str) -> List[str]:
    return re.findall(r"[\w\u4e00-\u9fff-]+", text.lower())

def _analyze_query(query: str) -> Tuple[int, int]:
    tokens = re.findall(r"[\w\u4e00-\u9fff-]+", query)
    entity_like_count = 0
    for token in tokens:
        if re.match(r"^[A-Z][A-Za-z0-9_-]{2,}$", token):
            entity_like_count += 1
        elif re.match(r"^[\u4e00-\u9fff]{2,}$", token):
            entity_like_count += 1
    return len(tokens), entity_like_count

def _compute_low_score_ratio(candidates: List[Dict[str, Any]], threshold: float = 0.45) -> float:
    if not candidates:
        return 0.0
    low_count = 0
    for item in candidates:
        if float(item.get("score", 0.0)) < threshold:
            low_count += 1
    return low_count / len(candidates)

def _resolve_routing_mode(query: str, candidates: List[Dict[str, Any]], args: argparse.Namespace) -> str:
    if not args.routing_enabled:
        return "hybrid_only"
    try:
        token_count, entity_like_count = _analyze_query(query)
        low_score_ratio = _compute_low_score_ratio(candidates)
        normalized_query = query.lower()
        has_causal_keyword = any(
            keyword and keyword.lower() in normalized_query for keyword in (args.router_causal_keyword or [])
        )
        should_expand = (
            token_count >= args.router_min_token_count
            and entity_like_count >= args.router_min_entity_like_tokens
        ) or has_causal_keyword or low_score_ratio >= args.router_min_low_score_ratio
        return "hybrid_plus_graph" if should_expand else "hybrid_only"
    except Exception:
        return "hybrid_only"

def _overlap_ratio(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    common = len(a.intersection(b))
    return common / max(len(a), len(b))

def _result_key(item: Dict[str, Any]) -> str:
    item_id = item.get("id")
    if item_id:
        return str(item_id)
    return f"{item.get('file_path','')}:{item.get('start_line',0)}:{item.get('end_line',0)}"

def _expand_graph_candidates(
    query: str,
    seeds: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    args: argparse.Namespace,
) -> List[Dict[str, Any]]:
    if not seeds or not candidates:
        return []
    start_time = time.time()
    timeout_s = max(0.02, args.graph_timeout_ms / 1000.0)
    query_tokens = set(_tokenize(query))
    seed_keys = {_result_key(item) for item in seeds}
    max_hops = max(1, int(args.graph_max_hops))
    max_expanded_nodes = max(1, int(args.graph_max_expanded_nodes))
    seed_limit = max(1, max_hops * 2)
    limited_seeds = seeds[:seed_limit]
    seed_token_sets = [set(_tokenize(seed.get("content", ""))) for seed in limited_seeds]
    expanded: List[Dict[str, Any]] = []

    for item in candidates:
        if time.time() - start_time > timeout_s:
            break
        if _result_key(item) in seed_keys:
            continue
        item_tokens = set(_tokenize(item.get("content", "")))
        relation_score = 0.0
        for seed_tokens in seed_token_sets:
            relation_score = max(relation_score, _overlap_ratio(item_tokens, seed_tokens))
        if relation_score < args.graph_min_relation_score:
            continue
        query_overlap = _overlap_ratio(item_tokens, query_tokens)
        merged_item = dict(item)
        merged_item["score"] = float(item.get("score", 0.0)) + (
            relation_score * args.graph_relation_weight
        ) + (query_overlap * args.graph_query_overlap_weight)
        merged_item["graph_relation_score"] = relation_score
        merged_item["graph_query_overlap"] = query_overlap
        expanded.append(merged_item)
        if len(expanded) >= max_expanded_nodes:
            break

    expanded.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    return expanded

def _fuse_results(
    hybrid_results: List[Dict[str, Any]],
    graph_results: List[Dict[str, Any]],
    limit: int,
) -> List[Dict[str, Any]]:
    by_key: Dict[str, Dict[str, Any]] = {}
    for item in hybrid_results + graph_results:
        key = _result_key(item)
        score = float(item.get("score", 0.0))
        existing = by_key.get(key)
        if existing is None or score > float(existing.get("score", 0.0)):
            by_key[key] = item
    ranked = list(by_key.values())
    ranked.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    return ranked[: max(1, limit)]

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
        candidate_limit = max(
            args.limit,
            args.limit * args.candidate_multiplier,
            args.limit + args.graph_max_expanded_nodes,
        )
        candidates = store.hybrid_search(
            query_text, 
            limit=candidate_limit,
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

    if not candidates:
        print("No results found.")
        return

    routing_mode = _resolve_routing_mode(query_text, candidates, args)
    results = candidates[: max(1, args.limit)]
    if routing_mode == "hybrid_plus_graph" and args.graph_enabled:
        try:
            graph_results = _expand_graph_candidates(query_text, results, candidates, args)
            results = _fuse_results(results, graph_results, args.limit)
        except Exception:
            routing_mode = "hybrid_only"
            results = candidates[: max(1, args.limit)]
    else:
        routing_mode = "hybrid_only"

    # Format Output: [SCORE] path:start-end snippet
    if args.show_mode:
        print(f"Mode: {routing_mode}")
        print()

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

    consolidate_parser = subparsers.add_parser("consolidate")
    consolidate_parser.add_argument("--title", default="整合当前记忆")
    consolidate_parser.add_argument("--content", action="append")
    consolidate_parser.add_argument("--stdin", action="store_true")
    consolidate_parser.add_argument("--max-points", type=int, default=8)
    consolidate_parser.add_argument("--source", default="当前上下文")
    consolidate_parser.add_argument("--scope", choices=sorted(SCOPE_VOCAB), default="session")
    consolidate_parser.add_argument("--status", choices=sorted(STATUS_VOCAB), default="active")
    consolidate_parser.add_argument("--default-topic", choices=sorted(TOPIC_VOCAB), default="misc")
    consolidate_parser.add_argument("--max-unknown-topic-ratio", type=float, default=0.6)
    consolidate_parser.add_argument("--max-fallback-kind-ratio", type=float, default=0.7)
    consolidate_parser.add_argument("--allow-threshold-breach", action="store_true")
    consolidate_parser.add_argument("--evergreen", action="store_true")
    consolidate_parser.add_argument("--no-sync", action="store_true")

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
    query_parser.add_argument("--candidate-multiplier", type=int, default=3)
    query_parser.add_argument("--routing-enabled", dest="routing_enabled", action="store_true")
    query_parser.add_argument("--no-routing", dest="routing_enabled", action="store_false")
    query_parser.add_argument("--router-min-token-count", type=int, default=6)
    query_parser.add_argument("--router-min-entity-like-tokens", type=int, default=2)
    query_parser.add_argument("--router-min-low-score-ratio", type=float, default=0.6)
    query_parser.add_argument(
        "--router-causal-keyword",
        action="append",
        default=["why", "because", "cause", "原因", "导致", "为什么"],
    )
    query_parser.add_argument("--graph-enabled", dest="graph_enabled", action="store_true")
    query_parser.add_argument("--no-graph", dest="graph_enabled", action="store_false")
    query_parser.add_argument("--graph-max-hops", type=int, default=2)
    query_parser.add_argument("--graph-max-expanded-nodes", type=int, default=20)
    query_parser.add_argument("--graph-timeout-ms", type=int, default=120)
    query_parser.add_argument("--graph-min-relation-score", type=float, default=0.1)
    query_parser.add_argument("--graph-relation-weight", type=float, default=0.35)
    query_parser.add_argument("--graph-query-overlap-weight", type=float, default=0.2)
    query_parser.add_argument("--show-mode", action="store_true")
    query_parser.set_defaults(routing_enabled=True, graph_enabled=True)
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
    elif args.command == "consolidate":
        handle_consolidate(args)
    elif args.command == "query":
        handle_query(args)
    elif args.command == "sync":
        handle_sync(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
