# Next step

_Last updated: Tue, Oct 13, 2026 (after step 3, round 2)_

## Where we are

Steps 1–3 are done on branch `phase-1-week5-page`. Step 3 results are in `docs/access-tests.md`.

Steps 1 and 2:
- `CLAUDE.md` holds the owner rules and every decision below.
- The Week 5 brief is rebuilt from `data/weeks/2026-w05.json` and shows on the home page.
- A GitHub Actions workflow is ready to deploy the site to GitHub Pages.

The site is **not live yet**. Two things block it (see "Blocked on the owner").

The old artifact and its two scheduled tasks are still running. Leave them on until cutover.

## Blocked on the owner

1. **The repo is private.** GitHub Pages from a private repo needs a paid GitHub plan (Pro, about US$4 a month). Pick one:
   - Make this repo public. Then research and round-ups go in a second, private repo.
   - Keep it private and pay for Pro. Then round-ups can live in this repo.
2. **Turn on Pages.** In the repo on GitHub: Settings → Pages → Source: "GitHub Actions". Then merge the branch to `main`.

## What's next

3. ~~Access tests~~ Done, two rounds. One item open: full YouTube transcripts. Episode lists and show notes work from here. Owner allows `www.youtube.com`, `youtube.com`, `www.espn.com` and `nflreadr.nflverse.com` in the environment's network settings, then Claude retests transcripts.
4. Line stats pipeline and stats page. Uses nflverse play-by-play, FTN charting, Pro Football Reference weekly pressures and Next Gen Stats. ESPN win rates read weekly by a Routine from the ESPN page. Per-play time to throw arrives after the season.
5. Media round-up routine (midweek, private, with candidate storylines).
6. Friday draft routine, then cutover: disable both old tasks the same day.

Soft goal: first brief on the new site for Week 10 vs Pittsburgh (Sun, Nov 15).

## How to check the Week 5 page (once live)

- Open it on your phone. Nothing should scroll sideways except the season strip.
- The season strip should open with Week 5 (orange outline) in view.
- Tap three source labels. Each should open the right article.
- Switch your phone to dark mode. Everything should stay readable.

## Decisions and why

| Date | Decision | Why |
|---|---|---|
| Oct 13 | A learning project: owner steers, Claude builds, owner never edits code | Success means steering the next project alone |
| Oct 13 | No hit rate, no grading, watch items are not predictions | Owner's call. Media round-up gives a reality check instead |
| Oct 13 | Watch list capped at 5 | Keeps the page near a 3-minute read |
| Oct 13 | Home page drops position room, sources list and past weeks | Too long for a phone |
| Oct 13 | Weekly writer: Claude Routines that open a session in the Claude app | No API key or extra cost. Owner picks storylines and approves by chat |
| Oct 13 | Media round-up is private, kept out of the public site | Research input, not content for friends |
| Oct 13 | Line stats as season trends. Play counts on every number; under 8 plays greyed out | Small samples mislead |
| Oct 13 | Stats pulled by GitHub Actions on Monday and Thursday | Thursday catches Monday-night games and data fixes |
| Oct 13 | Team settings in `data/team.json` | Other teams can be added later at low cost |
| Oct 13 | Week 5 port: kept 5 of 6 watch items, removed grades, kept "What happened" notes, shortened Alternative view to 1 paragraph | Matches the new rules. Item 6 (fourth-quarter margin) never came up in the game |
| Oct 13 | "Who is to blame" uses FTN's "QB fault sack" label plus weekly time to throw, not a 2.5-second rule | Per-play time to throw isn't published for 2026 |
| Oct 13 | ESPN win rates: read weekly from ESPN's leaderboard page by a Routine, not by the Actions pipeline | The page exists and updates weekly, but has no feed. Round 2 found it |
| Oct 13 | Pressure stats come from Pro Football Reference weekly data, not per-play | Per-play data is published after the season |
| Oct 13 | Podcast round-up uses YouTube (episode list and show notes), not RSS | Every podcast host is blocked here; YouTube's app service is open |
| Oct 13 | Kept the Week 5 win-chance bar, with its source shown under it | It came from the NFL data feed. Future weeks drop it unless a real source exists |
