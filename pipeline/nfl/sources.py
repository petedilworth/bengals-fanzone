"""Pull public NFL data (nflverse) into a local cache and report how fresh each source is.

Every source is pulled whole: every team, player and play. Nothing here is Bengals-specific,
so later questions (run game, passing game, any position) reuse the same pulls.

Downloads are kept small three ways:
- parquet files, not CSV (depth charts: 2.6 MB instead of 58 MB);
- a finished season is static, so it is pulled once and never again;
- each file's ETag is kept next to it and sent back as If-None-Match. GitHub answers
  304 when the file has not changed, and nothing is downloaded.

A source that is missing (404) or fails is recorded as unavailable and does not stop the run.
"""
import datetime as dt
import json
import pathlib
import sys
import urllib.error
import urllib.request

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
BASE = "https://github.com/nflverse/nflverse-data/releases/download"
UA = {"User-Agent": "bengals-fanzone stats pipeline (personal, non-commercial)"}

# name -> (url template, human label, kind). {season} is filled in. "all" files hold every season.
SOURCES = {
    "pbp": (f"{BASE}/pbp/play_by_play_{{season}}.parquet", "nflverse play-by-play", "season"),
    "ftn": (f"{BASE}/ftn_charting/ftn_charting_{{season}}.parquet", "FTN charting (via nflverse)", "season"),
    "pfr_pass": (f"{BASE}/pfr_advstats/advstats_week_pass_{{season}}.parquet", "Pro Football Reference weekly passing (via nflverse)", "season"),
    "pfr_rush": (f"{BASE}/pfr_advstats/advstats_week_rush_{{season}}.parquet", "Pro Football Reference weekly rushing (via nflverse)", "season"),
    "pfr_rec": (f"{BASE}/pfr_advstats/advstats_week_rec_{{season}}.parquet", "Pro Football Reference weekly receiving (via nflverse)", "season"),
    "pfr_def": (f"{BASE}/pfr_advstats/advstats_week_def_{{season}}.parquet", "Pro Football Reference weekly defence (via nflverse)", "season"),
    "ngs_passing": (f"{BASE}/nextgen_stats/ngs_passing.parquet", "Next Gen Stats passing (via nflverse)", "all"),
    "ngs_rushing": (f"{BASE}/nextgen_stats/ngs_rushing.parquet", "Next Gen Stats rushing (via nflverse)", "all"),
    "ngs_receiving": (f"{BASE}/nextgen_stats/ngs_receiving.parquet", "Next Gen Stats receiving (via nflverse)", "all"),
    "snap_counts": (f"{BASE}/snap_counts/snap_counts_{{season}}.parquet", "Snap counts (via nflverse)", "season"),
    "injuries": (f"{BASE}/injuries/injuries_{{season}}.parquet", "Injury reports (via nflverse)", "season"),
    "depth_charts": (f"{BASE}/depth_charts/depth_charts_{{season}}.parquet", "Depth charts (via nflverse)", "season"),
    "rosters": (f"{BASE}/weekly_rosters/roster_weekly_{{season}}.parquet", "Weekly rosters (via nflverse)", "season"),
}


def _path(name, season):
    url, _, kind = SOURCES[name]
    return RAW / (f"{name}_{season}.parquet" if kind == "season" else f"{name}.parquet"), url.format(season=season)


def pull(name, season, force=False, static=False):
    """Download one source into data/raw/ if it changed. Returns a manifest entry.

    static=True means the file never changes once present (a finished season): skip the request.
    """
    dest, url = _path(name, season)
    label = SOURCES[name][1]
    entry = {"name": name, "season": season, "label": label, "url": url, "file": str(dest.relative_to(ROOT)),
             "checked": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "ok": False, "downloaded": 0}
    RAW.mkdir(parents=True, exist_ok=True)
    etag_file = dest.with_suffix(".etag")
    if static and dest.exists() and not force:
        entry.update(ok=True, cached=True, note="finished season, never re-pulled")
        return entry
    headers = dict(UA)
    if dest.exists() and etag_file.exists() and not force:
        headers["If-None-Match"] = etag_file.read_text().strip()
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=300) as r:
            data = r.read()
            dest.write_bytes(data)
            if r.headers.get("ETag"):
                etag_file.write_text(r.headers["ETag"])
            entry.update(ok=True, downloaded=len(data))
    except urllib.error.HTTPError as e:
        if e.code == 304:
            entry.update(ok=True, cached=True, note="unchanged (304)")
        else:
            entry["error"] = f"HTTP {e.code}"
    except Exception as e:  # network errors must not kill the whole run
        entry["error"] = str(e)[:200]
    if not entry["ok"]:
        if dest.exists():
            entry.update(ok=True, cached=True, note=f"using cached copy after {entry['error']}")
        else:
            print(f"[{name} {season}] unavailable: {entry.get('error')}", file=sys.stderr)
    return entry


def load(name, season):
    """Read a pulled source as a DataFrame, or None if it was unavailable."""
    dest, _ = _path(name, season)
    if not dest.exists():
        return None
    df = pd.read_parquet(dest)
    kind = SOURCES[name][2]
    if kind == "all" and "season" in df.columns:
        df = df[df["season"] == season]
    return df


def through_week(df, team, team_col, week_col="week"):
    """Latest regular-season week in which `team` appears, or 0."""
    if df is None or team_col not in df.columns or week_col not in df.columns:
        return 0
    rows = df[df[team_col] == team]
    if "season_type" in rows.columns:
        rows = rows[rows["season_type"] == "REG"]
    if "game_type" in rows.columns:
        rows = rows[rows["game_type"] == "REG"]
    return int(rows[week_col].max()) if len(rows) else 0


def write_manifest(entries, extra, path):
    total = sum(e.get("downloaded", 0) for e in entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"downloaded_bytes": total, "sources": entries, **extra}, indent=2) + "\n")
    return total
