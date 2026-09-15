import unittest

from daily_arxiv.daily_arxiv.check_stats import normalize_arxiv_id, normalize_title


class DuplicateNormalizationTests(unittest.TestCase):
    def test_arxiv_versions_and_urls_share_the_same_id(self):
        self.assertEqual("2609.12345", normalize_arxiv_id("https://arxiv.org/abs/2609.12345v2"))
        self.assertEqual("2609.12345", normalize_arxiv_id("2609.12345"))

    def test_title_normalization_ignores_case_spacing_and_punctuation(self):
        self.assertEqual(
            normalize_title("LLM-Based  Optimizer: A Study"),
            normalize_title("llm based optimizer — a study"),
        )


if __name__ == "__main__":
    unittest.main()
