#!/usr/bin/env python3
"""Copy the weekly media topics files from the private research repo into data/media/.

The round-up session writes research/media/<season>-w<NN>.json in bengals-research (private).
In GitHub Actions, that repo is cloned with a read-only token (secret RESEARCH_TOKEN). Locally,
pass the path of a checkout. Rebuilds data/media/index.json from the files present.

Usage: python3 pipeline/sync_media.py /path/to/bengals-research
"""
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "media"
ALLOWED = {"season", "week", "opponent", "written", "sources", "topics"}
SOURCE_KEYS = {"id", "name", "type", "url"}
TOPIC_KEYS = {"topic", "sources", "stat_verdict"}


def clean(doc):
    """Keep only the fields the page uses, so nothing private can ride along by accident."""
    out = {k: doc[k] for k in ALLOWED if k in doc}
    out["sources"] = [{k: s[k] for k in SOURCE_KEYS if k in s} for s in doc.get("sources", [])]
    out["topics"] = [{k: t[k] for k in TOPIC_KEYS if k in t} for t in doc.get("topics", [])]
    return out


def main(src_root):
    src = pathlib.Path(src_root) / "research" / "media"
    DEST.mkdir(parents=True, exist_ok=True)
    copied = 0
    for f in sorted(src.glob("*-w*.json")) if src.exists() else []:
        try:
            doc = clean(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"skip {f.name}: {e}", file=sys.stderr)
            continue
        (DEST / f.name).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        copied += 1
    weeks, season = [], None
    for f in sorted(DEST.glob("*-w*.json")):
        m = re.match(r"(\d{4})-w(\d{2})\.json", f.name)
        if m:
            season, wk = int(m.group(1)), int(m.group(2))
            weeks.append(wk)
    index = DEST / "index.json"
    prev = json.loads(index.read_text()) if index.exists() else {}
    prev.update({"season": season or prev.get("season"), "weeks": sorted(set(weeks))})
    index.write_text(json.dumps(prev, indent=2) + "\n")
    print(f"media: copied {copied} file(s); weeks {prev['weeks']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../bengals-research")
