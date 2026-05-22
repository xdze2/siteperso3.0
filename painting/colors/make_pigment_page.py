#!/usr/bin/env python3
"""Generate content/painting-pigments.html from the liquitex_basics CSVs."""

import csv
from pathlib import Path

ROOT = Path(__file__).parent
MIXED_CSV = ROOT / "liquitex_basics/colors-mixed.csv"
PIGMENTS_CSV = ROOT / "liquitex_basics/pigments.csv"
OUT = ROOT / "liquitex_basics/pigment-matrix.html"

GROUP_ORDER = ["yellow-orange", "red", "violet", "blue", "green", "earth", "neutral"]
FAMILY_ORDER = ["Yellow", "Orange", "Red", "Violet", "Blue", "Green", "White", "Black"]


def read_mixed():
    colors = []
    with open(MIXED_CSV) as f:
        for row in csv.DictReader(f):
            pigments = [p.strip() for p in row["pigment_code"].split(",")]
            colors.append({
                "name": row["name"],
                "code": row["colour_code"],
                "group": row["group"],
                "pigments": pigments,
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


def build_html(colors, pigments):
    # color name -> set of pigment codes
    color_to_pigs = {c["name"]: set(c["pigments"]) for c in colors}

    # --- header row: one th per pigment, rotated, grouped by family ---
    pig_headers = ""
    prev_family = None
    for p in pigments:
        if p["family"] != prev_family:
            pig_headers += f'<th class="family-sep" title="{p["family"]}"></th>'
            prev_family = p["family"]
        pure_label = f'<span class="pure-tag" title="{p["pure"]}">&bull;</span>' if p["pure"] else ""
        pig_headers += f'<th class="pig-name"><span>{p["code"]}{pure_label}</span></th>'

    # --- body rows: one per color, grouped by group ---
    rows_html = ""
    prev_group = None
    for c in colors:
        if c["group"] != prev_group:
            cols = len(pigments) + len(set(p["family"] for p in pigments)) + 2
            rows_html += f'<tr class="group-spacer"><td colspan="{cols}"></td></tr>'
            prev_group = c["group"]

        cells = f'<td class="color-name-cell">{c["name"]}</td><td class="color-group">{c["group"]}</td>'

        prev_family = None
        for p in pigments:
            if p["family"] != prev_family:
                cells += '<td class="family-sep-cell"></td>'
                prev_family = p["family"]
            hit = p["code"] in color_to_pigs[c["name"]]
            cells += f'<td class="cell {"hit" if hit else "miss"}">{"&#x25CF;" if hit else ""}</td>'

        rows_html += f"<tr>{cells}</tr>\n"

    # legend
    legend_rows = ""
    for p in pigments:
        pure_cell = p["pure"] if p["pure"] else "<em>—</em>"
        legend_rows += f"<tr><td>{p['code']}</td><td>{p['family']}</td><td>{pure_cell}</td></tr>\n"

    family_legend = "  ".join(
        f'<span class="gl-group">{f}</span>' for f in FAMILY_ORDER
    )

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
    max-width: 1200px;
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

  /* rotated pigment headers */
  th.pig-name {{
    height: 100px;
    vertical-align: bottom;
    padding-bottom: 4px;
  }}
  th.pig-name span {{
    display: block;
    transform: rotate(-60deg);
    transform-origin: bottom left;
    width: 1em;
    white-space: nowrap;
    font-size: 0.75em;
    color: #444;
    padding-left: 4px;
  }}

  /* family separator columns */
  th.family-sep, td.family-sep-cell {{
    width: 8px;
    min-width: 8px;
    background: #e0d8cc;
  }}

  /* color label cells */
  td.color-name-cell {{
    font-size: 0.82em;
    padding-right: 6px;
    padding-left: 2px;
    white-space: nowrap;
    min-width: 180px;
  }}
  td.color-group {{
    font-size: 0.72em;
    color: #999;
    padding-right: 10px;
    white-space: nowrap;
    min-width: 80px;
  }}

  /* data cells */
  td.cell {{
    width: 18px;
    min-width: 18px;
    height: 18px;
    text-align: center;
    font-size: 0.7em;
    border: 1px solid #ddd;
  }}
  td.cell.hit {{ color: #222; background: #d4c9b0; }}
  td.cell.miss {{ color: transparent; background: #f8f4ee; }}

  tr:hover td.cell {{ border-color: #aaa; }}
  tr:hover td.color-name-cell {{ font-weight: bold; }}

  /* group spacer rows */
  tr.group-spacer td {{ height: 8px; background: transparent; }}

  /* pure-color bullet */
  .pure-tag {{
    color: #aaa;
    font-size: 0.9em;
    margin-left: 1px;
    cursor: default;
  }}

  /* family legend */
  .group-legend {{ margin: 1em 0; font-size: 0.8em; color: #555; }}
  .gl-group {{
    display: inline-block;
    margin-right: 1em;
    padding: 1px 6px;
    background: #e0d8cc;
    border-radius: 2px;
  }}

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
  Each row is a mixed color. Each column is a pigment, grouped by family.<br>
  &#x25CF; = pigment used in that color. &bull; after the code = a pure single-pigment tube exists.
</p>

<div class="group-legend">Pigment families: {family_legend}</div>

<div class="matrix-wrap">
<table class="matrix">
  <thead>
    <tr>
      <th colspan="2"></th>
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
    colors = read_mixed()
    pigments = read_pigments()
    html = build_html(colors, pigments)
    OUT.write_text(html)
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
