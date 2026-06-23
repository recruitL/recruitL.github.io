#!/usr/bin/env python3
"""Collect, rank, analyze, and render a daily research paper watch page."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import email.utils
import html
import json
import os
import re
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.message import EmailMessage
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - GitHub Actions uses modern Python.
    ZoneInfo = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "paper_watch.json"
DEFAULT_PREFERENCES = ROOT / "config" / "paper_preferences.json"
DATA_DIR = ROOT / "_data" / "paper_watch"
PAPERS_DIR = ROOT / "papers"
REVIEWS_DIR = ROOT / "_paper_reviews"
HISTORY_PATH = DATA_DIR / "history.json"
LATEST_PATH = DATA_DIR / "latest.json"
USER_AGENT = "recruitL-paper-watch/0.1 (https://recruitl.github.io)"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}
DC_NS = "{http://purl.org/dc/elements/1.1/}"


@dataclasses.dataclass
class Paper:
    uid: str
    title: str
    authors: list[str]
    abstract: str
    url: str
    source: str
    source_kind: str
    published: dt.datetime | None = None
    updated: dt.datetime | None = None
    categories: list[str] = dataclasses.field(default_factory=list)
    doi: str = ""
    journal: str = ""
    score: int = 0
    priority: str = "watch"
    area: str = "related"
    tags: list[str] = dataclasses.field(default_factory=list)
    noise_tags: list[str] = dataclasses.field(default_factory=list)
    matched_keywords: list[str] = dataclasses.field(default_factory=list)
    analysis: dict[str, str] = dataclasses.field(default_factory=dict)
    ai_blocked: bool = False


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_preferences(config: dict[str, Any]) -> dict[str, Any]:
    configured = config.get("preferences_path")
    path = ROOT / configured if configured else DEFAULT_PREFERENCES
    if not path.exists():
        return {
            "keep_title_patterns": [],
            "reject_title_patterns": [],
            "block_title_patterns": [],
            "keyword_weights": {},
            "tag_weights": {},
            "feedback_history": [],
        }
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def local_tz(config: dict[str, Any]) -> dt.tzinfo:
    tz_name = config.get("timezone", "Asia/Shanghai")
    if ZoneInfo is not None:
        return ZoneInfo(tz_name)
    return dt.timezone(dt.timedelta(hours=8), name=tz_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--date", help="Report date in YYYY-MM-DD, local timezone.")
    parser.add_argument("--lookback-days", type=int)
    parser.add_argument("--email", action="store_true", help="Send email after rendering.")
    parser.add_argument("--email-only", action="store_true", help="Send email from _data/paper_watch/latest.json without fetching.")
    parser.add_argument("--no-ai", action="store_true", help="Skip OpenAI analysis even if configured.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and rank without writing files.")
    parser.add_argument("--limit", type=int, help="Override max rendered papers.")
    return parser.parse_args()


def build_window(
    report_date: dt.date,
    tz: dt.tzinfo,
    lookback_days: int,
) -> tuple[dt.datetime, dt.datetime]:
    start_date = report_date - dt.timedelta(days=max(lookback_days - 1, 0))
    start = dt.datetime.combine(start_date, dt.time.min, tzinfo=tz)
    end = dt.datetime.combine(report_date + dt.timedelta(days=1), dt.time.min, tzinfo=tz)
    return start.astimezone(dt.timezone.utc), end.astimezone(dt.timezone.utc)


def parse_datetime(value: Any) -> dt.datetime | None:
    if not value:
        return None
    if isinstance(value, dt.datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        try:
            parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed = email.utils.parsedate_to_datetime(text)
            except (TypeError, ValueError):
                return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def parse_crossref_date(item: dict[str, Any]) -> dt.datetime | None:
    for key in ("published-online", "published-print", "published", "created", "indexed"):
        date_parts = item.get(key, {}).get("date-parts")
        if not date_parts:
            continue
        parts = date_parts[0]
        if not parts:
            continue
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
        return dt.datetime(year, month, day, tzinfo=dt.timezone.utc)
    return None


def is_recent(paper: Paper, start_utc: dt.datetime, end_utc: dt.datetime) -> bool:
    effective_date = paper.updated or paper.published
    if effective_date is None:
        return True
    return start_utc <= effective_date < end_utc


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_id(value: str) -> str:
    text = value.strip()
    text = re.sub(r"^https?://arxiv\.org/abs/", "arxiv:", text, flags=re.I)
    text = re.sub(r"^https?://dx\.doi\.org/", "doi:", text, flags=re.I)
    text = re.sub(r"^https?://doi\.org/", "doi:", text, flags=re.I)
    return text.lower()


def request_bytes(url: str, timeout: int = 30) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/xml, application/atom+xml, application/rss+xml, application/json;q=0.9, */*;q=0.7",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def request_json(url: str, timeout: int = 30) -> dict[str, Any]:
    return json.loads(request_bytes(url, timeout=timeout).decode("utf-8"))


def xml_text(node: ET.Element, path: str, ns: dict[str, str] | None = None) -> str:
    found = node.find(path, ns or {})
    return clean_text(found.text if found is not None else "")


def fetch_arxiv(
    config: dict[str, Any],
    start_utc: dt.datetime,
    end_utc: dt.datetime,
    statuses: list[dict[str, Any]],
) -> list[Paper]:
    arxiv_config = config.get("arxiv", {})
    endpoint = arxiv_config.get("endpoint", "https://export.arxiv.org/api/query")
    pause = float(arxiv_config.get("request_pause_seconds", 3.2))
    papers: list[Paper] = []

    for index, query in enumerate(arxiv_config.get("queries", [])):
        params = {
            "search_query": query["query"],
            "start": "0",
            "max_results": str(query.get("max_results", 50)),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        url = f"{endpoint}?{urllib.parse.urlencode(params)}"
        source_name = query.get("name", "arXiv")
        try:
            root = ET.fromstring(request_bytes(url))
            entries = root.findall("atom:entry", ATOM_NS)
            count = 0
            for entry in entries:
                title = xml_text(entry, "atom:title", ATOM_NS)
                abstract = xml_text(entry, "atom:summary", ATOM_NS)
                arxiv_id = normalize_id(xml_text(entry, "atom:id", ATOM_NS))
                authors = [
                    xml_text(author, "atom:name", ATOM_NS)
                    for author in entry.findall("atom:author", ATOM_NS)
                ]
                authors = [author for author in authors if author]
                categories = [
                    category.attrib.get("term", "")
                    for category in entry.findall("atom:category", ATOM_NS)
                    if category.attrib.get("term")
                ]
                url_out = ""
                for link in entry.findall("atom:link", ATOM_NS):
                    if link.attrib.get("rel") == "alternate":
                        url_out = link.attrib.get("href", "")
                        break
                doi = xml_text(entry, "arxiv:doi", ATOM_NS)
                paper = Paper(
                    uid=arxiv_id,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=url_out or arxiv_id.replace("arxiv:", "https://arxiv.org/abs/"),
                    source=source_name,
                    source_kind=query.get("source_kind", "arxiv"),
                    published=parse_datetime(xml_text(entry, "atom:published", ATOM_NS)),
                    updated=parse_datetime(xml_text(entry, "atom:updated", ATOM_NS)),
                    categories=categories,
                    doi=doi,
                    journal="arXiv",
                )
                if is_recent(paper, start_utc, end_utc):
                    papers.append(paper)
                    count += 1
            statuses.append({"source": source_name, "ok": True, "count": count})
        except Exception as exc:  # noqa: BLE001 - source failure should not kill report.
            statuses.append({"source": source_name, "ok": False, "error": str(exc)})
        if index < len(arxiv_config.get("queries", [])) - 1 and pause > 0:
            time.sleep(pause)
    return papers


def fetch_rss(
    config: dict[str, Any],
    start_utc: dt.datetime,
    end_utc: dt.datetime,
    statuses: list[dict[str, Any]],
) -> list[Paper]:
    papers: list[Paper] = []
    for source in config.get("rss_sources", []):
        source_name = source["name"]
        try:
            root = ET.fromstring(request_bytes(source["url"]))
            items = root.findall("./channel/item")
            if not items and root.tag.endswith("feed"):
                items = root.findall("atom:entry", ATOM_NS)
            count = 0
            for item in items:
                if item.tag.endswith("entry"):
                    title = xml_text(item, "atom:title", ATOM_NS)
                    abstract = xml_text(item, "atom:summary", ATOM_NS) or xml_text(item, "atom:content", ATOM_NS)
                    link = ""
                    for node in item.findall("atom:link", ATOM_NS):
                        if node.attrib.get("href"):
                            link = node.attrib["href"]
                            break
                    published = parse_datetime(xml_text(item, "atom:published", ATOM_NS))
                    authors = [
                        xml_text(author, "atom:name", ATOM_NS)
                        for author in item.findall("atom:author", ATOM_NS)
                    ]
                else:
                    title = xml_text(item, "title")
                    abstract = xml_text(item, "description")
                    link = xml_text(item, "link")
                    published = parse_datetime(xml_text(item, "pubDate"))
                    creators = [
                        clean_text(child.text)
                        for child in list(item)
                        if child.tag == f"{DC_NS}creator" and clean_text(child.text)
                    ]
                    authors = creators
                paper = Paper(
                    uid=normalize_id(link or f"{source_name}:{title}"),
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=link,
                    source=source_name,
                    source_kind=source.get("source_kind", "rss"),
                    published=published,
                    updated=published,
                    journal=source_name,
                )
                if title and is_recent(paper, start_utc, end_utc):
                    papers.append(paper)
                    count += 1
            statuses.append({"source": f"{source_name} RSS", "ok": True, "count": count})
        except Exception as exc:  # noqa: BLE001
            statuses.append({"source": f"{source_name} RSS", "ok": False, "error": str(exc)})
    return papers


def fetch_crossref(
    config: dict[str, Any],
    start_utc: dt.datetime,
    end_utc: dt.datetime,
    statuses: list[dict[str, Any]],
) -> list[Paper]:
    papers: list[Paper] = []
    base = "https://api.crossref.org/works"
    from_date = start_utc.date().isoformat()
    until_date = (end_utc - dt.timedelta(seconds=1)).date().isoformat()
    for source in config.get("crossref_sources", []):
        source_name = source["name"]
        filters = [
            f"from-pub-date:{from_date}",
            f"until-pub-date:{until_date}",
            f"issn:{source['issn']}",
        ]
        params = {
            "filter": ",".join(filters),
            "rows": str(source.get("rows", 20)),
            "sort": "published",
            "order": "desc",
        }
        url = f"{base}?{urllib.parse.urlencode(params)}"
        try:
            data = request_json(url, timeout=35)
            items = data.get("message", {}).get("items", [])
            count = 0
            for item in items:
                title = clean_text(" ".join(item.get("title", [])))
                abstract = clean_text(item.get("abstract", ""))
                doi = clean_text(item.get("DOI", ""))
                link = f"https://doi.org/{doi}" if doi else item.get("URL", "")
                authors = []
                for author in item.get("author", [])[:8]:
                    name = " ".join(
                        part for part in (author.get("given", ""), author.get("family", "")) if part
                    ).strip()
                    if name:
                        authors.append(name)
                container = clean_text(" ".join(item.get("container-title", []))) or source_name
                published = parse_crossref_date(item)
                paper = Paper(
                    uid=normalize_id(f"doi:{doi}" if doi else link or f"{source_name}:{title}"),
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=link,
                    source=f"{source_name} Crossref",
                    source_kind=source.get("source_kind", "crossref"),
                    published=published,
                    updated=published,
                    doi=doi,
                    journal=container,
                )
                if title and is_recent(paper, start_utc, end_utc):
                    papers.append(paper)
                    count += 1
            statuses.append({"source": f"{source_name} Crossref", "ok": True, "count": count})
        except Exception as exc:  # noqa: BLE001
            statuses.append({"source": f"{source_name} Crossref", "ok": False, "error": str(exc)})
    return papers


def deduplicate(papers: list[Paper]) -> list[Paper]:
    by_key: dict[str, Paper] = {}
    for paper in papers:
        key = normalize_id(f"doi:{paper.doi}") if paper.doi else paper.uid
        if not key:
            key = normalize_id(paper.url or paper.title)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = paper
            continue
        if len(paper.abstract) > len(existing.abstract):
            existing.abstract = paper.abstract
        if paper.url and not existing.url:
            existing.url = paper.url
        if paper.authors and not existing.authors:
            existing.authors = paper.authors
        existing.categories = sorted(set(existing.categories + paper.categories))
        existing.source = ", ".join(sorted(set(existing.source.split(", ") + [paper.source])))
        existing.source_kind = existing.source_kind if existing.source_kind == paper.source_kind else existing.source_kind
        existing.published = existing.published or paper.published
        existing.updated = max_datetime(existing.updated, paper.updated)
    return list(by_key.values())


def max_datetime(left: dt.datetime | None, right: dt.datetime | None) -> dt.datetime | None:
    if left is None:
        return right
    if right is None:
        return left
    return max(left, right)


def keyword_in_text(keyword: str, text: str) -> bool:
    needle = keyword.casefold()
    if re.fullmatch(r"[a-z0-9+-]{2,4}", needle):
        pattern = rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return needle in text


def score_papers(papers: list[Paper], config: dict[str, Any], preferences: dict[str, Any]) -> list[Paper]:
    source_weights = config.get("source_weights", {})
    for paper in papers:
        score = int(source_weights.get(paper.source_kind, 0))
        tags: list[str] = []
        noise_tags: list[str] = []
        matched_keywords: list[str] = []
        group_priorities: list[str] = []
        ai_blocked = False
        text = f"{paper.title} {paper.abstract} {' '.join(paper.categories)}".casefold()
        title_text = paper.title.casefold()

        if "gr-qc" in paper.categories:
            score += 8
        if paper.source_kind == "journal_review":
            score += 8

        keep_title_hits = [
            pattern for pattern in preferences.get("keep_title_patterns", [])
            if keyword_in_text(pattern, title_text)
        ]
        reject_title_hits = [
            pattern for pattern in preferences.get("reject_title_patterns", [])
            if keyword_in_text(pattern, title_text)
        ]
        blocked_title_hits = [
            pattern for pattern in config.get("blocked_title_patterns", [])
            if keyword_in_text(pattern, title_text)
        ] + [
            pattern for pattern in preferences.get("block_title_patterns", [])
            if keyword_in_text(pattern, title_text)
        ]
        if keep_title_hits:
            score += 80
            tags.append("人工保留")
            matched_keywords.extend(keep_title_hits[:3])
        if reject_title_hits:
            score -= 80
            noise_tags.append("人工拒绝")
            matched_keywords.extend(reject_title_hits[:3])
            ai_blocked = True
        if blocked_title_hits:
            score = min(score, int(config.get("minimum_score", 16)) - 1)
            noise_tags.append("显式屏蔽标题")
            matched_keywords.extend(blocked_title_hits[:3])
            ai_blocked = True

        for group in config.get("topic_groups", []):
            hits = [kw for kw in group.get("keywords", []) if keyword_in_text(kw, text)]
            if not hits:
                continue
            score += int(group.get("score", 0))
            score += min(max(len(hits) - 1, 0), 4) * 2
            if any(keyword_in_text(kw, title_text) for kw in hits):
                score += int(group.get("title_boost", 0))
            tags.append(group.get("label", group["name"]))
            matched_keywords.extend(hits[:5])
            group_priorities.append(group.get("priority", "related"))

        for group in config.get("negative_topic_groups", []):
            exempt_hits = [
                kw for kw in group.get("exempt_keywords", [])
                if keyword_in_text(kw, text)
            ]
            if exempt_hits:
                continue
            hits = [kw for kw in group.get("keywords", []) if keyword_in_text(kw, text)]
            if len(hits) < int(group.get("min_hits", 1)):
                continue
            score -= int(group.get("penalty", 0))
            noise_tags.append(group.get("label", group["name"]))
            matched_keywords.extend(hits[:5])
            ai_blocked = ai_blocked or bool(group.get("ai_block", False))

        for keyword, weight in preferences.get("keyword_weights", {}).items():
            if keyword_in_text(keyword, text):
                score += int(weight)
                matched_keywords.append(keyword)
        for tag in tags:
            score += int(preferences.get("tag_weights", {}).get(tag, 0))

        if blocked_title_hits:
            score = min(score, int(config.get("minimum_score", 16)) - 1)
            ai_blocked = True

        if "core" in group_priorities and score >= 58:
            priority = "must-read"
        elif "ai" in group_priorities and score >= 36:
            priority = "ai-news"
        elif score >= 46:
            priority = "recommended"
        elif score >= int(config.get("minimum_score", 16)):
            priority = "related"
        else:
            priority = "watch"

        if "ai" in group_priorities:
            area = "ai"
        elif "core" in group_priorities or paper.source_kind == "arxiv_core":
            area = "core"
        else:
            area = "related"

        if ai_blocked and priority in {"must-read", "recommended", "ai-news"}:
            priority = "related" if score >= int(config.get("minimum_score", 16)) else "watch"

        paper.score = score
        paper.priority = priority
        paper.area = area
        paper.tags = list(dict.fromkeys(tags))
        paper.noise_tags = list(dict.fromkeys(noise_tags))
        paper.matched_keywords = list(dict.fromkeys(matched_keywords))
        paper.ai_blocked = ai_blocked
        paper.analysis = fallback_analysis(paper)
    return sorted(papers, key=lambda item: (item.score, item.updated or item.published or dt.datetime.min.replace(tzinfo=dt.timezone.utc)), reverse=True)


def fallback_analysis(paper: Paper) -> dict[str, str]:
    summary = first_sentence(paper.abstract, max_chars=360)
    if not summary:
        summary = "该条目暂未提供摘要，建议从标题、来源和 DOI 链接判断是否需要进一步阅读。"
    matched = "、".join(paper.tags[:4]) if paper.tags else "来源优先级"
    why = f"匹配关注项：{matched}。"
    if paper.noise_tags:
        why += f" 低信号规则命中：{'、'.join(paper.noise_tags)}，默认不调用 AI。"
    if paper.source_kind == "arxiv_core":
        why += " 这是 gr-qc 每日新增或更新条目。"
    if paper.source_kind == "journal_review":
        why += " 综述类来源适合纳入长期阅读清单。"
    return {
        "zh_summary": summary,
        "why_relevant": why,
        "method_or_signal": ", ".join(paper.matched_keywords[:6]) or paper.source,
        "suggested_action": suggested_action(paper.priority),
    }


def first_sentence(text: str, max_chars: int = 320) -> str:
    text = clean_text(text)
    if not text:
        return ""
    match = re.search(r"(?<=[.!?])\s+", text)
    if match and match.start() <= max_chars:
        return text[: match.start()].strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."


def suggested_action(priority: str) -> str:
    return {
        "must-read": "优先精读，并检查方法、近似和可复现材料。",
        "recommended": "建议扫读摘要和结论，必要时加入阅读列表。",
        "ai-news": "作为 AI 工具/方法雷达，适合快速判断是否能迁移到论文检索或知识库流程。",
        "related": "相关性中等，适合保留链接后续筛选。",
    }.get(priority, "低优先级，暂作背景观察。")


def maybe_apply_ai(
    papers: list[Paper],
    config: dict[str, Any],
    no_ai: bool,
    statuses: list[dict[str, Any]],
) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if no_ai or not api_key:
        statuses.append({"source": "OpenAI analysis", "ok": False, "error": "skipped: OPENAI_API_KEY not set or --no-ai"})
        return

    max_items = int(config.get("ai_max_papers", 20))
    ai_priorities = set(config.get("ai_priorities", ["must-read", "recommended", "ai-news"]))
    candidates = [
        paper for paper in papers
        if not paper.ai_blocked and paper.priority in ai_priorities
    ]
    analyzed = 0
    for paper in candidates[:max_items]:
        try:
            result = analyze_with_openai(paper, config, api_key)
            if result:
                paper.analysis.update(result)
                analyzed += 1
        except Exception as exc:  # noqa: BLE001
            statuses.append({"source": f"OpenAI analysis: {paper.uid}", "ok": False, "error": str(exc)})
            break
    skipped = len(papers) - len(candidates)
    statuses.append({"source": "OpenAI analysis", "ok": True, "count": analyzed, "skipped": skipped})


def analyze_with_openai(paper: Paper, config: dict[str, Any], api_key: str) -> dict[str, str]:
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL") or config.get("openai_model", "gpt-4o-mini")
    endpoint = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是引力物理和相对论天体物理方向的论文助理。"
                    "请用中文给出简洁、可执行的阅读判断。只返回 JSON。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "title": paper.title,
                        "authors": paper.authors[:8],
                        "source": paper.source,
                        "categories": paper.categories,
                        "abstract": paper.abstract[:4000],
                        "score_tags": paper.tags,
                        "matched_keywords": paper.matched_keywords,
                    },
                    ensure_ascii=False,
                )
                + "\n返回字段：zh_summary, why_relevant, method_or_signal, suggested_action。每个字段不超过 80 个汉字。",
            },
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    content = parsed["choices"][0]["message"]["content"]
    json_text = extract_json_object(content)
    result = json.loads(json_text)
    return {key: clean_text(str(result.get(key, ""))) for key in ("zh_summary", "why_relevant", "method_or_signal", "suggested_action") if result.get(key)}


def extract_json_object(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError("OpenAI response did not contain a JSON object")
    return match.group(0)


def paper_to_dict(paper: Paper, tz: dt.tzinfo) -> dict[str, Any]:
    def fmt(value: dt.datetime | None) -> str:
        return value.astimezone(tz).isoformat() if value else ""

    return {
        "uid": paper.uid,
        "title": paper.title,
        "authors": paper.authors,
        "abstract": paper.abstract,
        "url": paper.url,
        "source": paper.source,
        "source_kind": paper.source_kind,
        "published": fmt(paper.published),
        "updated": fmt(paper.updated),
        "categories": paper.categories,
        "doi": paper.doi,
        "journal": paper.journal,
        "score": paper.score,
        "priority": paper.priority,
        "area": paper.area,
        "tags": paper.tags,
        "noise_tags": paper.noise_tags,
        "matched_keywords": paper.matched_keywords,
        "analysis": paper.analysis,
        "ai_blocked": paper.ai_blocked,
    }


def paper_from_dict(data: dict[str, Any]) -> Paper:
    return Paper(
        uid=data.get("uid", ""),
        title=data.get("title", ""),
        authors=list(data.get("authors", [])),
        abstract=data.get("abstract", ""),
        url=data.get("url", ""),
        source=data.get("source", ""),
        source_kind=data.get("source_kind", ""),
        published=parse_datetime(data.get("published", "")),
        updated=parse_datetime(data.get("updated", "")),
        categories=list(data.get("categories", [])),
        doi=data.get("doi", ""),
        journal=data.get("journal", ""),
        score=int(data.get("score", 0)),
        priority=data.get("priority", "watch"),
        area=data.get("area", "related"),
        tags=list(data.get("tags", [])),
        noise_tags=list(data.get("noise_tags", [])),
        matched_keywords=list(data.get("matched_keywords", [])),
        analysis=dict(data.get("analysis", {})),
        ai_blocked=bool(data.get("ai_blocked", False)),
    )


def keep_rendered_papers(papers: list[Paper], config: dict[str, Any], limit: int | None) -> list[Paper]:
    threshold = int(config.get("minimum_score", 16))
    max_papers = int(limit or config.get("max_papers", 45))
    kept = [paper for paper in papers if paper.score >= threshold]
    return kept[:max_papers]


def keep_review_papers(papers: list[Paper], config: dict[str, Any]) -> list[Paper]:
    review_config = config.get("review", {})
    threshold = int(review_config.get("min_score", 0))
    max_candidates = int(review_config.get("max_candidates", 80))
    return [paper for paper in papers if paper.score >= threshold and not paper.ai_blocked][:max_candidates]


def review_id(index: int) -> str:
    return f"P{index:03d}"


def review_to_dict(papers: list[Paper], tz: dt.tzinfo) -> list[dict[str, Any]]:
    rows = []
    for index, paper in enumerate(papers, start=1):
        rows.append({"review_id": review_id(index), **paper_to_dict(paper, tz)})
    return rows


def render_review(papers: list[Paper], metadata: dict[str, Any], tz: dt.tzinfo) -> str:
    lines = [
        f"# Paper Watch Review {metadata['date']}",
        "",
        f"- 生成时间：{metadata['generated_at']}",
        f"- 时间窗口：{metadata['window']}",
        f"- 候选数：{len(papers)}",
        "",
        "回复格式建议：`keep P001 P004 P009; reject P002 P007; block P003`。",
        "",
        "说明：`keep` 会提高相似条目的权重，`reject` 会降权，`block` 会把标题加入显式屏蔽并禁止 AI 分析。",
        "",
    ]
    for index, paper in enumerate(papers, start=1):
        paper_id = review_id(index)
        date = paper.updated or paper.published
        date_text = date.astimezone(tz).strftime("%Y-%m-%d %H:%M") if date else "date unknown"
        tags = " / ".join(paper.tags) if paper.tags else "untagged"
        noise = f" | low-signal: {' / '.join(paper.noise_tags)}" if paper.noise_tags else ""
        authors = format_authors(paper.authors)
        lines.extend(
            [
                f"- [ ] **{paper_id}** `{paper.priority}` `score {paper.score}` {paper.title}",
                f"  - 链接：{paper.url}",
                f"  - 来源：{paper.source} | {date_text} | {tags}{noise}",
            ]
        )
        if authors:
            lines.append(f"  - 作者：{authors}")
        if paper.matched_keywords:
            lines.append(f"  - 信号：{', '.join(paper.matched_keywords[:8])}")
        lines.append(f"  - 摘要：{first_sentence(paper.abstract, max_chars=260)}")
        lines.append("")
    return "\n".join(lines)


def render_report(
    papers: list[Paper],
    metadata: dict[str, Any],
    config: dict[str, Any],
    tz: dt.tzinfo,
) -> str:
    report_date = metadata["date"]
    title = f"论文日报 {report_date}"
    front_matter = [
        "---",
        f"title: {title}",
        "lang: zh-CN",
        f"permalink: /papers/{report_date}/",
        "---",
        "",
    ]
    lines = front_matter
    lines.extend(
        [
            f'<section class="paper-watch-summary">',
            f"<p><strong>生成时间：</strong>{html.escape(metadata['generated_at'])}</p>",
            f"<p><strong>窗口：</strong>{html.escape(metadata['window'])}</p>",
            f"<p><strong>收录：</strong>{len(papers)} 条。核心 {metadata['counts'].get('must-read', 0)}，推荐 {metadata['counts'].get('recommended', 0)}，AI {metadata['counts'].get('ai-news', 0)}，相关 {metadata['counts'].get('related', 0)}。</p>",
            "</section>",
            "",
        ]
    )

    if metadata.get("source_statuses"):
        lines.append('<details class="paper-source-status"><summary>源状态</summary>')
        lines.append("<ul>")
        for status in metadata["source_statuses"]:
            label = html.escape(status.get("source", "unknown"))
            if status.get("ok"):
                lines.append(f"<li>{label}: OK, {status.get('count', 0)} 条进入时间窗口。</li>")
            else:
                error = html.escape(str(status.get("error", "unknown error"))[:220])
                lines.append(f"<li>{label}: 跳过或失败，{error}</li>")
        lines.append("</ul>")
        lines.append("</details>")
        lines.append("")

    sections = [
        ("must-read", "核心必读"),
        ("recommended", "推荐关注"),
        ("ai-news", "AI/知识库雷达"),
        ("related", "相关扫读"),
        ("watch", "低优先级保留"),
    ]
    any_section = False
    for priority, heading in sections:
        group = [paper for paper in papers if paper.priority == priority]
        if not group:
            continue
        any_section = True
        lines.append(f"## {heading}")
        lines.append("")
        for paper in group:
            lines.extend(render_paper_card(paper, tz))
            lines.append("")

    if not any_section:
        lines.extend(
            [
                "## 今日结果",
                "",
                "当前时间窗口内没有达到阈值的新增条目。可以降低 `minimum_score`，或扩大 `lookback_days`。",
                "",
            ]
        )

    lines.extend(
        [
            "## 配置提示",
            "",
            "关键词、arXiv 分类、期刊 RSS 和 Crossref ISSN 都在 `config/paper_watch.json` 中维护。邮件提醒需要在 GitHub Secrets 中配置 SMTP 和收件人变量。",
            "",
        ]
    )
    return "\n".join(lines)


def render_paper_card(paper: Paper, tz: dt.tzinfo) -> list[str]:
    title = html.escape(paper.title)
    url = html.escape(paper.url or "#")
    authors = html.escape(format_authors(paper.authors))
    source = html.escape(paper.source)
    date = paper.updated or paper.published
    date_text = date.astimezone(tz).strftime("%Y-%m-%d %H:%M") if date else "date unknown"
    tags = "".join(f'<span class="paper-tag">{html.escape(tag)}</span>' for tag in paper.tags[:6])
    cats = " ".join(paper.categories[:6])
    meta_bits = [source, f"score {paper.score}", date_text]
    if cats:
        meta_bits.append(cats)
    analysis = paper.analysis or fallback_analysis(paper)
    lines = [
        f'<article class="paper-card paper-card--{html.escape(paper.priority)}">',
        f'<h3><a href="{url}">{title}</a></h3>',
        f'<p class="paper-meta">{html.escape(" | ".join(meta_bits))}</p>',
    ]
    if authors:
        lines.append(f'<p class="paper-authors">{authors}</p>')
    if tags:
        lines.append(f'<p class="paper-tags">{tags}</p>')
    lines.extend(
        [
            f'<p><strong>摘要判断：</strong>{html.escape(analysis.get("zh_summary", ""))}</p>',
            f'<p><strong>相关性：</strong>{html.escape(analysis.get("why_relevant", ""))}</p>',
            f'<p><strong>信号：</strong>{html.escape(analysis.get("method_or_signal", ""))}</p>',
            f'<p><strong>动作：</strong>{html.escape(analysis.get("suggested_action", ""))}</p>',
        ]
    )
    if paper.abstract:
        lines.extend(
            [
                "<details>",
                "<summary>英文摘要</summary>",
                f"<p>{html.escape(paper.abstract)}</p>",
                "</details>",
            ]
        )
    lines.append("</article>")
    return lines


def format_authors(authors: list[str]) -> str:
    if not authors:
        return ""
    if len(authors) <= 6:
        return ", ".join(authors)
    return ", ".join(authors[:6]) + " et al."


def render_index(history: list[dict[str, Any]], latest: dict[str, Any], config: dict[str, Any]) -> str:
    lines = [
        "---",
        "title: 论文日报",
        "lang: zh-CN",
        "permalink: /papers/",
        "---",
        "",
        '<section class="paper-watch-home">',
        "<p>这里自动汇总 gr-qc、致密双星建模、LVK/LISA、QNM、相关天文/高能方向，以及 AI/知识库方向的论文与新闻线索。</p>",
    ]
    if latest:
        date = latest.get("date", "")
        count = latest.get("total_papers", 0)
        review_count = latest.get("total_review_candidates", 0)
        lines.append(f'<p><strong>最新日报：</strong><a href="/papers/{html.escape(date)}/">{html.escape(date)}</a>，收录 {count} 条；批阅候选 {review_count} 条。</p>')
    lines.extend(
        [
            "</section>",
            "",
            "## 关注范围",
            "",
            "- 核心：致密双星建模，PM/PN/GSF/NR/EOB，波形模型，LVK/LISA/TianQin/Taiji，QNM/ringdown。",
            "- 次相关：gr-qc 其他方向，黑洞热力学、宇宙学、暗物质、修正引力，以及天文和高能交叉论文。",
            "- AI 雷达：LLM、RAG、知识库、智能体、模型架构和科研自动化方法。",
            "",
            "## 历史日报",
            "",
        ]
    )
    if history:
        lines.append('<ul class="paper-history">')
        for item in sorted(history, key=lambda row: row.get("date", ""), reverse=True)[:60]:
            date = html.escape(item.get("date", ""))
            count = item.get("total_papers", 0)
            generated = html.escape(item.get("generated_at", ""))
            lines.append(f'<li><a href="/papers/{date}/">{date}</a> <span>{count} 条，{generated}</span></li>')
        lines.append("</ul>")
    else:
        lines.append("暂无历史日报。")
    lines.extend(
        [
            "",
            "## 自动化",
            "",
            "GitHub Actions 会按计划运行 `scripts/paper_watch.py`。脚本同时生成 `_paper_reviews/YYYY-MM-DD.md` 批阅清单和公开日报。你可以用 `scripts/paper_feedback.py` 写入 keep/reject/block 反馈，再重新生成日报。",
            "",
        ]
    )
    return "\n".join(lines)


def count_priorities(papers: list[Paper]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for paper in papers:
        counts[paper.priority] = counts.get(paper.priority, 0) + 1
    return counts


def read_history() -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    with HISTORY_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, list) else []


def write_outputs(
    report_date: dt.date,
    papers: list[Paper],
    review_papers: list[Paper],
    metadata: dict[str, Any],
    config: dict[str, Any],
    tz: dt.tzinfo,
) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    report_path = PAPERS_DIR / f"{report_date.isoformat()}.md"
    report_path.write_text(render_report(papers, metadata, config, tz), encoding="utf-8")

    latest = {
        **metadata,
        "total_papers": len(papers),
        "total_review_candidates": len(review_papers),
        "report_path": f"/papers/{report_date.isoformat()}/",
        "review_path": f"_paper_reviews/{report_date.isoformat()}.md",
        "papers": [paper_to_dict(paper, tz) for paper in papers],
    }
    LATEST_PATH.write_text(json.dumps(latest, ensure_ascii=False, indent=2), encoding="utf-8")

    review_path = REVIEWS_DIR / f"{report_date.isoformat()}.md"
    review_path.write_text(render_review(review_papers, metadata, tz), encoding="utf-8")
    review_json_path = DATA_DIR / f"review_{report_date.isoformat()}.json"
    review_json = {
        **metadata,
        "review_path": str(review_path.relative_to(ROOT)),
        "candidates": review_to_dict(review_papers, tz),
    }
    review_json_path.write_text(json.dumps(review_json, ensure_ascii=False, indent=2), encoding="utf-8")

    history = [item for item in read_history() if item.get("date") != report_date.isoformat()]
    history.append(
        {
            "date": report_date.isoformat(),
            "generated_at": metadata["generated_at"],
            "total_papers": len(papers),
            "total_review_candidates": len(review_papers),
            "counts": metadata["counts"],
            "report_path": f"/papers/{report_date.isoformat()}/",
            "review_path": f"_paper_reviews/{report_date.isoformat()}.md",
        }
    )
    history = sorted(history, key=lambda item: item.get("date", ""), reverse=True)[:120]
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

    index_path = PAPERS_DIR / "index.md"
    index_path.write_text(render_index(history, latest, config), encoding="utf-8")


def send_email(metadata: dict[str, Any], papers: list[Paper], config: dict[str, Any]) -> bool:
    host = os.environ.get("SMTP_HOST")
    username = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    recipients = [item.strip() for item in os.environ.get("PAPER_WATCH_EMAIL_TO", "").split(",") if item.strip()]
    if not host or not username or not password or not recipients:
        print("Email skipped: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, or PAPER_WATCH_EMAIL_TO is missing.")
        return False

    port = int(os.environ.get("SMTP_PORT", "465"))
    sender = os.environ.get("SMTP_FROM", username)
    subject_prefix = config.get("email", {}).get("subject_prefix", "Paper Watch")
    subject = f"{subject_prefix} {metadata['date']}: {len(papers)} items"
    site_url = os.environ.get("PAPER_WATCH_SITE_URL", config.get("site_url", "")).rstrip("/")
    report_url = f"{site_url}/papers/{metadata['date']}/" if site_url else f"/papers/{metadata['date']}/"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(build_email_body(report_url, metadata, papers))

    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=30) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(username, password)
            smtp.send_message(message)
    print(f"Email sent to {len(recipients)} recipient(s).")
    return True


def build_email_body(report_url: str, metadata: dict[str, Any], papers: list[Paper]) -> str:
    lines = [
        f"Paper Watch {metadata['date']}",
        f"Report: {report_url}",
        f"Window: {metadata['window']}",
        "",
        "Top items:",
    ]
    for index, paper in enumerate(papers[:12], start=1):
        lines.append(f"{index}. [{paper.priority} | {paper.score}] {paper.title}")
        lines.append(f"   {paper.url}")
        lines.append(f"   {paper.analysis.get('why_relevant', '')}")
    if not papers:
        lines.append("No papers passed the configured threshold today.")
    return "\n".join(lines)


def collect_all(
    config: dict[str, Any],
    start_utc: dt.datetime,
    end_utc: dt.datetime,
    statuses: list[dict[str, Any]],
) -> list[Paper]:
    papers: list[Paper] = []
    papers.extend(fetch_arxiv(config, start_utc, end_utc, statuses))
    papers.extend(fetch_rss(config, start_utc, end_utc, statuses))
    papers.extend(fetch_crossref(config, start_utc, end_utc, statuses))
    return deduplicate(papers)


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    if args.email_only:
        if not LATEST_PATH.exists():
            print(f"Email skipped: {LATEST_PATH} does not exist.")
            return 0
        latest = json.loads(LATEST_PATH.read_text(encoding="utf-8"))
        papers = [paper_from_dict(item) for item in latest.get("papers", [])]
        metadata = {key: value for key, value in latest.items() if key != "papers"}
        send_email(metadata, papers, config)
        return 0

    tz = local_tz(config)
    report_date = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(tz).date()
    lookback_days = args.lookback_days or int(config.get("lookback_days", 2))
    start_utc, end_utc = build_window(report_date, tz, lookback_days)
    statuses: list[dict[str, Any]] = []

    preferences = load_preferences(config)
    raw_papers = collect_all(config, start_utc, end_utc, statuses)
    scored = score_papers(raw_papers, config, preferences)
    rendered = keep_rendered_papers(scored, config, args.limit)
    review_papers = keep_review_papers(scored, config)
    maybe_apply_ai(rendered, config, args.no_ai, statuses)

    generated_at = dt.datetime.now(tz).strftime("%Y-%m-%d %H:%M %Z")
    window = (
        f"{start_utc.astimezone(tz).strftime('%Y-%m-%d %H:%M')}"
        f" 至 {end_utc.astimezone(tz).strftime('%Y-%m-%d %H:%M')} {getattr(tz, 'key', '')}".strip()
    )
    metadata = {
        "date": report_date.isoformat(),
        "generated_at": generated_at,
        "window": window,
        "counts": count_priorities(rendered),
        "source_statuses": statuses,
    }

    if args.dry_run:
        print(json.dumps({**metadata, "total_papers": len(rendered), "total_review_candidates": len(review_papers)}, ensure_ascii=False, indent=2))
        for paper in rendered[:15]:
            print(f"- [{paper.priority} {paper.score}] {paper.title} ({paper.source})")
        return 0

    write_outputs(report_date, rendered, review_papers, metadata, config, tz)
    if args.email:
        send_email(metadata, rendered, config)
    print(f"Rendered {len(rendered)} papers for {report_date.isoformat()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
