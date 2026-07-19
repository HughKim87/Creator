"""Checks for the bounded L3.1 navigation helper and source manifest."""

from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.knowledge_navigation import (
    ACTIVE_MARKDOWN_ALLOWLIST,
    PROTECTED_PREFIXES,
    audit_manifest,
    audit_graph,
    audit_typed_route_graph,
    build_direct_baseline,
    build_typed_route_graph,
    compact_typed_route_result,
    compare_typed_routes,
    query_graph,
    query_typed_route,
    query_typed_write,
    sanitize_graph,
)


ROOT = Path(__file__).resolve().parents[1]


class KnowledgeNavigationTests(unittest.TestCase):
    def test_allowlist_is_exact_and_protected_paths_are_absent(self) -> None:
        self.assertEqual(len(ACTIVE_MARKDOWN_ALLOWLIST), 12)
        for relative_path in ACTIVE_MARKDOWN_ALLOWLIST:
            self.assertTrue((ROOT / relative_path).is_file(), relative_path)
            self.assertFalse(any(relative_path.startswith(prefix) for prefix in PROTECTED_PREFIXES))
            self.assertNotIn("docs/user/", relative_path)
            self.assertNotIn("docs/reports/", relative_path)

    def test_graphifyignore_reincludes_only_the_declared_sources(self) -> None:
        manifest = (ROOT / ".graphifyignore").read_text(encoding="utf-8")
        self.assertIn("\n*\n", manifest)
        for relative_path in ACTIVE_MARKDOWN_ALLOWLIST:
            self.assertIn(f"!{relative_path}", manifest)
        for prefix in PROTECTED_PREFIXES:
            self.assertIn(f"/{prefix}", manifest)
        self.assertFalse((ROOT / "graphify-out").exists())

    def test_obsidian_pilot_config_is_bounded_and_portable(self) -> None:
        app_config = json.loads((ROOT / ".obsidian" / "app.json").read_text(encoding="utf-8"))
        self.assertTrue(app_config["useMarkdownLinks"])
        self.assertTrue(app_config["alwaysUpdateLinks"])
        self.assertTrue(app_config["promptDelete"])
        protected_filters = [f"{directory}/" for directory in ("inputs", "outputs", "backup")]
        self.assertEqual(
            app_config["userIgnoreFilters"],
            protected_filters + [".git/", ".agents/", ".codex/", "tools/", "tests/"],
        )
        community_plugins = json.loads(
            (ROOT / ".obsidian" / "community-plugins.json").read_text(encoding="utf-8")
        )
        self.assertEqual(community_plugins, [])
        core_plugins = json.loads(
            (ROOT / ".obsidian" / "core-plugins.json").read_text(encoding="utf-8")
        )
        for plugin in ("file-explorer", "global-search", "graph", "backlink", "properties"):
            self.assertTrue(core_plugins[plugin], plugin)
        self.assertFalse(core_plugins["sync"])
        self.assertFalse(core_plugins["publish"])
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".obsidian/workspace*.json", gitignore)

    def test_direct_baseline_records_three_clean_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "baseline" / "direct_baseline.json"
            result = build_direct_baseline(ROOT, output, iterations=3)
            self.assertEqual(set(result["profiles"]), {
                "resume_current_work",
                "change_document_route",
                "handle_video_task_state",
            })
            self.assertEqual(result["protected_path_reads"], 0)
            self.assertTrue(output.is_file())
            for profile in result["profiles"].values():
                self.assertEqual(profile["wrong_authority_selections"], [])
                self.assertEqual(profile["unresolved_local_links"], [])

    def test_graph_audit_rejects_protected_and_unexpected_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            graph_path = Path(temporary_directory) / "graph.json"
            graph_path.write_text(
                json.dumps({
                    "nodes": [
                        {"id": "allowed", "source_file": "AGENTS.md"},
                        {"id": "protected", "source_file": "inputs/private.md"},
                        {"id": "unexpected", "source_file": "docs/reports/report.md"},
                        {"id": "escape", "source_file": "../AGENTS.md"},
                    ]
                }),
                encoding="utf-8",
            )
            result = audit_graph(graph_path, ROOT)
            self.assertFalse(result["passed"])
            self.assertEqual(result["protected_path_nodes"], ["inputs/private.md"])
            self.assertIn("docs/reports/report.md", result["unexpected_markdown_sources"])
            self.assertIn("../AGENTS.md", result["external_markdown_paths"])

    def test_sanitizer_drops_untraceable_nodes_and_edges(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            raw_path = Path(temporary_directory) / "raw.json"
            clean_path = Path(temporary_directory) / "clean.json"
            raw_path.write_text(
                json.dumps({
                    "directed": False,
                    "multigraph": False,
                    "graph": {},
                    "nodes": [
                        {"id": "agent", "label": "Agent Router", "source_file": "AGENTS.md"},
                        {"id": "rules", "label": "Project Rules", "source_file": "PROJECT_RULES.md"},
                        {
                            "id": "handoff_section",
                            "label": "Resume Checkpoint",
                            "source_file": "SESSION_HANDOFF.md#resume-checkpoint",
                        },
                        {"id": "protected", "label": "Private", "source_file": "inputs/private.md"},
                    ],
                    "links": [
                        {
                            "source": "agent",
                            "target": "rules",
                            "relation": "routes_to",
                            "confidence": "EXTRACTED",
                            "source_file": "AGENTS.md",
                        },
                        {
                            "source": "agent",
                            "target": "rules",
                            "source_file": "AGENTS.md",
                        },
                        {
                            "source": "agent",
                            "target": "protected",
                            "relation": "references",
                            "confidence": "EXTRACTED",
                            "source_file": "AGENTS.md",
                        },
                        {
                            "source": "agent",
                            "target": "handoff_section",
                            "relation": "resumes_with",
                            "confidence": "EXTRACTED",
                            "source_file": "AGENTS.md",
                        },
                    ],
                }),
                encoding="utf-8",
            )
            result = sanitize_graph(raw_path, clean_path, ROOT)
            self.assertTrue(result["passed"])
            self.assertEqual(result["kept_nodes"], 3)
            self.assertEqual(result["kept_edges"], 2)
            clean_graph = json.loads(clean_path.read_text(encoding="utf-8"))
            section = next(node for node in clean_graph["nodes"] if node["id"] == "handoff_section")
            self.assertEqual(section["source_file"], "SESSION_HANDOFF.md")
            self.assertEqual(section["source_location"], "#resume-checkpoint")
            self.assertTrue(audit_graph(clean_path, ROOT)["passed"])

    def test_query_path_is_structured_and_uses_allowlisted_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            graph_path = Path(temporary_directory) / "graph.json"
            manifest_path = Path(temporary_directory) / "manifest.json"
            graph_path.write_text(
                json.dumps({
                    "directed": False,
                    "multigraph": False,
                    "graph": {},
                    "nodes": [
                        {"id": "resume", "label": "Resume Current Work", "source_file": "SESSION_HANDOFF.md"},
                        {"id": "rules", "label": "Project Rules", "source_file": "PROJECT_RULES.md"},
                        {"id": "router", "label": "Agent Router", "source_file": "AGENTS.md"},
                    ],
                    "links": [
                        {
                            "source": "resume",
                            "target": "rules",
                            "relation": "governed_by",
                            "confidence": "EXTRACTED",
                            "source_file": "SESSION_HANDOFF.md",
                        },
                        {
                            "source": "resume",
                            "target": "router",
                            "relation": "routed_by",
                            "confidence": "EXTRACTED",
                            "source_file": "SESSION_HANDOFF.md",
                        },
                    ],
                }),
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps({
                    relative_path: {
                        "semantic_hash": hashlib.md5((ROOT / relative_path).read_bytes()).hexdigest()
                    }
                    for relative_path in ACTIVE_MARKDOWN_ALLOWLIST
                }),
                encoding="utf-8",
            )
            result = query_graph(graph_path, ROOT, manifest_path, "resume current work")
            self.assertTrue(result["passed"])
            self.assertEqual(
                set(result["selected_sources"]),
                {"AGENTS.md", "PROJECT_RULES.md", "SESSION_HANDOFF.md"},
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["SESSION_HANDOFF.md"]["semantic_hash"] = "0" * 32
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest is stale"):
                query_graph(graph_path, ROOT, manifest_path, "resume current work")

    def test_manifest_audit_detects_stale_allowlisted_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "manifest.json"
            manifest = {
                relative_path: {
                    "semantic_hash": hashlib.md5((ROOT / relative_path).read_bytes()).hexdigest()
                }
                for relative_path in ACTIVE_MARKDOWN_ALLOWLIST
            }
            manifest["SESSION_HANDOFF.md"]["semantic_hash"] = "0" * 32
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = audit_manifest(manifest_path, ROOT)
            self.assertFalse(result["passed"])
            self.assertEqual(result["stale_sources"], ["SESSION_HANDOFF.md"])

    def test_typed_route_graph_selects_only_one_hop_exact_documents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            graph_path = Path(temporary_directory) / "typed-route-graph.json"
            build = build_typed_route_graph(ROOT, graph_path)
            self.assertTrue(build["passed"])
            self.assertGreater(build["documents"], 3)

            resume = query_typed_route(graph_path, ROOT, "resume_current_work")
            self.assertTrue(resume["passed"])
            self.assertEqual(
                resume["selected_documents"],
                ["AGENTS.md", "PROJECT_RULES.md", "SESSION_HANDOFF.md"],
            )
            self.assertEqual(resume["traversal_hops"], 1)
            self.assertEqual(resume["document_node_expansion"], 0)
            self.assertEqual(resume["graph_document_contents_loaded"], 0)

            architecture = query_typed_route(
                graph_path,
                ROOT,
                "change_document_route",
                selector_value="document registry and navigation capability",
                selected_paths=["docs/agent/RECONSTRUCTION_MAP.md"],
            )
            self.assertTrue(architecture["passed"])
            self.assertEqual(set(architecture["selected_documents"]), {
                "AGENTS.md",
                "PROJECT_RULES.md",
                "SESSION_HANDOFF.md",
                "docs/agent/DOCUMENT_REGISTRY.md",
                "docs/agent/RECONSTRUCTION_MAP.md",
            })
            self.assertNotIn(
                "docs/agent/WORKFLOW_FOUNDATION.md",
                architecture["selected_documents"],
            )

    def test_typed_route_graph_keeps_exact_user_item_out_of_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            graph_path = Path(temporary_directory) / "typed-route-graph.json"
            build_typed_route_graph(ROOT, graph_path)
            state_route = query_typed_route(
                graph_path,
                ROOT,
                "handle_video_task_state",
                selector_value="the user-designated synthetic state",
                selected_paths=["outputs/synthetic/state.json"],
            )
            self.assertTrue(state_route["passed"])
            self.assertEqual(
                state_route["exact_selected_items_not_indexed"],
                ["outputs/synthetic/state.json"],
            )
            self.assertNotIn(
                "outputs/synthetic/state.json",
                state_route["selected_documents"],
            )
            with self.assertRaisesRegex(ValueError, "outside the workspace"):
                query_typed_route(
                    graph_path,
                    ROOT,
                    "change_document_route",
                    selector_value="malicious relative path",
                    selected_paths=["../AGENTS.md"],
                )

    def test_typed_route_graph_fails_closed_when_stale_or_recursive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            graph_path = Path(temporary_directory) / "typed-route-graph.json"
            build_typed_route_graph(ROOT, graph_path)
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
            graph["graph"]["navigation_contract"]["source_sha256"]["AGENTS.md"] = "0" * 64
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            self.assertFalse(audit_typed_route_graph(graph_path, ROOT)["passed"])
            with self.assertRaisesRegex(ValueError, "stale or invalid"):
                query_typed_route(graph_path, ROOT, "resume_current_work")

            build_typed_route_graph(ROOT, graph_path)
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
            graph["links"].append({
                "source": "document:doc.registry",
                "target": "document:doc.rebuild_plan",
                "relation": "requires",
                "confidence": "EXTRACTED",
                "source_file": "AGENTS.md",
            })
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            audit = audit_typed_route_graph(graph_path, ROOT)
            self.assertFalse(audit["passed"])
            self.assertTrue(audit["invalid_edges"])

    def test_typed_write_route_resolves_single_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            graph_path = Path(temporary_directory) / "typed-route-graph.json"
            build_typed_route_graph(ROOT, graph_path)
            result = query_typed_write(graph_path, ROOT, "document_classification")
            self.assertTrue(result["passed"])
            self.assertEqual(
                result["write_targets"],
                ["docs/agent/DOCUMENT_REGISTRY.md"],
            )

    def test_typed_route_token_comparison_keeps_direct_as_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            graph_path = directory / "typed-route-graph.json"
            current_baseline_path = directory / "current-baseline.json"
            historical_baseline_path = directory / "historical-baseline.json"
            semantic_comparison_path = directory / "semantic-comparison.json"
            output_path = directory / "typed-comparison.json"
            build_typed_route_graph(ROOT, graph_path)
            current = build_direct_baseline(ROOT, current_baseline_path, iterations=1)

            historical = json.loads(json.dumps(current))
            historical_tokens = {
                "resume_current_work": 5175,
                "change_document_route": 8848,
                "handle_video_task_state": 8186,
            }
            semantic_tokens = {
                "resume_current_work": 26229,
                "change_document_route": 23045,
                "handle_video_task_state": 8226,
            }
            for profile, tokens in historical_tokens.items():
                historical["profiles"][profile]["total_estimated_tokens"] = tokens
            historical_baseline_path.write_text(json.dumps(historical), encoding="utf-8")
            semantic_comparison_path.write_text(
                json.dumps({
                    "profiles": {
                        profile: {"graph_total_estimated_tokens": tokens}
                        for profile, tokens in semantic_tokens.items()
                    }
                }),
                encoding="utf-8",
            )

            result = compare_typed_routes(
                graph_path,
                ROOT,
                current_baseline_path,
                historical_baseline_path,
                semantic_comparison_path,
                output_path,
            )
            self.assertTrue(result["exact_selection_passed"])
            self.assertFalse(result["token_benefit_vs_direct_passed"])
            self.assertFalse(result["passed"])
            self.assertEqual(
                result["default_route_decision"],
                "direct_default_typed_graph_optional",
            )
            self.assertTrue(output_path.is_file())
            for profile in result["profiles"].values():
                query_tokens = profile["compact_query_estimated_tokens"]
                self.assertGreater(query_tokens, 0)
                self.assertEqual(profile["historical_typed_delta_vs_direct"], query_tokens)
                self.assertEqual(profile["current_typed_delta_vs_direct"], query_tokens)
                self.assertTrue(profile["exact_selection_passed"])
                self.assertFalse(profile["token_benefit_vs_direct_passed"])
                self.assertTrue(
                    set(profile["compact_query_payload"]["read_delta"])
                    .isdisjoint({"AGENTS.md", "PROJECT_RULES.md", "SESSION_HANDOFF.md"})
                )


if __name__ == "__main__":
    unittest.main()
