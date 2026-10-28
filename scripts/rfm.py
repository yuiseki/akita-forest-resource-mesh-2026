"""Constants shared by the scripts of akita-forest-resource-mesh-2026."""

CKAN = "https://www.geospatial.jp/ckan/api/3/action/package_show?id="
MESH_ID = "mesh_10"  # 全国森林資源メッシュ, Plane Rectangular CS X zone: Aomori, Akita, Yamagata, Iwate, Miyagi
LAYER_ID = "layer"  # 森林計画対象森林レイヤ: carries 民国別 and 市町村, which the mesh lacks
PAGE = "https://www.geospatial.jp/ckan/dataset/"
PDL_URL = "https://www.digital.go.jp/resources/open_data/public_data_license_v1.0"
UA = "Mozilla/5.0 (research; yuiseki)"
N03_URL = "https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2026/N03-20260101_05_GML.zip"
N03_PAGE_URL = "https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N03-2026.html"
MESH_CRS = 6678  # JGD2011 / Japan Plane Rectangular CS X
LAYER_FILE = "fr_layer_05_2025.7z"  # prefecture code 05 = Akita
MESH_COLUMNS = ["林種", "森林簿樹種１", "森林簿樹種２", "森林簿樹種３", "林齢", "森林簿年月日",
                "樹冠高", "レーザ解析樹種", "立木密度", "平均標高", "計測年月日"]  # fmt: skip
