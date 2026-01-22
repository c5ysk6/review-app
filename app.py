import streamlit as st
from openai import OpenAI
import pandas as pd
import time

# --- ⚙️ 設定エリア ---
# ★ここにスプレッドシートのURLを貼ってください
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmDV5UTQENMNag-AjCx-FLMx7nTo8egWu7kdt5Df-n13Tst-ctf6Ew48MbcMpsTAs844v0Zbfv3gfS/pub?output=csv"

# 店舗ごとのGoogleマップリンク
STORES = {
    "渋谷店": "https://g.page/r/CdXIDXyii4lgEAE/review",
    "池袋西口店": "https://g.page/r/CaV4ekjwYsV1EAE/review",
    "池袋東口店": "https://g.page/r/CdTMjlluc_OFEAE/review",
    "新宿店": "https://g.page/r/CYky-2vp6Y0REAE/review",
    "上野店": "https://g.page/r/CQh9ZNzN-HMPEAE/review",
    "北千住店": "https://g.page/r/CVCsbonX5vKQEAE/review",
    "吉祥寺店": "https://g.page/r/CUFrBrlWrjwaEAE/review",
    "博多店": "https://g.page/r/Cfs_-7LhTWtDEAE/review",
    "那覇新都心店": "https://g.page/r/CU_5fyrZxjvwEAE/review",
}

# 【NEW】SEO用エリアキーワード辞書
# 店舗名に紐づく「MEOで狙いたい地名・駅名」を定義
STORE_AREAS = {
    "渋谷店": "渋谷",
    "池袋西口店": "池袋",
    "池袋東口店": "池袋",
    "新宿店": "新宿",
    "上野店": "上野",
    "北千住店": "北千住",
    "吉祥寺店": "吉祥寺",
    "博多店": "博多",
    "那覇新都心店": "那覇",
}

# --- 🎨 ページ設定 & デザイン ---
st.set_page_config(page_title="EIGHT MEN 口コミ", layout="centered")

# CSSでスタイリング（白ベース・赤アクセント・シンプル）
st.markdown("""
    <style>
    .stButton>button {
        width: 100%; 
        border-radius: 30px; 
        font-weight: bold; 
        padding: 16px; 
        background: linear-gradient(135deg, #D32F2F 0%, #FF5252 100%); 
        color: white; 
        border: none;
        box-shadow: 0 4px 10px rgba(211, 47, 47, 0.3);
        transition: all 0.3s ease;
        font-size: 18px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(211, 47, 47, 0.5);
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    h1 {
        color: #333;
        font-family: sans-serif;
        font-weight: 800;
        border-bottom: 3px solid #D32F2F;
        display: inline-block;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .stCaption {
        font-size: 16px;
        color: #555;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 📥 データ読み込み ---
@st.cache_data(ttl=600)
def load_staff_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.groupby('店舗名')['スタッフ名'].apply(list).to_dict()
    except Exception:
        return {}

staff_data_dict = load_staff_data()

# --- 📍 店舗自動判定 ---
query_params = st.query_params
pre_selected_store = query_params.get("store", None)

if pre_selected_store and pre_selected_store in STORES:
    selected_store_name = pre_selected_store
    selected_store_link = STORES[pre_selected_store]
    st.markdown(f"<h3 style='color: #D32F2F;'>📍 {selected_store_name}</h3>", unsafe_allow_html=True)
else:
    selected_store_name = st.selectbox("店舗を選択", list(STORES.keys()))
    selected_store_link = STORES[selected_store_name]

st.title("GUEST REVIEW")
st.write("簡単な質問に答えるだけで、AIが口コミ文章を作成します。")

# --- 📝 入力フォーム ---
st.divider() 

# スタッフ選択
st.caption("担当スタッフ")
current_staff_list = staff_data_dict.get(selected_store_name, ["指定しない"])
if not current_staff_list: current_staff_list = ["指定しない"]
staff_name = st.selectbox("担当スタッフ", current_staff_list, label_visibility="collapsed")

st.write("") 

# メニュー選択
st.caption("① 本日のメニュー（複数選択可）")
menu = st.pills(
    "メニュー",
    ["メンズカット", "パーマ", "ツイストスパイラル", "波巻きパーマ", "ニュアンスパーマ", "カラー", "ブリーチ", "縮毛矯正", "眉毛カット", "ヘッドスパ"],
    selection_mode="multi",
    label_visibility="collapsed"
)

st.write("")

# 満足度
st.caption("② 本日の満足度")
rating_stars = st.feedback("stars")
rating = (rating_stars + 1) if rating_stars is not None else 5

st.write("")

# ポイント選択
st.caption("③ 気に入ったポイント（複数選択可）")
points = st.pills(
    "ポイント",
    ["セットが楽になった", "似合う髪型にしてくれた", "カウンセリングが丁寧", "店の雰囲気が良い", "スピーディー", "また来たい"],
    selection_mode="multi",
    label_visibility="collapsed"
)

st.divider() 

submit_button = st.button("口コミを生成する ✨")

# --- 🤖 生成ロジック（ここをMEO特化型に改造） ---
if submit_button:
    if not menu:
        st.error("メニューを1つ以上選んでください")
    else:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
