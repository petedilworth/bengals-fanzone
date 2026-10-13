# Access tests (step 3)

_Round 1 and round 2, Tue, Oct 13, 2026, from a Claude Code cloud session._

Network note: this environment lets through github.com, pypi and youtubei.googleapis.com (the service behind the YouTube app). It blocks www.youtube.com, every podcast host, every news and TV-station site, espn.com and nflreadr.nflverse.com. Web search still works, so some facts below come from search snippets, not from the page itself.

## Results

| Test | Result | What it means |
|---|---|---|
| 2026 nflverse play-by-play | **Pass.** Weeks 1–5, 372 columns, last game Oct 12 | All three line questions can use it |
| Cross-check vs known numbers | **Pass.** Week 4 rushing 15 for 23, Week 5 31 for 117, Miami 217 rushing yards, 0 sacks on Burrow in Week 5 all match | The data agrees with the box scores we had |
| 2026 FTN charting | **Pass.** Weeks 1–5, pulled Oct 13. Pass rushers, blitzers, play action, out of pocket, **"QB fault sack"** | Protection split works. "Who is to blame" can use FTN's own label |
| Time to throw per play | **Not published until after the season.** nflreadr's docs say the per-play file (which holds time to throw and pressure) comes from FTN after the post-season. 2026 lands around Feb 2027 | **Replacement found:** Pro Football Reference weekly passing in nflverse (`advstats_week_pass_2026.csv`) with per-game pressures, hurries, hits, blitzes and bad throws. Plus Next Gen Stats weekly time to throw (Burrow 2.48–2.64 s) |
| ESPN block win rates | **Found.** ESPN's 2026 leaderboard, updated Oct 13 ([ESPN](https://www.espn.com/nfl/story/_/id/49742016/2026-win-rates-team-player-rankings-pass-rush-run-stop-blocking)). Read from search snippets, since espn.com is blocked here. Column order checked against the Raiders, who led pass blocking at 63% through Week 4 ([Paganetti on X](https://x.com/RyanPaganetti/status/2107517902287200759)) and show 62% (1st) in column 3 | No feed, so a Routine reads the page weekly. A Claude Routine in the app can open espn.com |
| YouTube: find episodes | **Pass.** The YouTube app's own service answers from here. A search returns Locked On Bengals videos with ID, title, length and age | A Routine can list the week's episodes without a browser |
| YouTube: show notes | **Pass.** The video page call returns the full description. Locked On's post-game episode has 190 words of structured notes | The realistic base for the round-up |
| YouTube: full transcript | **Fail here.** The transcript call answers "Precondition check failed" for a plain client, and the player call says a login is needed. The usual fix (posing as the YouTube phone app, what yt-dlp does) was blocked by this session's safety rules, so it is untested, not disproven | Retest from a GitHub Action with yt-dlp, or after allowing www.youtube.com here |
| Podcast RSS | **Blocked here**, every host | Not needed. Locked On puts full episodes on YouTube, and the YouTube route works |

## ESPN win rates, Bengals, through Week 5

Source: ESPN 2026 win rate leaderboard, Oct 13, 2026, via search snippet.

| Metric | Bengals | Rank |
|---|---|---|
| Pass rush win rate | 48% | 23rd |
| Run stop win rate | 31% | 6th |
| Pass block win rate | 46% | 24th |
| Run block win rate | 77% | **1st** |

Non-obvious: the Bengals have the best run blocking in the league by ESPN's measure, and still ran 15 times for 23 yards in Week 4. Run stop rate ranks 6th, yet Miami ran for 217. Both say "look past the line".

## Pro Football Reference, Burrow by week (nflverse, pulled Oct 13)

| Week | Blitzed | Hurried | Hit | Pressured | Bad throws |
|---|---|---|---|---|---|
| 1 | 16 | 3 | 5 | 9 | 3 |
| 2 | 7 | 2 | 4 | 11 | 6 |
| 3 | 11 | 2 | 4 | 7 | 3 |
| 4 | 11 | 3 | 9 | 14 | 7 |

Week 5 was not in the file yet on Oct 13. Expect a lag of a few days after each game.

## Bengals dropbacks by pass rushers, Weeks 1–5

Source: nflverse play-by-play joined to FTN charting, pulled Oct 13, 2026.

| Rushers | Plays | EPA per play | Sacks | Interceptions |
|---|---|---|---|---|
| 3 or fewer | 7 | 0.81 | 0 | 0 |
| 4 | 144 | 0.21 | 6 | 2 |
| 5 or more | 53 | −0.11 | 3 | 1 |

9 sacks allowed in total. FTN charted 2 of them as the QB's fault.
The 3-or-fewer row has under 8 plays, so it would be greyed out on the site.

## Locked On Bengals episodes found (Oct 13)

| Video | Length | Age |
|---|---|---|
| Bengals Beat Dolphins, But These Mistakes Cannot Continue! | 8:43 | 1 day |
| Bengals-Dolphins POSTGAME LIVE Stream: A Win, But Work To Do! | 31:37 | 1 day |
| Bengals Bye Week ADJUSTMENTS: Opportunity for Jack Endries, Defense MUST Fix Miscues | 31:50 | new |
| The Bengals Have A MASSIVE Special Teams Problem! | 2:15 | 3 hours |
| Locked On Dolphins: The Good, The Bad, And The UGLY From Week 5 | 30:05 | 1 day |

Show-notes sample (post-game episode): "Joe Burrow posted a clean stat line with 190 yards and 4 touchdowns ... the running game showed marked improvement behind a stronger offensive line. Despite three turnovers forced by the Bengals defense ..."
