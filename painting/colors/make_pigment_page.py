#!/usr/bin/env python3
"""Generate content/painting-pigments.html from the liquitex_basics CSVs."""

import csv
from pathlib import Path

ROOT = Path(__file__).parent
MIXED_CSV = ROOT / "liquitex_basics/colors-mixed.csv"
PURE_CSV = ROOT / "liquitex_basics/colors-pure.csv"
PIGMENTS_CSV = ROOT / "liquitex_basics/pigments.csv"
SPECS_CSV = ROOT / "liquitex_basics/liquitex-basics-specs.csv"
OUT = ROOT / "liquitex_basics/pigment-matrix.html"

GROUP_ORDER = ["yellow-orange", "red", "violet", "blue", "green", "earth", "neutral"]
FAMILY_ORDER = ["Yellow", "Orange", "Red", "Violet", "Blue", "Green", "White", "Black"]

FAMILY_COLOR = {
    "Yellow":  "#e8d44d",
    "Orange":  "#e8933a",
    "Red":     "#c94040",
    "Violet":  "#7c5c9e",
    "Blue":    "#3a6db5",
    "Green":   "#4a9e5c",
    "White":   "#cccccc",
    "Black":   "#555555",
}


def load_slugs():
    """Map color name -> image slug from the specs CSV page_url."""
    slugs = {}
    with open(SPECS_CSV) as f:
        for row in csv.DictReader(f):
            name = row["name"].removeprefix("Basics Acrylic Color ")
            slug = row["page_url"].rstrip("/").rsplit("/", 1)[-1]
            slugs[name] = slug
    return slugs


def read_pure():
    slugs = load_slugs()
    colors = []
    with open(PURE_CSV) as f:
        for row in csv.DictReader(f):
            name = row["name"]
            pig = row["pigment_code"].strip()
            colors.append({
                "name": name,
                "code": row["colour_code"],
                "group": "pure",
                "pigments": [pig],
                "slug": slugs.get(name, ""),
                "pure": True,
            })
    colors.sort(key=lambda c: c["name"])
    return colors


def read_mixed():
    slugs = load_slugs()
    colors = []
    with open(MIXED_CSV) as f:
        for row in csv.DictReader(f):
            pigments = [p.strip() for p in row["pigment_code"].split(",")]
            name = row["name"]
            colors.append({
                "name": name,
                "code": row["colour_code"],
                "group": row["group"],
                "pigments": pigments,
                "slug": slugs.get(name, ""),
                "pure": False,
            })
    colors.sort(key=lambda c: (GROUP_ORDER.index(c["group"]) if c["group"] in GROUP_ORDER else 99, c["name"]))
    return colors


def read_pigments():
    pigs = []
    with open(PIGMENTS_CSV) as f:
        for row in csv.DictReader(f):
            pigs.append({
                "code": row["pigment_code"],
                "family": row["family"],
                "pure": row["pure_color"],
            })
    pigs.sort(key=lambda p: (FAMILY_ORDER.index(p["family"]) if p["family"] in FAMILY_ORDER else 99, p["code"]))
    return pigs


def color_row(c, pigments):
    color_to_pigs = set(c["pigments"])
    img = f'<img src="images_web/{c["slug"]}.png" width="20" height="20" alt="">'
    row_cls = ' class="pure-row"' if c["pure"] else ""
    cells = f'<td class="color-name-cell">{img} {c["name"]}</td>'
    for p in pigments:
        hit = p["code"] in color_to_pigs
        col_cls = "no-pure" if not p["pure"] else ""
        cell_cls = f"cell hit {col_cls}".strip() if hit else f"cell miss {col_cls}".strip()
        cells += f'<td class="{cell_cls}">{p["code"] if hit else ""}</td>'
    return f"<tr{row_cls}>{cells}</tr>\n"


def section_header(label, ncols):
    return f'<tr class="section-header"><td colspan="{ncols + 1}" class="section-label">{label}</td></tr>\n'


def build_html(pure_colors, mixed_colors, pigments):
    ncols = len(pigments)

    # --- colgroup: one col per pigment for column styling ---
    colgroup = '<colgroup><col class="col-label"></colgroup>\n<colgroup>\n'
    for p in pigments:
        fam_cls = f"fam-{p['family'].lower()}"
        colgroup += f'  <col class="col-pig {fam_cls}">\n'
    colgroup += '</colgroup>'

    # --- family bar row: spans of th per family ---
    # count pigments per family in order
    from itertools import groupby
    family_bar = '<tr class="family-bar"><th></th>'
    for family, group in groupby(pigments, key=lambda p: p["family"]):
        count = sum(1 for _ in group)
        color = FAMILY_COLOR.get(family, "#ccc")
        family_bar += f'<th colspan="{count}" class="family-bar-cell" style="--fam-color:{color}">{family}</th>'
    family_bar += '</tr>'

    # --- header row: one th per pigment, rotated ---
    pig_headers = ""
    for p in pigments:
        cls = "" if p["pure"] else ' class="no-pure"'
        pig_headers += f'<th{cls}><div class="pig-name"><span>{p["code"]}</span></div></th>'

    # --- body: pure colors first, then mixed grouped by group ---
    rows_html = section_header("single-pigment", ncols)
    for c in pure_colors:
        rows_html += color_row(c, pigments)

    rows_html += f'<tr class="group-spacer"><td colspan="{ncols + 1}"></td></tr>\n'
    rows_html += section_header("mixed", ncols)

    prev_group = None
    for c in mixed_colors:
        if c["group"] != prev_group:
            if prev_group is not None:
                rows_html += f'<tr class="group-spacer"><td colspan="{ncols + 1}"></td></tr>\n'
            prev_group = c["group"]
        rows_html += color_row(c, pigments)

    # legend
    legend_rows = ""
    for p in pigments:
        pure_cell = p["pure"] if p["pure"] else "<em>—</em>"
        legend_rows += f"<tr><td>{p['code']}</td><td>{p['family']}</td><td>{pure_cell}</td></tr>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Liquitex Basics — Pigment Matrix</title>
