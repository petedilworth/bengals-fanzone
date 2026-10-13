# Access tests (step 3)

_Run Tue, Oct 13, 2026, from a Claude Code cloud session._

| Test | Result | What it means |
|---|---|---|
| 2026 nflverse play-by-play | **Pass.** Weeks 1–5, 372 columns, last game Oct 12. Run gap filled on 21% of plays (designed runs only) | All three line questions can use it |
| Cross-check vs known numbers | **Pass.** Week 4 rushing 15 for 23, Week 5 31 for 117, Miami 217 rushing yards, 0 sacks on Burrow in Week 5 all match | Data agrees with the box scores we already had |
| 2026 FTN charting | **Pass.** Weeks 1–5, pulled Oct 13. Has pass rushers, blitzers, play action, out of pocket and **"QB fault sack"** | Protection split works. "Who is to blame" can use FTN's own charting label |
| Time to throw per play | **Fail for 2026.** The per-play file (participation) exists for 2025 but not 2026 | Use Next Gen Stats weekly averages (Burrow 2.48–2.64 sec) plus FTN's QB-fault label. No per-play lineup data, so lineup changes stay out |
| ESPN block win rates | **No 2026 table found.** ESPN posts it as an article a few times a season, with no feed | Manual and irregular. Leave it out of the pipeline |
| YouTube transcripts | **Not tested.** This environment's network policy blocks youtube.com | Retest after allowing the host. Even if allowed, YouTube may block GitHub Actions servers |
| Podcast RSS (Locked On Bengals) | **Not tested.** Blocked: feeds.megaphone.fm | Retest after allowing the host. Show notes are the fallback if transcripts fail |

## Preview: Bengals dropbacks by pass rushers, Weeks 1–5

Source: nflverse play-by-play joined to FTN charting, pulled Oct 13, 2026.

| Rushers | Plays | EPA per play | Sacks | Interceptions |
|---|---|---|---|---|
| 3 or fewer | 7 | 0.81 | 0 | 0 |
| 4 | 144 | 0.21 | 6 | 2 |
| 5 or more | 53 | −0.11 | 3 | 1 |

9 sacks allowed in total. FTN charted 2 of them as the QB's fault.
The 3-or-fewer row has under 8 plays, so it would be greyed out on the site.
