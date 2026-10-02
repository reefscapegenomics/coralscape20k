#!/usr/bin/env python3
"""
Draws the README banner in a light and a dark version:

  assets/img/banner_light.svg
  assets/img/banner_dark.svg

Text is converted to outlines so the banner looks the same everywhere
(GitHub can't load web fonts inside images). The font is Source Sans 3
(SIL Open Font License), a close open match to the lab logo's Myriad;
it is downloaded once and cached in ~/.cache/coralscape20k/.

Requires fontTools:  pip install fonttools
Run:                 python3 scripts/make_banner.py
"""
import urllib.request
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / 'assets' / 'img'
FONT_URL = 'https://github.com/google/fonts/raw/main/ofl/sourcesans3/SourceSans3%5Bwght%5D.ttf'
FONT_CACHE = Path.home() / '.cache' / 'coralscape20k' / 'SourceSans3.ttf'

# Banner text
PLACE = 'CURAÇAO · SOUTHERN CARIBBEAN · SINCE 2019'
TITLE_BOLD, TITLE_LIGHT = 'CoralScape', '20K'
SUBTITLE = 'A persistent digital specimen collection of Caribbean corals'
LAB = 'REEFSCAPE GENOMICS LAB · CALIFORNIA ACADEMY OF SCIENCES'

# Reefscape Genomics Lab logo colors, top to bottom
STRIPES = ['#EB3300', '#F0703A', '#FFB81C', '#25BD59', '#00C2A6', '#00B2E5', '#009CDE', '#0078BF']
CYAN = '#00B2E5'
THEMES = {
    'light': {'gray': '#59636e', 'sub': '#1f2328'},
    'dark': {'gray': '#9198a1', 'sub': '#f0f6fc'},
}

W, H = 1280, 270
ROW_H, TOP_W, STEP = 30, 420, 52.5   # corner triangle: stripe height, top stripe width, shrink per row


def load_fonts():
    if not FONT_CACHE.exists():
        FONT_CACHE.parent.mkdir(parents=True, exist_ok=True)
        print(f'Downloading Source Sans 3 to {FONT_CACHE}')
        urllib.request.urlretrieve(FONT_URL, FONT_CACHE)
    return {w: instantiateVariableFont(TTFont(FONT_CACHE), {'wght': w}) for w in (400, 600, 700)}


def text_path(fonts, s, weight, size, x, y, tracking=0.0):
    """Returns SVG path data for a line of text and its width."""
    font = fonts[weight]
    cmap, glyphs, hmtx = font.getBestCmap(), font.getGlyphSet(), font['hmtx']
    scale = size / font['head'].unitsPerEm
    pen = SVGPathPen(glyphs)
    cx = x
    for ch in s:
        name = cmap.get(ord(ch), '.notdef')
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cx, y)))
        cx += hmtx[name][0] * scale + tracking
    return pen.getCommands(), cx - x - tracking


def main():
    fonts = load_fonts()
    title_bold, title_w = text_path(fonts, TITLE_BOLD, 700, 96, 0, 126)
    title_light, _ = text_path(fonts, TITLE_LIGHT, 400, 96, title_w + 20, 126)
    subtitle, _ = text_path(fonts, SUBTITLE, 400, 23, 3, 176)
    place, _ = text_path(fonts, PLACE, 600, 15, 3, 46, tracking=3.2)
    lab, _ = text_path(fonts, LAB, 600, 13, 3, 250, tracking=2.6)

    # Stepped triangle in the top-right corner: each stripe shorter than the one above
    corner = ''.join(
        f'<rect x="{W - (TOP_W - i * STEP)}" y="{i * ROW_H}" width="{TOP_W - i * STEP}" '
        f'height="{ROW_H}" fill="{color}"/>'
        for i, color in enumerate(STRIPES))

    for theme, c in THEMES.items():
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
               f'role="img" aria-labelledby="t">\n'
               f'<title id="t">{TITLE_BOLD} {TITLE_LIGHT}: {SUBTITLE.lower()}. Curaçao, Southern Caribbean, '
               f'since 2019. Reefscape Genomics Lab, California Academy of Sciences.</title>\n'
               f'<defs><clipPath id="corner"><rect width="{W}" height="{H}" rx="16"/></clipPath></defs>\n'
               f'<g clip-path="url(#corner)">{corner}</g>\n'
               f'<path d="{place}" fill="{c["gray"]}"/>\n'
               f'<path d="{title_bold}" fill="{CYAN}"/>\n'
               f'<path d="{title_light}" fill="{CYAN}"/>\n'
               f'<path d="{subtitle}" fill="{c["sub"]}"/>\n'
               f'<path d="{lab}" fill="{c["gray"]}"/>\n'
               f'</svg>\n')
        out = IMG / f'banner_{theme}.svg'
        out.write_text(svg, encoding='utf-8')
        print(f'Wrote {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
