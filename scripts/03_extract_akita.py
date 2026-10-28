#!/usr/bin/env python3
"""Keep the 20 m cells of the 60 raw sheets whose centre lies inside Akita, one GeoParquet per sheet.

Rule (recorded in the card): cells are not cut; a cell belongs to Akita when its centre is inside the
KSJ N03 (2026-01-01) polygon of Akita. The original 11 attributes keep their names and values.
Added columns: sheet, source_fid (fid inside the sheet), cell_x, cell_y (lower-left corner in
EPSG:6678, metres), and three columns taken from the 森林計画対象森林レイヤ of Akita by the cell centre:
layer_ownership (民国別), layer_municipality_code5 (市町村コード5桁), layer_municipality_name (市町村名称).

    uv run python scripts/03_extract_akita.py   # writes data/parquet/sheet=<name>/part.parquet and docs/extract_log.json
"""

import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import rfm
import shapely
from pyproj import Transformer
from shapely import STRtree

ROOT = Path(__file__).parents[1]


def main() -> int:
    run = sorted((ROOT / "data" / "raw").glob("*/MANIFEST.json"))[-1].parent
    z = ROOT / "data" / "docs" / "N03-20260101_05_GML.zip"
    shp = next(n for n in zipfile.ZipFile(z).namelist() if n.endswith(".shp"))
    n03 = gpd.read_file(f"zip://{z}!{shp}")
    assert set(n03["N03_001"]) == {"秋田県"} and n03.crs.to_epsg() == 6668
    cutter = n03.to_crs(rfm.MESH_CRS).geometry.union_all()
    shapely.prepare(cutter)
    layer = gpd.read_file(run / "gpkg" / "fr_layer_05_2025.gpkg", layer="秋田県")
    tree = STRtree(layer.geometry.values)
    to_geo = Transformer.from_crs(rfm.MESH_CRS, 6668, always_xy=True)
    out_dir = ROOT / "data" / "parquet"
    log = {
        "cutter": "KSJ N03 20260101 05 (Akita), dissolved",
        "sheets": {},
        "layer_polygons": len(layer),
    }
    total = 0
    for p in sorted((run / "gpkg").glob("fr_mesh20m_*_2025.gpkg")):
        sheet = p.name.split("_")[2]
        df = pyogrio.read_dataframe(p, fid_as_index=True, use_arrow=True)
        b = shapely.bounds(df.geometry.values)
        cx, cy = (b[:, 0] + b[:, 2]) / 2, (b[:, 1] + b[:, 3]) / 2
        sel = shapely.contains_xy(cutter, cx, cy)
        if not sel.any():
            log["sheets"][sheet] = {"read": len(df), "kept": 0}
            continue
        d = df[sel].copy()
        b, cx, cy = b[sel], cx[sel], cy[sel]
        d.insert(0, "source_fid", d.index.astype("int64"))
        d.insert(0, "sheet", sheet)
        d["cell_x"] = np.rint(b[:, 0]).astype("int64")
        d["cell_y"] = np.rint(b[:, 1]).astype("int64")
        lon, lat = to_geo.transform(cx, cy)
        pts = shapely.points(lon, lat)
        ii, jj = tree.query(pts, predicate="within")
        first = pd.Series(jj, index=ii).groupby(level=0).first()
        n_multi = int((pd.Series(ii).value_counts() > 1).sum())
        match = np.full(len(d), -1)
        match[first.index.values] = first.values
        for col, src in (("layer_ownership", "民国別"), ("layer_municipality_code5", "市町村コード5桁"),
                         ("layer_municipality_name", "市町村名称")):  # fmt: skip
            vals = layer[src].values
            d[col] = np.where(match >= 0, vals[np.maximum(match, 0)], None)
        d = d.reset_index(drop=True)
        (out_dir / f"sheet={sheet}").mkdir(parents=True, exist_ok=True)
        d.to_parquet(
            out_dir / f"sheet={sheet}" / "part.parquet",
            compression="zstd",
            write_covering_bbox=True,
            index=False,
        )
        log["sheets"][sheet] = {"read": len(df), "kept": len(d), "no_layer_polygon": int((match < 0).sum()),
                                "cells_in_several_layer_polygons": n_multi}  # fmt: skip
        total += len(d)
        print(sheet, log["sheets"][sheet], flush=True)
    log["rows"] = total
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "extract_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=1) + "\n"
    )
    print("rows", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
