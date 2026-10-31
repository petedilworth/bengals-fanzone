"""Expected points examples for the weekly brief.

Two kinds of example, both from nflverse play-by-play, whose `ep` column is the nflfastR
expected points model and whose `epa` column is the change a play made to it:

  situations()  what a down, distance and field spot is worth: the average `ep` of every
                league play in that spot this season and last, early in a half, with the
                play count. Same five spots every week.
  plays()       real plays from each team's most recent game: our best and worst offensive
                play, our defence's best play, and the opponent's best and worst offensive play.

Pages only display this; the words that explain it live in data/explainers/.
"""
import re

import pandas as pd

# (label, down, distance, yards from the opponent's goal line, why it matters).
SITUATIONS = [
    ("1st-and-10 at your own 25", 1, 10, 75, "Where most drives start after a touchback."),
    ("3rd-and-8 at your own 30", 3, 8, 70, "The passing down a pass rush wants to force."),
    ("3rd-and-2 near midfield", 3, 2, 50, "Short yardage: run it or throw it quick."),
    ("1st-and-10 at the opponent's 25", 1, 10, 25, "The edge of field-goal range."),
    ("1st-and-goal at the 5", 1, 5, 5, "Touchdown or settle for three."),
]


def _snaps(pbp):
    p = pbp
    if "season_type" in p.columns:
        p = p[p["season_type"] == "REG"]
    p = p[p["play_type"].isin(["pass", "run"])]
    for c in ("qb_kneel", "qb_spike"):
        if c in p.columns:
            p = p[p[c] != 1]
    return p.dropna(subset=["ep", "epa"])


def situations(frames):
    """Average expected points per spot, early in a half, over all frames given."""
    p = pd.concat([_snaps(f) for f in frames if f is not None], ignore_index=True)
    # Early in a half, not inside the last four minutes, so the clock does not skew the value.
    p = p[p["half_seconds_remaining"] > 240]
    out = []
    for label, down, dist, yl, why in SITUATIONS:
        d = p[(p["down"] == down) & (p["ydstogo"].between(dist - 1, dist + 1))
              & (p["yardline_100"].between(yl - 3, yl + 3))]
        if label.startswith("1st-and-goal"):
            d = p[(p["down"] == 1) & (p["yardline_100"].between(yl - 1, yl + 1))]
        out.append({"label": label, "why": why, "ep": round(float(d["ep"].mean()), 1) if len(d) else None,
                    "n": int(len(d))})
    return out


def _clean(desc):
    s = re.sub(r"^\(\d+:\d+\)\s*", "", str(desc))
    s = re.sub(r"\((Shotgun|No Huddle|No Huddle, Shotgun|Run formation|Pass formation)\)\s*", "", s)
    s = re.sub(r"\b\d+-(?=[A-Z])", "", s)              # 9-J.Burrow -> J.Burrow
    s = re.split(r"\.\s+(?:Penalty|The penalty|PENALTY|The Replay|Replay)", s)[0]
    s = re.split(r"\s*\*\*", s)[0]                      # "** Injury Update ..." notes
    s = re.sub(r"\s*\([^)]*\)|\s*\[[^\]]*\]", "", s).strip()  # tacklers and QB hits in brackets
    s = s.rstrip(".")
    return s if len(s) <= 160 else s[:157].rsplit(" ", 1)[0] + "…"


ORD = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}


def _play(row, team, side, note):
    yl = int(row["yardline_100"])
    spot = f"{row['posteam']} {100 - yl}" if yl > 50 else ("midfield" if yl == 50 else f"{row['defteam']} {yl}")
    epa = float(row["epa"])
    return {
        "team": team, "side": side, "note": note,
        "week": int(row["week"]), "offence": row["posteam"], "defence": row["defteam"],
        "quarter": int(row["qtr"]), "clock": str(row["time"]),
        "situation": f"{ORD.get(int(row['down']), row['down'])}-and-{int(row['ydstogo'])} at {spot}",
        "text": _clean(row["desc"]),
        "ep_before": round(float(row["ep"]), 1),
        "epa": round(epa, 1),
        # Value from `team`'s point of view: a defensive stop is a gain for the defence.
        "for_team": round(epa if side == "offence" else -epa, 1),
    }


def _last_game(p, team):
    mine = p[(p["posteam"] == team) | (p["defteam"] == team)]
    if not len(mine):
        return None
    return mine[mine["week"] == mine["week"].max()]


def plays(pbp, team, opp):
    p = _snaps(pbp).dropna(subset=["down"])
    out = []
    g = _last_game(p, team)
    if g is not None:
        off, dfn = g[g["posteam"] == team], g[g["defteam"] == team]
        if len(off):
            out.append(_play(off.loc[off["epa"].idxmax()], team, "offence", "Best offensive play"))
            out.append(_play(off.loc[off["epa"].idxmin()], team, "offence", "Costliest offensive play"))
        if len(dfn):
            out.append(_play(dfn.loc[dfn["epa"].idxmin()], team, "defence", "Best defensive play"))
    g = _last_game(p, opp) if opp else None
    if g is not None:
        off = g[g["posteam"] == opp]
        if len(off):
            out.append(_play(off.loc[off["epa"].idxmax()], opp, "offence", "Best offensive play"))
            out.append(_play(off.loc[off["epa"].idxmin()], opp, "offence", "Costliest offensive play"))
    return out


def build(pbp, pbp_prev, team, opp, season):
    return {
        "season": season, "team": team, "opponent": opp,
        "situations": situations([pbp, pbp_prev]),
        "situations_seasons": f"{season - 1}–{str(season)[-2:]}",
        "plays": plays(pbp, team, opp),
        "source": "nflverse play-by-play (nflfastR expected points model)",
        "source_url": "https://github.com/nflverse/nflverse-data/releases/tag/pbp",
    }
