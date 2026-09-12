"""Classify AI-enhanced arXiv papers against the configured research interests."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Iterable

from ai.runtime import build_chat_openai_kwargs


DEFAULT_THRESHOLD = 60
ALLOWED_TOPICS = {
    "CO",
    "LLM",
    "EC",
    "RL",
    "Automated Algorithm Design",
    "Automated Heuristic Design",
    "Evolutionary Algorithm",
    "Genetic Algorithm",
    "Genetic Programming",
    "Metaheuristic",
    "Hyper-heuristic",
    "Neural CO",
    "Neural Combinatorial Optimization",
    "Learning to Optimize",
    "Algorithm Generation",
    "Algorithm Discovery",
    "Algorithm Portfolio",
    "LLM-as-Optimizer",
    "LLM-as-Designer",
    "LLM-as-Controller",
    "LLM Agent",
    "Planning",
    "Search",
    "Optimization",
}

SYSTEM_PROMPT = """You are a conservative research paper relevance classifier.

The user's core research interests are:
- combinatorial optimization (CO)
- large language models (LLM)
- evolutionary computation (EC), evolutionary/genetic algorithms and genetic programming
- reinforcement learning (RL), especially for optimization
- automated algorithm, heuristic, metaheuristic and hyper-heuristic design
- neural combinatorial optimization and learning to optimize
- algorithm generation, discovery, evolution and portfolios
- LLM agents used as optimizers, designers or controllers
- search, optimization and planning work in which LLMs play a substantive role

Particularly value intersections such as LLM+CO, LLM+EC, LLM+RL, EC+CO,
RL+CO, and automatic generation, design or improvement of optimization algorithms.

Judge the paper's main contribution using only its title and abstract. A passing
mention in background or references is not relevant. Be conservative: reject
pure CV, pure NLP/linguistics, model compression and visual generation papers
unless their main contribution clearly connects to the interests above.

Scoring:
- 90-100: directly addresses a core intersection or automated optimization-algorithm design
- 80-89: strongly relevant to a core research direction
- 60-79: relevant and potentially useful
- 40-59: only loosely related
- 0-39: irrelevant

Return strict JSON only, without Markdown or commentary:
{"relevant": true, "score": 85, "topics": ["LLM", "EC", "CO"],
 "reason": "简短中文原因", "title_zh": "准确简洁的中文标题"}

The reason must be concise Chinese. Use short canonical topic labels. Set
relevant=false when score is below the configured threshold."""


def get_threshold(value: str | int | None = None) -> int:
    raw = value if value is not None else os.environ.get("RELEVANCE_THRESHOLD", DEFAULT_THRESHOLD)
    try:
        threshold = int(raw)
    except (TypeError, ValueError) as error:
        raise ValueError("RELEVANCE_THRESHOLD must be an integer from 0 to 100") from error
    if not 0 <= threshold <= 100:
        raise ValueError("RELEVANCE_THRESHOLD must be between 0 and 100")
    return threshold


def build_prompt(paper: dict[str, Any], threshold: int) -> str:
    return (
        f"Configured relevance threshold: {threshold}\n\n"
        f"Title: {paper.get('title', '').strip()}\n\n"
        f"Abstract: {paper.get('summary', '').strip()}"
    )


def _message_text(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


def parse_classifier_json(raw: str, threshold: int) -> dict[str, Any]:
    """Parse strict JSON while tolerating common Markdown fences and surrounding text."""
    text = raw.strip().lstrip("\ufeff")
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise
        payload = json.loads(text[start : end + 1])

    if not isinstance(payload, dict):
        raise ValueError("Classifier response must be a JSON object")

    try:
        score = max(0, min(100, int(round(float(payload.get("score", 0))))))
    except (TypeError, ValueError):
        score = 0

    raw_topics = payload.get("topics", [])
    if not isinstance(raw_topics, list):
        raw_topics = []
    topics = []
    for topic in raw_topics:
        label = str(topic).strip()
        if label and label in ALLOWED_TOPICS and label not in topics:
            topics.append(label)

    return {
        "relevant": score >= threshold,
        "score": score,
        "topics": topics[:6],
        "reason": str(payload.get("reason", "")).strip() or "模型未提供推荐理由",
        "title_zh": str(payload.get("title_zh", "")).strip(),
    }


def classify_paper(llm: Any, paper: dict[str, Any], threshold: int) -> dict[str, Any]:
    response = llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", build_prompt(paper, threshold)),
        ]
    )
    try:
        return parse_classifier_json(_message_text(response), threshold)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        print(
            f"Invalid classifier JSON for {paper.get('id', 'unknown')}: {error}",
            file=sys.stderr,
        )
        return {
            "relevant": False,
            "score": 0,
            "topics": [],
            "reason": "相关性结果解析失败，已按保守策略排除",
            "title_zh": "",
            "classification_error": str(error),
        }


def create_llm() -> Any:
    # Lazy import keeps JSON/HTML tooling usable in lightweight local test environments.
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        **build_chat_openai_kwargs(
            model_name=os.environ.get("MODEL_NAME", "gpt-4o-mini"),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", ""),
        )
    )


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    papers = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                papers.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL at line {line_number}: {path}") from error
    return papers


def write_jsonl(path: str | Path, papers: Iterable[dict[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for paper in papers:
            handle.write(json.dumps(paper, ensure_ascii=False) + "\n")


def filter_papers(
    papers: list[dict[str, Any]],
    llm: Any,
    threshold: int,
    max_workers: int = 1,
) -> list[dict[str, Any]]:
    """Classify all papers and return passing records sorted by descending score."""
    classified: list[dict[str, Any] | None] = [None] * len(papers)
    request_errors: list[str] = []

    def process(index: int, paper: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        result = classify_paper(llm, paper, threshold)
        enriched = dict(paper)
        enriched["relevance"] = result
        return index, enriched

    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
        futures = {executor.submit(process, index, paper): index for index, paper in enumerate(papers)}
        for future in as_completed(futures):
            index = futures[future]
            try:
                result_index, paper = future.result()
                classified[result_index] = paper
            except Exception as error:
                print(
                    f"Relevance classification failed for {papers[index].get('id', index)}: {error}",
                    file=sys.stderr,
                )
                request_errors.append(str(error))

    if request_errors:
        raise RuntimeError(
            f"{len(request_errors)} relevance request(s) failed; first error: {request_errors[0]}"
        )

    relevant = [
        paper
        for paper in classified
        if paper is not None and paper["relevance"]["score"] >= threshold
    ]
    return sorted(relevant, key=lambda paper: paper["relevance"]["score"], reverse=True)


def default_filtered_path(input_path: str | Path) -> Path:
    name = Path(input_path).name
    match = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    if not match:
        raise ValueError("Input filename must start with YYYY-MM-DD")
    return Path(input_path).parent / f"{match.group(1)}_filtered.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="AI-enhanced JSONL file")
    parser.add_argument("--output", help="Filtered JSONL path")
    parser.add_argument("--threshold", type=int)
    parser.add_argument("--max-workers", type=int, default=1)
    args = parser.parse_args()

    threshold = get_threshold(args.threshold)
    papers = read_jsonl(args.data)
    relevant = filter_papers(papers, create_llm(), threshold, args.max_workers)
    output = Path(args.output) if args.output else default_filtered_path(args.data)
    write_jsonl(output, relevant)
    print(f"Relevant papers: {len(relevant)}/{len(papers)} (threshold={threshold})")
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
