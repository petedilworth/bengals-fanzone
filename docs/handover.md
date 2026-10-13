> **History, not rules.** This is the original handover from the Claude chat session (Oct 8–13, 2026).
> Many points were changed on Oct 13 (no hit rate, no grading, watch items are not predictions, smaller home page).
> `CLAUDE.md` and `NEXT.md` win wherever they differ.

# Bengals Fanzone – Handover

Handover from a Claude chat session (Oct 8–13, 2026) to Claude Code.
Repo: `bengals-fanzone` · Hosting: GitHub Pages · Owner: Pedro (Toronto, ET).

## 1. What we are building

A personal Cincinnati Bengals fan site with three jobs:

1. **Stats** – team and player numbers by week, with an offensive line focus.
2. **Key weekly insights** – ranked storylines, Devil's Advocate, and the opponent's view.
3. **Game-watching prep** – a "what to watch for" list in game order, graded after the game.

It replaces a single-page artifact that hit its limits: it had no live data fetch, no back end and no multi-page structure.

## 2. Owner rules

See `CLAUDE.md` for the current version.

## 3. State as of Tue Oct 13, 2026

### Live artifact (the old system)
- Page: https://claude.ai/artifact/7bfuM1SCYcdZJWoiVMRcca ("Bengals Season Brief"), shared by link.
- Layout: season strip → scoreboard → "What the result means" → Main storylines (5) → What to watch for (6 graded calls) → position room → Devil's Advocate and Alternative view → Past weeks → sources.
- Saved as `docs/reference-week5-page.html`.

### Scheduled tasks (cloud, auto-approve, push alerts)
| Task | When (ET) | What it does | ID |
|---|---|---|---|
| Weekly Bengals season page update | Fri 8:46 am | Archives last week, updates the strip, writes the new week, sends a 3-line summary | `trig_01WFB8pQxGYVUvWzVbgjuWHE` |
| Bengals Monday grading | Mon 11:52 am | Grades each watch call, adds the score, scorecard and "What the result means" | `trig_011ywrxpNpWVgJs8UmGXVFTY` |

Cutover: repoint or disable both tasks once the site is live. Don't run both systems for long.

### Week 5 grading result
Scorecard: 2 of 6 right, 2 partly, 1 wrong, 1 didn't happen.
- The brief said forcing carries "pays poorly". Cincinnati won by running: 31 carries for 117 yards, a season high.
- It flagged Jordan Battle for missed tackles. Battle made both interceptions.
- It missed the real problem: Miami ran for 217 yards against the Bengals' defence.
- Two calls were checklists, not predictions.

Lesson still in force: always cover both sides of the ball.

## 4. Season data

See `data/season-2026.json`. Record after Week 5: 3–2.

**Context worth keeping**
- Receivers: Dohnte Meyers came from the CFL (Saskatchewan, 89 catches and 1,405 yards over 2 seasons), signed January 2026. Mitchell Tinsley re-signed Sept. 29 from Houston's practice squad. Andrei Iosivas is on injured reserve (thumb). Colbie Young is a rookie with a knee injury.
- Tight ends: Tanner Hudson was promoted from the practice squad and scored a red-zone TD in Week 5. Mike Gesicki had 1 catch (a TD) on 2 targets. Watch whether Hudson is taking over Gesicki's role.
- Burrow leads the NFL in fourth-quarter and overtime turnovers since 2024 (ESPN Research via TSN).
- Offseason: traded the 10th pick for Dexter Lawrence; signed Jonathan Allen, Kyle Dugger and Bryan Cook. Dugger missed Week 5 (quad).
- Correction already made once: Week 4 team rushing was 15 carries for 23 yards. Chase Brown's 10 yards was his own total, not the team's.

## 5. Stats: what is realistic

| Source | What it gives | Access |
|---|---|---|
| nflverse (`nfl_data_py`) | Every play with EPA, sacks, run direction and gap; Next Gen Stats and Pro Football Reference advanced tables | Free, scriptable |
| NFL Next Gen Stats (via nflverse) | Time to throw, rushing yards over expected | Free |
| Pro Football Reference advanced (via nflverse) | Pressures, hurries, knockdowns, blitzes | Free |
| ESPN pass and run block win rate | Best free line measure | Free to view; no clean API |
| PFF | Lineman grades, pressures allowed per player | Paid |
| FTN (ex-Football Outsiders) | Adjusted line yards, adjusted sack rate, stuffed rate | Paid |

## 6. Design reference

Tokens and fonts are in `site/styles.css`, taken from the reference page.
- Fonts: Barlow Condensed (display), IBM Plex Sans (body), IBM Plex Mono (data).
- Colours: cool grey paper, black scoreboard, Bengal orange accent (`#E8440F` light, `#FF6B2E` dark).
- Status always shows as text plus colour, never colour alone.
- Season strip: win green, loss red, current week orange outline, bye dashed.
