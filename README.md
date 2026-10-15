# sanjoseforce.com

Static club site for the **San Jose FORCE**, a fantasy football team in the Schmeague.
Built to match the standard NFL club-site template — same page furniture, same module rhythm,
same relentless "presented by" placement.

Live at **https://sanjoseforce.com**, published from this repo by GitHub Pages.

## Viewing it

```bash
python3 serve.py
```

Then visit http://localhost:8000

Use `serve.py`, not `python3 -m http.server`, and don't open the files directly. Every link
on the site is extensionless (`/schedule`, `/news/<slug>`), which is how GitHub Pages serves
them; only `serve.py` resolves those locally. It also serves `404.html` with a real 404.

## Pages

| URL | What it is |
| --- | --- |
| `/` | Homepage — hero, season countdown, headlines, promo, 2025 recap, community, mission |
| `/news` | News landing — top story, latest grid and archive, all auto-generated |
| `/news/<slug>` | 20 article pages — see **News articles** below |
| `/schedule` | 2026 season — fourteen games, postseason, opponent frequency |
| `/schedule/2025` | Archived 2025 results, season splits, final league standings |
| `/team` | Club overview, coaching staff / front office, club facts, history |
| `/stadium` | General Electric Field — plan your visit, bag policy, A–Z guide |
| `/community` | FORCE Nation, FORCE Foundation, Buster, FAQ |
| `/tickets` | Ticket options, 2026 pricing table, ticketing FAQ |
| `/shop` | Team Shop |
| `/accessibility`, `/privacy`, `/terms` | Legal and accessibility statements |

## News articles

Articles live in `pages/articles/<slug>.html` and contain **only the prose**, preceded by
metadata comments:

```html
<!--title: FORCE Fall Short in Schmeague Championship-->
<!--dek: One-sentence summary used on cards and under the headline.-->
<!--date: 2025-12-29-->
<!--category: Game Recap-->
<!--image: news-championship-recap-->
<!--sponsor: Franklin Mutual-->
<!--tag: green-->
<!--author: Stu Baker-->
```

`build.py` wraps each one in the full article furniture — hero, byline, sidebar, related
list, "More FORCE News" grid. Adding a new file to that folder is all it takes; **the news
index and the homepage update themselves**. `news.body.html` and `index.body.html` contain
tokens the builder fills from the article list, newest first:

| Token | Fills |
| --- | --- |
| `{{NEWS_TOP}}` | Top story promo — the single newest article |
| `{{NEWS_CARDS}}` | Latest News grid — articles 2 through 7 |
| `{{NEWS_ARCHIVE}}` | News Archive list — everything older |
| `{{HOME_HERO}}` | Homepage hero — the newest article |
| `{{HOME_LEAD}}` | Lead card beneath it |
| `{{HOME_CARDS}}` | The two compact cards |
| `{{HOME_MORE}}` | More News rail — skips anything already carded above |

`image` names a pair in `assets/img/`: `<name>.jpg` (1280×720 card) and `<name>-hero.jpg`
(2000×900 page header). `tag` sets the card label colour — blank for blue, `green`, or
`lime`. `author` is optional and defaults to `FORCE Communications`; set it for guest pieces.

Sort order is by date descending, so dates control placement. Two articles on the same date
tie-break by slug; give them distinct dates if the order matters.

Published articles live at `/news/<headline-slug>-<suffix>`. The suffix is derived from the
**filename**, not the headline, so an article keeps its URL even if you rewrite the title.
Older URL shapes keep working through generated redirect stubs.

## Editing

Section page content lives in `pages/<name>.body.html`. The shared chrome (utility bar,
masthead, footer) is defined **once** in `build.py`. After editing anything, rebuild:

```bash
python3 build.py
```

**Never edit the HTML in the repo root** — it is build output and will be overwritten. If
you do it by accident, the build notices: it saves your version into `.build-backups/` and
prints a warning rather than destroying it. Every generated file opens with a banner naming
the source you should have edited instead.

