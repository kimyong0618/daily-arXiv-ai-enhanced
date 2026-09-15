"""Generate an email-client-friendly HTML research digest."""

from __future__ import annotations

import argparse
import html
from datetime import date
from pathlib import Path
from typing import Any

from .filter_papers import read_jsonl


RESEARCH_DIRECTIONS = "CO / LLM / EC / RL / Automated Algorithm Design"


def _escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _authors(paper: dict[str, Any]) -> str:
    authors = paper.get("authors", [])
    return ", ".join(map(str, authors)) if isinstance(authors, list) else str(authors or "")


def _published(paper: dict[str, Any], digest_date: str) -> str:
    value = str(paper.get("published", "")).strip()
    return value[:10] if value else digest_date


def _summary(paper: dict[str, Any]) -> str:
    ai = paper.get("AI") if isinstance(paper.get("AI"), dict) else {}
    fields = [ai.get("tldr"), ai.get("method"), ai.get("result")]
    parts = [str(value).strip() for value in fields if value and str(value).strip()]
    return " ".join(parts) if parts else str(paper.get("summary", "")).strip()


def _truncate(value: str, limit: int = 1500) -> str:
    return value if len(value) <= limit else value[:limit].rstrip() + "…"


def _paper_card(paper: dict[str, Any], digest_date: str, highly_relevant: bool) -> str:
    relevance = paper.get("relevance", {})
    score = int(relevance.get("score", 0))
    topics = " / ".join(map(str, relevance.get("topics", []))) or "Research"
    title_zh = str(relevance.get("title_zh", "")).strip()
    categories = " / ".join(map(str, paper.get("categories", [])))
    border = "#dc2626" if highly_relevant else "#2563eb"
    badge = "#dc2626" if highly_relevant else "#2563eb"
    label = "高度相关" if highly_relevant else "相关"
    abstract = str(paper.get("summary", "")).strip()
    abstract_block = ""
    if abstract:
        abstract_block = (
            '<p style="margin:12px 0 4px;color:#64748b;font-size:12px;font-weight:700;">原始 Abstract</p>'
            f'<p style="margin:0;color:#64748b;font-size:13px;line-height:1.6;">{_escape(_truncate(abstract))}</p>'
        )

    return f"""
<div style="background:#ffffff;border:1px solid #e2e8f0;border-left:4px solid {border};border-radius:8px;margin:0 0 18px;padding:20px;">
  <div style="margin-bottom:10px;">
    <span style="display:inline-block;background:{badge};color:#ffffff;border-radius:999px;padding:4px 9px;font-size:12px;font-weight:700;">{score} · {label}</span>
    <span style="display:inline-block;color:#475569;margin-left:8px;font-size:12px;">{_escape(topics)}</span>
  </div>
  <h2 style="color:#0f172a;font-size:19px;line-height:1.35;margin:0 0 7px;">{_escape(paper.get('title'))}</h2>
  {f'<p style="color:#334155;font-size:15px;margin:0 0 10px;"><strong>中文标题：</strong>{_escape(title_zh)}</p>' if title_zh else ''}
  <p style="color:#64748b;font-size:12px;line-height:1.6;margin:0 0 12px;">{_escape(_authors(paper))}<br>分类：{_escape(categories)} · 发布时间：{_escape(_published(paper, digest_date))}</p>
  <p style="color:#0f172a;font-size:14px;line-height:1.65;margin:0 0 10px;"><strong>为什么推荐：</strong>{_escape(relevance.get('reason'))}</p>
  <p style="color:#0f172a;font-size:14px;line-height:1.7;margin:0;"><strong>中文摘要：</strong>{_escape(_summary(paper))}</p>
  {abstract_block}
  <p style="margin:15px 0 0;font-size:13px;"><a href="{_escape(paper.get('abs'))}" style="color:#2563eb;text-decoration:none;">arXiv Abstract</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="{_escape(paper.get('pdf'))}" style="color:#2563eb;text-decoration:none;">PDF</a></p>
</div>"""


