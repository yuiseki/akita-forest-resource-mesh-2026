#!/usr/bin/env python3
"""Write data/README.md (the dataset card), data/LICENSE and data/provenance.yaml from the measured docs.

uv run python scripts/05_card.py
"""

import json
from pathlib import Path

import rfm

ROOT = Path(__file__).parents[1]
DATA = ROOT / "data"
MESH_PAGE = rfm.PAGE + rfm.MESH_ID
LAYER_PAGE = rfm.PAGE + rfm.LAYER_ID
GITHUB = "https://github.com/yuiseki/akita-forest-resource-mesh-2026"

ATTRIBUTION = (
    f"出典：林野庁（{MESH_PAGE}、{LAYER_PAGE}）、PDL1.0（{rfm.PDL_URL}）をもとに yuiseki が作成。"
    "林野庁の「全国森林資源メッシュ」と「森林計画対象森林レイヤ」から秋田県の部分を切り出し、"
    "GeoParquet に変換し、市町村と民有林・国有林の列を加えた加工物であり、林野庁が作成した未加工のデータではない。"
    "（取得日 {date}）"
)

CARD = """---
license: other
license_name: pdl-1.0
license_link: {pdl}
language:
- ja
tags:
- forest
- japan
- akita
- geospatial
- geoparquet
size_categories:
- 10M<n<100M
configs:
- config_name: default
  data_files: parquet/*.parquet
---

# 全国森林資源メッシュ 秋田県 (akita-forest-resource-mesh-2026)

林野庁の「全国森林資源メッシュ」(20 m メッシュ)のうち、秋田県の部分を切り出して固定した GeoParquet です。
分析やモデルは含みません。原データの属性は名前も値も変えていません。

An Akita Prefecture extract of 全国森林資源メッシュ (Forestry Agency, MAFF; 20 m cells), frozen as GeoParquet, one file per
source sheet. The 11 source attributes keep their names and values.

## Read this first: what the Akita data can and cannot say

- The tree columns (森林簿樹種1, 森林簿樹種2, 森林簿樹種3) hold coarse classes from the forest register: スギ, ヒノキ類,
  マツ類, カラマツ, ヒバ, エゾマツ, その他針葉樹, 広葉樹, タケ, その他, 伐採跡地. All broad-leaved trees are one class,
  **広葉樹**. No value contains ブナ, ミズナラ, ナラ or コナラ, so beech and oak cannot be told apart in these data.
- The laser-derived columns (レーザ解析樹種, 樹冠高, 立木密度, 平均標高, 計測年月日) are NULL in **every** Akita cell.
- {n_cells:,} cells cover all of the land of Akita; only {pct_forest:.1f}% of them carry a forest register value
  (林種 non-NULL in {forest_cells:,} cells). The others are outside the forest register (non-forest land, water,
  or forest without register data).
- Yuzawa city: {yuzawa_null:,} of {yuzawa_n:,} private-forest cells have no register value (21%); other municipalities
  are nearly complete (see `docs/akita_profile.md`).

## Source and licence

- Source: 全国森林資源メッシュ, 林野庁 森林整備部 計画課, Plane Rectangular CS X zone (青森・秋田・山形・岩手・宮城), the
  record `mesh_10` on G空間情報センター ({mesh_page}); the 60 sheets (国土基本図図郭 quarter sheets, file names
  `fr_mesh20m_<sheet>_2025`) that touch Akita. The ownership and municipality columns come from the 森林計画対象森林レイヤ
  of Akita, `fr_layer_05_2025` ({layer_page}), by the same agency.
- Retrieved {date}. The records have no version field (created {created}, metadata modified {modified}); the archives were
  last modified {archive_lm} on the server. Each original is dated by its own 森林簿年月日 (2019/4/1 to 2024/4/1).
  sha256 of every archive is in `raw/{run}/MANIFEST.json`.
- Licence: 公共データ利用規約 第1.0版 (PDL1.0), stated on the record together with the Forestry Agency's 重要情報 and the
  全国森林資源メッシュの利用規約 (the CKAN licence field says 政府標準利用規約, the earlier terms; both are CC BY compatible).
  Conditions: cite the source; say that the data were edited and by whom; do not present the result as made by the
  Forestry Agency; matching with a personal-information database falls under the personal information protection law.
- The 利用規約 of the data adds these cautions: the register-derived information is made mainly by interpreting aerial
  photographs at 1/5,000 and may carry errors from the originating offices; laser-derived information has no guaranteed
  accuracy; the data are not equal to the field, to land registers or to tax records and prove no ownership, boundary,
  area or value of standing timber; they show the state at the time of each original (see 森林簿年月日), not today;
  the Forestry Agency and the originating offices take no responsibility for any use, including use of processed data.
- Attribution to use: {attribution}
- Cutter: the polygon of Akita in 国土数値情報 行政区域 (N03, 2026-01-01; MLIT), used only to choose cells and not republished.

## Files

| path | content |
| --- | --- |
| `parquet/<sheet>.parquet` | {n_files} files, one per source sheet that has cells inside Akita; GeoParquet, EPSG:6678, zstd; {n_cells:,} cells in all |
| `docs/akita_profile.md`, `docs/akita_profile.json` | unique values, NULL and non-NULL rates by column, municipality and ownership |
| `docs/raw_profile.md`, `docs/raw_profile.json` | the same for the 60 whole sheets before the cut |
| `docs/extract_log.json`, `docs/verify_local.json` | counts of the cut and the check against the source |
| `raw/{run}/MANIFEST.json`, `raw/{run}/ckan_*.json` | source archives with sha256 and HTTP headers; the records |

Read it with `read_parquet('hf://datasets/yuiseki/akita-forest-resource-mesh-2026/parquet/*.parquet')`.

## Columns and their correspondence to the source

| column here | source | note |
| --- | --- | --- |
| `林種` | 林種 | 人工林, 天然林, 伐採跡地, 未立木地, 竹林, その他 |
| `森林簿樹種1`, `森林簿樹種2`, `森林簿樹種3` | same | first, second, third tree class by area share in the register. The real column names use the digits 1, 2, 3; the data definition writes １, ２, ３ |
| `林齢` | 林齢 | integer, age of tree class 1 |
| `森林簿年月日` | 森林簿年月日 | text such as 2024/3/31 |
| `樹冠高`, `レーザ解析樹種`, `立木密度`, `平均標高`, `計測年月日` | same | all NULL in Akita |
| `geometry` | geom | MultiPolygon of one 20 m cell, EPSG:6678 (JGD2011 / Plane Rectangular CS X), unchanged |
| `sheet` | added | the source sheet name, such as 10IC1 |
| `source_fid` | added | the GeoPackage fid inside that sheet's file |
| `cell_x`, `cell_y` | added | lower-left corner of the cell in EPSG:6678 (metres) |
| `layer_ownership` | added from the layer's 民国別 | 民有林 or 国有林 of the 森林計画対象森林レイヤ polygon that contains the cell centre |
| `layer_municipality_code5`, `layer_municipality_name` | added from the layer's 市町村コード5桁, 市町村名称 | same polygon; NULL when the centre lies in no layer polygon |

## How Akita was cut

1. The rule: a cell belongs to Akita when its centre lies inside the N03 polygon of Akita. Cells are not cut; a cell
   on the prefecture boundary goes to the side of its centre. Cells of other prefectures and of the sea in the border
   sheets are dropped.
2. {n_cells:,} cells of {raw_rows:,} cells in the 60 sheets are kept (all of the land of Akita: they cover {cover:,.1f} km2
   against 11,635.9 km2 for the N03 polygon). Every kept cell is kept, including the ones with NULL attributes.
3. Layer columns: the cell centre is moved to EPSG:6668 and tested against the layer polygons; {no_layer:,} cells lie in no
   polygon (NULL); if a centre lies in several polygons the first one is taken ({multi:,} such cells).

## Cautions

- {dups} cell positions occur twice in the source (inside the same sheet, identical attributes); they are kept.
- The text `#N/A` occurs as a value of 森林簿樹種1 ({na1:,} cells) and of 森林簿樹種2 ({na2:,}); it is kept as in the source.
- 林齢 is 0 in {age0:,} cells (whether 0 means a real age of zero or an unknown age is not stated) and exceeds 200 in
  {age200:,} cells, up to {age_max:.0f}, which looks like a year and not an age; kept as published.
- {edge:,} cells have a register value although their centre lies in no layer polygon, so the mesh and the layer do not
  coincide at their edges.
- 森林簿樹種2 and 3 are rarely present ({n2:.1f}% and {n3:.1f}% of cells) and 国有林 cells have them much more often than 民有林.
- The cells and attributes are as of each original's date; this is the copy retrieved on {date}.

## Verification

`scripts/06_verify.py` reads each raw sheet again with a second engine (DuckDB spatial) and checks, sheet by sheet, that
the same cells are chosen, that the 11 attributes, the geometry (byte-equal WKB) and the cell corner are equal, and that
the three layer columns agree with a point-in-polygon test done again (`docs/verify_local.json`). After the upload,
`scripts/07_verify_hub.py` reads this repository back at a fixed revision and compares checksums, row counts, schema,
CRS, extent, geometry validity, value counts and NULL counts. The revision is recorded in `docs/revision.md` of the GitHub
repository ({github}).

Reproduce: `uv run python scripts/01_download.py`, then `02` to `07` in order.
"""


