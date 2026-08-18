#!/usr/bin/env python3
"""
sanjoseforce.com static site builder.

Each page's content lives in pages/<name>.body.html and starts with three
metadata comments:

    <!--title: Page Title-->
    <!--desc: Meta description-->
    <!--nav: news-->        (which top-nav item to mark current; "" for none)

Running this script wraps every body in the shared chrome (utility bar,
masthead, footer) and writes <name>.html to the site root.

    python3 build.py
"""

import datetime
import hashlib
import html as _html
import json
import pathlib
import re
import struct
from urllib.parse import quote

# Canonical origin — used for share intents, canonical tags and Open Graph.
SITE_URL = "https://sanjoseforce.com"

ROOT = pathlib.Path(__file__).parent
PAGES = ROOT / "pages"

SPONSOR_URLS = {
    "General Electric": "https://www.ge.com",
    "Franklin Mutual":  "https://www.fmiweb.com",
    "Sport Clips":      "https://www.sportclips.com",
    "Deloitte":         "https://www.deloitte.com",
}


def sponsor_tag(name):
    """Sponsor name as a link to the company's real site, if we have one on file."""
    url = SPONSOR_URLS.get(name)
    if url:
        return f'<a class="sponsor" href="{url}" target="_blank" rel="noopener sponsored">{name}</a>'
    return f'<span class="sponsor">{name}</span>'


NAV = [
    ("home",      "/",         "Home"),
    ("schedule",  "schedule",  "Schedule"),
    ("news",      "news",      "News"),
    ("team",      "team",      "Team"),
    ("stadium",   "stadium",   "Stadium"),
    ("community", "community", "Community"),
]

FOOT_COLS = [
    ("Team", [
        ("The Club", "team"), ("Roster", "team#roster"),
        ("Coaches", "team#coaches"), ("Front Office", "team#front-office"),
        ("Club History", "team#history"), ("Milestones", "team#milestones"),
        ("Club Facts", "team#club-facts"),
    ]),
    ("Game Day", [
        ("Schedule", "schedule"), ("Stadium Info", "stadium"),
        ("Parking", "stadium#parking"), ("Bag Policy", "stadium#bag-policy"),
        ("Concessions Guide", "stadium#concessions"), ("A&ndash;Z Guide", "stadium#az"),
        ("Accessibility", "stadium#accessibility"),
    ]),
    ("Tickets", [
        ("Season Tickets", "tickets#season"), ("Single Game Tickets", "tickets#single-game"),
        ("Group Tickets", "tickets#groups"), ("Premium &amp; Suites", "tickets#premium"),
        ("Account Manager", "tickets#ticketing"),
        ("Ticketing Terms", "terms#ticketing-terms"),
    ]),
    ("Fans &amp; Media", [
        ("FORCE Nation", "community#force-nation"),
        ("FORCE Foundation", "community#foundation"),
        ("News", "news"),
    ]),
]

