#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TSV = SCRIPT_DIR / "liquitex-basics-colors.txt"
PAGES_DIR = SCRIPT_DIR / "liquitex_basics" / "pages"
OUT_CSV = SCRIPT_DIR / "liquitex_basics" / "liquitex-basics-specs.csv"
BASE_URL = "https://www.liquitex.com"


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def extract_spec(html, label):
    """Extract td text following a th that contains label."""
    # Match <th ...>...label...</th><td ...>...value...</td>
    pattern = (
        r"<th[^>]*>.*?" + re.escape(label) + r".*?</th>\s*<td[^>]*>(.*?)</td>"
    )
    m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    if m:
        return strip_tags(m.group(1))
    return ""


def extract_sku(html):
    m = re.search(r'class="[^"]*product-sku[^"]*"[^>]*>(.*?)</td>', html, re.DOTALL)
    if m:
        return strip_tags(m.group(1))
    return ""


# Load TSV: name, page_path, img_url
entries = []
with open(TSV) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) == 3:
            entries.append(parts)

fields = ["name", "page_url", "image_url", "sku", "colour_code",
          "lightfastness", "opacity", "series", "pigment_code"]

rows = []
missing = []

for name, page_path, img_url in entries:
    slug = page_path.split("/")[-1]
    html_file = PAGES_DIR / f"{slug}.html"

    if not html_file.exists():
        print(f"MISSING page: {slug}", file=sys.stderr)
        missing.append(slug)
        row = {f: "" for f in fields}
        row["name"] = name
        row["page_url"] = BASE_URL + page_path
        row["image_url"] = img_url
        rows.append(row)
        continue

    html = html_file.read_text(encoding="utf-8", errors="replace")

    row = {
        "name": name,
        "page_url": BASE_URL + page_path,
        "image_url": img_url,
        "sku": extract_sku(html),
        "colour_code": extract_spec(html, "Colour Code:"),
        "lightfastness": extract_spec(html, "Lightfastness:"),
        "opacity": extract_spec(html, "Opacity:"),
        "series": extract_spec(html, "Series:"),
        "pigment_code": extract_spec(html, "Pigment Code:"),
    }
    rows.append(row)
    print(f"OK  {name:50s}  pigment={row['pigment_code']}")

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nWrote {len(rows)} rows to {OUT_CSV}")
if missing:
    print(f"Missing pages: {missing}")
