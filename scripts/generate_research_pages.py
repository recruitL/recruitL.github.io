#!/usr/bin/env python3
"""Generate /research/<slug>/ pages from _data/research_topics.yml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "_data" / "research_topics.yml"
RESEARCH_DIR = ROOT / "research"
AUTO_MARKER = "<!-- AUTO-GENERATED: research-topic-page -->"


def load_topics(data_file: Path) -> list[dict]:
    if not data_file.exists():
        raise FileNotFoundError(f"Missing data file: {data_file}")
    data = yaml.safe_load(data_file.read_text(encoding="utf-8")) or {}
    topics = data.get("topics", [])
    if not isinstance(topics, list):
        raise ValueError("Expected top-level 'topics' to be a list.")
    return topics


def page_content(topic: dict) -> str:
    slug = topic.get("slug")
    title = topic.get("title") or topic.get("short_title") or slug
    description = topic.get("summary", "")
    return f"""---
layout: research_topic
title: {title!r}
topic_slug: {slug!r}
auto_generated: true
permalink: /research/{slug}/
description: {description!r}
---

{AUTO_MARKER}

本页由 `_data/research_topics.yml` 自动生成。正文内容由 `_layouts/research_topic.html` 根据数据文件渲染。
"""


def can_overwrite(path: Path) -> bool:
    if not path.exists():
        return True
    text = path.read_text(encoding="utf-8")
    return AUTO_MARKER in text or "auto_generated: true" in text


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate research topic pages.")
    parser.add_argument("--data", type=Path, default=DATA_FILE)
    parser.add_argument("--output-dir", type=Path, default=RESEARCH_DIR)
    args = parser.parse_args()

    try:
        topics = load_topics(args.data)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    generated = 0
    skipped = 0
    for topic in topics:
        slug = topic.get("slug")
        if not slug:
            print(f"WARNING: skipped topic without slug: {topic}", file=sys.stderr)
            skipped += 1
            continue
        target_dir = args.output_dir / slug
        target = target_dir / "index.md"
        if not can_overwrite(target):
            print(f"WARNING: skipped manually maintained page: {target}", file=sys.stderr)
            skipped += 1
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        target.write_text(page_content(topic), encoding="utf-8")
        print(f"Generated {target}")
        generated += 1

    print(f"Done: generated={generated}, skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
