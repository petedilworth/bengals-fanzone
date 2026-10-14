"""Offensive line metrics from the pulled sources.

Everything returns plain dicts with a play count ("n") on every number, so the site can grey
out small samples. Ranks are 1 = best out of 32. Functions take whole-league frames and a team,
so the same code answers "what does Baltimore allow" and "what does Cincinnati do".
"""
import math

import pandas as pd

GAPS = ["left end", "left tackle", "left guard", "middle", "right guard", "right tackle", "right end"]


def _r(x, d=3):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), d)


def _rank(series, higher_is_better):
    """Rank a per-team series, 1 = best. Returns {team: rank}."""
    s = series.dropna()
    return s.rank(ascending=not higher_is_better, method="min").astype(int).to_dict()


# ---------- play filters ----------

def reg(pbp):
    return pbp[pbp["season_type"] == "REG"] if "season_type" in pbp else pbp


def dropbacks(pbp):
    p = reg(pbp)
    return p[(p["qb_dropback"] == 1) & (p["qb_spike"] != 1) & (p["two_point_attempt"] != 1) & p["posteam"].notna()]


def designed_runs(pbp):
    p = reg(pbp)
    r = p[(p["rush_attempt"] == 1) & (p["qb_scramble"] != 1) & (p["two_point_attempt"] != 1) & p["posteam"].notna()].copy()
    loc, gap = r["run_location"], r["run_gap"]
    r["gap"] = loc.where(loc == "middle", loc.astype(str) + " " + gap.astype(str))
    r.loc[loc.isna(), "gap"] = None
    r = r[r["gap"].isin(GAPS)]
    return r


def with_ftn(pbp, ftn):
    if ftn is None:
        return pbp.assign(is_play_action=None, n_pass_rushers=None, is_qb_fault_sack=None)
    cols = ["nflverse_game_id", "nflverse_play_id", "is_play_action", "n_pass_rushers", "n_blitzers", "is_qb_fault_sack"]
    f = ftn[[c for c in cols if c in ftn.columns]].rename(columns={"nflverse_game_id": "game_id", "nflverse_play_id": "play_id"})
    return pbp.merge(f, on=["game_id", "play_id"], how="left")


# ---------- question 1: who is to blame for sacks? ----------

