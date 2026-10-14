# Next step

_Last updated: Wed, Oct 14, 2026 (first round-up ran; moving the Routine to a Full-network environment)_

## Where we are

Steps 1–4 are done and merged to `main`. The transcript pipeline lives in the private `bengals-research` repo (connected Oct 13). Step 3 results are in `docs/access-tests.md`.

Steps 1 and 2:
- `CLAUDE.md` holds the owner rules and every decision below.
- The Week 5 brief is rebuilt from `data/weeks/2026-w05.json` and shows on the home page.
- A GitHub Actions workflow is ready to deploy the site to GitHub Pages.

The site is live at https://petedilworth.github.io/bengals-fanzone/ (repo made public and Pages turned on by the owner, Oct 14).

The old artifact and its two scheduled tasks are still running. Leave them on until cutover.

## Owner items

1. ~~Make the repo public or go Pro~~ Done Oct 14 (public).
2. ~~Turn on Pages~~ Done Oct 14.
3. ~~Allow domains in this cloud environment~~ Done Oct 14, then superseded: owner chose to set Network access to **Full** for the round-up Routine (it must read beat-writer sites). Until that switch is made, the round-up session cannot read news sites or podcast feeds.
4. **Create a read-only token so the public site can copy the media topics file.** The round-up session cannot push to the public repo (unattended sessions are refused that permission), so it writes the file to `bengals-research/research/media/` and the public repo's stats workflow copies it. One-time setup, about 3 minutes:
   1. GitHub → your profile photo → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
   2. Name: `bengals-research read`. Expiration: 1 year. **Repository access:** Only select repositories → `bengals-research`. **Permissions → Repository permissions → Contents: Read-only.** Generate, then copy the token.
   3. Go to the `bengals-fanzone` repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Name: `RESEARCH_TOKEN`. Value: the token. Save.
   Until it exists, the workflow prints "RESEARCH_TOKEN not set; skipping media sync" and the media page stays empty.
