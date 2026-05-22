#!/usr/bin/env python3
"""
For each color, find all subsets of other colors whose union of pigments
covers exactly the target color's pigments (no more, no less).
"""

import json
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).parent
data = json.loads((ROOT / "pigment_table.json").read_text())

colors = data["colors"]
# color_id -> frozenset of pigments
pigset = {c["color_id"]: frozenset(c["pigments"]) for c in colors}
id_to_name = {c["color_id"]: c["name"] for c in colors}
all_ids = list(pigset.keys())

results = {}

for target in colors:
    tid = target["color_id"]
    target_pigs = pigset[tid]
    others = [cid for cid in all_ids if cid != tid]

    # Try all subsets of size 1, 2, 3 of other colors
    # whose pigment union == target_pigs
    found = []
    for size in range(1, 4):
        for combo in combinations(others, size):
            union = frozenset().union(*(pigset[cid] for cid in combo))
            if union == target_pigs:
                found.append([id_to_name[cid] for cid in combo])
        # if found at this size, don't look for larger (redundant supersets)
        if found:
            break

    results[target["name"]] = {
        "pigments": sorted(target_pigs),
        "mixable_from": found,
    }

OUT = ROOT / "mixings.json"
OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(f"Written: {OUT}")