SCRIPT = """
<script>
/* Mobile navigation drawer */
(function () {
  var mast = document.querySelector('.masthead');
  var toggle = document.querySelector('.mast-toggle');
  if (!mast || !toggle) return;
  toggle.addEventListener('click', function () {
    var open = mast.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
})();

/* Season countdown */
(function () {
  var el = document.getElementById('season-countdown');
  if (!el) return;
  var target = new Date(el.getAttribute('data-target')).getTime();
  var nums = {
    d: el.querySelector('[data-cd="d"]'),
    h: el.querySelector('[data-cd="h"]'),
    m: el.querySelector('[data-cd="m"]'),
    s: el.querySelector('[data-cd="s"]')
  };
  function pad(n) { return String(Math.max(0, n)).padStart(2, '0'); }
  function tick() {
    var diff = target - Date.now();
    if (diff <= 0) {
      nums.d.textContent = nums.h.textContent = nums.m.textContent = nums.s.textContent = '00';
      clearInterval(timer);
      return;
    }
    var s = Math.floor(diff / 1000);
    nums.d.textContent = pad(Math.floor(s / 86400));
    nums.h.textContent = pad(Math.floor((s % 86400) / 3600));
    nums.m.textContent = pad(Math.floor((s % 3600) / 60));
    nums.s.textContent = pad(s % 60);
  }
  tick();
  var timer = setInterval(tick, 1000);
})();

/* Copy-link share button */
(function () {
  var btns = document.querySelectorAll('[data-copy-url]');
  if (!btns.length) return;
  [].forEach.call(btns, function (btn) {
    btn.addEventListener('click', function () {
      var url = btn.getAttribute('data-copy-url');
      function ok() {
        btn.classList.add('is-copied');
        btn.setAttribute('aria-label', 'Link copied');
        setTimeout(function () {
          btn.classList.remove('is-copied');
          btn.setAttribute('aria-label', 'Copy link');
        }, 1600);
      }
      function fallback() {
        var ta = document.createElement('textarea');
        ta.value = url;
        ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); ok(); } catch (e) {}
        document.body.removeChild(ta);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(ok, fallback);
      } else {
        fallback();
      }
    });
  });
})();

/* Shop category filter */
(function () {
  var bar = document.getElementById('shop-filters');
  var grid = document.getElementById('shop-grid');
  var count = document.getElementById('shop-count');
  if (!bar || !grid) return;
  var items = [].slice.call(grid.querySelectorAll('.prod'));

  bar.addEventListener('click', function (e) {
    var chip = e.target.closest('.chip');
    if (!chip) return;
    var want = chip.getAttribute('data-filter');

    [].forEach.call(bar.querySelectorAll('.chip'), function (c) {
      c.setAttribute('aria-pressed', c === chip ? 'true' : 'false');
    });

    var shown = 0;
    items.forEach(function (el) {
      var match = want === 'all' || el.getAttribute('data-cat') === want;
      el.hidden = !match;
      if (match) shown++;
    });
    if (count) {
      count.textContent = 'Showing ' + shown + ' product' + (shown === 1 ? '' : 's');
    }
  });
})();

/* Preference modals (Cookie Settings, Ad Choices) */
(function () {
  var scrims = document.querySelectorAll('.modal-scrim');
  if (!scrims.length) return;
  var open = null, lastFocus = null;

  function close() {
    if (!open) return;
    open.hidden = true;
    open = null;
    document.body.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
    lastFocus = null;
  }

  function show(id) {
    var scrim = document.getElementById(id);
    if (!scrim) return;
    if (open && open !== scrim) { open.hidden = true; } else { lastFocus = document.activeElement; }
    scrim.hidden = false;
    open = scrim;
    document.body.style.overflow = 'hidden';
    var first = scrim.querySelector('.modal-close');
    if (first) first.focus();
  }

  /* Keep tabbing inside the dialog while it is open. */
  function trap(e) {
    if (!open || e.key !== 'Tab') return;
    var f = open.querySelectorAll('button, [href], input, select, textarea');
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  document.addEventListener('click', function (e) {
    var opener = e.target.closest('[data-modal]');
    if (opener) { e.preventDefault(); show(opener.getAttribute('data-modal')); return; }

    if (e.target.closest('[data-modal-close]')) { e.preventDefault(); close(); return; }

    var allowAll = e.target.closest('[data-modal-allow-all]');
    if (allowAll) {
      e.preventDefault();
      var t = allowAll.closest('.modal').querySelectorAll('.toggle:not([aria-disabled="true"])');
      for (var i = 0; i < t.length; i++) t[i].setAttribute('aria-checked', 'true');
      close();
      return;
    }

    var toggle = e.target.closest('.toggle');
    if (toggle && toggle.getAttribute('aria-disabled') !== 'true') {
      toggle.setAttribute('aria-checked', toggle.getAttribute('aria-checked') === 'true' ? 'false' : 'true');
      return;
    }

    /* Click on the backdrop itself, outside the dialog. */
    if (open && e.target === open) close();
  });

  document.addEventListener('keydown', function (e) {
    if (!open) return;
    if (e.key === 'Escape' || e.keyCode === 27) { close(); return; }
    trap(e);
  });
})();

/* Sign In cascade */
(function () {
  var trigger = null, links = document.querySelectorAll('.utility a');
  for (var i = 0; i < links.length; i++) {
    if (links[i].textContent.trim() === 'Sign In') { trigger = links[i]; break; }
  }
  if (!trigger) return;

  var CARD_W = 184, CARD_H = 238, GRAVITY = 0.45, BOUNCE = 0.82;
  /* Root-relative: article pages sit at /news/<slug>, and these paths are
     inside a script, so the build's link rewriting never sees them. */
  var CARD_SRCS = ['/assets/img/signin-card-1.jpg', '/assets/img/signin-card-2.jpg',
                  '/assets/img/signin-card-3.jpg'];
  var running = false, canvas, ctx, raf, spawnTimer;
  var sprites = null, activeSprite = null, loading = false;
  var cards = [], origin = { x: 0, y: 0 };

  /* Pre-render the sprite once: rounded corners + white border, like a card. */
  function makeSprite(image) {
    var dpr = window.devicePixelRatio || 1;
    var c = document.createElement('canvas');
    c.width = CARD_W * dpr; c.height = CARD_H * dpr;
    var g = c.getContext('2d');
    g.scale(dpr, dpr);
    var r = 13, inset = 6;
    g.beginPath();
    g.moveTo(r, 0);
    g.arcTo(CARD_W, 0, CARD_W, CARD_H, r);
    g.arcTo(CARD_W, CARD_H, 0, CARD_H, r);
    g.arcTo(0, CARD_H, 0, 0, r);
    g.arcTo(0, 0, CARD_W, 0, r);
    g.closePath();
    g.fillStyle = '#fff';
    g.fill();
    g.save();
    g.clip();
    g.drawImage(image, inset, inset, CARD_W - inset * 2, CARD_H - inset * 2);
    g.restore();
    g.lineWidth = 2.5;
    g.strokeStyle = 'rgba(0,0,0,.28)';
    g.stroke();
    return c;
  }

  function stop() {
    if (!running) return;
    running = false;
    cancelAnimationFrame(raf);
    clearInterval(spawnTimer);
    document.removeEventListener('keydown', onKey);
    window.removeEventListener('resize', stop);
    if (canvas && canvas.parentNode) canvas.parentNode.removeChild(canvas);
    canvas = null; ctx = null; cards = [];
  }

  function onKey(e) { if (e.key === 'Escape' || e.keyCode === 27) stop(); }

  /* The cards launch from the top-right corner, so anything thrown rightward is
     off screen before you can see it. Aim between straight down and 90 degrees
     to the left, with a little room to the right of straight down. */
  var AIM_LEFT = Math.PI / 2;
  var AIM_RIGHT = -Math.PI / 12;

  function spawn() {
    var aim = AIM_RIGHT + Math.random() * (AIM_LEFT - AIM_RIGHT);
    var speed = 4 + Math.random() * 8;
    cards.push({
      x: origin.x - CARD_W / 2,
      y: origin.y,
      vx: -Math.sin(aim) * speed,
      vy: Math.cos(aim) * speed
    });
    if (cards.length > 80) cards.shift();
  }

  function frame() {
    if (!running) return;
    var W = window.innerWidth, H = window.innerHeight;
    /* Oldest first, so the newest card is painted last and lands on top.
       Survivors are collected instead of spliced mid-loop, which would skip
       entries while iterating forwards. */
    var alive = [];
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      c.vy += GRAVITY;
      c.x += c.vx;
      c.y += c.vy;
      if (c.y + CARD_H >= H) {
        c.y = H - CARD_H;
        c.vy = -c.vy * BOUNCE;
        /* keep it lively so it never smears along the floor */
        if (Math.abs(c.vy) < 2) c.vy = -(4 + Math.random() * 3);
      }
      ctx.drawImage(activeSprite, c.x, c.y, CARD_W, CARD_H);
      if (c.x > -CARD_W * 2 && c.x < W + CARD_W * 2) alive.push(c);
    }
    cards = alive;
    raf = requestAnimationFrame(frame);
  }

  function start() {
    if (running || !sprites || !sprites.length) return;
    running = true;

    /* Pick one image for this run; every card in the cascade uses it. */
    activeSprite = sprites[(Math.random() * sprites.length) | 0];

    var box = trigger.getBoundingClientRect();
    origin.x = box.left + box.width / 2;
    origin.y = box.bottom + 4;

    canvas = document.createElement('canvas');
    canvas.style.cssText =
      'position:fixed;top:0;left:0;width:100%;height:100%;z-index:9999;pointer-events:none';
    var dpr = window.devicePixelRatio || 1;
    canvas.width = window.innerWidth * dpr;
    canvas.height = window.innerHeight * dpr;
    document.body.appendChild(canvas);
    ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    document.addEventListener('keydown', onKey);
    window.addEventListener('resize', stop);

    spawn();
    spawnTimer = setInterval(spawn, 264);
    frame();
  }

  /* Load every card image, then pre-render each into a sprite. */
  function loadSprites(done) {
    if (loading) return;
    loading = true;
    var pending = CARD_SRCS.length, loaded = [];
    CARD_SRCS.forEach(function (src, i) {
      var im = new Image();
      im.onload = function () { loaded[i] = im; if (!--pending) finish(); };
      im.onerror = function () { if (!--pending) finish(); };
      im.src = src;
    });
    function finish() {
      sprites = loaded.filter(Boolean).map(makeSprite);
      loading = false;
      done();
    }
  }

  trigger.addEventListener('click', function (e) {
    e.preventDefault();
    if (running) { stop(); return; }
    if (sprites) { start(); return; }
    loadSprites(start);
  });
})();
</script>
"""


