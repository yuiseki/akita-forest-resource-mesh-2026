# Raw profile of the 60 sheets that touch Akita (whole sheets, before any cutting)

Source: G空間情報センター dataset `mesh_10` (全国森林資源メッシュ, zone X), sheets chosen by intersecting the sheet index with the Akita boundary (KSJ N03). Downloaded 2026-10-28; sha256 of each archive is in data/raw/20261028/MANIFEST.json (kept in the Hugging Face repo).

These counts cover the whole sheets, so they include cells of Aomori, Iwate, Yamagata and Miyagi and of the sea. The Akita-only figures are in docs/akita_profile.md.

- sheets: 60; rows: 38,875,524; one layer per file named like the file; geometry: MultiPolygon only (type id 6); invalid geometries: 0
- CRS: EPSG:6678 (JGD2011 / Japan Plane Rectangular CS X); plane bbox x -97460 to 20000, y -135000 to 60000
- columns (identical in all sheets): 林種, 森林簿樹種1, 森林簿樹種2, 森林簿樹種3, 林齢, 森林簿年月日, 樹冠高, レーザ解析樹種, 立木密度, 平均標高, 計測年月日 (plus the GeoPackage fid). The tree columns are named 森林簿樹種1/2/3 with ASCII digits, while the data definition writes １/２/３.

| column | NULL rows | share of rows |
| --- | ---: | ---: |
| 林種 | 8,395,280 | 21.6% |
| 森林簿樹種1 | 8,348,958 | 21.5% |
| 森林簿樹種2 | 26,331,365 | 67.7% |
| 森林簿樹種3 | 33,745,582 | 86.8% |
| 林齢 | 8,395,280 | 21.6% |
| 森林簿年月日 | 8,347,696 | 21.5% |
| 樹冠高 | 38,875,524 | 100.0% |
| レーザ解析樹種 | 38,757,133 | 99.7% |
| 立木密度 | 38,815,028 | 99.8% |
| 平均標高 | 38,762,388 | 99.7% |
| 計測年月日 | 38,757,133 | 99.7% |

## Unique values of the text columns (all 60 sheets)

### 林種

| value | rows |
| --- | ---: |
| 天然林 | 15,779,127 |
| 人工林 | 13,533,653 |
| <NULL> | 8,395,280 |
| その他 | 858,374 |
| 伐採跡地 | 204,243 |
| 未立木地 | 99,286 |
| 竹林 | 5,561 |

### 森林簿樹種1

| value | rows |
| --- | ---: |
| 広葉樹 | 15,114,837 |
| スギ | 11,983,548 |
| <NULL> | 8,348,958 |
| マツ類 | 894,193 |
| その他 | 887,867 |
| カラマツ | 868,361 |
| その他針葉樹 | 345,779 |
| #N/A | 207,716 |
| ヒバ | 120,576 |
| 伐採跡地 | 89,412 |
| ヒノキ類 | 8,703 |
| タケ | 5,561 |
| エゾマツ | 13 |

### 森林簿樹種2

| value | rows |
| --- | ---: |
| <NULL> | 26,331,365 |
| 広葉樹 | 10,468,784 |
| スギ | 810,267 |
| マツ類 | 602,334 |
| カラマツ | 371,987 |
| ヒバ | 164,187 |
| その他針葉樹 | 120,742 |
| ヒノキ類 | 4,654 |
| #N/A | 589 |
| 伐採跡地 | 444 |
| タケ | 95 |
| その他 | 76 |

### 森林簿樹種3

| value | rows |
| --- | ---: |
| <NULL> | 33,745,582 |
| 広葉樹 | 2,953,332 |
| マツ類 | 815,637 |
| スギ | 525,214 |
| その他針葉樹 | 456,875 |
| ヒバ | 302,595 |
| カラマツ | 71,619 |
| ヒノキ類 | 4,670 |

### レーザ解析樹種

| value | rows |
| --- | ---: |
| <NULL> | 38,757,133 |
| スギ | 52,389 |
| その他 | 31,302 |
| その他L | 22,808 |
| マツ類 | 10,051 |
| 伐採跡地 | 938 |
| タケ | 636 |
| カラマツ | 265 |
| その他N | 1 |
| ヒノキ類 | 1 |

### 森林簿年月日

| value | rows |
| --- | ---: |
| 2024/3/31 | 11,853,069 |
| <NULL> | 8,347,696 |
| 2023/4/1 | 6,991,660 |
| 2020/4/1 | 5,735,809 |
| 2019/4/1 | 1,738,898 |
| 2022/4/1 | 1,607,494 |
| 2024/4/1 | 1,290,650 |
| 2021/4/1 | 1,113,086 |
| 2023/3/31 | 197,162 |

## Other findings

- 樹冠高 is NULL in every row of these sheets, and レーザ解析樹種, 立木密度, 平均標高 and 計測年月日 are NULL in about 99.7% of rows; the only 計測年月日 present is 2022-08-22 (118,391 rows).
- The literal text `#N/A` occurs as a value of 森林簿樹種1 (207,716 rows) and 森林簿樹種2 (589 rows). It is kept as it is in the source.
- 林齢 is 0 in 1,125,443 rows besides the NULLs; whether 0 means an age of zero or an unknown age is not stated in the definition.
- 森林簿年月日 holds nine dates between 2019/4/1 and 2024/4/1, as text.
- No column separates 国有林 from 民有林 in the mesh; that attribute (民国別) is in the 森林計画対象森林レイヤ of Akita (downloaded as well).
