#!/usr/bin/env python3
"""Pull each linked site's favicon once and store it locally.

    python3 scripts/fetch-icons.py

Fetched at build time rather than hotlinked, for three reasons. Hotlinking would
make every visitor open a connection to seven other hosts, handing each of them
the visitor's IP and user agent — including an employer's marketing site, which
has no business knowing who reads this page. A favicon service like Google's or
DuckDuckGo's is worse: it routes every visitor through one third party. And the
page currently makes zero external requests, which is worth keeping.

The cost is that an icon goes stale if a site changes its own. Rerun this then;
that is the whole maintenance story.

.ico is converted to PNG at 48px (crisp at the 18px it displays, on 2x screens).
SVG is copied through untouched, since it scales better than anything we could
rasterise from it.
"""
import io
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "icons"
SIZE = 48
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) histand.net icon fetcher"

# name -> the page whose icon we want. Kept explicit rather than scraped from
# index.html: a typo in a link should break the page visibly, not silently swap
# somebody else's logo into the list.
SITES = {
    "sqlanvil": "https://sqlanvil.com/",
    "incise": "https://incise.dev/",
    "checklists": "https://checklists.io/",
    "listanvil": "https://listanvil.com/",
    "graver": "https://graver.dev/",
    "claude-skills": "https://github.com/",
    "acuantia": "https://acuantia.com/",
}


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def declared_icon(page_url: str) -> str | None:
    """The <link rel=icon> the site itself declares, which is authoritative.

    /favicon.ico is only the fallback, and several of these sites 404 it while
    serving a perfectly good icon from somewhere else.
    """
    try:
        html = get(page_url).decode("utf-8", "ignore")
    except Exception:
        return None
    for m in re.finditer(r'<link[^>]*rel="[^"]*icon[^"]*"[^>]*>', html, re.I):
        href = re.search(r'href="([^"]+)"', m.group(0), re.I)
        if href:
            return urllib.parse.urljoin(page_url, href.group(1))
    return None


def save(name: str, page_url: str) -> str:
    candidates = [c for c in (declared_icon(page_url),
                              urllib.parse.urljoin(page_url, "/favicon.ico")) if c]
    for url in candidates:
        try:
            raw = get(url)
        except Exception:
            continue
        if not raw:
            continue
        # SVG passes through — it is already resolution independent.
        if raw.lstrip()[:5].lower().startswith(b"<svg") or url.lower().endswith(".svg"):
            (OUT / f"{name}.svg").write_bytes(raw)
            return f"{name}.svg  ({len(raw)}B, from {url.split('/')[-1][:28]})"
        try:
            im = Image.open(io.BytesIO(raw))
        except Exception:
            continue
        # An .ico holds several sizes; take the largest so downscaling is clean.
        if getattr(im, "n_frames", 1) > 1 or im.format == "ICO":
            try:
                im = Image.open(io.BytesIO(raw))
                im.size = max(im.ico.sizes())
                im = im.convert("RGBA")
            except Exception:
                im = Image.open(io.BytesIO(raw)).convert("RGBA")
        else:
            im = im.convert("RGBA")
        im = im.resize((SIZE, SIZE), Image.LANCZOS)
        im.save(OUT / f"{name}.png")
        return f"{name}.png  ({SIZE}px, from {url.split('/')[-1][:28]})"
    return f"{name}  FAILED — no usable icon"


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    failures = 0
    for name, page in SITES.items():
        line = save(name, page)
        if "FAILED" in line:
            failures += 1
        print("  " + line)
    print("done" if not failures else f"done with {failures} failure(s)")
    sys.exit(1 if failures else 0)
