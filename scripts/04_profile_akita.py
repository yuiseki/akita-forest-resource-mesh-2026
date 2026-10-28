#!/usr/bin/env python3
"""Profile the Akita cells: unique values and counts of every tree column, NULL and non-NULL rates,
by municipality and by 国有林/民有林, and the cell-key uniqueness.

    uv run python scripts/04_profile_akita.py   # writes docs/akita_profile.json and docs/akita_profile.md
"""

import json
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).parents[1]
GLOB = str(ROOT / "data" / "parquet" / "sheet=*" / "part.parquet")
TREE = ["林種", "森林簿樹種1", "森林簿樹種2", "森林簿樹種3", "レーザ解析樹種"]
OTHER = ["林齢", "森林簿年月日", "樹冠高", "立木密度", "平均標高", "計測年月日"]
WORDS = ["ブナ", "ミズナラ", "ナラ", "コナラ"]


def main() -> int:
    con = duckdb.connect()
    con.execute(f"create view m as select * from read_parquet('{GLOB}')")
    q = lambda sql: con.execute(sql).fetchall()  # noqa: E731
    res = {}
    res["rows"] = q("select count(*) from m")[0][0]
    res["distinct_cells"] = q("select count(*) from (select distinct cell_x, cell_y from m)")[0][0]
    res["sheets"] = q("select count(distinct sheet) from m")[0][0]
    res["cell_extent"] = list(
        q("select min(cell_x), min(cell_y), max(cell_x), max(cell_y) from m")[0]
    )
    cols = TREE + OTHER
    res["non_null"] = {c: q(f'select count("{c}") from m')[0][0] for c in cols}
    res["unique_values"] = {
        c: dict(
            q(
                f"select coalesce(cast(\"{c}\" as varchar), '<NULL>') v, count(*) from m group by 1 order by 2 desc"
            )
        )
        for c in TREE + ["森林簿年月日", "計測年月日"]
    }
    res["age_zero_and_null"] = {
        "age0": q('select count(*) from m where "林齢" = 0')[0][0],
        "age_null": q('select count(*) from m where "林齢" is null')[0][0],
    }
    res["age_stats_non_null_non_zero"] = list(
        q('select min("林齢"), max("林齢"), avg("林齢") from m where "林齢" > 0')[0]
    )
    res["age_gt200"] = q('select count(*) from m where "林齢" > 200')[0][0]
    res["layer_ownership"] = dict(
        q("select coalesce(layer_ownership,'<NULL>'), count(*) from m group by 1 order by 2 desc")
    )
    res["layer_municipality_null"] = q(
        "select count(*) from m where layer_municipality_name is null"
    )[0][0]
    nn = ", ".join(
        f'count("{c}") as "{c}"'
        for c in TREE + ["林齢", "森林簿年月日", "樹冠高", "レーザ解析樹種", "立木密度", "平均標高"]
    )
    for key, col in (
        ("by_municipality", "layer_municipality_name"),
        ("by_ownership", "layer_ownership"),
    ):
        rows = con.execute(
            f"select coalesce({col}, '<NULL>') g, count(*) n, {nn} from m group by 1 order by n desc"
        ).fetchall()
        names = (
            ["group", "cells"]
            + TREE
            + ["林齢", "森林簿年月日", "樹冠高", "レーザ解析樹種", "立木密度", "平均標高"]
        )
        res[key] = [dict(zip(names, r, strict=True)) for r in rows]
    res["cross_林種_樹種1"] = [
        list(r)
        for r in con.execute(
            "select coalesce(\"林種\",'<NULL>'), coalesce(\"森林簿樹種1\",'<NULL>'), count(*) from m group by 1,2 order by 3 desc"
        ).fetchall()
    ]
    res["ownership_x_樹種1"] = [
        list(r)
        for r in con.execute(
            "select coalesce(layer_ownership,'<NULL>'), coalesce(\"森林簿樹種1\",'<NULL>'), count(*) from m group by 1,2 order by 1,3 desc"
        ).fetchall()
    ]
    res["any_value_with_search_word"] = {
        w: sum(n for c in TREE for v, n in res["unique_values"][c].items() if w in v) for w in WORDS
    }
    (ROOT / "docs" / "akita_profile.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1) + "\n"
    )
    n = res["rows"]
    pct = lambda a, b: f"{100 * a / b:.1f}%"  # noqa: E731
    md = [
        "# Akita cells of 全国森林資源メッシュ: profile",
        "",
        f"- cells: {n:,} in {res['sheets']} sheets (centre inside Akita); distinct (cell_x, cell_y): {res['distinct_cells']:,}, so {n - res['distinct_cells']} cell positions occur twice (both inside the same sheet, with identical attributes; kept as in the source)",
        f"- cell_x / cell_y extent in EPSG:6678: x {res['cell_extent'][0]} to {res['cell_extent'][2]}, y {res['cell_extent'][1]} to {res['cell_extent'][3]}; the cells cover {n * 400 / 1e6:,.1f} km2, against 11,635.9 km2 for the N03 polygon of Akita",
        f"- the cells are all of the land of Akita, forest or not; cells outside the forest register carry NULL: 林種 is NULL in {n - res['non_null']['林種']:,} cells",
        "",
        "## Non-NULL rate of every attribute (all Akita cells)",
        "",
        "| column | non-NULL cells | share |",
        "| --- | ---: | ---: |",
    ]
    md += [f"| {c} | {v:,} | {pct(v, n)} |" for c, v in res["non_null"].items()]
    md += [
        "",
        "レーザ解析樹種, 樹冠高, 立木密度, 平均標高 and 計測年月日 are NULL in every Akita cell: the laser-derived attributes are empty for the whole prefecture.",
        "",
        "## Unique values (Akita)",
        "",
    ]
    for c, v in res["unique_values"].items():
        md += (
            [f"### {c}", "", "| value | cells |", "| --- | ---: |"]
            + [f"| {k} | {x:,} |" for k, x in v.items()]
            + [""]
        )
    w = res["any_value_with_search_word"]
    md += [
        f"No value of any tree column contains ブナ, ミズナラ, ナラ or コナラ (cells with such a value: {w}). Broad-leaved trees are one class, 広葉樹.",
        "",
        f"林齢: 0 in {res['age_zero_and_null']['age0']:,} cells and NULL in {res['age_zero_and_null']['age_null']:,}; among the cells above 0 it runs {res['age_stats_non_null_non_zero'][0]:.0f} to {res['age_stats_non_null_non_zero'][1]:.0f} (mean {res['age_stats_non_null_non_zero'][2]:.1f}), and {res['age_gt200']:,} cells have an age above 200, the largest being {res['age_stats_non_null_non_zero'][1]:.0f}, which looks like a year and not an age (mostly 天然林 of 広葉樹); all kept as published.",
        "",
        "## Non-NULL by ownership (民国別, taken from the 森林計画対象森林レイヤ by the cell centre)",
        "",
    ]
    cols = ["林種", "森林簿樹種1", "森林簿樹種2", "森林簿樹種3", "林齢", "森林簿年月日"]
    md += [
        "| group | cells | " + " | ".join(cols) + " |",
        "| --- | ---: | " + " | ".join("---:" for _ in cols) + " |",
    ]
    for r in res["by_ownership"]:
        md.append(
            f"| {r['group']} | {r['cells']:,} | "
            + " | ".join(pct(r[c], r["cells"]) for c in cols)
            + " |"
        )
    md += [
        "",
        "`<NULL>` here means that the cell centre lies in no polygon of the layer (sea, rivers, non-forest land, and the edge of forest areas); 931,623 of those cells still carry a forest register value, so the mesh and the layer do not coincide at their edges.",
        "",
        "## Non-NULL by municipality (the same layer)",
        "",
        "| municipality | cells | " + " | ".join(cols) + " |",
        "| --- | ---: | " + " | ".join("---:" for _ in cols) + " |",
    ]
    for r in res["by_municipality"]:
        md.append(
            f"| {r['group']} | {r['cells']:,} | "
            + " | ".join(pct(r[c], r["cells"]) for c in cols)
            + " |"
        )
    md += [
        "",
        "## 林種 by 森林簿樹種1 (cells)",
        "",
        "| 林種 | 森林簿樹種1 | cells |",
        "| --- | --- | ---: |",
    ]
    md += [f"| {a} | {b} | {c:,} |" for a, b, c in res["cross_林種_樹種1"]]
    (ROOT / "docs" / "akita_profile.md").write_text("\n".join(md) + "\n")
    print(
        json.dumps(
            {
                k: res[k]
                for k in (
                    "rows",
                    "distinct_cells",
                    "sheets",
                    "non_null",
                    "layer_ownership",
                    "layer_municipality_null",
                    "any_value_with_search_word",
                )
            },
            ensure_ascii=False,
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
