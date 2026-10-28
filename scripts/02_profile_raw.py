#!/usr/bin/env python3
"""Profile the raw sheets (whole sheets, before any cutting by prefecture): layer, rows, geometry,
CRS, extent, invalid geometries, columns, NULL counts and the unique values of the text columns.

    uv run python scripts/02_profile_raw.py   # writes docs/raw_profile.json and docs/raw_profile.md
"""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pyogrio
import shapely

ROOT = Path(__file__).parents[1]
TEXT = ["林種", "森林簿樹種1", "森林簿樹種2", "森林簿樹種3", "レーザ解析樹種", "森林簿年月日"]


def main() -> int:
    run = sorted((ROOT / "data" / "raw").glob("*/MANIFEST.json"))[-1].parent
    sheets = sorted((run / "gpkg").glob("fr_mesh20m_*_2025.gpkg"))
    per_sheet, counts = {}, {c: Counter() for c in TEXT}
    nulls, rows, invalid = Counter(), 0, 0
    types, crs_seen, fields_seen, layers_seen = Counter(), set(), set(), set()
    ages, meas = Counter(), Counter()
    bbox = [1e18, 1e18, -1e18, -1e18]
    for p in sheets:
        layer = [str(x[0]) for x in pyogrio.list_layers(p) if x[1] is not None][0]
        layers_seen.add(layer)
        info = pyogrio.read_info(p, layer=layer)
        crs_seen.add(str(info["crs"]))
        fields_seen.add(tuple(info["fields"]))
        df = pyogrio.read_dataframe(p, layer=layer)
        g = df.geometry.values
        n = len(df)
        bad = int((~shapely.is_valid(g)).sum())
        for t, c in zip(*np.unique(shapely.get_type_id(g), return_counts=True), strict=True):
            types[int(t)] += int(c)
        b = df.total_bounds
        bbox = [min(bbox[0], b[0]), min(bbox[1], b[1]), max(bbox[2], b[2]), max(bbox[3], b[3])]
        for c in df.columns.drop("geometry"):
            nulls[c] += int(df[c].isna().sum())
        for c in TEXT:
            counts[c].update(df[c].fillna("<NULL>").tolist())
        ages.update(df["林齢"].fillna(-1).astype(int).tolist())
        meas.update(df["計測年月日"].astype(str).fillna("<NULL>").tolist())
        rows += n
        invalid += bad
        per_sheet[p.name] = {
            "rows": n,
            "invalid": bad,
            "fid_unique": bool(df.index.is_unique),
            "layer": layer,
        }
        print(p.name, n, bad, flush=True)
    res = {"sheets": len(sheets), "rows": rows, "invalid_geometry": invalid, "geometry_type_ids": dict(types),
           "layers": sorted(layers_seen), "crs": sorted(crs_seen), "field_sets": [list(f) for f in fields_seen],
           "bbox_plane_xy": bbox, "nulls": dict(nulls), "per_sheet": per_sheet,
           "value_counts": {c: dict(counts[c].most_common()) for c in TEXT},
           "age_counts": dict(sorted(ages.items())), "measure_date_counts": dict(sorted(meas.items()))}  # fmt: skip
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "raw_profile.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1) + "\n"
    )
    print("rows", rows, "invalid", invalid, "nulls", dict(nulls))
    return 0


if __name__ == "__main__":
    sys.exit(main())
