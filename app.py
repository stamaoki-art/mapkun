import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import streamlit as st
import folium
from folium.plugins import Geocoder
from streamlit_folium import st_folium

st.set_page_config(page_title="地理院地図 Viewer", layout="wide")
st.title("🗺️ 国土地理院地図 Viewer")

# 1. Session State の初期化
if "lat" not in st.session_state:
    st.session_state["lat"] = 35.681236  # 初期値（東京駅）
if "lon" not in st.session_state:
    st.session_state["lon"] = 139.767125
if "zoom" not in st.session_state:
    st.session_state["zoom"] = 14
if "drawn_geojson" not in st.session_state:
    st.session_state["drawn_geojson"] = None
if "is_point" not in st.session_state:
    st.session_state["is_point"] = False
if "drawn_count" not in st.session_state:
    st.session_state["drawn_count"] = 0

# 都道府県ポリゴン＆液状化タイルURLデータ
PREF_EKIJOKA_DATA = [
    {"name": "北海道", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/01_hokkai/{z}/{x}/{y}.png", "bbox": [139.3, 41.3, 148.9, 45.6]},
    {"name": "青森県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/02_aomori/{z}/{x}/{y}.png", "bbox": [139.8, 40.2, 141.7, 41.6]},
    {"name": "岩手県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/03_iwate/{z}/{x}/{y}.png", "bbox": [140.6, 38.7, 142.1, 40.5]},
    {"name": "宮城県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/04_miyagi/{z}/{x}/{y}.png", "bbox": [140.2, 37.7, 141.7, 39.0]},
    {"name": "秋田県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/05_akita/{z}/{x}/{y}.png", "bbox": [139.7, 38.9, 140.8, 40.5]},
    {"name": "山形県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/06_yamagata/{z}/{x}/{y}.png", "bbox": [139.5, 37.7, 140.7, 39.2]},
    {"name": "福島県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/07_fukushima/{z}/{x}/{y}.png", "bbox": [139.1, 36.8, 141.1, 37.9]},
    {"name": "茨城県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/08_ibaraki/{z}/{x}/{y}.png", "bbox": [139.7, 35.7, 140.9, 36.9]},
    {"name": "栃木県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/09_tochigi/{z}/{x}/{y}.png", "bbox": [139.3, 36.2, 140.3, 37.2]},
    {"name": "群馬県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/10_gunma/{z}/{x}/{y}.png", "bbox": [138.3, 35.9, 139.6, 37.1]},
    {"name": "埼玉県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/11_saitama/{z}/{x}/{y}.png", "bbox": [138.7, 35.7, 139.9, 36.3]},
    {"name": "千葉県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/12_chiba/{z}/{x}/{y}.png", "bbox": [139.7, 34.9, 140.9, 36.1]},
    {"name": "東京都", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/13_tokyo/{z}/{x}/{y}.png", "bbox": [138.9, 35.5, 139.9, 35.9]},
    {"name": "神奈川県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/14_kanagawa/{z}/{x}/{y}.png", "bbox": [138.9, 35.1, 139.8, 35.7]},
    {"name": "新潟県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/15_niigata/{z}/{x}/{y}.png", "bbox": [137.8, 36.7, 139.9, 38.6]},
    {"name": "富山県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/16_toyama/{z}/{x}/{y}.png", "bbox": [136.7, 36.2, 137.8, 36.9]},
    {"name": "石川県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/17_ishikawa/{z}/{x}/{y}.png", "bbox": [136.2, 36.0, 137.4, 37.9]},
    {"name": "福井県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/18_fukui/{z}/{x}/{y}.png", "bbox": [135.4, 35.4, 136.8, 36.3]},
    {"name": "山梨県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/19_yamanashi/{z}/{x}/{y}.png", "bbox": [138.1, 35.1, 139.2, 35.9]},
    {"name": "長野県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/20_nagano/{z}/{x}/{y}.png", "bbox": [137.3, 35.1, 138.8, 37.0]},
    {"name": "岐阜県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/21_gifu/{z}/{x}/{y}.png", "bbox": [136.2, 35.1, 137.7, 36.5]},
    {"name": "静岡県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/22_shizuoka/{z}/{x}/{y}.png", "bbox": [137.4, 34.5, 139.2, 35.6]},
    {"name": "愛知県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/23_aichi/{z}/{x}/{y}.png", "bbox": [136.6, 34.5, 137.8, 35.4]},
    {"name": "三重県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/24_mie/{z}/{x}/{y}.png", "bbox": [135.8, 33.7, 137.0, 35.3]},
    {"name": "滋賀県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/25_shiga/{z}/{x}/{y}.png", "bbox": [135.8, 34.7, 136.5, 35.7]},
    {"name": "京都府", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/26_kyoto/{z}/{x}/{y}.png", "bbox": [134.8, 34.7, 136.1, 35.8]},
    {"name": "大阪府", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/27_osaka/{z}/{x}/{y}.png", "bbox": [135.1, 34.2, 135.7, 35.0]},
    {"name": "兵庫県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/28_hyogo/{z}/{x}/{y}.png", "bbox": [134.2, 34.1, 135.5, 35.7]},
    {"name": "奈良県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/29_nara/{z}/{x}/{y}.png", "bbox": [135.5, 33.8, 136.2, 34.8]},
    {"name": "和歌山県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/30_wakayama/{z}/{x}/{y}.png", "bbox": [134.9, 33.4, 136.0, 34.4]},
    {"name": "鳥取県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/31_tottori/{z}/{x}/{y}.png", "bbox": [133.1, 35.0, 134.5, 35.6]},
    {"name": "島根県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/32_shimane/{z}/{x}/{y}.png", "bbox": [131.6, 34.3, 133.4, 36.3]},
    {"name": "岡山県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/33_okayama/{z}/{x}/{y}.png", "bbox": [133.3, 34.3, 134.4, 35.3]},
    {"name": "広島県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/34_hiroshima/{z}/{x}/{y}.png", "bbox": [132.0, 34.0, 133.5, 35.1]},
    {"name": "山口県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/35_yamaguchi/{z}/{x}/{y}.png", "bbox": [130.7, 33.7, 132.3, 34.6]},
    {"name": "徳島県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/36_tokushima/{z}/{x}/{y}.png", "bbox": [133.6, 33.5, 134.8, 34.3]},
    {"name": "香川県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/37_kagawa/{z}/{x}/{y}.png", "bbox": [133.4, 34.0, 134.5, 34.6]},
    {"name": "愛媛県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/38_ehime/{z}/{x}/{y}.png", "bbox": [132.0, 32.8, 133.7, 34.3]},
    {"name": "高知県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/39_kochi/{z}/{x}/{y}.png", "bbox": [132.4, 32.7, 134.3, 33.9]},
    {"name": "福岡県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/40_fukuoka/{z}/{x}/{y}.png", "bbox": [130.0, 33.0, 131.2, 34.0]},
    {"name": "佐賀県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/41_saga/{z}/{x}/{y}.png", "bbox": [129.7, 32.9, 130.5, 33.6]},
    {"name": "長崎県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/42_nagasaki/{z}/{x}/{y}.png", "bbox": [128.5, 32.5, 130.4, 34.7]},
    {"name": "熊本県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/43_kumamoto/{z}/{x}/{y}.png", "bbox": [129.9, 32.1, 131.3, 33.2]},
    {"name": "大分県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/44_oita/{z}/{x}/{y}.png", "bbox": [130.8, 32.7, 132.2, 33.7]},
    {"name": "宮崎県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/45_miyazaki/{z}/{x}/{y}.png", "bbox": [130.7, 31.3, 131.9, 32.8]},
    {"name": "鹿児島県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/46_kagoshima/{z}/{x}/{y}.png", "bbox": [128.4, 27.0, 131.3, 32.3]},
    {"name": "沖縄県", "url": "https://disaportaldata.gsi.go.jp/raster/08_03_ekijoka_pref/47_okinawa/{z}/{x}/{y}.png", "bbox": [122.9, 24.0, 131.3, 27.9]},
]

# 該当するすべての都道府県の液状化タイルURLをリストで抽出
def detect_pref_ekijoka_list(lat, lon):
    matched = []
    for item in PREF_EKIJOKA_DATA:
        minx, miny, maxx, maxy = item["bbox"]
        if minx <= lon <= maxx and miny <= lat <= maxy:
            matched.append((item["name"], item["url"]))
    return matched

matched_ekijoka_list = detect_pref_ekijoka_list(st.session_state["lat"], st.session_state["lon"])

# 基本ハザードマップタイルのURL定義
HAZARD_MAPS = {
    "洪水（想定最大規模）": "https://disaportaldata.gsi.go.jp/raster/01_flood_l2_shinsuishin_data/{z}/{x}/{y}.png",
    "高潮（想定最大規模）": "https://disaportaldata.gsi.go.jp/raster/03_hightide_l2_shinsuishin_data/{z}/{x}/{y}.png",
    "津波": "https://disaportaldata.gsi.go.jp/raster/04_tsunami_newlegend_data/{z}/{x}/{y}.png",
    "土砂災害：土石流": "https://disaportaldata.gsi.go.jp/raster/05_dosekiryukeikaikuiki/{z}/{x}/{y}.png",
    "土砂災害：急傾斜地の崩壊": "https://disaportaldata.gsi.go.jp/raster/05_kyukeishakeikaikuiki/{z}/{x}/{y}.png",
    "土砂災害：地すべり": "https://disaportaldata.gsi.go.jp/raster/05_jisuberikeikaikuiki/{z}/{x}/{y}.png",
}

# 複数ヒットした都道府県の液状化タイルを動的追加
for pref_name, url in matched_ekijoka_list:
    ekijoka_label = f"💧 液状化危険度（{pref_name}）"
    HAZARD_MAPS[ekijoka_label] = url

# 2. サイドバー設定
st.sidebar.header("🗺️ 表示・検索設定")

map_type = st.sidebar.radio(
    "背景地図の選択",
    ["写真（航空写真）", "標準地図"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("🌊 ハザードマップレイヤー")

selected_hazards = st.sidebar.multiselect(
    "重ね表示するハザード情報",
    options=list(HAZARD_MAPS.keys()),
    default=[]
)

hazard_opacity = st.sidebar.slider(
    "ハザードマップの不透明度",
    min_value=0.0,
    max_value=1.0,
    value=0.6,
    step=0.1
)

st.sidebar.markdown("---")
st.sidebar.subheader("📍 座標指定ジャンプ")

default_coord_str = f"{st.session_state['lat']:.6f}, {st.session_state['lon']:.6f}"
coord_input = st.sidebar.text_input(
    "現在の基準座標 (緯度, 経度)",
    value=default_coord_str,
    help="直接入力してジャンプすることも可能です。地図上を右クリックでも指定できます。"
)

def parse_coord_input(input_str):
    try:
        parts = [p.strip() for p in input_str.split(",")]
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
    except ValueError:
        pass
    return None, None

# 「指定した座標へ移動」ボタン
if st.sidebar.button("指定した座標へ移動"):
    plat, plon = parse_coord_input(coord_input)
    if plat is not None and plon is not None:
        st.session_state["lat"] = plat
        st.session_state["lon"] = plon
        st.session_state["zoom"] = 14
        st.session_state["drawn_geojson"] = None  # 描画表示をリセット
        st.rerun()
    else:
        st.sidebar.error("「緯度, 経度」のカンマ区切り形式で入力してください。")

# 「現在地に指定」ボタン
if st.sidebar.button("📍 現在地に指定"):
    map_state = st.session_state.get("map")
    if map_state and map_state.get("center"):
        st.session_state["lat"] = map_state["center"]["lat"]
        st.session_state["lon"] = map_state["center"]["lng"]
        st.session_state["drawn_geojson"] = None
        st.success("現在位置を更新しました！")
        st.rerun()
    else:
        st.sidebar.warning("地図の操作情報がまだ読み込まれていません。少し動かしてから押してください。")

st.sidebar.markdown("---")
st.sidebar.subheader("📁 GPKGファイルの読み込み")

uploaded_file = st.sidebar.file_uploader("GeoPackage (.gpkg) を選択", type=["gpkg"])

# 地理院タイルのURL設定
if map_type == "標準地図":
    tile_url = "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png"
    attr = "国土地理院"
else:
    tile_url = "https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg"
    attr = "国土地理院"

# 3. 地図オブジェクト作成
m = folium.Map(
    location=[st.session_state["lat"], st.session_state["lon"]],
    zoom_start=st.session_state["zoom"],
    tiles=None,
    prefer_canvas=True
)

folium.TileLayer(
    tiles=tile_url,
    attr=attr,
    name=map_type,
    overlay=False,
    control=True
).add_to(m)

# 指定座標（現在地基準点）の場所に赤いピンを立てる
folium.Marker(
    location=[st.session_state["lat"], st.session_state["lon"]],
    popup=f"📍 基準座標<br>緯度: {st.session_state['lat']:.6f}<br>経度: {st.session_state['lon']:.6f}",
    tooltip="📍 現在の基準座標",
    icon=folium.Icon(color="red", icon="info-sign")
).add_to(m)

# ★ 右クリック（contextmenu）のイベントを Leaflet の click イベントに変換して Python へ送信する JS を追加
right_click_js = folium.Element(f"""
    var map_obj = {m.get_name()};
    map_obj.on('contextmenu', function(e) {{
        map_obj.fire('click', e);
    }});
""")
m.get_root().script.add_child(right_click_js)

# 選択されたハザードマップタイル（液状化含む）を重ね合わせ
for hazard_name in selected_hazards:
    hazard_url = HAZARD_MAPS[hazard_name]
    folium.TileLayer(
        tiles=hazard_url,
        attr="ハザードマップポータルサイト",
        name=hazard_name,
        overlay=True,
        opacity=hazard_opacity,
        control=True
    ).add_to(m)

Geocoder(collapsed=True, position="topleft").add_to(m)

# 4. GPKG読み込み・座標周辺（ズーム14範囲）の描画処理
if uploaded_file is not None:
    try:
        @st.cache_data
        def load_gpkg(file):
            gdf = gpd.read_file(file)
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)
            return gdf

        gdf = load_gpkg(uploaded_file)
        raw_fields = [col for col in gdf.columns if col not in ["geometry", "_color"]]

        st.sidebar.markdown("⚡ **描画設定**")

        map_state = st.session_state.get("map")
        current_zoom = map_state.get("zoom") if (map_state and map_state.get("zoom")) else st.session_state["zoom"]
        st.sidebar.info(f"🔍 **現在のズームレベル:** `{current_zoom}`")

        style_mode = st.sidebar.radio(
            "表示モード",
            ["単色表示", "カテゴリ別（色分け）", "10段階ヒートマップ風"]
        )

        selected_col = None
        cmap_name = "jet_r"
        if style_mode == "カテゴリ別（色分け）":
            selected_col = st.sidebar.selectbox("色分け属性", raw_fields)
        elif style_mode == "10段階ヒートマップ風":
            selected_col = st.sidebar.selectbox("0〜1の数値属性", raw_fields)
            cmap_name = st.sidebar.selectbox(
                "カラーテーマ", 
                ["jet_r (低:赤 ➔ 高:青)", "jet (低:青 ➔ 高:赤)", "viridis", "coolwarm", "plasma"]
            )
            cmap_name = cmap_name.split(" ")[0]

        st.sidebar.markdown("---")

        draw_button = st.sidebar.button("🎨 画面中央の周辺(Zoom14相当)を描画する", type="primary")

        # 描画ボタンを押した瞬間：画面中心座標を取得して差し替え＆現在地確定
        if draw_button:
            map_state = st.session_state.get("map")
            
            if map_state and map_state.get("center"):
                st.session_state["lat"] = map_state["center"]["lat"]
                st.session_state["lon"] = map_state["center"]["lng"]
            else:
                plat, plon = parse_coord_input(coord_input)
                if plat is not None and plon is not None:
                    st.session_state["lat"] = plat
                    st.session_state["lon"] = plon

            center_lat = st.session_state["lat"]
            center_lon = st.session_state["lon"]

            # ズーム14相当の範囲（約3km四方）で空間切り出し
            minx = center_lon - 0.020
            maxx = center_lon + 0.020
            miny = center_lat - 0.015
            maxy = center_lat + 0.015

            display_gdf = gdf.cx[minx:maxx, miny:maxy].copy()

            if len(display_gdf) == 0:
                st.sidebar.warning("現在表示位置の周辺に地物が存在しません。")
                st.session_state["drawn_geojson"] = None
                st.session_state["drawn_count"] = 0
            else:
                if style_mode == "単色表示":
                    display_gdf["_color"] = "#ff3333"

                elif style_mode == "カテゴリ別（色分け）":
                    unique_vals = display_gdf[selected_col].dropna().unique()
                    cmap = matplotlib.colormaps["tab10"]
                    color_dict = {
                        val: mcolors.to_hex(cmap(i % 10))
                        for i, val in enumerate(unique_vals)
                    }
                    display_gdf["_color"] = display_gdf[selected_col].map(color_dict).fillna("#888888")

                elif style_mode == "10段階ヒートマップ風":
                    num_series = pd.to_numeric(display_gdf[selected_col], errors="coerce")
                    if num_series.notnull().any():
                        cmap = matplotlib.colormaps[cmap_name]

                        def val_to_10steps_color(val):
                            if pd.isna(val):
                                return "#888888"
                            try:
                                v = float(val)
                                v = max(0.0, min(1.0, v))
                                v_step = round(v * 10) / 10
                                return mcolors.to_hex(cmap(v_step))
                            except:
                                return "#888888"

                        display_gdf["_color"] = num_series.apply(val_to_10steps_color)
                    else:
                        display_gdf["_color"] = "#ff3333"

                geom_types = [str(gt).lower() for gt in display_gdf.geometry.type.unique()]
                st.session_state["is_point"] = any("point" in gt for gt in geom_types)
                st.session_state["drawn_count"] = len(display_gdf)

                st.session_state["drawn_geojson"] = display_gdf.__geo_interface__

        # 描画済みデータがあればオーバーレイ
        drawn_geojson = st.session_state.get("drawn_geojson")
        if drawn_geojson is not None and st.session_state.get("drawn_count", 0) > 0:
            st.sidebar.success(f"表示中地物: {st.session_state['drawn_count']:,} 件")

            fields = list(drawn_geojson["features"][0]["properties"].keys()) if drawn_geojson.get("features") else []
            tooltip_fields = [col for col in fields if col not in ["geometry", "_color"]][:5]

            tooltip_obj = None
            if tooltip_fields:
                tooltip_obj = folium.GeoJsonTooltip(
                    fields=tooltip_fields,
                    aliases=tooltip_fields,
                    localize=True,
                    sticky=True
                )

            if st.session_state.get("is_point", False):
                geojson_layer = folium.GeoJson(
                    drawn_geojson,
                    name="GPKG Points",
                    tooltip=tooltip_obj,
                    marker=folium.CircleMarker(radius=6, fill=True),
                    style_function=lambda feature: {
                        "fillColor": feature["properties"].get("_color", "#ff3333"),
                        "color": "#ffffff",
                        "weight": 1.0,
                        "fillOpacity": 0.9,
                        "opacity": 1.0
                    }
                )
                geojson_layer.add_to(m)

            else:
                geojson_layer = folium.GeoJson(
                    drawn_geojson,
                    name="GPKG Layer",
                    tooltip=tooltip_obj,
                    style_function=lambda feature: {
                        "fillColor": feature["properties"].get("_color", "#ff3333"),
                        "color": feature["properties"].get("_color", "#ff3333"),
                        "weight": 1.5,
                        "fillOpacity": 0.6,
                    }
                )
                geojson_layer.add_to(m)

    except Exception as e:
        st.sidebar.error(f"ファイル読み込みエラー: {e}")

folium.LayerControl().add_to(m)

# 5. 地図表示（★ last_clicked を取得してクリック・右クリック座標を受け取る）
st_data = st_folium(
    m,
    width="100%",
    height=600,
    key="map",
    returned_objects=["center", "zoom", "last_clicked"]
)

# ★ マップ上を右クリック（または左クリック）した際、クリック位置を基準座標に即座に差し替えて画面更新
if st_data and st_data.get("last_clicked"):
    click_lat = round(st_data["last_clicked"]["lat"], 6)
    click_lon = round(st_data["last_clicked"]["lng"], 6)
    
    if click_lat != round(st.session_state["lat"], 6) or click_lon != round(st.session_state["lon"], 6):
        st.session_state["lat"] = click_lat
        st.session_state["lon"] = click_lon
        st.session_state["drawn_geojson"] = None  # 描画データをリセット
        st.rerun()
