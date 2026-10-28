# akita-forest-resource-mesh-2026

Akita Prefecture extract of 全国森林資源メッシュ (Forestry Agency, MAFF), frozen on Hugging Face as
`yuiseki/akita-forest-resource-mesh-2026`. Survey: https://github.com/yuiseki/akita-beech-oak-sources

Scripts run in order (`uv run python scripts/NN_*.py`); `data/` is not in git.

1. `01_download.py` the 60 sheets that touch Akita, the 森林計画対象森林レイヤ of Akita, the terms and the data definition
2. `02_profile_raw.py` raw profile of the whole sheets; results in `docs/`
3. `03_extract_akita.py`, `04_profile_akita.py` keep the cells whose centre is inside Akita and profile them
4. `05_card.py` card, licence, provenance; `06_verify.py` second-engine check against the raw sheets
5. `src/publish.py --push` upload in one commit; `07_verify_hub.py` read back at the fixed revision (`docs/revision.md`)
