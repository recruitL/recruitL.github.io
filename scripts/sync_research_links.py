#!/usr/bin/env python3
"""Sync compact research-topic display data from research-links.

This script intentionally copies only data/site/research_topics.yml. Full CSV
datasets stay in the research-links repository and are linked from the site.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "_data" / "research_topics.yml"
DEFAULT_LOCAL_SOURCE = ROOT.parent / "research-links" / "data" / "site" / "research_topics.yml"
DEFAULT_REMOTE_SOURCE = (
    "https://raw.githubusercontent.com/recruitL/research-links/main/data/site/research_topics.yml"
)


def read_remote(url: str, timeout: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "research-site-sync/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def backup_target(target: Path) -> Path | None:
    if not target.exists():
        return None
    backup = target.with_suffix(target.suffix + ".bak")
    shutil.copy2(target, backup)
    return backup


def write_bytes_safely(target: Path, content: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=target.parent) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    tmp_path.replace(target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync _data/research_topics.yml from research-links.")
    parser.add_argument("--local-source", type=Path, default=DEFAULT_LOCAL_SOURCE)
    parser.add_argument("--remote-source", default=DEFAULT_REMOTE_SOURCE)
    parser.add_argument("--target", type=Path, default=TARGET)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    content: bytes | None = None
    source_label = ""

    if args.local_source.exists():
        content = args.local_source.read_bytes()
        source_label = str(args.local_source)
    else:
        print(f"Local source not found: {args.local_source}", file=sys.stderr)
        try:
            content = read_remote(args.remote_source, args.timeout)
            source_label = args.remote_source
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"Remote source unavailable: {args.remote_source}", file=sys.stderr)
            print(f"Reason: {exc}", file=sys.stderr)

    if content is None:
        if args.target.exists():
            print(f"Keeping existing target without overwrite: {args.target}")
            return 0
        print("No research topic data source is available and target does not exist.", file=sys.stderr)
        return 1

    backup = backup_target(args.target)
    write_bytes_safely(args.target, content)
    print(f"Synced research topics from {source_label}")
    print(f"Wrote {args.target}")
    if backup:
        print(f"Backup saved to {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
