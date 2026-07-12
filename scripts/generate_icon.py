#!/usr/bin/env python3
"""
Generate app icons for ひらがなたからさがし.
Output: icons/icon-180.png, icons/icon-512.png

Design:
  - Background: purple gradient #667eea → #764ba2 (135deg)
  - Centered white rounded tile
  - Rainbow border (4 colors, one per side) like in-game tiles
  - Bold dark-navy「あ」character
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = 'icons'

FONT_CANDIDATES = [
    '/mnt/c/Windows/Fonts/meiryob.ttc',
    '/mnt/c/Windows/Fonts/YuGothB.ttc',
    '/mnt/c/Windows/Fonts/NotoSansJP-VF.ttf',
]

BG_START   = (102, 126, 234)  # #667eea
BG_END     = (118,  75, 162)  # #764ba2
TILE_WHITE = (255, 255, 255)
TEXT_DARK  = ( 45,  52,  54)  # #2d3436

# 4 border colors (top / right / bottom / left), from TILE_BORDER_COLORS
BORDER_COLORS = [
    (255, 107, 107),  # #FF6B6B  top
    (254, 202,  87),  # #FECA57  right
    ( 72, 219, 251),  # #48DBFB  bottom
    ( 29, 209, 161),  # #1DD1A1  left
]

CHAR = 'あ'


def load_font(size):
    # type: (int) -> ImageFont.FreeTypeFont
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    raise RuntimeError(
        'Japanese font not found.\n'
        'Install with: sudo apt-get install fonts-noto-cjk\n'
        'Candidates: ' + ', '.join(FONT_CANDIDATES)
    )


def gradient_bg(size):
    # type: (int) -> Image.Image
    img = Image.new('RGB', (size, size))
    pix = img.load()
    r1, g1, b1 = BG_START
    r2, g2, b2 = BG_END
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            pix[x, y] = (
                int(r1 + (r2 - r1) * t),
                int(g1 + (g2 - g1) * t),
                int(b1 + (b2 - b1) * t),
            )
    return img


def draw_rainbow_border(draw, x0, y0, x1, y1, radius, border_w):
    # type: (ImageDraw.ImageDraw, int, int, int, int, int, int) -> None
    """Draw 4-color border (top/right/bottom/left) on a rounded rect."""
    ct, cr, cb, cl = BORDER_COLORS

    # straight edges
    draw.rectangle([x0 + radius, y0,      x1 - radius, y0 + border_w - 1], fill=ct)  # top
    draw.rectangle([x1 - border_w + 1, y0 + radius, x1, y1 - radius],     fill=cr)  # right
    draw.rectangle([x0 + radius, y1 - border_w + 1, x1 - radius, y1],     fill=cb)  # bottom
    draw.rectangle([x0, y0 + radius, x0 + border_w - 1, y1 - radius],     fill=cl)  # left

    # corners: quadrant arcs with full bounding box of the ellipse at each corner
    arc_w = border_w
    # top-left (color: average top+left → use top)
    draw.arc([x0, y0, x0 + 2*radius, y0 + 2*radius], 180, 270, fill=ct, width=arc_w)
    # top-right (use top)
    draw.arc([x1 - 2*radius, y0, x1, y0 + 2*radius], 270, 360, fill=cr, width=arc_w)
    # bottom-right (use bottom)
    draw.arc([x1 - 2*radius, y1 - 2*radius, x1, y1], 0, 90, fill=cb, width=arc_w)
    # bottom-left (use left)
    draw.arc([x0, y1 - 2*radius, x0 + 2*radius, y1], 90, 180, fill=cl, width=arc_w)


def generate(size):
    # type: (int) -> Image.Image
    img = gradient_bg(size)
    draw = ImageDraw.Draw(img)

    # tile geometry (65% of image)
    tile_size = int(size * 0.65)
    tx0 = (size - tile_size) // 2
    ty0 = (size - tile_size) // 2
    tx1 = tx0 + tile_size
    ty1 = ty0 + tile_size
    radius = tile_size // 7       # corner radius
    border_w = max(4, tile_size // 22)  # border thickness

    # outer rounded rect (border layer)
    draw.rounded_rectangle([tx0, ty0, tx1, ty1], radius=radius, fill=TILE_WHITE)

    # draw 4-color border on top
    draw_rainbow_border(draw, tx0, ty0, tx1, ty1, radius, border_w)

    # inner white fill (shrink by border width to preserve border visibility)
    inner = border_w
    draw.rounded_rectangle(
        [tx0 + inner, ty0 + inner, tx1 - inner, ty1 - inner],
        radius=max(1, radius - inner),
        fill=TILE_WHITE,
    )

    # character — fit to ~70% of tile interior
    inner_size = tile_size - 2 * inner
    target_h = int(inner_size * 0.70)
    font = load_font(target_h)

    bb = font.getbbox(CHAR)           # (left, top, right, bottom)
    glyph_w = bb[2] - bb[0]
    glyph_h = bb[3] - bb[1]

    cx = tx0 + inner + (inner_size - glyph_w) // 2 - bb[0]
    cy = ty0 + inner + (inner_size - glyph_h) // 2 - bb[1]

    draw.text((cx, cy), CHAR, font=font, fill=TEXT_DARK)

    return img


def main():
    # type: () -> None
    os.makedirs(OUT_DIR, exist_ok=True)
    for size, name in [(180, 'icon-180.png'), (512, 'icon-512.png')]:
        img = generate(size)
        out = os.path.join(OUT_DIR, name)
        img.save(out, 'PNG')
        print(f'{size}x{size} → {out}')


if __name__ == '__main__':
    main()