5. **Create a new cloud environment with Network access Full** (owner's call, Oct 14: a separate environment named "Bengals research", not a change to this one). Steps: Safari → claude.ai/code → cloud icon → Cloud → Add cloud environment → name "Bengals research", Network access **Full**, leave variables and setup script empty → Create. Then tell Claude "done". Claude then moves the round-up session and its Wednesday Routine into it and retires the old ones.

## What's next

3. ~~Access tests~~ Done. Transcripts solved by the Whisper route (step 5). Allowing the domains in this environment is still worth doing: it lets Claude test pipeline changes here in minutes instead of 20-minute Actions cycles.
4. ~~Line stats pipeline and stats page~~ Built Oct 14. `pipeline/build_stats.py` pulls 13 nflverse sources for 2026 and 2025 (play-by-play, FTN, PFR pass/rush/rec/def, Next Gen passing/rushing/receiving, snap counts, injuries, depth charts, rosters), computes the three line questions with ranks and a 2025 baseline, and writes `data/stats/line.json`. `site/stats.html` shows them. Runs in about 25 s. Downloads: 35 MB cold, 0 MB when nothing changed. Workflow `stats.yml` runs Mon, Wed, Thu, Sat.
   - Freshness: PFR lagged (file last built Sun Oct 11, 7:02 am ET, before the 1 pm games) and showed "waiting" until nflverse rebuilt it on Oct 14, when a re-pull picked up Week 5. The retry design worked as intended. Expect the same lag every week: PFR lands Tuesday or Wednesday.
   - ESPN win rates are now pulled by the pipeline (`pipeline/nfl/espn.py`): all 32 teams and the 8 player tables (121 players), with ESPN's own "Through Week N" line. Six Bengals appear in the player tables; the "blame" answer lists the linemen.
   - Owner's note (Oct 14): the data must be reusable for other questions and other positions. Done by design: every source is pulled whole and cached; a new question is a new function in `pipeline/nfl/metrics.py` and a new JSON file. Nothing Bengals-specific lives in the pulls.
   - Not yet: the "one line-stat finding" slot on the home page is still hand-written in the week JSON. Could be fed from `line.json` later.
5. Media round-up routine. Built Oct 14 (owner's picks: Full network; Wed 1:17 pm ET into a standing session; sources: Bengals.com, Cincy Jungle, WCPO, Local 12, Enquirer and The Athletic headlines only, ESPN/NFL.com/The Ringer/PFF by search, plus a second podcast feed to be chosen once the network is Full).
   - In `bengals-research`: `research/ROUNDUP.md` (playbook), `research/sources.json`, `pipeline/roundup_inputs.py` (gathers transcripts + public stats into one inputs file; tested, works). First inputs file written for Week 7 at BAL.
   - A standing "Bengals round-up" session with `bengals-research` attached, woken by a Routine every Wednesday 1:17 pm ET. The owner opens that session in the Claude app and replies with the 5 storyline picks.
   - Second podcast feed: candidates found via Apple's directory (The Growler by Paul Dehner Jr., Cincy Jungle's show, The Athletic's Hear That Podcast Growlin', the team's Renee All Dey). Freshness check needs the Full network; pick after that.
   - **Media page** (owner's idea, Oct 14): `site/media.html` shows a source × topic grid per week, plus consensus and unique lists. Fed by `data/media/<season>-w<NN>.json`, which the round-up session writes (topic and source names only). Owner's picks: public page, grid view, built now. Empty until the first round-up lands.
   - Note: a Routine's prompt can only be edited from the session it posts into. The Routine says "follow ROUNDUP.md exactly", so new steps go in the playbook, not the prompt.
   - **First run, Wed Oct 14, 1:17 pm ET: worked, but transcripts only.** It wrote `research/roundups/2026-w06.md` (about 1,800 words, 7 Locked On episodes, stat ideas table, 8 ranked candidate storylines) and the public topics file `research/media/2026-w06.json` (5 sources, 15 topics), committed as `8ea1330`. All 10 written sources answered 403: the environment's network was still Custom. Fix in progress: the new Full-network environment (owner item 5). Until `RESEARCH_TOKEN` exists (owner item 4) the topics file is not copied to the public site, so the media page stays empty.
   - Why a new environment and not a switch: the owner asked what Full network risks (Oct 14). Answer given: the round-up session reads public sites and has no secrets, and the private repo token is read-only, so the exposure is low. A separate environment keeps the build sessions on the tighter Custom list.
6. Friday draft routine, then cutover: disable both old tasks the same day.

Soft goal: first brief on the new site for Week 10 vs Pittsburgh (Sun, Nov 15).

## Transcript pipeline: status of the first real runs (Oct 13)

| Run | What happened |
|---|---|
| 1 | Guessed feed address was 404. YouTube route: GitHub's servers get "Sign in to confirm you're not a bot" on every video, so that route is dead from Actions |
| 2 | Feed now resolved from Apple Podcasts ID 1159723162 (real feed is on Simplecast). 7 episodes found, MP3 downloaded with no bot check, Whisper model downloaded. Crashed on a PyAV version mismatch |
| 3 | PyAV pinned below 15, but pip picked 14.4 and tried to compile it. Failed at install |
| 4 | PyAV 14.2.0 from its prebuilt wheel. **Worked.** 7 Locked On episodes (4.8 hours of audio, about 62,000 words) in 26 minutes, committed to `research/transcripts/` |

Quality of the "base" model: readable and the substance is intact; roster names are mangled ("Smajie P Ryan" for Samaje Perine, "Jamar" for Ja'Marr). Fix pushed Oct 13: Whisper is now primed with a roster-name list from `pipeline/podcasts.json`, plus a `fixes` dictionary for known mis-hearings. The Wednesday run tests it on new episodes. Owner's call (Oct 13): keep "base" with the name fix. Revisit only if Wednesday's transcripts still mangle names.

Next scheduled run: Wed, Oct 14, 9:17 am ET. YouTube captions route stays in the workflow as best-effort and fails harmlessly from Actions.

## Step 4 recap and how to check it

What was built: a data pipeline that pulls all public nflverse data, a metrics library, and a stats page with three sections: who is to blame for sacks, does the run set up the pass, where to attack the next opponent. Every number carries its play count; under 8 plays is greyed out; every section names its sources; the top of the page says which week each source runs through.

Three findings from the first run (through Week 5):
- Burrow's sack rate is 7th best (4%), but pressure rate is 21st (24%) and his release is the 3rd fastest in the league (2.57 s). The quick throws hide the line. ESPN agrees: pass block win rate 24th.
- Play-action has been worse than no play-action: −0.05 EPA per dropback (25th) against +0.19 without it. The fake is not working yet.
- Baltimore's run defence is 6th overall, but allows 50% success at left end (8 carries, right at the floor). Weak evidence, flagged as such.

How to check on your phone (once Pages is on, or in `_site/` locally):
- Open `stats.html`. Nothing scrolls sideways except the week-by-week tables.
- The greyed rows (right tackle, 4 plays) should look faded with the count still readable.
- The freshness pills at the top: PFR should say "waiting" until its Week 5 file lands, then clear on a later run.
- Dark mode: bars, ticks and tables all readable.

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
| Oct 14 | ESPN win rates: read by the pipeline from ESPN's article page (`pipeline/nfl/espn.py`), every team and every listed player kept; last good file kept if the page changes shape | Page is reachable with a plain request. Replaces the hand-typed file and the Routine idea. Column order verified on the page itself: PRWR, RSWR, PBWR, RBWR |
| Oct 13 | Pressure stats come from Pro Football Reference weekly data, not per-play | Per-play data is published after the season |
| Oct 13 | Full transcripts required. Primary route: feed MP3 → Whisper in Actions. yt-dlp captions kept as best-effort only | Show notes are not enough (owner). YouTube blocks GitHub's servers; the podcast feed does not |
| Oct 13 | Feeds are resolved from the show's Apple Podcasts ID at run time, with a fixed address as fallback | A guessed feed address cost a run |
| Oct 13 | Whisper "base" model, primed with roster names, plus a mis-hearing fix list | 26 min per 7 episodes and free. "small" is 3x slower for a gain priming may already give |
| Oct 14 | "Who is to blame" opens with a pressure-vs-sacks line chart by week: one axis, two validated colours, dashed league lines, a gap where PFR is missing, hover tooltip | Owner liked the idea. Makes the finding land faster than the tiles |
| Oct 14 | Stats page: three questions stacked, plain HTML bars, ranks + opponent + 2025 + weekly all shown by default | Owner's picks Oct 14. Charts question unanswered, so the recommended plain-bar option was used |
| Oct 14 | Pipeline pulls every source whole and caches raw files; metrics are per-question modules | Owner wants the data reusable for other questions and all positions |
| Oct 14 | Pulls use parquet, keep ETags and send If-None-Match, never re-pull a finished season, and the Actions cache keeps `data/raw` between runs | Owner: 170 MB per run was too much. Now 35 MB cold, 0 MB when nothing changed, about 6 MB on a normal game week |
| Oct 14 | Media page is public but carries only topic names, source names and counts; summaries stay in the private repo | Overlap is useful to friends and safe to publish; the summaries are not ours to republish |
| Oct 14 | Pipeline also fills results and record into the season file from play-by-play | One less thing to type each Monday; the strip updates itself |
| Oct 13 | Stats pipeline runs Mon, Wed, Thu, Sat and retries any lagging source | PFR's file was last rebuilt before Week 5 kicked off; it must be picked up even if that takes extra runs (owner) |
| Oct 13 | Kept the Week 5 win-chance bar, with its source shown under it | It came from the NFL data feed. Future weeks drop it unless a real source exists |
| Oct 14 | Round-up weeks are named for the NFL week being written in, bye weeks included (first file is Week 6, "Bye, next at BAL") | One file per week keeps the media grid honest about when a topic was raised |
| Oct 14 | Round-up Routine runs in its own Full-network environment; build sessions stay on the Custom list | It must read beat-writer sites. Owner weighed the risk and chose a separate environment |
