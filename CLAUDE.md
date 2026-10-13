# Bengals Fanzone

A personal Cincinnati Bengals fan site for the owner (Pedro, Toronto, ET) and a few friends.
It's a learning project: the owner steers and Claude builds. The owner never edits code.

Read `NEXT.md` at the start of every session. It says where we are, what's next and why past choices were made.

## Owner rules

**Writing (site content and replies)**
- Canadian spelling: offence, defence, colour, practised (verb).
- Short, active sentences in everyday language. No idioms, no jargon.
- Never use an em dash. Use an en dash with a space on each side ( – ).
- Cite sources in-line as small linked labels. Keep any direct quote under 15 words.
- Be blunt. Prefer non-obvious insights over headlines.
- Never invent numbers. If a stat has no real source or model behind it, leave it out.
- Keep pages short. Don't add sections without asking.

**Working with the owner**
- Unless the request is simple, ask 3 questions first. Use multiple-choice questions.
- Before building, lay out 2–3 options with trade-offs and let the owner pick.
- Critique the owner's request: point out what is vague or missing before starting.
- End each phase with a short plain-language recap and a "how to check this" list the owner can run on a phone.
- End each session by updating `NEXT.md`.
- The owner works from a phone. Everything must work at phone width (about 400px).
- Replies end with a short Devil's Advocate section.

## The weekly brief (home page)

Order: season strip → scoreboard → What the result means → Main storylines → Things to watch → one line-stat finding → Devil's Advocate and Alternative view.

- **Storylines:** 5, ranked by how much each could change the result, 2–3 lines each (a sourced fact, then one "why it matters" line). Across the five: at least one on defence, at least one led by the line stats, at least one the media round-up did not cover. One storyline can meet more than one rule.
- **Things to watch:** at most 5, in game order, each with why it matters. Not predictions. Not graded.
- **Devil's Advocate:** 3 bullets. **Alternative view:** 1 paragraph, usually the opponent's side.
- **Length:** the whole page is a 3-minute read, about 600–800 words.
- Not on the home page: position room, sources list, past weeks (own page), hit rate, grading.

## Stats

- Focus: offensive line, shown as season trends on the stats page.
- Every number shows its play count. Numbers from fewer than 8 plays are greyed out.
- Every chart names its source and the date the data was pulled.
- Cross-check against box scores where two sources cover the same stat (sacks, carries, rushing yards).
- Label stand-in measures as such. Example: FTN charts a sack as "QB fault"; say "FTN charted it as QB fault", not "Burrow's fault".

## Code layout

- `data/` – content as JSON. Weekly updates touch only these files.
  - `team.json` – team settings (name, colours, abbreviation). Keeps other teams possible later.
  - `season-2026.json` – schedule and results.
  - `weeks/2026-wNN.json` – one brief per week. Text fields allow `[label](url)` source links and `**bold**`.
- `site/` – static HTML, CSS and JS. No build step. Reads `data/` at run time.
- `scripts/build.sh` – copies `site/` and `data/` into `_site/` for preview and deploy.
- `.github/workflows/pages.yml` – deploys `_site/` to GitHub Pages on push to `main`.
- `docs/` – the original handover and the Week 5 reference page. History, not rules. This file wins.

Preview locally: `scripts/build.sh && python3 -m http.server -d _site 8000`.
