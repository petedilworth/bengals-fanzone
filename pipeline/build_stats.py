#!/usr/bin/env python3
"""Pull every source, work out how fresh each one is, compute the line stats and write JSON.

Outputs (all under data/):
  stats/sources.json  - what was pulled, when, and which week each source runs through
  stats/line.json     - the three offensive-line questions, this season and last, with ranks
  season-<year>.json  - results and scores filled in from play-by-play for finished games

Usage: python3 pipeline/build_stats.py [--force] [--no-pull]
"""
import argparse
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from nfl import espn, metrics, sources  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def next_opponent(season, current_week=None):
    """First scheduled game without a result. Does not depend on team.json's currentWeek,
    which moves to the coming week as soon as its brief goes up."""
    for g in season["games"]:
        if not g.get("bye") and not g.get("result"):
            return g["opp"], g["week"]
    return None, None


def league_week(df, week_col, game_col, min_games=13):
    """Latest regular-season week with at least `min_games` games in the file: the most
    byes in one week is six teams, so 13 games means the week has been played. A week
    with only Thursday's game in it does not count yet."""
    if df is None or week_col not in df.columns or game_col not in df.columns:
        return 0
    d = df
    for c in ("season_type", "game_type"):
        if c in d.columns:
            d = d[d[c] == "REG"]
    counts = d.groupby(week_col)[game_col].nunique()
    if game_col in ("team", "team_abbr"):
        counts = counts / 2
    done = counts[counts >= min_games]
    return int(done.index.max()) if len(done) else 0


def ftn_through_week(ftn, team):
    """FTN game ids look like 2026_05_CIN_MIA; the week is the second part."""
    if ftn is None or "nflverse_game_id" not in ftn.columns:
        return 0
    ids = ftn["nflverse_game_id"].astype(str)
    mine = ids[ids.str.endswith(f"_{team}") | ids.str.contains(f"_{team}_")]
    return int(mine.str.split("_").str[1].astype(int).max()) if len(mine) else 0


