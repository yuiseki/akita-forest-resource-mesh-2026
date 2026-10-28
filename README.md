# akita-forest-resource-mesh-2026

Akita Prefecture extract of 全国森林資源メッシュ (Forestry Agency, MAFF), frozen on Hugging Face as
`yuiseki/akita-forest-resource-mesh-2026`. Survey: https://github.com/yuiseki/akita-beech-oak-sources

Scripts run in order (`uv run python scripts/NN_*.py`); `data/` is not in git.

1. `01_download.py` the 60 sheets that touch Akita, the 森林計画対象森林レイヤ of Akita, the terms and the data definition
2. `02_profile_raw.py` raw profile of the whole sheets; results in `docs/`
