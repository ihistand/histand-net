#!/usr/bin/env python3
"""Generate the site's icons and share image.

    python3 scripts/make-assets.py

Everything here is derived from the two brand colours and the serif H already
inlined as the SVG favicon in index.html, so the raster files can be thrown away
and rebuilt rather than treated as binaries to be preserved. Rerun after changing
a colour.

Outputs, all at the repo root because that is what the platforms request:
  favicon.ico          16/32/48 — /favicon.ico is fetched whether or not linked
  apple-touch-icon.png 180 square, full bleed (iOS applies its own mask, so
                       baking in rounded corners double-rounds it)
  icon-192.png         manifest
  icon-512.png         manifest, and the maskable-ish source
  og.png               1200x630 link preview
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NAVY = (31, 58, 95)      # --accent  #1f3a5f
GOLD = (232, 176, 74)    # --accent-ink  #e8b04a
CREAM = (245, 241, 234)  # --bg light  #f5f1ea
DIM = (168, 186, 208)    # cream muted against navy

SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
SERIF_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def mark(size: int, radius_ratio: float = 0.18) -> Image.Image:
    """The H mark: navy tile, gold Georgia H, optically centred.

    Optically, not arithmetically: a capital H sits above the baseline with no
    descender, so centring its bounding box leaves it looking high. Measuring the
    glyph and centring *that* is the difference between a mark that looks placed
    and one that looks dropped in.
    """
    scale = 8  # supersample; the rounded corner is the part that shows aliasing
    img = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = int(size * scale * radius_ratio)
    if radius > 0:
        draw.rounded_rectangle([0, 0, size * scale - 1, size * scale - 1],
                               radius=radius, fill=NAVY)
    else:
        draw.rectangle([0, 0, size * scale - 1, size * scale - 1], fill=NAVY)

    f = font(SERIF_BOLD, int(size * scale * 0.62))
    left, top, right, bottom = draw.textbbox((0, 0), "H", font=f)
    draw.text(((size * scale - (right - left)) / 2 - left,
               (size * scale - (bottom - top)) / 2 - top),
              "H", font=f, fill=GOLD)
    return img.resize((size, size), Image.LANCZOS)


def write_icons() -> None:
    # .ico carries several sizes in one file; browsers pick. 48 covers Windows
    # taskbar-ish uses, 16/32 the tab.
    ico = mark(256)
    ico.save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("  favicon.ico          16/32/48")

    # Full bleed: iOS masks the corners itself.
    apple = mark(180, radius_ratio=0).convert("RGB")
    apple.save(ROOT / "apple-touch-icon.png")
    print("  apple-touch-icon.png 180 (square, iOS masks it)")

    for px in (192, 512):
        mark(px).save(ROOT / f"icon-{px}.png")
        print(f"  icon-{px}.png{' ' * (9 - len(str(px)))}manifest")


def write_og() -> None:
    """1200x630 link preview.

    Sized for how it is actually seen: a few hundred pixels wide in a timeline.
    That rules out small type and detail — the name has to carry it, with the
    tagline as support rather than a second headline.
    """
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    m = mark(132, radius_ratio=0.22)
    img.paste(m, (96, 96), m)

    draw.text((96, 300), "Ivan Histand", font=font(SERIF_BOLD, 96), fill=CREAM)
    draw.text((96, 424), "Data engineering, and tools", font=font(SERIF, 40), fill=DIM)
    draw.text((96, 480), "for the people who do it.", font=font(SERIF, 40), fill=DIM)

    draw.rectangle([96, 566, 96 + 132, 570], fill=GOLD)
    draw.text((96 + 164, 552), "histand.net", font=font(SERIF, 30), fill=GOLD)

    img.save(ROOT / "og.png")
    print(f"  og.png               {W}x{H}")


if __name__ == "__main__":
    write_icons()
    write_og()
    print("done — rerun after any brand colour change")