def update_results(season_doc, pbp, team):
    """Fill result and score for finished games, from play-by-play final scores."""
    if pbp is None:
        return 0
    p = pbp[(pbp["season_type"] == "REG") & ((pbp["home_team"] == team) | (pbp["away_team"] == team))]
    finals = p.groupby("week").agg(home=("home_team", "first"), away=("away_team", "first"),
                                   hs=("home_score", "max"), as_=("away_score", "max"))
    changed = 0
    wins = losses = 0
    for g in season_doc["games"]:
        if g.get("bye"):
            continue
        if g["week"] in finals.index:
            f = finals.loc[g["week"]]
            us, them = (f["hs"], f["as_"]) if f["home"] == team else (f["as_"], f["hs"])
            res = "W" if us > them else "L" if us < them else "T"
            score = f"{int(us)}–{int(them)}"
            if g.get("result") != res or g.get("score") != score:
                g["result"], g["score"] = res, score
                changed += 1
        if g.get("result") == "W":
            wins += 1
        elif g.get("result") == "L":
            losses += 1
    season_doc["record"] = f"{wins}–{losses}"
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download even if cached recently")
    ap.add_argument("--no-pull", action="store_true", help="use the local cache only")
    args = ap.parse_args()

    team_doc = json.loads((DATA / "team.json").read_text())
    team, season = team_doc["abbr"], team_doc["currentSeason"]
    season_path = DATA / f"season-{season}.json"
    season_doc = json.loads(season_path.read_text())
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    # 1. Pull everything, this season and last.
    manifest = []
    if not args.no_pull:
        for name in sources.SOURCES:
            for yr in ([season, season - 1] if sources.SOURCES[name][2] == "season" else [season]):
                manifest.append(sources.pull(name, yr, force=args.force, static=(yr < season)))

    pbp = sources.load("pbp", season)
    ftn = sources.load("ftn", season)
    pfr = sources.load("pfr_pass", season)
    ngs = sources.load("ngs_passing", season)
    pbp_prev, ftn_prev = sources.load("pbp", season - 1), sources.load("ftn", season - 1)
    pfr_prev, ngs_prev = sources.load("pfr_pass", season - 1), sources.load("ngs_passing", season - 1)
    if pbp is None:
        sys.exit("No play-by-play for this season; nothing to compute.")

    # 2. Results from play-by-play, then freshness per source.
    changed = update_results(season_doc, pbp, team)
    played = [g["week"] for g in season_doc["games"] if g.get("result")]
    expected = max(played) if played else 0
    fresh = {
        "pbp": sources.through_week(pbp, team, "posteam"),
        "ftn": ftn_through_week(ftn, team),
        "pfr_pass": sources.through_week(pfr, team, "team"),
        "ngs_passing": sources.through_week(ngs, team, "team_abbr"),
    }
    league = {
        "pbp": league_week(pbp, "week", "game_id"),
        "ftn": league_week(ftn, "week", "nflverse_game_id"),
        "pfr_pass": league_week(pfr, "week", "team"),
        "ngs_passing": league_week(ngs, "week", "team_abbr"),
    }
    byes = [g["week"] for g in season_doc["games"] if g.get("bye")]
    # through_week is the league's latest played week in the file (ranks, averages, the
    # opponent); team_through_week is our team's latest game in it. "pending" still means
    # our latest game is missing, which is what the re-pull loop waits for.
    status = {k: {"through_week": max(league[k], fresh[k]), "team_through_week": fresh[k],
                  "expected_week": expected, "pending": fresh[k] < expected} for k in fresh}
    for k, v in status.items():
        print(f"[{k}] league through week {v['through_week']}, {team} through week {v['team_through_week']} "
              f"(expected {expected}){' - PENDING' if v['pending'] else ''}")

    # 3. Metrics.
    opp, opp_week = next_opponent(season_doc, team_doc["currentWeek"])
    line = {
        "generated": now, "season": season, "team": team, "status": status, "bye_weeks": byes,
        "next_opponent": {"abbr": opp, "week": opp_week},
        "protection": metrics.protection(pbp, ftn, pfr, ngs, team),
        "run_sets_up_pass": metrics.run_sets_up_pass(pbp, ftn, team),
        "offence_by_gap": metrics.run_by_gap(pbp, team, "posteam"),
        "opponent_defence_by_gap": metrics.run_by_gap(pbp, opp, "defteam") if opp else None,
        "own_defence_by_gap": metrics.run_by_gap(pbp, team, "defteam"),
    }
    if pbp_prev is not None:
        line["last_season"] = {
            "season": season - 1,
            "protection": metrics.protection(pbp_prev, ftn_prev, pfr_prev, ngs_prev, team),
            "run_sets_up_pass": metrics.run_sets_up_pass(pbp_prev, ftn_prev, team),
            "offence_by_gap": metrics.run_by_gap(pbp_prev, team, "posteam"),
        }
        for k in ("protection", "run_sets_up_pass", "offence_by_gap"):
            line["last_season"][k].pop("weekly", None)

    # 4. ESPN win rates (article page, no feed). Keeps the last good file if the page changes shape.
    if not args.no_pull:
        print("[espn]", espn.refresh(DATA / "stats" / "espn-winrates.json", team))

    # 5. Write.
    (DATA / "stats").mkdir(exist_ok=True)
    (DATA / "stats" / "line.json").write_text(json.dumps(line, indent=1) + "\n")
    total = sources.write_manifest(manifest, {"generated": now, "status": status}, DATA / "stats" / "sources.json")
    print(f"downloaded {total/1048576:.1f} MB this run")
    if changed:
        season_path.write_text(json.dumps(season_doc, indent=2, ensure_ascii=False) + "\n")
        print(f"season file: {changed} game(s) updated, record {season_doc['record']}")
    print("wrote data/stats/line.json")


if __name__ == "__main__":
    main()