def protection(pbp, ftn, pfr, ngs, team):
    db = with_ftn(dropbacks(pbp), ftn)
    out = {}

    # League table: sack rate per team.
    per_team = db.groupby("posteam").agg(dropbacks=("sack", "size"), sacks=("sack", "sum"))
    per_team["sack_rate"] = per_team["sacks"] / per_team["dropbacks"]
    rank = _rank(per_team["sack_rate"], higher_is_better=False)
    t = per_team.loc[team] if team in per_team.index else None
    out["sack_rate"] = {"value": _r(t["sack_rate"]) if t is not None else None, "n": int(t["dropbacks"]) if t is not None else 0,
                        "sacks": int(t["sacks"]) if t is not None else 0, "rank": rank.get(team),
                        "league": _r(per_team["sacks"].sum() / per_team["dropbacks"].sum())}

    # FTN: sacks charted as the QB's fault.
    mine = db[db["posteam"] == team]
    if "is_qb_fault_sack" in mine and mine["is_qb_fault_sack"].notna().any():
        sacks = mine[mine["sack"] == 1]
        fault = sacks["is_qb_fault_sack"].astype(str).str.lower().isin(["true", "1", "1.0"]).sum()
        out["qb_fault_sacks"] = {"value": int(fault), "n": int(len(sacks)), "label": "FTN charted as QB fault"}

    # By number of pass rushers (FTN).
    if "n_pass_rushers" in mine and mine["n_pass_rushers"].notna().any():
        m = mine[mine["n_pass_rushers"].notna()].copy()
        m["bucket"] = pd.cut(m["n_pass_rushers"], [-1, 3, 4, 99], labels=["3 or fewer", "4", "5 or more"])
        g = m.groupby("bucket", observed=True).agg(n=("epa", "size"), epa=("epa", "mean"), sacks=("sack", "sum"))
        out["by_rushers"] = [{"label": str(k), "n": int(v["n"]), "epa": _r(v["epa"]), "sacks": int(v["sacks"]),
                              "sack_rate": _r(v["sacks"] / v["n"])} for k, v in g.iterrows()]

    # PFR: pressures per dropback, team level, for the weeks PFR covers.
    if pfr is not None and len(pfr):
        p = pfr[pfr.get("game_type", "REG") == "REG"] if "game_type" in pfr else pfr
        pt = p.groupby(["team", "week"]).agg(pressured=("times_pressured", "sum"), blitzed=("times_blitzed", "sum"),
                                             hurried=("times_hurried", "sum"), hit=("times_hit", "sum")).reset_index()
        # PFR posts teams at different times, so count each team's dropbacks only in the weeks PFR has for it.
        weeks_by_team = pt.groupby("team")["week"].apply(set)
        dbw = pd.Series({t: int(d[d["week"].isin(weeks_by_team.get(t, set()))].shape[0]) for t, d in db.groupby("posteam")})
        tot = pt.groupby("team")["pressured"].sum()
        rate = (tot / dbw.replace(0, pd.NA)).dropna().astype(float)
        prank = _rank(rate, higher_is_better=False)
        out["pressure_rate"] = {"value": _r(rate.get(team)), "n": int(dbw.get(team, 0)), "pressures": int(tot.get(team, 0)),
                                "rank": prank.get(team), "league": _r(tot.sum() / dbw.sum()),
                                "through_week": int(max(weeks_by_team.get(team, {0})))}
        out["_pfr_weekly"] = pt[pt["team"] == team].set_index("week")[["pressured", "blitzed", "hurried", "hit"]].to_dict("index")

    # NGS: time to throw, weighted by attempts, team level.
    if ngs is not None and len(ngs):
        n = ngs[(ngs["week"] > 0) & ngs["avg_time_to_throw"].notna()]
        n = n.assign(w=n["avg_time_to_throw"] * n["attempts"])
        tt = n.groupby("team_abbr").agg(w=("w", "sum"), a=("attempts", "sum"))
        tt = (tt["w"] / tt["a"]).dropna()
        out["time_to_throw"] = {"value": _r(tt.get(team), 2), "n": int(n[n["team_abbr"] == team]["attempts"].sum()),
                                "league": _r(tt.mean(), 2), "rank_fastest": _rank(tt, higher_is_better=False).get(team)}
        out["_ngs_weekly"] = {int(r.week): _r(r.w / r.attempts, 2) for r in n[n["team_abbr"] == team].groupby("week").agg(w=("w", "sum"), attempts=("attempts", "sum")).reset_index().itertuples()}

    # Weekly line for the team.
    wk = mine.groupby(["week", "defteam"]).agg(dropbacks=("sack", "size"), sacks=("sack", "sum"), epa=("epa", "mean")).reset_index()
    out["weekly"] = []
    for r in wk.itertuples():
        row = {"week": int(r.week), "opp": r.defteam, "dropbacks": int(r.dropbacks), "sacks": int(r.sacks), "epa": _r(r.epa)}
        pf = out.get("_pfr_weekly", {}).get(int(r.week))
        if pf:
            row.update({"pressures": int(pf["pressured"]), "blitzed": int(pf["blitzed"])})
        if int(r.week) in out.get("_ngs_weekly", {}):
            row["time_to_throw"] = out["_ngs_weekly"][int(r.week)]
        out["weekly"].append(row)
    out.pop("_pfr_weekly", None)
    out.pop("_ngs_weekly", None)
    return out


# ---------- question 2: does the run set up the pass? ----------