def share_row(a):
    """Real share intents. These open the platform's compose window with the
    link prefilled — they need no club account on any of these services."""
    url = short_url(a)
    title = _html.unescape(a["title"])
    u, t = quote(url, safe=""), quote(title, safe="")
    subject = quote(title, safe="")
    body = quote(f"{title}\n\n{url}", safe="")
    return f"""          <div class="share">
            <span>Share</span>
            <a href="https://x.com/intent/post?url={u}&amp;text={t}"
               target="_blank" rel="noopener" aria-label="Share on X">
              <img src="assets/img/share-x.png" width="34" height="34" alt="">
            </a>
            <a href="https://www.facebook.com/sharer/sharer.php?u={u}"
               target="_blank" rel="noopener" aria-label="Share on Facebook">
              <img src="assets/img/share-facebook.png" width="34" height="34" alt="">
            </a>
            <a href="mailto:?subject={subject}&amp;body={body}" aria-label="Share by email">
              <img src="assets/img/share-email.png" width="34" height="34" alt="">
            </a>
            <button type="button" data-copy-url="{url}" aria-label="Copy link">
              <img src="assets/img/share-link.png" width="34" height="34" alt="">
            </button>
          </div>"""


def head(title, desc, path="", image="", og_type="website"):
    """Page head, including the Open Graph tags that give a shared link its
    preview card on X, Facebook, iMessage and Slack."""
    canonical = f"{SITE_URL}/{path}" if path else f"{SITE_URL}/"
    img = f"{SITE_URL}/{image or 'assets/img/og-default.png'}"
    q = lambda s: s.replace('"', "&quot;")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{q(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:site_name" content="San Jose FORCE">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{q(title)}">
<meta property="og:description" content="{q(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="theme-color" content="#0B2E3D">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800;900&amp;family=Archivo+Narrow:wght@600;700&amp;family=Barlow+Condensed:wght@600;700;800&amp;display=swap">
<link rel="stylesheet" href="assets/css/site.css">
</head>
<body>
"""


def masthead(active):
    links = "".join(
        '      <a href="{href}"{cur}>{label}</a>\n'.format(
            href=href, label=label,
            cur=' aria-current="page"' if key == active else "")
        for key, href, label in NAV
    )
    return f"""
<div class="utility">
  <div class="wrap">
    <a class="shield" href="https://fantasy.espn.com/football/league?leagueId=279774" target="_blank" rel="noopener">The Schmeague</a>
    <a href="https://fantasy.espn.com/football/league/standings?leagueId=279774" target="_blank" rel="noopener">Standings</a>
    <a href="https://fantasy.espn.com/football/league/scoreboard?leagueId=279774" target="_blank" rel="noopener">Scores</a>
    <a href="https://fantasy.espn.com/football/league/offerreport?leagueId=279774" target="_blank" rel="noopener">Transactions</a>
    <a class="spacer" href="https://www.venmo.com/u/Kevin-Malcolm" target="_blank" rel="noopener">SCHMEAGUE+</a>
    <a href="https://www.youtube.com/watch?v=x5y_mP3usTc" target="_blank" rel="noopener">Watch</a>
    <a href="#">Sign In</a>
  </div>
</div>

<header class="masthead">
  <div class="wrap">
    <a class="brand" href="/">
      <img src="assets/img/logo.png" alt="San Jose FORCE">
      <span class="wordmark"><span class="city">San Jose</span><span class="name">FORCE</span></span>
    </a>
    <nav class="mainnav">
{links}    </nav>
    <button class="mast-toggle" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>
    <div class="mast-actions">
      <a class="btn btn-ghost btn-sm" href="shop">Shop</a>
      <a class="btn btn-primary btn-sm" href="tickets">Tickets</a>
    </div>
  </div>
</header>
"""


def footer():
    cols = ""
    for title, items in FOOT_COLS:
        lis = "".join(f'<li><a href="{href}">{label}</a></li>' for label, href in items)
        cols += f'        <div><h5>{title}</h5><ul>{lis}</ul></div>\n'

    return f"""
<footer class="footer">
  <div class="foot-top">
    <div class="wrap">
      <div class="foot-brand">
        <img src="assets/img/logo.png" alt="San Jose FORCE">
        <p>San Jose FORCE<br>General Electric Field<br>1 Partnership Way<br>San Jose, California</p>
      </div>
      <div class="foot-cols">
{cols}      </div>
    </div>
  </div>

  <div class="foot-legal">
    <div class="wrap">
      <div class="links">
        <a href="privacy">Privacy Policy</a><a href="terms">Terms of Use</a><a href="accessibility">Accessibility</a>
        <a href="#" data-modal="cookie-modal">Cookie Settings</a><a href="#" data-modal="adchoices-modal">Ad Choices</a>
      </div>
      <p class="fine">
        &copy; 2025 San Jose FORCE Holdings, LLC. All rights reserved. FORCE, San Jose FORCE,
        FORCE Nation, Buster, Football. For Everyone. and the FORCE logo are registered
        trademarks of San Jose FORCE Holdings, LLC.
      </p>
    </div>
  </div>
</footer>

<div class="modal-scrim" id="cookie-modal" role="dialog" aria-modal="true" aria-labelledby="cookie-modal-title" hidden>
  <div class="modal">
    <div class="modal-head">
      <div class="eyebrow">Your Privacy Choices</div>
      <h2 id="cookie-modal-title">Cookie Preference Center</h2>
      <button class="modal-close" type="button" data-modal-close aria-label="Close">&times;</button>
    </div>
    <div class="modal-body">
      <p>When you visit sanjoseforce.com, the club and its partners may store or retrieve information
      in your browser, mostly in the form of cookies. This information does not usually identify you
      directly, but it can give you a more personalised experience of the site. Because we respect
      your right to privacy, you can choose not to allow some types of cookies. Blocking some types
      may affect your experience of the site and the services we are able to offer.</p>

      <div class="pref">
        <div class="pref-row">
          <div>
            <h3>Strictly Necessary Cookies</h3>
            <p>Required for the site to function and cannot be switched off. They are usually set only
            in response to actions you take, such as setting your privacy preferences, signing in, or
            completing a ticket or merchandise purchase.</p>
          </div>
          <div class="pref-state">
            <span class="pref-locked">Always Active</span>
          </div>
        </div>
      </div>

      <div class="pref">
        <div class="pref-row">
          <div>
            <h3>Performance Cookies</h3>
            <p>Allow us to count visits and traffic sources so we can measure and improve the
            performance of the site. They help us know which pages are the most and least popular.</p>
          </div>
          <div class="pref-state">
            <button class="toggle" type="button" role="switch" aria-checked="true" aria-label="Performance Cookies"></button>
          </div>
        </div>
      </div>

      <div class="pref">
        <div class="pref-row">
          <div>
            <h3>Functional Cookies</h3>
            <p>Enable enhanced functionality and personalisation, such as remembering your preferred
            game-day content and the region you follow the club from.</p>
          </div>
          <div class="pref-state">
            <button class="toggle" type="button" role="switch" aria-checked="true" aria-label="Functional Cookies"></button>
          </div>
        </div>
      </div>

      <div class="pref">
        <div class="pref-row">
          <div>
            <h3>Targeting Cookies</h3>
            <p>Set through our site by our advertising partners to build a profile of your interests
            and show you relevant offers on other sites. They do not store directly personal
            information, but are based on uniquely identifying your browser and device.</p>
          </div>
          <div class="pref-state">
            <button class="toggle" type="button" role="switch" aria-checked="false" aria-label="Targeting Cookies"></button>
          </div>
        </div>
      </div>

      <div class="pref">
        <div class="pref-row">
          <div>
            <h3>Social Media Cookies</h3>
            <p>Set by services we have added to the site to let you share club content with your
            network. They are capable of tracking your browser across other sites.</p>
          </div>
          <div class="pref-state">
            <button class="toggle" type="button" role="switch" aria-checked="false" aria-label="Social Media Cookies"></button>
          </div>
        </div>
      </div>

      <p style="margin-top:18px">For more information about how the club handles your data, see our
      <a href="privacy">Privacy Policy</a>.</p>
    </div>
    <div class="modal-foot">
      <button class="btn btn-ghost" type="button" data-modal-close>Reject All</button>
      <button class="btn btn-ghost" type="button" data-modal-allow-all>Allow All</button>
      <button class="btn btn-primary spacer" type="button" data-modal-close>Confirm My Choices</button>
    </div>
  </div>
</div>

<div class="modal-scrim" id="adchoices-modal" role="dialog" aria-modal="true" aria-labelledby="adchoices-modal-title" hidden>
  <div class="modal">
    <div class="modal-head">
      <div class="eyebrow">Advertising</div>
      <h2 id="adchoices-modal-title">Ad Choices</h2>
      <button class="modal-close" type="button" data-modal-close aria-label="Close">&times;</button>
    </div>
    <div class="modal-body">
      <p>The San Jose FORCE work with advertising partners to deliver interest-based advertising
      &mdash; advertising selected on the basis of your activity on this site and elsewhere online.
      Interest-based advertising helps keep club content free for FORCE Nation and helps our partners
      show you offers that are more relevant to you.</p>

      <p>The club participates in the self-regulatory programme for online behavioural advertising
      administered by the Digital Advertising Alliance. Choices you make here apply to this browser
      and this device only. If you clear your cookies, use a different browser, or use a different
      device, you will need to set your preference again.</p>

      <div class="pref">
        <div class="pref-row">
          <div>
            <h3>Interest-Based Advertising</h3>
            <p>When switched off, our partners will no longer use your browsing activity to select
            the advertising you see on this site. You will still see the same number of
            advertisements, but they may be less relevant to you.</p>
          </div>
          <div class="pref-state">
            <button class="toggle" type="button" role="switch" aria-checked="true" aria-label="Interest-Based Advertising"></button>
          </div>
        </div>
      </div>

      <p style="margin-top:18px">Opting out of interest-based advertising does not opt you out of
      club communications. To manage the email and mobile messages you receive from the FORCE, visit
      your account settings. For details on the categories of data we collect and how they are used,
      see our <a href="privacy">Privacy Policy</a> and
      <a href="#" data-modal="cookie-modal">Cookie Settings</a>.</p>
    </div>
    <div class="modal-foot">
      <button class="btn btn-ghost" type="button" data-modal-close>Cancel</button>
      <button class="btn btn-primary spacer" type="button" data-modal-close>Save Preferences</button>
    </div>
  </div>
</div>
""" + SCRIPT + """
</body>
</html>
"""


_SIZES = {}


def image_size(src):
    """(width, height) read straight from the file header. Kept dependency-free
    so the build only ever needs the standard library."""
    if src in _SIZES:
        return _SIZES[src]
    path = ROOT / src
    size = None
    try:
        data = path.read_bytes()
    except OSError:
        data = b""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        size = struct.unpack(">II", data[16:24])
    elif data[:2] == b"\xff\xd8":                      # JPEG: walk to the frame header
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker == 0xD8 or 0xD0 <= marker <= 0xD9:
                i += 2
                continue
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                size = (w, h)
                break
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    _SIZES[src] = size
    return size


def tune_images(html):
    """Stamp every <img> with its intrinsic size so nothing reflows as images
    arrive, and defer the ones below the fold. The first image after the header
    is the hero or page banner, so it loads eagerly and at high priority."""
    fold = html.find('<section class="section')
    hero_done = [False]

    def repl(m):
        tag, src = m.group(0), m.group(1)
        if "width=" in tag:
            return tag
        extra = ""
        size = image_size(src)
        if size:
            extra += f' width="{size[0]}" height="{size[1]}"'
        above = m.start() < fold or fold == -1
        if above and "logo" not in src and not hero_done[0]:
            hero_done[0] = True
            extra += ' fetchpriority="high"'
        elif not above:
            extra += ' loading="lazy" decoding="async"'
        return tag[:-1].rstrip() + extra + ">"

    return re.sub(r'<img [^>]*src="(assets/img/[^"]+)"[^>]*>', repl, html)


def meta(body, key, default=""):
    m = re.search(rf"<!--{key}:\s*(.*?)-->", body)
    return m.group(1).strip() if m else default


# ---------------------------------------------------------------- articles --

ARTICLE_DIR = PAGES / "articles"


def slugify(title, limit=62):
    """Headline reduced to a URL path, trimmed at a word boundary."""
    s = re.sub(r"&[a-z]+;", " ", _html.unescape(title).lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > limit:
        s = s[:limit].rsplit("-", 1)[0]
    return s


def article_slug(stem, title):
    """Headline slug plus a short stable suffix, the way a large CMS builds them:
    two stories that share a headline still land on different URLs. The suffix is
    derived from the source filename, so a given article keeps its URL forever."""
    return f"{slugify(title)}-{hashlib.sha1(stem.encode()).hexdigest()[:5]}"


def load_articles():
    """Read pages/articles/*.html into a list of dicts, newest first."""
    arts = []
    if not ARTICLE_DIR.is_dir():
        return arts
    for src in ARTICLE_DIR.glob("*.html"):
        raw = src.read_text(encoding="utf-8")
        iso = meta(raw, "date")
        dt = datetime.date.fromisoformat(iso) if iso else datetime.date(1970, 1, 1)
        arts.append({
            "slug": src.stem,                  # stable id; how bodies refer to it
            "file": f"news/{article_slug(src.stem, meta(raw, 'title'))}.html",
            "url": f"news/{article_slug(src.stem, meta(raw, 'title'))}",
            "title": meta(raw, "title"),
            "dek": meta(raw, "dek"),
            "date": dt,
            "long_date": dt.strftime("%B ") + str(dt.day) + dt.strftime(", %Y"),
            "short_date": dt.strftime("%b ") + str(dt.day),
            "category": meta(raw, "category", "Club News"),
            "image": meta(raw, "image", src.stem),
            "sponsor": meta(raw, "sponsor", "Franklin Mutual"),
            "tag": meta(raw, "tag", ""),
            "body": re.sub(r"<!--(title|dek|date|category|image|sponsor|tag):.*?-->\s*",
                           "", raw).strip(),
        })
    arts.sort(key=lambda a: (a["date"], a["slug"]), reverse=True)
    return arts


def tag_cls(a):
    """Category badge class — the colour modifier is optional."""
    return f'tag {a["tag"]}'.rstrip()


def card(a, show_dek=True, lead=False):
    dek = f"\n        <p>{a['dek']}</p>" if (show_dek and a["dek"]) else ""
    cls = "card card-lead" if lead else "card"
    return f"""      <a class="{cls}" href="{a['url']}">
        <div class="thumb"><img src="assets/img/{a['image']}.jpg" alt=""><span class="{tag_cls(a)}">{a['category']}</span></div>
        <h3>{a['title']}</h3>{dek}
        <div class="meta">{a['short_date']} &middot; {a['category']}</div>
      </a>"""


def headline_li(a):
    return (f'      <li><a href="{a["url"]}"><h4>{a["title"]}</h4>'
            f'<div class="meta">{a["short_date"]} &middot; {a["category"]}</div></a></li>')


def home_hero(a):
    """Homepage hero. Same story the news index leads with, so the two can never
    disagree about what the latest headline is."""
    return f"""  <div class="hero-media"><img src="assets/img/{a['image']}-hero.jpg" alt=""></div>
  <div class="wrap">
    <div class="eyebrow-row" style="margin-top:18px">
      <div class="eyebrow on-dark">{a['category']}</div>
      <div class="presented"><span>Presented by</span>{sponsor_tag(a['sponsor'])}</div>
    </div>
    <h1><a href="{a['url']}">{a['title']}</a></h1>
    <p class="dek">{a['dek']}</p>
    <div class="byline">{a['long_date']} &middot; FORCE Communications</div>
  </div>"""


def home_card(a, lead=False):
    """Homepage headline card. The lead card carries the dek and a year on the
    date; the two beneath it are compact."""
    date = a["short_date"] + f", {a['date'].year}"
    dek = f"\n          <p>{a['dek']}</p>" if lead else ""
    thumb = (f'<div class="thumb">\n            <img src="assets/img/{a["image"]}.jpg" alt="">\n'
             f'            <span class="{tag_cls(a)}">{a["category"]}</span>\n          </div>'
             if lead else
             f'<div class="thumb"><img src="assets/img/{a["image"]}.jpg" alt="">'
             f'<span class="{tag_cls(a)}">{a["category"]}</span></div>')
    return (f'        <a class="card{" card-lead" if lead else ""}" href="{a["url"]}">\n'
            f'          {thumb}\n'
            f'          <h3>{a["title"]}</h3>{dek}\n'
            f'          <div class="meta">{date} &middot; {a["category"]}</div>\n'
            f'        </a>')


def article_page(a, arts):
    others = [x for x in arts if x["slug"] != a["slug"]]
    # Sidebar "Related": same category first, then nearest in time.
    same = [x for x in others if x["category"] == a["category"]]
    rest = [x for x in others if x["category"] != a["category"]]
    rest.sort(key=lambda x: abs((x["date"] - a["date"]).days))
    related = "\n".join(headline_li(x) for x in (same + rest)[:4])
    # "More FORCE News": lead with the latest story so it is reachable from every
    # article, then fill with the nearest in time so each page surfaces different cards.
    near = sorted(others, key=lambda x: abs((x["date"] - a["date"]).days))
    latest = [x for x in others if x is others[0]]  # others keeps arts' newest-first order
    picks = latest + [x for x in near if x not in latest]
    more = "\n".join(card(x, show_dek=False) for x in picks[:4])
    return f"""
<section class="pagehead">
  <img class="bg" src="assets/img/{a['image']}-hero.jpg" alt="">
  <div class="wrap" style="padding-bottom:46px">
    <div class="eyebrow-row">
      <div class="eyebrow on-dark">{a['category']}</div>
      <div class="presented"><span>Presented by</span>{sponsor_tag(a['sponsor'])}</div>
    </div>
    <h1 style="max-width:24ch">{a['title']}</h1>
    <p style="max-width:70ch">{a['dek']}</p>
    <div class="byline" style="margin-top:24px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:rgba(255,255,255,.62)">
      {a['long_date']} &middot; FORCE Communications
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="split">
      <article>
        <div class="article-body">
{a['body']}

{share_row(a)}
        </div>
      </article>

      <aside>
        <div class="sidebar">
          <h3>Related</h3>
          <ul class="headlines">
{related}
          </ul>
        </div>

        <div class="sidebar">
          <h3>2025 Season</h3>
          <div style="border:1px solid var(--rule);border-radius:2px;padding:20px;text-align:center">
            <div class="pill pill-blue">Final</div>
            <div style="font-family:var(--hd);font-size:38px;font-weight:800;text-transform:uppercase;margin:12px 0 4px">8&ndash;6</div>
            <div style="font-size:13px;color:var(--ink-2)">Schmeague Championship Runner-Up</div>
            <div style="font-size:13px;color:var(--ink-3);margin-bottom:16px">First postseason berth in club history</div>
            <a class="btn btn-primary" href="schedule" style="width:100%">Full Results</a>
          </div>
        </div>

        <div class="sidebar">
          <h3>Media Inquiries</h3>
          <div class="notice">
            Members of the media can reach the FORCE Communications Department at
            media@sanjoseforce.com for interview requests, credentials and photography.
          </div>
        </div>
      </aside>
    </div>
  </div>
</section>

<section class="section alt">
  <div class="wrap">
    <div class="sec-head">
      <h2>More FORCE News</h2>
      <div class="presented"><span>Presented by</span>{sponsor_tag('Franklin Mutual')}</div>
      <a class="more" href="news">All News &rsaquo;</a>
    </div>
    <div class="grid g4">
{more}
    </div>
  </div>
</section>
"""


MANIFEST = ROOT / ".build-manifest.json"
BACKUPS = ROOT / ".build-backups"

_manifest = {}
_rescued = []


def absolutise(html):
    """Make internal links and asset paths root-relative.

    Article pages live at /news/<slug>, so a relative "assets/img/x.jpg" would
    resolve to /news/assets/... . The site always serves from the domain root,
    so a leading slash is both correct and simpler than counting ../ levels.
    """
    return re.sub(r'\b(href|src)="(?!https?:|mailto:|#|/)([^"]+)"', r'\1="/\2"', html)


_article_urls = {}


def resolve_article_links(html):
    """Page bodies refer to articles by their stable stem, as /news/<stem>.
    Swap in the real headline-derived URL so the bodies never have to carry it."""
    def sub(m):
        target = _article_urls.get(m.group(1))
        return f'href="/{target}{m.group(2)}"' if target else m.group(0)
    return re.sub(r'href="/news/([a-z0-9-]+)((?:#[^"]*)?)"', sub, html)


def write_page(name, html, source):
    """Write a generated page.

    The HTML in the repo root is build output. Anyone can open it and edit it —
    it is named exactly like the page it produces — so before overwriting, check
    the file against the hash of what this script last wrote there. If it differs,
    somebody edited the output by hand: keep a copy and say so loudly rather than
    destroying their work.
    """
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    html = resolve_article_links(absolutise(html))
    banner = ("<!-- GENERATED FILE - do not edit.\n"
              "     Anything you change here is overwritten on the next build.\n"
              f"     Edit {source} instead, then run: python3 build.py -->\n")
    html = html.replace("<!DOCTYPE html>\n", "<!DOCTYPE html>\n" + banner, 1)
    data = html.encode("utf-8")

    previous = _manifest.get(name)
    if previous and path.exists():
        on_disk = hashlib.sha256(path.read_bytes()).hexdigest()
        if on_disk != previous:
            BACKUPS.mkdir(exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            kept = BACKUPS / f"{name}.{stamp}.bak"
            kept.write_bytes(path.read_bytes())
            _rescued.append((name, kept.relative_to(ROOT), source))

    path.write_bytes(data)
    _manifest[name] = hashlib.sha256(data).hexdigest()


def load_manifest():
    global _manifest
    try:
        _manifest = json.loads(MANIFEST.read_text())
    except (OSError, ValueError):
        _manifest = {}


def save_manifest():
    MANIFEST.write_text(json.dumps(_manifest, indent=1, sort_keys=True) + "\n")


# --- Short links -------------------------------------------------------------
# sjf.social is a separate GitHub Pages repo holding nothing but redirect pages.
# It is generated from this article list so a new story gets a code for free.

SHORT_DIR = ROOT.parent / "sjf-social"
SHORT_HOST = "sjf.social"
_B62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

_short_codes = {}                       # stem -> code, assigned once per build


def short_code(stem, length=4):
    """Deterministic from the article's stem, so a code never changes once minted."""
    value = int(hashlib.sha1(("sjf:" + stem).encode()).hexdigest(), 16)
    out = ""
    for _ in range(length):
        out = _B62[value % 62] + out
        value //= 62
    return out


def assign_short_codes(arts):
    """Give every article a code, widening only where two would collide."""
    taken = {}
    for a in arts:
        length = 4
        code = short_code(a["slug"], length)
        while code in taken and taken[code] != a["slug"]:
            length += 1
            code = short_code(a["slug"], length)
        taken[code] = a["slug"]
        _short_codes[a["slug"]] = code
    return _short_codes


def short_url(a):
    """The sjf.social link for an article, or the canonical URL if it has no code."""
    code = _short_codes.get(a["slug"])
    return f"https://{SHORT_HOST}/{code}" if code else f"{SITE_URL}/{a['url']}"


def redirect_html(target, note):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>San Jose FORCE</title>
<link rel="canonical" href="{target}">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace({json.dumps(target)});</script>
</head>
<body><p>{note} <a href="{target}">{target}</a></p></body>
</html>
"""


def build_shortlinks(arts):
    if not SHORT_DIR.is_dir():
        return None

    codes = {_short_codes[a["slug"]]: a for a in arts}

    for code, a in codes.items():
        target = f"{SITE_URL}/{a['url']}"
        (SHORT_DIR / f"{code}.html").write_text(
            redirect_html(target, "Redirecting to"), encoding="utf-8")

    (SHORT_DIR / "index.html").write_text(
        redirect_html(SITE_URL + "/", "The official site of the San Jose FORCE:"), encoding="utf-8")
    (SHORT_DIR / "404.html").write_text(
        redirect_html(SITE_URL + "/news", "That link has expired. The latest club news:"),
        encoding="utf-8")
    (SHORT_DIR / "CNAME").write_text(SHORT_HOST + "\n", encoding="utf-8")
    (SHORT_DIR / ".nojekyll").write_text("", encoding="utf-8")
    (SHORT_DIR / "links.txt").write_text(
        "".join(f"https://{SHORT_HOST}/{c}  ->  {SITE_URL}/{a['url']}\n"
                for c, a in sorted(codes.items(), key=lambda kv: kv[1]["date"], reverse=True)),
        encoding="utf-8")
    return codes


def build():
    if not PAGES.is_dir():
        raise SystemExit(f"no pages/ directory at {PAGES}")

    load_manifest()
    arts = load_articles()
    _article_urls.update({a["slug"]: a["url"] for a in arts})
    assign_short_codes(arts)
    built = []

    # 1. Article pages
    for a in arts:
        out = (head(f"{a['title']} | San Jose FORCE", a["dek"],
                    path=a["url"], image=f"assets/img/{a['image']}-hero.jpg",
                    og_type="article")
               + masthead("news") + article_page(a, arts) + footer())
        write_page(a["file"], tune_images(out), f"pages/articles/{a['slug']}.html")
        built.append(a["file"])

    # 2. Section pages. Tokens let a page pull in the live article list.
    top = arts[0] if arts else None
    tokens = {
        "{{NEWS_TOP}}": ("" if not top else f"""    <a class="promo" href="{top['url']}" style="display:block">
      <img src="assets/img/{top['image']}-hero.jpg" alt="">
      <div class="inner">
        <div>
          <div class="eyebrow on-dark">{top['category']} &middot; {top['long_date']}</div>
          <h3>{top['title']}</h3>
          <p>{top['dek']}</p>
        </div>
        <div class="promo-cta"><span class="btn btn-white btn-lg">Read More</span></div>
      </div>
    </a>"""),
        "{{NEWS_CARDS}}": "\n".join(card(a) for a in arts[1:7]),
        "{{NEWS_ARCHIVE}}": "\n".join(headline_li(a) for a in arts[7:]),
        # Homepage. Everything below is derived from the same ordered list, so a
        # new article reorders the front page without anyone editing markup.
        "{{HOME_HERO}}": home_hero(arts[0]) if arts else "",
        "{{HOME_LEAD}}": home_card(arts[1], lead=True) if len(arts) > 1 else "",
        "{{HOME_CARDS}}": "\n".join(home_card(a) for a in arts[2:4]),
    }

    for src in sorted(PAGES.glob("*.body.html")):
        body = src.read_text(encoding="utf-8")
        name = src.name.replace(".body.html", "")
        title = meta(body, "title", "San Jose FORCE")
        desc = meta(body, "desc", "Official site of the San Jose FORCE.")
        nav = meta(body, "nav", "")
        content = re.sub(r"<!--(title|desc|nav):.*?-->\s*", "", body).strip()
        for tok, val in tokens.items():
            content = content.replace(tok, val)
        if "{{HOME_MORE}}" in content:
            # Fill the rail with the newest stories the page does not already
            # link to, so the curated sections below never appear twice.
            shown = set(re.findall(r'href="([a-z0-9-]+)"', content))
            rest = [a for a in arts if a["slug"] not in shown]
            content = content.replace("{{HOME_MORE}}",
                                      "\n".join(headline_li(a) for a in rest[:7]))
        # Use the page's own header image for the share card when it has one.
        bg = re.search(r'<img class="bg" src="(assets/img/[\w.-]+)"', content)
        url = "" if name == "index" else name
        out = (head(title, desc, path=url, image=bg.group(1) if bg else "")
               + masthead(nav) + "\n" + content + "\n" + footer())
        outfile = "news/index.html" if name == "news" else f"{name}.html"
        write_page(outfile, tune_images(out), str(src.relative_to(ROOT)))
        built.append(outfile)

    # 3. A 404 page, reusing the chrome so a wrong URL still looks like the club.
    notfound = (head("Page Not Found | San Jose FORCE",
                     "The page you are looking for is not available.", path="404.html")
                + masthead("")
                + """
<section class="pagehead">
  <div class="wrap">
    <div class="eyebrow-row"><div class="eyebrow on-dark">Error 404</div></div>
    <h1>Page Not Found</h1>
    <p>The page you are looking for has moved or is no longer available.</p>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="sec-head"><h2>Try One of These</h2></div>
    <ul class="headlines" style="max-width:640px">
      <li><a href="/"><h4>Home</h4><div class="meta">The latest from the club</div></a></li>
      <li><a href="news"><h4>News</h4><div class="meta">Official club announcements</div></a></li>
      <li><a href="schedule"><h4>Schedule</h4><div class="meta">Results and fixtures</div></a></li>
      <li><a href="tickets"><h4>Tickets</h4><div class="meta">2026 season and single game tickets</div></a></li>
      <li><a href="stadium"><h4>General Electric Field</h4><div class="meta">Plan your visit</div></a></li>
    </ul>
  </div>
</section>
"""
                + footer())
    write_page("404.html", tune_images(notfound), "build.py (the 404 block)")

    # 4. robots.txt + sitemap.xml, generated so they never fall behind the pages.
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")

    today = datetime.date.today().isoformat()
    urls = []
    for name in sorted(built):
        # the homepage is the bare origin; articles carry their publication date
        slug = name[:-11] if name.endswith("/index.html") else name[:-5]
        loc = f"{SITE_URL}/" if slug == "index" else f"{SITE_URL}/{slug}"
        art = next((a for a in arts if a["file"] == name), None)
        lastmod = art["date"].isoformat() if art else today
        priority = "1.0" if name == "index.html" else ("0.8" if art else "0.7")
        urls.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{lastmod}</lastmod>\n"
                    f"    <priority>{priority}</priority>\n  </url>")
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")

    save_manifest()

    if _rescued:
        print()
        print("!" * 72)
        print("Hand-edited output detected. Those files were NOT lost - a copy of each")
        print("is saved below. Move your changes into the source file, then rebuild.")
        for name, kept, source in _rescued:
            print(f"  {name}")
            print(f"      your version : {kept}")
            print(f"      edit instead : {source}")
        print("!" * 72)
        print()

    # 5. The articles used to live at /<slug>. Anything already shared at an old
    #    URL keeps working: a stub that redirects and points search engines at
    #    the canonical location. Static hosting has no server-side redirects.
    for a in arts:
        target = f"/{a['url']}"
        for old in (f"{a['slug']}.html", f"news/{a['slug']}.html"):
            (ROOT / old).write_text(
            f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_html.escape(a['title'])} | San Jose FORCE</title>
<link rel="canonical" href="{SITE_URL}{target}">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={target}">
</head>
<body><p>This article has moved to <a href="{target}">{target}</a>.</p></body>
</html>
""", encoding="utf-8")

    codes = build_shortlinks(arts)
    if codes is not None:
        print(f"  short links: {len(codes)} written to {SHORT_DIR.name}/")

    print(f"built {len(arts)} articles + {len(built) - len(arts)} section pages")
    print(f"  plus 404.html, robots.txt, sitemap.xml ({len(urls)} urls)")
    print("  articles:", ", ".join(a["slug"] for a in arts))


if __name__ == "__main__":
    build()
