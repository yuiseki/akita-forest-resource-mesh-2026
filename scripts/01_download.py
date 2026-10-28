#!/usr/bin/env python3
"""Download the Akita part of 全国森林資源メッシュ (and the 森林計画対象森林レイヤ of Akita).

    uv run python scripts/01_download.py

Steps: read the two CKAN records and stop if the licence text is gone; save the terms PDFs and the
sheet index; cut the sheet index with the Akita boundary (KSJ N03, a cutter only) to choose the
sheets; download and unpack those sheets; write MANIFEST.json with sha256, size and HTTP headers.
"""

import hashlib
import json
import subprocess
import sys
import time
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

import geopandas as gpd
import rfm

ROOT = Path(__file__).parents[1]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": rfm.UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
    return h.hexdigest()


def probe(url: str) -> tuple[str, dict]:
    out = subprocess.run(
        ["curl", "-sS", "-L", "-A", rfm.UA, "-r", "0-0", "-D", "-", "-o", "/dev/null",
         "-w", "\n@@%{url_effective}", url],
        check=True, capture_output=True, text=True,
    ).stdout.replace("\r", "")  # fmt: skip
    final = out.rsplit("@@", 1)[1].strip()
    last = [h for h in out.split("\n\n") if h.startswith("HTTP/")][-1]
    pick = {}
    for line in last.splitlines()[1:]:
        k, _, v = line.partition(":")
        if k.lower() in ("etag", "last-modified", "content-range"):
            pick[k.lower()] = v.strip()
    return final, pick


def fetch(url: str, dest: Path, connections: int = 2) -> dict:
    """Resumable ranged download; the signed link is resolved again whenever a round falls short."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    for _attempt in range(6):
        final, head = probe(url)
        total = int(head["content-range"].rsplit("/", 1)[1])
        done = dest.exists() and dest.stat().st_size == total
        if done and not dest.with_name(dest.name + ".aria2").exists():
            return head
        subprocess.run(["aria2c", "-c", "-x", str(connections), "-s", str(connections), "-k", "4M",
                        "--user-agent", rfm.UA, "--summary-interval=0", "--console-log-level=warn",
                        "-d", str(dest.parent), "-o", dest.name, final], check=False)  # fmt: skip
    raise SystemExit(f"could not fetch {url}")


def read_n03(zpath: Path) -> gpd.GeoDataFrame:
    """The Akita polygons of the KSJ N03 zip (the shapefile inside; GeoJSON copies are ignored)."""
    shp = next(n for n in zipfile.ZipFile(zpath).namelist() if n.endswith(".shp"))
    return gpd.read_file(f"zip://{zpath}!{shp}")


def record(ckan_id: str) -> dict:
    return json.loads(get(rfm.CKAN + ckan_id))["result"]


def main() -> int:
    run = date.today().strftime("%Y%m%d")
    out = ROOT / "data" / "raw" / run
    docs = ROOT / "data" / "docs"
    out.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    mesh, layer = record(rfm.MESH_ID), record(rfm.LAYER_ID)
    for rec in (mesh, layer):
        if "公共データ利用規約（第1.0版）" not in rec["notes"]:
            raise SystemExit(f"{rec['name']}: the PDL1.0 statement is gone from the record")
        if not any("重要情報" in r["name"] for r in rec["resources"]):
            raise SystemExit(f"{rec['name']}: the 重要情報 PDF is gone from the record")
    keep = ("id", "name", "title", "license_id", "license_title", "metadata_created",
            "metadata_modified", "author", "notes")  # fmt: skip
    manifest = {"run": run, "files": {}}
    for rec in (mesh, layer):
        meta = {k: rec.get(k) for k in keep}
        meta["resources"] = [{k: r.get(k) for k in ("name", "format", "url", "size", "last_modified")}
                             for r in rec["resources"] if r["format"] in ("PDF", "gpkg", "7z", "")]  # fmt: skip
        (out / f"ckan_{rec['name']}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1) + "\n"
        )
    # terms, definition and index
    for rec in (mesh, layer):
        for r in rec["resources"]:
            if r["format"] == "PDF" or (r["format"] == "gpkg" and "mesh_index" in r["url"]):
                name = f"{rec['name']}__{r['url'].rsplit('/', 1)[1]}"
                (docs / name).write_bytes(get(r["url"]))
                manifest["files"][name] = {"url": r["url"], "sha256": sha256(docs / name)}
    n03 = docs / "N03-20260101_05_GML.zip"
    n03.write_bytes(get(rfm.N03_URL))
    manifest["files"][n03.name] = {"url": rfm.N03_URL, "sha256": sha256(n03), "role": "cutter only"}
    # choose the sheets that touch Akita
    idx_name = next(n for n in manifest["files"] if n.endswith("10kei_mesh_index.gpkg"))
    sheets = gpd.read_file(docs / idx_name)
    akita = read_n03(n03).to_crs(rfm.MESH_CRS)
    cutter = akita.geometry.union_all()
    chosen = sorted(
        set(sheets.loc[sheets.intersects(cutter), "図郭名"])
    )  # the index repeats some sheets
    print(len(chosen), "sheets touch Akita:", chosen)
    manifest["sheets"] = chosen
    by_name = {r["name"]: r for r in mesh["resources"] if r["format"] == "7z"}
    for sheet in chosen:
        name = f"fr_mesh20m_{sheet}_2025.7z"
        r = by_name[name]
        head = fetch(r["url"], out / name)
        time.sleep(2)  # the host answered 403 to a burst of requests once
        subprocess.run(
            ["7z", "x", "-y", f"-o{out / 'gpkg'}", str(out / name)], check=True, capture_output=True
        )
        manifest["files"][name] = {"url": r["url"], "size": (out / name).stat().st_size,
                                   "sha256": sha256(out / name), "record_last_modified": r["last_modified"],
                                   "http": head}  # fmt: skip
        print(name, manifest["files"][name]["size"])
    lr = next(r for r in layer["resources"] if r["name"] == rfm.LAYER_FILE)
    # the record gives ".../download/www.geospatial.jpfr_layer_05_2025.7z", which answers 500; the
    # same resource under its plain file name works
    layer_url = lr["url"].replace("/download/www.geospatial.jp", "/download/")
    head = fetch(layer_url, out / rfm.LAYER_FILE)
    subprocess.run(
        ["7z", "x", "-y", f"-o{out / 'gpkg'}", str(out / rfm.LAYER_FILE)],
        check=True,
        capture_output=True,
    )
    manifest["files"][rfm.LAYER_FILE] = {"url": layer_url, "size": (out / rfm.LAYER_FILE).stat().st_size,
                                         "sha256": sha256(out / rfm.LAYER_FILE),
                                         "record_last_modified": lr["last_modified"], "http": head}  # fmt: skip
    manifest["gpkg"] = sorted(p.name for p in (out / "gpkg").rglob("*.gpkg"))
    (out / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    print("wrote", out / "MANIFEST.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
