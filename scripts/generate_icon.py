#!/usr/bin/env python3
"""
Generate app icons for いちにのぽん!.
Output: icons/icon-180.png, icons/icon-512.png

Design:
  - Background: warm orange gradient #FF9F43 → #EE5A24 (135deg)
  - Centered white rounded tile
  - Rainbow border (4 colors, one per side)
  - Bold digits「1」「2」stacked, in dark navy
"""

import os
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = 'icons'

FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/mnt/c/Windows/Fonts/NotoSans-Bold.ttf',
    '/mnt/c/Windows/Fonts/arialbd.ttf',
    '/mnt/c/Windows/Fonts/meiryob.ttc',
    '/mnt/c/Windows/Fonts/YuGothB.ttc',
]

BG_START   = (255, 159,  67)  # #FF9F43  warm orange
BG_END     = (238,  90,  36)  # #EE5A24  deep orange-red
TILE_WHITE = (255, 255, 255)
TEXT_DARK  = ( 45,  52,  54)  # #2d3436

BORDER_COLORS = [
    (255, 107, 107),  # #FF6B6B  top
    (254, 202,  87),  # #FECA57  right
    ( 72, 219, 251),  # #48DBFB  bottom
    ( 29, 209, 161),  # #1DD1A1  left
]

DIGITS = ['1', '2']


def load_font(size):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    raise RuntimeError(
        'Font not found.\n'
        'Install with: sudo apt-get install fonts-dejavu-core\n'
        'Candidates: ' + ', '.join(FONT_CANDIDATES)
    )


def gradient_bg(size):
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
    ct, cr, cb, cl = BORDER_COLORS

    draw.rectangle([x0 + radius, y0,               x1 - radius, y0 + border_w - 1], fill=ct)
    draw.rectangle([x1 - border_w + 1, y0 + radius, x1,         y1 - radius],       fill=cr)
    draw.rectangle([x0 + radius, y1 - border_w + 1, x1 - radius, y1],               fill=cb)
    draw.rectangle([x0, y0 + radius, x0 + border_w - 1, y1 - radius],               fill=cl)

    arc_w = border_w
    draw.arc([x0,          y0,          x0 + 2*radius, y0 + 2*radius], 180, 270, fill=ct, width=arc_w)
    draw.arc([x1 - 2*radius, y0,        x1,            y0 + 2*radius], 270, 360, fill=cr, width=arc_w)
    draw.arc([x1 - 2*radius, y1 - 2*radius, x1,        y1],             0,  90, fill=cb, width=arc_w)
    draw.arc([x0,          y1 - 2*radius, x0 + 2*radius, y1],          90, 180, fill=cl, width=arc_w)


def generate(size):
    img = gradient_bg(size)
    draw = ImageDraw.Draw(img)

    tile_size = int(size * 0.65)
    tx0 = (size - tile_size) // 2
    ty0 = (size - tile_size) // 2
    tx1 = tx0 + tile_size
    ty1 = ty0 + tile_size
    radius   = tile_size // 7
    border_w = max(4, tile_size // 22)

    draw.rounded_rectangle([tx0, ty0, tx1, ty1], radius=radius, fill=TILE_WHITE)
    draw_rainbow_border(draw, tx0, ty0, tx1, ty1, radius, border_w)

    inner = border_w
    draw.rounded_rectangle(
        [tx0 + inner, ty0 + inner, tx1 - inner, ty1 - inner],
        radius=max(1, radius - inner),
        fill=TILE_WHITE,
    )

    inner_size = tile_size - 2 * inner
    gap_ratio  = 0.06
    gap        = int(inner_size * gap_ratio)
    n          = len(DIGITS)
    slot_h     = (inner_size - gap * (n - 1)) // n

    # Choose font size: fit each digit to 85% of slot height
    target_h = int(slot_h * 0.85)
    font = load_font(target_h)

    bboxes = [font.getbbox(d) for d in DIGITS]
    glyph_hs = [bb[3] - bb[1] for bb in bboxes]
    block_h = sum(glyph_hs) + gap * (n - 1)

    cy_start = ty0 + inner + (inner_size - block_h) // 2

    y_cursor = cy_start
    for i, digit in enumerate(DIGITS):
        bb = bboxes[i]
        glyph_w = bb[2] - bb[0]
        glyph_h = glyph_hs[i]
        cx = tx0 + inner + (inner_size - glyph_w) // 2 - bb[0]
        cy = y_cursor - bb[1]
        draw.text((cx, cy), digit, font=font, fill=TEXT_DARK)
        y_cursor += glyph_h + gap

    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for size, name in [(180, 'icon-180.png'), (512, 'icon-512.png')]:
        img = generate(size)
        out = os.path.join(OUT_DIR, name)
        img.save(out, 'PNG')
        print(f'{size}x{size} → {out}')


if __name__ == '__main__':
    main()