def run_sets_up_pass(pbp, ftn, team):
    p = reg(pbp).sort_values(["game_id", "play_id"]).copy()
    p["is_db"] = (p["qb_dropback"] == 1) & (p["qb_spike"] != 1) & (p["two_point_attempt"] != 1)
    p["is_run"] = (p["rush_attempt"] == 1) & (p["qb_scramble"] != 1) & (p["two_point_attempt"] != 1)
    grp = p.groupby(["game_id", "drive", "posteam"], sort=False)
    p["prev_run"] = grp["is_run"].shift(1)
    p["prev_success"] = grp["success"].shift(1)
    db = with_ftn(p[p["is_db"] & p["posteam"].notna()], ftn)
    out = {}

    def block(d):
        return {"n": int(len(d)), "epa": _r(d["epa"].mean()), "success": _r(d["success"].mean())}

    mine = db[db["posteam"] == team]
    if "is_play_action" in db and db["is_play_action"].notna().any():
        pa = db["is_play_action"].astype(str).str.lower().isin(["true", "1", "1.0"])
        out["play_action"] = block(mine[pa[mine.index]])
        out["no_play_action"] = block(mine[~pa[mine.index]])
        # League rank on play-action EPA per play (teams with 20+ play-action dropbacks).
        lg = db[pa].groupby("posteam").agg(n=("epa", "size"), epa=("epa", "mean"))
        lg = lg[lg["n"] >= 20]
        out["play_action"]["rank"] = _rank(lg["epa"], higher_is_better=True).get(team)
        out["play_action"]["league"] = _r(db[pa]["epa"].mean())
        out["no_play_action"]["league"] = _r(db[~pa]["epa"].mean())
    out["after_successful_run"] = block(mine[(mine["prev_run"] == True) & (mine["prev_success"] == 1)])
    out["after_failed_run"] = block(mine[(mine["prev_run"] == True) & (mine["prev_success"] == 0)])
    out["after_pass"] = block(mine[(mine["prev_run"] == False)])
    lg_succ = db[(db["prev_run"] == True) & (db["prev_success"] == 1)]["epa"].mean()
    lg_fail = db[(db["prev_run"] == True) & (db["prev_success"] == 0)]["epa"].mean()
    out["after_successful_run"]["league"] = _r(lg_succ)
    out["after_failed_run"]["league"] = _r(lg_fail)
    wk = []
    for w, d in mine.groupby("week"):
        row = {"week": int(w), "opp": d["defteam"].iloc[0], "dropbacks": int(len(d)), "epa": _r(d["epa"].mean())}
        if "is_play_action" in d and d["is_play_action"].notna().any():
            pa = d["is_play_action"].astype(str).str.lower().isin(["true", "1", "1.0"])
            row.update({"pa_n": int(pa.sum()), "pa_epa": _r(d[pa]["epa"].mean()) if pa.sum() else None})
        wk.append(row)
    out["weekly"] = wk
    return out


# ---------- question 3: where to attack? ----------

def run_by_gap(pbp, team, side):
    """side='posteam' -> what the team's offence does; side='defteam' -> what its defence allows."""
    r = designed_runs(pbp)
    per = r.groupby([side, "gap"]).agg(n=("epa", "size"), epa=("epa", "mean"), success=("success", "mean"), ypc=("rushing_yards", "mean"))
    league = r.groupby("gap").agg(epa=("epa", "mean"), success=("success", "mean"), ypc=("rushing_yards", "mean"))
    rows = []
    for g in GAPS:
        if (team, g) in per.index:
            v = per.loc[(team, g)]
            # Rank among teams on success rate in this gap (teams with 8+ runs there).
            lg = per.xs(g, level="gap")
            lg = lg[lg["n"] >= 8]
            rank = _rank(lg["success"], higher_is_better=(side == "posteam")).get(team)
            rows.append({"gap": g, "n": int(v["n"]), "epa": _r(v["epa"]), "success": _r(v["success"]), "ypc": _r(v["ypc"], 1),
                         "league_success": _r(league.loc[g, "success"]), "league_epa": _r(league.loc[g, "epa"]), "rank": rank})
        else:
            rows.append({"gap": g, "n": 0, "epa": None, "success": None, "ypc": None,
                         "league_success": _r(league.loc[g, "success"]) if g in league.index else None, "league_epa": None, "rank": None})
    tot = r[r[side] == team]
    overall = {"n": int(len(tot)), "epa": _r(tot["epa"].mean()), "success": _r(tot["success"].mean()), "ypc": _r(tot["rushing_yards"].mean(), 1),
               "league_success": _r(r["success"].mean()), "league_ypc": _r(r["rushing_yards"].mean(), 1)}
    allt = r.groupby(side).agg(n=("epa", "size"), success=("success", "mean"))
    overall["rank"] = _rank(allt[allt["n"] >= 40]["success"], higher_is_better=(side == "posteam")).get(team)
    weekly = [{"week": int(w), "opp": d["defteam" if side == "posteam" else "posteam"].iloc[0], "n": int(len(d)),
               "success": _r(d["success"].mean()), "ypc": _r(d["rushing_yards"].mean(), 1)} for w, d in tot.groupby("week")]
    return {"gaps": rows, "overall": overall, "weekly": weekly}
