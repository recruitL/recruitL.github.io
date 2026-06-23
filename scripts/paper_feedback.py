#!/usr/bin/env python3
"""Record keep/reject/block feedback from a paper review queue."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "paper_watch.json"
DEFAULT_PREFERENCES = ROOT / "config" / "paper_preferences.json"
DATA_DIR = ROOT / "_data" / "paper_watch"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Review date in YYYY-MM-DD.")
    parser.add_argument("--keep", default="", help="IDs to keep, e.g. P001,P004 or '1 4'.")
    parser.add_argument("--reject", default="", help="IDs to down-rank.")
    parser.add_argument("--block", default="", help="IDs to explicitly block.")
    parser.add_argument("--note", default="", help="Optional feedback note.")
    parser.add_argument("--dry-run", action="store_true", help="Validate feedback without writing preferences.")
    return parser.parse_args()


def load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def review_ids(text: str) -> list[str]:
    ids = []
    for token in re.split(r"[\s,;]+", text.strip()):
        if not token:
            continue
        match = re.fullmatch(r"[Pp]?(\d{1,3})", token)
        if not match:
            raise ValueError(f"Invalid review id: {token}")
        ids.append(f"P{int(match.group(1)):03d}")
    return list(dict.fromkeys(ids))


def default_preferences() -> dict[str, Any]:
    return {
        "keep_title_patterns": [],
        "reject_title_patterns": [],
        "block_title_patterns": [],
        "keyword_weights": {},
        "tag_weights": {},
        "feedback_history": [],
    }


def add_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def bump_weight(weights: dict[str, int], key: str, delta: int, lower: int = -30, upper: int = 30) -> None:
    if not key:
        return
    current = int(weights.get(key, 0))
    weights[key] = max(lower, min(upper, current + delta))


def apply_learning(preferences: dict[str, Any], item: dict[str, Any], direction: int) -> None:
    tag_delta = 2 * direction
    keyword_delta = direction
    for tag in item.get("tags", []):
        bump_weight(preferences.setdefault("tag_weights", {}), tag, tag_delta)
    for keyword in item.get("matched_keywords", [])[:8]:
        bump_weight(preferences.setdefault("keyword_weights", {}), keyword, keyword_delta)


def main() -> int:
    args = parse_args()
    config = load_json(DEFAULT_CONFIG, {})
    preference_path = ROOT / config.get("preferences_path", "config/paper_preferences.json")
    preferences = load_json(preference_path, default_preferences())
    review_path = DATA_DIR / f"review_{args.date}.json"
    review = load_json(review_path, None)
    if not review:
        raise FileNotFoundError(f"Review queue not found: {review_path}")

    items = {item["review_id"]: item for item in review.get("candidates", [])}
    keep_ids = review_ids(args.keep)
    reject_ids = review_ids(args.reject)
    block_ids = review_ids(args.block)

    all_ids = keep_ids + reject_ids + block_ids
    missing = [paper_id for paper_id in all_ids if paper_id not in items]
    if missing:
        raise KeyError(f"Review id(s) not found for {args.date}: {', '.join(missing)}")

    for paper_id in keep_ids:
        item = items[paper_id]
        add_unique(preferences.setdefault("keep_title_patterns", []), item["title"])
        apply_learning(preferences, item, 1)
    for paper_id in reject_ids:
        item = items[paper_id]
        add_unique(preferences.setdefault("reject_title_patterns", []), item["title"])
        apply_learning(preferences, item, -1)
    for paper_id in block_ids:
        item = items[paper_id]
        add_unique(preferences.setdefault("block_title_patterns", []), item["title"])
        apply_learning(preferences, item, -2)

    preferences.setdefault("feedback_history", []).append(
        {
            "date": args.date,
            "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "keep": keep_ids,
            "reject": reject_ids,
            "block": block_ids,
            "note": args.note,
        }
    )
    if not args.dry_run:
        write_json(preference_path, preferences)

    print(
        f"{'Validated' if args.dry_run else 'Recorded'} feedback for {args.date}: "
        f"keep={len(keep_ids)}, reject={len(reject_ids)}, block={len(block_ids)}."
    )
    if not args.dry_run:
        print("Regenerate with: python3 scripts/paper_watch.py --date " + args.date + " --no-ai")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
