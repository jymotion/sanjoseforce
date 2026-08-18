# sanjoseforce.com

Static club site for the **San Jose FORCE**, a fantasy football team in the Schmeague.
Built to match the standard NFL club-site template — same page furniture, same module rhythm,
same relentless "presented by" placement.

## Viewing it

Open `index.html` in a browser. No build step or server is required.

For a local server (nicer URLs, avoids any `file://` quirks):

```bash
python3 -m http.server 8000 --directory /home/kevin/sync/claude/code/sanjoseforce
```

Then visit http://localhost:8000

## Pages

| File | What it is |
| --- | --- |
| `index.html` | Homepage — hero, season countdown, headlines, promo, 2025 recap, community, mission |
| 16 article pages | Every news headline is a real article — see **News articles** below |
| `news.html` | News landing — top story, latest grid and archive, all auto-generated |
| `schedule.html` | Full 2025 results, postseason, season splits, final league standings |
| `team.html` | Club overview, coaching staff / front office, club facts, history |
| `stadium.html` | General Electric Field — plan your visit, bag policy, A–Z guide |
| `community.html` | FORCE Nation, FORCE Foundation, Buster, Kids Club, FAQ |
| `tickets.html` | Ticket options, 2026 pricing table, ticketing FAQ |

## News articles

Articles live in `pages/articles/<slug>.html` and contain **only the prose**, preceded by
metadata comments:

```html
<!--title: FORCE Fall Short in Schmeague Championship-->
<!--dek: One-sentence summary used on cards and under the headline.-->
<!--date: 2025-12-29-->
<!--category: Game Recap-->
<!--image: news-championship-recap-->
<!--sponsor: Clearwater Bottling Co.-->
<!--tag: green-->
```

`build.py` wraps each one in the full article furniture — hero, byline, sidebar, related
list, "More FORCE News" grid — and writes `<slug>.html`. Adding a new file to that folder is
all it takes; **the news index updates itself**. `news.body.html` contains three tokens the
builder fills from the article list, newest first:

| Token | Fills |
| --- | --- |
| `{{NEWS_TOP}}` | Top story promo — the single newest article |
| `{{NEWS_CARDS}}` | Latest News grid — articles 2 through 7 |
| `{{NEWS_ARCHIVE}}` | News Archive list — everything older |

`image` names a pair in `assets/img/`: `<name>.jpg` (1280×720 card) and `<name>-hero.jpg`
(2000×900 page header). `tag` sets the card label colour — blank for blue, `green`, or
`lime`.

Sort order is by date descending, so dates control placement. Two articles on the same date
tie-break by slug; give them distinct dates if the order matters.

## Editing

Section page content lives in `pages/<name>.body.html`. The shared chrome (utility bar,
masthead, footer) is defined **once** in `build.py`. After editing anything, rebuild:

```bash
python3 build.py
```

That regenerates every `<name>.html` in the site root.

Each body file starts with three metadata comments the builder reads:

```html
<!--title: Page Title-->
<!--desc: Meta description-->
<!--nav: news-->
```

`nav` marks which top-nav item gets the current-page underline. Leave it empty for pages
that aren't in the nav (e.g. tickets).

## Brand

Sampled from the club's own graphics. Defined as CSS variables in
`assets/css/site.css`:

| Token | Hex | Club name |
| --- | --- | --- |
| `--force-blue` | `#0175A2` | FORCE Blue |
| `--force-cyan` | `#0298C7` | Horizon Blue |
| `--force-green` | `#78B225` | Community Green |
| `--force-lime` | `#DDE91E` | Optimism Yellow |
| `--force-navy` | `#0B2E3D` | — |

Headlines are Barlow Condensed, body is Archivo, both loaded from Google Fonts with
condensed/system fallbacks if you're offline.

## Voice

The club never breaks character. Every line is written as sincere, on-message club copy —
the blandness is for the reader to notice, not for the FORCE to admit. No line should ever
read as the club describing its own emptiness, and there is no disclaimer anywhere on the
site. Buster is "one of the most recognizable figures at General Electric Field," not "a
non-specific figure of indeterminate species."

The championship result does the same work. The club calls 2025 "a historic season" and
"the most successful in club history," which it was — while the game strip directly above
reads 80.22 to 149.88. The site never connects the two.

## What is real vs. invented

**Real, do not alter without new data:** the 2025 schedule, every score, the 8–6 record,
the postseason run, and all twelve club names and their final records. Final standings are
derived from your schedule and balance exactly at 84–84.

**Invented, safe to edit freely:** sponsors, General Electric Field details, community
programs, Buster, ticket pricing, front office titles.

**Deliberately absent:** there is no roster, no depth chart, no transactions log and no
injury reporting anywhere on the site, because inventing players would put false
information into the bit. The Team page instead carries an in-character offseason notice
that the 2026 roster will be announced after the draft. When you know your roster, that
block in `pages/team.body.html` is where it goes — `.roster-grid` and `.player` styles are
still in the stylesheet, ready to use.

**No divisions.** The Schmeague has twelve clubs and a randomized schedule. The
footer lists all twelve as a flat league. Standings are league-wide, not divisional.

## Season data

Your real 2025 season: 8–6 regular season, 3–4 at home, 5–2 on the road, 1,400.62 points
for, 1,346.52 against. Postseason 2–1 — wins over Throat Goats (147.06, the club's
single-game high) and The Philly Fakeouts, then the championship loss to Bustin Lutz OG.

The site is set at **training camp, August 2026**. The 2025 season is the most recent
completed one, recapped on the homepage and in full on `schedule.html`. Week dates map to
the real Sunday calendar: Week 1 on September 7 2025, the championship on December 28. The
GE announcement stays dated November 24 2024 and lives in the news archive, the stadium
page and its own article page. The homepage counts down to the **September 9 2026 opener,
8:20 PM ET**.

If you move the site's "now" again, the things that go stale are: the Team page roster
notice, the Tickets on-sale language, and the countdown target in `pages/index.body.html`.

## Images

All article imagery is real photography you supplied. Each article names an image pair via
its `image:` field:

- `assets/img/<name>.jpg` — 1280×720 card thumbnail
- `assets/img/<name>-hero.jpg` — 2000×900 page header

Both are cover-cropped from the source so they fill their frame without distortion. To swap
one, regenerate that pair at those dimensions and keep the filenames — no markup changes
needed.

Section pages use `banner-*.jpg` for their page headers, cropped the same way. Every
image on the site is now real photography — the abstract placeholders are gone.

`assets/img/logo.png` is your original club mark with the white background knocked out.
`assets/img/signin-card-*.jpg` are the two photos used by the Sign In easter egg.

Article metadata is the single source of truth. The homepage hero, its lead card, the two
cards beneath it and the More News rail are all generated from the article list at build
time via the `{{HOME_*}}` tokens, exactly as the news index is. Adding an article or
changing its date, photo or headline reorders the front page on the next build — there is
no homepage markup to keep in sync.

`build.py` also stamps every `<img>` with its intrinsic width and height (read from the
file header, no dependencies) and adds `loading="lazy"` to everything below the fold, so
neither is something to remember when adding markup.

## Notes

- Coaches and front office are listed by title only, since I don't know your league
  personas. Tenure lines assume continuity since 2023 — bump them when the season rolls.
- To change the nav, footer columns, or sponsor links, edit the lists near the top of
  `build.py` and rebuild. Sponsor URLs live in `SPONSOR_URLS`.
- Video and Photo Gallery sections were removed pending real footage; the CSS for them is
  kept and marked `RESERVED` in `site.css`. Same for the unused roster/player card styles.
