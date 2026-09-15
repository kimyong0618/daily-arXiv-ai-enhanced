import json
import tempfile
import unittest
from pathlib import Path

from email_digest.run_digest import collect_rolling_digest


class RollingDigestTests(unittest.TestCase):
    def test_combines_seven_days_and_deduplicates_id_versions_and_titles(self):
        current = [{"id": "2609.00003", "title": "New Paper"}]
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            history = [
                {"id": "2609.00003v2", "title": "New Paper (revised)"},
                {"id": "2609.00002", "title": "Historical Paper"},
                {"id": "different-id", "title": "  historical-paper! "},
            ]
            path = output_dir / "2026-09-14_filtered.jsonl"
            path.write_text(
                "\n".join(json.dumps(paper) for paper in history) + "\n",
                encoding="utf-8",
            )

            result = collect_rolling_digest(current, output_dir, "2026-09-15", 7)

        self.assertEqual(["2609.00003", "2609.00002"], [paper["id"] for paper in result])


if __name__ == "__main__":
    unittest.main()
