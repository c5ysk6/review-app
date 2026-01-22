import streamlit as st
from openai import OpenAI
import pandas as pd

# --- ⚙️ 設定エリア ---
# ★ここに【手順2】でコピーしたスプレッドシートのURLを貼ってください
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

# --- 🎨 ページ設定 ---
st.set_page_config(page_title="EIGHT MEN 口コミ", layout="centered")
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 12px; font-weight: bold; padding: 12px; background-color: #D32F2F; color: white; border: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 📥 スプレッドシート読み込みロジック ---
@st.cache_data(ttl=600) # 10分ごとにデータを再取得（更新反映）
def load_staff_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # 店舗名をキー、スタッフリストを値にする辞書に変換
        return df.groupby('店舗名')['スタッフ名'].apply(list).to_dict()
    except Exception:
        return {}

# データをロード
staff_data_dict = load_staff_data()

# --- 📍 店舗自動判定 ---
query_params = st.query_params
pre_selected_store = query_params.get("store", None)

if pre_selected_store and pre_selected_store in STORES:
    selected_store_name = pre_selected_store
    selected_store_link = STORES[pre_selected_store]
    st.subheader(f"📍 {selected_store_name}")
else:
    selected_store_name = st.selectbox("店舗を選択", list(STORES.keys()))
    selected_store_link = STORES[selected_store_name]

st.title("本日の感想をお聞かせください")
st.caption("AIがあなたの代わりに口コミ文章を作成します🤖")

# --- 📝 入力フォーム ---
with st.form("review_form"):
    
    # スプレッドシートからその店のスタッフリストを取得
    current_staff_list = staff_data_dict.get(selected_store_name, ["指名なし"])
    
    # 万が一シートにデータがない場合のエラー回避
    if not current_staff_list:
        current_staff_list = ["指名なし"]

    staff_name = st.selectbox("担当スタッフ", current_staff_list)

    menu = st.multiselect(
        "施術メニュー",
        ["カット", "パーマ", "カラー", "ブリーチ", "縮毛矯正", "眉毛カット", "スパ", "トリートメント"],
        default=["カット"]
    )

    rating = st.slider("満足度", 1, 5, 5)

    points = st.multiselect(
        "良かったポイント",
        ["セットが楽になった", "似合う髪型を提案してくれた", "説明が丁寧", "店の雰囲気が良い", "スピーディー", "また来たい"]
    )
    
    submit_button = st.form_submit_button("口コミを生成する ✨")

# --- 🤖 生成ロジック ---
if submit_button:
    if not menu:
        st.error("メニューを1つ以上選んでください")
    else:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # 名前処理（苗字抽出）
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

        with st.spinner("AIが執筆中..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": system_prompt}],
                )
                generated_text = response.choices[0].message.content
                
                st.success("生成されました！右上のアイコンでコピーできます")
                st.code(generated_text, language=None)
                
                st.markdown(f"""
                <a href="{selected_store_link}" target="_blank">
                    <button style="
                        width:100%; 
                        padding:15px; 
                        background-color:#4285F4; 
                        color:white; 
                        border:none; 
                        border-radius:12px; 
                        font-weight:bold; 
                        font-size:16px; 
                        cursor:pointer;
                        margin-top: 10px;">
                        Googleマップを開いて投稿 📍
                    </button>
                </a>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"エラー: {e}")