def main() -> None:
    run = sorted((DATA / "raw").glob("*/MANIFEST.json"))[-1].parent
    man = json.loads((run / "MANIFEST.json").read_text())
    mesh = json.loads((run / "ckan_mesh_10.json").read_text())
    prof = json.loads((ROOT / "docs" / "akita_profile.json").read_text())
    raw = json.loads((ROOT / "docs" / "raw_profile.json").read_text())
    log = json.loads((ROOT / "docs" / "extract_log.json").read_text())
    date = f"{run.name[:4]}-{run.name[4:6]}-{run.name[6:]}"
    n = prof["rows"]
    yuzawa = next(r for r in prof["by_municipality"] if r["group"] == "湯沢市")
    # private-forest cells of Yuzawa that lack the register: counted in the profile of the same data
    import duckdb

    con = duckdb.connect()
    glob = str(DATA / "parquet" / "sheet=*" / "part.parquet")
    yz = con.execute(
        f"select count(*), count(*) filter (where \"森林簿樹種1\" is null) from read_parquet('{glob}') "
        "where layer_municipality_name = '湯沢市' and layer_ownership = '民有林'"
    ).fetchone()
    del yuzawa
    edge = con.execute(
        f"select count(*) from read_parquet('{glob}') where layer_ownership is null and \"林種\" is not null"
    ).fetchone()[0]
    dup = n - prof["distinct_cells"]
    na = prof["unique_values"]
    sheets = log["sheets"]
    archive_lm = man["files"][next(k for k in man["files"] if k.startswith("fr_mesh20m_"))]["http"][
        "last-modified"
    ]
    attribution = ATTRIBUTION.format(date=date)
    card = CARD.format(
        pdl=rfm.PDL_URL, n_cells=n, pct_forest=100 * prof["non_null"]["林種"] / n, forest_cells=prof["non_null"]["林種"],
        yuzawa_null=yz[1], yuzawa_n=yz[0], mesh_page=MESH_PAGE, layer_page=LAYER_PAGE, date=date, run=run.name,
        created=mesh["metadata_created"][:10], modified=mesh["metadata_modified"][:10], archive_lm=archive_lm,
        attribution=attribution, n_files=sum(1 for v in sheets.values() if v["kept"]), raw_rows=raw["rows"],
        cover=n * 400 / 1e6, no_layer=sum(v.get("no_layer_polygon", 0) for v in sheets.values()),
        multi=sum(v.get("cells_in_several_layer_polygons", 0) for v in sheets.values()), dups=dup,
        na1=na["森林簿樹種1"].get("#N/A", 0), na2=na["森林簿樹種2"].get("#N/A", 0),
        age0=prof["age_zero_and_null"]["age0"], age200=prof["age_gt200"], age_max=prof["age_stats_non_null_non_zero"][1],
        edge=edge, n2=100 * prof["non_null"]["森林簿樹種2"] / n, n3=100 * prof["non_null"]["森林簿樹種3"] / n, github=GITHUB,
    )  # fmt: skip
    (DATA / "README.md").write_text(card, encoding="utf-8")
    (DATA / "LICENSE").write_text(
        "公共データ利用規約（第1.0版）PDL1.0 (" + rfm.PDL_URL + ")\n\n"
        "The data are 全国森林資源メッシュ and 森林計画対象森林レイヤ of the Forestry Agency (MAFF), published under PDL1.0,\n"
        "which is compatible with CC BY 4.0, together with the 全国森林資源メッシュの利用規約. They were processed as described in README.md.\n\n"
        + attribution
        + "\n",
        encoding="utf-8",
    )
    (DATA / "provenance.yaml").write_text(
        f"source: 全国森林資源メッシュ (林野庁)\nurl: {MESH_PAGE}\nlayer_url: {LAYER_PAGE}\nlicense: PDL1.0\nretrieved: {date}\n"
        f"record_metadata_modified: {mesh['metadata_modified']}\narchives: {len(man['sheets'])} sheets, sha256 in raw/{run.name}/MANIFEST.json\n"
        f"cutter: {rfm.N03_URL}\nrows: {n}\n",
        encoding="utf-8",
    )
    print("wrote card, LICENSE, provenance.yaml")


if __name__ == "__main__":
    main()