Each body file starts with three metadata comments the builder reads:

```html
<!--title: Page Title-->
<!--desc: Meta description-->
<!--nav: news-->
```

`nav` marks which top-nav item gets the current-page underline. Leave it empty for pages
that aren't in the nav (e.g. tickets).

## Publishing

```bash
python3 build.py && git add -A && git commit -m "…" && git push
```

A GitHub Actions workflow rebuilds and deploys to GitHub Pages. Allow one to five minutes.

The share buttons on every article point at **sjf.social**, a link shortener living in the
sibling `../sjf-social` repo. `build.py` generates it at the same time, so a new article
means committing and pushing **two repos**. Codes derive from the article filename and never
change.

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

The one exception is signposted: the draft grades article runs as a guest opinion piece by
Stu Baker, with a neutral disclaimer at the top and a bio at the foot. That framing is what
lets it be blunt about rival clubs without the FORCE saying it.

## What is real vs. invented

**Real, do not alter without new data:** the 2025 schedule, every score, the 8–6 record,
the postseason run, the 2026 schedule, draft results and trades, and all twelve club names.
Final standings are derived from the schedule and balance exactly at 84–84.

**Invented, safe to edit freely:** sponsors, General Electric Field details, community
programs, Buster, ticket pricing, coaching and front office names.

**Deliberately absent:** there is no roster, no depth chart and no injury reporting, because
inventing players would put false information into the bit. Individual players appear only
where you have supplied them — the Burrow trade and the draft grades. The Team page carries
an in-character notice that the 2026 roster will be published when camp closes; that block
in `pages/team.body.html` is where a real roster goes.

**No divisions.** The Schmeague has twelve clubs and a randomized schedule. Standings are
league-wide, not divisional.

## Season data

The 2025 season: 8–6 regular season, 3–4 at home, 5–2 on the road, 1,400.62 points for,
1,346.52 against. Postseason 2–1 — wins over Boutte Tuten (147.06, the club's single-game
high) and The Philly Fakeouts, then the championship loss to Bustin Lutz OG.

2025 week dates map to the real Sunday calendar: Week 1 on September 7 2025, the
championship on December 28. The GE announcement stays dated November 24 2024.

The 2026 schedule lives as data in `SEASON_2026` in `build.py` — fourteen games from Sunday
September 13, eight of them at General Electric Field. That one list feeds both the schedule
table and the "Next Game" card in the article sidebar, which picks its fixture by comparing
the build date against the schedule and so advances on its own each week.

The homepage counts down to the **September 9 2026 opener, 8:20 PM ET**. If you move the
site's "now", the things that go stale are the Team page roster notice, the Tickets on-sale
language, and that countdown target in `pages/index.body.html`.

## Images

All imagery is real photography you supplied. Each article names an image pair via its
`image:` field:

- `assets/img/<name>.jpg` — 1280×720 card thumbnail
- `assets/img/<name>-hero.jpg` — 2000×900 page header

Both are cover-cropped from the source so they fill their frame without distortion. To swap
one, regenerate that pair at those dimensions and keep the filenames — no markup changes
needed.

Section pages use `banner-*.jpg` for their page headers, cropped the same way.
`assets/img/logo.png` is your club mark with the white background knocked out, and
`assets/img/signin-card-*.jpg` are the three photos used by the Sign In easter egg.

`build.py` stamps every `<img>` with its intrinsic width and height (read from the file
header, no dependencies) and adds `loading="lazy"` to everything below the fold, so neither
is something to remember when adding markup.

## Notes

- To change the nav, footer columns, or sponsor links, edit the lists near the top of
  `build.py` and rebuild. Sponsor URLs live in `SPONSOR_URLS`.
- Video and Photo Gallery sections were removed pending real footage.
- `CLAUDE.md` holds the architectural detail — the build pipeline, URL scheme and the
  rendering traps this codebase has hit. Neither it nor this file is published.
