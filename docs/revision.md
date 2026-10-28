# Fixed revision on Hugging Face

- repository: https://huggingface.co/datasets/yuiseki/akita-forest-resource-mesh-2026
- revision: `1cad01a041ad2e1bfc2fa9ba35bd1385070d3f5f`
- read back at this revision on 2026-10-29 by `scripts/07_verify_hub.py`: 72 files with the recorded sha256, 29,088,595 rows, one schema in all 60 parquet files and equal to the local copy, CRS EPSG:6678, 0 invalid geometries, rows per file equal to the extract log, non-NULL counts, unique values and ownership counts equal to the profile, no problems.
- load it with `hf://datasets/yuiseki/akita-forest-resource-mesh-2026@1cad01a041ad2e1bfc2fa9ba35bd1385070d3f5f/parquet/*.parquet`.
