"""Run relevance filtering and generate the daily email artifacts."""

from __future__ import annotations

import argparse
import os
import re
from datetime import date, timedelta
from pathlib import Path

from .filter_papers import create_llm, filter_papers, get_threshold, read_jsonl, write_jsonl
from .generate_email import generate_html, generate_plain_text, save_html


DEFAULT_DIGEST_DAYS = 7


def _paper_key(paper: dict) -> tuple[str, str]:
    paper_id = str(paper.get("id", "")).strip().lower().rstrip("/").rsplit("/", 1)[-1]
    paper_id = re.sub(r"v\d+$", "", paper_id)
    title = " ".join(re.sub(r"[^\w]+", " ", str(paper.get("title", "")).casefold()).split())
    return paper_id, title


def collect_rolling_digest(
    current_papers: list[dict], output_dir: Path, digest_date: str, days: int
) -> list[dict]:
    """Combine current and prior filtered files without duplicating a paper."""
    if days < 1:
        raise ValueError("DIGEST_DAYS must be at least 1")

    combined = list(current_papers)
    end_date = date.fromisoformat(digest_date)
    for offset in range(1, days):
        history_path = output_dir / f"{end_date - timedelta(days=offset)}_filtered.jsonl"
        if history_path.exists():
            combined.extend(read_jsonl(history_path))

    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    unique = []
    for paper in combined:
        paper_id, title = _paper_key(paper)
        if (paper_id and paper_id in seen_ids) or (title and title in seen_titles):
            continue
        unique.append(paper)
        if paper_id:
            seen_ids.add(paper_id)
        if title:
            seen_titles.add(title)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", help="AI-enhanced JSONL; omit with --empty")
    parser.add_argument("--scanned-data", help="Raw crawl JSONL used only for the scanned-paper count")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--empty", action="store_true", help="Generate a zero-paper digest without LLM calls")
    parser.add_argument("--max-workers", type=int, default=int(os.environ.get("RELEVANCE_MAX_WORKERS", "1")))
    parser.add_argument("--digest-days", type=int, default=int(os.environ.get("DIGEST_DAYS", DEFAULT_DIGEST_DAYS)))
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
    digest_papers = collect_rolling_digest(relevant, output_dir, args.date, args.digest_days)

    write_jsonl(filtered_path, relevant)
    save_html(html_path, generate_html(digest_papers, args.date, scanned_count, args.digest_days))
    plain_path.write_text(
        generate_plain_text(digest_papers, args.date, scanned_count, args.digest_days),
        encoding="utf-8",
    )
    print(f"Scanned {scanned_count} papers; classified {len(papers)}; selected {len(relevant)}")
    print(f"Rolling {args.digest_days}-day digest contains {len(digest_papers)} unique papers")
    print(f"Saved {filtered_path}, {html_path}, and {plain_path}")


if __name__ == "__main__":
    main()
