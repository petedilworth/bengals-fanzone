#!/usr/bin/env python3
"""Fallback: pull YouTube auto-captions for recent channel uploads with yt-dlp.

Reads the youtube_channels list in pipeline/podcasts.json, finds uploads from the
last `days_back` days, and saves each one's English captions as Markdown in
research/transcripts/. Videos already transcribed (by this script or by
transcribe.py, matched on date and title) are skipped.

YouTube sometimes refuses cloud servers. When that happens this script prints the
error and exits 0, so the workflow can carry on with the Whisper route.

Usage:
  python3 pipeline/yt_captions.py
  python3 pipeline/yt_captions.py --days 3 --dry-run
"""
import argparse
import json
import pathlib
import re
import sys
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "pipeline" / "podcasts.json"
OUT = ROOT / "research" / "transcripts"


def slug(s, n=60):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:n].rstrip("-")


def vtt_to_lines(vtt):
    """Collapse a WebVTT file to '[mm:ss] text' lines, dropping repeated cues."""
    lines, last = [], None
    stamp = None
    for raw in vtt.splitlines():
        m = re.match(r"(\d\d):(\d\d):(\d\d)\.\d+ --> ", raw)
        if m:
            h, mi, s = map(int, m.groups())
            stamp = f"[{h*60+mi:02d}:{s:02d}]"
            continue
        if not raw.strip() or raw.startswith(("WEBVTT", "Kind:", "Language:")) or raw.strip().isdigit():
            continue
        text = re.sub(r"<[^>]+>", "", raw).strip()
        if text and text != last:
            lines.append(f"{stamp or ''} {text}".strip())
            last = text
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    import yt_dlp

    cfg = json.loads(CONFIG.read_text())
    days = args.days or cfg.get("days_back", 7)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    OUT.mkdir(parents=True, exist_ok=True)
    have = {p.stem for p in OUT.glob("*.md")}
    new = 0

    for ch in cfg.get("youtube_channels", []):
        name = ch["name"]
        list_opts = {"quiet": True, "extract_flat": True, "playlistend": 15}
        try:
            with yt_dlp.YoutubeDL(list_opts) as y:
                info = y.extract_info(ch["url"], download=False)
        except Exception as e:
            print(f"[{name}] could not list uploads: {e}", file=sys.stderr)
            continue
        for v in info.get("entries") or []:
            vid, title = v.get("id"), v.get("title", "")
            if not vid:
                continue
            opts = {
                "quiet": True,
                "skip_download": True,
                "writeautomaticsub": True,
                "writesubtitles": True,
                "subtitleslangs": ["en", "en-orig"],
                "subtitlesformat": "vtt",
                "outtmpl": str(OUT / "_tmp" / vid),
            }
            try:
                with yt_dlp.YoutubeDL(opts) as y:
                    meta = y.extract_info(f"https://www.youtube.com/watch?v={vid}", download=not args.dry_run)
            except Exception as e:
                print(f"  [{name}] {vid}: {e}", file=sys.stderr)
                continue
            ts = meta.get("timestamp") or meta.get("release_timestamp")
            when = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
            if when is None or when < since:
                continue
            day = when.strftime("%Y-%m-%d")
            stem = f"{day}-{slug(name, 20)}-{slug(title)}"
            if stem in have:
                print(f"  skip (have it): {title}")
                continue
            if args.dry_run:
                print(f"  would fetch captions: {title}")
                continue
            vtts = sorted((OUT / "_tmp").glob(f"{vid}*.vtt"))
            if not vtts:
                print(f"  no English captions: {title}")
                continue
            text = vtt_to_lines(vtts[0].read_text(encoding="utf-8", errors="ignore"))
            for f in vtts:
                f.unlink()
            body = (
                f"# {title}\n\n- Show: {name}\n- Published: {when.isoformat()}\n"
                f"- Link: https://www.youtube.com/watch?v={vid}\n"
                f"- Transcribed: {datetime.now(timezone.utc).isoformat(timespec='seconds')} from YouTube auto-captions\n\n"
                f"## Show notes\n\n{meta.get('description', '').strip()}\n\n## Transcript\n\n{text}\n"
            )
            (OUT / f"{stem}.md").write_text(body, encoding="utf-8")
            print(f"  wrote {stem}.md ({len(text.split())} words)")
            new += 1
    tmp = OUT / "_tmp"
    if tmp.exists() and not any(tmp.iterdir()):
        tmp.rmdir()
    print(f"{new} new caption transcript(s)")


if __name__ == "__main__":
    main()
