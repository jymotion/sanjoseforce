# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
python3 build.py        # regenerate the whole site (stdlib only, no dependencies)
python3 serve.py 8000   # local preview on the port given (default 8000)
```

There are no tests, no linter and no build toolchain. Deploying is `git push`: a GitHub
Actions workflow runs `build.py` and publishes to GitHub Pages at sanjoseforce.com.

`python -m http.server` is **not** a substitute for `serve.py`. Every link on the site is
extensionless (`/schedule`, `/news/<slug>`), and only `serve.py` resolves those the way
GitHub Pages does — it also serves `404.html` with a real 404 status.

## The one rule that matters

**The HTML in the repo root is build output. Never edit it.** Sources live in `pages/`:

| Edit this | To change |
|---|---|
| `pages/<name>.body.html` | a section page (schedule, team, tickets…) |
| `pages/articles/<slug>.html` | an article — prose only, no chrome |
| `build.py` | masthead, footer, nav, scripts, league data, any shared component |

Root files are named exactly like the pages they produce, so they are the obvious thing to
open and the wrong thing to open. `build.py` guards against this: it keeps a hash of
everything it wrote in `.build-manifest.json`, and if a file no longer matches, it copies
your version into `.build-backups/` and prints a loud warning instead of silently
overwriting. Every generated file also opens with a banner naming its source.

The same manifest drives stale-output pruning — a page that is renamed or deleted has its
old output removed, because a leftover file beats a directory index when the host resolves
a URL.

## Architecture

`build.py` is the whole system (~1300 lines, standard library only). It wraps each body
file in shared chrome and writes HTML to the repo root.

**Articles** carry metadata as HTML comments at the top of the file:
`title`, `dek`, `date`, `category`, `image`, `sponsor`, `tag`, `author` (optional, defaults
to `FORCE Communications`). Everything else — headline, byline, hero, share row, related
list — is generated from those.

`image` is optional. Omit it and the post uses `news-default` (a real club photo), so
writing an article never depends on having a photo to hand — add the field later to swap in
a specific one. Naming an image that is not in `assets/img/` **fails the build** rather than
publishing a broken hero.

Article URLs are `/news/<headline-slug>-<suffix>`. The suffix is five hex characters
derived from the **source filename**, not from content or randomness, so an article keeps
its URL forever even if the headline changes. Each article also gets redirect stubs at its
two previous URL shapes (`/<stem>` and `/news/<stem>`); static hosting has no server-side
redirects.

**Tokens** let a body file pull in the live article list, so index pages regenerate
themselves instead of being hand-maintained:

- `{{HOME_HERO}}`, `{{HOME_LEAD}}`, `{{HOME_CARDS}}`, `{{HOME_MORE}}` — homepage
- `{{NEWS_TOP}}`, `{{NEWS_CARDS}}`, `{{NEWS_ARCHIVE}}` — news index
- `{{SCHEDULE_ROWS}}` — regular season table, from `SEASON_2026`

Publishing an article reorders the front page automatically. `{{HOME_MORE}}` excludes the
four stories the page already gives a card to plus anything hand-linked further down, so
nothing appears twice. Bodies may reference an article by its stable stem
(`href="news/<stem>"`) and the builder resolves it to the real URL — never hardcode the
suffix in a body file.

**`SEASON_2026`** in `build.py` is the single source for both the schedule table and the
"Next Game" card in the article sidebar. The card picks the fixture by comparing the build
date against the schedule, so it advances on its own each week.

**Short links.** Every article's share buttons point at sjf.social, a shortener living in
its own repo (`jymotion/sjf-social`) because GitHub Pages allows one custom domain per repo.
`build.py` generates it into `../sjf-social` when that sibling exists, so locally a new
article means committing and pushing **two repos**. Codes derive from the article filename
and never change.

When the sibling is absent — a cloud session, a fresh clone — the build prints a loud
warning and skips it. That matters because `short_url()` still writes sjf.social links into
the share buttons either way, so skipping silently would ship dead links.

You do not have to fix that by hand. `sjf-social` carries a `refresh.yml` workflow that
clones this repo, runs `build.py` with `SJF_SHORT_DIR` pointed at itself, and commits any
new redirect pages. It runs every 15 minutes and on manual dispatch, needs no secrets, and
means **pushing only this repo is enough** — the short link appears within the cron window.

### Post-processing in `write_page()`

Every page passes through, in order: `tune_images()` (stamps intrinsic width/height read
from the file headers, adds `loading="lazy"` below the fold), `absolutise()` (rewrites
internal `href`/`src` to root-relative), then `resolve_article_links()`.

Paths are root-relative because articles live one directory deep at `/news/<slug>` — a
relative `assets/…` would resolve against `/news/`. **`absolutise()` only rewrites `href`
and `src` attributes.** Asset paths inside the `SCRIPT` block must be written
root-relative by hand; this has broken the Sign In easter egg once already.

## Voice and content rules

**The club never breaks character.** Every line is sincere, on-message club copy. The joke
is that the FORCE are the blandest, most focus-grouped franchise imaginable, and the club
never acknowledges it. Juxtaposition carries it — the site calls 2025 "a historic season"
while the scoreline beside it reads 80.22–149.88, and never connects the two. No winking,
no self-deprecation, no disclaimer anywhere.

**Never invent anything inside the fantasy league** — players, rosters, draft results,
scores, standings, team names. The user supplies all of it. Inventing *outside* the league
is expected and encouraged: sponsors, stadium details, community programs, front office
names, ticket pricing, Buster the mascot.

**Never generate illustrated or procedural artwork to fill a photo slot.** It reads as
clip-art in a layout built for photography. Ask what the user wants instead; a correctly
named and sized placeholder is fine, invented artwork shipped as finished is not.

## Verification habits

Check rendered output rather than assuming — this codebase has produced several bugs that
only appear in a browser:

- **No page should scroll sideways** at 1280, 860 or 375px. Grid items default to
  `min-width:auto` and will not shrink below their content, so a wide table or a long team
  name pushes the whole page over instead of scrolling in place. Fixed with `min-width:0`
  on `.split` and `.recap-block` children, and `minmax(0,1fr)` on `.stats`.
- `requestAnimationFrame` and programmatic scrolling do not run in the preview pane, so
  animation and anchor-scroll behaviour cannot be observed there — verify the mechanism
  (ids, computed `scroll-margin-top`) or simulate the physics instead.
- Pillow here has **no AVIF codec** and no converter is installed. AVIF sources have to be
  decoded through the browser; JPEG or PNG is far less work.

## Deploying

`git push` triggers `.github/workflows/deploy.yml`, which builds and publishes. The staging
step copies the tree and **excludes** sources rather than listing what to include — listing
inclusions silently dropped a whole new directory once. Anything that should not be public
needs an exclude line there.

Deploys take one to five minutes. The live site is the check that matters.
