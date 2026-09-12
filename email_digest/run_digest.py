"""Run relevance filtering and generate the daily email artifacts."""

from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from .filter_papers import create_llm, filter_papers, get_threshold, read_jsonl, write_jsonl
from .generate_email import generate_html, generate_plain_text, save_html


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", help="AI-enhanced JSONL; omit with --empty")
    parser.add_argument("--scanned-data", help="Raw crawl JSONL used only for the scanned-paper count")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--empty", action="store_true", help="Generate a zero-paper digest without LLM calls")
    parser.add_argument("--max-workers", type=int, default=int(os.environ.get("RELEVANCE_MAX_WORKERS", "1")))
    args = parser.parse_args()

    if not args.empty and not args.data:
        parser.error("--data is required unless --empty is used")

    output_dir = Path(args.output_dir)
    filtered_path = output_dir / f"{args.date}_filtered.jsonl"
    html_path = output_dir / f"{args.date}_email.html"
    plain_path = output_dir / f"{args.date}_email.txt"

    if args.empty:
        papers: list[dict] = []
        relevant: list[dict] = []
    else:
        papers = read_jsonl(args.data)
        relevant = filter_papers(
            papers,
            create_llm(),
            get_threshold(),
            args.max_workers,
        )

    scanned_count = len(read_jsonl(args.scanned_data)) if args.scanned_data else len(papers)

    write_jsonl(filtered_path, relevant)
    save_html(html_path, generate_html(relevant, args.date, scanned_count))
    plain_path.write_text(generate_plain_text(relevant, args.date, scanned_count), encoding="utf-8")
    print(f"Scanned {scanned_count} papers; classified {len(papers)}; selected {len(relevant)}")
    print(f"Saved {filtered_path}, {html_path}, and {plain_path}")


if __name__ == "__main__":
    main()
