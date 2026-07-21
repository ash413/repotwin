import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from investigator.nl_query import answer_question


def sample_graph():
    graph = nx.DiGraph()
    graph.add_node("redis", type="cache", label="Redis")
    graph.add_node(
        "app.services.session_store",
        type="module",
        label="session_store",
        routes=[{"method": "POST", "path": "/login", "function": "login"}],
    )
    graph.add_edge(
        "app.services.session_store",
        "redis",
        type="calls",
        evidence=[{"file": "app/services/session_store.py", "line": 8, "snippet": "redis.get(key)"}],
    )
    return graph


class AnswerQuestionTests(unittest.TestCase):
    def test_uses_deterministic_narrative_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            result = answer_question(sample_graph(), "What breaks if I remove Redis?")

        self.assertEqual(result["resolved_node"], "redis")
        self.assertEqual(result["narrative_source"], "deterministic")
        self.assertEqual(result["report"]["risk_level"], "high")
        self.assertEqual(result["report"]["directly_affected"][0]["label"], "session_store")

    def test_uses_gpt_5_6_narrative_when_configured(self):
        fake_client = MagicMock()
        fake_client.responses.create.return_value = SimpleNamespace(output_text="Grounded migration brief")
        fake_module = SimpleNamespace(OpenAI=MagicMock(return_value=fake_client))

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True), patch.dict(
            sys.modules, {"openai": fake_module}
        ):
            result = answer_question(sample_graph(), "What breaks if I remove Redis?")

        self.assertEqual(result["narrative"], "Grounded migration brief")
        self.assertEqual(result["narrative_source"], "gpt-5.6")
        request = fake_client.responses.create.call_args.kwargs
        self.assertEqual(request["model"], "gpt-5.6-sol")
        self.assertEqual(request["reasoning"], {"effort": "none"})
        self.assertIn("redis", request["input"])

    def test_falls_back_if_openai_is_unavailable(self):
        fake_client = MagicMock()
        fake_client.responses.create.side_effect = RuntimeError("offline")
        fake_module = SimpleNamespace(OpenAI=MagicMock(return_value=fake_client))

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True), patch.dict(
            sys.modules, {"openai": fake_module}
        ):
            result = answer_question(sample_graph(), "What breaks if I remove Redis?")

        self.assertEqual(result["narrative_source"], "deterministic")
        self.assertIn("directly affects", result["narrative"])


if __name__ == "__main__":
    unittest.main()
