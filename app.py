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

# --- 🎨 ページ設定 & シンプルデザイン ---
st.set_page_config(page_title="EIGHT MEN 口コミ", layout="centered")

# CSSでスタイリング（白ベース・赤アクセント）
st.markdown("""
    <style>
    /* ボタンのデザイン（EIGHT MENレッドのグラデーション） */
    /* 白背景に映えるように調整 */
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
    /* ヘッダー隠し */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* タイトルを見やすく強調 */
    h1 {
        color: #333;
        font-family: sans-serif;
        font-weight: 800;
        border-bottom: 3px solid #D32F2F;
        display: inline-block;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    /* サブタイトルや説明文 */
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
    # 店舗名を赤文字で強調
    st.markdown(f"<h3 style='color: #D32F2F;'>📍 {selected_store_name}</h3>", unsafe_allow_html=True)
else:
    selected_store_name = st.selectbox("店舗を選択", list(STORES.keys()))
    selected_store_link = STORES[selected_store_name]

st.title("GUEST REVIEW")
st.write("ご来店ありがとうございます。\n簡単な質問に答えるだけで、AIが口コミ文章を作成します。")

# --- 📝 見やすい入力フォーム ---
st.divider() # 区切り線で見やすく

# スタッフ選択
st.caption("担当スタッフ")
current_staff_list = staff_data_dict.get(selected_store_name, ["指名なし"])
if not current_staff_list: current_staff_list = ["指名なし"]
staff_name = st.selectbox("担当スタッフ", current_staff_list, label_visibility="collapsed")

st.write("") 

# pills（カプセルボタン）
st.caption("① 本日のメニュー（複数選択可）")
menu = st.pills(
    "メニュー",
    ["メンズカット", "パーマ", "ツイストスパイラル", "波巻きパーマ", "カラー", "ブリーチ", "縮毛矯正", "眉毛カット", "ヘッドスパ"],
    selection_mode="multi",
    label_visibility="collapsed"
)

st.write("")

# 星評価
st.caption("② 本日の満足度")
rating_stars = st.feedback("stars")
rating = (rating_stars + 1) if rating_stars is not None else 5

st.write("")

# pillsでポイント選択
st.caption("③ 気に入ったポイント（複数選択可）")
points = st.pills(
    "ポイント",
    ["セットが楽になった", "似合う髪型にしてくれた", "カウンセリングが丁寧", "店の雰囲気が良い", "スピーディー", "また来たい"],
    selection_mode="multi",
    label_visibility="collapsed"
)

st.divider() # 区切り線

# 生成ボタン
submit_button = st.button("口コミを生成する ✨")

# --- 🤖 生成ロジック ---
if submit_button:
    if not menu:
        st.error("メニューを1つ以上選んでください")
    else:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # 名前処理
        if staff_name and staff_name != "指名なし":
            short_name = staff_name.replace("　", " ").split(" ")[0]
            staff_prompt = f"担当の「{short_name}」さんについても好意的に触れてください。"
        else:
            staff_prompt = "スタッフの対応についても軽く触れてください。"
        
        system_prompt = f"""
        あなたは「メンズサロン EIGHT MEN {selected_store_name}」を利用した男性客です。
        Googleマップの口コミを書いてください。
        
        【条件】
        - 施術: {', '.join(menu)}
        - 満足度: 星{rating}
        - ポイント: {', '.join(points)}
        - {staff_prompt}
        - 文字数: 100文字前後
        - 口調: 自然な口語体（絵文字は使わない）
        - 嘘は書かず、実体験のように書く
        """

        # シンプルで見やすいローディング
        with st.status("AIが執筆中...", expanded=True) as status:
            st.write("少々お待ちください...")
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": system_prompt}],
                )
                generated_text = response.choices[0].message.content
                
                status.update(label="完了しました！", state="complete", expanded=False)
                st.toast('生成完了！', icon='✅')
                
                st.success("下のボックスからコピーできます 👇")
                st.code(generated_text, language=None)
                
                # Googleマップボタン（青色で目立たせる）
                st.markdown(f"""
                <a href="{selected_store_link}" target="_blank">
                    <button style="
                        width:100%; 
                        padding:15px; 
                        background: #1A73E8; 
                        color:white; 
                        border:none; 
                        border-radius:30px; 
                        font-weight:bold; 
                        font-size:16px; 
                        cursor:pointer;
                        box-shadow: 0 4px 10px rgba(26, 115, 232, 0.3);
                        margin-top: 15px;">
                        Googleマップを開いて投稿 📍
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"エラー: {e}")
