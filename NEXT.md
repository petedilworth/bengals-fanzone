# Next step

_Last updated: Tue, Oct 13, 2026 (after step 3, round 2)_

## Where we are

Steps 1–3 are done and merged to `main`. The transcript pipeline lives in the private `bengals-research` repo (connected Oct 13). Step 3 results are in `docs/access-tests.md`.

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
2. **Turn on Pages.** In the repo on GitHub: Settings → Pages → Source: "GitHub Actions". Until then the "Deploy site" workflow fails on every push to `main`; that is expected.
4. **Allow domains in this cloud environment** (environment menu in the session title bar → Edit → Network access): `www.youtube.com`, `youtube.com`, `feeds.megaphone.fm`, `huggingface.co`, `cdn-lfs.huggingface.co`, `www.espn.com`, `nflreadr.nflverse.com`. Then Claude can test transcripts and Whisper here before the first Actions run.

## What's next

3. ~~Access tests~~ Done. Transcripts solved by the Whisper route (step 5). Allowing the domains in this environment is still worth doing: it lets Claude test pipeline changes here in minutes instead of 20-minute Actions cycles.
4. Line stats pipeline and stats page. Uses nflverse play-by-play, FTN charting, Pro Football Reference weekly pressures and Next Gen Stats. ESPN win rates read weekly by a Routine from the ESPN page. Per-play time to throw arrives after the season.
   - **Pipeline rule (owner, Oct 13):** PFR data must be picked up even if that takes extra runs. Design: the Actions job runs Mon, Wed, Thu and Sat. Every run pulls every source and records the latest week each source covers. If any source is behind the schedule, the job marks it pending and the next run tries again. The site shows "data through Week N" per source.
5. Media round-up routine (midweek, private, with candidate storylines). **Full transcripts are required (owner, Oct 13), and the Whisper route now delivers them** (see the run table below). The pipeline lives in `bengals-research` and refuses to commit to a public repo.
6. Friday draft routine, then cutover: disable both old tasks the same day.

Soft goal: first brief on the new site for Week 10 vs Pittsburgh (Sun, Nov 15).

## Transcript pipeline: status of the first real runs (Oct 13)

| Run | What happened |
|---|---|
| 1 | Guessed feed address was 404. YouTube route: GitHub's servers get "Sign in to confirm you're not a bot" on every video, so that route is dead from Actions |
| 2 | Feed now resolved from Apple Podcasts ID 1159723162 (real feed is on Simplecast). 7 episodes found, MP3 downloaded with no bot check, Whisper model downloaded. Crashed on a PyAV version mismatch |
| 3 | PyAV pinned below 15, but pip picked 14.4 and tried to compile it. Failed at install |
| 4 | PyAV 14.2.0 from its prebuilt wheel. **Worked.** 7 Locked On episodes (4.8 hours of audio, about 62,000 words) in 26 minutes, committed to `research/transcripts/` |

Quality of the "base" model: readable and the substance is intact; roster names are mangled ("Smajie P Ryan" for Samaje Perine, "Jamar" for Ja'Marr). Fix pushed Oct 13: Whisper is now primed with a roster-name list from `pipeline/podcasts.json`, plus a `fixes` dictionary for known mis-hearings. The Wednesday run tests it on new episodes. Model size ("base" vs "small") is the owner's call.

Next scheduled run: Wed, Oct 14, 9:17 am ET. YouTube captions route stays in the workflow as best-effort and fails harmlessly from Actions.

## How to check the Week 5 page (once live)

- Open it on your phone. Nothing should scroll sideways except the season strip.
- The season strip should open with Week 5 (orange outline) in view.
- Tap three source labels. Each should open the right article.
- Switch your phone to dark mode. Everything should stay readable.

## Decisions and why

| Date | Decision | Why |
|---|---|---|
| Oct 13 | Claude merges its own work to `main`; nothing waits on the owner to merge | Owner's call, Oct 13 |
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
| Oct 13 | Full transcripts required. Primary route: feed MP3 → Whisper in Actions. yt-dlp captions kept as best-effort only | Show notes are not enough (owner). YouTube blocks GitHub's servers; the podcast feed does not |
| Oct 13 | Feeds are resolved from the show's Apple Podcasts ID at run time, with a fixed address as fallback | A guessed feed address cost a run |
| Oct 13 | Stats pipeline runs Mon, Wed, Thu, Sat and retries any lagging source | PFR's file was last rebuilt before Week 5 kicked off; it must be picked up even if that takes extra runs (owner) |
| Oct 13 | Kept the Week 5 win-chance bar, with its source shown under it | It came from the NFL data feed. Future weeks drop it unless a real source exists |
