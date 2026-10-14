"""ESPN win rates: read the leaderboard article and keep every team and every listed player.

ESPN publishes pass rush, run stop, pass block and run block win rates as an article with
tables, not as a feed. The article's address changes each season; it lives in the output
file itself (data/stats/espn-winrates.json) so the pipeline can find it.

If the fetch or the parse fails, the previous file is kept and marked stale. The page is
read with a plain request; nothing here logs in or bypasses anything.
"""
import datetime as dt
import html
import json
import pathlib
import re
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"}
METRICS = ["pass_rush_win_rate", "run_stop_win_rate", "pass_block_win_rate", "run_block_win_rate"]  # ESPN's column order
TEAM_ROW = re.compile(r"([A-Z][A-Za-z0-9.' ]+?) (\d+)% \((\d+)\) (\d+)% \((\d+)\) (\d+)% \((\d+)\) (\d+)% \((\d+)\)")
PLAYER_TABLE = re.compile(r"((?:Edge|DT|OT|IOL) (?:pass rush|run stop|pass block|run block) win rate rankings) Rank Name Team Wins Plays")
PLAYER_ROW = re.compile(r"(\d{1,2}) ([A-Z][A-Za-z'.-]+(?: [A-Z][A-Za-z'.-]+| Jr \.| Sr \.| I{2,3}){0,3}) ([A-Z]{2,3}) (\d+) (\d+) (\d+)% (\d+)%")


def page_text(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        raw = r.read().decode("utf-8", errors="ignore")
    text = re.sub(r"<script.*?</script>", " ", raw, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text))


def parse(text):
    header = "team PRWR RSWR PBWR RBWR"
    i = text.find(header)
    if i < 0:
        raise ValueError("team table header not found")
    i += len(header)
    league = {}
    for m in TEAM_ROW.finditer(text[i: i + 6000]):
        name = m.group(1).strip()
        vals = [int(m.group(k)) for k in range(2, 10)]
        league[name] = {METRICS[j]: {"value": vals[2 * j] / 100, "rank": vals[2 * j + 1]} for j in range(4)}
        if len(league) == 32:
            break
    if len(league) < 30:
        raise ValueError(f"only {len(league)} team rows parsed")
    players = {}
    starts = [(m.start(), m.group(1)) for m in PLAYER_TABLE.finditer(text)]
    for k, (pos, title) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else min(len(text), pos + 5000)
        rows = []
        for r in PLAYER_ROW.finditer(text[pos:end]):
            rows.append({"rank": int(r.group(1)), "name": r.group(2).replace(" .", "."), "team": r.group(3),
                         "wins": int(r.group(4)), "plays": int(r.group(5)), "win_rate": int(r.group(6)) / 100,
                         "double_team_rate": int(r.group(7)) / 100})
        players[title] = rows
    m = re.search(r"((?:Updated|Through|As of)[^|]{0,120}?(?:a\.m\.|p\.m\.) ET)", text)
    if not m:  # ESPN sometimes puts only the date line right before its "Jump to:" index
        m = re.search(r"([A-Z][a-z]{2,8}\.? \d{1,2}[^|]{0,60}?(?:a\.m\.|p\.m\.) ET)(?= Jump to:)", text)
    return league, players, (m.group(1).strip() if m else None)


TEAM_NAMES = {"CIN": "Cincinnati Bengals"}


def refresh(path, team_abbr):
    """Rewrite data/stats/espn-winrates.json from ESPN's page. Returns a status string."""
    path = pathlib.Path(path)
    prev = json.loads(path.read_text()) if path.exists() else {}
    url = prev.get("url")
    if not url:
        return "no url in espn-winrates.json; skipped"
    today = dt.date.today().isoformat()
    try:
        league, players, updated = parse(page_text(url))
    except Exception as e:  # keep the last good numbers, say so
        prev["stale"] = {"checked": today, "error": str(e)[:200]}
        path.write_text(json.dumps(prev, indent=2, ensure_ascii=False) + "\n")
        print(f"[espn] kept previous file: {e}", file=sys.stderr)
        return f"stale ({e})"
    team_name = TEAM_NAMES.get(team_abbr, team_abbr)
    mine = league.get(team_name)
    out = {
        "_note": "Written by pipeline/nfl/espn.py from ESPN's win-rate leaderboard. Change `url` when ESPN starts a new season's article.",
        "source": prev.get("source", "ESPN win rates leaderboard"), "url": url, "as_of": today,
        "espn_updated_line": updated, "team": team_abbr,
        **(mine or {}),
        "league": league,
        "players": players,
        "team_players": [dict(table=t, **r) for t, rows in players.items() for r in rows if r["team"] == team_abbr],
    }
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    return f"ok: {len(league)} teams, {sum(len(v) for v in players.values())} players, {len(out['team_players'])} {team_abbr}"
