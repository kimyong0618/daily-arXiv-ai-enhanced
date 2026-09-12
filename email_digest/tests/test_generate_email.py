import unittest

from email_digest.generate_email import generate_html, generate_plain_text


class GenerateEmailTests(unittest.TestCase):
    def setUp(self):
        self.paper = {
            "id": "2609.00001",
            "title": "LLM < Optimizer",
            "authors": ["Alice", "Bob"],
            "categories": ["cs.AI", "math.OC"],
            "published": "2026-09-12T00:00:00+00:00",
            "summary": "Original abstract",
            "abs": "https://arxiv.org/abs/2609.00001",
            "pdf": "https://arxiv.org/pdf/2609.00001",
            "AI": {"tldr": "中文总结", "method": "中文方法", "result": "中文结果"},
            "relevance": {
                "score": 92,
                "topics": ["LLM", "CO"],
                "reason": "使用LLM设计组合优化算法",
                "title_zh": "大模型优化器",
            },
        }

    def test_html_contains_counts_cards_links_and_escaped_content(self):
        result = generate_html([self.paper], "2026-09-12", 132)
        self.assertIn("扫描论文：<strong>132</strong>", result)
        self.assertIn("Highly Relevant", result)
        self.assertIn("LLM &lt; Optimizer", result)
        self.assertIn("中文总结 中文方法 中文结果", result)
        self.assertIn("https://arxiv.org/pdf/2609.00001", result)

    def test_empty_digest_has_required_message_and_plain_fallback(self):
        html = generate_html([], "2026-09-12", 0)
        plain = generate_plain_text([], "2026-09-12", 0)
        expected = "今日未发现与 CO / LLM / EC / RL 高度相关的新论文。"
        self.assertIn(expected, html)
        self.assertIn(expected, plain)


if __name__ == "__main__":
    unittest.main()
