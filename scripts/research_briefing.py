#!/usr/bin/env python3
"""Generate the curated daily research briefing as a Jekyll collection item."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "_research_briefings"
TIMEZONE = ZoneInfo("Asia/Shanghai")
DEFAULT_MODEL = "gpt-5.6-terra"

SYSTEM_PROMPT = """
你是一名严谨的中文研究简报编辑，熟悉引力物理、相对论天体物理和科研软件。
你必须先使用 web search 核对当天可公开访问的一手来源，再编写简报。

关注范围按优先级排序：
1. 引力波波源建模：EOB、PM/EFT、PN、GSF、EMRI、NR。
2. 黑洞微扰：Teukolsky、Sasaki-Nakamura、MST、Green function、metric reconstruction。
3. QNM/ringdown：EP、VAM/TTM、谱不稳定、伪谱与 continued fraction。
4. LISA/TianQin/Taiji、LVK、环境效应、modified-gravity tests。
5. 可直接复用的 Mathematica/Python/Julia/BHPT/FEW/Codex/Zotero 工具更新。
6. 与上述主线直接相关的会议、讲座和公开课件。

内容规则：
- 只保留 5 至 8 条高信号内容；宁缺毋滥。
- 优先最近 72 小时的一手来源。周末或无新批次时可补充重要修订、软件和会议。
- 排除只有换背景、低阶 WKB 或弱现象学包装、且没有可靠方法增量的低信号论文。
- 不得虚构论文编号、发布日期、软件版本、会议状态或结论。
- 每条必须说明核心内容、为什么与上述研究相关、下一步具体动作。
- 来源必须是实际核对过的公开 URL，优先 arXiv、期刊、官方项目仓库或会议官网。
- 输出简体中文。不要输出 Markdown，不要输出代码围栏。

只返回一个 JSON 对象，格式严格如下：
{
  "summary": "不超过 80 字的当日总览",
  "items": [
    {
      "topic": "短标签",
      "title": "标题",
      "summary": "2 至 4 句核心内容",
      "relevance": "1 至 3 句为什么相关",
      "action": "1 至 3 句具体动作",
      "sources": [
        {"label": "来源名", "url": "https://..."}
      ]
    }
  ]
}
""".strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        help="Briefing date in YYYY-MM-DD. Defaults to today in Asia/Shanghai.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("RESEARCH_BRIEFING_MODEL")
        or DEFAULT_MODEL,
        help="OpenAI model used by the Responses API.",
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        help="Render a previously reviewed JSON payload without calling OpenAI.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated Jekyll document instead of writing it.",
    )
    return parser.parse_args()


def target_date(value: str | None) -> date:
    if value:
        return date.fromisoformat(value)
    return datetime.now(TIMEZONE).date()


def call_openai(report_date: date, model: str) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required unless --input-json is used")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    endpoint = f"{base_url}/responses"
    payload = {
        "model": model,
        "tools": [{"type": "web_search"}],
        "instructions": SYSTEM_PROMPT,
        "input": (
            f"请生成北京时间 {report_date.isoformat()} 的研究每日简报。"
            "先核对来源日期和链接，再按规定 JSON 格式返回。"
        ),
        "max_output_tokens": 8000,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            body = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI Responses API returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI Responses API request failed: {exc}") from exc

    text_parts: list[str] = []
    for item in body.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                text_parts.append(content["text"])
    if not text_parts:
        raise RuntimeError("OpenAI response did not contain output_text")
    return parse_json_output("\n".join(text_parts))


def parse_json_output(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("briefing output must be a JSON object")
    return value


def clean_text(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError(f"{field} cannot be empty")
    return cleaned[:maximum]


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    items = payload.get("items")
    if not isinstance(items, list) or not 5 <= len(items) <= 8:
        raise ValueError("items must contain 5 to 8 entries")

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"items[{index}] must be an object")
        sources = item.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"items[{index}].sources must not be empty")
        normalized_sources: list[dict[str, str]] = []
        for source in sources[:3]:
            if not isinstance(source, dict):
                raise ValueError(f"items[{index}].sources entries must be objects")
            label = clean_text(source.get("label"), "source label", 80)
            url = clean_text(source.get("url"), "source url", 500)
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(f"items[{index}] contains an invalid source URL")
            normalized_sources.append({"label": label, "url": url})
        normalized.append(
            {
                "topic": clean_text(item.get("topic"), f"items[{index}].topic", 50),
                "title": clean_text(item.get("title"), f"items[{index}].title", 180),
                "summary": clean_text(item.get("summary"), f"items[{index}].summary", 1400),
                "relevance": clean_text(
                    item.get("relevance"), f"items[{index}].relevance", 1000
                ),
                "action": clean_text(item.get("action"), f"items[{index}].action", 1000),
                "sources": normalized_sources,
            }
        )
    return {
        "summary": clean_text(payload.get("summary"), "summary", 240),
        "items": normalized,
    }


def h(value: str) -> str:
    return html.escape(value, quote=True)


def render_document(report_date: date, payload: dict[str, Any], generated_at: datetime) -> str:
    summary = payload["summary"]
    items = payload["items"]
    lines = [
        "---",
        f'title: "中文研究简报｜{report_date.isoformat()}"',
        f"date: {report_date.isoformat()} 09:00:00 +0800",
        f'generated_at: "{generated_at.strftime("%Y-%m-%d %H:%M CST")}"',
        f"description: {json.dumps(summary, ensure_ascii=False)}",
        f"item_count: {len(items)}",
        'source_task: "GitHub Actions · OpenAI Responses API"',
        "---",
        "",
        f'<p class="briefing-lead">{h(summary)}</p>',
        "",
    ]
    for index, item in enumerate(items, start=1):
        links = " ".join(
            f'<a href="{h(source["url"])}">{h(source["label"])}</a>'
            for source in item["sources"]
        )
        lines.extend(
            [
                '<section class="briefing-item">',
                f'<h2>{index}. {h(item["topic"])}：{h(item["title"])}</h2>',
                f'<p><span class="briefing-item__label">核心内容：</span>{h(item["summary"])}</p>',
                f'<p><span class="briefing-item__label">为什么相关：</span>{h(item["relevance"])}</p>',
                f'<p><span class="briefing-item__label">具体动作：</span>{h(item["action"])}</p>',
                f'<p class="briefing-sources"><span>来源：</span>{links}</p>',
                "</section>",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    report_date = target_date(args.date)
    if args.input_json:
        with args.input_json.open(encoding="utf-8") as handle:
            raw_payload = json.load(handle)
        payload = validate_payload(raw_payload)
    else:
        validation_error: ValueError | None = None
        for _attempt in range(2):
            raw_payload = call_openai(report_date, args.model)
            try:
                payload = validate_payload(raw_payload)
                break
            except ValueError as exc:
                validation_error = exc
        else:
            raise RuntimeError(
                f"OpenAI returned an invalid briefing twice: {validation_error}"
            )
    generated_at = datetime.now(TIMEZONE)
    document = render_document(report_date, payload, generated_at)

    if args.dry_run:
        sys.stdout.write(document)
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{report_date.isoformat()}.md"
    output_path.write_text(document, encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT)} with {len(payload['items'])} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
