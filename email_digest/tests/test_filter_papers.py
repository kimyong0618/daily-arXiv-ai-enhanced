import unittest

from email_digest.filter_papers import filter_papers, parse_classifier_json


class Response:
    def __init__(self, content):
        self.content = content


class FakeLlm:
    def __init__(self, responses):
        self.responses = iter(responses)

    def invoke(self, _messages):
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return Response(response)


class ClassifierJsonTests(unittest.TestCase):
    def test_markdown_fence_is_tolerated_and_threshold_is_authoritative(self):
        parsed = parse_classifier_json(
            '```json\n{"relevant": false, "score": 85, "topics": ["LLM", "CO"], '
            '"reason": "直接研究LLM组合优化", "title_zh": "测试标题"}\n```',
            60,
        )
        self.assertTrue(parsed["relevant"])
        self.assertEqual(85, parsed["score"])
        self.assertEqual(["LLM", "CO"], parsed["topics"])

    def test_invalid_json_fails_closed_without_aborting_batch(self):
        papers = [{"id": "1", "title": "Paper", "summary": "Abstract"}]
        self.assertEqual([], filter_papers(papers, FakeLlm(["not json"]), 60))

    def test_relevant_papers_are_sorted_and_below_threshold_is_removed(self):
        papers = [
            {"id": "1", "title": "A", "summary": "A"},
            {"id": "2", "title": "B", "summary": "B"},
            {"id": "3", "title": "C", "summary": "C"},
        ]
        responses = [
            '{"score": 65, "topics": ["RL"], "reason": "相关", "title_zh": "甲"}',
            '{"score": 92, "topics": ["LLM", "EC"], "reason": "高度相关", "title_zh": "乙"}',
            '{"score": 59, "topics": ["Optimization"], "reason": "弱相关", "title_zh": "丙"}',
        ]
        filtered = filter_papers(papers, FakeLlm(responses), 60)
        self.assertEqual(["2", "1"], [paper["id"] for paper in filtered])

    def test_llm_request_failure_fails_the_batch(self):
        papers = [{"id": "1", "title": "Paper", "summary": "Abstract"}]
        with self.assertRaisesRegex(RuntimeError, "relevance request"):
            filter_papers(papers, FakeLlm([ConnectionError("offline")]), 60)


if __name__ == "__main__":
    unittest.main()
