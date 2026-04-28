#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


EPISODE_RE = re.compile(r"第(\d+)話")


def parse_episode(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    title = None
    body_lines = []

    for line in lines:
        if line.startswith("#"):
            if title is None:
                title = line.lstrip("#").strip()
            continue
        if line.strip() == "---":
            continue
        body_lines.append(line)

    while body_lines and body_lines[0] == "":
        body_lines.pop(0)
    while body_lines and body_lines[-1] == "":
        body_lines.pop()

    match = EPISODE_RE.search(path.name)
    if not match:
        raise ValueError(f"Cannot find episode number in filename: {path}")

    number = int(match.group(1))
    if title is None:
        title = path.stem

    short_title = re.sub(r"^第\d+話[ 　:：_-]*", "", title).strip() or title
    body = "\n".join(body_lines)
    counted_lines = [line for line in body_lines if line]
    char_count = len(re.sub(r"\n", "", "\n".join(counted_lines)))

    return {
        "number": number,
        "title": title,
        "short_title": short_title,
        "path": str(path),
        "char_count": char_count,
        "body": body,
    }


def collect(root: Path, series: str, start: int | None, end: int | None) -> list[dict]:
    base = root / series
    if not base.exists():
        raise FileNotFoundError(f"Series directory not found: {base}")

    paths = sorted(base.glob("第*部/第*章*/第*話*.md"))
    episodes = [parse_episode(path) for path in paths]
    episodes.sort(key=lambda item: item["number"])

    if start is not None:
        episodes = [item for item in episodes if item["number"] >= start]
    if end is not None:
        episodes = [item for item in episodes if item["number"] <= end]

    seen = set()
    duplicates = []
    for item in episodes:
        if item["number"] in seen:
            duplicates.append(item["number"])
        seen.add(item["number"])
    if duplicates:
        raise ValueError(f"Duplicate episode numbers: {duplicates}")

    return episodes


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Markdown episodes for Syosetu draft upload.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--series", default="辺境拠点日誌", help="Series directory under the root.")
    parser.add_argument("--start", type=int, help="First episode number to include.")
    parser.add_argument("--end", type=int, help="Last episode number to include.")
    parser.add_argument("--out", help="Output JSON path. Prints JSON to stdout when omitted.")
    args = parser.parse_args()

    episodes = collect(Path(args.root).resolve(), args.series, args.start, args.end)
    payload = {
        "series": args.series,
        "count": len(episodes),
        "episodes": episodes,
    }
    data = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.out:
        Path(args.out).write_text(data + "\n", encoding="utf-8")
        print(f"Wrote {len(episodes)} episode(s) to {args.out}")
    else:
        print(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
