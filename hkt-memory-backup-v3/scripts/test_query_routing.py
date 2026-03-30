import argparse
import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from hkt_memory import (
    _build_consolidated_points,
    _build_structured_items,
    _expand_graph_candidates,
    _fuse_results,
    _resolve_routing_mode,
    _validate_structured_items,
)


class QueryRoutingTests(unittest.TestCase):
    def test_router_disabled_returns_hybrid_only(self):
        args = argparse.Namespace(
            routing_enabled=False,
            router_min_token_count=6,
            router_min_entity_like_tokens=2,
            router_min_low_score_ratio=0.6,
            router_causal_keyword=["why"],
        )
        mode = _resolve_routing_mode(
            "Why AuthService failed",
            [{"id": "1", "score": 0.4}],
            args,
        )
        self.assertEqual(mode, "hybrid_only")

    def test_router_detects_complex_query(self):
        args = argparse.Namespace(
            routing_enabled=True,
            router_min_token_count=3,
            router_min_entity_like_tokens=1,
            router_min_low_score_ratio=0.9,
            router_causal_keyword=["why", "because"],
        )
        mode = _resolve_routing_mode(
            "Why AuthService failed because Redis timeout",
            [{"id": "1", "score": 0.8}, {"id": "2", "score": 0.7}],
            args,
        )
        self.assertEqual(mode, "hybrid_plus_graph")

    def test_graph_expansion_and_fusion(self):
        args = argparse.Namespace(
            graph_timeout_ms=200,
            graph_max_hops=2,
            graph_max_expanded_nodes=5,
            graph_min_relation_score=0.1,
            graph_relation_weight=0.35,
            graph_query_overlap_weight=0.2,
        )
        seeds = [
            {
                "id": "seed-1",
                "file_path": "memory/2026-03-05.md",
                "start_line": 1,
                "end_line": 2,
                "content": "AuthService calls Gateway and Redis",
                "score": 0.8,
            }
        ]
        candidates = [
            *seeds,
            {
                "id": "rel-1",
                "file_path": "memory/2026-03-04.md",
                "start_line": 3,
                "end_line": 4,
                "content": "Gateway retry because Redis timeout",
                "score": 0.35,
            },
            {
                "id": "unrel-1",
                "file_path": "memory/2026-03-03.md",
                "start_line": 5,
                "end_line": 6,
                "content": "Frontend icon color adjusted",
                "score": 0.34,
            },
        ]
        graph = _expand_graph_candidates(
            "Why Gateway timeout because Redis",
            seeds,
            candidates,
            args,
        )
        ids = [item["id"] for item in graph]
        self.assertIn("rel-1", ids)
        self.assertNotIn("unrel-1", ids)
        fused = _fuse_results(seeds, graph, 5)
        self.assertGreaterEqual(len(fused), 2)
        self.assertEqual(fused[0]["id"], "seed-1")

    def test_build_consolidated_points_deduplicates_and_extracts_keywords(self):
        lines = [
            "- 决策：默认启用 routing",
            "- 决策：默认启用 routing",
            "行动: 增加 --no-routing 用于回归",
            "风险：graph 触发阈值需要调优",
        ]
        points = _build_consolidated_points(lines, max_points=5)
        self.assertGreaterEqual(len(points), 3)
        self.assertEqual(points[0], "决策：默认启用 routing")
        self.assertTrue(any("关键词聚合：" in point for point in points))

    def test_build_consolidated_points_returns_empty_when_no_valid_line(self):
        points = _build_consolidated_points(["  ", "-", "   "], max_points=5)
        self.assertEqual(points, [])

    def test_build_structured_items_maps_kind_and_topic(self):
        args = argparse.Namespace(
            scope="session",
            status="active",
            default_topic="misc",
        )
        points = [
            "决策: 默认只开routing",
            "行动: graph按阈值触发",
            "风险: 阈值需要继续调优",
            "约束: 必须可回滚",
        ]
        items = _build_structured_items(points, args)
        self.assertEqual(items[0]["kind"], "decision")
        self.assertEqual(items[0]["topic"], "routing")
        self.assertEqual(items[1]["kind"], "action")
        self.assertEqual(items[1]["topic"], "graph")
        self.assertEqual(items[2]["kind"], "risk")
        self.assertEqual(items[3]["kind"], "constraint")
        self.assertEqual(items[3]["topic"], "misc")

    def test_validate_structured_items_respects_thresholds(self):
        items = [
            {"kind": "decision", "topic": "routing"},
            {"kind": "fact", "topic": "misc"},
            {"kind": "fact", "topic": "misc"},
        ]
        args = argparse.Namespace(
            max_unknown_topic_ratio=0.5,
            max_fallback_kind_ratio=0.5,
        )
        passed, metrics = _validate_structured_items(items, args)
        self.assertFalse(passed)
        self.assertGreater(metrics["unknown_topic_ratio"], 0.5)
        self.assertGreater(metrics["fallback_kind_ratio"], 0.5)


if __name__ == "__main__":
    unittest.main()
