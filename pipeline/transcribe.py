#!/usr/bin/env python3
"""Transcribe recent podcast episodes with Whisper.

Reads pipeline/podcasts.json, fetches each feed, downloads every episode from the
last `days_back` days as MP3, runs faster-whisper on it, and writes one Markdown
file per episode into research/transcripts/. Episodes already on disk are skipped.

Usage:
  python3 pipeline/transcribe.py            # all feeds, last 7 days
  python3 pipeline/transcribe.py --days 3   # shorter window
  python3 pipeline/transcribe.py --dry-run  # list episodes, download nothing
"""
import argparse
import email.utils
import json
import pathlib
import re
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "pipeline" / "podcasts.json"
OUT = ROOT / "research" / "transcripts"
UA = {"User-Agent": "bengals-fanzone transcript bot (personal, non-commercial)"}


def slug(s, n=60):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:n].rstrip("-")


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def episodes(feed_url, since):
    """Yield (title, published, link, mp3_url, description) for items newer than `since`."""
    root = ET.fromstring(fetch(feed_url))
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        pub = item.findtext("pubDate")
        when = email.utils.parsedate_to_datetime(pub) if pub else None
        if when is None or when < since:
            continue
        enc = item.find("enclosure")
        mp3 = enc.get("url") if enc is not None else None
        if not mp3:
            continue
        yield {
            "title": title,
            "published": when,
            "link": (item.findtext("link") or "").strip(),
            "mp3": mp3,
            "description": re.sub(r"<[^>]+>", " ", item.findtext("description") or "").strip(),
        }


def transcribe(mp3_path, model_name):
    from faster_whisper import WhisperModel  # imported late so --dry-run needs no model

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(mp3_path), beam_size=1, vad_filter=True)
    lines = []
    for seg in segments:
        m, s = divmod(int(seg.start), 60)
        lines.append(f"[{m:02d}:{s:02d}] {seg.text.strip()}")
    return "\n".join(lines), info


def write(ep, feed_name, text, info):
    OUT.mkdir(parents=True, exist_ok=True)
    day = ep["published"].astimezone(timezone.utc).strftime("%Y-%m-%d")
    path = OUT / f"{day}-{slug(feed_name, 20)}-{slug(ep['title'])}.md"
    body = [
        f"# {ep['title']}",
        "",
        f"- Show: {feed_name}",
        f"- Published: {ep['published'].isoformat()}",
        f"- Link: {ep['link']}",
        f"- Audio: {ep['mp3']}",
        f"- Transcribed: {datetime.now(timezone.utc).isoformat(timespec='seconds')} with Whisper "
        f"({info.language}, {info.duration/60:.0f} min)",
        "",
        "## Show notes",
        "",
        ep["description"],
        "",
        "## Transcript",
        "",
        text,
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = json.loads(CONFIG.read_text())
    days = args.days or cfg.get("days_back", 7)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    model_name = cfg.get("whisper_model", "base")
    done = {p.stem for p in OUT.glob("*.md")} if OUT.exists() else set()
    new = 0

    for feed in cfg["feeds"]:
        try:
            eps = list(episodes(feed["url"], since))
        except Exception as e:  # a dead feed must not stop the others
            print(f"[{feed['name']}] feed failed: {e}", file=sys.stderr)
            continue
        print(f"[{feed['name']}] {len(eps)} episode(s) in the last {days} days")
        for ep in eps:
            day = ep["published"].astimezone(timezone.utc).strftime("%Y-%m-%d")
            stem = f"{day}-{slug(feed['name'], 20)}-{slug(ep['title'])}"
            if stem in done:
                print(f"  skip (have it): {ep['title']}")
                continue
            print(f"  {'would transcribe' if args.dry_run else 'transcribing'}: {ep['title']}")
            if args.dry_run:
                continue
            with tempfile.TemporaryDirectory() as td:
                mp3 = pathlib.Path(td) / "episode.mp3"
                mp3.write_bytes(fetch(ep["mp3"], timeout=300))
                text, info = transcribe(mp3, model_name)
            path = write(ep, feed["name"], text, info)
            print(f"  wrote {path.relative_to(ROOT)} ({len(text.split())} words)")
            new += 1

    print(f"{new} new transcript(s)")


if __name__ == "__main__":
    main()