def generate_html(
    papers: list[dict[str, Any]],
    digest_date: str,
    scanned_count: int,
    window_days: int = 1,
) -> str:
    papers = sorted(papers, key=lambda paper: paper.get("relevance", {}).get("score", 0), reverse=True)
    high = [paper for paper in papers if paper.get("relevance", {}).get("score", 0) >= 80]
    regular = [paper for paper in papers if paper.get("relevance", {}).get("score", 0) < 80]

    if papers:
        sections = []
        if high:
            sections.append(
                '<h1 style="font-size:18px;color:#b91c1c;margin:24px 0 12px;">🔥 Highly Relevant</h1>'
                + "".join(_paper_card(paper, digest_date, True) for paper in high)
            )
        if regular:
            sections.append(
                '<h1 style="font-size:18px;color:#1d4ed8;margin:24px 0 12px;">⭐ Relevant</h1>'
                + "".join(_paper_card(paper, digest_date, False) for paper in regular)
            )
        content = "".join(sections)
    else:
        content = f"""
<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;margin-top:24px;padding:28px;text-align:center;">
  <p style="color:#334155;font-size:16px;line-height:1.7;margin:0;">近{window_days}日未发现与 CO / LLM / EC / RL 高度相关的新论文。</p>
</div>"""

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="background:#f8fafc;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',Arial,sans-serif;">
<div style="max-width:800px;margin:0 auto;padding:24px 14px 40px;">
  <div style="background:#0f172a;border-radius:10px;padding:24px;color:#ffffff;">
    <p style="font-size:12px;letter-spacing:.08em;margin:0 0 8px;color:#cbd5e1;">{window_days}-DAY ARXIV RESEARCH DIGEST</p>
    <h1 style="font-size:24px;line-height:1.3;margin:0 0 16px;">{_escape(digest_date)}</h1>
    <table role="presentation" style="border-collapse:collapse;width:100%;color:#ffffff;font-size:13px;"><tr>
      <td style="padding:4px 12px 4px 0;">今日扫描：<strong>{scanned_count}</strong></td>
      <td style="padding:4px 12px 4px 0;">近{window_days}日相关：<strong>{len(papers)}</strong></td>
      <td style="padding:4px 0;">近{window_days}日高度相关：<strong>{len(high)}</strong></td>
    </tr></table>
    <p style="font-size:12px;line-height:1.6;margin:14px 0 0;color:#cbd5e1;">研究方向：{RESEARCH_DIRECTIONS}</p>
  </div>
  {content}
  <p style="color:#94a3b8;font-size:11px;text-align:center;margin:24px 0 0;">由 daily-arXiv-ai-enhanced 自动生成</p>
</div></body></html>"""


def generate_plain_text(
    papers: list[dict[str, Any]], digest_date: str, scanned_count: int, window_days: int = 1
) -> str:
    lines = [
        f"近{window_days}日 arXiv 论文速递 | {digest_date}",
        f"今日扫描：{scanned_count} 近{window_days}日相关：{len(papers)} 近{window_days}日高度相关：{sum(p.get('relevance', {}).get('score', 0) >= 80 for p in papers)}",
        f"研究方向：{RESEARCH_DIRECTIONS}",
        "",
    ]
    if not papers:
        lines.append(f"近{window_days}日未发现与 CO / LLM / EC / RL 高度相关的新论文。")
    for paper in papers:
        relevance = paper.get("relevance", {})
        lines.extend(
            [
                f"[{relevance.get('score', 0)}] {paper.get('title', '')}",
                f"中文标题：{relevance.get('title_zh', '')}",
                f"Topics: {' / '.join(relevance.get('topics', []))}",
                f"推荐理由：{relevance.get('reason', '')}",
                f"中文摘要：{_summary(paper)}",
                f"Abstract: {paper.get('abs', '')}",
                f"PDF: {paper.get('pdf', '')}",
                "",
            ]
        )
    return "\n".join(lines)


def save_html(path: str | Path, content: str) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Filtered JSONL file")
    parser.add_argument("--output", required=True, help="Output HTML file")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--scanned-count", required=True, type=int)
    args = parser.parse_args()
    papers = read_jsonl(args.data)
    save_html(args.output, generate_html(papers, args.date, args.scanned_count))


if __name__ == "__main__":
    main()
