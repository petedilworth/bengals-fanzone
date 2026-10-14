"""Pull public NFL data (nflverse) into a local cache and report how fresh each source is.

Every source is pulled whole: every team, player and play. Nothing here is Bengals-specific,
so later questions (run game, passing game, any position) reuse the same pulls.

A source that is missing (404) or fails is recorded as unavailable and does not stop the run.
"""
import datetime as dt
import gzip
import io
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
    "pbp": (f"{BASE}/pbp/play_by_play_{{season}}.csv.gz", "nflverse play-by-play", "season"),
    "ftn": (f"{BASE}/ftn_charting/ftn_charting_{{season}}.csv", "FTN charting (via nflverse)", "season"),
    "pfr_pass": (f"{BASE}/pfr_advstats/advstats_week_pass_{{season}}.csv", "Pro Football Reference weekly passing (via nflverse)", "season"),
    "pfr_rush": (f"{BASE}/pfr_advstats/advstats_week_rush_{{season}}.csv", "Pro Football Reference weekly rushing (via nflverse)", "season"),
    "pfr_rec": (f"{BASE}/pfr_advstats/advstats_week_rec_{{season}}.csv", "Pro Football Reference weekly receiving (via nflverse)", "season"),
    "pfr_def": (f"{BASE}/pfr_advstats/advstats_week_def_{{season}}.csv", "Pro Football Reference weekly defence (via nflverse)", "season"),
    "ngs_passing": (f"{BASE}/nextgen_stats/ngs_passing.csv.gz", "Next Gen Stats passing (via nflverse)", "all"),
    "ngs_rushing": (f"{BASE}/nextgen_stats/ngs_rushing.csv.gz", "Next Gen Stats rushing (via nflverse)", "all"),
    "ngs_receiving": (f"{BASE}/nextgen_stats/ngs_receiving.csv.gz", "Next Gen Stats receiving (via nflverse)", "all"),
    "snap_counts": (f"{BASE}/snap_counts/snap_counts_{{season}}.csv", "Snap counts (via nflverse)", "season"),
    "injuries": (f"{BASE}/injuries/injuries_{{season}}.csv", "Injury reports (via nflverse)", "season"),
    "depth_charts": (f"{BASE}/depth_charts/depth_charts_{{season}}.csv", "Depth charts (via nflverse)", "season"),
    "rosters": (f"{BASE}/weekly_rosters/roster_weekly_{{season}}.csv", "Weekly rosters (via nflverse)", "season"),
}


def _fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def pull(name, season, force=False):
    """Download one source into data/raw/. Returns a manifest entry."""
    url, label, kind = SOURCES[name]
    url = url.format(season=season)
    dest = RAW / (f"{name}_{season}" if kind == "season" else name)
    dest = dest.with_suffix(".csv.gz" if url.endswith(".gz") else ".csv")
    entry = {"name": name, "label": label, "url": url, "file": str(dest.relative_to(ROOT)),
             "pulled": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "ok": False}
    RAW.mkdir(parents=True, exist_ok=True)
    try:
        if force or not dest.exists() or _is_stale(dest):
            data = _fetch(url)
            dest.write_bytes(data)
            entry["bytes"] = len(data)
        else:
            entry["bytes"] = dest.stat().st_size
            entry["cached"] = True
        entry["ok"] = True
    except urllib.error.HTTPError as e:
        entry["error"] = f"HTTP {e.code}"
    except Exception as e:  # network errors must not kill the whole run
        entry["error"] = str(e)[:200]
    if not entry["ok"]:
        print(f"[{name}] unavailable: {entry.get('error')}", file=sys.stderr)
    return entry


def _is_stale(path, hours=6):
    age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc)
    return age > dt.timedelta(hours=hours)


def load(name, season):
    """Read a pulled source as a DataFrame, or None if it was unavailable."""
    url, _, kind = SOURCES[name]
    dest = RAW / (f"{name}_{season}" if kind == "season" else name)
    dest = dest.with_suffix(".csv.gz" if url.endswith(".gz") else ".csv")
    if not dest.exists():
        return None
    df = pd.read_csv(dest, low_memory=False)
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"sources": entries, **extra}, indent=2) + "\n")
