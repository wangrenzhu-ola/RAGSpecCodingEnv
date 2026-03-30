#!/usr/bin/env python3
"""
HKT-Memory v4.5 - Production-grade long-term memory system

Features:
- L0/L1/L2 layered storage
- Smart Extraction with 6-category classification
- Cross-Encoder Reranking (Jina/SiliconFlow)
- Weibull Decay lifecycle management
- Self-Improvement Governance
- MCP Server support
- Auto-Capture/Auto-Recall
- ✅ BM25 Full-Text Search
- ✅ Hybrid Retrieval (Vector + BM25 Fusion)
- ✅ Adaptive Retrieval
- ✅ MMR Diversity
- ✅ Multi-Scope Isolation
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent.parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from layers import LayerManager
from extraction import MemoryClassifier, TwoStageDeduplicator
from reranker import JinaReranker, SiliconFlowReranker
from lifecycle import TierManager
from governance import LearningTracker, ErrorTracker
from mcp.tools import MemoryTools
from session.auto_manager import AutoCaptureRecall

# v4.5新增模块
from retrieval import BM25Index, HybridFusion, AdaptiveRetriever, MMRDiversifier
from scopes import ScopeManager


class HKTMv4:
    """HKT-Memory v4.5 主类"""
    
    def __init__(self, memory_dir: str = None):
        self.memory_dir = Path(memory_dir or os.environ.get("HKT_MEMORY_DIR", "memory"))
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化各模块
        self.layers = LayerManager(self.memory_dir)
        self.classifier = MemoryClassifier()
        self.deduplicator = TwoStageDeduplicator()
        self.tier_manager = TierManager(self.memory_dir)
        self.learning_tracker = LearningTracker(self.memory_dir / "governance")
        self.error_tracker = ErrorTracker(self.memory_dir / "governance")
        self.mcp_tools = MemoryTools(self.memory_dir)
        self.auto_manager = AutoCaptureRecall(self.memory_dir)
        
        # 初始化重排序器（如果API key存在）
        self.reranker = None
        if os.environ.get("JINA_API_KEY"):
            self.reranker = JinaReranker()
        elif os.environ.get("SILICONFLOW_API_KEY"):
            self.reranker = SiliconFlowReranker()
        
        # v4.5新增模块初始化
        self.bm25_index = BM25Index(str(self.memory_dir / "bm25_index.db"))
        self.hybrid_fusion = HybridFusion()
        self.adaptive_retriever = AdaptiveRetriever()
        self.mmr_diversifier = MMRDiversifier()
        self.scope_manager = ScopeManager()
    
    def store(self, content: str, title: str = "", topic: str = "general", 
              layer: str = "L2", extract: bool = True,
              scope: str = "global", agent_id: str = None, project_id: str = None,
              **kwargs) -> Dict[str, str]:
        """
        存储记忆
        
        v4.5新增参数:
            scope: 作用域 (global/agent:<id>/project:<id>)
            agent_id: Agent标识
            project_id: 项目标识
        """
        # 去重检查
        if extract:
            existing = []  # TODO: 获取现有记忆
            dedup_result = self.deduplicator.check_duplicate(content, existing)
            
            if dedup_result.action.value == "skip":
                print(f"Skipping duplicate: {dedup_result.reason}")
                return {}
        
        # 分层存储
        ids = self.layers.store(content, title, layer, topic, kwargs.get('metadata'))
        
        # 同时存储到向量数据库 (使用智谱AI Embedding)
        try:
            doc_id = ids.get('L2') or ids.get('L0') or f"doc-{datetime.now().timestamp()}"
            self.layers.vector_store.add(
                doc_id=doc_id,
                content=content,
                layer=layer,
                source=ids.get('L2', ''),
                metadata={
                    "title": title,
                    "topic": topic,
                    "classified": extract,
                    "scope": scope,
                    "agent_id": agent_id,
                    "project_id": project_id,
                    **(kwargs.get('metadata') or {})
                }
            )
            print(f"✓ Stored to vector database (doc_id: {doc_id})")
        except Exception as e:
            print(f"⚠ Vector store failed (non-critical): {e}")
        
        # 同时存储到BM25索引 (v4.5)
        try:
            self.bm25_index.add_document(
                doc_id=doc_id,
                content=content,
                metadata={
                    "title": title,
                    "topic": topic,
                    "layer": layer
                },
                scope=scope,
                agent_id=agent_id,
                project_id=project_id
            )
            print(f"✓ Stored to BM25 index")
        except Exception as e:
            print(f"⚠ BM25 index failed (non-critical): {e}")
        
        # 智能分类
        if extract:
            classified = self.classifier.classify(content)
            print(f"Classified as: {classified.category.value} (confidence: {classified.confidence:.2f})")
        
        # 注册到生命周期管理
        for layer_name, memory_id in ids.items():
            self.tier_manager.register_memory(memory_id)
        
        return ids
    
    def retrieve(self, 
                 query: str, 
                 layer: str = "all", 
                 limit: int = 10,
                 # v4.5新增参数
                 retrieval_mode: str = "hybrid",  # vector/bm25/hybrid
                 vector_weight: float = 0.7,
                 bm25_weight: float = 0.3,
                 adaptive: bool = True,
                 scopes: List[str] = None,
                 min_score: float = 0.35,
                 apply_mmr: bool = True,
                 mmr_threshold: float = 0.85,
                 rerank: bool = True, 
                 use_vector: bool = True) -> List[Dict[str, Any]]:
        """
        检索记忆 - v4.5增强版6阶段检索管道
        
        检索流程:
        1. 自适应判断 → 2. 混合检索 → 3. 重排序 → 4. 生命周期增强 → 5. MMR多样性 → 6. Scope过滤
        
        Args:
            query: 查询文本
            layer: 目标层 (L0/L1/L2/all)
            limit: 返回数量
            retrieval_mode: 检索模式 (vector/bm25/hybrid)
            vector_weight: 向量搜索权重
            bm25_weight: BM25权重
            adaptive: 是否启用自适应检索
            scopes: 作用域过滤
            min_score: 最小分数阈值
            apply_mmr: 是否应用MMR多样性
            mmr_threshold: MMR相似度阈值
            rerank: 是否重排序
            use_vector: 是否使用向量搜索
            
        Returns:
            检索结果列表
        """
        # Stage 1: 自适应检索判断
        if adaptive:
            should_retrieve, reason, metadata = self.adaptive_retriever.should_retrieve(query)
            if not should_retrieve:
                print(f"🚫 Adaptive retrieval skipped: {reason}")
                return []
            print(f"✅ Adaptive retrieval enabled: {reason}")
        
        # 设置作用域
        if scopes:
            self.scope_manager.set_scopes(scopes)
        
        all_results = []
        
        # Stage 2: 混合检索
        if retrieval_mode == "hybrid":
            # 向量搜索
            vector_results = []
            if use_vector:
                try:
                    print(f"🔍 Performing vector search with Zhipu AI embedding...")
                    vector_results = self.layers.vector_store.search(
                        query=query,
                        top_k=limit * 3,  # 获取更多结果用于融合
                        layer=layer if layer != "all" else None
                    )
                    print(f"✓ Vector search returned {len(vector_results)} results")
                except Exception as e:
                    print(f"⚠ Vector search failed: {e}")
            
            # BM25搜索
            bm25_results = []
            try:
                print(f"🔍 Performing BM25 search...")
                active_scopes = self.scope_manager.get_active_scopes()
                bm25_results = self.bm25_index.search(
                    query=query,
                    top_k=limit * 3,
                    scopes=active_scopes
                )
                print(f"✓ BM25 search returned {len(bm25_results)} results")
            except Exception as e:
                print(f"⚠ BM25 search failed: {e}")
            
            # 融合结果
            if vector_results or bm25_results:
                from retrieval.hybrid_fusion import FusionConfig
                fusion_config = FusionConfig(
                    vector_weight=vector_weight,
                    bm25_weight=bm25_weight,
                    min_score=min_score,
                    candidate_pool_size=limit * 2
                )
                self.hybrid_fusion = HybridFusion(fusion_config)
                all_results = self.hybrid_fusion.fuse(vector_results, bm25_results, query)
                print(f"✓ Hybrid fusion returned {len(all_results)} results")
        
        elif retrieval_mode == "vector":
            # 纯向量搜索
            if use_vector:
                try:
                    print(f"🔍 Performing vector search...")
                    all_results = self.layers.vector_store.search(
                        query=query,
                        top_k=limit * 2,
                        layer=layer if layer != "all" else None
                    )
                except Exception as e:
                    print(f"⚠ Vector search failed: {e}")
        
        elif retrieval_mode == "bm25":
            # 纯BM25搜索
            try:
                print(f"🔍 Performing BM25 search...")
                active_scopes = self.scope_manager.get_active_scopes()
                all_results = self.bm25_index.search(
                    query=query,
                    top_k=limit * 2,
                    scopes=active_scopes
                )
            except Exception as e:
                print(f"⚠ BM25 search failed: {e}")
        
        # 如果主检索无结果，回退到分层检索
        if not all_results:
            print(f"🔍 Falling back to layered keyword search...")
            if layer == "all":
                results = self.layers.progressive_retrieve(query, limit)
                for layer_name, layer_results in results.items():
                    for r in layer_results:
                        r['layer'] = layer_name
                        all_results.append(r)
            else:
                all_results = self.layers.retrieve(query, layer, limit, use_vector=False)
        
        # Stage 3: 重排序
        if rerank and self.reranker and len(all_results) > 1:
            print(f"🔄 Reranking with Cross-Encoder...")
            all_results = self.reranker.rerank_with_original(query, all_results)
        
        # Stage 4: 生命周期增强 (Weibull Decay Boost)
        if all_results:
            print(f"📈 Applying lifecycle decay boost...")
            all_results = self._apply_lifecycle_boost(all_results)
        
        # Stage 5: MMR多样性
        if apply_mmr and len(all_results) > 1:
            print(f"🎯 Applying MMR diversity (threshold={mmr_threshold})...")
            from retrieval.mmr_diversifier import MMRConfig
            mmr_config = MMRConfig(
                similarity_threshold=mmr_threshold,
                candidate_pool_size=limit
            )
            self.mmr_diversifier = MMRDiversifier(mmr_config)
            all_results = self.mmr_diversifier.simple_diversify(all_results, mmr_threshold)
        
        # Stage 6: Scope过滤
        if scopes:
            print(f"🔒 Filtering by scopes: {scopes}")
            all_results = self.scope_manager.filter_by_scope(all_results, scopes)
        
        # 硬最小分数过滤
        all_results = [r for r in all_results if r.get('score', 0) >= min_score]
        
        # 记录访问
        for r in all_results[:limit]:
            mem_id = r.get('id')
            if mem_id:
                self.tier_manager.record_access(mem_id)
        
        return all_results[:limit]
    
    def _apply_lifecycle_boost(self, results: List[Dict]) -> List[Dict]:
        """应用生命周期增强（Weibull Decay）"""
        from lifecycle.weibull_decay import WeibullDecay, MemoryTier
        
        weibull = WeibullDecay()
        boosted = []
        
        for result in results:
            base_score = result.get('score', 0.5)
            access_count = result.get('access_count', 0)
            
            # 计算访问增强
            boost = weibull._access_boost(access_count)
            boosted_score = min(1.0, base_score * boost)
            
            result = dict(result)
            result['score'] = round(boosted_score, 4)
            result['original_score'] = round(base_score, 4)
            boosted.append(result)
        
        # 重新排序
        boosted.sort(key=lambda x: x['score'], reverse=True)
        return boosted
    
    def auto_capture(self, conversation_file: str = None) -> Dict[str, Any]:
        """自动捕获对话中的记忆"""
        if conversation_file and Path(conversation_file).exists():
            with open(conversation_file, 'r') as f:
                conversation = json.load(f)
        else:
            # 从stdin读取
            import sys
            conversation = []
            print("Enter conversation (JSON format), Ctrl+D to finish:")
            try:
                data = sys.stdin.read()
                conversation = json.loads(data)
            except:
                return {"error": "Invalid JSON input"}
        
        result = self.auto_manager.auto_capture(conversation)
        return result or {"captured": False, "reason": "No valuable memories found"}
    
    def auto_recall(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """自动回忆相关记忆"""
        return self.auto_manager.auto_recall(query, top_k=top_k)
    
    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'layers': self.layers.get_stats(),
            'vector_store': self.layers.vector_store.get_stats(),
            'bm25_index': self.bm25_index.get_stats(),
            'tier_distribution': self.tier_manager.get_tier_distribution(),
            'learnings': self.learning_tracker.get_stats(),
            'errors': self.error_tracker.get_stats(),
            'scopes': self.scope_manager.get_stats()
        }


def main():
    parser = argparse.ArgumentParser(
        prog="hkt-memory-v4.5",
        description="HKT-Memory v4.5 - Enhanced production-grade memory system"
    )
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Store command
    store_parser = subparsers.add_parser("store", help="Store a memory")
    store_parser.add_argument("--content", "-c", required=True, help="Memory content")
    store_parser.add_argument("--title", "-t", default="", help="Memory title")
    store_parser.add_argument("--topic", default="general", help="Topic/category")
    store_parser.add_argument("--layer", choices=["L0", "L1", "L2", "all"], default="L2")
    store_parser.add_argument("--no-extract", action="store_true", help="Disable smart extraction")
    # v4.5新增
    store_parser.add_argument("--scope", default="global", help="Scope (global/agent:<id>/project:<id>)")
    store_parser.add_argument("--agent-id", help="Agent ID for scope isolation")
    store_parser.add_argument("--project-id", help="Project ID for scope isolation")
    
    # Retrieve command
    retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve memories")
    retrieve_parser.add_argument("--query", "-q", required=True, help="Search query")
    retrieve_parser.add_argument("--layer", choices=["L0", "L1", "L2", "all"], default="all")
    retrieve_parser.add_argument("--limit", "-n", type=int, default=10)
    retrieve_parser.add_argument("--no-rerank", action="store_true", help="Disable reranking")
    retrieve_parser.add_argument("--no-vector", action="store_true", help="Disable vector search")
    # v4.5新增参数
    retrieve_parser.add_argument("--mode", choices=["vector", "bm25", "hybrid"], 
                                 default="hybrid", help="Retrieval mode")
    retrieve_parser.add_argument("--vector-weight", type=float, default=0.7,
                                 help="Vector search weight (0-1)")
    retrieve_parser.add_argument("--bm25-weight", type=float, default=0.3,
                                 help="BM25 weight (0-1)")
    retrieve_parser.add_argument("--no-adaptive", action="store_true",
                                 help="Disable adaptive retrieval")
    retrieve_parser.add_argument("--scope", help="Comma-separated scopes (e.g., global,agent:main)")
    retrieve_parser.add_argument("--min-score", type=float, default=0.35,
                                 help="Minimum score threshold")
    retrieve_parser.add_argument("--no-mmr", action="store_true",
                                 help="Disable MMR diversity")
    retrieve_parser.add_argument("--mmr-threshold", type=float, default=0.85,
                                 help="MMR similarity threshold")
    
    # Stats command
    subparsers.add_parser("stats", help="Show statistics")
    
    # Learning commands
    learn_parser = subparsers.add_parser("learn", help="Record a learning")
    learn_parser.add_argument("--content", "-c", required=True, help="Learning content")
    learn_parser.add_argument("--category", choices=["pattern", "methodology", "insight"], default="insight")
    learn_parser.add_argument("--context", default="", help="Context")
    
    # Error commands
    error_parser = subparsers.add_parser("error", help="Record an error")
    error_parser.add_argument("--description", "-d", required=True, help="Error description")
    error_parser.add_argument("--severity", choices=["critical", "high", "medium", "low"], default="medium")
    error_parser.add_argument("--message", "-m", default="", help="Error message")
    
    # Maintenance command
    subparsers.add_parser("maintenance", help="Run maintenance tasks")
    
    # MCP commands
    mcp_parser = subparsers.add_parser("mcp", help="MCP tool commands")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command")
    
    mcp_recall = mcp_subparsers.add_parser("recall", help="Recall memories via MCP")
    mcp_recall.add_argument("--query", "-q", required=True, help="Query")
    mcp_recall.add_argument("--limit", "-n", type=int, default=5)
    
    mcp_store = mcp_subparsers.add_parser("store", help="Store memory via MCP")
    mcp_store.add_argument("--content", "-c", required=True, help="Content")
    mcp_store.add_argument("--title", "-t", default="", help="Title")
    
    mcp_stats = mcp_subparsers.add_parser("stats", help="Get stats via MCP")
    
    # Auto commands
    auto_parser = subparsers.add_parser("auto", help="Auto capture/recall")
    auto_subparsers = auto_parser.add_subparsers(dest="auto_command")
    
    auto_capture = auto_subparsers.add_parser("capture", help="Auto capture from conversation")
    auto_capture.add_argument("--file", "-f", help="Conversation JSON file")
    
    auto_recall = auto_subparsers.add_parser("recall", help="Auto recall memories")
    auto_recall.add_argument("--query", "-q", required=True, help="Query")
    
    # v4.5新增: BM25管理命令
    bm25_parser = subparsers.add_parser("bm25", help="BM25 index management")
    bm25_subparsers = bm25_parser.add_subparsers(dest="bm25_command")
    bm25_stats = bm25_subparsers.add_parser("stats", help="BM25 index statistics")
    bm25_optimize = bm25_subparsers.add_parser("optimize", help="Optimize BM25 index")
    
    # v4.5新增: 检索测试命令
    test_parser = subparsers.add_parser("test-retrieval", help="Test retrieval pipeline")
    test_parser.add_argument("--query", "-q", required=True, help="Test query")
    test_parser.add_argument("--mode", choices=["vector", "bm25", "hybrid"], default="hybrid")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize HKT-Memory v4.5
    memory = HKTMv4()
    
    if args.command == "store":
        ids = memory.store(
            content=args.content,
            title=args.title,
            topic=args.topic,
            layer=args.layer,
            extract=not args.no_extract,
            scope=args.scope,
            agent_id=args.agent_id,
            project_id=args.project_id
        )
        print(f"Stored with IDs: {ids}")
    
    elif args.command == "retrieve":
        # 解析scope
        scopes = None
        if args.scope:
            scopes = [s.strip() for s in args.scope.split(",")]
        
        results = memory.retrieve(
            query=args.query,
            layer=args.layer,
            limit=args.limit,
            retrieval_mode=args.mode,
            vector_weight=args.vector_weight,
            bm25_weight=args.bm25_weight,
            adaptive=not args.no_adaptive,
            scopes=scopes,
            min_score=args.min_score,
            apply_mmr=not args.no_mmr,
            mmr_threshold=args.mmr_threshold,
            rerank=not args.no_rerank,
            use_vector=not args.no_vector
        )
        print(f"\nFound {len(results)} results:\n")
        for i, r in enumerate(results, 1):
            score = r.get('score', 0)
            layer = r.get('layer', 'unknown')
            content = r.get('content', '')[:200]
            print(f"{i}. [{layer}] Score: {score:.4f}")
            print(f"   {content}...\n")
    
    elif args.command == "stats":
        stats = memory.stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    elif args.command == "learn":
        learning_id = memory.learning_tracker.record(
            content=args.content,
            category=args.category,
            context=args.context
        )
        print(f"Learning recorded: {learning_id}")
    
    elif args.command == "error":
        error_id = memory.error_tracker.record(
            error_description=args.description,
            severity=args.severity,
            error_message=args.message
        )
        print(f"Error recorded: {error_id}")
    
    elif args.command == "maintenance":
        results = memory.tier_manager.run_maintenance()
        print("Maintenance completed:")
        print(f"  Promoted: {len(results['promoted'])}")
        print(f"  Demoted: {len(results['demoted'])}")
        print(f"  Unchanged: {len(results['unchanged'])}")
    
    elif args.command == "mcp":
        if args.mcp_command == "recall":
            result = memory.mcp_tools.memory_recall(
                query=args.query,
                limit=args.limit
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.mcp_command == "store":
            result = memory.mcp_tools.memory_store(
                content=args.content,
                title=args.title
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.mcp_command == "stats":
            result = memory.mcp_tools.memory_stats()
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "auto":
        if args.auto_command == "capture":
            result = memory.auto_capture(args.file)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        elif args.auto_command == "recall":
            result = memory.auto_recall(args.query)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "bm25":
        if args.bm25_command == "stats":
            stats = memory.bm25_index.get_stats()
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        
        elif args.bm25_command == "optimize":
            memory.bm25_index.optimize()
            print("BM25 index optimized")
    
    elif args.command == "test-retrieval":
        # 测试检索管道
        print(f"\n🧪 Testing retrieval pipeline with query: '{args.query}'")
        print("=" * 60)
        
        # 自适应判断
        should_retrieve, reason, metadata = memory.adaptive_retriever.should_retrieve(args.query)
        print(f"\n1️⃣ Adaptive Retrieval:")
        print(f"   Should retrieve: {should_retrieve}")
        print(f"   Reason: {reason}")
        
        if should_retrieve:
            results = memory.retrieve(
                query=args.query,
                retrieval_mode=args.mode,
                limit=5
            )
            print(f"\n2️⃣ Results ({len(results)}):")
            for i, r in enumerate(results, 1):
                print(f"   {i}. Score: {r.get('score', 0):.4f} - {r.get('content', '')[:80]}...")


if __name__ == "__main__":
    main()
