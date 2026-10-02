#!/usr/bin/env python3
"""
Draws the survey coverage figures for the README from the CSVs in data/:

  data/survey_overview_primary.csv     -> assets/img/survey_overview.svg
  data/survey_overview_additional.csv  /
  data/medium_overview.csv             -> assets/img/medium_overview.svg

Rerun after updating the CSVs:  python3 scripts/plot_survey_overview.py
Uses only the Python standard library.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA, IMG = ROOT / 'data', ROOT / 'assets' / 'img'

FIGURES = [
    {
        'title': 'Monitoring plots',
        'unit': 'plots',
        'sections': [('Core monitoring plots', DATA / 'survey_overview_primary.csv'),
                     ('Additional plots', DATA / 'survey_overview_additional.csv')],
        'output': IMG / 'survey_overview.svg',
        'legend': True,
    },
    {
        'title': 'Medium areas',
        'unit': 'areas',
        'sections': [(None, DATA / 'medium_overview.csv')],
        'output': IMG / 'medium_overview.svg',
        'legend': False,
    },
]

SURVEYED = '✓'
# Reefscape Genomics Lab logo colors, warm (shallow) to blue (deep)
DEPTH_COLORS = {5: '#F0703A', 10: '#FFB81C', 20: '#25BD59', 40: '#00B2E5', 60: '#0078BF'}
NO_DEPTH_COLOR = '#00C2A6'
BG, INK, MUTED, EMPTY = '#000000', '#ffffff', '#8a8a8a', '#ffffff'
FONT = "'Myriad Pro', 'Source Sans 3', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

# Layout (px)
WIDTH = 880
PAD = 32
LABEL_W = 96        # site and depth labels
COUNT_W = 44        # n surveys column
ROW_H = 15
CELL_H = 11
GROUP_GAP = 8
SECTION_GAP = 30


def read_table(path):
    """Returns survey labels and a list of (site, depth_m or None, [bool per survey])."""
    with open(path, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    header = rows[0]
    survey_cols = [i for i, h in enumerate(header) if i > 0 and h.strip().lower() != 'n']
    rows_out = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        site, _, suffix = row[0].strip().partition('_')
        digits = re.sub(r'\D', '', suffix)
        depth_m = int(digits) if digits else None
        rows_out.append((site, depth_m, [row[i].strip() == SURVEYED for i in survey_cols]))
    return [header[i].strip() for i in survey_cols], rows_out


def split_label(label):
    """'Nov–Dec 2019' -> ('Nov', '2019')."""
    parts = label.split()
    year = parts[-1] if parts and parts[-1].isdigit() else ''
    month = re.split(r'[–-]', parts[0])[0] if parts else label
    return month, year


def text(x, y, s, size=11, fill=INK, anchor='start', weight='400', spacing=0):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'letter-spacing="{spacing}" text-anchor="{anchor}">{s}</text>')


def draw(fig):
    sections = [(title, *read_table(path)) for title, path in fig['sections'] if path.exists()]
    if not sections:
        return
    surveys = sections[0][1]
    n_cols = len(surveys)
    grid_x = PAD + LABEL_W
    grid_w = WIDTH - grid_x - COUNT_W - PAD
    col_w = grid_w / n_cols

    out = []
    y = PAD + 6

    # Title and summary
    n_rows = sum(len(s[2]) for s in sections)
    n_sites = len({r[0] for s in sections for r in s[2]})
    n_models = sum(sum(done) for s in sections for _, _, done in s[2])
    first_year, last_year = split_label(surveys[0])[1], split_label(surveys[-1])[1]
    out.append(text(PAD, y + 14, fig['title'], size=22, fill='#00B2E5', weight='700'))
    summary = (f'{n_rows} {fig["unit"]} · {n_sites} sites · {n_cols} surveys · '
               f'{n_models} 3D models · {first_year}–{last_year}')
    out.append(text(WIDTH - PAD, y + 14, summary, size=12, fill=MUTED, anchor='end'))
    y += 40

    # Depth legend
    if fig['legend']:
        lx = PAD
        out.append(text(lx, y + 9, 'DEPTH', size=10, fill=MUTED, weight='600', spacing=1.5))
        lx += 52
        for depth, color in DEPTH_COLORS.items():
            out.append(f'<rect x="{lx}" y="{y}" width="22" height="{CELL_H}" rx="2" fill="{color}"/>')
            out.append(text(lx + 28, y + 9, f'{depth} m', size=11, fill=MUTED))
            lx += 78
        out.append(f'<rect x="{lx + 12}" y="{y}" width="22" height="{CELL_H}" rx="2" fill="none" '
                   f'stroke="{EMPTY}" stroke-opacity=".22"/>')
        out.append(text(lx + 40, y + 9, 'not surveyed', size=11, fill=MUTED))
        y += 36

    # Column headers: year on top (once per year), month below
    prev_year = None
    for i, label in enumerate(surveys):
        month, year = split_label(label)
        if year != prev_year:
            out.append(text(grid_x + i * col_w + 2, y, year, size=11, weight='600'))
            prev_year = year
        out.append(text(grid_x + i * col_w + col_w / 2, y + 16, month, size=10, fill=MUTED, anchor='middle'))
    out.append(text(WIDTH - PAD, y + 16, 'n', size=10, fill=MUTED, anchor='end', weight='600'))
    y += 26

    for s_idx, (title, _, rows) in enumerate(sections):
        if title:
            if s_idx > 0:
                y += SECTION_GAP - GROUP_GAP
            out.append(text(PAD, y + 10, title.upper(), size=10, fill=MUTED, weight='600', spacing=1.5))
            out.append(f'<line x1="{grid_x}" x2="{WIDTH - PAD}" y1="{y + 6}" y2="{y + 6}" '
                       f'stroke="{EMPTY}" stroke-opacity=".15"/>')
            y += 20
        prev_site = None
        for site, depth, done in rows:
            if prev_site is not None and site != prev_site and depth is not None:
                y += GROUP_GAP
            if site != prev_site:
                out.append(text(PAD, y + 10, site, size=12, weight='600'))
            if depth is not None:
                out.append(text(grid_x - 10, y + 10, f'{depth} m', size=10, fill=MUTED, anchor='end'))
            color = DEPTH_COLORS.get(depth, NO_DEPTH_COLOR)
            for i, ok in enumerate(done):
                x = grid_x + i * col_w + 1.5
                w = col_w - 3
                if ok:
                    out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{CELL_H}" rx="2" fill="{color}"/>')
                else:
                    out.append(f'<rect x="{x + .5:.1f}" y="{y + .5}" width="{w - 1:.1f}" height="{CELL_H - 1}" '
                               f'rx="2" fill="none" stroke="{EMPTY}" stroke-opacity=".22"/>')
            out.append(text(WIDTH - PAD, y + 10, str(sum(done)), size=11, anchor='end'))
            prev_site = site
            y += ROW_H

    height = int(y + PAD)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" '
           f'height="{height}" role="img" aria-labelledby="t">\n'
           f'<title id="t">CoralScape 20K survey coverage, {fig["title"].lower()}: {summary}</title>\n'
           f'<rect width="{WIDTH}" height="{height}" rx="16" fill="{BG}"/>\n'
           f'<g font-family="{FONT}">\n' + '\n'.join(out) + '\n</g>\n</svg>\n')
    fig['output'].write_text(svg, encoding='utf-8')
    print(f'Wrote {fig["output"].relative_to(ROOT)}: {summary}')


if __name__ == '__main__':
    for figure in FIGURES:
        draw(figure)