<style>
  body {{
    font-family: 'Courier New', Courier, monospace;
    background: #f5f0e8;
    color: #222;
    margin: 2em auto;
    max-width: 1600px;
    font-size: 0.95em;
  }}
  h1 {{ font-size: 1.4em; letter-spacing: 0.05em; margin-bottom: 0.2em; }}
  p.sub {{ color: #666; margin-top: 0; font-size: 0.85em; }}

  /* matrix table */
  .matrix-wrap {{ overflow-x: auto; margin: 2em 0; }}
  table.matrix {{
    border-collapse: collapse;
    white-space: nowrap;
  }}
  table.matrix th, table.matrix td {{
    padding: 0;
    border: none;
  }}

  /* family bar */
  tr.family-bar th {{ padding: 0; border: none; }}
  th.family-bar-cell {{
    font-size: 0.65em;
    font-weight: normal;
    color: #fff;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    text-align: left;
    padding: 2px 0 2px 3px;
    background: var(--fam-color);
    border-right: 2px solid #f5f0e8;
  }}

  /* rotated pigment headers */
  th .pig-name {{
    height: 100px;
    display: flex;
    align-items: flex-end;
    padding-bottom: 4px;
  }}
  th .pig-name span {{
    display: block;
    transform: rotate(-60deg);
    transform-origin: bottom left;
    width: 1em;
    white-space: nowrap;
    font-size: 0.75em;
    color: #444;
    padding-left: 4px;
  }}
  th.no-pure .pig-name span {{ color: #aaa; }}

  /* color label cells */
  td.color-name-cell {{
    font-size: 0.78em;
    padding: 1px 8px 1px 2px;
    white-space: nowrap;
    vertical-align: middle;
    line-height: 1;
  }}
  td.color-name-cell img {{
    vertical-align: middle;
    margin-right: 4px;
  }}

  /* data cells */
  td.cell {{
    width: 44px;
    min-width: 44px;
    height: 15px;
    text-align: center;
    font-family: 'Courier New', Courier, monospace;
    font-size: 0.58em;
    border: 1px solid #e8e2d8;
    vertical-align: middle;
    padding: 0;
  }}
  td.cell.hit  {{ color: #333; background: #c8bda4; }}
  td.cell.miss {{ color: transparent; background: #f8f4ee; }}
  td.cell.no-pure.hit  {{ background: #bfc8b0; }}
  td.cell.no-pure.miss {{ background: #f2f5ee; }}

  tr:nth-child(even) td.cell.miss     {{ background: #ede8e0; }}
  tr:nth-child(even) td.cell.no-pure.miss {{ background: #e6e9e0; }}
  tr:nth-child(even) td.color-name-cell {{ background: #ede8e0; }}

  tr:hover td.cell {{ border-color: #bbb; }}
  tr:hover td.color-name-cell {{ font-weight: bold; }}

  /* pure color rows */
  tr.pure-row td.color-name-cell {{ font-style: italic; color: #555; }}

  /* section header rows */
  tr.section-header td.section-label {{
    font-size: 0.72em;
    color: #999;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 0 2px 2px;
  }}

  /* group spacer rows */
  tr.group-spacer td {{ height: 8px; }}

  /* legend table */
  table.legend {{
    border-collapse: collapse;
    font-size: 0.85em;
    margin-top: 2em;
  }}
  table.legend th {{
    text-align: left;
    border-bottom: 1px solid #aaa;
    padding: 2px 12px 2px 0;
    font-weight: bold;
  }}
  table.legend td {{
    padding: 2px 12px 2px 0;
    border-bottom: 1px solid #eee;
  }}

  hr {{ border: none; border-top: 1px solid #bbb; margin: 2em 0; }}
</style>
</head>
<body>

<h1>Liquitex Basics — Pigment Matrix</h1>
<p class="sub">
  Each row is a mixed color. Each column is a pigment.<br>
  &#x25CF; = pigment used. Greyed columns have no pure single-pigment tube in the Basics range.
</p>

<div class="matrix-wrap">
<table class="matrix">
  {colgroup}
  <thead>
    {family_bar}
    <tr>
      <th></th>
      {pig_headers}
    </tr>
  </thead>
  <tbody>
{rows_html}
  </tbody>
</table>
</div>

<hr>

<h2 style="font-size:1.1em;">Pigment reference</h2>
<table class="legend">
  <thead><tr><th>Code</th><th>Family</th><th>Pure tube</th></tr></thead>
  <tbody>{legend_rows}</tbody>
</table>

<hr>
<footer style="font-size:0.8em;color:#999;">Liquitex Basics range &mdash; generated from pigment data</footer>

</body>
</html>
"""
    return html


def main():
    pure_colors = read_pure()
    mixed_colors = read_mixed()
    pigments = read_pigments()
    html = build_html(pure_colors, mixed_colors, pigments)
    OUT.write_text(html)
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
